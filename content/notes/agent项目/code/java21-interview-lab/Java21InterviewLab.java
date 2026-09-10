import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Deterministic semantic examples; not a throughput benchmark. Requires JDK 21. */
public final class Java21InterviewLab {
    private static int passed;

    public static void main(String[] args) throws Exception {
        System.out.println("Runtime: " + Runtime.version());
        System.out.println("Vendor: " + System.getProperty("java.vendor"));
        unboundedQueue();
        boundedQueue();
        timeoutDoesNotStopWork();
        samePoolStarvation();
        threadLocalReuse();
        volatileIsNotAtomic();
        virtualThreadsStillNeedAdmission();
        System.out.println("PASS: " + passed + " semantic cases; no performance claim.");
    }

    private static void unboundedQueue() throws Exception {
        var release = new CountDownLatch(1);
        var started = new CountDownLatch(1);
        var pool = new ThreadPoolExecutor(1, 3, 1, TimeUnit.SECONDS,
                new LinkedBlockingQueue<>());
        try {
            var first = pool.submit(() -> { started.countDown(); await(release); });
            await(started);
            var second = pool.submit(() -> {});
            var third = pool.submit(() -> {});
            check(pool.getPoolSize() == 1 && pool.getQueue().size() == 2,
                    "unbounded queue should hold tasks without expanding to max=3");
            release.countDown();
            first.get(5, TimeUnit.SECONDS);
            second.get(5, TimeUnit.SECONDS);
            third.get(5, TimeUnit.SECONDS);
            pass("unbounded queue: pool=1, queued=2 while first task is held");
        } finally { release.countDown(); stop(pool); }
    }

    private static void boundedQueue() throws Exception {
        var release = new CountDownLatch(1);
        var started = new CountDownLatch(2);
        var pool = new ThreadPoolExecutor(1, 2, 1, TimeUnit.SECONDS,
                new ArrayBlockingQueue<>(1), new ThreadPoolExecutor.AbortPolicy());
        Runnable held = () -> { started.countDown(); await(release); };
        try {
            var first = pool.submit(held); // core worker
            var queued = pool.submit(() -> {}); // one queue slot
            var expanded = pool.submit(held); // full queue forces second worker
            await(started);
            boolean rejected = false;
            try { pool.execute(() -> {}); }
            catch (RejectedExecutionException expected) { rejected = true; }
            check(rejected && pool.getPoolSize() == 2 && pool.getQueue().size() == 1,
                    "fourth task must be rejected while both workers are held");
            release.countDown();
            first.get(5, TimeUnit.SECONDS);
            queued.get(5, TimeUnit.SECONDS);
            expanded.get(5, TimeUnit.SECONDS);
            pass("bounded queue: pool=2, queued=1, fourth task rejected");
        } finally { release.countDown(); stop(pool); }
    }

    private static void timeoutDoesNotStopWork() throws Exception {
        var pool = Executors.newSingleThreadExecutor();
        var started = new CountDownLatch(1);
        var release = new CountDownLatch(1);
        var completed = new CountDownLatch(1);
        var sideEffects = new AtomicInteger();
        try {
            var future = CompletableFuture.supplyAsync(() -> {
                started.countDown();
                await(release);
                sideEffects.incrementAndGet();
                completed.countDown();
                return "committed";
            }, pool);
            await(started);
            boolean timedOut = false;
            try { future.orTimeout(100, TimeUnit.MILLISECONDS).get(5, TimeUnit.SECONDS); }
            catch (ExecutionException expected) {
                timedOut = expected.getCause() instanceof TimeoutException;
            }
            check(timedOut && completed.getCount() == 1 && sideEffects.get() == 0,
                    "future should time out while underlying work is still waiting");
            release.countDown();
            await(completed);
            check(sideEffects.get() == 1 && future.isCompletedExceptionally(),
                    "underlying work should finish even though future remains failed");
            pass("orTimeout: caller failed, underlying work later produced one side effect");
        } finally { release.countDown(); stop(pool); }
    }

    private static void samePoolStarvation() throws Exception {
        var pool = Executors.newSingleThreadExecutor();
        var childSubmitted = new CountDownLatch(1);
        var childFinished = new CountDownLatch(1);
        try {
            var parent = pool.submit(() -> {
                var child = pool.submit(childFinished::countDown);
                childSubmitted.countDown();
                try {
                    child.get(150, TimeUnit.MILLISECONDS);
                    throw new AssertionError("child cannot run while parent holds only worker");
                } catch (TimeoutException expected) {
                    check(childFinished.getCount() == 1, "child must still be queued");
                }
                return "parent released worker after bounded wait";
            });
            await(childSubmitted);
            parent.get(5, TimeUnit.SECONDS);
            await(childFinished);
            pass("same pool: parent timed out waiting; child ran after parent returned");
        } finally { stop(pool); }
    }

    private static void threadLocalReuse() throws Exception {
        var pool = Executors.newSingleThreadExecutor();
        var actor = new ThreadLocal<String>();
        try {
            pool.submit(() -> actor.set("user-A")).get(5, TimeUnit.SECONDS);
            String leaked = pool.submit(actor::get).get(5, TimeUnit.SECONDS);
            check("user-A".equals(leaked), "next task on reused thread sees stale actor");
            pool.submit(() -> {
                try { actor.set("user-B"); }
                finally { actor.remove(); }
            }).get(5, TimeUnit.SECONDS);
            check(pool.submit(actor::get).get(5, TimeUnit.SECONDS) == null,
                    "finally remove must clear worker thread context");
            pass("ThreadLocal: stale actor reproduced; finally/remove cleared it");
        } finally { stop(pool); }
    }

    private static final class Counter { volatile int value; }

    private static void volatileIsNotAtomic() throws Exception {
        var pool = Executors.newFixedThreadPool(2);
        var bothRead = new CyclicBarrier(2);
        var counter = new Counter();
        var atomic = new AtomicInteger();
        Callable<Void> increment = () -> {
            int observed = counter.value; // decomposed read-modify-write, like value++
            bothRead.await(5, TimeUnit.SECONDS); // force both to read zero first
            counter.value = observed + 1;
            atomic.incrementAndGet();
            return null;
        };
        try {
            var a = pool.submit(increment);
            var b = pool.submit(increment);
            a.get(5, TimeUnit.SECONDS);
            b.get(5, TimeUnit.SECONDS);
            check(counter.value == 1 && atomic.get() == 2,
                    "volatile read/write pair loses one update; atomic increment does not");
            pass("read-modify-write: volatile=1, AtomicInteger=2 under forced interleaving");
        } finally { stop(pool); }
    }

    private static void virtualThreadsStillNeedAdmission() throws Exception {
        var pool = Executors.newVirtualThreadPerTaskExecutor();
        var permits = new Semaphore(2);
        var admitted = new CountDownLatch(2);
        var attemptedThird = new CountDownLatch(1);
        var release = new CountDownLatch(1);
        var active = new AtomicInteger();
        var peak = new AtomicInteger();
        Callable<Void> work = () -> {
            check(Thread.currentThread().isVirtual(), "must run in virtual thread");
            permits.acquire();
            try {
                int now = active.incrementAndGet();
                peak.accumulateAndGet(now, Math::max);
                admitted.countDown();
                await(release);
            } finally { active.decrementAndGet(); permits.release(); }
            return null;
        };
        try {
            var a = pool.submit(work);
            var b = pool.submit(work);
            await(admitted);
            var c = pool.submit(() -> { attemptedThird.countDown(); return work.call(); });
            await(attemptedThird);
            check(active.get() == 2 && permits.availablePermits() == 0,
                    "third task cannot enter while first two hold permits");
            release.countDown();
            a.get(5, TimeUnit.SECONDS);
            b.get(5, TimeUnit.SECONDS);
            c.get(5, TimeUnit.SECONDS);
            check(peak.get() == 2, "downstream concurrency must never exceed two");
            pass("virtual threads: three tasks, semaphore limited downstream peak to two");
        } finally { release.countDown(); stop(pool); }
    }

    private static void await(CountDownLatch latch) {
        try {
            if (!latch.await(5, TimeUnit.SECONDS)) throw new AssertionError("latch timed out");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException(e);
        }
    }

    private static void stop(ExecutorService pool) throws InterruptedException {
        pool.shutdown();
        if (!pool.awaitTermination(5, TimeUnit.SECONDS)) {
            pool.shutdownNow();
            check(pool.awaitTermination(5, TimeUnit.SECONDS), "executor failed to terminate");
        }
    }

    private static void check(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }

    private static void pass(String message) {
        passed++;
        System.out.println("PASS " + passed + ": " + message);
    }
}

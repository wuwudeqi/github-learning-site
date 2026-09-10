Java 21 interview semantic lab

Requirements: JDK 21, no third-party dependencies. No database, network or business data.
Run from this directory with a JDK 21 java executable:

  java Java21InterviewLab.java

Seven named cases contain assertions and bounded waits. A failed assertion exits nonzero.
Latches/barriers force relevant interleavings; timeout durations are test guards, not SLOs.
These are small semantic experiments, not JUnit tests or performance benchmarks.
The volatile example deliberately decomposes read-modify-write to reproduce a lost update.
The virtual-thread case demonstrates admission control, not pinning or higher throughput.
Production Spring transaction handling, JDBC cancellation and distributed execution are not tested.
verification.txt records the actual run used in the accompanying article.

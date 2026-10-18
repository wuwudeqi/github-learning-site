"""Local, synthetic experiment. No network requests or real orders.
Run: python3 idempotency_demo.py > idempotency-results.json
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


def worker(database, key, amount, crash):
    conn = sqlite3.connect(database, timeout=10, isolation_level=None)
    payload = json.dumps({'amount': amount}, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(payload.encode()).hexdigest()
    conn.execute('BEGIN IMMEDIATE')
    try:
        prior = conn.execute('SELECT payload_hash, result FROM receipts WHERE request_key=?', (key,)).fetchone()
        if prior:
            if prior[0] != digest:
                conn.rollback()
                return {'status': 'conflict', 'request': key}
            conn.commit()
            return {'status': 'replayed', 'request': key, 'result': json.loads(prior[1])}
        cur = conn.execute('INSERT INTO orders(amount) VALUES (?)', (amount,))
        result = {'order_id': cur.lastrowid, 'amount': amount}
        conn.execute('INSERT INTO receipts VALUES (?,?,?)', (key, digest, json.dumps(result)))
        if crash == 'before':
            os._exit(74)  # Actual child process exit; transaction is not committed.
        conn.commit()
        if crash == 'after':
            os._exit(75)  # Commit succeeded; caller receives no response.
        return {'status': 'created', 'request': key, 'result': result}
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def experiment():
    with tempfile.TemporaryDirectory(prefix='frontiers-idempotency-') as directory:
        database = str(Path(directory) / 'demo.sqlite')
        with sqlite3.connect(database) as conn:
            conn.executescript('CREATE TABLE orders(id INTEGER PRIMARY KEY, amount INTEGER NOT NULL);'
                               'CREATE TABLE receipts(request_key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, result TEXT NOT NULL);')
        rows = []
        def command(key, amount=3, crash='none'):
            return [sys.executable, str(Path(__file__).resolve()), '--worker', database, key, str(amount), crash]
        def count():
            with sqlite3.connect(database) as conn:
                return conn.execute('SELECT count(*) FROM orders').fetchone()[0]
        def run(label, key, amount=3, crash='none', expected=None):
            result = subprocess.run(command(key, amount, crash), text=True, capture_output=True)
            record = {'case': label, 'exitCode': result.returncode, 'response': json.loads(result.stdout) if result.stdout else None, 'ordersAfter': count()}
            rows.append(record)
            if expected is not None:
                assert record['ordersAfter'] == expected, record
            return record
        first = run('首次 A', 'A', expected=1)
        replay = run('重试 A', 'A', expected=1)
        assert first['response']['result'] == replay['response']['result']
        conflict = run('A 换参数', 'A', amount=4, expected=1)
        assert conflict['response']['status'] == 'conflict'
        before = run('B 提交前退出', 'B', crash='before', expected=1)
        assert before['exitCode'] == 74 and before['response'] is None
        run('重试 B', 'B', expected=2)
        after = run('C 提交后退出', 'C', crash='after', expected=3)
        assert after['exitCode'] == 75 and after['response'] is None
        replay_c = run('重试 C', 'C', expected=3)
        assert replay_c['response']['status'] == 'replayed'
        children = [subprocess.Popen(command('D'), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        concurrent = []
        for child in children:
            out, err = child.communicate(timeout=20)
            assert child.returncode == 0, err
            concurrent.append(json.loads(out))
        assert sorted(x['status'] for x in concurrent) == ['created', 'replayed'], concurrent
        assert concurrent[0]['result'] == concurrent[1]['result']
        assert count() == 4
        rows.append({'case': '并发 D × 2', 'responses': concurrent, 'ordersAfter': count(), 'exitCode': 0})
        with sqlite3.connect(database) as conn:
            assert conn.execute('SELECT count(*) FROM receipts').fetchone()[0] == 4
        return {'observedAt': datetime.now(timezone.utc).isoformat(), 'environment': {'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version, 'platform': platform.system(), 'machine': platform.machine()}, 'data': 'synthetic local orders; process exits are real, not power-loss tests', 'requests': 9, 'uniqueKeys': 4, 'finalOrders': 4, 'checks': 'passed', 'cases': rows}


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        print(json.dumps(worker(sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5])))
    else:
        print(json.dumps(experiment(), ensure_ascii=False, indent=2))

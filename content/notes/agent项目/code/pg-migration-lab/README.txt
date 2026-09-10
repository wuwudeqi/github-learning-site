PostgreSQL migration semantic lab

Run: python3 run-lab.py
Requires installed PostgreSQL server binaries and Python 3. Run as an ordinary user, not root.
The runner creates a temporary cluster under /tmp, binds only a private Unix socket,
and removes that cluster after stopping it. It does not use existing database connections.
No application data is read. All sample tables are temporary and contain synthetic rows.

Seven cases: empty/null, numeric rounding/overflow, date/time, identity sequence,
operation conflict, project-level reconciliation, and failed transaction SQLSTATE.
The last case deliberately emits two database errors and asserts 23505 followed by 25P02.
A failure of either expected state or any DO assertion makes psql and the runner fail.

verification.txt records the actual PostgreSQL version and results.
This is not an Oracle-to-PostgreSQL migration test: no Oracle instance, CDC,
JDBC/Spring integration, concurrent upsert test or performance comparison is included.
Sequence alignment is only a local nonempty-table example, not a general cutover script.

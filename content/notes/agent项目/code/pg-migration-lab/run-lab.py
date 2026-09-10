"""Run only against a new, disposable PostgreSQL cluster; never connect to a saved DB."""
from pathlib import Path
import shutil
import subprocess
import tempfile

here = Path(__file__).resolve().parent
pg_ctl = shutil.which("pg_ctl")
if not pg_ctl:
    raise SystemExit("PostgreSQL server tools are required (pg_ctl/initdb/psql).")
bin_dir = Path(pg_ctl).resolve().parent

def run(tool, *args):
    result = subprocess.run([str(bin_dir / tool), *map(str, args)],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout, end="", flush=True)
    if result.returncode:
        raise RuntimeError(f"{tool} exited with {result.returncode}")

with tempfile.TemporaryDirectory(prefix="pg-migration-lab-", dir="/tmp") as work:
    root = Path(work)
    data = root / "data"
    socket = root / "socket"
    socket.mkdir(mode=0o700)
    run("initdb", "-D", data, "-U", "lab_owner", "--no-locale", "--encoding=UTF8",
        "--auth-local=trust", "--auth-host=reject")
    with (data / "postgresql.conf").open("a") as config:
        config.write(f"\nlisten_addresses = ''\nunix_socket_directories = '{socket}'\n"
                     "port = 55439\nunix_socket_permissions = 0700\n")
    try:
        run("pg_ctl", "-D", data, "-l", root / "server.log", "-w", "start")
        run("psql", "-X", "-h", socket, "-p", "55439", "-U", "lab_owner",
            "-d", "postgres", "-f", here / "checks.sql")
    finally:
        if (data / "postmaster.pid").exists():
            run("pg_ctl", "-D", data, "-m", "fast", "-w", "stop")

import os
import signal
import subprocess
import sys


def main() -> None:
    port = 8000
    print(f"[kill_port] checking for listeners on port {port}")
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        print("[kill_port] lsof not available; skipping port cleanup", file=sys.stderr)
        return

    pids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not pids:
        print(f"[kill_port] no process on port {port}")
        return

    for raw in pids:
        try:
            pid = int(raw)
        except ValueError:
            continue
        print(f"[kill_port] terminating PID {pid} on port {port}")
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            print(f"[kill_port] PID {pid} disappeared before kill", file=sys.stderr)


if __name__ == "__main__":
    main()

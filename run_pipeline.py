from pathlib import Path
import subprocess
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable

def run_stage(name, script):
    path = ROOT / script
    if not path.exists():
        raise FileNotFoundError(f"Required pipeline script not found: {path}")

    print(f"\n{'=' * 60}", flush=True)
    print(f"START: {name} — {datetime.now():%Y-%m-%d %H:%M:%S}", flush=True)
    print(f"{'=' * 60}", flush=True)

    subprocess.run([PYTHON, str(path)], cwd=ROOT, check=True)

    print(f"SUCCESS: {name}", flush=True)

def main():
    print("GP Appointments KPI Pipeline", flush=True)

    try:
        run_stage("Extract", "src/extract.py")
        run_stage("Transform", "src/transform.py")
        print("\nPIPELINE COMPLETED SUCCESSFULLY", flush=True)
    except Exception as exc:
        print(f"\nPIPELINE FAILED: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1)

if __name__ == "__main__":
    main()

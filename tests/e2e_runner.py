"""Runner script for Conch E2E Verification Test Suite."""

import shutil
import subprocess
import sys
import time


def run_e2e_suite():
    print("=" * 80)
    print(" CONCH - E2E TEST SUITE RUNNER")
    print(" Requirement-Driven Opaque-Box Verification (Tiers 1 - 4)")
    print("=" * 80)

    start_time = time.time()

    # Prefer uv run if uv is available in environment
    if shutil.which("uv"):
        cmd = ["uv", "run", "pytest", "tests/e2e", "-v"]
    else:
        cmd = [sys.executable, "-m", "pytest", "tests/e2e", "-v"]

    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    elapsed = time.time() - start_time

    print("=" * 80)
    print(f"Suite completed in {elapsed:.2f} seconds with exit code {result.returncode}")
    print("=" * 80)

    return result.returncode


if __name__ == "__main__":
    sys.exit(run_e2e_suite())

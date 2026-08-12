import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "-v", "tests/"],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)
print(f"\nExit code: {result.returncode}")
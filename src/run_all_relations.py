"""
Execute all three extraction scripts sequentially.
Assumes GraphDB is already running and accessible at GRAPHDB_ENDPOINT.
"""
import subprocess

scripts = ["src/distoken.py", "src/dirtoken.py", "src/topotoken.py"]

for script in scripts:
    print(f"[INFO] Running {script}")
    subprocess.run(["python3", script], check=True)
print("[INFO] All extractions completed.")
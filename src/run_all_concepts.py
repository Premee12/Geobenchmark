# Run All Geobenchmark Dataset Generators
import subprocess, os
scripts = ["atomicconcept.py", "dir_top.py", "dis_dir.py", "top_dis.py", "3concepts.py"]

SRC_DIR = os.path.join(os.path.dirname(__file__))
def run_script(script):
    script_path = os.path.join(SRC_DIR, script)
    if not os.path.exists(script_path):
        print(f"[WARN] Skipping {script} — file not found.")
        return
    print(f"\n[INFO] Running {script} ")
    try:
        subprocess.run(["python3", script_path], check=True)
        print(f"[DONE] {script} completed successfully.\n")
    except subprocess.CalledProcessError:
        print(f"[ERROR] {script} failed.\n")

def main():
    print(" GeoBenchmark Dataset Generation")
    for script in scripts:
        run_script(script)
    print(" All Generators Completed ")

if __name__ == "__main__":
    main()

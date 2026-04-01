import subprocess

def run(cmd):
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        print(f"--- Command: {cmd} ---")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return result.stdout.strip()
    except Exception as e:
        print(f"ERROR: {e}")
        return None

print("Checking Git status and branch...")
run("git rev-parse --abbrev-ref HEAD")
run("git branch")
run("git status")
run("git remote -v")

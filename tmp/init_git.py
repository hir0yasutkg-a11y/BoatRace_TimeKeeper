import subprocess

def run(cmd):
    try:
        print(f"Executing: {cmd}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        if result.stdout: print(result.stdout)
        if result.stderr: print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

# 1. Initialize git
run("git init")
# 2. Add files (respecting .gitignore)
run("git add .")
# 3. Create initial commit
run('git commit -m "Initial commit with PWA support"')

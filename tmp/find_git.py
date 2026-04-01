import os

def find_git_dirs(start_path):
    current = start_path
    found = []
    while True:
        git_path = os.path.join(current, ".git")
        if os.path.exists(git_path) and os.path.isdir(git_path):
            found.append(git_path)
        
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return found

start = r"c:\Users\hiroy\Documents\Antigravity_local"
dirs = find_git_dirs(start)
print(f"Found .git directories in parent hierarchy: {dirs}")

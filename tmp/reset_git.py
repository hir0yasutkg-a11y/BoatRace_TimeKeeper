import os
import shutil

# Target directory
target_dir = r"c:\Users\hiroy\Documents\Antigravity_local"
git_dir = os.path.join(target_dir, ".git")

def remove_readonly(func, path, excinfo):
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)

if os.path.exists(git_dir):
    try:
        print(f"Removing {git_dir}...")
        shutil.rmtree(git_dir, onerror=remove_readonly)
        print("Successfully removed .git directory.")
    except Exception as e:
        print(f"Error removing .git directory: {e}")
else:
    print(".git directory not found in the project folder.")

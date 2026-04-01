import shutil
import os

source = r"C:\Users\hiroy\.gemini\antigravity\brain\2a9252e0-f159-46b1-9928-92fbfbed3583\boatrace_pwa_icon_1775055032690.png"
dest = r"c:\Users\hiroy\Documents\Antigravity_local\web\public\icon-512.png"

try:
    shutil.copy2(source, dest)
    print(f"Successfully copied icon to {dest}")
except Exception as e:
    print(f"Error copying icon: {e}")

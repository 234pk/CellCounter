import os
import subprocess
import sys

def build():
    print("🚀 Starting Nuitka Build Process...")
    
    # Define the main entry point
    main_script = "main.py"
    
    if not os.path.exists(main_script):
        print(f"❌ Error: {main_script} not found!")
        return

    # Try to find a non-Windows Store Python
    python_exe = sys.executable
    if "WindowsApps" in python_exe:
        alternatives = [
            r"C:\Users\16500\AppData\Local\Programs\Python\Python312\python.exe",
            r"C:\Users\16500\AppData\Local\Programs\Python\Python310\python.exe"
        ]
        for alt in alternatives:
            if os.path.exists(alt):
                python_exe = alt
                print(f"🔄 Switched to alternative Python: {python_exe}")
                break

    # Nuitka command parameters
    cmd = [
        python_exe, "-m", "nuitka",
        "--standalone",
        "--show-progress",
        "--windows-console-mode=disable",
        "--plugin-enable=pyqt6",
        "--follow-imports",
        "--include-package=cv2",
        "--include-package=numpy",
        "--output-dir=build",
        "--onefile",
        "--mingw64",  # Force use of MinGW64
        "--assume-yes-for-downloads", # Automatically download missing compiler
        "main.py"
    ]
    
    print(f"📦 Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Build successful! You can find the EXE in the 'build' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    build()

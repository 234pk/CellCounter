import os
import subprocess
import sys

def build():
    print("🚀 Starting Nuitka macOS Build Process...")
    
    # Define the main entry point
    main_script = "main.py"
    
    if not os.path.exists(main_script):
        print(f"❌ Error: {main_script} not found!")
        return

    # Nuitka command parameters for macOS
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--macos-create-app-bundle",
        "--show-progress",
        "--plugin-enable=pyqt6",
        "--no-deployment-flag=self-test",
        "--follow-imports",
        "--include-package=cv2",
        "--include-package=numpy",
        "--output-dir=build",
        "main.py"
    ]
    
    print(f"📦 Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Build successful! App bundle created in 'build/main.app'.")
        print("💡 To create a DMG, you can use tools like 'create-dmg'.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    build()

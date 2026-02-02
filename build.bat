@echo off
echo Starting Nuitka Build...
python -m nuitka --standalone ^
    --show-progress ^
    --windows-console-mode=disable ^
    --plugin-enable=pyside6 ^
    --follow-imports ^
    --include-package=cv2 ^
    --include-package=numpy ^
    --output-dir=build ^
    --onefile ^
    --assume-yes-for-downloads ^
    main.py
echo Build finished. Check build directory.
pause

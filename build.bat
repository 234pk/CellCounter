@echo off
echo Starting Nuitka Build...
"C:\Users\16500\AppData\Local\Programs\Python\Python312\python.exe" -m nuitka --standalone ^
    --show-progress ^
    --windows-console-mode=disable ^
    --plugin-enable=pyside6 ^
    --follow-imports ^
    --include-package=cv2 ^
    --include-package=numpy ^
    --include-data-file=gui/translations.json=gui/translations.json ^
    --output-dir=build ^
    --onefile ^
    --assume-yes-for-downloads ^
    main.py
echo Build finished. Check build directory.
pause

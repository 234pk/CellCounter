import sys
import traceback

def exception_hook(exctype, value, tb):
    """Catch-all for exceptions to log them to a file in standalone mode"""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    print(error_msg)
    with open("crash_report.log", "a", encoding="utf-8") as f:
        f.write(f"\n--- CRASH AT {__import__('datetime').datetime.now()} ---\n")
        f.write(error_msg)
    sys.exit(1)

sys.excepthook = exception_hook

from gui.main_window import main

if __name__ == "__main__":
    try:
        main()
    except Exception:
        exception_hook(*sys.exc_info())

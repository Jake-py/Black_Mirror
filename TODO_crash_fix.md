# TODO: Fix Segmentation Fault on Scan (Threading Issue)

## Plan Steps:
1. [x] Analyze crash: Confirmed UI updates from worker thread
1. [x] Analyze crash: Confirmed UI updates from worker thread
2. [x] Update TODO
3. [x] Edit core/runner.py: Replace threading.Thread with QThread + progress/finished signals (fixed pyqtSignal → Signal as pyqtSignal)
4. [x] Edit ui/main_window.py: Connect runner signals instead of callbacks
5. [x] Edit main.py: Remove deprecated Qt.AA_* high DPI attributes
6. [ ] Test: `venv/bin/python main.py` - launch GUI
7. [ ] Test: `sudo venv/bin/python main.py` - scan without crash
8. [ ] Update TODO: Mark complete
9. [ ] attempt_completion

Current status: PySide6 import fixed, threading ready. Testing GUI launch and scan.

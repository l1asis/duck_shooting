import os, sys

if os.name != "nt" or sys.getwindowsversion()[0] < 6:
    pass
else:
    import ctypes
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
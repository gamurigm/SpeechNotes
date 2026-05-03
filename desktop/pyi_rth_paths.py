import sys
import os

# When running inside a PyInstaller bundle, the "backend" and "src" directories
# are at the top level of _MEIPASS. We need to register them as packages
# so that `from backend.xxx` imports work.
if getattr(sys, 'frozen', False):
    base = sys._MEIPASS
    for pkg in ('backend', 'src'):
        pkg_path = os.path.join(base, pkg)
        if os.path.isdir(pkg_path) and pkg_path not in sys.path:
            sys.path.insert(0, base)
            break

import ctypes
import os

libs = [
    "libdbus-1.so.3",
    "libEGL.so.1",
    "libGL.so.1",
    "libxkbcommon.so.0"
]

for lib in libs:
    try:
        ctypes.CDLL(lib)
        print(f"[OK] {lib} loaded")
    except OSError:
        print(f"[MISSING] {lib}")
        with open(os.path.join(os.environ["WACHTER_HOME"], "logs/startup_log.csv"), "a") as log:
            log.write(f"{lib},missing\n")

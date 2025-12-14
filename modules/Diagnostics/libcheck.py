import ctypes

libs = ["libGL.so.1", "libEGL.so.1", "libdbus-1.so.3", "libxkbcommon.so.0"]
for lib in libs:
    try:
        ctypes.CDLL(lib)
        print(f"[OK] {lib} loaded")
    except OSError:
        print(f"[MISSING] {lib}")

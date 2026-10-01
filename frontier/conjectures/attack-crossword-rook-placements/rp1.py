import ctypes, os, numpy as np
_lib = ctypes.CDLL(os.path.join(os.path.dirname(os.path.abspath(__file__)), "librp1.so"))
_lib.rp1.restype = ctypes.c_ulonglong
_lib.rp1.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
def rp(w):
    """w: 1-based permutation sequence"""
    n = len(w); arr = (ctypes.c_int * n)(*[x-1 for x in w])
    return _lib.rp1(n, arr)

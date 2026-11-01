"""Windows Job Object: closing/crashing the API also kills its heavy descendants."""
import ctypes
from ctypes import wintypes as w
import time


class Limits(ctypes.Structure):
    _fields_ = [("ProcessTime", ctypes.c_int64), ("JobTime", ctypes.c_int64), ("Flags", w.DWORD),
                ("MinWS", ctypes.c_size_t), ("MaxWS", ctypes.c_size_t), ("ActiveLimit", w.DWORD),
                ("Affinity", ctypes.c_size_t), ("Priority", w.DWORD), ("Scheduling", w.DWORD)]


class IO(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes", "OtherBytes")]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [("Basic", Limits), ("IO", IO), ("ProcessMemory", ctypes.c_size_t),
                ("JobMemory", ctypes.c_size_t), ("PeakProcess", ctypes.c_size_t), ("PeakJob", ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_int64) for name in ("User", "Kernel", "PeriodUser", "PeriodKernel")] + [
        (name, w.DWORD) for name in ("Faults", "Total", "Active", "Terminated")]


class ProcessGuard:
    def __init__(self, process):
        self.process = process
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        for name, args, restype in (
            ("CreateJobObjectW", [ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            ("SetInformationJobObject", [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            ("AssignProcessToJobObject", [w.HANDLE, w.HANDLE], w.BOOL),
            ("TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL),
            ("QueryInformationJobObject", [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            ("CloseHandle", [w.HANDLE], w.BOOL),
        ):
            fn = getattr(self.api, name); fn.argtypes = args; fn.restype = restype
        self.handle = self.api.CreateJobObjectW(None, None)
        info = ExtendedLimits(); info.Basic.Flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.handle or not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            self.close(); raise OSError("No se pudo reservar el proceso cancelable.")
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            self.close(); raise OSError("No se pudo proteger el proceso cancelable.")

    def close(self):
        if self.handle:
            self.api.TerminateJobObject(self.handle, 1)
            # Keep the heavy lock until every descendant has exited.
            accounting = Accounting()
            while self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
                if not accounting.Active:
                    break
                time.sleep(0.02)
            self.api.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

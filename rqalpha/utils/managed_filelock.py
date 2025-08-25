import os
from typing import Optional
from filelock import FileLock


class ManagedFileLock:
    def __init__(self, file: str, timeout: Optional[int] = None):
        self._lock_file = f"{file}.lock"
        self._lock = FileLock(self._lock_file)
        self._timeout = timeout

    def _cleanup(self):
        if os.path.exists(self._lock_file):
            try:
                os.remove(self._lock_file)
            except OSError:
                pass  # 忽略删除错误

    def __enter__(self):
        self._lock.acquire(timeout=self._timeout)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._lock.release()
        self._cleanup()
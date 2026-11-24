import os, time, threading, psutil

def _safe(fn, default=None):
    try: return fn()
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, OSError):
        return default   # الـ playbook: امسك AccessDenied ومتعملش crash

def proc_info(p):
    return {
        "pid": p.pid,
        "name": _safe(p.name),
        "exe": _safe(p.exe),
        "cmdline": _safe(p.cmdline, []),
        "parent_pid": _safe(p.ppid),
        "start_time": _safe(p.create_time),   # بجانب الـ PID بسبب إعادة استخدامه
    }

class ProcessMonitor:
    def __init__(self, store, interval=1.0):
        self.store, self.interval = store, interval
        self.known = set()          # (pid, start_time)
        self.prev_write = {}        # pid -> write_bytes
        self.top_writer = None      # أكتر برنامج كتب بيانات في آخر ثانية
        self._stop = False

    def start(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self): self._stop = True

    def _loop(self):
        first = True
        while not self._stop:
            best_pid, best_delta = None, 0
            for p in psutil.process_iter():
                key = (p.pid, _safe(p.create_time))
                if key not in self.known:
                    self.known.add(key)
                    if not first:   # أول لفة بس نسجل اللي موجود من غير ما نبعت أحداث
                        self.store.append({"schema_version": 1, "event_id": f"{time.time_ns()}",
                            "timestamp": time.time(), "event_type": "process",
                            "action": "started", "process": proc_info(p)})
                io = _safe(p.io_counters)
                if io:
                    delta = io.write_bytes - self.prev_write.get(p.pid, io.write_bytes)
                    self.prev_write[p.pid] = io.write_bytes
                    if delta > best_delta: best_pid, best_delta = p.pid, delta
            self.top_writer = best_pid
            first = False
            time.sleep(self.interval)

    def attribute(self, path):
        """ترجع (معلومات البرنامج, confidence)"""
        target = os.path.normcase(path)
        # 1) أقوى دليل: البرنامج فاتح الملف دلوقتي
        for p in psutil.process_iter():
            for f in _safe(p.open_files, []):
                if os.path.normcase(f.path) == target:
                    return proc_info(p), 0.9
        # 2) تخمين: أكتر برنامج بيكتب على الديسك الآن (ثقة ضعيفة)
        if self.top_writer:
            p = _safe(lambda: psutil.Process(self.top_writer))
            if p: return proc_info(p), 0.4
        return None, 0.0   # مش عارفين، وبنقول كده بصراحة
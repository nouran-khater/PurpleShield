import os, time, uuid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def __init__(self, store, procmon, cfg):
        self.store, self.procmon = store, procmon
        self.debounce = cfg["debounce_seconds"]
        self.ignore = [os.path.normcase(p) for p in cfg["self_ignore"]]
        self.last_modify = {}   # path -> آخر وقت سجلنا فيه Modify

    def _ignored(self, path):   # Self-Filter
        p = os.path.normcase(path)
        return any(p.startswith(i) for i in self.ignore)

    def on_any_event(self, ev):
        if ev.is_directory: return
        action = {"created": "created", "modified": "modified",
                  "deleted": "deleted", "moved": "moved"}.get(ev.event_type)
        if not action: return
        path = ev.src_path
        dest = getattr(ev, "dest_path", None) or None
        if self._ignored(path) or (dest and self._ignored(dest)): return

        now = time.time()
        if action == "modified":    # Debounce
            if now - self.last_modify.get(path, 0) < self.debounce: return
            self.last_modify[path] = now

        final = dest or path
        try: size = os.path.getsize(final)
        except OSError: size = None   # الملف اتمسح

        proc, conf = (None, 0.0) if action == "deleted" else self.procmon.attribute(final)
        if proc: proc["confidence"] = conf
        self.store.append({
            "schema_version": 1, "event_id": str(uuid.uuid4()), "timestamp": now,
            "event_type": "file", "action": action,
            "path": final, "old_path": path if dest else None,
            "filename": os.path.basename(final),
            "extension": os.path.splitext(final)[1].lower(), "size": size,
            "process": proc})

def start_file_monitor(store, procmon, cfg):
    obs = Observer()
    h = Handler(store, procmon, cfg)
    for p in cfg["watch_paths"]:
        obs.schedule(h, p, recursive=True)
    obs.start()
    return obs
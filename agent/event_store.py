import json, os, threading, time

class JsonlEventStore:
    """append: يضيف حدث | query: يقرا أحداث | rotation: يقفل الملف لما يكبر"""
    def __init__(self, path, rotate_mb=5):
        self.path = path
        self.rotate_bytes = rotate_mb * 1024 * 1024
        self.lock = threading.Lock()   # عشان أكتر من Thread يكتبوا من غير ما يتلخبطوا
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def _rotate_if_needed(self):
        if os.path.exists(self.path) and os.path.getsize(self.path) >= self.rotate_bytes:
            os.rename(self.path, self.path.replace(".jsonl", f".{int(time.time())}.jsonl"))

    def append(self, event: dict):
        with self.lock:
            self._rotate_if_needed()
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def query(self, event_type=None, since=None, limit=None):
        results = []
        if not os.path.exists(self.path):
            return results
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                e = json.loads(line)
                if event_type and e["event_type"] != event_type: continue
                if since and e["timestamp"] < since: continue
                results.append(e)
        return results[-limit:] if limit else results
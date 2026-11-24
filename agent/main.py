import time, psutil
from agent.config import load_config
from agent.event_store import JsonlEventStore
from agent.process_monitor import ProcessMonitor
from agent.file_monitor import start_file_monitor

cfg = load_config()
store = JsonlEventStore(cfg["log_path"], cfg["rotate_mb"])
procmon = ProcessMonitor(store)
procmon.start()
observer = start_file_monitor(store, procmon, cfg)
print("PurpleShield agent running. Ctrl+C to stop.")

me = psutil.Process()
me.cpu_percent(None)
try:
    while True:
        time.sleep(30)
        print(f"[baseline] CPU={me.cpu_percent(None):.1f}%  RAM={me.memory_info().rss/1024/1024:.0f} MB")
except KeyboardInterrupt:
    observer.stop(); procmon.stop(); observer.join()
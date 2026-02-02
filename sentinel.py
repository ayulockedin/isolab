import time
import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tracer import ExecutionTracer
from healer import get_fix_from_local_brain

# CONFIGURATION
TARGET_FILE = "target.py"

class HealingHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_run = 0
        self.is_healing = False 

    def on_modified(self, event):
        if not event.src_path.endswith(TARGET_FILE):
            return
        
        if time.time() - self.last_run < 1.0:
            return
        
        if self.is_healing:
            return

        self.last_run = time.time()
        print(f"\n[SENTINEL] Detected change in {TARGET_FILE}. Scanning...")
        
        tracer = ExecutionTracer()
        report = tracer.run_script(TARGET_FILE)
        
        if report["status"] == "success":
            print("[SENTINEL] Integrity Check Passed.")
        else:
            print(f"[SENTINEL] FAILURE DETECTED: {report['error_log'].splitlines()[-1]}")
            self.activate_healer(report)

    def activate_healer(self, report):
        print("[SENTINEL] Deploying Healer...")
        self.is_healing = True 
        
        try:
            with open(TARGET_FILE, "r") as f:
                broken_code = f.read()
            
            # Consult Llama 3
            fixed_code = get_fix_from_local_brain(broken_code, report["trace_history"], report["error_log"])
            
            # Verify before applying
            test_file = "target_v2.py"
            with open(test_file, "w") as f:
                f.write(fixed_code)
                
            verifier = ExecutionTracer()
            verify_report = verifier.run_script(test_file)
            
            if verify_report["status"] == "success":
                print("[SENTINEL] Fix Verified. Applying patch...")
                with open(TARGET_FILE, "w") as f:
                    f.write(fixed_code)
                print("[SENTINEL] Codebase Repaired.")
            else:
                # NEW: PRINT THE REASON FOR FAILURE
                print("[SENTINEL] Auto-Fix Failed. The AI code crashed during verification.")
                print("--- AI ERROR LOG ---")
                print(verify_report["error_log"])
                print("--------------------")
                
            if os.path.exists(test_file):
                os.remove(test_file)
                
        except Exception as e:
            print(f"[SENTINEL] Critical Error: {e}")
        finally:
            time.sleep(1)
            self.is_healing = False

def start_sentinel():
    print(f"[SENTINEL] Watching {TARGET_FILE} for corruption...")
    print("   (Press Ctrl+C to stop)")
    
    event_handler = HealingHandler()
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_sentinel()
import sys
import json
import traceback

class ExecutionTracer:
    def __init__(self):
        self.history = []
        self.error = None

    def trace_calls(self, frame, event, arg):
        if event != 'line':
            return self.trace_calls
        
        line_no = frame.f_lineno
        local_vars = {}
        # Capture variables safely
        for var_name, var_val in frame.f_locals.items():
            if not var_name.startswith("__"):
                try:
                    local_vars[var_name] = str(var_val)
                except:
                    local_vars[var_name] = "<unprintable>"

        self.history.append({
            "line": line_no,
            "variables": local_vars
        })
        return self.trace_calls

    def run_script(self, script_path):
        with open(script_path, 'r') as f:
            code = f.read()

        try:
            compiled_code = compile(code, script_path, 'exec')
        except SyntaxError as e:
            return {
                "status": "syntax_error",
                "trace_history": [],
                "error_log": f"Syntax Error: {e}"
            }

        sys.settrace(self.trace_calls)
        try:
            # CRITICAL FIX: execution context must be __main__
            # This ensures if __name__ == "__main__": blocks actually run
            global_context = {"__name__": "__main__"}
            # NEW (Fixed)
            # We pass the same dictionary for globals AND locals to emulate a real module
            exec(compiled_code, global_context, global_context)
            status = "success"
        except Exception:
            sys.settrace(None)
            status = "runtime_error"
            self.error = traceback.format_exc()
        finally:
            sys.settrace(None)

        return {
            "status": status,
            "trace_history": self.history,
            "error_log": self.error
        }

if __name__ == "__main__":
    # Test itself
    tracer = ExecutionTracer()
    # Create a dummy file to test the fix
    with open("test_main.py", "w") as f:
        f.write("if __name__ == '__main__':\n    raise ValueError('It Works')")
    
    report = tracer.run_script("test_main.py")
    print("Test Result:", report["status"]) # Should say 'runtime_error'
import os
import json
import requests
import re
from tracer import ExecutionTracer

# CONFIGURATION
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3" 

def extract_code(text):
    pattern = r"```(?:python)?\s*(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def get_fix_from_local_brain(code, trace, error):
    # DETECT MODE
    if "NotImplementedError" in error:
        mode = "GENERATOR"
        instruction = """
        [TASK]
        The user wants you to IMPLEMENT the function that raised NotImplementedError.
        1. Read the comments in the function to understand the goal.
        2. Write the complete function implementation.
        3. Output the FULL executable file code (including the if __name__ == "__main__" block).
        """
    else:
        mode = "DEBUGGER"
        instruction = """
        [TASK]
        Fix the runtime crash.
        1. Analyze the trace and error.
        2. Modify the code to fix the bug.
        3. Output the FULL executable file code.
        """

    prompt = f"""
    You are a backend Python Coding Engine.
    
    [INPUT SOURCE]
    ```python
    {code}
    ```
    Error: {error}
    
    {instruction}
    
    [STRICT OUTPUT RULES]
    1. Output ONLY valid Python code.
    2. Enclose code in ```python ... ``` blocks.
    3. NO explanations. NO conversational text.
    """
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2 
        }
    }
    
    try:
        print(f"   ... Sending Request to {MODEL_NAME}")
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        
        result_json = response.json()
        raw_text = result_json.get("response", "")
        return extract_code(raw_text)

    except requests.exceptions.ConnectionError:
        raise ConnectionError("Could not connect to Ollama.")

# (Main function remains mostly the same, useful for manual testing)
def main():
    target_file = "target.py"
    tracer = ExecutionTracer()
    report = tracer.run_script(target_file)
    
    if report["status"] != "success":
        print(f"[HEALER] Crash: {report['error_log'].splitlines()[-1]}")
        with open(target_file, "r") as f:
            broken_code = f.read()
        fixed_code = get_fix_from_local_brain(broken_code, report["trace_history"], report["error_log"])
        
        # Verify
        test_file = "target_v2.py"
        with open(test_file, "w") as f:
            f.write(fixed_code)
        verifier = ExecutionTracer()
        if verifier.run_script(test_file)["status"] == "success":
            with open(target_file, "w") as f:
                f.write(fixed_code)
            print("[HEALER] Success.")
        else:
            print("[HEALER] Failed.")
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    main()
import subprocess
import sys

def main():
    print("Starting Uvicorn server...")
    try:
        # Run uvicorn and capture its output
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(f"UVICORN: {line}", end="")
            
        process.wait()
        print(f"Uvicorn exited with code: {process.returncode}")
        
    except Exception as e:
        print(f"Failed to start server: {e}")

if __name__ == "__main__":
    main()

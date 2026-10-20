"""
Application Runner Script
-----------------------
This script is used to start the EnCompliance backend application in development mode.
It provides:
- Uvicorn server configuration
- Development server settings
- Hot reloading for development
- Port and host configuration
- Logging setup
"""

import os
import sys
import signal
import subprocess
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run the server in a way that allows for clean shutdowns with Ctrl+C"""
    # Get settings from environment
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    # Build the command for Uvicorn
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        f"--host={host}", 
        f"--port={port}", 
        "--reload",
        "--workers=1"
    ]
    
    print(f"Starting server on port {port} with hot reload.")
    print("Press Ctrl+C to stop all server processes.")
    
    try:
        # Start Uvicorn as a subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Forward output from Uvicorn to our console
        while process.poll() is None:
            line = process.stdout.readline()
            if line:
                print(line, end='')
                
    except KeyboardInterrupt:
        # On Ctrl+C, terminate the subprocess and its children
        print("\nStopping server...")
        
        # Try a gentle termination first
        try:
            process.terminate()
            # Give it some time to terminate gracefully
            for _ in range(10):
                if process.poll() is not None:
                    break
                # Wait a bit
                time.sleep(0.1)
        except:
            pass
            
        # If still running, force kill
        if process.poll() is None:
            try:
                process.kill()
            except:
                pass
            
    finally:
        print("Server has been stopped.")

if __name__ == "__main__":
    main() 
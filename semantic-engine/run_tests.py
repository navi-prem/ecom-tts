#!/usr/bin/env python3
"""Test script that starts server and tests endpoints"""

import subprocess
import time
import sys
import signal
import os

def start_server():
    """Start the FastAPI server"""
    print(">>> Starting FastAPI server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "warning"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/Users/bharath.sanjeevi/codes/CARA"
    )
    
    # Wait for server to start
    time.sleep(5)
    
    return process

def run_tests():
    """Run the test script"""
    print(">>> Running tests...")
    result = subprocess.run(
        [sys.executable, "test_endpoints.py"],
        cwd="/Users/bharath.sanjeevi/codes/CARA"
    )
    return result.returncode

def main():
    server_process = None
    try:
        # Start server
        server_process = start_server()
        
        # Run tests
        exit_code = run_tests()
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n>>> Interrupted by user")
        return 1
    finally:
        if server_process:
            print(">>> Stopping server...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    sys.exit(main())

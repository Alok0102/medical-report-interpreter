import subprocess
import sys
import time
import os

def run_services():
    processes = []
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 60)
    print("           AetherMed Workspace Service Launcher")
    print("=" * 60)
    
    try:
        # 1. Start the MCP Server on Port 8001
        print("[System] Launching local MCP Server on port 8001...")
        mcp_proc = subprocess.Popen(
            [sys.executable, "mcp_server/server.py"],
            cwd=current_dir
        )
        processes.append(mcp_proc)
        
        # 2. Start the FastAPI Backend on Port 8000
        print("[System] Launching FastAPI Backend on port 8000...")
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=current_dir
        )
        processes.append(backend_proc)
        
        # 3. Start the Frontend Simple HTTP Server on Port 8080
        print("[System] Serving Frontend UI on port 8080...")
        frontend_proc = subprocess.Popen(
            [sys.executable, "-m", "http.server", "8080", "--directory", "frontend"],
            cwd=current_dir
        )
        processes.append(frontend_proc)
        
        print("\n[Status] All services launched successfully!")
        print(" -> Access web dashboard at: http://localhost:8080")
        print(" -> Press Ctrl+C to terminate all services.\n")
        
        # Keep launcher alive and monitor processes
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"\n[Warning] One of the servers terminated unexpectedly (exit code {p.returncode}).")
                    raise KeyboardInterrupt
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[System] Shutting down all services gracefully...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                p.kill()
        print("[System] Shutdown complete. Goodbye!")

if __name__ == "__main__":
    # Ensure dependencies are running inside workspace directory context
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_services()

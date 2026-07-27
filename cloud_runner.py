import time
import subprocess
import sys
from datetime import datetime

def cloud_daemon_monitor():
    """
    Cloud Daemon Runner: Ensures the quantum multi-agent system 
    restarts automatically and runs continuously 24/7 without human intervention.
    """
    print("==================================================")
    print("☁️ Initializing Autonomous Cloud Daemon (24/7 Mode)")
    print("==================================================")
    
    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] 🚀 Launching Quantum Engine Core...")
            
            # Spawn the main quantum engine process
            process = subprocess.Popen([sys.executable, "main.py"])
            
            # Keep monitoring the process
            process.wait()
            
            print(f"[{timestamp}] ⚠️ Core process stopped. Restarting in 5 seconds...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("🛑 Cloud Daemon safely terminated by user.")
            break
        except Exception as e:
            print(f"❌ Daemon Exception: {e}")
            time.sleep(10)

if __name__ == "__main__":
    cloud_daemon_monitor()
          

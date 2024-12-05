import subprocess 
import time

# List of scripts to run
scripts = [
    "market_analyst_XRPUSDT.py",
    "market_analyst_SOLUSDT.py",
    "market_analyst_ETHUSDT.py",
    "market_analyst_BTCUSDT.py",
    "market_analyst_BNBUSDT.py"
]

# Start each script in a separate process
processes = []
for script in scripts:
    process = subprocess.Popen(["python", script])
    processes.append(process)
    time.sleep(7) # Wait for 5 seconds before starting the next script

# Optionally, wait for all processes to complete
for process in processes:
    process.wait()
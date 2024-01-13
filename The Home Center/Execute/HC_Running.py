import multiprocessing
import subprocess

# Function to run a Python script using subprocess
def run_script(script):
    subprocess.call(['python', script])

if __name__ == '__main__':

    # List of scripts to be executed concurrently
    scripts = ['MQTT_Windows_HC', 'CoAP_Windows_HC.py'] # Replace with your own file names and ensure they are in the same directory

    # Create a list of multiprocessing.Process objects for each script
    processes = [multiprocessing.Process(target=run_script, args=(script,)) for script in scripts]

    # Start all processes
    for process in processes:
        process.start()
    
    # Wait for all processes to finish
    for process in processes:
        process.join()

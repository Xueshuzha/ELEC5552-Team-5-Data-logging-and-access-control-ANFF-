import os
import time
import pexpect
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define your local directory and remote server details
local_dir = "/home/pi/logData"
remote_user = "tomgreenland"
remote_host = "172.20.10.3"
remote_dir = "C:/Apache24/htdocs/logdata"
remote_password = "3005"

# Define a function to perform the SCP transfer
def perform_scp(file_path):
    try:
        # Create an SCP command
        scp_command = f"scp {file_path} {remote_user}@{remote_host}:{remote_dir}"

        # Use pexpect to automate password entry
        child = pexpect.spawn(scp_command, timeout=None)

        # Define a function to print output in real-time
        def print_output(child):
            while True:
                index = child.expect(["password:", pexpect.EOF, pexpect.TIMEOUT], timeout=None)
                if index == 0:
                    print("Password prompt detected. Entering password...")
                    child.sendline(remote_password)
                    print("Password entered.")
                elif index == 1:
                    print(child.before.decode())  # Print the output before EOF
                    print(f"File {file_path} copied to remote server.")
                    break
                elif index == 2:
                    break  # Handle timeout

        print_output(child)

    except Exception as e:
        print(f"Error: {str(e)}")

# Define a custom event handler to watch for file creation
class MyHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        print(f"New file created: {event.src_path}")
        perform_scp(event.src_path)

if __name__ == "__main__":
    # Create an observer to watch the local directory
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=local_dir, recursive=False)
    observer.start()

    print(f"Watching directory: {local_dir}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

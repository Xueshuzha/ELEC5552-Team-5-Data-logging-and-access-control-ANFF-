# to determine run time of script
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from digi.xbee.devices import XBeeDevice

start_time = time.time()


PORT = "COM3"
BAUD_RATE = 19200

xbee = XBeeDevice(PORT, BAUD_RATE)

REMOTE_NODE_ID = '1'

device = XBeeDevice(PORT, BAUD_RATE)
device.open()

xbee_network = device.get_network()
remote_device = xbee_network.discover_device(REMOTE_NODE_ID)

def log_files(folder_path):
    file_names = [] 
    #searches through folder extracting filenames for .log type files
    for file_name in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, file_name)):
            if file_name.endswith(".log"):
                file_names.append(file_name)
    return file_names

def cached_files():
    #reads cache txt files and stores the filenames
    with open("cache.txt", 'r') as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines]
        return lines
    
def new_log_files(cached_file_names, file_names):
    #checks if file is in the folder and not in Cache text file indicating it is new and requires analysing
    log_files_to_analyse = [file for file in file_names if file not in cached_file_names]
        # Remove filenames from cache.txt that are no longer in the folder
    removed_files = [file for file in cached_file_names if file not in file_names]
    
    # Update the cache.txt file to remove the deleted filenames
    with open("cache.txt", "r") as cache_file:
        lines = cache_file.readlines()
    
    with open("cache.txt", "w") as cache_file:
        for line in lines:
            if line.strip() not in removed_files:
                cache_file.write(line)
    
    return log_files_to_analyse


def extract_data(log_file_path):

    data_columns = {}  # To store data columns with header as key
    headers = []  # To store header names

    cleaning_status = False # If specified Cleaning in File will change to True

    # Open the log file for reading
    with open(log_file_path, 'r', encoding='ISO-8859-1') as log_file:

        found_data_start = False

        # Read the file line by line
        for line in log_file:
            elements = line.strip().split('\t') # Strip whitespace and split by tab

            if not found_data_start:
                if elements[0] == "Recipe: StandardCleaning.rcp":
                    cleaning_status = True   
                    
                if "time (ms)" in elements:   #fix this to not rely on time (ms) 
                    headers = elements
                    for header in headers:
                        data_columns[header] = []  # Initialize empty list for each header
                    found_data_start = True

            else:
                # Check if the line starts with numeric values
                if elements[0].replace('.', '', 1).isdigit():
                    for header, value in zip(headers, elements):
                        if header not in data_columns:
                            data_columns[header] = []  # Initialize empty list for each header
                        data_columns[header].append(value)

    return data_columns,cleaning_status

def calculate_time_on(data_columns):

    #process time calculation - added robustness the machine power can reach 0 within the run 

    power_on_index = []

    # determine index of when power is on
    for i in range(len(data_columns['ICP power (W)'])):
        value = data_columns['ICP power (W)'][i]
        if float(value) > 0.0:
            power_on_index.append(i)

    #create time span list
    time_span_values = []

    for i in range(len(data_columns['time (ms)'])-1):
        span_end = float(data_columns['time (ms)'][i+1])
        span_start = float(data_columns['time (ms)'][i])
        time_span = span_end - span_start
        time_span_values.append(time_span)

    #use time span and power on indexes to calculate time on
    total_time_on = 0

    for i in power_on_index:
        if i == 0:     # account for edge case where machine is on when .log file starts
            right_span = float((time_span_values[i] / 2))
            time_on = right_span
        elif i == (len(data_columns['time (ms)'])-1):  # account for edge case where machine is on when .log file ends (power cut)
            left_span = float((time_span_values[i-1] / 2))
            time_on = left_span
        else:
            left_span = float((time_span_values[i-1] / 2))
            right_span = float((time_span_values[i] / 2))
            time_on = left_span + right_span

        total_time_on += time_on

    return total_time_on


def Calculate_Average_AVG_ICP_Powr(data_columns):

    #Calculate average ICP Power (for values > 0 only)
    ICP_power_list = []

    for value in data_columns['ICP power (W)']:
        value = float(value)
        if value > 0:
            ICP_power_list.append(value)

    if ICP_power_list:  #prevent divide by zero error 
        AVG_ICP_Power = float(sum(ICP_power_list)) / float(len(ICP_power_list))
    else:
        AVG_ICP_Power = 0

    return AVG_ICP_Power



def extract_parameters(data_columns, cleaning_status):
    Penning_pr_t0 = data_columns['Penning pr. (Pa)'][0]   # assuming log starts at t= 0
    MSK_t0 = data_columns['MSK (Pa)'][0]
    Penning_pr_tmax = data_columns['Penning pr. (Pa)'][-1]
    MSK_tmax = data_columns['MSK (Pa)'][-1]

    #if no data available add N/D (no data) as user may view blank space as a transmission issue
    if Penning_pr_t0 == '':
        Penning_pr_t0 = "N/D"
    if Penning_pr_tmax == '':
        Penning_pr_tmax = "N/D"

    total_time_on = calculate_time_on(data_columns)

    AVG_ICP_Power = Calculate_Average_AVG_ICP_Powr(data_columns)

    return cleaning_status ,total_time_on, AVG_ICP_Power, Penning_pr_t0, Penning_pr_tmax, MSK_t0,MSK_tmax


def main():
    # log_file_path = os.path.dirname(os.path.abspath(__file__))

    log_file_path = r'C:\Users\galna\OneDrive\Documents\Uni\Masters Sem2\Design\USB Data Logger Module'
    file_names = log_files(log_file_path)
    cached_file_names = cached_files()
    log_files_to_analyse = new_log_files(cached_file_names, file_names)

    for name in log_files_to_analyse:
        try:
            data_columns,cleaning_status = extract_data(name)
            cleaning_status ,total_time_on, AVG_ICP_Power, Penning_pr_t0, Penning_pr_tmax, MSK_t0,MSK_tmax = extract_parameters(data_columns,cleaning_status)

            transmit_data = (str(cleaning_status) + " " + str(total_time_on) + " " + str(AVG_ICP_Power)  + " " 
                             + str(Penning_pr_t0) + " " + str(Penning_pr_tmax) + " "+ str(MSK_t0) + " " + str(MSK_tmax))
        
            device.send_data(remote_device, transmit_data)

            print("_"*60)
                
            print("cleaning_status = ", cleaning_status)

            print("total_time_on = ", total_time_on)
            print("AVG_ICP_Power = ", AVG_ICP_Power)

            print("Penning_pr_t0 = ", Penning_pr_t0)
            print("Penning_pr_tmax = ", Penning_pr_tmax)

            print("MSK_t0 = ", MSK_t0)
            print("MSK_tmax = ", MSK_tmax)

            print("_" * 60)

            # with open("output.txt", "w") as file:
            #     file.write("_" * 60 + "\n")
            #     file.write("file name = " + str(name) + "\n")
            #     file.write("_" * 60 + "\n")
            #     file.write("cleaning_status = " + str(cleaning_status) + "\n")
            #     file.write("total_time_on = " + str(total_time_on) + "\n")
            #     file.write("AVG_ICP_Power = " + str(AVG_ICP_Power) + "\n")
            #     file.write("Penning_pr_t0 = " + str(Penning_pr_t0) + "\n")
            #     file.write("Penning_pr_tmax = " + str(Penning_pr_tmax) + "\n")
            #     file.write("MSK_t0 = " + str(MSK_t0) + "\n")
            #     file.write("MSK_tmax = " + str(MSK_tmax) + "\n")
            #     file.write("_" * 60 + "\n")

            transmit_data = (str(cleaning_status) + " " + str(total_time_on) + " " + str(AVG_ICP_Power)  + " " + str(Penning_pr_t0) + " " + str(Penning_pr_tmax) + " "+ str(MSK_t0) + " " + str(MSK_tmax))
        
            device.send_data(remote_device, transmit_data)


            # with open("cache.txt", "a") as file:
            #     file.write(str(name) + "\n")

        except Exception as e:
            error_message = f"Error analyzing file {name}: {str(e)}"
            print(error_message)
            with open("output.txt", "w") as error_log_file:
                error_log_file.write(error_message + "\n")

class LogFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".log"):
            print(f"New log file added: {event.src_path}")
            main()  # Run your analysis when a new log file is added
            
if __name__ == "__main__":
    print("running")
    # folder_path = os.path.dirname(os.path.abspath(__file__))
    folder_path = r'C:\Users\galna\OneDrive\Documents\Uni\Masters Sem2\Design\USB Data Logger Module'
    # print(folder_path)
    
    # Set up the watchdog observer
    event_handler = LogFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=folder_path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

print("Process finished --- %s millseconds ---" % ((time.time() - start_time) * 1000))
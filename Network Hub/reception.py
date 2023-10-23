import datetime
import shutil
import time
import serial

ser = serial.Serial('/dev/ttyS0', 19200)

#intialise default name
RS232_file_name = "default.txt"
RS232_status = False 

def data_sorting(data):

    global RS232_file_name
    global RS232_status

    current_datetime = datetime.datetime.now()

    #change to pi data log folder path
    path = "/home/pi/logData/" 

    date_time_str = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")

    file_A = path + "USB_Data_Logger_" + date_time_str + ".txt"

    data_split = data.split(" ")  
    print(data_split)
    if len(data_split) > 1:
        if data_split[0] == 'A':
            None
        elif data_split[0] == 'B':
            None
        else:
            data_split.pop(0)
    print(data_split)
    if data_split[0] == 'A': 
        with open(file_A, "w") as f_A:
                f_A.write("USB Data Logger " + date_time_str + '\n')
                f_A.write('\n')
                f_A.write("cleaning_status = " + data_split[1] + '\n')
                f_A.write("total_time_on = " + data_split[2] + '\n')
                f_A.write("AVG_ICP_Power = " + data_split[3] + '\n')
                f_A.write("Penning_pr_t0 = " + data_split[4] + '\n')
                f_A.write("Penning_pr_tmax = " + data_split[5] + '\n')
                f_A.write("MSK_t0 = " + data_split[6] + '\n')
                f_A.write("MSK_tmax = " + data_split[7] + '\n')
                f_A.close()

    elif data_split[0] == 'B':
        #print(data_split)
        if data_split[1] == "end":
            RS232_status = False
            with open(RS232_file_name, "a") as f_B:
                f_B.close()
            source = RS232_file_name

            destination = path + RS232_file_name

            shutil.move(source, destination)

        elif not RS232_status :
            RS232_status = True
            RS232_file_name = "RS232_" + date_time_str + ".txt"
            with open(RS232_file_name, "w") as f_B:

                f_B.write(RS232_file_name[:-4] + '\n' +'\n')

                f_B.write('Density' + '\t' + 'Tooling' + '\t' + 'Z-ratio' + '\t' + 'Rate' + '\t' + 'Thickness' + '\n')

                f_B.write(data_split[1] + '\t' + data_split[2] + '\t' + data_split[3] + '\t' + data_split[4] + '\t' + data_split[5]  + '\n')

        elif RS232_status:
            with open(RS232_file_name, "a") as f_B:
                f_B.write(data_split[1] + '\t' + data_split[2] + '\t' + data_split[3] + '\t' + data_split[4] + '\t' + data_split[5]  + '\n')
        
        else:
            print("weird")
            None


try:
    while True:
        
        data = ser.readline().decode('iso-8859-1').strip()
        #ser.flushInput()
        #print(data)
        data_sorting(data)
        
except KeyboardInterrupt:
    ser.close()
     
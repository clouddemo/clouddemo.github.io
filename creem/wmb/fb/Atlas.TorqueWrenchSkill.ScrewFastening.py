import ast
import csv
import json
import os
import socket
import sys
import time
from array import array

CSV_PATH = '/home/siemens/workspace/danfoss_atlas_wrench_datalog.csv'
HEADER_LIST = ['Time Stamp', 'Parameter Set ID', 'Tightening Status', 'Torque', 'Angle']
RECV_DATA_LENGTH = 1024
TIME_OUT_ATLAS = 50
RETRY_COUNTER = 5
IP_DEFAULT = "192.168.1.98"
PORT_DEFAULT = 4545

# atlas application message ID
MID0001_COMM_START      = '00200001003000000000'  # Application Communication start
MID0003_COMM_STOP       = '00200003001000000000'  # Application Communication stop
MID0018_SELECT_PSET     = '00230018001000000000'  # Select Parameter set (header+ID)
MID0040_TOOL_DATA       = '00200040002000000000'  # Tool data upload request
MID0060_TIGHT_RESU_SUBS = '00200060001100000000'  # Last tightening result data subscribe
MID9999_KEEP_ALIVE      = '00209999000000000000'  # Keep alive open protocol communication

MID0061_TIGHT_RESU_CODE = '0061'  # Last tightening result data
MID0004_NEG_ACK_CODE    = '0004'  # Application Communication negative acknowledge
MID9999 = '9999'
KEEP_ALIVE_TIME_MAX     = 10
KEEP_ALIVE_RECV_DELAY   = 4
MID_CMD_SEND_DELAY      = 1

# byte number of MID9999 receive data
HEADER_MID_START   = 4
HEADER_MID_END     = 8
DATA_MID_START     = 25
DATA_MID_END       = 29
PARA_SET_ID_START  = 111
PARA_SET_ID_END    = 113
TIGHT_STATUS_START = 128
TIGHT_STATUS_END   = 129
TORQUE_START       = 161
TORQUE_END         = 167
ANGLE_START        = 190
ANGLE_END          = 195
TIME_STAMP_START   = 197
TIME_STAMP_END     = 216
PSET_DICT_DEFAULT = '{"Pset":"002"}'

#TODO IP, Port shall be refactored to read from _device
#Input Port: pset
def SPIDR_FB_Main(IP, Port, pset):

    #TODO This part shall be refactored to SPIDR implementation
    ip_socket = IP
    port_socket = int(Port)

    pset_dict["Pset"] = pset

    client = AtlasClient(ip_socket, port_socket)
    client.start_comm()
    client.select_pset(pset_dict)
    client.tighten_result_subscribe()
    time.sleep(4)
    data = client.keep_alive()
    time.sleep(2)

    if len(data) < 1 or data is None:
        print("- ERROR: read atlas tightening resule data error")
    else:
        print("- OK: log data")
        check_log_file()
        print("- KK: log data 1111")
        log_data(data)

    client.stop_comm()

    status = 0x00000000

    #Output Port: status
    return (status)

def check_log_file():
    print("- check log file existed or setup a new csv file")

    # check the csv file and write the header
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w', encoding='utf-8') as f:
            header = HEADER_LIST
            csvwriter = csv.writer(f)
            csvwriter.writerow(header)
            f.close

def log_data(recv_data):
    print("- log data start")
    print("- input data: %s, type: %s" % (recv_data, type(recv_data)))

    # data extraction
    time_stamp_recv        = recv_data[TIME_STAMP_START : TIME_STAMP_END]
    parameter_set_id_recv  = recv_data[PARA_SET_ID_START : PARA_SET_ID_END]
    tightening_status_recv = recv_data[TIGHT_STATUS_START : TIGHT_STATUS_END]
    torque_recv            = recv_data[TORQUE_START : TORQUE_END]
    angle_recv             = recv_data[ANGLE_START : ANGLE_END]
    
    data_log = [time_stamp_recv, parameter_set_id_recv, tightening_status_recv, 
                torque_recv, angle_recv]

    # write data to csv file
    with open (CSV_PATH, 'a', encoding='utf-8', newline='') as f:
        csvwriter = csv.writer(f)
        csvwriter.writerow(data_log)
        f.close
    print("- log data to csv file")
    #return ()


#@singleton
class AtlasClient(object):
    def __init__(self, ip=IP_DEFAULT, port =PORT_DEFAULT):
        counter = RETRY_COUNTER
        while counter > 0:
            counter -= 1
            try:
                self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except socket.error as msg:
                self.sk = None
                continue

            try:
                self.sk.connect((ip, port))
                print("--socket connect")
                self.sk.settimeout(TIME_OUT_ATLAS)
            except socket.error as msg:
                self.sk.close()
                self.sk = None
                continue
            break

    def start_comm(self):
        mid_send = MID0001_COMM_START + chr(0)
        counter = RETRY_COUNTER
        while counter > 0:
            counter -= 1
            try:
                self.sk.sendall(mid_send.encode())
                print("--socket start communication")
                data = self.sk.recv(RECV_DATA_LENGTH)
                data = data.decode()
                print("- start comm recv data: %s type: %s" % (data, type(data)))
                mid_recv = data[HEADER_MID_START : HEADER_MID_END]
                print("- mid0001 feedback mid code", mid_recv)
                if data is None :
                    print("- ERROR: start communicaton feedback error", mid_recv)
                    #return None
                #return data.decode('utf-8')
            except socket.error as msg:
                print(msg)
                continue
            break

    def select_pset(self, pset_dict):
        pset_dict = json.loads(pset_dict)
        mid_send = MID0018_SELECT_PSET + pset_dict["Pset"] + chr(0)
        counter = RETRY_COUNTER
        while counter > 0:
            counter -= 1
            try:
                self.sk.sendall(mid_send.encode())
                print("--socket select pset")
                data = self.sk.recv(RECV_DATA_LENGTH)
                data = data.decode()
                print("- select pset recv data: %s" % data)
                mid_recv = data[HEADER_MID_START : HEADER_MID_END]
                print("- mid0001 feedback mid code", mid_recv)
                if len(data) < 1 or data is None:
                    #return None
                    print("- ERROR: select pset feedback error", mid_recv)
            except socket.error as msg:
                print(msg)
                continue
            break

    def tighten_result_subscribe(self):
        mid_send = MID0060_TIGHT_RESU_SUBS + chr(0)
        counter = RETRY_COUNTER
        while counter > 0:
            counter -= 1
            try:
                self.sk.sendall(mid_send.encode())
                print("--socket tighten resulte subscribe")
                data = self.sk.recv(RECV_DATA_LENGTH)
                data = data.decode()
                print("- select tighten recv data: %s" % data)
                mid_recv = data[HEADER_MID_START : HEADER_MID_END]
                print("- mid0001 feedback mid code", mid_recv)
                if len(data) < 1 or data is None:
                    #return None
                    print("- ERROR: tighten subscribe feedback error", mid_recv)
                #self.keep_alive()
            except socket.error as msg:
                print(msg)
                continue
            break

    def keep_alive(self):
        mid_send = MID9999_KEEP_ALIVE + chr(0)
        counter = RETRY_COUNTER
        keep_alive_time = KEEP_ALIVE_TIME_MAX
        mid_recv = "9999"

        while counter > 0:
            counter -= 1
            try:
                while (mid_recv != MID0061_TIGHT_RESU_CODE):
                    keep_alive_time -= 1
                    self.sk.sendall(mid_send.encode())
                    time.sleep(KEEP_ALIVE_RECV_DELAY)
                    print("- keep alive loop start")

                    data = self.sk.recv(RECV_DATA_LENGTH)
                    print("- mid9999 feedback data: %s, type: %s" % (data, type(data)))
                    data = data.decode()
                    if len(data) < 1 or data is None:
                        print("- ERROR: tighten subscribe feedback error", mid_recv)
                        return None					
					
                    mid_recv = data[DATA_MID_START : DATA_MID_END]
                    print("- mid_recv[25:29]: %s, type: %s" % (mid_recv, type(mid_recv)))        
                    if (mid_recv == MID0004_NEG_ACK_CODE):
                        print("- ERROR: Error, code: ", mid_recv )
                        return None

                    if keep_alive_time < 1 :
                        print("- ERROR: over the Max keep alive time")
                        return None	
						
                    print("## mid9999 feedback mid recv:%s, type:%s " % (mid_recv, type(mid_recv)))
                    print("- keep alive loop end")

                return(data)
		
            except socket.error as msg:
                print(msg)
                continue
            break		

    def stop_comm(self):
        mid_send = MID0003_COMM_STOP + chr(0)
        counter = RETRY_COUNTER
        while counter > 0:
            counter -= 1
            try:
                self.sk.sendall(mid_send.encode())
                print("--socket stop communication")
                data = self.sk.recv(RECV_DATA_LENGTH)
                data = data.decode()
                print("- stop comm recv data: %s" % data)
                mid_recv = data[HEADER_MID_START : HEADER_MID_END]
                print("- mid0001 feedback mid code", mid_recv)
                if data is None :
                    print("- ERROR: stop communicaton feedback error", mid_recv)
                    #return None
                #return data.decode('utf-8')
            except socket.error as msg:
                print(msg)
                continue
            break

        self.sk.close()
        print("--socket close")
        self.sk = None


#TODO This part shall be refactored to SPIDR implementation
if __name__ == "__main__":
    SPIDR_FB_Main(IP_DEFAULT, PORT_DEFAULT)

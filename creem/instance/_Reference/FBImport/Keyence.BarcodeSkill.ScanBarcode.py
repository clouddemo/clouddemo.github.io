import csv
import json
import socket
import sys
import time

from array import array

CSV_PATH = '/home/siemens/workspace/danfoss_keyence_barcode_index.csv'
RECV_DATA_LENGTH = 1024

TIME_OUT_KEYENCE_BARCODE = 50
RETRY_COUNTER = 5
IP_DEFAULT = "192.168.1.100"
PORT_DEFAULT = 9004
LON_COMMAND = array('b', [0x4c, 0x4f, 0x4e, 0x0D])         # start to read
LOFF_COMMAND = array('b', [0x4c, 0x4f, 0x46, 0x46, 0x0D])  # stop read
BARCODE_INDEX_MIN = 0
BARCODE_INDEX_MAX = 10
CSV_BARCODE_NAME = "Barcode"
CSV_PSET_NAME = "Pset"
PSET_LENGTH = 3

def SPIDR_FB_Main(IP, Port, pset):
    ip_socket = IP
    port_socket = int(Port)

    client = BarcodeClient(ip_socket, port_socket)
    barcode = client.run_module()

    time.sleep(2)

    json_Pset = data_compare(barcode)

    client.close_module()
    
    status = 0x00000000
    return (barcode, status)


def data_compare(barcode):
    print("- barcode: %s, type: %s" % (barcode, type(barcode)))
    str_pset = 'ERR'
    int_pset = 0
    index_flag = 0 
    dict_pset = {"Pset":"000"}

    # open csv file and check barcode name
    csv_index = open(CSV_PATH,'r') # , encoding='utf-8'
    reader = csv.DictReader(csv_index)

    for i in reader:
        if i[CSV_BARCODE_NAME] == barcode:
            int_pset = int(i[CSV_PSET_NAME])
            if int_pset >= BARCODE_INDEX_MAX or int_pset <= BARCODE_INDEX_MIN:
                str_pset = 'ERR'
                print("ERROR: undefined pset value")
                break
            str_pset = i[CSV_PSET_NAME].zfill(PSET_LENGTH)
            index_flag += 1
            print("- str_pset: %s, type: %s" % (str_pset, type(str_pset)))
            print("- index_flag: %d" % index_flag)
            break

    if index_flag <= 0:
        print("ERROR: unrecoder barcode name")

    dict_pset["Pset"] = str_pset
    json_Pset = json.dumps(dict_pset)
    print("- json_Pset: %s, type: %s" % (json_Pset, type(json_Pset)))
    csv_index.close()

    return (json_Pset)

'''
def singleton(cls, *args, **kw):
    instances = {}
    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton()

@singleton
'''

class BarcodeClient(object):
    def __init__(self, ip=IP_DEFAULT, port=PORT_DEFAULT):
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
                self.sk.settimeout(TIME_OUT_KEYENCE_BARCODE)
            except socket.error as msg:
                self.sk.close()
                self.sk = None
                continue
            break

    def recv(self):
        counter = RETRY_COUNTER
        while counter > 0:
            counter -= 1
            try:
                data = self.sk.recv(RECV_DATA_LENGTH)
                print("- recv data: %s" % data)
                if len(data) < 1 or data is None:
                    return None
                print("- len(data): %d" % len(data))
                return data.replace(b'\r', b'')
            except socket.error as msg:
                print(msg)
                continue
            break

    def run_module(self):
        counter = RETRY_COUNTER
        while counter > 0:
            counter -= 1
            try:
                self.sk.sendall(LON_COMMAND)
                print("--socket send LON command")
                data = self.recv()
                print("- run module recv data: %s" % data)
                if data is None :
                    return None
                return data.decode('utf-8')
            except socket.error as msg:
                print(msg)
                continue
            break
    
    def close_module(self):
        counter = RETRY_COUNTER
        while counter > 0:
            counter -= 1
            try:
                self.sk.sendall(LOFF_COMMAND)
                print("--socket send LOFF command")
            except socket.error as msg:
                print(msg)
                continue
            break
        self.sk.close()
        print("--socket close")
        self.sk = None



if __name__ == "__main__":
    SPIDR_FB_Main(IP_DEFAULT, PORT_DEFAULT)


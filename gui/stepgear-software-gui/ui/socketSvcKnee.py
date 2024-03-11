import sys
import socket
import select
import json
import struct
TCP_IP = '0.0.0.0'
TCP_PORT = 4444
toDeg=57.29577951
BUFFER_SIZE = 18 #uint8_t strikes, uint16_t vals[8]
param = []

print('Listening for client...')
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((TCP_IP,TCP_PORT))
server.listen(1)
rxset = [server]
txset = []

_counter=0
while 1:
    rxfds, txfds, exfds = select.select(rxset, txset, rxset)
    for sock in rxfds:
        if sock is server:
            conn, addr = server.accept()
            conn.setblocking(0)
            rxset.append(conn)
            print('Connection from address:', addr)
            _counter=0
        else:
            try:
                data = sock.recv(BUFFER_SIZE)
                jsondat={}
                jdataStates=[0,0,0,0]
                jdatadist=[0,0,0,0]
                jdataprox=[0.0,0.0,0.0,0.0]
                for tmp in range(0,4):
                    jdataStates[tmp]=(data[0]&(0x03<<((3-tmp)*2)))>>((3-tmp)*2)
                    #tmpp = ((data[3+(tmp*4)]<<8)&0xff00) + data[4+(tmp*4)]
                    val=data[2+(tmp*4):3+(tmp*4)+1]
                    tmpp=(struct.unpack("<h",val))[0]
                    jdataprox[tmp]=(tmpp/100.0)
                    #jdataprox[tmp]=(tmpp/2000.0)*toDeg
                    val=data[4+(tmp*4):5+(tmp*4)+1]
                    tmpp=(struct.unpack("<h",val))[0]
                    jdatadist[tmp]=(tmpp/100.0)
                    #jdatadist[tmp]=(tmpp/2000.0)*toDeg
                    #print("here",tmp,data)
                # {"counter":19,"state":[0,0,0,0],"prox":[29.9,29.8,30.0,30.3],"dist":[0.0,0.0,0.0,0.0]}
                jsondat["counter"]=_counter
                jsondat["state"]=jdataStates
                jsondat["prox"]=jdataprox #*toDeg
                jsondat["dist"]=jdatadist #*toDeg
                _counter+=1
                with open('/home/motto/gitreconlabco/stepgear/ui/knee', 'w') as f:
                    json.dump(jsondat, f, ensure_ascii=False)
                x=data #":".join("{:02x}".format(ord(c)) for c in data)
                #print(x)
                print(jsondat)
                #if data == ";" :
                #    print("Received all the data")
                #    for x in param:
                #        print(x)
                #    param = []
                #    rxset.remove(sock)
                #    sock.close()
                #else:
                #    print("received data: ", data)
                #    param.append(data)
            except:
                print("Connection closed by remote end")
                param = []
                rxset.remove(sock)
                sock.close()

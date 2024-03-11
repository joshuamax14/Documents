import sys
import asyncio
from bleak import BleakClient,BleakScanner
import json
import struct

#address = "A0:76:4E:48:D7:8E"
NOTIFY_UUID = "0000ABF2-0000-1000-8000-00805F9B34FB"

devtype="none"

jsondat={}
jdataStates=[0,0,0,0]
jdatadist=[0,0,0,0]
jdataprox=[0.0,0.0,0.0,0.0]

_counter = 0
indx = 0

ALPHA1 = 0.03
#ALPHA1 = 0.4
ALPHA2 = 1.0 - ALPHA1

BETA1 = 0.02
#BETA1 = 0.03
BETA2 = 1.0 - BETA1

def xcompfiltA(oldval, gyro, accel):
    ret = ALPHA1*(oldval+gyro)+ALPHA2*(accel);
    return ret

def xcompfiltB(oldval, gyro, accel):
    ret = BETA1*(oldval+gyro)+BETA2*(accel);
    return ret

def compfiltA(gyro, accel):
    ret = ALPHA1*(accel+gyro)+ALPHA2*(accel);
    return ret

def compfiltB(gyro, accel):
    ret = BETA1*(accel+gyro)+BETA2*(accel);
    return ret

def callback(handle, datax):
    global indx,_counter, devtype
    #print(f"{len(datax)}: {datax}")
    #check if length is valid
    if len(datax)==10:
        data = datax
        data.extend(b"\x00")
        #print(f"{data}")
        if data[0]==ord('a'):
            #print("angles ok")
            #angles data
            val=data[2:4]
            pgyroA=(struct.unpack("<h",val))[0]/10.0
            val=data[4:6]
            paccelA=90+(struct.unpack("<h",val))[0]/10.0
            val=data[6:8]
            dgyroA=(struct.unpack("<h",val))[0]/10.0
            val=data[8:10]
            daccelA=90+(struct.unpack("<h",val))[0]/10.0
            if paccelA<0:
                paccelA+=360
            if daccelA<0:
                daccelA+=360
            if devtype=="foot":
                jdataprox[indx]=compfiltB(pgyroA,paccelA)
                #jdataprox[indx]=xcompfiltA(jdataprox[indx],pgyroA,paccelA)
                jdataStates[indx]=data[1] #data[1] contains state data
            elif devtype=="hips":
                jdataprox[indx]=compfiltB(pgyroA,paccelA)
                #jdataprox[indx]=xcompfiltA(jdataprox[indx],pgyroA,paccelA)
                #jdataStates[indx]=data[1]
            elif devtype=="knee":
                #jdataprox[indx]=compfiltA(pgyroA,paccelA)
                #jdatadist[indx]=compfiltA(dgyroA,daccelA)
                jdataprox[indx]=xcompfiltA(jdataprox[indx],pgyroA,paccelA)
                jdatadist[indx]=xcompfiltA(jdatadist[indx],dgyroA,daccelA)
            #print(f"{jdataStates} - {hex(pgyroA)} {hex(paccelA)} {hex(dgyroA)} {hex(daccelA)}")
            #print(f"{jdataStates} - {compfilt(pgyroA,paccelA)} {compfilt(dgyroA,daccelA)}")
            if devtype=="hips":
                jdataprox[indx]=compfiltB(pgyroA,paccelA)
                #jdataprox[indx]=xcompfiltA(jdataprox[indx],pgyroA,paccelA)
                #jdataStates[indx]=data[1]
            indx+=1
            if indx>=4:
                #save json file
                indx=0
                jsondat["counter"]=_counter
                jsondat["state"]=jdataStates
                jsondat["prox"]=jdataprox
                jsondat["dist"]=jdatadist
                _counter+=1
                print(f"{jsondat}")
                with open(f"C:/Users/Rafael/Documents/3rd_Thesis/stepgear/ui/{devtype}", 'w') as f: #change this to local repository
                    json.dump(jsondat, f, ensure_ascii=False)
    else:
        print("invalid data")

async def getAdress(type):
    global devtype
    device=None
    if type=="knee":
        devtype="knee"
        device = await BleakScanner.find_device_by_filter(lambda d, ad: d.name and d.name.lower() == "kneespp_server")
    elif type=="foot":
        devtype="foot"
        device = await BleakScanner.find_device_by_filter(lambda d, ad: d.name and d.name.lower() == "footspp_server")
    elif type=="hips":
        devtype="hips"
        device = await BleakScanner.find_device_by_filter(lambda d, ad: d.name and d.name.lower() == "hipsspp_server")    
    if device == None:
        print(f"No {type} devices found.")
    else:
        print(f"Connecting to {device} with level {device.rssi}")
        await asyncio.sleep(2)
        await main(device.address)

async def main(address):
    client = BleakClient(address)
    try:
        await client.connect()
        await client.start_notify(NOTIFY_UUID, callback)
        # wait forever
        await asyncio.Event().wait()
        await client.stop_notify(NOTIFY_UUID)
        print("stopped properly")
        #model_number = await client.read_gatt_char(NOTIFY_UUID)
        #print("Model Number: {0}".format("".join(map(chr, model_number))))
    except Exception as e:
        #await client.stop_notify(NOTIFY_UUID)
        print(e)
    finally:
        await client.disconnect()

if len(sys.argv)>1:
    #ok, what device are we looking for?
    asyncio.run(getAdress(sys.argv[1]))
else:
    print("incomplete arguments...")
#asyncio.run(main(address))
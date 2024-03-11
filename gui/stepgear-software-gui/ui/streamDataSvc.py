import json
import numpy as np

def neoReadKneeAngles():
    kneedecodedArrays={}
    #footdecodedArrays={}
    prox=[]
    dist=[]
    state=[]
    counter=0
    try:
        #print("reading...")
        file = open("./knee", "r")
        decodedArrays = json.load(file)
        file.close()
        #print("reading... state")
        counter=decodedArrays["counter"]
        #state = np.asarray(decodedArrays["state"])
        prox = np.asarray(decodedArrays["prox"])
        dist = np.asarray(decodedArrays["dist"])
    except:
        print(f"error occured while trying to read data: {kneedecodedArrays}")
    return (counter,prox,dist)

def neoReadFootAngles():
    kneedecodedArrays={}
    #footdecodedArrays={}
    prox=[]
    dist=[]
    state=[]
    counter=0
    try:
        #print("reading...")
        file = open("./foot", "r")
        decodedArrays = json.load(file)
        file.close()
        #print("reading... state")
        counter=decodedArrays["counter"]
        state = np.asarray(decodedArrays["state"])
        prox = np.asarray(decodedArrays["prox"])
        #dist = np.asarray(decodedArrays["dist"])
    except:
        print(f"error occured while trying to read data: {kneedecodedArrays}")
    return (counter,prox,state)



def readKneeAngles():
    kneedecodedArrays={}
    footdecodedArrays={}
    try:
        #print("reading...")
        file = open("./knee", "r")
        decodedArrays = json.load(file)
        file.close()
        #print("reading... state")
        ddaState = (decodedArrays["state"])
        ddaKneeFlex = np.asarray(decodedArrays["kneeFlex"])
        ddaAnkleFlex = np.asarray(decodedArrays["ankleFlex"])
        kneedecodedArrays["state"]=ddaState
        kneedecodedArrays["kneeFlex"]=ddaKneeFlex
        kneedecodedArrays["ankleFlex"]=ddaAnkleFlex
    except:
        ddaState = 0
        kneedecodedArrays["state"]=[8,8]
        kneedecodedArrays["kneeFlex"]=[-200,-200]
        kneedecodedArrays["ankleFlex"]=[-200, -200]
        print(f"error occured while trying to read data: {kneedecodedArrays}")
    return (kneedecodedArrays)

def readDataKnee():
    kneedecodedArrays={}
    footdecodedArrays={}
    try:
        #print("reading...")
        file = open("./knee", "rb")
        decodedArrays = json.load(file)
        file.close()
        ddaState = (decodedArrays["state"])
        ddaPsensor = np.asarray(decodedArrays["psensor"])
        ddaDistal = np.asarray(decodedArrays["distal"])
        ddaProximal = np.asarray(decodedArrays["proximal"])
        ddaFoot = np.asarray(decodedArrays["foot"])
        ddaDistalR = np.sqrt((ddaDistal[0]**2)+(ddaDistal[1]**2)+(ddaDistal[2]**2))
        ddaProximalR = np.sqrt((ddaProximal[0]**2)+(ddaProximal[1]**2)+(ddaProximal[2]**2))
        ddaFootR = np.sqrt((ddaFoot[0]**2)+(ddaFoot[1]**2)+(ddaFoot[2]**2))
        kneedecodedArrays["state"]=ddaState
        kneedecodedArrays["psensor"]=ddaPsensor
        kneedecodedArrays["distal"]=ddaDistal
        kneedecodedArrays["proximal"]=ddaProximal
        kneedecodedArrays["distalR"]=ddaDistalR
        kneedecodedArrays["proximalR"]=ddaProximalR
        footdecodedArrays["state"]=ddaState
        footdecodedArrays["psensor"]=ddaPsensor
        footdecodedArrays["distal"]=ddaDistal
        footdecodedArrays["proximal"]=ddaFoot
        footdecodedArrays["distalR"]=ddaDistalR
        footdecodedArrays["proximalR"]=ddaFootR
    except:
        ddaState = 0
        ddaPsensor = [0.,0.]
        ddaDistal = [0.,0.,0.]
        ddaDistalR = np.sqrt((ddaDistal[0]**2)+(ddaDistal[1]**2)+(ddaDistal[2]**2))
        ddaProximal = [0.,0.,0.]
        ddaProximalR = np.sqrt((ddaProximal[0]**2)+(ddaProximal[1]**2)+(ddaProximal[2]**2))
        kneedecodedArrays["state"]=ddaState
        kneedecodedArrays["psensor"]=ddaPsensor
        kneedecodedArrays["distal"]=ddaDistal
        kneedecodedArrays["proximal"]=ddaProximal
        kneedecodedArrays["distalR"]=ddaDistalR
        kneedecodedArrays["proximalR"]=ddaProximalR
        footdecodedArrays["state"]=ddaState
        footdecodedArrays["psensor"]=ddaPsensor
        footdecodedArrays["distal"]=ddaDistal
        footdecodedArrays["proximal"]=ddaProximal
        footdecodedArrays["distalR"]=ddaDistalR
        footdecodedArrays["proximalR"]=ddaProximalR
        print(f"error occured while trying to read foot data: {kneedecodedArrays}")
    return (kneedecodedArrays, footdecodedArrays)
def readDataFoot():
    kneedecodedArrays={}
    footdecodedArrays={}
    try:
        #print("reading...")
        file = open("./foot", "rb")
        decodedArrays = json.load(file)
        file.close()
        ddaState = (decodedArrays["state"])
        ddaPsensor = np.asarray(decodedArrays["psensor"])
        ddaDistal = np.asarray(decodedArrays["distal"])
        ddaProximal = np.asarray(decodedArrays["proximal"])
        ddaFoot = np.asarray(decodedArrays["foot"])
        ddaDistalR = np.sqrt((ddaDistal[0]**2)+(ddaDistal[1]**2)+(ddaDistal[2]**2))
        ddaProximalR = np.sqrt((ddaProximal[0]**2)+(ddaProximal[1]**2)+(ddaProximal[2]**2))
        ddaFootR = np.sqrt((ddaFoot[0]**2)+(ddaFoot[1]**2)+(ddaFoot[2]**2))
        kneedecodedArrays["state"]=ddaState
        kneedecodedArrays["psensor"]=ddaPsensor
        kneedecodedArrays["distal"]=ddaDistal
        kneedecodedArrays["proximal"]=ddaProximal
        kneedecodedArrays["distalR"]=ddaDistalR
        kneedecodedArrays["proximalR"]=ddaProximalR
        footdecodedArrays["state"]=ddaState
        footdecodedArrays["psensor"]=ddaPsensor
        footdecodedArrays["distal"]=ddaDistal
        footdecodedArrays["proximal"]=ddaFoot
        footdecodedArrays["distalR"]=ddaDistalR
        footdecodedArrays["proximalR"]=ddaFootR
    except:
        ddaState = 0
        ddaPsensor = [0.,0.]
        ddaDistal = [0.,0.,0.]
        ddaDistalR = np.sqrt((ddaDistal[0]**2)+(ddaDistal[1]**2)+(ddaDistal[2]**2))
        ddaProximal = [0.,0.,0.]
        ddaProximalR = np.sqrt((ddaProximal[0]**2)+(ddaProximal[1]**2)+(ddaProximal[2]**2))
        kneedecodedArrays["state"]=ddaState
        kneedecodedArrays["psensor"]=ddaPsensor
        kneedecodedArrays["distal"]=ddaDistal
        kneedecodedArrays["proximal"]=ddaProximal
        kneedecodedArrays["distalR"]=ddaDistalR
        kneedecodedArrays["proximalR"]=ddaProximalR
        footdecodedArrays["state"]=ddaState
        footdecodedArrays["psensor"]=ddaPsensor
        footdecodedArrays["distal"]=ddaDistal
        footdecodedArrays["proximal"]=ddaProximal
        footdecodedArrays["distalR"]=ddaDistalR
        footdecodedArrays["proximalR"]=ddaProximalR
        print(f"error occured while trying to read foot data: {kneedecodedArrays}")
    return (kneedecodedArrays, footdecodedArrays)

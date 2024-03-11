import asyncio
import json
from bleak import BleakScanner

async def main():
    devices = await(BleakScanner.discover())
    kneeDevList={}
    footDevList={}
    devList={}
    for d in devices:
        print(d)
        n=str(d).split(" ")
        devName=n[1].strip()
        m=n[0].strip().split(":")
        #choicesEM.append(p)
        #devList[str(d)[19:]]=p
        if ("StepGear_KA") in devName:
            kneeDevList[devName]=str(d)[0:17]
        elif ("StepGear_FA") in devName:
            footDevList[devName]=str(d)[0:17]
        #print(p,0,str(d)[19:])
    devList["knee"]=kneeDevList
    devList["foot"]=footDevList
    print(devList)
    json_object = json.dumps(devList, indent=4)
    with open("devList.json", "w") as outfile:
        outfile.write(json_object)
asyncio.run(main())

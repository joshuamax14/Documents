# --- Imports
from scipy.signal import savgol_filter
from scipy import interpolate
from scipy import signal

import numpy.linalg as LA
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import TclError,ttk, font as tkfont
from PIL import ImageTk, Image

import subprocess
import time
import signal

import os
import numpy as np
import json

from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import mpl_toolkits.mplot3d as a3
from matplotlib.animation import FuncAnimation
import matplotlib.image as mpimg
from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox

from matplotlib.patches import Circle,Rectangle
import mpl_toolkits.mplot3d.art3d as art3d
from scipy.spatial.transform import Rotation as R

import mdtdcomputeSvc as md
import streamDataSvc as stream

import threading
import asyncio
from bleak import BleakScanner
# --- End of imports

import aiotkinter
import nest_asyncio
import random
import string
import datetime

import psutil
import logging
# Create a custom logger
logger = logging.getLogger("stepgear_sys")
# Create handlers
logger.setLevel(logging.DEBUG)
f_handler = logging.FileHandler('app.log')
# Create formatters and add it to handlers
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
# Add handlers to the logger
logger.addHandler(f_handler)
logger.info('Software Started')

def is_float(v):
    try:
        f=float(v)
    except ValueError:
        return False
    return True

def checkAndKill(pname):
    _processKilled=0
    try:
        for process in psutil.process_iter():
            if process.name() == 'thingy':
                print(process)
                logger.info(f"killing {str(process)}")
                process.kill()
                _processKilled+=1
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        print("Processes not detected or access denied.")
        #pass
    logger.info(f"{str(_processKilled)} processes were killed.")

def checkPID(pid):
    ret = False
    if pid==-1:
        #no app ran
        ret = False
    else:
        for process in psutil.process_iter():
            if str(process.pid) == str(pid.pid):
                ret = True
                continue
    return ret

def runme(add1, stype):
    pidd = subprocess.Popen(['./thingy', '-d', add1, '-s', stype])
    #pidd2 = subprocess.Popen(['./thingy', '-d', add2, '-s', 'foot'])
    logger.info(f"{stype} process {pidd} started")
    return pidd
    
def genSessionCode():
    #Generate a datetime string for session
    now = datetime.datetime.now()
    strl = string.ascii_uppercase
    trailing= ''.join(random.choice(strl) for i in range(7))
   
    return "{}{}{}-{}:{}-{}".format(now.year,str(now.month).rjust(2,'0'),str(now.day).rjust(2,'0'),str(now.hour).rjust(2,'0'),str(now.minute).rjust(2,'0'),trailing)

_scale=1.0
_width = 1280
_height = 720

_em=""
_sp=""

class mainClass(tk.Tk):

    def getorigin(self,eventorigin):
        global x0,y0
        x0 = eventorigin.x
        y0 = eventorigin.y
        print(x0,y0)
    #mouseclick event
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title('Stepgear App')
        #self.resizable(0, 0)
        self.geometry("{}x{}".format(int(_width*_scale),int(_height*_scale)))
        #self.attributes('-fullscreen', True)
        self.title_font = tkfont.Font(family='Helvetica', size=18, weight="bold", slant="italic")
        self.messFont = tkfont.Font(family='Helvetica', size=12, slant="italic")
        self.gensession = genSessionCode()
        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        self.dataAvailable=False
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self._session=""
        self.statusbar = tk.Label(self, text="System Ready.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.sysReady=False
        #tracking variables
        
        self.processId=-1
        self.processId2=-1

        self.frames = {}
        for F in (StartPage, DeviceSelection, MainPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.bind("<Button 1>",self.getorigin)

            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")
        #self.show_frame("MainPage")
        
    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame = self.frames[page_name]
        frame.tkraise()

class StartPage(tk.Frame):
    def populateDevList(self):
        #checkAndKill("thingy")
        task = asyncio.ensure_future(self.loadBle())
        task.add_done_callback(self.tasks_done)
        
    def tasks_done(self,task):
        self.controller.statusbar.config(text="Device Selection")
        print("{} done. switching view.".format(task))
        with open('devList.json', 'r') as openfile:
            # Reading from json file
            self.controller.devList = json.load(openfile)
        logger.info(f"devices discovered: {self.controller.devList}")
        print(self.controller.devList)
        self.controller.tkvarEM.set("Select Knee Assy")
        self.controller.tkvarSP.set("Select Foot Assy")
        self.controller.dropEM['menu'].delete(0,"end")
        self.controller.dropSP['menu'].delete(0,"end")
        for dev in self.controller.devList["knee"]:
            print(dev)
            choicesEM.append(dev)
            self.controller.dropEM["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarEM, dev))
        for dev in self.controller.devList["foot"]:
            print(dev)
            choicesSP.append(dev)
            self.controller.dropSP["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarSP, dev))
        self.controller.show_frame("DeviceSelection")

    async def loadBle(self):
        logger.info(f"running search...")
        self.controller.statusbar.config(text="Searching for devices...")
        await os.system("python3 ./discoverySvc.py")
        #await asyncio.sleep(5)

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
                
        label = tk.Label(self, text="Welcome!", font=self.controller.title_font)
        label.pack(side="top", fill="x", pady=20)

        label = tk.Label(self, text="Click Proceed for device selection process.", font=controller.messFont)
        label.pack(side="top", fill="x", pady=10)

        label = tk.Label(self, text="Make sure instruments are in range \nbefore proceeding.", font=controller.messFont)
        label.pack(side="top", fill="x", pady=10)
        
        #image1 = Image.open("./images/welcome.png")
        #image1 = image1.resize((int(900*.70), int(600*.70)), Image.ANTIALIAS)
        #pImage = ImageTk.PhotoImage(image1)

        #label1 = tk.Label(self,image=pImage)
        #label1.image = pImage
        #label1.pack(side="top", fill="x", pady=5)
        
        _vloc=600
        _iHeight=int(71*_scale)
        _iWidth=int(234*_scale)
        button = tk.Button(self, text="Proceed",
                            #command=lambda: self.controller.show_frame("DeviceSelection"), height=20, bg="GREEN")
                            command=lambda: self.populateDevList(), height=20, bg="GREEN")
        button.place(height=_iHeight, width=_iWidth, x=int(((_width/2)-(_iWidth/2))*_scale), y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+5
        #button1.pack(side="bottom", fill="x")
        #button1.pack(side="bottom", fill="both",expand=False)

class DeviceSelection(tk.Frame):
    def madeSelection(self):
        emList=self.controller.devList["knee"]
        spList=self.controller.devList["foot"]
        try:
            self.controller._em=str(self.controller.tkvarEM.get())
            self.controller._sp=str(self.controller.tkvarSP.get())
            self.controller.emAdd = emList[self.controller._em]
            self.controller.spAdd = spList[self.controller._sp]
        except:
            self.controller._em=""
            self.controller._sp=""
            self.controller.emAdd = ""
            self.controller.spAdd = ""
        logger.info(f"checking emboard {self.controller._em} sensor {self.controller._sp}")
        if ("StepGear_KA" in self.controller._em):
            #valid emboard input
            if ("StepGear_FA" in self.controller._sp):
                #valid sensor also
                #check if there are current running streaming service, then close them
                #start thingy stream service -> os.system("./thingy -d {} -e {}".format(self.controller._em, self.controller._sp))
                logger.info(f"OK knee board {self.controller._em} foot board {self.controller._sp}")
                #print(str(self.controller.devList["em"]))
                self.controller.statusText = "Knee: {} \tFoot: {}".format(self.controller._em,self.controller._sp)
                self.controller.statusbar.config(text=self.controller.statusText)
                logger.info(f"switching to HOME view")
                self.controller.show_frame("MainPage")
                #self.controller.calibFile = f"./{self.controller._em[-4:]}-{self.controller._sp[-4:]}.npy"
                checkAndKill("thingy")
                self.controller.sysReady=False
                self.controller.processId2= runme(self.controller.spAdd,"foot")
                self.controller.processId= runme(self.controller.emAdd,"knee")
                self.controller.sysReady=True
                                                
            else:
                #no sensor selected
                logger.info(f"Invalid entry.")
                self.controller.show_frame("MainPage")
                #res=tk.messagebox.showerror("Invalid Device Selection","Invalid EM-Sensor pair selected")    
        else:
            #no sensor selected
                logger.info(f"Invalid entry.")
                self.controller.show_frame("MainPage")
                #res=tk.messagebox.showerror("Invalid Device Selection","Invalid EM-Sensor pair selected")    
    def populateDevList(self):
        logger.info("searching for devices.")
        task = asyncio.ensure_future(self.loadBle())
        task.add_done_callback(self.tasks_done)
        
    def tasks_done(self,task):
        print("{} done. switching view.".format(task))
        with open('devList.json', 'r') as openfile:
            # Reading from json file
            self.controller.devList = json.load(openfile)
            print("refresh {}".format(str(self.controller.devList)))
        logger.info(f"REFRESHED. devices discovered: {self.controller.devList}")
        print(self.controller.devList)
        self.controller.tkvarEM.set("Select Knee Assy")
        self.controller.tkvarSP.set("Select Foot Assy")
        self.controller.dropEM['menu'].delete(0,"end")
        self.controller.dropSP['menu'].delete(0,"end")
        for dev in self.controller.devList["knee"]:
            print(dev)
            choicesEM.append(dev)
            self.controller.dropEM["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarEM, dev))
        for dev in self.controller.devList["foot"]:
            print(dev)
            choicesSP.append(dev)
            self.controller.dropSP["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarSP, dev))
        self.controller.show_frame("DeviceSelection")
    async def loadBle(self):
        await os.system("python3 ./discoverySvc.py")
        #await asyncio.sleep(5)
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Available Devices", font=self.controller.title_font)
        label.pack(side="top", fill="y", pady=20)
        label = tk.Label(self, text='Knee Assembly:',font=self.controller.messFont)
        label.pack(side="top", fill="y", pady=10)
        self.controller.tkvarEM = tk.StringVar(self)
        self.controller.tkvarEM.set('   ') # set the default option
        self.controller.dropEM = tk.OptionMenu(self , self.controller.tkvarEM , *choicesEM )
        self.controller.dropEM.config(height=2)
        #self.controller.dropEM.pack(side="top", fill="y", pady=10)
        self.controller.dropEM.pack(side="top", pady=10)
        
        label = tk.Label(self, text='Foot Assembly:',font=self.controller.messFont)
        label.pack(side="top", fill="y", pady=10)
        self.controller.tkvarSP = tk.StringVar(self)
        self.controller.tkvarSP.set('   ') # set the default option
        self.controller.dropSP = tk.OptionMenu(self , self.controller.tkvarSP , *choicesSP )
        self.controller.dropSP.config(height=2)
        self.controller.dropSP.pack(side="top", pady=10)
        
        _iHeight=int(71*_scale)
        _iWidth=int(234*_scale)
        _vloc=600-5-_iHeight
        button = tk.Button(self, text="Refresh",
                           command=lambda: self.populateDevList(),height=60, bg="GREEN")
        button.place(height=_iHeight, width=_iWidth, x=int(((_width/2)-(_iWidth/2))*_scale), y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+5

        _vloc=600
        _iHeight=int(71*_scale)
        _iWidth=int(234*_scale)
        button = tk.Button(self, text="Proceed",
                           command=lambda: self.madeSelection(),height=60, bg="GREEN")
        button.place(height=_iHeight, width=_iWidth, x=int(((_width/2)-(_iWidth/2))*_scale), y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+5
        
choicesEM = [ 'Pizza','Lasagne','Fries','Fish','Potato']
choicesSP = [ 'Pizza','Lasagne','Fries','Fish','Potato']
devList={}

class MainPage(tk.Frame):
    def newSession(self):
        pass
    def loadSession(self):
        pass
    def saveSession(self,task):
        pass
    def genChart(self):
        pass
    def exportChart(self):
        pass    
    def startLoopDeLoop(self):
        task = asyncio.ensure_future(self.loopDeLoop())
        task.add_done_callback(self.loop_done)
    def getAngle(self,v,axis):
        a=[0.,0.]
        b=[0.,1.]
        if axis=='xz':
            a[0]=v[0] #x
            a[1]=v[2] #z
        elif axis=='zx':
            a[1]=v[0] #y
            a[0]=v[2] #z
        elif axis=='yz':
            a[0]=v[1] #y
            a[1]=v[2] #z
        elif axis=='zy':
            a[1]=v[1] #y
            a[0]=v[2] #z
        elif axis=='yx':
            a[0]=v[1] #y
            a[1]=v[0] #x
        elif axis=='xy':
            a[1]=v[1] #y
            a[0]=v[0] #x
        try:
            inner = np.inner(a, b)
            norms = LA.norm(a) * LA.norm(b)
            cos = inner / norms
            rad = np.arccos(np.clip(cos, -1.0, 1.0))
        except:
            rad=0.0 #deg = np.rad2deg(rad)
        return(rad) 
    def loop_done(self,task):
        logger.info("loop stopped")
        self.startLoopDeLoop()
    async def loopDeLoop(self):
        while True:
            #get new data
            runagain=False
            ddaKneeArray = stream.readDataKnee()
            ddaFootArray = stream.readDataFoot()
            if self.controller.sysReady:
                if self.oldResKnee == ddaKneeArray["distalR"]:
                    #same data. stream halted? try running again
                    self.nomovementknee+=1
                    #runagain = True
                else:
                    self.nomovementknee=0
                    self.oldResKnee = ddaKneeArray["distalR"]
                if self.oldResFoot == ddaFootArray["proximalR"]:
                    #same data. stream halted? try running again
                    self.nomovementfoot+=1
                    #print(f"no foot!!! {self.nomovementfoot}")
                    #runagain = True
                else:
                    self.nomovementfoot=0
                    self.oldResFoot = ddaFootArray["proximalR"]
                if self.nomovementknee>50:
                    self.nomovementknee=0
                    if self.controller.processId!=-1:
                        self.controller.processId.terminate()
                        self.controller.processId.kill()
                    self.controller.processId1 = runme(self.controller.emAdd,"knee")
                if self.nomovementfoot>50:
                    self.nomovementfoot=0
                    if self.controller.processId2!=-1:
                        self.controller.processId2.terminate()
                        self.controller.processId2.kill()
                    self.controller.processId2 = runme(self.controller.spAdd, "foot")
                    #     logger.info(f"started background stream process {self.controller.processId}")
            distalangle = np.rad2deg(self.getAngle(ddaKneeArray["distal"],"xz"))
            proximalangle = np.rad2deg(self.getAngle(ddaKneeArray["proximal"],"xz"))
            diffKneeAngle = (distalangle-proximalangle)
            ankleFlex = np.rad2deg(self.getAngle(ddaFootArray["proximal"],"xy"))
            #print(distalangle,proximalangle,diffKneeAngle)
            if is_float(distalangle):
                if is_float(proximalangle):
                    if is_float(ankleFlex):
                        self.heel0StrikePos-=1
                        #self.heel1StrikePos-=1
                        self.midfootStrikePos-=1
                        self.forefootStrikePos-=1
                        self.liftPos-=1
                        self.gaitOffset+=1
                        self.kneeProxAngles[:-1] = self.kneeProxAngles[1:]
                        self.kneeProxAngles[-1] = proximalangle
                        self.kneeDistAngles[:-1] = self.kneeDistAngles[1:]
                        self.kneeDistAngles[-1] = distalangle
                        self.kneeAngles[:-1] = self.kneeAngles[1:]
                        self.kneeAngles[-1] = diffKneeAngle
                        self.footAnkleAngles[:-1] = self.footAnkleAngles[1:]
                        self.footAnkleAngles[-1] = ankleFlex-self.ankleAngleOffset
                        #print(f'state = {ddaFootArray["state"]}')
                        self.state = ddaFootArray["state"]
                        if (self.oldState != self.state):
                            #state change
                            if self.state ==1:
                                #heel strike
                                self.heel1StrikePos=self.sampsize
                                if self.stval == 0:
                                    self.stval = 50
                                else:
                                    self.stval = 0
                                if self.oldState == 0:
                                #if self.heel0StrikePos>0:
                                    #filtKnee = signal.correlate(self.kneeAngles, self.refy)
                                    filtKnee=savgol_filter(self.kneeAngles[-(self.sampsize-self.heel0StrikePos):],8,3)
                                    filtFoot=savgol_filter(self.footAnkleAngles[-(self.sampsize-self.heel0StrikePos):],8,3)
                                    self.mainPlot.clear()
                                    mmin = np.min([np.min(filtKnee),np.min(filtFoot)])
                                    mmax = np.max([np.max(filtKnee),np.max(filtFoot)])
                                    # plotting the graph
                                    reso = np.abs((self.sampsize-self.heel0StrikePos)/100.0)
                                    xnew=np.arange(0, 100, reso)
                                    xx = np.linspace(0,100, num = len(filtKnee)) # np.arange(0, len(filtKnee),1)
                                    #f = interpolate.interp1d(xx, filtKnee)
                                    newfiltKnee = np.interp(xnew,xx,filtKnee) #f(xnew)
                                    self.stepsData[self.stepsDataCount]["data"]=newfiltKnee
                                    self.stepsData[self.stepsDataCount]["vert"]=100*((self.forefootStrikePos-self.heel0StrikePos)/len(filtKnee))
                                    #self.stepsData[self.stepsDataCount]["vert"]=(self.forefootStrikePos-self.heel0StrikePos)*reso
                                    self.stepsData[self.stepsDataCount]["label"]=f"oldlength {len(filtKnee)} ffstrike: {self.stepsData[self.stepsDataCount]['vert']}% / {(self.sampsize-self.heel0StrikePos)}"
                                    self.stepsDataCount +=1
                                    self.stepCounter +=1
                                    if self.stepsDataCount>=self.maxStepData:
                                        self.stepsDataCount = 0
                                    #self.mainPlot.set_xlim(0, 100)
                                    self.mainPlot.plot(self.kneerefx,self.kneerefy,"g-", label="normal")
                                    for tempp in range(0, self.maxStepData):
                                        if len(self.stepsData[tempp]["data"])>0:
                                            #valid step?
                                            self.mainPlot.set_ylabel(self.stepsData[tempp]["label"])
                                            self.mainPlot.plot(xnew,self.stepsData[tempp]["data"],self.lineorders[tempp], label=self.stepsData[tempp]["label"])
                                            self.mainPlot.axvline(x=self.stepsData[tempp]["vert"], color='red', linestyle='-')
                                    self.mainPlot.set_ylim(-10.2, 90)
                                    self.mainPlot.legend(loc='best')
                                    #offsset = self.heel0StrikePos
                                    #self.kneeline, = self.mainPlot.plot(newfiltKnee,"b+", label="Knee Flex Angle")
                                    #self.kneeline, = self.mainPlot.plot(filtKnee,"black", label="Knee Flex Angle")
                                    #self.ankleline, = self.mainPlot.plot(filtFoot,"red", label = "Ankle Flex Angle")
                                    #self.mainPlot.axvline(x=self.heel0StrikePos-offsset, color='pink', linestyle='-')
                                    #self.mainPlot.axvline(x=self.heel1StrikePos-offsset, color='pink', linestyle='-')
                                    #self.mainPlot.axvline(x=self.forefootStrikePos-offsset, color='red', linestyle='-')
                                    #self.mainPlot.axvline(x=self.liftPos-offsset, color='blue', linestyle='-')
                                    #self.mainPlot.set_ylim(np.min(newfiltKnee), np.max(newfiltKnee))
                                    #self.mainPlot.set_ylim(mmin, mmax)
                                    #self.mainPlot.set_xlim(0, 100)
                                    self.bigfigcanvas.draw()
                                    #self.bigfig.savefig(f"./charts/{self.controller.gensession}_{self.imgCount}.png")
                                    self.imgCount+=1
                                #else:
                                #    exit()
                                self.heel0StrikePos = self.sampsize
                                print("heel strike")
                            elif self.state ==2:
                                self.ankleAngleOffset = ankleFlex
                                print("midfoot strike")
                                if self.oldState == 1:
                                    self.midfootStrikePos = self.sampsize
                            elif self.state == 4:
                                print("forefoot strike")
                                if self.oldState == 2:
                                    self.forefootStrikePos =self.sampsize
                            elif self.state ==0:
                                print("foot lifted")
                                if self.oldState == 4:
                                    self.liftPos = self.sampsize
                            self.oldState = self.state
                        self.fStates[:-1] = self.fStates[1:]
                        self.fStates[-1] = self.stval
                        if self.startStepRecord:
                            #print("recording")
                            #record flexes
                            self.stepKneeFlex = np.append(self.stepKneeFlex,diffKneeAngle)            
                            self.stepAnkleFlex = np.append(self.stepAnkleFlex,ankleFlex)            
                        mmin = np.min([np.min(self.kneeProxAngles),np.min(self.kneeDistAngles),np.min(self.kneeAngles),np.min(self.footAnkleAngles)])
                        mmax = np.max([np.max(self.kneeProxAngles),np.max(self.kneeDistAngles),np.max(self.kneeAngles),np.max(self.footAnkleAngles)])
                        self.secondPlot.set_ylim(mmin, mmax)
                        #self.kneeProxAnglesline.set_ydata(self.kneeProxAngles)
                        #self.kneeDistAnglesline.set_ydata(self.kneeDistAngles)
                        self.kneeAnglesline.set_ydata((self.kneeAngles))
                        self.fStatesline.set_ydata((self.fStates))
                        self.footAnkleAnglesline.set_ydata((self.footAnkleAngles))
                        self.littlefigcanvas.draw()

            #await asyncio.sleep(0.01)
            await asyncio.sleep(self.interv)
            #process data
            
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.imgCount = 0
        self.interv = 0.005 #data point to data point interval
        self.window = 1.0 #seconds
        self.wind=int(self.window/self.interv)
        _scale = 1.0
        self.nomovementknee=0
        self.nomovementfoot=0

        self.stval = 0

        self.kneerefx=[0, 5, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90, 95, 100]
        self.kneerefy=[6.0, 6.0, 11.0, 10.0, 5.0, 4.5, 8.0, 10.0, 45.0, 62.0, 55.0, 35.0, 10.0, 6.0]
        self.newkneerefx= np.linspace(0,100, num = 1000) #np.arange(0, 100, 0.1)
        self.newkneerefy = np.interp(self.newkneerefx,self.kneerefx,self.kneerefy)
        self.refy=savgol_filter(self.newkneerefy,8,3)

        self.lineorders=["r+","g-","b-","y-"]        
        self.maxStepData = 1
        self.stepCounter = 1
        self.stepsData=[{}]
        for tempp in range(0,self.maxStepData):
            self.stepsData.append({})
        self.stepsDataCount = 0
        self.sampsize = 500
        
        _iHeight=int(50*_scale)
        _iWidth=int(234*_scale)
        _vloc=100-5-_iHeight
        
        self.heel0StrikePos=self.sampsize
        self.heel1StrikePos=self.sampsize
        self.midfootStrikePos=self.sampsize
        self.forefootStrikePos=self.sampsize
        self.liftPos=0
        leftoffset = 7
        button = tk.Button(self, text="New Session",
                           command=lambda: self.newSession(),height=60, bg="GREEN")
        button.place(height=_iHeight, width=_iWidth, x=int(leftoffset*_scale), y=int(int(_vloc*_scale)))
        #button.place(height=_iHeight, width=_iWidth, x=int(((_width/4)-(_iWidth/1))*_scale), y=int(int(_vloc*_scale)))
        #_vloc+=_iHeight+5

        button = tk.Button(self, text="Load Session",
                           command=lambda: self.madeSelection(),height=60, bg="GREEN")
        button.place(height=_iHeight, width=_iWidth, x=int((_width/4)*_scale), y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+15

        _iHeight=int(20*_scale)
        _iWidth=int(250*_scale)
        self.gaitOffset = 0
        label = tk.Label(self, text='Patient: Juan de la Cruz',font=self.controller.messFont,justify="left",width=_iWidth, anchor = 'w')
        label.place(height=_iHeight, width=_iWidth, x=int(leftoffset*_scale), y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+5
        label = tk.Label(self, text='DOB: 1 Jan 2020',font=self.controller.messFont,justify="left",width=_iWidth, anchor = 'w')
        label.place(height=_iHeight, width=_iWidth, x=int(leftoffset*_scale), y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+20

        label = tk.Label(self, text='Session:',font=self.controller.messFont,justify="left",width=_iWidth, anchor = 'w')
        label.place(height=_iHeight, width=_iWidth, x=int(leftoffset*_scale), y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+5
        _iWidth=int(400*_scale)
        label = tk.Label(self, text=f'\t\t{self.controller.gensession}',font=self.controller.messFont,justify="left",width=_iWidth, anchor = 'w')
        label.place(height=_iHeight, width=_iWidth, x=int(leftoffset*_scale), y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+20

        _iWidth=int(250*_scale)

        label = tk.Label(self, text='Session Average:',font=self.controller.messFont,justify="left",width=_iWidth, anchor = 'w')
        label.place(height=_iHeight, width=_iWidth, x=int(leftoffset*_scale), y=int(int(_vloc*_scale)))
        #_vloc+=_iHeight+5
        
        self.ankleAngleOffset = 0.0
        self.state = 0
        self.oldState = 0
        self.stepKneeFlex = []
        self.stepAnkleFlex = []
        self.lastStepKneeFlex = []
        self.lastStepAnkleFlex = []

        self.startStepRecord = False

        self.fStates = np.zeros(self.sampsize)
        self.kneeAngles = np.zeros(self.sampsize)
        self.footAnkleAngles = np.zeros(self.sampsize)
        self.kneeProxAngles = np.zeros(self.sampsize)
        self.kneeDistAngles = np.zeros(self.sampsize)
        self.oldResKnee = 0.
        self.oldResFoot = 0.
        _sampleChoices = ['latest','latest 2','latest 4','latest 8','latest 16']
        _sampleOptions = tk.StringVar(self)
        _sampleOptions.set('latest 16') # set the default option
        _dropSamples = tk.OptionMenu(self , _sampleOptions , *_sampleChoices )
        _dropSamples.config(height=50)
        _iHeight=int(30*_scale)
        _dropSamples.place(height=_iHeight, width=_iWidth, x=int((_width/4)*_scale)-50, y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+10
        
        leftoffset = 7
        _iHeight=int(50*_scale)
        _iWidth=int(234*_scale)
        button = tk.Button(self, text="Save Session",
                           command=lambda: self.saveSession(),height=60, bg="GREEN")
        button.place(height=_iHeight, width=_iWidth, x=int(leftoffset*_scale), y=int(int(_vloc*_scale)))

        button = tk.Button(self, text="Generate Chart >>",
                           command=lambda: self.genChart(),height=60, bg="GREEN")
        button.place(height=_iHeight, width=_iWidth, x=int((_width/4)*_scale), y=int(int(_vloc*_scale)))
        _vloc+=_iHeight+15
        
        self.bigfig = Figure(figsize = (5, 5),dpi = 100)
        # adding the subplot
        self.mainPlot = self.bigfig.add_subplot(111)
        self.mainPlot.set_title("Angles Flex - Ext [deg]")
        # plotting the graph
        self.kneeline, = self.mainPlot.plot(np.zeros(self.sampsize),"black", label="Knee Flex Angle")
        self.ankleline, = self.mainPlot.plot(np.zeros(self.sampsize),"red", label = "Ankle Flex Angle")
        # creating the Tkinter canvas
        # containing the Matplotlib figure
        self.mainPlot.set_ylabel("flex angles (degrees)")
        self.mainPlot.set_xlabel("time")
        self.mainPlot.legend(loc='best')
        self.bigfigcanvas = FigureCanvasTkAgg(self.bigfig, master = self)

        self.littlefig = Figure(figsize = (5, 5),dpi = 100)
        # list of squares
        # adding the subplot
        self.secondPlot = self.littlefig.add_subplot(111)
        self.secondPlot.set_title("Realtime Chart")
        self.secondPlot.set_ylim(-90, 100)
        self.secondPlot.set_ylabel("flex angles(degrees)")
        self.secondPlot.set_xlabel("time")
        self.secondPlot.legend(loc='best')

        # plotting the graph
        self.kneeAnglesline,=self.secondPlot.plot(self.kneeAngles,"r-")
        self.fStatesline,=self.secondPlot.plot(self.fStates,"g-")
        #self.kneeProxAnglesline,=self.secondPlot.plot(self.kneeProxAngles,"b-",label="proximal knee sensor")
        #self.kneeDistAnglesline,=self.secondPlot.plot(self.kneeDistAngles,"g-", label="distal knee sensor")
        self.footAnkleAnglesline,=self.secondPlot.plot(self.footAnkleAngles,"orange", label = "foot sensor")
        # creating the Tkinter canvas
        # containing the Matplotlib figure
        self.littlefigcanvas = FigureCanvasTkAgg(self.littlefig, master = self)

        self.bigfigcanvas.draw()
        self.littlefigcanvas.draw()
        
        _iHeight=int(250*_scale)
        #_iWidth=int(250*_scale)
        _iWidth=int(600*_scale)

        self.littlefigcanvas.get_tk_widget().place(height=_iHeight, width=_iWidth, x=leftoffset, y=int(_vloc))
        
        _iHeight=int(550*_scale)
        _iWidth=int(550*_scale)
        _vloc=50 #100-5-_iHeight
        
        self.xOffset = int(_width/2)

        self.bigfigcanvas.get_tk_widget().place(height=_iHeight, width=_iWidth, x=self.xOffset, y=int(_vloc))
        _vloc+=_iHeight+15
        
        _iHeight=int(50*_scale)
        _iWidth=int(234*_scale)
        button = tk.Button(self, text="Export Chart",
                           command=lambda: self.saveSession(),height=60, bg="GREEN")
        button.place(height=_iHeight, width=_iWidth, x=self.xOffset, y=int(int(_vloc*_scale)))
        
        self.startLoopDeLoop()

async def scanBle():
    global choicesEM
    devices = await BleakScanner.discover()
    choicesEM=[]
    for d in devices:
        #print(d)
        n=str(d).split(" ")
        m=n[0].strip().split(":")
        p="{}{}".format(m[len(m)-3],m[len(m)-2])
        choicesEM.append(p)
        print(m)
    print(choicesEM)
    app.dropEM.configure(cnf=None, *choicesEM)
    app.dropSP.configure(cnf=None, *choicesEM)

nest_asyncio.apply()
#fig = plt.Figure()
#immg = plt.imread("./images/targetDist.png")
#x = np.arange(0, 2*np.pi, 0.01)
#ax = fig.add_subplot(111)
#ax.imshow(immg)
#line, = ax.plot(x, np.sin(x))
if __name__ == "__main__":
    #print(genSessionCode())
    asyncio.set_event_loop_policy(aiotkinter.TkinterEventLoopPolicy())
    #loop2 = asyncio.new_event_loop()
    loop = asyncio.get_event_loop()
    app = mainClass()
    loop.run_forever()
    #app.mainloop()

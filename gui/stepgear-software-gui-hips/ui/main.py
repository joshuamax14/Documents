# --- Imports
#MODE_TEST=False
MODE_TEST=True

from scipy.signal import savgol_filter
from scipy import interpolate
from scipy import signal
import pandas as pd

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

#import mdtdcomputeSvc as md
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
f_handler = logging.FileHandler(f"app{datetime.datetime.now().strftime('%Y-%m-%d')}.log")
# Create formatters and add it to handlers
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)
# Add handlers to the logger
logger.addHandler(f_handler)
logger.info('Software Started')

_tprocessName = 'thingyAngles'
#_tprocessName = 'thingy'

#spike removal pandas and forwards-backwards exponential weighted moving average
# Distance away from the FBEWMA that data should be removed.
DELTA = 90
# clip data above this value:
HIGH_CLIP = 270
# clip data below this value:
LOW_CLIP = -270 #-180
# How many samples to run the FBEWMA over.
SPAN = 20 #20 is also ok

MIDFOOTPERCENT = 0.19
#MIDFOOTPERCENT = 0.20

SYNC_DELAY = 2

def clip_data(unclipped, high_clip, low_clip):
    ''' Clip unclipped between high_clip and low_clip. 
    unclipped contains a single column of unclipped data.'''
    #np_unclipped = np.array(unclipped)
    np_unclipped = unclipped
    # clip data above HIGH_CLIP or below LOW_CLIP
    cond_high_clip = (np_unclipped > HIGH_CLIP) | (np_unclipped < LOW_CLIP)
    np_clipped = np.where(cond_high_clip, np.nan, np_unclipped)
    return np_clipped

def ewma_fb(df_column, span):
    ''' Apply forwards, backwards exponential weighted moving average (EWMA) to df_column. '''
    # Forwards EWMA.
    fwd = pd.Series.ewm(pd.DataFrame(df_column), span=span).mean()
    # Backwards EWMA.
    bwd = pd.Series.ewm(pd.DataFrame(df_column[::-1]),span=span).mean()
    # Add and take the mean of the forwards and backwards EWMA.
    stacked_ewma = np.vstack(( fwd, bwd[::-1] ))
    fb_ewma = np.mean(stacked_ewma, axis=0)
    return fb_ewma
    #print(fwd)
    

def remove_outliers(spikey, fbewma, delta):
    ''' Remove data from df_spikey that is > delta from fbewma. '''
    np_spikey = np.array(spikey)
    np_fbewma = np.array(fbewma)
    cond_delta = (np.abs(np_spikey-np_fbewma) > delta)
    np_remove_outliers = np.where(cond_delta, np.nan, np_spikey)
    return np_remove_outliers


def is_float(v):
    try:
        f=float(v)
    except ValueError:
        return False
    return True

def checkAndKill(pname):
    if MODE_TEST:
        return
    _processKilled=0
    try:
        for process in psutil.process_iter():
            if process.name() == _tprocessName:
                print(process)
                logger.info(f"killing {str(process)}")
                process.kill()
                _processKilled+=1
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        print("Processes not detected or access denied.")
        #pass
    logger.info(f"{str(_processKilled)} processes were killed.")

def checkPID(pid):
    if MODE_TEST:
        return False
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
    if MODE_TEST:
        return -1
    #pidd = subprocess.Popen(['./thingy', '-d', add1, '-s', stype])
    #pidd = subprocess.Popen(['./thingy', '-d', add1, '-s', stype])
    pidd = subprocess.Popen([f"./{_tprocessName}", '-d', add1, '-s', stype])
    logger.info(f"{stype} process {pidd} started")
    return pidd
    
def genSessionCode():
    #Generate a datetime string for session
    now = datetime.datetime.now()
    strl = string.ascii_uppercase
    trailing= ''.join(random.choice(strl) for i in range(7))
   
    return "{}{}{}-{}:{}-{}".format(now.year,str(now.month).rjust(2,'0'),str(now.day).rjust(2,'0'),str(now.hour).rjust(2,'0'),str(now.minute).rjust(2,'0'),trailing)

def getTimestamp():
    now = datetime.datetime.now()
    return "{}{}-{}:{}:{}".format(str(now.month).rjust(2,'0'),str(now.day).rjust(2,'0'),str(now.hour).rjust(2,'0'),str(now.minute).rjust(2,'0'),str(now.second).rjust(2,'0'))

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

        if MODE_TEST:
            self.show_frame("MainPage")
        else:
            self.show_frame("StartPage")
        
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
        self.controller.tkvarHP.set("Select Hips Assy")
        self.controller.dropEM['menu'].delete(0,"end")
        self.controller.dropSP['menu'].delete(0,"end")
        self.controller.dropHP['menu'].delete(0,"end")
        for dev in self.controller.devList["knee"]:
            print(dev)
            choicesEM.append(dev)
            self.controller.dropEM["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarEM, dev))
        for dev in self.controller.devList["foot"]:
            print(dev)
            choicesSP.append(dev)
            self.controller.dropSP["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarSP, dev))
        self.controller.show_frame("DeviceSelection")
        for dev in self.controller.devList["hips"]:
            print(dev)
            choicesHP.append(dev)
            self.controller.dropSP["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarHP, dev))
        self.controller.show_frame("DeviceSelection")

    async def loadBle(self):
        logger.info(f"running search...")
        self.controller.statusbar.config(text="Searching for devices...")
        await os.system("python3 ./discoverySvc.py")
        await asyncio.sleep(5)

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
        hpList=self.controller.devList["hips"]
        try:
            self.controller._em=str(self.controller.tkvarEM.get())
            #self.controller._sp=str(self.controller.tkvarSP.get())
            #self.controller._hp=str(slf.controller.hpvarSP.get())
            self.controller.emAdd = emList[self.controller._em]
            self.controller.spAdd = "" #spList[self.controller._sp]
            self.controller.hpAdd = "" #hpList[selfcontroller._hp]
            print(f"testing {emList}")
        except:
            self.controller._em=""
            self.controller._sp=""
            self.controller._hp=""
            self.controller.emAdd = ""
            self.controller.spAdd = ""
            self.controller.hpAdd = ""
        logger.info(f"checking emboard {self.controller._em}")
        if ("StepGear_KA" in self.controller._em):
            #valid emboard input
            #if ("StepGear_FA" in self.controller._sp):
            #valid sensor also
            #check if there are current running streaming service, then close them
            #start thingy stream service -> os.system("./thingy -d {} -e {}".format(self.controller._em, self.controller._sp))
            logger.info(f"OK knee board {self.controller._em}")
            #logger.info(f"OK knee board {self.controller._em} foot board {self.controller._sp}")
            #print(str(self.controller.devList["em"]))
            self.controller.statusText = "Knee: {}".format(self.controller._em)
            self.controller.statusbar.config(text=self.controller.statusText)
            logger.info(f"switching to HOME view")
            self.controller.show_frame("MainPage")
            #self.controller.calibFile = f"./{self.controller._em[-4:]}-{self.controller._sp[-4:]}.npy"
            checkAndKill(_tprocessName)
            self.controller.sysReady=False
            self.controller.processId= runme(self.controller.emAdd,"knee")
            #self.controller.processId2= runme(self.controller.spAdd,"foot")
            self.controller.sysReady=True    
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
        self.controller.tkvarHP.set("Select Hips Assy")
        self.controller.dropEM['menu'].delete(0,"end")
        self.controller.dropSP['menu'].delete(0,"end")
        self.controller.dropHP['menu'].delete(0,"end")
        for dev in self.controller.devList["knee"]:
            print(dev)
            choicesEM.append(dev)
            self.controller.dropEM["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarEM, dev))
        for dev in self.controller.devList["foot"]:
            print(dev)
            choicesSP.append(dev)
            self.controller.dropSP["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarSP, dev))
        self.controller.show_frame("DeviceSelection")
        for dev in self.controller.devList["hips"]:
            print(dev)
            choicesHP.append(dev)
            self.controller.dropSP["menu"].add_command(label=dev, command=tk._setit(self.controller.tkvarHP, dev))
        self.controller.show_frame("DeviceSelection")
    async def loadBle(self):
        #await os.system("python3 ./discoverySvc.py")
        await asyncio.sleep(5)
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
        #label.pack(side="top", fill="y", pady=10)
        self.controller.tkvarSP = tk.StringVar(self)
        self.controller.tkvarSP.set('   ') # set the default option
        self.controller.dropSP = tk.OptionMenu(self , self.controller.tkvarSP , *choicesSP )
        self.controller.dropSP.config(height=2)
        #self.controller.dropSP.pack(side="top", pady=10)
        
        label = tk.Label(self, text='Hips Assembly:',font=self.controller.messFont)
        #label.pack(side="top", fill="y", pady=10)
        self.controller.tkvarHP = tk.StringVar(self)
        self.controller.tkvarHP.set('   ') # set the default option
        self.controller.dropHP = tk.OptionMenu(self , self.controller.tkvarHP , *choicesHP )
        self.controller.dropHP.config(height=2)
        #self.controller.dropSP.pack(side="top", pady=10)
        
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
choicesHP = [ 'Pizza','Lasagne','Fries','Fish','Potato']
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
        #logger.info("loop stopped")
        self.startLoopDeLoop()
    async def loopDeLoop(self):
        self.oldKneeCount=0
        self.oldFootCount=0
        self.oldHipsCount=0
        while True:
            #get new data
            runagain=False
            footCount, footProx, states= stream.neoReadFootAngles()
            kneeCount, kneeProx, kneeDist= stream.neoReadKneeAngles()
            hipsCount, hipsProx = stream.neoReadHipsAngles()
            #print(self.nomovementknee,self.oldResKnee,kneeCount)
            if self.controller.sysReady:
                if self.oldResKnee == kneeCount:
                    #same data. stream halted? try running again
                    self.nomovementknee+=1
                    #don't use this data, use previous
                    kneeProx[0]=kneeProx[3]
                    kneeProx[1]=kneeProx[3]
                    kneeProx[2]=kneeProx[3]
                    kneeDist[0]=kneeDist[3]
                    kneeDist[1]=kneeDist[3]
                    kneeDist[2]=kneeDist[3]
                    if self.nomovementknee>1:
                        break
                    #runagain = True
                else:
                    self.nomovementknee=0
                    self.oldResKnee = kneeCount
                if self.oldResFoot == footCount:
                    #same data. stream halted? try running again
                    self.nomovementfoot+=1
                    #print(f"no foot!!! {self.nomovementfoot}")
                    #runagain = True
                    #don't use this data, use previous
                    footProx[0]=footProx[3]
                    footProx[1]=footProx[3]
                    footProx[2]=footProx[3]
                    states[0]=states[3]
                    states[1]=states[3]
                    states[2]=states[3]
                    if self.nomovementfoot>1:
                        break
                else:
                    self.nomovementfoot=0
                    self.oldResFoot = footCount
                if self.oldResHips == hipsCount:
                    #same data. stream halted? try running again
                    self.nomovementhips+=1
                    #print(f"no hips!!! {self.nomovementhips}")
                    #runagain = True
                    #don't use this data, use previous
                    hipsProx[0]=hipsProx[3]
                    hipsProx[1]=hipsProx[3]
                    hipsProx[2]=hipsProx[3]
                    #states[0]=states[3]
                    #states[1]=states[3]
                    #states[2]=states[3]
                    if self.nomovementhips>1:
                        break
                else:
                    self.nomovementhips=0
                    self.oldResHips= hipsCount
                
                if self.nomovementknee>1:
                    self.nomovementknee=0
                    #print("NO KNEE DATA")
                    break
                if self.nomovementfoot>1:
                    self.nomovementfoot=0
                    #print("NO FOOT DATA")
                    break
                if self.nomovementhips>1:
                    self.nomovementhips=0
                    #print("NO HIPS DATA")
                    break
                if len(footProx)==4:
                    #good foot data, check knee
                    if len(kneeProx)==4:
                        #good knee data, check knee
                        if len(hipsProx)==4:
                            #good hips data, proceed with compute
                            for n in range(0,4):
                                if footProx[n]>180:
                                    footProx[n]=footProx[n]-360
                                if hipsProx[n]>180:
                                    hipsProx[n]=hipsProx[n]-360
                                if kneeProx[n]>180:
                                    kneeProx[n]=kneeProx[n]-360
                                if kneeDist[n]>180:
                                    kneeDist[n]=kneeDist[n]-360

                            self.kneeProx[:-4]=self.kneeProx[4:]
                            self.kneeProx[-4:]=kneeProx
                            self.kneeDist[:-4]=self.kneeDist[4:]
                            self.kneeDist[-4:]=kneeDist
                            self.footProx[:-4]=self.footProx[4:]
                            self.footProx[-4:]=footProx
                            self.hipsProx[:-4]=self.hipsProx[4:]
                            self.hipsProx[-4:]=hipsProx
                            #self.footProx[-4:]=footProx-14
                            self.fStates[:-4]=self.fStates[4:]
                            self.fStates[-4:]=states
                            cleandat={}
                            cleandat["clippedknp"]=clip_data(self.kneeProx[-(SPAN*5):], HIGH_CLIP, LOW_CLIP)
                            cleandat["clippedknd"]=clip_data(self.kneeDist[-(SPAN*5):], HIGH_CLIP, LOW_CLIP)
                            cleandat["clippedfp"] =clip_data(self.footProx[-(SPAN*5):], HIGH_CLIP, LOW_CLIP)
                            cleandat["clippedhp"] =clip_data(self.hipsProx[-(SPAN*5):], HIGH_CLIP, LOW_CLIP)
                            cleandat["ewmadataknp"]=ewma_fb(cleandat["clippedknp"], SPAN)
                            cleandat["ewmadataknd"]=ewma_fb(cleandat["clippedknd"], SPAN)
                            cleandat["ewmadatafp"] =ewma_fb(cleandat["clippedfp"] , SPAN)
                            cleandat["ewmadatahp"] =ewma_fb(cleandat["clippedhp"] , SPAN)
                            cleandat["nooutliersknp"]=remove_outliers(cleandat["clippedknp"].tolist(), cleandat["ewmadataknp"].tolist(), DELTA)
                            cleandat["nooutliersknd"]=remove_outliers(cleandat["clippedknd"].tolist(), cleandat["ewmadataknd"].tolist(), DELTA)
                            cleandat["nooutliersfp"] =remove_outliers(cleandat["clippedfp"].tolist() , cleandat["ewmadatafp"].tolist() , DELTA)
                            cleandat["nooutliershp"] =remove_outliers(cleandat["clippedhp"].tolist() , cleandat["ewmadatahp"].tolist() , DELTA)
                            cleandat["y_interpolatedknp"] = self.kneeProx[-(SPAN*5):] 
                            cleandat["y_interpolatedknd"] = self.kneeDist[-(SPAN*5):] 
                            cleandat["y_interpolatedfp"]  = self.footProx[-(SPAN*5):] 
                            cleandat["y_interpolatedhp"]  = self.hipsProx[-(SPAN*5):] 
                            self.cleankneeProx[:-(SPAN*5)]=self.cleankneeProx[(SPAN*5):]
                            self.cleankneeProx[-(SPAN*5):]=np.asarray(cleandat["y_interpolatedknp"])
                            self.cleankneeDist[:-(SPAN*5)]=self.cleankneeDist[(SPAN*5):]
                            self.cleankneeDist[-(SPAN*5):]=np.asarray(cleandat["y_interpolatedknd"])
                            self.cleanfootProx[:-(SPAN*5)]=self.cleanfootProx[(SPAN*5):]
                            self.cleanfootProx[-(SPAN*5):]=np.asarray(cleandat["y_interpolatedfp"])
                            self.cleanhipsProx[:-(SPAN*5)]=self.cleanhipsProx[(SPAN*5):]
                            self.cleanhipsProx[-(SPAN*5):]=np.asarray(cleandat["y_interpolatedhp"])
                            kangletmp=[]
                            aangletmp=[]
                            hangletmp=[]
                            for n in range(0,4):
                                #knee flexion compute
                                self.stateTrans[0]=self.stateTrans[1]
                                self.stateTrans[1]=states[n]
                                #print(self.stateTrans)
                                if self.stateTrans[0]==0:
                                    if self.stateTrans[1]==1:
                                        #possible heelstrike
                                        self.checkForHeelStrike=True
                                        self.delay = SYNC_DELAY
                                diff = (self.cleankneeDist[(self.sampsize-4)+n]-self.cleankneeProx[(self.sampsize-4)+n])
                                #diff = self.cleankneeDist[(self.sampsize-4)+n]
                                kangletmp.append(diff)
                                #diff = ((90-self.cleanfootProx[(self.sampsize-4)+n])-self.cleankneeDist[(self.sampsize-4)+n])-46.4 +20
                                #diff = ((self.cleankneeDist[(self.sampsize-4)+n]+90) + self.cleanfootProx[(self.sampsize-4)+n])
                                #diff = ((self.cleanfootProx[(self.sampsize-4)+n] +14) - (self.cleankneeDist[(self.sampsize-4)+n]) )
                                diff = -1*(self.cleankneeDist[(self.sampsize-4)+n] - self.cleanfootProx[(self.sampsize-4)+n]+90)
                                #diff = (self.cleanfootProx[(self.sampsize-4)+n])
                                aangletmp.append((diff))
                                diff = -1*(self.cleanhipsProx[(self.sampsize-4)+n]) + self.cleankneeProx[(self.sampsize-4)+n]
                                hangletmp.append((diff))  
                            self.kneeFlexion[:-4] = self.kneeFlexion[4:]
                            self.kneeFlexion[-4:] = kangletmp
                            self.ankleFlexion[:-4] = self.ankleFlexion[4:]
                            self.ankleFlexion[-4:] = aangletmp
                            self.hipsFlexion[:-4] = self.hipsFlexion[4:]
                            self.hipsFlexion[-4:] = hangletmp
                            toeoffindex=999
                            if self.checkForHeelStrike:
                                self.delay-=1
                            if self.delay==0:
                                self.delay=SYNC_DELAY
                                self.checkForHeelStrike=False
                                #print(f"knee flex: {self.kneeFlexion[-1:]}")
                                startfound=False
                                endfound=False
                                toesofffound=False
                                endindex = 0
                                startindex = 0
                                dell=12
                                #print(f"checking heelstrike ")
                                for z in range(1,200):
                                #for z in range(1,self.sampsize):
                                    n=self.sampsize-z
                                    #print(f"checking {self.fStates[n]} and {self.fStates[n-1]}")
                                    if self.fStates[n]==1:
                                        if (n>=3):
                                            if (self.fStates[n-1] == 1) and (self.fStates[n-2] == 0) and (self.fStates[n-3] == 0):
                                            #found valid heelstrike
                                                if endfound==False:
                                                    #found the end
                                                    endfound=True
                                                    endindex=n-1 #+dell #+((SYNC_DELAY-0)*2)
                                                else:
                                                    #found start of heelstrike
                                                    if endindex-n>5:
                                                        startindex = n-1 #+dell  #+((SYNC_DELAY-0)*2)
                                                        startfound=True
                                                        break
                                        else:
                                            #no start in this sample set.
                                            break
                                rawkneeFlex=[]
                                rawankleFlex=[]
                                rawtoeoff=[]
                                rawhipsFlex=[]
                                toeoffLocation=0.0 
                                midfootLocation = 0
                                midfootfound=False
                                if (startfound):
                                    durr = endindex-startindex
                                    print(f"{self.durr}  HEELSTRIKE end {endindex} - start {startindex} = {endindex-startindex}")
                                    #if durr>self.durr*1.5:
                                    #    startindex = endindex-self.durr
                                    for n in range(startindex,endindex-1):
                                        if self.fStates[n]==0: #lifted foot
                                            if self.fStates[n-1]==0: #lifted foot
                                                if self.fStates[n-2]==2: #toestrike
                                                    if self.fStates[n-3]==2: #toestrike
                                                        toeoffindex=n-1
                                                        if midfootfound:
                                                            toeoffLocation = MIDFOOTPERCENT + (toeoffindex-(midfootLocation))/durr
                                                        else:
                                                            toeoffLocation = float(toeoffindex - startindex)/durr
                                                        break
                                        elif not midfootfound:
                                            if self.fStates[n]==3: #midfoot
                                                if self.fStates[n-1]==1: #heelstrike
                                                    midfootLocation = n
                                                    midfootfound=True
                                            elif self.fStates[n]==2: #toe
                                                if self.fStates[n-1]==1: #heel
                                                    if self.fStates[n-2]==1: #heel
                                                        midfootLocation = n-2
                                                        midfootfound=True
                                    if midfootfound:
                                        startindex = endindex - int((endindex - midfootLocation)/(1.0-MIDFOOTPERCENT))
                                    dell=int((endindex-startindex)*.0)
                                    #dell=int((endindex-startindex)*.1)
                                    #dell=int((endindex-startindex)*.05)
                                    startindex+=dell
                                    #startindex-=0
                                    endindex+=dell
                                    #toeoffindex-=dell
                                    rawtoeoff = self.fStates[startindex:endindex]
                                    print("HEELSTRIKE found")
                                    #lets plot it
                                    nElements = endindex-startindex
                                    #filtKnee=savgol_filter(self.kneeFlexion,6,1)
                                    filtKnee=savgol_filter(self.kneeFlexion,6,1)
                                    filtFoot=savgol_filter(self.ankleFlexion,10,1)
                                    filtHips=savgol_filter(self.hipsFlexion,10,1)
                                    #filtFoot=savgol_filter(self.ankleFlexion,16,8)
                                    #filtFoot=savgol_filter(cleandat["y_interpolated"],16,3)
                                    filtKnee=filtKnee[startindex:endindex]
                                    filtFoot=filtFoot[startindex:endindex]
                                    filtHips=filtHips[startindex:endindex]
                                    #tmean=np.mean(filtFoot)
                                    self.mainPlot.clear()
                                    self.main2Plot.clear()
                                    self.main3Plot.clear()
                                    reso = np.abs((nElements)/100.0)
                                    xnew=np.arange(0, 100, reso)
                                    xnewfoot=np.arange(0, 100, reso)
                                    xx = np.linspace(0,100, num = len(filtKnee)) # np.arange(0, len(filtKnee),1)
                                    xxhips = np.linspace(0,100, num = len(filtHips)) # np.arange(0, len(filtHips),1)
                                    #xxnewfoot = np.linspace(-20,100, num = len(filtFoot))
                                    #f = interpolate.interp1d(xx, filtKnee)
                                    self.normKneePlot = self.mainPlot.imshow(self.kneeNormal,extent=[0,100,-10,90])
                                    self.normAnklePlot = self.main2Plot.imshow(self.ankleNormal,extent=[0,100,-30,40])
                                    self.normHipsPlot = self.main3Plot.imshow(self.hipsNormal,extent=[0,100,-11.4,31])
                                    newfiltKnee = np.interp(xnew,xx,filtKnee) #f(xnew)
                                    newfiltFoot = np.interp(xnew,xx,filtFoot) #f(xnew)
                                    newfiltHips = np.interp(xnew,xx,filtHips) #f(xnew)
                                    #tmean=np.mean(newfiltFoot[20:])
                                    #newfiltFoot=newfiltFoot-tmean
                                    #newfiltFoot=newfiltFoot-tmean #+5
                                    #newfiltFoot=newfiltFoot-12.7
                                    #newfiltKnee=newfiltKnee-np.min(newfiltKnee)+4
                                    self.stepsData[self.stepsDataCount]["datahips"]=newfiltHips
                                    self.stepsData[self.stepsDataCount]["verthips"]=100*toeoffLocation
                                    #self.stepsData[self.stepsDataCount]["verthips"]=100*((toeoffindex-startindex)/(nElements))
                                    self.stepsData[self.stepsDataCount]["labelhips"]=f"{getTimestamp()} step {self.stepCounter}"
                                    self.stepsData[self.stepsDataCount]["dataknee"]=newfiltKnee
                                    self.stepsData[self.stepsDataCount]["vertknee"]=100*toeoffLocation
                                    #self.stepsData[self.stepsDataCount]["vertknee"]=100*((toeoffindex-startindex)/(nElements))
                                    self.stepsData[self.stepsDataCount]["labelknee"]=f"{getTimestamp()} step {self.stepCounter}"
                        
                                    self.stepsData[self.stepsDataCount]["datafoot"]=newfiltFoot
                                    self.stepsData[self.stepsDataCount]["vertfoot"]=100*toeoffLocation
                                    #self.stepsData[self.stepsDataCount]["vertfoot"]=100*((toeoffindex-startindex)/(nElements))-5
                                    self.stepsData[self.stepsDataCount]["labelfoot"]=f"step {self.stepCounter}"
                                    self.stepsDataCount +=1
                                    if self.stepsDataCount>=self.maxStepData:
                                        self.stepsDataCount = 0
                                    self.mainPlot.set_xlim(0, 100)
                                    self.main2Plot.set_xlim(0, 100)
                                    self.main3Plot.set_xlim(0, 100)
                                    for tempp in range(0, self.maxStepData):
                                        if len(self.stepsData[tempp])>0:
                                            #valid step?
                                            self.mainPlot.plot(xnew,self.stepsData[tempp]["dataknee"],self.lineorders[tempp], label=self.stepsData[tempp]["labelknee"])
                                            #self.mainPlot.plot(xnew,self.stepsData[tempp]["dataknee"],self.lineorders[tempp+2], label=self.stepsData[tempp]["labelknee"])
                                            self.main2Plot.plot(xnewfoot,self.stepsData[tempp]["datafoot"],self.lineorders[tempp])
                                            self.main3Plot.plot(xnew,self.stepsData[tempp]["datahips"],self.lineorders[tempp], label=self.stepsData[tempp]["labelhips"])
                                            self.mainPlot.axvline(x=self.stepsData[tempp]["vertknee"], color='red', linestyle='-')
                                            self.main2Plot.axvline(x=self.stepsData[tempp]["vertfoot"], color='red', linestyle='-')
                                            self.main3Plot.axvline(x=self.stepsData[tempp]["verthips"], color='red', linestyle='-')

                                    self.mainPlot.plot([0,100],[0,0],"p-")
                                    mmin = np.min([np.min(self.krefy),np.min(filtKnee)])-0
                                    mmax = np.max([np.max(self.krefy),np.max(filtKnee)])+0
                                    self.mainPlot.set_ylim(mmin, mmax)
                                    #self.mainPlot.set_ylim(-5, 100)
                                
                                    self.main2Plot.plot([0,100],[0,0],"p-")
                                    mmin = np.min([np.min(self.frefy),np.min(filtFoot)])-0
                                    mmax = np.max([np.max(self.frefy),np.max(filtFoot)])+0
                                    self.main2Plot.set_ylim(mmin, mmax)
                                    
                                    self.main3Plot.plot([0,100],[0,0],"p-")
                                    mmin = np.min([np.min(self.hrefy),np.min(filtHips)])-0
                                    mmax = np.max([np.max(self.hrefy),np.max(filtHips)])+0
                                    self.main3Plot.set_ylim(mmin, mmax)
                                    
                                    self.mainPlot.legend(loc='best')
                                    self.main2Plot.legend(loc='best')
                                    self.main3Plot.legend(loc='best')
                                    self.mainPlot.axis("tight")
                                    self.main2Plot.axis("tight")
                                    self.main3Plot.axis("tight")
                                    if 100*(toeoffLocation)>50:
                                        #if 100*((toeoffindex-startindex)/(nElements))<80:
                                        if 100*(toeoffLocation)<100:
                                            if (endindex-startindex)>20:
                                                #self.durr=endindex-startindex
                                                self.bigfigcanvas.draw()
                                                pass
                                    #if 100*((toeoffindex-startindex)/(nElements))>58:
                                    #    if 100*((toeoffindex-startindex)/(nElements))<80:
                                    if 100*(toeoffLocation)>20:
                                        if 100*(toeoffLocation)<100:
                                            #take a pic
                                            fname=f"./charts/{self.controller.gensession}_step{self.imgCount}"
                                            self.bigfig.savefig(f"{fname}.png")
                                            #self.littlefig.savefig(f"./charts/{self.controller.gensession}_raw{self.imgCount}.png")
                                            self.stepCounter +=1
                                            self.imgCount+=1
                                            with open(f"{fname}-kn.dat", 'wb') as f:
                                                np.save(f,self.kneeFlexion)
                                                #np.save(f,newfiltKnee)
                                            with open(f"{fname}-ank.dat", 'wb') as f:
                                                np.save(f,self.ankleFlexion)
                                                #np.save(f,newfiltFoot)
                                            with open(f"{fname}-hip.dat", 'wb') as f:
                                                np.save(f,self.hipsFlexion)
                                                #np.save(f,newfiltHips)
                                            with open(f"{fname}-states.dat", 'wb') as f:
                                                np.save(f,self.fStates)
                            #print(self.footProx[len(self.footProx)-1],kneeDist[3],aangletmp[3])
                            #proceed plotting
                            mmin = -120 #np.min([np.min(self.fStates),np.min(self.kneeFlexion),np.min(self.ankleFlexion)])
                            mmax = 120 #np.max([np.max(self.fStates),np.max(self.kneeFlexion),np.max(self.ankleFlexion)])
                            #mmin = np.min([np.min(self.footProx),np.min(self.kneeFlexion),np.min(self.fStates)])
                            #mmax = np.max([np.max(self.footProx),np.max(self.kneeFlexion),np.min(self.fStates)])
                            #mmin = np.min(self.kneeFlexion)
                            #mmax = np.max(self.kneeFlexion)
                            #mmin = np.min(self.ankleFlexion)
                            #mmax = np.max(self.ankleFlexion)
                            self.secondPlot.set_ylim(mmin, mmax)
                            #self.kneeProxline.set_ydata((self.kneeProx))
                            self.kneeDistline.set_ydata((self.cleankneeDist[-200:])) #b
                            self.ankleFlexionlineRT.set_ydata((self.ankleFlexion[-200:])) #red
                            self.hipsFlexionlineRT.set_ydata((self.ankleFlexion[-200:])) #yellow
                            self.kneeFlexionlineRT.set_ydata((self.kneeFlexion[-200:])) #green
                            self.fStatesline.set_ydata((self.fStates[-200:]*20)) #magenta
                            #self.footProxline.set_ydata((self.footProx)) #blue
                            #self.footProxline.set_ydata((cleandat["nooutliers"]))
                            self.littlefigcanvas.draw()
                        else:
                            #missing data, don't proceed
                            print("missing hips data")
                    else:
                        print("missing knee data")  
                else:
                    print("missing foot data")      
            #await asyncio.sleep(0.01)
            await asyncio.sleep(self.interv)
            #process data
            
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.imgCount = 0
        self.durr = 30
        #self.interv = 0.05 #data point to data point interval
        self.interv = 0.01 #data point to data point interval
        self.window = 1.0 #seconds
        self.wind=int(self.window/self.interv)
        _scale = 1.0
        self.nomovementknee=0
        self.nomovementfoot=0
        self.nomovementhips=0

        
        self.controller.sysReady=True
        self.stval = 0
        self.stateTrans=[0,0]
        self.checkForHeelStrike=False
        self.kneerefx=   [ 0,    5,    12.5, 25,   37.5, 44,  50,  62.5, 75,   80.5,   95, 100]
        self.kneerefy=   [-0.2,  4.4,  13.0, 10.0, 5.0,  4.4, 5.0, 17.9, 53.9, 26.95,  0,  0]
        self.maxkneerefy=[-0.2,  6.0,  18.0, 12.0, 6.0,  5.4, 5.6, 20.9, 63.9, 34.95,  2,  0]
        self.minkneerefy=[-0.2,  2.8,  8.0,  8.0,  4.0,  3.4, 4.4, 14.9, 43.9, 18.95,  0,  0]
        #self.kneerefx=[0, 5, 10, 20, 30, 40, 45, 50, 60, 70, 80, 90, 95, 100]
        #self.kneerefy=[6.0, 6.0, 11.0, 10.0, 5.0, 4.5, 8.0, 10.0, 45.0, 62.0, 55.0, 35.0, 10.0, 6.0]
        self.newkneerefx= np.linspace(0,100, num = 1000) #np.arange(0, 100, 0.1)
        self.newkneerefy = np.interp(self.newkneerefx,self.kneerefx,self.kneerefy)
        self.krefy=savgol_filter(self.newkneerefy,4,3)
        self.maxkneerefy=np.interp(self.newkneerefx,self.kneerefx,self.maxkneerefy)
        self.maxkneerefy=savgol_filter(self.maxkneerefy,4,3)
        self.minkneerefy=np.interp(self.newkneerefx,self.kneerefx,self.minkneerefy)
        self.minkneerefy=savgol_filter(self.minkneerefy,4,3)
        
        self.footrefx=[0, 5, 10, 12.5, 25, 37.5, 50, 55, 62.5, 75, 80, 87.5, 100]
        self.footrefy=[6.0, 1.0, 0.0, 1.0, 8.0, 10.2, 12.0, 10.2, -3.6, 10.2, 12.0, 11.0, 6.0]
        #self.footrefx=[0, 5, 10, 15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 95, 100]
        #self.footrefy=[2.0, 7.0, 12.0, 7.0, 2.0, -4.0, -7.0, -10.0, -12.0, 0.0, 15.0, 3.0, 5.0, 3.0, 2.0]
        self.newfootrefx= np.linspace(0,100, num = 1000) #np.arange(0, 100, 0.1)
        self.newfootrefy = np.interp(self.newfootrefx,self.footrefx,self.footrefy)
        self.frefy=savgol_filter(self.newfootrefy,4,3)
        
        
        self.hipsrefx=[0, 5, 10, 12.5, 25, 37.5, 50, 55, 62.5, 75, 80, 87.5, 100]
        self.hipsrefy=[30.0, 31.0, 29.0, 17.8, 0.5, -10.8, -11.4, -6.1, -3.6, 20.4, 22.4, 31.0, 29.0]
        #self.hipsrefx=[0, 5, 10, 15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 95, 100]
        #self.hipsrefy=[2.0, 7.0, 12.0, 7.0, 2.0, -4.0, -7.0, -10.0, -12.0, 0.0, 15.0, 3.0, 5.0, 3.0, 2.0]
        self.newhipsrefx= np.linspace(0,100, num = 1000) #np.arange(0, 100, 0.1)
        self.newhipsrefy = np.interp(self.newhipsrefx,self.hipsrefx,self.hipsrefy)
        self.hrefy=savgol_filter(self.newhipsrefy,4,3)

        self.delay=SYNC_DELAY
        self.lineorders=["r-","bo","g-","y-"]        
        self.maxStepData = 1
        self.stepCounter = 1
        self.stepsData=[{}]
        #for tempp in range(0,self.maxStepData):
        #    self.stepsData.append({"datafoot":[]})
        self.stepsDataCount = 0
        self.sampsize = 1000
        
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
        
        self.ankleAngleOffset = 0 #104.5
        self.state = 0
        self.oldState = 0
        self.stepKneeFlex = []
        self.stepAnkleFlex = []
        self.stepHipsFlex = []
        self.lastStepKneeFlex = []
        self.lastStepAnkleFlex = []
        self.lastStepHipsFlex = []
        self.startStepRecord = False

        self.fStates = np.zeros(self.sampsize)
        self.kneeProx = np.zeros(self.sampsize)
        self.kneeDist = np.zeros(self.sampsize)
        self.footProx = np.zeros(self.sampsize)
        self.hipsProx = np.zeros(self.sampsize)
        self.cleankneeProx = np.zeros(self.sampsize)
        self.cleankneeDist = np.zeros(self.sampsize)
        self.cleanfootProx = np.zeros(self.sampsize)
        self.cleanhipsProx = np.zeros(self.sampsize)
        self.kneeFlexion = np.zeros(self.sampsize)
        self.ankleFlexion = np.zeros(self.sampsize)
        self.hipsFlexion = np.zeros(self.sampsize)
        self.oldResKnee = 0.
        self.oldResFoot = 0.
        self.oldResHips = 0.
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
        self.mainPlot = self.bigfig.add_subplot(311)
        self.main2Plot = self.bigfig.add_subplot(312,sharex=self.mainPlot)
        self.main3Plot = self.bigfig.add_subplot(313, sharex=self.mainPlot)
        self.mainPlot.set_title("Knee Flex - Ext [deg]")
        self.main2Plot.set_title("Ankle Flex - Ext [deg]")
        self.main3Plot.set_title("Hips Flex - Ext [deg]")
        # plotting the graph

        self.kneeNormal=plt.imread("./normalKneePlot.png")
        self.ankleNormal=plt.imread("./normalAnklePlot.png")
        self.hipsNormal=plt.imread("./normalHipsPlot.png")
        self.normKneePlot = self.mainPlot.imshow(self.kneeNormal,extent=[0,1000,-10,90])
        
        self.kneeFlexionLine, = self.mainPlot.plot(self.kneeFlexion,"r-", label="Knee Flex Angle")
        self.ankleFlexionLine, = self.main2Plot.plot(self.ankleFlexion,"r-", label = "Ankle Flex Angle")
        self.hipsFlexionLine, = self.main3Plot.plot(self.hipsFlexion,"r-", label = "Hips Flex Angle")
        # creating the Tkinter canvas
        # containing the Matplotlib figure
        #self.mainPlot.set_ylabel("flex angles (degrees)")
        self.main3Plot.set_xlabel("% GAIT")
        self.main2Plot.set_xlabel("% GAIT")
        self.mainPlot.legend(loc='best')
        self.mainPlot.axis("tight")
        self.main2Plot.legend(loc='best')
        self.main2Plot.axis("tight")
        self.main3Plot.legend(loc='best')
        self.main3Plot.axis("tight")
        

        self.normAnklePlot = self.main2Plot.imshow(self.ankleNormal,extent=[0,1000,-30,40])
        self.bigfigcanvas = FigureCanvasTkAgg(self.bigfig, master = self)
        self.littlefig = Figure(figsize = (5, 5),dpi = 100)

        self.normHipsPlot = self.main3Plot.imshow(self.hipsNormal,extent=[0,1000,-11.4,31])
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
        #self.kneeProxline,=self.secondPlot.plot(self.kneeProx,"r-")
        self.kneeDistline,=self.secondPlot.plot(self.kneeDist[-200:],"b-")
        self.kneeFlexionlineRT,=self.secondPlot.plot(self.kneeFlexion[-200:],"g-")
        self.ankleFlexionlineRT,=self.secondPlot.plot(self.ankleFlexion[-200:],"r-")
        self.hipsFlexionlineRT,=self.secondPlot.plot(self.hipsFlexion[-200:],"y-") #yellow
        #self.footProxline,=self.secondPlot.plot(self.footProx,"b-")
        self.fStatesline,=self.secondPlot.plot(self.fStates[-200:],"m+")
        
        #self.footProxline,=self.secondPlot.plot(self.footProx,"orange", label = "foot sensor")
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
    app.dropHP.configure(cnf=None, *choicesEM)

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

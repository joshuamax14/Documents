#!/usr/bin/python3
import numpy as np
import numpy.linalg as LA
import scipy.optimize as sp
from scipy.spatial.transform import Rotation as R

class MDTD(object):
	# You almost always want to initialize instance variables in the `__init__` method.
	def __init__(self, ):
		#for monitoring
		self.r1 = 0.0
		self.sinT = 0.0
		self.cosT = 0.0
		self.sinP = 0.0
		self.cosP = 0.0
		self.sinS = 0.0
		self.cosS = 0.0
		self.sinG = 0.0
		self.cosG = 0.0
		self.sinO = 0.0
		self.cosO = 0.0
		self.cosA3 = 0.0
		#coords
		self.x1CS1 = 0.0
		self.x1CS2 = 0.0
		self.x1CS3 = 0.0
		self.x1CS4 = 0.0
		self.x1CS5 = 0.0
		self.y1CS1 = 0.0
		self.y1CS2 = 0.0
		self.y1CS3 = 0.0
		self.y1CS4 = 0.0
		self.y1CS5 = 0.0
		self.z1CS1 = 0.0
		self.z1CS2 = 0.0
		self.z1CS3 = 0.0
		self.z1CS4 = 0.0
		self.z1CS5 = 0.0

		self.x2CS1 = 0.0
		self.x2CS2 = 0.0
		self.x2CS3 = 0.0
		self.x2CS4 = 0.0
		self.x2CS5 = 0.0
		self.y2CS1 = 0.0
		self.y2CS2 = 0.0
		self.y2CS3 = 0.0
		self.y2CS4 = 0.0
		self.y2CS5 = 0.0
		self.z2CS1 = 0.0
		self.z2CS2 = 0.0
		self.z2CS3 = 0.0
		self.z2CS4 = 0.0
		self.z2CS5 = 0.0

		self.x3CS1 = 0.0
		self.x3CS2 = 0.0
		self.x3CS3 = 0.0
		self.x3CS4 = 0.0
		self.x3CS5 = 0.0
		self.y3CS1 = 0.0
		self.y3CS2 = 0.0
		self.y3CS3 = 0.0
		self.y3CS4 = 0.0
		self.y3CS5 = 0.0
		self.z3CS1 = 0.0
		self.z3CS2 = 0.0
		self.z3CS3 = 0.0
		self.z3CS4 = 0.0
		self.z3CS5 = 0.0

		# constants for the newton-krylov function
		self.toler=1e-5
		self.Br=1.0
		self.delta=45.0
		# min value in gauss for valid value
		self.activeThresh = 0.0 #min threshold for valid fieldstrength (autocomputed)
		self.minvalid = 0.01 # min valid offseted fieldstrength
		#let d[x] be distance from coil 0 to coil 2 in mm
		self.dy = 59.4 #72.5 #60.0 72.5 #50 #;// dist bet EM1 & EM2
		self.d = 70.0
		self.h = 84.01
		self.c = 50.0
		#let R = resultant of 3d coordinates of EM0 and EM2 from sensor origin
		self.R=0.0
		#let r be ratio of distance from dM0 MM and dM1 to MM in xy, yz, and xz planes
		self.r = [1.0,1.0,1.0]
		# let B[x] be an array of raw data from sensor X,Y,Z
		self.B=[[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
		# let BRes[x] be resultant magnitude from B[x]
		self.BRes=[0.0,0.0,0.0]
		# let Bratio be ratio of resultant magnitude coil0/coil2
		self.Bratio=1.0
		# let alpha[x] be array of angles of B[x] in XY, YZ, XZ plane
		self.alpha1d=0.0
		self.alpha=[[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
		# let theta[x] be array of angles from 0 to coil[x] in XY, YZ, XZ
		self.theta=[[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
		# let silent be sensor values at no coil energized
		self.silent=[0.0,0.0,0.0]
		#let positionx be calculated relative positions of the coil in space
		self.position=[[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
		# let BPos be coordinates of Magnet Vector
		self.BPos=[[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]]
		# let solReady be indicator for complete data on all coils
		self.BReady=[False,False,False]
		self.m=0.0
		self.oldtheta = [0.0,0.0]
		self.DT1 = 0.0
		self.DT2 = 0.0
		self.T1 = 0.0
		self.T2 = 0.0
		self.DT = 0.0 #T1-T2
		self.xem=0.0
		self.yem=0.0 # x,y coordinates of sensor origin in EM1 coordinate system
		#sinT1,cosT1,sinT2,cosT2 #sin(Theta1),cos(Theta1),sin(Theta2),cos(Theta2)
		#6DOF coordinates
		self.x1EM = 0.
		self.y1EM = self.d #70
		self.z1EM = self.h #84 
		self.x2EM = 0.
		self.y2EM = self.d #70 
		self.z2EM = self.h - self.c #84 
		self.x3EM = 0.
		self.y3EM = 0.
		self.z3EM = self.d #70
		self.x4EM = 0.
		self.y4EM = 0.
		self.z4EM = self.d #70
		self.x5EM = 0.
		self.y5EM = 0.
		self.z5EM = self.d #70
		self.x6EM = 0.
		self.y6EM = 0.
		self.z6EM = self.d #70
		self.x7EM = 0.
		self.y7EM = 0.
		self.z7EM = self.d #70
		self.x8EM = 0.
		self.y8EM = 0.
		self.z8EM = self.d #70

	# getAngle() returns angle of the vector to the x,y,z axis.
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
		inner = np.inner(a, b)
		norms = LA.norm(a) * LA.norm(b)
		cos = inner / norms
		rad = np.arccos(np.clip(cos, -1.0, 1.0))
		#deg = np.rad2deg(rad)
		return(rad) 
	#def setParams(self,d,h,c):
	def setParams(self,c,h,d): #length, clearance from top, drill length
		emwidth=30.0
		self.d=d
		self.h=h
		self.c=c #50
		self.x4EM = emwidth/2
		self.y4EM = self.d
		self.z4EM = self.h

		self.x1EM = 0.0 #-emwidth/2
		self.y1EM = 70.0 #self.d #70
		self.z1EM = 80.0 #self.h #84 
		self.x2EM = 0.0 #-emwidth/2
		self.y2EM = 0.0 #self.d #70 
		self.z2EM = 80.0 #self.h - self.c #34 
		self.x3EM = 0.0 #0.0 #emwidth/2
		self.y3EM = 70.0 #self.d 
		self.z3EM = 100.0 #self.h #-self.c

		self.x1EM = 0.0 #-emwidth/2
		self.y1EM = 75.0 #self.d #70
		self.z1EM = 60.0 #self.h #84 
		self.x2EM = 0.0 #-emwidth/2
		self.y2EM = 0.0 #self.d #70 
		self.z2EM = 60.0 #self.h - self.c #34 
		self.x3EM = 0.0 #0.0 #emwidth/2
		self.y3EM = 75.0 #self.d 
		self.z3EM = 80.0 #self.h #-self.c

		#other side
		self.x5EM = emwidth/2
		self.y5EM = 0.
		self.z5EM = self.h #84 
		self.x6EM = emwidth/2
		self.y6EM = 0 #70 
		self.z6EM = self.h - self.c #84 
		self.x7EM = -emwidth/2
		self.y7EM = 0.
		self.z7EM = self.h - self.c 
		self.x8EM = -emwidth/2
		self.y8EM = 0.
		self.z8EM = self.h 
	def setConst(self,b,d):
		self.Br = b
		self.delta = d #np.deg2rad(45)
	# functions for newton_krylov
	def f(self,x):
		f0 = ((np.sin(x[0])**3)*np.sqrt(1+3*(np.cos(x[0])**2))) - (self.Br * (np.sin(x[1])**3)*np.sqrt(1+3*(np.cos(x[1])**2)))
		#f1 = np.arccos((2*np.cos(x[0]))/np.sqrt(1+3*(np.cos(x[0])**2))) - np.arccos((2*np.cos(x[1]))/np.sqrt(1+3*(np.cos(x[1])**2))) + np.rad2deg(x[0]) - np.rad2deg(x[1]) - self.delta
		f1 = np.arccos((2*np.cos(x[0]))/np.sqrt(1+3*(np.cos(x[0])**2))) - np.arccos((2*np.cos(x[1]))/np.sqrt(1+3*(np.cos(x[1])**2))) + (x[0]) - (x[1]) - self.delta
		return [f0, f1]
	def getRootsFast(self):
		#print("test")
		#self.setConst(self.Bratio,self.d)
		self.setConst(self.Bratio,self.alpha1d)
		_roots=0.0,0.0
		try:
			_roots=sp.newton_krylov(self.f, [1.57,0.785], rdiff=0.00001, method='gmres', f_tol=1e-5, verbose=False) # %np.pi
			#_roots=sp.newton_krylov(self.f, [1.57,0.785], rdiff=0.0001, method='gmres', f_tol=1e-6, verbose=False) #%np.pi
		except:
			_roots=np.copy(self.oldtheta)
			self.T1=_roots[0]
			self.T2=_roots[1]
		#print("thetas: {} Bratio: {} delta: {}".format(np.rad2deg(_roots), b,d))
		#return _roots
		self.oldtheta[0]=_roots[0]
		self.oldtheta[1]=_roots[1]
		self.T1=_roots[0]
		self.T2=_roots[1]
		Dy = self.dy
		self.cosT1=np.cos(self.T1)
		self.cosT2=np.cos(self.T2)
		self.sinT1=np.sin(self.T1)
		self.sinT2=np.sin(self.T2)
		self.m = 1+3*np.power(self.cosT1,2)
		self.DT = self.T1-self.T2
		r1 = (Dy*self.sinT2)/np.sin(self.DT)
		self.r1 = r1
		#6dof
		self.xem = r1*self.sinT1
		self.yem = r1*self.cosT1+(Dy/2.0)
		rdiffs = abs(np.rad2deg(_roots[0]-_roots[1]))
		if (rdiffs>0.1):
			print("done: {}".format(np.rad2deg(_roots)))
		else:
			print("INVALID MAGFIELD")
			self.T1=0.0
			self.T2=0.0
		#5dof
		#self.xem = abs(r1*self.sinT1)
		#self.yem = r1*self.cosT1
		self.R = np.sqrt(np.power(self.xem,2)+np.power(self.yem,2))
	def getRoots(self):
		self.setConst(self.Bratio,self.alpha1d)
		_roots=0.0,0.0
		try:
			_roots=sp.newton_krylov(self.f, [0.1,0.001], rdiff=0.1, method='gmres', f_tol=self.toler, verbose=False) #%np.pi
			#_roots=sp.newton_krylov(self.f, self.oldtheta, rdiff=0.1, method='gmres', f_tol=self.toler, verbose=True)%np.pi
		except:
			_roots=0.0,0.0
			return _roots
		#print("thetas: {} Bratio: {} delta: {}".format(np.rad2deg(_roots), b,d))
		self.T1=_roots[0]
		self.T2=_roots[1]
		Dy = self.dy
		self.cosT1=np.cos(self.T1)
		self.cosT2=np.cos(self.T2)
		self.sinT1=np.sin(self.T1)
		self.sinT2=np.sin(self.T2)
		self.m = 1+3*np.power(self.cosT1,2)
		self.DT = self.T1-self.T2
		r1 = Dy *self.sinT2/np.sin(self.DT)
		self.xem = abs(r1*self.sinT1)
		self.yem = r1*self.cosT1
		self.R = np.sqrt(np.power(self.xem,2)+np.power(self.yem,2))
	def getRootsSlow(self):
		T10 = 1.57 #;//initial value of Theta1 rads
		T20 = 0.785 #;//initial value of Theta2 = 45 deg
		Dy = self.dy
		self.T1 = T10
		self.T2 = T20
		Hr = self.Bratio
		Alphad=self.alpha1d
		for i in range(1,5):
		#for i in range(1,5):
			self.T1 = self.T1+self.DT1
			self.T2 = self.T2+self.DT2
			sinT1 = np.sin(self.T1)
			cosT1 = np.cos(self.T1)
			sinT2 = np.sin(self.T2)
			cosT2 = np.cos(self.T2)
			#print("values {}".format([sinT1,cosT1,sinT2,cosT2]))
			m = 1+3*np.power(cosT1,2)
			n = 1+3*np.power(cosT2,2)
			a = 2/m+1
			b = -2/n-1
			c = 12*np.power(sinT1,2)*np.power(cosT1,3.0)/np.sqrt(m)
			#print("c={}".format(c))
			d = -12*Hr*np.power(sinT2,2)*np.power(cosT2,3.0)/np.sqrt(n)
			u = -( np.arccos(2*cosT1/np.sqrt(m)) - np.arccos(2*cosT2/np.sqrt(n)) + self.T1-self.T2-Alphad )
			#print("u={}".format(u))
			v = -(np.power(sinT1,3.0)*np.sqrt(m)-Hr*np.power(sinT2,3.0)*np.sqrt(n))
			self.DT1 = (u*d-b*v)/(a*d-b*c)
			self.DT2 = (a*v-c*u)/(a*d-b*c)
			self.DT = self.T1-self.T2
			r1 = Dy*sinT2/np.sin(self.DT)
			#6dof
			self.xem = r1*sinT1
			self.yem = r1*cosT1+(Dy/2.0)
			#5dof
			#self.xem = abs(r1*sinT1)
			#self.yem = r1*cosT1
			self.R = np.sqrt(np.power(self.xem,2)+np.power(self.yem,2))
			#print("em coord = {}".format([self.xem,self.yem]))
			self.m=m
			self.cosT1=cosT1
			self.cosT2=cosT2
			self.sinT1=sinT1
			self.sinT2=sinT2
		#rdiffs = abs(np.rad2deg(self.T1-self.T2))
		#if (rdiffs>0.1):
		#	print("done: {}".format(np.rad2deg(_roots)))
		#else:
		#	print("diff <=0.1 deg")
		#	#self.T1=0.0
		#	#self.T2=0.0
	def getLine6dof(self):
		m=self.m
		cosT1=self.cosT1
		sinT1=self.sinT1
		cosT2=self.cosT2
		sinT2=self.sinT2
		#transform xem,yem to sensor coordinate system (x,y,z coordinates)
		#compute rotation parameters:
		cosT = self.B[0][1]/np.sqrt(np.power(self.B[0][1],2)+np.power(self.B[0][2],2)) #cosT = Y1/sqrt(sq(Y1)+sq(Z1))
		sinT = self.B[0][2]/np.sqrt(np.power(self.B[0][1],2)+np.power(self.B[0][2],2)) #sinT = Z1/sqrt(sq(Y1)+sq(Z1))
		X11 = self.B[0][0] #X1
		X21 = self.B[2][0] #X2
		Y11 = self.B[0][1]*cosT+self.B[0][2]*sinT #Y1*cosT+Z1*sinT
		Y21 = self.B[2][1]*cosT+self.B[2][2]*sinT #Y2*cosT+Z2*sinT
		Z21 = -1*self.B[2][1]*sinT+self.B[2][2]*cosT #-Y2*sinT+Z2*cosT
		cosP = X11/np.sqrt(np.power(X11,2)+np.power(Y11,2))
		sinP = Y11/np.sqrt(np.power(X11,2)+np.power(Y11,2))
		X22 = X21*cosP+Y21*sinP
		Y22 = -1*X21*sinP+Y21*cosP #check ended here.
		Z22 = Z21
		cosS = Z22/np.sqrt(np.power(Y22,2)+np.power(Z22,2))
		#sinS = -Y22/np.sqrt(np.power(Y22,2)+np.power(Z22,2))
		sinS = Y22/np.sqrt(np.power(Y22,2)+np.power(Z22,2))
		Alpha1 = np.arccos(2*cosT1/np.sqrt(m))
		Gamma = (np.pi/2.0)+(Alpha1+self.T1) #angle from xCS3-axis to xem-axis
		cosG = np.cos(Gamma)
		sinG = np.sin(Gamma)
		#new
		#Transformation for EM3 vector components, for computation of sinO and cosO:
		#Rotate CS0 to CS1 by Theta about xCS0
		X31 = self.B[1][0]			#X3 #mid EM
		Y31 = self.B[1][1]*cosT + self.B[1][2]*sinT			#Y3*cosT + Z3*sinT;
		Z31 = -self.B[1][1]*sinT + self.B[1][2]*cosT		#-Y3*sinT + Z3*cosT;
		#Rotate CS1 to CS2 by Phi about zCS1
		X32 = X31*cosP + Y31*sinP			#X31*cosP + Y31*sinP;
		Y32 = -X31*sinP + Y31*cosP			#-X31*sinP + Y31*cosP;
		#Y32 = -self.B[1][0]*sinP + self.B[1][1]*cosP			#-X31*sinP + Y31*cosP;
		#X32 = self.B[1][0]*cosP + self.B[1][1]*sinP			#X31*cosP + Y31*sinP;
		Z32 = Z31
		#Rotate CS2 to CS3 by -Sigma about xCS2
		X33 = X32
		Z33 = Y32*sinS + Z32*cosS
		#Rotate CS3 to CS4 by -Gamma about yCS3
		X34 = X33*cosG + Z33*sinG
		Z34 = -X33*sinG + Z33*cosG
		#Compute sinO, cosO
		cosA3 = (self.xem*X34-self.yem*Z34)/(self.R*self.BRes[1]) #corrects middle coil polarity
		#cosA3 = (-self.xem*X34-self.yem*Z34)/(self.R*self.BRes[1])
		cosO = self.R*cosA3/(self.xem*np.sqrt(4-(3*np.power(cosA3,2))))
		sinO = np.sqrt(1-np.power(cosO,2))
		#Transform 3 points with EMCS coordinates (0,60,0), (0,60,50), and (0,0,50) to CS0.
		#Take note EMCS not same as emCS. EMCS is fixed relative to EMA, with xEM along EM3 axis,
		#yEM along EM1/EM2 axis while emCS is "movable", with xem and yem coplanar with B1 and B2.
		#The xem-yem plane moves with MM while xEM, yEM, and zEM are fixed to EMA.
		#Rotate EMCS to CS5 by -Omega about yEM (CS5 same as emCS).
		#Use "CS5" instead of "emCS" to differentiate xCS5 from xem and yCS5 from yem.
		#-Omega is used assuming MM is in the +zEM hemisphere.
		x1CS5 = self.x1EM*cosO + self.z1EM*sinO
		y1CS5 = self.y1EM
		z1CS5 = -self.x1EM*sinO + self.z1EM*cosO
		x2CS5 = self.x2EM*cosO + self.z2EM*sinO
		y2CS5 = self.y2EM
		z2CS5 = -self.x2EM*sinO + self.z2EM*cosO
		x3CS5 = self.x3EM*cosO + self.z3EM*sinO
		y3CS5 = self.y3EM
		z3CS5 = -self.x3EM*sinO + self.z3EM*cosO
		#non-essentials
		#print("REACHED")
		x4CS5 = self.x4EM*cosO + self.z4EM*sinO
		y4CS5 = self.y4EM
		z4CS5 = -self.x4EM*sinO + self.z4EM*cosO
		x5CS5 = self.x5EM*cosO + self.z5EM*sinO
		y5CS5 = self.y5EM
		z5CS5 = -self.x5EM*sinO + self.z5EM*cosO
		x6CS5 = self.x6EM*cosO + self.z6EM*sinO
		y6CS5 = self.y6EM
		z6CS5 = -self.x6EM*sinO + self.z6EM*cosO
		x7CS5 = self.x7EM*cosO + self.z7EM*sinO
		y7CS5 = self.y7EM
		z7CS5 = -self.x7EM*sinO + self.z7EM*cosO
		x8CS5 = self.x8EM*cosO + self.z8EM*sinO
		y8CS5 = self.y8EM
		z8CS5 = -self.x8EM*sinO + self.z8EM*cosO
		#Translate CS5 to CS4
		#Rotation about zCS5 not shown (short cut)
		x1CS4 = self.xem - x1CS5
		y1CS4 = -z1CS5
		z1CS4 = self.yem - y1CS5
		x2CS4 = self.xem - x2CS5
		y2CS4 = -z2CS5
		z2CS4 = self.yem - y2CS5
		x3CS4 = self.xem - x3CS5
		y3CS4 = -z3CS5
		z3CS4 = self.yem - y3CS5
		x4CS4 = self.xem - x4CS5
		#non-essentials
		y4CS4 = -z4CS5
		z4CS4 = self.yem - y4CS5
		x5CS4 = self.xem - x5CS5
		y5CS4 = -z5CS5
		z5CS4 = self.yem - y5CS5
		x6CS4 = self.xem - x6CS5
		y6CS4 = -z6CS5
		z6CS4 = self.yem - y6CS5
		x7CS4 = self.xem - x7CS5
		y7CS4 = -z7CS5
		z7CS4 = self.yem - y7CS5
		x8CS4 = self.xem - x8CS5
		y8CS4 = -z8CS5
		z8CS4 = self.yem - y8CS5
		#Rotate CS4 to CS3 by Gamma about yCS4 -s
		x1CS3 = x1CS4*cosG - z1CS4*sinG
		y1CS3 = y1CS4
		z1CS3 = x1CS4*sinG + z1CS4*cosG
		x2CS3 = x2CS4*cosG - z2CS4*sinG
		y2CS3 = y2CS4
		z2CS3 = x2CS4*sinG + z2CS4*cosG
		x3CS3 = x3CS4*cosG - z3CS4*sinG
		y3CS3 = y3CS4
		z3CS3 = x3CS4*sinG + z3CS4*cosG
		#non-essentials
		x4CS3 = x4CS4*cosG - z4CS4*sinG
		y4CS3 = y4CS4
		z4CS3 = x4CS4*sinG + z4CS4*cosG
		x5CS3 = x5CS4*cosG - z5CS4*sinG
		y5CS3 = y5CS4
		z5CS3 = x5CS4*sinG + z5CS4*cosG
		x6CS3 = x6CS4*cosG - z6CS4*sinG
		y6CS3 = y6CS4
		z6CS3 = x6CS4*sinG + z6CS4*cosG
		x7CS3 = x7CS4*cosG - z7CS4*sinG
		y7CS3 = y7CS4
		z7CS3 = x7CS4*sinG + z7CS4*cosG
		x8CS3 = x8CS4*cosG - z8CS4*sinG
		y8CS3 = y8CS4
		z8CS3 = x8CS4*sinG + z8CS4*cosG
		#Rotate CS3 to CS2 by Sigma about xCS3
		x1CS2 = x1CS3
		y1CS2 = y1CS3*cosS + z1CS3*sinS
		z1CS2 = -y1CS3*sinS + z1CS3*cosS
		x2CS2 = x2CS3
		y2CS2 = y2CS3*cosS + z2CS3*sinS
		z2CS2 = -y2CS3*sinS + z2CS3*cosS
		x3CS2 = x3CS3
		y3CS2 = y3CS3*cosS + z3CS3*sinS
		z3CS2 = -y3CS3*sinS + z3CS3*cosS
		#non-essentials
		x4CS2 = x4CS3
		y4CS2 = y4CS3*cosS + z4CS3*sinS
		z4CS2 = -y4CS3*sinS + z4CS3*cosS
		x5CS2 = x5CS3
		y5CS2 = y5CS3*cosS + z5CS3*sinS
		z5CS2 = -y5CS3*sinS + z5CS3*cosS
		x6CS2 = x6CS3
		y6CS2 = y6CS3*cosS + z6CS3*sinS
		z6CS2 = -y6CS3*sinS + z6CS3*cosS
		x7CS2 = x7CS3
		y7CS2 = y7CS3*cosS + z7CS3*sinS
		z7CS2 = -y7CS3*sinS + z7CS3*cosS
		x8CS2 = x8CS3
		y8CS2 = y8CS3*cosS + z8CS3*sinS
		z8CS2 = -y8CS3*sinS + z8CS3*cosS
		#Rotate CS2 to CS1 by -Phi about zCS2
		x1CS1 = x1CS2*cosP - y1CS2*sinP
		y1CS1 = x1CS2*sinP + y1CS2*cosP
		z1CS1 = z1CS2
		x2CS1 = x2CS2*cosP - y2CS2*sinP
		y2CS1 = x2CS2*sinP + y2CS2*cosP
		z2CS1 = z2CS2
		x3CS1 = x3CS2*cosP - y3CS2*sinP
		y3CS1 = x3CS2*sinP + y3CS2*cosP
		z3CS1 = z3CS2
		#non-essentials
		x4CS1 = x4CS2*cosP - y4CS2*sinP
		y4CS1 = x4CS2*sinP + y4CS2*cosP
		z4CS1 = z4CS2
		x5CS1 = x5CS2*cosP - y5CS2*sinP
		y5CS1 = x5CS2*sinP + y5CS2*cosP
		z5CS1 = z5CS2
		x6CS1 = x6CS2*cosP - y6CS2*sinP
		y6CS1 = x6CS2*sinP + y6CS2*cosP
		z6CS1 = z6CS2
		x7CS1 = x7CS2*cosP - y7CS2*sinP
		y7CS1 = x7CS2*sinP + y7CS2*cosP
		z7CS1 = z7CS2
		x8CS1 = x8CS2*cosP - y8CS2*sinP
		y8CS1 = x8CS2*sinP + y8CS2*cosP
		z8CS1 = z8CS2
		#Rotate CS1 to CS0 by -Theta about xCS1.
		#These are the coordinates of points 1, 2, and 3 wrt to MMCS (CS0):
		x1S = x1CS1
		y1S = y1CS1*cosT - z1CS1*sinT
		z1S = y1CS1*sinT + z1CS1*cosT
		x2S = x2CS1
		y2S = y2CS1*cosT - z2CS1*sinT
		z2S = y2CS1*sinT + z2CS1*cosT
		x3S = x3CS1
		y3S = y3CS1*cosT - z3CS1*sinT
		z3S = y3CS1*sinT + z3CS1*cosT
		#non-essentials
		x4S = x4CS1
		y4S = y4CS1*cosT - z4CS1*sinT
		z4S = y4CS1*sinT + z4CS1*cosT
		x5S = x5CS1
		y5S = y5CS1*cosT - z5CS1*sinT
		z5S = y5CS1*sinT + z5CS1*cosT
		x6S = x6CS1
		y6S = y6CS1*cosT - z6CS1*sinT
		z6S = y6CS1*sinT + z6CS1*cosT
		x7S = x7CS1
		y7S = y7CS1*cosT - z7CS1*sinT
		z7S = y7CS1*sinT + z7CS1*cosT
		x8S = x8CS1
		y8S = y8CS1*cosT - z8CS1*sinT
		z8S = y8CS1*sinT + z8CS1*cosT
		#print("postion {}".format([x,y,z,x2,y2,z2]))
		#corrected order of stuff
		self.position[0][0]= y1S
		self.position[0][1]= -z1S
		self.position[0][2]= x1S
		self.position[1][0]= y2S
		self.position[1][1]= -z2S
		self.position[1][2]= x2S
		self.position[2][0]= y3S
		self.position[2][1]= -z3S
		self.position[2][2]= x3S
		print("p1: {} \np2: {}".format(self.position[0], self.position[1]))
		#non-essentials
		self.position[3][0]= y4S
		self.position[3][1]= -z4S
		self.position[3][2]= x4S
		self.position[4][0]= y5S
		self.position[4][1]= -z5S
		self.position[4][2]= x5S
		self.position[5][0]= y6S
		self.position[5][1]= -z6S
		self.position[5][2]= x6S
		self.position[6][0]= y7S
		self.position[6][1]= -z7S
		self.position[6][2]= x7S
		self.position[7][0]= y8S
		self.position[7][1]= -z8S
		self.position[7][2]= x8S
		#for monitoring
		self.sinT = sinT
		self.cosT = cosT
		self.sinP = sinP
		self.cosP = cosP
		self.sinS = sinS
		self.cosS = cosS
		self.sinG = sinG
		self.cosG = cosG
		self.sinO = sinO
		self.cosO = cosO
		self.cosA3 = cosA3
		self.x1CS1 = x1CS1
		self.x1CS2 = x1CS2
		self.x1CS3 = x1CS3
		self.x1CS4 = x1CS4
		self.x1CS5 = x1CS5
		self.y1CS1 = y1CS1
		self.y1CS2 = y1CS2
		self.y1CS3 = y1CS3
		self.y1CS4 = y1CS4
		self.y1CS5 = y1CS5
		self.z1CS1 = z1CS1
		self.z1CS2 = z1CS2
		self.z1CS3 = z1CS3
		self.z1CS4 = z1CS4
		self.z1CS5 = z1CS5

		self.x2CS1 = x2CS1
		self.x2CS2 = x2CS2
		self.x2CS3 = x2CS3
		self.x2CS4 = x2CS4
		self.x2CS5 = x2CS5
		self.y2CS1 = y2CS1
		self.y2CS2 = y2CS2
		self.y2CS3 = y2CS3
		self.y2CS4 = y2CS4
		self.y2CS5 = y2CS5
		self.z2CS1 = z2CS1
		self.z2CS2 = z2CS2
		self.z2CS3 = z2CS3
		self.z2CS4 = z2CS4
		self.z2CS5 = z2CS5

		self.x3CS1 = x3CS1
		self.x3CS2 = x3CS2
		self.x3CS3 = x3CS3
		self.x3CS4 = x3CS4
		self.x3CS5 = x3CS5
		self.y3CS1 = y3CS1
		self.y3CS2 = y3CS2
		self.y3CS3 = y3CS3
		self.y3CS4 = y3CS4
		self.y3CS5 = y3CS5
		self.z3CS1 = z3CS1
		self.z3CS2 = z3CS2
		self.z3CS3 = z3CS3
		self.z3CS4 = z3CS4
		self.z3CS5 = z3CS5

	def getLine(self):
		m=self.m
		cosT1=self.cosT1
		sinT1=self.sinT1
		cosT2=self.cosT2
		sinT2=self.sinT2
		#transform xem,yem to sensor coordinate system (x,y,z coordinates)
		#compute rotation parameters:
		cosT = self.B[0][1]/np.sqrt(np.power(self.B[0][1],2)+np.power(self.B[0][2],2)) #cosT = Y1/sqrt(sq(Y1)+sq(Z1))
		sinT = self.B[0][2]/np.sqrt(np.power(self.B[0][1],2)+np.power(self.B[0][2],2)) #sinT = Z1/sqrt(sq(Y1)+sq(Z1))
		X11 = self.B[0][0] #X1
		X21 = self.B[2][0] #X2
		Y11 = self.B[0][1]*cosT+self.B[0][2]*sinT #Y1*cosT+Z1*sinT
		Y21 = self.B[2][1]*cosT+self.B[2][2]*sinT #Y2*cosT+Z2*sinT
		Z21 = -1*self.B[2][1]*sinT+self.B[2][2]*cosT #-Y2*sinT+Z2*cosT
		cosP = X11/np.sqrt(np.power(X11,2)+np.power(Y11,2))
		sinP = Y11/np.sqrt(np.power(X11,2)+np.power(Y11,2))
		X22 = X21*cosP+Y21*sinP
		Y22 = -1*X21*sinP+Y21*cosP
		Z22 = Z21
		cosS = Z22/np.sqrt(np.power(Y22,2)+np.power(Z22,2))
		sinS = -Y22/np.sqrt(np.power(Y22,2)+np.power(Z22,2))
		Alpha1 = np.arccos(2*cosT1/np.sqrt(m))
		Gamma = np.pi/2+(Alpha1+self.T1) #angle from xCS3-axis to xem-axis
		cosG = np.cos(Gamma)
		sinG = np.sin(Gamma)
		#translate from CSEM to CS4:
		xCS4 = self.xem
		x2CS4 = xCS4
		#//yCS4 = 0
		#//y2CS4 = 0
		zCS4 = self.yem
		z2CS4 = self.yem-self.d #self.yem-50// point 2 is 50mm from EM1 along +yem
		#Rotate from CS4 to CS3 - rotate about yCS4 by Gamma:
		xCS3 = xCS4*cosG-zCS4*sinG
		x2CS3 = x2CS4*cosG-z2CS4*sinG
		#//yCS3 = 0
		#//y2CS3 = 0
		zCS3 = xCS4*sinG+zCS4*cosG
		z2CS3 = x2CS4*sinG+z2CS4*cosG
		#//Rotate from CS3 to CS2 - rotate about xCS3-axis by -Sigma:
		xCS2 = xCS3
		x2CS2 = x2CS3
		yCS2 = -zCS3*sinS
		y2CS2 = -z2CS3*sinS
		zCS2 = zCS3*cosS
		z2CS2 = z2CS3*cosS
		#//Rotate from CS2 to CS1 - rotate about yCS2-axis by -Phi:
		xCS1 = xCS2*cosP-yCS2*sinP
		x2CS1 = x2CS2*cosP-y2CS2*sinP
		yCS1 = xCS2*sinP+yCS2*cosP
		y2CS1 = x2CS2*sinP+y2CS2*cosP
		zCS1 = zCS2
		z2CS1 = z2CS2
		#//Rotate from CS1 to CS0 - rotate about zCS1-axis by -Theta:
		x = xCS1
		x2 = x2CS1
		y = yCS1*cosT-zCS1*sinT
		y2 = y2CS1*cosT-z2CS1*sinT
		z = yCS1*sinT+zCS1*cosT
		z2 = y2CS1*sinT+z2CS1*cosT
		#print("postion {}".format([x,y,z,x2,y2,z2]))
		self.position[0][0]=x
		self.position[0][1]=y
		self.position[0][2]=z
		self.position[1][0]=x2
		self.position[1][1]=y2
		self.position[1][2]=z2
		#print("clear line")
	def setSilent(self, values):
		self.silent[0]=values[0]
		self.silent[1]=values[1]
		self.silent[2]=values[2]
		self.activeThresh=self.minvalid*np.sqrt(np.power(self.silent[0],2)+np.power(self.silent[1],2)+np.power(self.silent[2],2))
	def setSol(self,bcoil,values):
		coil=bcoil
		#if bcoil==0:
		#	coil=2
		#elif bcoil==2:
		#	coil=0
		self.B[coil][0]=(values[0]-self.silent[0])*100
		self.B[coil][1]=(values[1]-self.silent[1])*100
		self.B[coil][2]=(values[2]-self.silent[2])*100
		#print("setting coil {} to {} - {} = {}".format(coil,values,self.silent,self.B[coil]))
		#print("setting Bcoil {} to {} <<-- {}".format(coil,self.B[coil],values))
		self.calcBRes(coil) #get resultant if above threshold
		curRes=self.BRes[coil]
		#self.calcAlpha(coil)
		#if all(_e < self.minvalid for _e in np.absolute(self.B[coil])):
			#there is an element < self.minvalid in the values. coil data not ready.
		if curRes<self.minvalid: #self.activeThresh:
			self.BReady[coil]=False
			#self.BReady[0]=False
			#self.BReady[1]=False
			#self.BReady[2]=False
			#print("{}===== {}<{}".format(coil,curRes,self.activeThresh))
		else:
			self.BReady[coil]=True
			#print("{}===== {}>{}".format(coil,curRes,self.activeThresh))
		if self.isReady():
			#print("Bcoil {}".format(coil,self.B))
			self.calcBratio()
			#self.calcAlpha()
			self.calcAlpha1d()
			#print("alpha is {}".format(np.rad2deg(self.alpha1d)))
			self.getRootsFast()
			#self.getRootsSlow()
			#self.getRoots()
			#print("roots.={}".format([self.xem,self.yem]))
			# all coil values are available, you may calculate positions for tracking
			if self.T1*self.T2 ==0.0:
				nextcoil=coil+1
				if nextcoil>2:
					nextcoil=0
				#self.BReady[nextcoil]=False
				self.BReady[0]=False
				self.BReady[1]=False
				self.BReady[2]=False
			else:
				print("getting line...")
				self.getLine6dof() #6dof
				#self.getLine() #5dof
			#print("em coords = {}".format(self.position))
			#self.calcPosition()
			#reset ready indicator
		else:
			#self.position[0][0]=0.0
			#self.position[0][1]=0.0
			#self.position[0][2]=0.0
			#self.position[1][0]=0.0
			#self.position[1][1]=0.0
			#self.position[1][2]=0.0
			#self.position[2][0]=0.0
			#self.position[2][1]=0.0
			#self.position[2][2]=0.0
			print("out of range")
	def isReady(self,):
		if self.BReady[0]:
			if self.BReady[1]:
				if self.BReady[2]:
					return True
				else:
					return False
			else:
				return False
		else:
			return False
		print("isReady check failed")
	def calcAlpha(self, coil):
		_x = self.B[coil][0]
		_y = self.B[coil][1]
		_z = self.B[coil][2]
		if _x == 0.0:
			self.alpha[coil][0]=0.0
			self.alpha[coil][2]=0.0
		else:
			self.alpha[coil][0]=np.rad2deg(np.arctan(_y/_x))
			self.alpha[coil][2]=np.rad2deg(np.arctan(_z/_x))
		if _y == 0.0:
			self.alpha[coil][1]=0.0
		else:
			self.alpha[coil][1]=np.rad2deg(np.arctan(_z/_y))
	def calcAlpha1d(self):
		x0 = self.B[0][0]
		y0 = self.B[0][1]
		z0 = self.B[0][2]
		x2 = self.B[2][0]
		y2 = self.B[2][1]
		z2 = self.B[2][2]
		self.alpha1d = (np.arccos((x0*x2+y0*y2+z0*z2)/(self.BRes[0]*self.BRes[2]))) #in rads
	def calcTransforms(self,):
		#rotate z to get B0[xy] to 0 deg
		_r = self.alpha[0]
		#print("alphas: {}".format(_r))
		r=R.from_euler("zyx",[_r[0],-1*_r[2],_r[1]],degrees=True)
		#return R.from_euler("zxy",_r,degrees=True)
		return r
	def calcBratio(self):
		self.Bratio=self.BRes[0]/self.BRes[2]
	def calcR(self):
		self.r[0]=np.sin(self.theta[0][0])/np.sin(self.theta[2][0]) #xy plane
		self.r[1]=np.sin(self.theta[0][1])/np.sin(self.theta[2][1]) #yz plane
		self.r[2]=np.sin(self.theta[0][2])/np.sin(self.theta[2][2]) #xz plane
	def calcBRes(self,coil):
		self.BRes[coil]=np.sqrt(np.power(self.B[coil][0],2)+np.power(self.B[coil][1],2)+np.power(self.B[coil][2],2))
		#print("magnitude in gauss coil {} is {}.".format(coil,self.BRes[coil]))
	def calcTheta(self):
		# get theta
		_br = self.Bratio
		#get angle between B0 and B2 vectors
		_delta = np.absolute(np.rad2deg(np.arccos(np.dot(self.B[0], self.B[2]) / (np.linalg.norm(self.B[0]) * np.linalg.norm(self.B[2])))))
		#print("_delta={}".format(_delta))
		_theta = self.getRoots(_br,_delta)
		return np.rad2deg(_theta)
	def calcPosition(self):
		_theta = self.calcTheta()
		_beta=_theta[0]-_theta[1]
		_P1=[0.0,0.0,0.0]
		_P2=[0.0,0.0,0.0]
		if _beta==0:
			print("err")
		else:
			#self.oldtheta[0]=_theta[0]
			#self.oldtheta[1]=_theta[1]
			_r1=self.dy*(np.sin(np.deg2rad(_theta[1])))/(np.sin(np.deg2rad(_beta)))
			_Mx= _r1*np.sin(np.deg2rad(_theta[0]))
			_My= _r1*np.cos(np.deg2rad(_theta[0]))
			_Mz= 0.0
			_P1=[0.0-_Mx,self.dy-_My,0.0-_Mz]
			_P2=[0.0-_Mx,0.0-_My,0.0-_Mz]
			_r = self.calcTransforms()
			_P1 = _r.apply(_P1)
			_P2 = _r.apply(_P2)
			self.position[0][0]=_P1[0]
			self.position[0][1]=_P1[1]
			self.position[0][2]=_P1[2]
			self.position[1][0]=_P2[0]
			self.position[1][1]=_P2[1]
			self.position[1][2]=_P2[2]
			#self.position[1][0]=0.0
			#self.position[1][1]=0.0
			#self.position[1][2]=0.0
			#self.position[0][0]=_Mx
			#self.position[0][1]=_My
			#self.position[0][2]=0.0
			#_r2xy
			#print("calculating")
	def getPosition(self,):
		return self.position
	def wgetPosition(self,):
		self.position[0][0]=self.x1EM
		self.position[0][1]=self.y1EM
		self.position[0][2]=self.z1EM
		self.position[1][0]=self.x2EM
		self.position[1][1]=self.y2EM
		self.position[1][2]=self.z2EM
		self.position[2][0]=self.x3EM
		self.position[2][1]=self.y3EM
		self.position[2][2]=self.z3EM
		self.position[3][0]=self.x4EM
		self.position[3][1]=self.y4EM
		self.position[3][2]=self.z4EM
		self.position[4][0]=self.x5EM
		self.position[4][1]=self.y5EM
		self.position[4][2]=self.z5EM
		self.position[5][0]=self.x6EM
		self.position[5][1]=self.y6EM
		self.position[5][2]=self.z6EM
		self.position[6][0]=self.x7EM
		self.position[6][1]=self.y7EM
		self.position[6][2]=self.z7EM
		self.position[7][0]=self.x8EM
		self.position[7][1]=self.y8EM
		self.position[7][2]=self.z8EM
		return self.position


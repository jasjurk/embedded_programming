import numpy as np
import cv2
import time

import descent
import transforms
from outputs.lights_output import Lights_udp as Out 

Marknum = 10

ids = np.load('camids.npy')
names = np.load('camnames.npy')

Camnum = len(ids)

vc = [None] * Camnum
Kinv = [None] * Camnum
K = [None] * Camnum
r = [None] * Camnum
tvec = [None] * Camnum
campos = [None] * Camnum
dist = [None] * Camnum
for i in range(Camnum):
	r[i] = np.load('rinv' + str(names[i]) + '.npy')
	tvec[i] = np.load('tvec' + str(names[i]) + '.npy')
	Kinv[i] = np.load('kinv' + str(names[i]) + '.npy')
	K[i] = np.load('K' + str(names[i]) + '.npy')
	campos[i] = transforms.calculate_campos(r[i], tvec[i])
	dist[i] = np.load('dist' + str(names[i]) + '.npy')
	prefs[camid] = np.load('prefs' + camid + '.npy', allow_pickle = True)
	vc[i] = cv2.VideoCapture(ids[i])

marks = [None] * Marknum

cv2.imshow('img',0)
	
ls = [0.0] * Marknum

out = Out(Marknum)

for inx in range(Marknum):
	avg = [[[None, None]]] * Camnum
	hits = 0
	s = False
	
	ls[inx] = 1.0
	
	
	out.light_pwm(ls)
		
	time.sleep(5)
	
	for i in range(Camnum):	
			
		ret, frame = vc[i].read()
			
		height = frame.shape[0]
		width = frame.shape[1]
			
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		#newK, roi = cv2.getOptimalNewCameraMatrix(K[i], dist[i], (width,height), 1, (width,height))
		frame = cv2.undistort(frame, K[i], dist[i], None, K[i])
		if(ret):
			cv2.imshow('imgg' + str(i),frame)
			th, threshed = cv2.threshold(frame, 100, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
			cnts = cv2.findContours(threshed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]

			s1 = 2
			xcnts = []
			max_contour = 10000  
			for cnt in cnts:
				if s1<cv2.contourArea(cnt) and cv2.contourArea(cnt) < max_contour:
					xcnts = cnt
					max_contour = cv2.contourArea(cnt)
				
					
			if(len(xcnts) >= 1):
				hits = hits + 1
				s = True
				avg[i] = [[0, 0]] 
				for p in xcnts:
					avg[i] = avg[i] + p
				avg[i] = avg[i] / len(xcnts)
				cv2.imshow('img' + str(i),cv2.circle(threshed, (int(avg[i][0][0]), int(avg[i][0][1])), radius = 10, color = (255, 0, 0)))
	if(cv2.waitKey(1) & 0xFF == ord('q')):
		break
	if(s):
		print(avg)
		if hits >= 2:	
			L = []
			for i in range(Camnum):
				if avg[i][0][0] != None:
					L.append((campos[i], transforms.calculate_XYZ(Kinv[i], r[i], tvec[i], avg[i][0][0], avg[i][0][1])))
			print(L)
			result = descent.solvePoint(L)
			print(result)
			marks[inx] = result
				
	ls[inx] = 0.0
	
print(marks)
np.save('lights', np.array(marks))
	
for i in range(Camnum):	
	vc[i].release()
cv2.destroyAllWindows()

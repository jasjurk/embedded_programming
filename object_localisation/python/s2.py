import numpy as np
import descent
import transforms
import cv2
import os
import math
import subprocess
import requests
import time
import serial
import sys
import math

from outputs.lights_output import Lights_udp as Out
	
def tr2(p):
	return (int(p[0] * 100) + 500, int(p[2] * 100) + 500)
	
def diff(p1, p2):
	x1, y1 = p1
	x2, y2 = p2
	return abs(x1 - x2) + abs(y1 - y2)

Camnum = 2
Marknum = 1

ids = np.load('camids.npy')
names = np.load('camnames.npy')
lights = np.load('lights.npy', allow_pickle = True)
lights = [None] * 8
lights[0] = [0, 0, 0]
lights[1] = [1, 0, 1]
lights[2] = [1, 0, 0]
lights[3] = [1, 0, 3]
lights[4] = [-10, 0, 0]
lights[5] = [0, 0, 2]
lights[6] = [0, 0, 1]
lights[7] = [0, 0, 3]
#ind = 0
#for i in range(3):
	#for i2 in range(3):
		#if(True):
			#lights[ind] = [i, 0, i2]
			#ind = ind + 1

Camnum = len(ids)

vc = [None] * Camnum
Kinv = [None] * Camnum
K = [None] * Camnum
r = [None] * Camnum
tvec = [None] * Camnum
campos = [None] * Camnum
dist = [None] * Camnum
newK = [None] * Camnum
newKinv = [None] * Camnum
width = 640
height = 320
for i in range(Camnum):
	r[i] = np.load('rinv' + str(names[i]) + '.npy')
	tvec[i] = np.load('tvec' + str(names[i]) + '.npy')
	Kinv[i] = np.load('kinv' + str(names[i]) + '.npy')
	K[i] = np.load('K' + str(names[i]) + '.npy')
	dist[i] = np.load('dist' + str(names[i]) + '.npy')
	newK[i], roi = cv2.getOptimalNewCameraMatrix(K[i], dist[i], (width,height), 1, (width,height))
	newKinv[i] = np.linalg.inv(newK[i])
	campos[i] = transforms.calculate_campos(r[i], tvec[i])


light_status = [False] * len(lights)
light_plus = [0.0] * len(lights)

result = (0, 0)

def draw_circle(event,x,y,flags,param):
    global result
    result = (x, y)
    if event == cv2.EVENT_LBUTTONDBLCLK:
        min_dist = 100000
        min_ind = -1
        for i in range(len(lights)):
             if diff((x, y), tr2(lights[i])) < min_dist:
                 min_dist = diff((x, y), tr2(lights[i]))
                 min_ind = i
        light_status[min_ind] = not light_status[min_ind]

cv2.namedWindow('pos')
cv2.setMouseCallback('pos',draw_circle)


background = np.zeros((1000,1000,3), np.uint8)
background = cv2.circle(background, tr2([0, 0, 0]), radius = 2, color = (255, 255, 255))
background = cv2.circle(background, tr2([1.0, 0, 0]), radius = 2, color = (255, 255, 255))
background = cv2.circle(background, tr2([0, 0, -1.0]), radius = 2, color = (255, 255, 255))
background = cv2.circle(background, tr2([1.0, 0, -1.0]), radius = 2, color = (255, 255, 255))

for i in range(Camnum):
       maxx = transforms.calculate_XYZ(newKinv[i], r[i], tvec[i], 600, 160, pre = 10.0)
       minx = transforms.calculate_XYZ(newKinv[i], r[i], tvec[i], 40, 160, pre = 10.0)
       background = cv2.circle(background, tr2(campos[i]), radius = 2, color = (255, 255, 255))
       background = cv2.line(background, tr2(campos[i]), tr2(maxx), color = (255, 255, 255))
       background = cv2.line(background, tr2(campos[i]), tr2(minx), color = (255, 255, 255))
       
out = Out(len(lights))

while True:
	if(cv2.waitKey(1) & 0xFF == ord('q')):
		break
	for inx in range(Marknum):
		#requests.get("http://" + ips[inx] + "/LEDOFF")
		avg = [[[None, None]]] * Camnum
		hits = 0
		s = False
		
		for i in range(Camnum):	
			
			frame = np.load('f' + str(i) + '0.npy')
			
			height = frame.shape[0]
			width = frame.shape[1]
			
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			frame = cv2.undistort(frame, K[i], dist[i], None, newK[i])
			if(True):
				th, threshed = cv2.threshold(frame, 100, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
				cnts = cv2.findContours(threshed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]

				s1 = 10
				xcnts = []
				max_contour = 0	  
				for cnt in cnts:
					if s1<cv2.contourArea(cnt) and max_contour < cv2.contourArea(cnt):
						xcnts = cnt
						max_contour = cv2.contourArea(cnt)
				
					
				if(len(xcnts) >= 1):
					hits = hits + 1
					s = True
					avg[i] = [[0, 0]] 
					for p in xcnts:
						avg[i] = avg[i] + p
					avg[i] = avg[i] / len(xcnts)
					#cv2.imshow('img' + str(i),cv2.circle(threshed, (int(avg[i][0][0]), int(avg[i][0][1])), radius = 10, color = (255, 0, 0)))
		#requests.get("http://" + ips[inx] + "/LEDON")
		posim = np.copy(background)
		for i in range(len(lights)):
			posim = cv2.circle(posim, tr2(lights[i]), radius = 2, color = (int(255 * light_plus[i]), int(255 * light_plus[i]), int(255 * light_plus[i])))
		if(s):
			if hits >= 2:
				L = []
				for i in range(Camnum):
					if avg[i][0][0] != None:
						L.append((campos[i], transforms.calculate_XYZ(newKinv[i], r[i], tvec[i], avg[i][0][0], avg[i][0][1])))
						posim = cv2.line(posim, tr2(campos[i]), tr2(transforms.calculate_XYZ(newKinv[i], r[i], tvec[i], avg[i][0][0], avg[i][0][1], pre = 10.0)), color = (255, 0, 0))
				#result = descent.solvePoint(L)
				
				#print(result)
				(x1, y1) = result
				max_r = 1000
				min_r = 0
				dia = 0
				while(max_r - min_r > 1):
					dia = (max_r + min_r) / 2.0
					sums = 0
					for i in range(len(lights)):
						(x2, y2) = tr2(lights[i])
						light_plus[i] = (max(0, 1 - (math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2) / float(dia))))
						sums += light_plus[i]
						if light_status[i]:
							light_plus[i] += 0.2
						light_plus[i] = min(1, light_plus[i])
						
					if sums >= 1:
						max_r = dia
					else:
						min_r = dia
				out.lights_pwm(light_plus)
				
				posim = cv2.circle(posim, result, radius = 2, color = (255, 0, 0))
				
		cv2.imshow('pos', posim)
	
cv2.destroyAllWindows()

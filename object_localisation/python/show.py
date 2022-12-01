import numpy as np
import cv2
import math

import descent
import transforms
from outputs.lights_output import Lights_udp as Out

from timeit import default_timer as timer
	
def tr2(p):
	return (int(p[0] * 100) + 500, int(p[2] * 100) + 500)
	
def diff(p1, p2):
	x1, y1 = p1
	x2, y2 = p2
	return abs(x1 - x2) + abs(y1 - y2)

Marknum = 1

ids = np.load('camids.npy')
names = np.load('camnames.npy')
lights = np.load('lights.npy', allow_pickle = True)

Camnum = len(ids)

prefs = {}

vc = [None] * Camnum
Kinv = [None] * Camnum
K = [None] * Camnum
r = [None] * Camnum
tvec = [None] * Camnum
campos = [None] * Camnum
dist = [None] * Camnum
newK = [None] * Camnum
newKinv = [None] * Camnum
for i in range(Camnum):
	prefs[names[i]] = np.load('prefs' + str(names[i]) + '.npy', allow_pickle = True).item()
	
	backend = cv2.CAP_GSTREAMER
	if prefs[names[i]]['backend'] == "L4V2":
		backend = cv2.CAP_V4L2
	if prefs[names[i]]['backend'] == "DSHOW":
		backend = cv2.DSHOW
	
	vc[i] = cv2.VideoCapture(ids[i], backend)
	if(not vc[i].isOpened()):
		print("Warning: backend " + str(backend) + " not supported for camera " + str(names[i]))
	
	if prefs[names[i]]['codec']:
		target_codec = prefs[names[i]]['codec']
		vc[i].set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(target_codec[0], target_codec[1], target_codec[2], target_codec[3]))
		
		if vc[i].get(cv2.CAP_PROP_FOURCC) != cv2.VideoWriter.fourcc(target_codec[0], target_codec[1], target_codec[2], target_codec[3]):
			print("Warning: codec " + target_codec + " unsupported on camera " + str(names[i]))
		
	if int(prefs[names[i]]['fps']) > 0:
		target_fps = int(prefs[names[i]]['fps']) 
	
		vc[i].set(cv2.CAP_PROP_FPS, target_fps)
		if vc[i].get(cv2.CAP_PROP_FRAME_WIDTH) != target_fps:
			print("Warning: fps " + str(target_fps) + " not supported on camera " + str(names[i]))
	
	if int(prefs[names[i]]['w']) > 0 and int(prefs[names[i]]['h']) > 0:
		frame_width = int(prefs[names[i]]['w']) 
		frame_height = int(prefs[names[i]]['h']) 
		
		vc[i].set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
		vc[i].set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
		if vc[i].get(cv2.CAP_PROP_FRAME_WIDTH) != frame_width or vc[i].get(cv2.CAP_PROP_FRAME_HEIGHT) != frame_height:
			print("Warning: resolution (" + str(frame_width) + "x" + str(frame_height) +  ") unsupported for camera " + str(names[i]))

	r[i] = np.load('rinv' + str(names[i]) + '.npy')
	tvec[i] = np.load('tvec' + str(names[i]) + '.npy')
	Kinv[i] = np.load('kinv' + str(names[i]) + '.npy')
	K[i] = np.load('K' + str(names[i]) + '.npy')
	dist[i] = np.load('dist' + str(names[i]) + '.npy')
	newK[i], roi = cv2.getOptimalNewCameraMatrix(K[i], dist[i], (int(vc[i].get(cv2.CAP_PROP_FRAME_WIDTH)), int(vc[i].get(cv2.CAP_PROP_FRAME_HEIGHT))), 1, (int(vc[i].get(cv2.CAP_PROP_FRAME_WIDTH)), int(vc[i].get(cv2.CAP_PROP_FRAME_HEIGHT))))
	newKinv[i] = np.linalg.inv(newK[i])
	campos[i] = transforms.calculate_campos(r[i], tvec[i])

light_status = [False] * len(lights)
light_plus = [0.0] * len(lights)

out = Out(len(lights))

def draw_circle(event,x,y,flags,param):
    if event == cv2.EVENT_LBUTTONDBLCLK:
        min_dist = 100000
        min_ind = -1
        for i in range(len(lights)):
             if lights[i] is not None:
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
       frame_width = vc[i].get(cv2.CAP_PROP_FRAME_WIDTH)
       frame_height = vc[i].get(cv2.CAP_PROP_FRAME_HEIGHT)
       maxx = transforms.calculate_XYZ(Kinv[i], r[i], tvec[i], frame_width, frame_height / 2.0, pre = 10.0)
       minx = transforms.calculate_XYZ(Kinv[i], r[i], tvec[i], 0, frame_height / 2.0, pre = 10.0)
       background = cv2.circle(background, tr2(campos[i]), radius = 2, color = (255, 255, 255))
       background = cv2.line(background, tr2(campos[i]), tr2(maxx), color = (255, 255, 255))
       background = cv2.line(background, tr2(campos[i]), tr2(minx), color = (255, 255, 255))

framec = 0
st1 = timer()

while True:
	if(cv2.waitKey(1) & 0xFF == ord('q')):
		break
	for inx in range(Marknum):
		framec = framec + 1
		avg = [[[None, None]]] * Camnum
		hits = 0
		s = False
		
		start = timer()
		
		for i in range(Camnum):	
			
			ret, frame = vc[i].read()
			
			print("t1")
			print(timer() - start)
			
			height = frame.shape[0]
			width = frame.shape[1]
			
			#frame = cv2.undistort(frame, K[i], dist[i], None, newK[i])
			#frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			#cv2.imshow('cam' + str(i), frame)
			if(False):
				th, threshed = cv2.threshold(frame, 100, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
				cnts = cv2.findContours(threshed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]

				s1 = 2
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
		print("t2")
		print(timer() - start)
		posim = np.copy(background)
		for i in range(len(lights)):
			if lights[i] is not None:
				posim = cv2.circle(posim, tr2(lights[i]), radius = 2, color = (int(0), int(255 * light_plus[i]), int(255 * (1 - light_plus[i]))))
		if(s):
			if hits >= 2:
				L = []
				for i in range(Camnum):
					if avg[i][0][0] != None:
						L.append((campos[i], transforms.calculate_XYZ(newKinv[i], r[i], tvec[i], avg[i][0][0], avg[i][0][1])))
						posim = cv2.line(posim, tr2(campos[i]), tr2(transforms.calculate_XYZ(newKinv[i], r[i], tvec[i], avg[i][0][0], avg[i][0][1], pre = 10.0)), color = (255, 0, 0))
				print("t3")
				print(timer() - start)
				result = descent.solvePoint(L)
				print("t4")
				print(timer() - start)
				(x1, y1) = tr2(result)
				print(result)
				distances = [0.0] * 10
				min_dist = 1000000
				for i in range(len(lights)):
					if lights[i] is None:
						continue
					(x2, y2) = tr2(lights[i])
					distances[i] = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
					min_dist = min(min_dist, distances[i])
				if(min_dist > 0):
					length = 0.0
					for i in range(len(lights)):
						if lights[i] is None:
							continue
						distances[i] = (min_dist / distances[i]) ** 2
						length = length + distances[i] ** 2
					length = math.sqrt(length)
					for i in range(len(lights)):
						if lights[i] is None:
							continue
						light_plus[i] = distances[i] / length * 2.0
						light_plus[i] = light_plus[i] + int(light_status[i]) * 0.2
						light_plus[i] = min(light_plus[i], 1)
					out.lights_pwm(light_plus)
				
				posim = cv2.circle(posim, tr2(result), radius = 2, color = (255, 0, 0))
		
		end = timer()
		print("t5")
		print(end - start)
		print(framec / (timer() - st1))
		cv2.imshow('pos', posim)
		
	
for i in range(Camnum):	
	vc[i].release()
cv2.destroyAllWindows()

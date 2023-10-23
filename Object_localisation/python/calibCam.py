#!/usr/bin/env python

import cv2
import numpy as np
import glob
import re
import time

import transforms
from outputs.calib_output import Calibration_tcp as Out

# Defining the world coordinates for 3D points
objp = np.array([(0, 1.0, 0), (0, 1.0, -1.0), (1.0, 1.0, -1.0), (1.0, 1.0, 0)], dtype = np.float32)

Marknum = len(objp)

def get_available_cameras(s = set()):
        res = set()
        for i in range(100):
             if not (i in s):
                    cv = cv2.VideoCapture(i)
                    if cv.isOpened():
                        res.add(i)
                    cv.release()
        return res
	
cv2.namedWindow('pos')
	
max_index = 0
ids = []
names = []
K = {}
prefs = {}
dist = {}
	
cameras = glob.glob('./K*.npy')
for fname in cameras:
    print(fname)
    m = re.search('K(.+?).npy', fname)
    if m:
        print(m.group(1))
        camid = m.group(1)
        prev = get_available_cameras()
        current = set()
        while (len(current) == 0):
               print('Connect camera ' + camid)
               cv2.waitKey(0)
               for i in range(5):
                   current = get_available_cameras(prev)
                   if (len(current) > 0):
                       break
                   print(".")
                   time.sleep(1)
 
               if (len(current) == 0):
                   print("error detecting camera")

        
        cam = current.pop()
        print(cam)
        
        K[camid] = np.load('K' + camid + '.npy')
        dist[camid] = np.load('dist' + camid + '.npy')
        prefs[camid] = np.load('prefs' + camid + '.npy', allow_pickle = True)
        print(prefs[camid])
        ids.append(cam)
        names.append(camid)
        
np.save('camids', ids)
np.save('camnames', names)

camids
        
Camnum = len(ids)

vc = [None] * Camnum
for i in range(Camnum):
	backend = cv2.CAP_V4L2
	#if prefs[names[i]]['backend'] == "L4V2":
		#backend = cv2.CAP_V4L2
	#if prefs[names[i]]['backend'] == "DSHOW":
		#backend = cv2.DSHOW
	
	vc[i] = cv2.VideoCapture(ids[i], backend)
	if(not vc[i].isOpened()):
		print("Warning: backend " + backend + " not supported for camera " + str(names[i]))
	
	#if prefs[names[i]]['codec']:
		#target_codec = prefs[names[i]]['codec']
		#vc[i].set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(target_codec[0], target_codec[1], target_codec[2], target_codec[3]))
		
		#if (vc[i].get(cv2.CAP_PROP_FOURCC) != cv2.VideoWriter.fourcc(target_codec[0], target_codec[1], target_codec[2], target_codec[3])):
			#print("Warning: codec " + target_codec + " unsupported on camera " + str(ids[i]))
		
	#if prefs[names[i]]['fps']:
		#target_fps = int(prefs[names[i]]['fps']) 
	
		#vc[i].set(cv2.CAP_PROP_FPS, target_fps)
		#if vc[i].get(cv2.CAP_PROP_FRAME_WIDTH) != target_fps:
			#print("Warning: fps " + str(target_fps) + " not supported on camera " + str(names[i]))
	
	if True:#(prefs[names[i]]['w']) and (prefs[names[i]]['h']):
		frame_width = 640#int(prefs[names[i]]['w']) 
		frame_height = 360#int(prefs[names[i]]['h']) 
		
		vc[i].set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
		vc[i].set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
		if vc[i].get(cv2.CAP_PROP_FRAME_WIDTH) != frame_width or vc[i].get(cv2.CAP_PROP_FRAME_HEIGHT) != frame_height:
			print("Warning: resolution (" + str(frame_width) + "x" + str(frame_height) +  ") unsupported for camera " + str(names[i]))



out = Out()

for i in range(Camnum):	
	avg = [0] * Marknum

	for j in range(Marknum):
		
		out.light_on(j)
		
		time.sleep(1)
		
		ret, frame = vc[i].read()
		
		if not ret:
			print("notret " + str(i) + " " + str(j))
			
		
		cv2.imshow('imgraw' + str(i),frame)
		
		time.sleep(1)
		
		out.light_off(j)
		
		h = frame.shape[0]
		w = frame.shape[1]
		
		newK, roi = cv2.getOptimalNewCameraMatrix(K[names[i]], dist[names[i]], (w,h), 1, (w,h))		
		frame = cv2.undistort(frame, K[names[i]], dist[names[i]], None, newK)
		
		cv2.imshow('img' + str(i),frame)
		cv2.waitKey(0)
			
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		if(ret):
			th, threshed = cv2.threshold(frame, 100, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
			cv2.imshow('img' + str(i),threshed)
			cv2.waitKey(0)
			cnts = cv2.findContours(threshed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]				
			s1 = 3
			xcnts = []
			max_contour = 0	  
			for cnt in cnts:
				if s1<cv2.contourArea(cnt) and max_contour < cv2.contourArea(cnt):
					xcnts = cnt
					max_contour = cv2.contourArea(cnt)
			
				
			if(len(xcnts) >= 1):
				avg[j] = [[0, 0]] 
				for p in xcnts:
					avg[j] = avg[j] + p
				avg[j] = avg[j] / len(xcnts)
				cv2.imshow('img' + str(i),cv2.circle(threshed, (int(avg[j][0][0]), int(avg[j][0][1])), radius = 10, color = (255, 0, 0)))
				cv2.waitKey(0)
	

	Kinv = np.linalg.inv(K[names[i]])
	
	retval, rvec, tvec = cv2.solvePnP(objp, np.float32(avg), newK, np.array([0] * 5))
	rmat, _ = cv2.Rodrigues(rvec)
	rinv = np.transpose(rmat)
	np.save('rinv' + str(names[i]), rinv)
	np.save('kinv' + str(names[i]), Kinv)
	np.save('tvec' + str(names[i]), tvec)
	print(ids[i])
	print(Kinv)
	print(rinv)
	print(rmat)
	print(tvec)
	print(transforms.calculate_campos(rinv, tvec))
	
	
out.destroy()

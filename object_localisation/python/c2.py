#!/usr/bin/env python

import cv2
import numpy as np
import os
import glob
import math
import requests
import re

import time

import transforms

def calculate_XYZ(s, Kinv, rinv, t, u,v):
                                      
	#Solve: From Image Pixels, find World Points
	
	uv_1=np.array([[s * u, s * v, s]], dtype=np.float32)
	uv_1=uv_1.T
	suv_1=uv_1
	xyz_c=Kinv.dot(suv_1)
	xyz_c=xyz_c-t
	XYZ=rinv.dot(xyz_c)
        
	return XYZ
	
def normsqr(P):
	return np.inner(P, P)[0][0]

def ltpdist(P1, P2, P):
	return normsqr(np.cross(P2-P1, P1-P)) / normsqr(P2-P1)

# Defining the world coordinates for 3D points
objp = np.array([(0, 1.0, 0), (1.0, 1.0, 0), (1.0, 1.0, 1.0), (0, 1.0, 1.0)], dtype = np.float32)

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
	
cv2.imshow('example', 0)

names = ['1', '2']
K = {}
dist = {}
	
cameras = glob.glob('./K*.npy')
for fname in names:
    
        
        K[fname] = np.load('K' + fname + '.npy')
        dist[fname] = np.load('dist' + fname + '.npy')
        
Camnum = len(names)

for i in range(Camnum):	
	avg = [0] * Marknum

	for j in range(Marknum):
		
		
		frame = np.load('f' + str(i) + str(j) + '.npy')
		
		h = frame.shape[0]
		w = frame.shape[1]
		
		print(h)
		print(w)

		newK, roi = cv2.getOptimalNewCameraMatrix(K[names[i]], dist[names[i]], (w,h), 1, (w,h))		
		cv2.imshow('imgu' + str(i),frame)
		frame = cv2.undistort(frame, K[names[i]], dist[names[i]], None, newK)
		
		cv2.imshow('img' + str(i),frame)
		cv2.waitKey(0)
			
		frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		if(True):
			th, threshed = cv2.threshold(frame, 100, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU)
			cv2.imshow('img' + str(i),threshed)
			cv2.waitKey(0)
			cnts = cv2.findContours(threshed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]				
			s1 = 5
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
	print(Kinv)
	print(rinv)
	print(rmat)
	print(tvec)
	print(transforms.calculate_campos(rinv, tvec))
	

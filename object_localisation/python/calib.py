#!/usr/bin/env python

import cv2
import settings
import numpy as np
import os
import glob
    
cami = input('Enter the id of camera: ')

cw = input('Enter number of checker board fields in width: ')
ch = input('Enter number of checker board fields in height: ')

if not cw:
   cw = "7"
if not ch:
   ch = "9"

# Defining the dimensions of checkerboard
CHECKERBOARD = (int(cw),int(ch))
maxi = input('Enter number of maximum iterations: ')
if(not maxi):
    maxi = "50"
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, int(maxi), 0.001)

# Creating vector to store vectors of 3D points for each checkerboard image
objpoints = []
# Creating vector to store vectors of 2D points for each checkerboard image
imgpoints = [] 


# Defining the world coordinates for 3D points
objp = np.zeros((1, CHECKERBOARD[0] * CHECKERBOARD[1], 3), np.float32)
objp[0,:,:2] = np.mgrid[0:CHECKERBOARD[0], 0:CHECKERBOARD[1]].T.reshape(-1, 2)
prev_img_shape = None

edge = input('Enter length of an edge of rectangles: ')

if(not edge):
    edge = "0.02"

objp = objp * float(edge)

backend = input('Enter the backend for the camera: ')
codec = input('Enter the target codec for the camera: ')
fps = input('Enter the target fps for the camera: ')
width = input('Enter the target width for the camera: ')
height = input('Enter the target height for the camera: ')
if not fps:
   fps = "0"
if not width:
   width = "0"
if not height:
   height = "0"

if(float(edge) == 0):
    egde = "0.02"

# Extracting path of individual image stored in a given directory
img = ""
gray = ""
images = glob.glob('./images' + cami + '/*.png')
for fname in images:
    img = cv2.imread(fname)
    if(int(width) > 0 and int(height) > 0):
    	img = cv2.resize(img, (int(width), int(height)), interpolation = cv2.INTER_AREA)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # Find the chess board corners
    # If desired number of corners are found in the image then ret = true
    ret, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE)
    
    """
    If desired number of corner are detected,
    we refine the pixel coordinates and display 
    them on the images of checker board
    """
    if ret == True:
        objpoints.append(objp)
        # refining pixel coordinates for given 2d points.
        corners2 = cv2.cornerSubPix(gray, corners, (11,11),(-1,-1), criteria)
        
        imgpoints.append(corners2)

        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, CHECKERBOARD, corners2, ret)
    
    cv2.imshow('img',img)
    cv2.waitKey(0)

cv2.destroyAllWindows()

h,w = img.shape[:2]

"""
Performing camera calibration by 
passing the value of known 3D points (objpoints)
and corresponding pixel coordinates of the 
detected corners (imgpoints)
"""
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

print("Camera matrix : \n")
print(mtx)
print("dist : \n")
print(dist)
print("rvecs : \n")
print(rvecs)
print("tvecs : \n")
print(tvecs)

np.save('K' + cami, mtx)
np.save('prefs' + cami, {'backend': backend, 'codec': codec, 'fps': fps, 'h': height, 'w': width})
np.save('dist' + cami, dist)

images = glob.glob('./images' + cami + '/*.png')
for fname in images:
# Refining the camera matrix using parameters obtained by calibration
	img = cv2.imread(fname)
	if(int(width) > 0 and int(height) > 0):
    	    img = cv2.resize(img, (int(width), int(height)), interpolation = cv2.INTER_AREA)
	h, w = img.shape[:2]
	gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
	dst = cv2.undistort(gray, mtx, dist, None, newcameramtx)
	alpha = 1
	dst = cv2.addWeighted(dst, alpha, gray, 1 - alpha, 0.0)
	cv2.imshow("undistorted image",dst)
	cv2.waitKey(0)


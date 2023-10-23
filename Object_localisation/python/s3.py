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

import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
from pydub import AudioSegment
from pydub.playback import play
import time
from multiprocessing import Process

time.sleep(20)

# Audio file, .wav file
wavFile = "thunder.wav"

# Retrieve the data from the wav file
data, samplerate = sf.read(wavFile)

n = len(data)  # the length of the arrays contained in data
Fs = samplerate  # the sample rate

# Working with stereo audio, there are two channels in the audio data.
# Let's retrieve each channel seperately:
ch1 = np.array([data[i][0] for i in range(n)])  # channel 1
ch2 = np.array([data[i][1] for i in range(n)])  # channel 2

# x-axis and y-axis to plot the audio data
time_axis = np.linspace(0, n / Fs, n, endpoint=False)
sound_axis = ch1 #we only focus on the first channel here

def playing_audio():
    song = AudioSegment.from_wav(wavFile)
    play(song)
    
p1 = Process(target=playing_audio, args=())
p1.start()
	
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
lights = [None] * 10
lights[0] = [-10, 0, 0]
lights[1] = [1, 0, 1]
lights[2] = [-10, 0, 0]
lights[3] = [1, 0, 0]
lights[4] = [1, 0, 2]
lights[5] = [0, 0, 1]
lights[6] = [0, 0, 0]
lights[7] = [0, 0, 2]
lights[8] = [-10, 0, 0]
lights[9] = [-10, 0, 0]
#lights = [None] * 8
#ind = 0
#for i in range(3):
	#for i2 in range(3):
		#if(ind < 8):
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

out = Out(len(lights))

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
        if light_status[min_ind]:
            bs[min_ind] = ord('T')
        else:
            bs[min_ind] = ord('F')
        #ser.write(bs)

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
       
#ser = serial.Serial('/dev/ttyUSB0', 115200)

phase = 0

previousTime = time.time()
our_pos = 0

mov_avg = [0] * 50
suma = 0

while True:
	secs = (time.time() - previousTime)
	if(cv2.waitKey(1) & 0xFF == ord('q')):
		break
	for inx in range(Marknum):
		#requests.get("http://" + ips[inx] + "/LEDOFF")
		avg = [[[None, None]]] * Camnum
		hits = 2
		s = True
		
		
		posim = np.copy(background)
		if(s):
			if hits >= 2:
				if(True):
					for i in range(len(lights)):
						if lights[i] is not None:
							while(time_axis[our_pos] < secs):
								our_pos += 1
							print(our_pos)
							print(secs)
							
							suma -= mov_avg[0]
							mov_avg.pop(0)
							suma += abs(sound_axis[our_pos])
							mov_avg.append(abs(sound_axis[our_pos]))
							light_plus[i] = min(1, (suma / len(mov_avg)) ** 4 * 50)
							out.lights_pwm(light_plus)
							time.sleep(0.005)
		cv2.imshow('pos', posim)
		phase = phase + 1
		if phase >= 110:
			phase = 0
	
cv2.destroyAllWindows()

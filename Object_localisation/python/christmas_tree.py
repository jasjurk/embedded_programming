import cv2
import requests

Marknum = 4
ids = [0, 2]

Camnum = len(ids)

ip = "192.168.43.23"

vc = [None] * Camnum
for i in range(Camnum):
	vc[i] = cv2.VideoCapture(ids[i])
	
for j in range(Marknum):
	requests.get("http://" + ip + "/LEDON?led=" + str(j + 1))
	
while True:
	if(cv2.waitKey(1) & 0xFF == ord('q')):
		break
	for i in range(Camnum):	
		ret, frame = vc[i].read()
		cv2.imshow('img' + str(i),frame)
		
for j in range(Marknum):
	requests.get("http://" + ip + "/LEDOFF?led=" + str(j + 1))

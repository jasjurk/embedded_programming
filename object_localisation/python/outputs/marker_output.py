import socket

class Marker_output:
	def turn_on(self):
		print("virtual")
	
	def turn_off(self):
		print("virtual")

class Marker_udp(Marker_output):
	def __init__(self, ip = "192.168.1.2", port = 20001):
		self.sock = socket.socket(socket.AF_INET, # Internet
			socket.SOCK_DGRAM) # UDP
		self.ip = ip
		self.port = port
		
	def turn_on(self):
		self.sock.sendto(b"B", (self.ip, self.port))
	
	def turn_off(self):
		self.sock.sendto(b"A", (self.ip, self.port))

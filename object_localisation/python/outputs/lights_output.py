import socket
import serial

class Lights_output:
	def lights_pwm(self, arrs):
		print("virtual")

class Lights_udp(Lights_output):
	def __init__(self, n = 10, ip = "192.168.1.4", port = 2137):
		self.sock = socket.socket(socket.AF_INET, # Internet
			socket.SOCK_DGRAM) # UDP
		self.light_num = n
		self.ip = ip
		self.port = port
		
	def lights_pwm(self, arrs):
		bs = bytearray(str('\x00' * self.light_num + '|').encode())
		for i in range(self.light_num):
			bs[i] = int(255 * arrs[i])
		self.sock.sendto(bs, (self.ip, self.port))
		
class Lights_serial(Lights_output):
	def __init__(self, n, address = "/dev/ttyUSB0", baudrate = "115200"):
		self.serial = ser = serial.Serial(address, baudrate)
		self.light_num = n
		
	def lights_pwm(self, arrs):
		bs = bytearray(str('\x00' * self.light_num + '|').encode())
		for i in range(self.light_num):
			bs[i] = int(255 * arrs[i])
		self.serial.write(bs)


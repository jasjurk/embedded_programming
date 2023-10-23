import requests

class Calibration_output:
	def light_on(self, n):
		print("virtual")
	
	def light_off(self, n):
		print("virtual")
		
class Calibration_tcp(Calibration_output):
	def __init__(self, ip = "192.168.1.6"):
		self.ip = ip
		self.session = requests.Session()
		adapter = requests.adapters.HTTPAdapter(max_retries=20)
		self.session.mount('http://', adapter)
	
	
	def light_on(self, n):
		print(self.session.get("http://" + self.ip + "/LEDON?led=" + str(n + 1), timeout=1))
	
	def light_off(self, n):
		print(self.session.get("http://" + self.ip + "/LEDOFF?led=" + str(n + 1), timeout=1))
		
	def destroy(self):
		print("destroyed")
		
	def light_all(self):
		print(self.session.get("http://" + self.ip + "/LEDON?led=" + str(1), timeout=1))
		print(self.session.get("http://" + self.ip + "/LEDON?led=" + str(2), timeout=1))
		print(self.session.get("http://" + self.ip + "/LEDON?led=" + str(3), timeout=1))
		print(self.session.get("http://" + self.ip + "/LEDON?led=" + str(4), timeout=1))
		
	def lights_all_off(self):
		print(self.session.get("http://" + self.ip + "/LEDOFF?led=" + str(1), timeout=1))
		print(self.session.get("http://" + self.ip + "/LEDOFF?led=" + str(2), timeout=1))
		print(self.session.get("http://" + self.ip + "/LEDOFF?led=" + str(3), timeout=1))
		print(self.session.get("http://" + self.ip + "/LEDOFF?led=" + str(4), timeout=1))

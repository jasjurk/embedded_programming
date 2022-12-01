import numpy as np
import math

def calculate_XYZ(Kinv, rinv, t, u, v, pre = 1.0):
                                      
	#Solve: From Image Pixels, find World Points
	
	uv_1=np.array([[pre * u, pre * v, pre * 1]], dtype=np.float32)
	uv_1=uv_1.T
	suv_1=uv_1
	xyz_c=Kinv.dot(suv_1)
	xyz_c=xyz_c-t
	XYZ=rinv.dot(xyz_c)
        
	return XYZ
	
	
def calculate_campos(rinv, t):
	return rinv.dot(-t)


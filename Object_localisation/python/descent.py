import numpy as np
import math

eps = 0.0005
dzia = 0.1
h = 0.00000001
maxit = 1000

def normsqr(P):
	return np.inner(P, P)[0][0]

def ltpdist(P1, P2, P):
	P1 = P1.T
	P2 = P2.T
	P = P.T
	#print(P1.shape)
	#print(P2.shape)
	#print(P.shape)
	return normsqr(np.cross(P2-P1, P1-P)) / normsqr(P2-P1)

def f(L, P):
	res = 0
	for (p1, p2) in L:
		res = res + ltpdist(p1, p2, P)
	return res
	
def gradf(L, P):
	return np.array([[(f(L, P + np.array([[h,0,0]]).T) - f(L, P - np.array([[h,0,0]]).T)) / (2 * h), 
	        	  (f(L, P + np.array([[0,h,0]]).T) - f(L, P - np.array([[0,h,0]]).T)) / (2 * h),
	        	  (f(L, P + np.array([[0,0,h]]).T) - f(L, P - np.array([[0,0,h]]).T)) / (2 * h)]]).T

def solvePoint(L):
	res = np.array([[0,0,0]], dtype=np.longdouble).T
	pres = np.array([[eps,eps,eps]], dtype=np.longdouble).T
	i = 0
	while np.linalg.norm(pres - res) > eps and i < maxit:
		i = i + 1
		pres = res
		res = res - dzia * gradf(L, res)
	print(i)
	return res
	


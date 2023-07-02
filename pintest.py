#!/usr/bin/python3
# Import required libraries
import sys
import time
import RPi.GPIO as GPIO
import time
import getopt

# Use BCM GPIO references
# instead of physical pin numbers
def usage():
	print("usage: -m <i/o> -p pin <pin_no 1-40 BOARD> -d duration <seconds> -l laststate <1/0>")

def main():
	try: 
		opts, args =getopt.getopt(sys.argv[1:], "m:p:d:l:",["mode=","pin=","duration=","laststate="])
	except getopt.GetoptError as err:
		usage()
		sys.exit(2)
	#print("opts: ",opts)
	#print("args: ",sys.argv[1:])
	if len(opts)<4:
		usage()
		sys.exit(2)
	for o,a, in opts:
		if o=="-m":
			mode=a
		elif o=="-p":
			testPin=int(a)
		elif o=="-d":
			duration=float(a)
		elif o=="-l":
			laststate=int(a)
			
	#print("laststate: ",laststate)
	
	GPIO.setmode(GPIO.BOARD)
	GPIO.setwarnings(False)
	if testPin<1 or testPin>40:
		print("wrong pin number, you entered: ", testPin)
		sys.exit(2)
	if mode=="o":
		GPIO.setup(testPin,GPIO.OUT)
		GPIO.output(testPin, True)
		time.sleep(duration)
		print("turned on")
		if laststate==0:
			GPIO.output(testPin, False)
			print("turned off")
	elif mode=="i":
		GPIO.setup(testPin,GPIO.IN)
		startTime=time.time()
		endTime=startTime+duration
		while time.time()<endTime:
			value = GPIO.input(testPin)
			print("we read: ",value)
			time.sleep(0.1)
	else:
		print("wrong mode, you entered: ", mode)
		sys.exit(2)
	

if __name__ == "__main__":
	main()

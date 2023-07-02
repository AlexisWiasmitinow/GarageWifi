#!/usr/bin/python3
# Import required libraries
import sys, time, subprocess, os, time, getopt
import RPi.GPIO as GPIO
from threading import Thread
from counter import *
from server import *

#what tariff do we have right now?
def checkHighTariff():
	now=datetime.now()
	highTariff = True
	if now.weekday() == 6:
		highTariff = False
	elif now.weekday() == 5 and (now.hour < 7 or now.hour >= 13):
		highTariff = False
	elif now.weekday() < 5 and (now.hour < 7 or now.hour >= 20):
		highTariff = False
	return highTariff

#write the status log
def writeLog(string):
	logFileName = "/var/log/hostapd.log"
	now=datetime.now()
	logFile = open(logFileName,"a")
	logFile.write(str(now)+" "+string+"\n")
	logFile.close()
	if debug:
		print(string+"\n")

def main():
	GPIO.setmode(GPIO.BOARD)
	GPIO.setwarnings(False)
	GPIO.setup(chargePin,GPIO.OUT)
	GPIO.output(chargePin, False)
	GPIO.setup(ssrPin,GPIO.OUT)
	GPIO.output(ssrPin, False)
	canCharge = False
	lastCanCharge = False
	lastSSRon = False
	writeLog("Charge access daemon started")
	print("starting charge access daemon")
	counter = electricityCounter()
	counter.startCounter() #start counting pulses
	counter.startSwitcher() #keep an eye on the button
	runServer() #the web interface
	while True:
		serverVariables["ssrOn"] = counterStatus["ssrOn"]
		serverVariables["startSSR"] = counterStatus["startSSR"]
		counterStatus["highTariff"] = checkHighTariff()
		overrideFile = open(overrideFileName,"r")
		overrideText = overrideFile.read()
		overrideFile.close()
		override=bool(int(overrideText))
		if time.time() > counterStatus["startSSR"] + ssrChargeTime:
			counterStatus["ssrOn"] = False
		if counterStatus["ssrOn"]:
			if canCharge:
				canCharge = False
				GPIO.output(chargePin, canCharge)
				writeLog(" charger disabled by button: ")
				time.sleep(switchTimeout)
		else:
			out = subprocess.Popen(['/usr/sbin/hostapd_cli','list'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
			stdout,stderr = out.communicate()
			outputString = str(stdout).split('\\n')
			canCharge=False
			for address in outputString:
				if address == validAddress:
					if override:
						canCharge = True
					else:
						canCharge = not counterStatus["highTariff"]
		if canCharge != lastCanCharge:
			GPIO.output(chargePin, canCharge)
			writeLog(" charger status changed to: "+str(canCharge))
		if counterStatus["ssrOn"] != lastSSRon:
			GPIO.output(ssrPin, counterStatus["ssrOn"])
			writeLog(" SSR status changed to: "+str(counterStatus["ssrOn"]))
		lastCanCharge = canCharge
		lastSSRon = counterStatus["ssrOn"]
		time.sleep(1)

if __name__ == "__main__":
	main()

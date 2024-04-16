import RPi.GPIO as GPIO
import time, threading
from datetime import datetime

pulsePin = 33
switchPin = 31
debug = False
chargePin = 5
ssrPin = 35
switchTimeout = 20  # seconds
ssrChargeTime = 8 * 60 * 60  # 8 hours
validAddress = "4c:fc:aa:09:a7:0d"  # if your car connects to the wifi (like a Tesla)
energyLogFile = "/home/pi/logs/electricityCounter.log"  # where your energy consumption goes
lowTariff = 0.2974  # per kWh price for low tariff
highTariff = 0.3594  # per kWh price for high tariff
tariffMarkup = 0.1  # how much you charge your neighbor on top of the price you buy
overrideFileName = "/home/pi/override"  # set to 1 means charging at high tariff


counterStatus = {}
counterStatus["ssrOn"] = False
counterStatus["highTariff"] = False
counterStatus["startSSR"] = 0


class electricityCounter:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(pulsePin, GPIO.IN)
        GPIO.setup(switchPin, GPIO.IN)
        self.lastLog = 0
        self.logFileName = energyLogFile
        self.logInterval = 5 * 60  # 5 minutes
        self.pulses = 0

    # counting pulses coming from the counter
    def countPulse(self, pin):
        now = time.time()
        self.pulses += 1
        if debug:
            print("pulse counted\n")
        if now > self.lastLog + self.logInterval:
            timestamp = datetime.now()
            logFile = open(self.logFileName, "a")
            logString = f"time:,{timestamp},"
            logString += f'ssrHigh:, {self.pulses * int(counterStatus["highTariff"]) * int(counterStatus["ssrOn"])},'
            logString += f'ssrLow:,{self.pulses * int(not counterStatus["highTariff"]) * int(counterStatus["ssrOn"])},'
            logString += f'chargerHigh:,{self.pulses * int(counterStatus["highTariff"]) * int(not counterStatus["ssrOn"])},'
            logString += (
                f'chargerLow:,{self.pulses * int(not counterStatus["highTariff"]) * int(not counterStatus["ssrOn"])}\n'
            )
            logFile.write(logString)
            logFile.close()
            self.pulses = 0
            self.lastLog = now

    def switchToSSR(self, pin):
        buttonPress = 0
        # this part is needed if you experience EMI issues like button presses showing up even if the button wasn't pressed. It verifies the button is pressed at least 0.5s
        for i in range(10):
            buttonPress += int(GPIO.input(switchPin))
            time.sleep(0.05)
        if buttonPress == 10:
            counterStatus["ssrOn"] = True
            counterStatus["startSSR"] = time.time()

    def counter(self):
        GPIO.add_event_detect(pulsePin, GPIO.RISING, callback=self.countPulse, bouncetime=10)

    def switcher(self):
        GPIO.add_event_detect(switchPin, GPIO.RISING, callback=self.switchToSSR, bouncetime=100)

    def startCounter(self):
        counterThread = threading.Thread(target=self.counter)
        counterThread.daemon = True
        counterThread.start()

    def startSwitcher(self):
        switchThread = threading.Thread(target=self.switcher)
        switchThread.daemon = True
        switchThread.start()

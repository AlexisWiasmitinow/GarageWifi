from http.server import BaseHTTPRequestHandler, HTTPServer
from counter import *
import calendar

hostName = "192.168.1.170"
port = 80

serverVariables = {}
serverVariables["ssrOn"] = False
serverVariables["startSSR"] = 0

def kWh(pulses, high, internal):
	kWh = pulses/400.0
	price = 0
	if high:
		if internal:
			price = highTariff
		else:
			price = highTariff + tariffMarkup
	else:
		if internal:
			price = lowTariff
		else:
			price = lowTariff + tariffMarkup
	CHF = round(kWh * price, 2)
	return f"{kWh} kWh / CHF {CHF}"

class MyServer(BaseHTTPRequestHandler):
	def do_GET(self):
		with open(energyLogFile, 'r') as file:
			lines = file.readlines()
		lastMonth = 0
		ssrHighSum = 0
		ssrLowSum = 0
		chargerHighSum = 0
		chargerLowSum = 0
		energyValues = ""
		for i, line in enumerate(lines):
			values = line.split(',')
			date = datetime.strptime(values[1], '%Y-%m-%d %H:%M:%S.%f')
			month = int(date.strftime('%m'))
			ssrHigh = int(values[3])
			ssrLow = int(values[5])
			chargerHigh = int(values[7])
			chargerLow = int(values[9])
			if month == lastMonth or lastMonth == 0:
				ssrHighSum += ssrHigh
				ssrLowSum += ssrLow
				chargerHighSum += chargerHighSum
				chargerLowSum += chargerLow
			elif lastMonth > 0:
				monthString = calendar.month_name[lastMonth]
				energyValues += f"Month: {monthString}, Socket High: {kWh(ssrHighSum, True, True)}, Socket Low: {kWh(ssrLowSum, False, True)}, Charger High: {kWh(chargerHighSum, True, False)}, Charger Low: {kWh(chargerLowSum, False, False)} <br> "
				ssrHighSum = ssrHigh
				ssrLowSum = ssrLow
				chargerHighSum = chargerHighSum
				chargerLowSum = chargerLow
			if i == len(lines) - 1:
				monthString = calendar.month_name[month]
				energyValues += f"Month: {monthString}, Socket High: {kWh(ssrHighSum, True, True)}, Socket Low: {kWh(ssrLowSum, False, True)}, Charger High: {kWh(chargerHighSum, True, False)}, Charger Low: {kWh(chargerLowSum, False, False)} <br> "
			lastMonth = month

		if debug:
			print("energyValues:", energyValues)
		startSSR = datetime.fromtimestamp(serverVariables["startSSR"])
		startSSRstring = startSSR.strftime('%Y-%m-%d %H:%M:%S')
		if serverVariables["ssrOn"]:
			statusText = f"We have currently the socket enabled, it started at{startSSRstring}."
		else:
			statusText = f"We have currently the charger enabled."
		self.send_response(200)
		self.send_header("Content-type", "text/html")
		self.end_headers()
		self.wfile.write(bytes("<html><head><title>Electricity Meter</title></head>", "utf-8"))
		self.wfile.write(bytes("<body>", "utf-8"))
		self.wfile.write(bytes("<p>%s<br></p>" % statusText, "utf-8"))
		self.wfile.write(bytes("<p>We have the following Electricity counts:</p>", "utf-8"))
		self.wfile.write(bytes("<p>Energy Consumptions:<br> %s</p>" % energyValues, "utf-8"))
		self.wfile.write(bytes("</body></html>", "utf-8"))

def startServer():
	webServer = HTTPServer((hostName, port), MyServer)
	webServer.serve_forever()

def runServer():
	serverThread = threading.Thread(target=startServer)
	serverThread.daemon = True
	serverThread.start()

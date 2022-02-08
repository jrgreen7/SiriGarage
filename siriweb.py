import os
import time
from datetime import datetime
from flask import Flask, render_template, request
import socket

hostname = socket.gethostname()
ip_address = socket.gethostbyname(socket.gethostname() + ".local")

# Define the pin numbers (C = closed sensor; O = open sensor; R = relay output)
D1_C_PIN = 16
D1_O_PIN = 18
D2_C_PIN = 29
D2_O_PIN = 31
D3_C_PIN = 33
D3_O_PIN = 37
D1_R_PIN = 7
D2_R_PIN = 11
D3_R_PIN = 13  # Used to toggle light on Door 1 (connected via resistor)
D4_R_PIN = 15


import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)  # the pin numbers refer to the board connector not the chip
GPIO.setwarnings(False)
GPIO.setup(D1_C_PIN, GPIO.IN, GPIO.PUD_UP) # Door 1 is Closed sensor
GPIO.setup(D1_O_PIN, GPIO.IN, GPIO.PUD_UP) # Door 1 is Open sensor
GPIO.setup(D2_C_PIN, GPIO.IN, GPIO.PUD_UP) # Door 2 is Closed sensor
GPIO.setup(D2_O_PIN, GPIO.IN, GPIO.PUD_UP) # Door 2 is Open sensor
GPIO.setup(D3_C_PIN, GPIO.IN, GPIO.PUD_UP) # Door 3 is Closed sensor
GPIO.setup(D3_O_PIN, GPIO.IN, GPIO.PUD_UP) # Door 3 is Open sensor

GPIO.setup(D1_R_PIN, GPIO.OUT)			#Door 1 Relay to Open Door
GPIO.output(D1_R_PIN, GPIO.HIGH)
GPIO.setup(D2_R_PIN, GPIO.OUT)		#Door 2 Relay to Open Door
GPIO.output(D2_R_PIN, GPIO.HIGH)
GPIO.setup(D3_R_PIN, GPIO.OUT)		#Door 3 Relay to Open Door (highjacked to toggle light)
GPIO.output(D3_R_PIN, GPIO.HIGH)
GPIO.setup(D4_R_PIN, GPIO.OUT)		#Not Used for the project
GPIO.output(D4_R_PIN, GPIO.HIGH)

from config import (
	PORT,
	ENABLE_PASSWORD,
	PASSWORD,
	ENABLE_SIRI,
	SIRI_PASSWORD,
	BG_COLOR_QUESTION,
	BG_COLOR_OPEN,
	BG_COLOR_CLOSED,
	IMAGE_QUESTION,
	IMAGE_OPEN,
	IMAGE_CLOSED,
	NUMBER_OF_DOORS,
	DOOR_1_NAME,
	DOOR_2_NAME,
	DOOR_3_NAME,
	SENSORS_PER_DOOR,
	ADMIN,
	ADMIN_PASS,
)

directory = os.getcwd()
APP_PATH = os.path.abspath(__file__)
LOG_FILE = directory + '/log.py'

BadPassword = 0

Any_Door_Open = 1			#Default Status, If any door is Not Closed, this will be greater than 0
bgcolor = BG_COLOR_QUESTION		#Default Status, Door is questionable, so background yellow
door1image = IMAGE_QUESTION		#Default Status, Door is questionable, so image is question mark
door2image = IMAGE_QUESTION		#Default Status, Door is questionable, so image is question mark
door3image = IMAGE_QUESTION		#Default Status, Door is questionable, so image is question mark

if NUMBER_OF_DOORS == 1:
	door1 = "inline-block"
	door2 = "none"
	door3 = "none"
	imagesize = 100
elif NUMBER_OF_DOORS == 2:
	door1 = "inline-block"
	door2 = "inline-block"
	door3 = "none"
	imagesize = 100
elif NUMBER_OF_DOORS == 3:
	door1 = "inline-block"
	door2 = "inline-block"
	door3 = "inline-block"
	imagesize = 100

app = Flask(__name__)

print('-------------------------------------------')
print('\n Hostname of your Pi: ' + hostname)
print(' IP address of Pi: ' + ip_address)
print('')
print(' Garage Door Status Found at: http://' + ip_address + ':' + str(PORT))
print(' Settings Can Be Found at: http://' + ip_address + ':' + str(PORT) + '/Settings')
print(' Siri Setup Instructions Can Be Found at: http://' + ip_address + ':' + str(PORT) + '/page/sirisetup.html')
print('')
print('-------------------------------------------')


# Helper function to activate one of the doors. 
# door = door number (1, 2 or 3)
def activateDoor(door):
	door2Pin = {
		1: D1_R_PIN,
		2: D2_R_PIN,
		3: D3_R_PIN
	}
	pin = door2Pin.get(door, 0)

	if pin == 0:
		print("Bad door number requested in activateDoor()")
	else:
		print("Activating Door", door)
		GPIO.output(pin, GPIO.LOW)
		time.sleep(1)
		GPIO.output(pin, GPIO.HIGH)


# Helper function to print to log file
def printLOG(request, msg):
	logfile = open("static/log.txt","a")
	logfile.write(datetime.now().strftime("%Y/%m/%d -- %H:%M:%S  -- ") + request.environ['REMOTE_ADDR'] + " -- " + msg + "\n")
	logfile.close()


# Code to implement web HTML interface  (Flask address is /)
@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		global BadPassword
		code = request.form['garagecode']
		Door_To_Open = request.form.get('garagedoorradio', "UNKNOWN")

		if code == PASSWORD and ENABLE_PASSWORD == "YES" and BadPassword <= 5:  # 12345678 is the Default Password that Opens Garage Door (Code if Password is Correct)
			print("Door requested to open: " + Door_To_Open)
			if Door_To_Open == "door1":
				activateDoor(1)
				time.sleep(2)
			if Door_To_Open == "door2":
				activateDoor(2)
				time.sleep(2)
			if Door_To_Open == "door3":
				activateDoor(3)
				time.sleep(2)

		else:  		# 12345678 is the Password that Opens Garage Door (Code if Password is Incorrect)
			if code == "":
				code = "NULL"
			else:
				BadPassword += 1
				printLOG(request, "Bad Password Entered: " + code)
				print(request.environ['REMOTE_ADDR'] + " -- " + str(BadPassword) + " wrong password(s) have been entered!")

			if BadPassword > 5:
				printLOG(request, "Too many wrong passwords, System disabled")
				print("Too many wrong passwords, System disabled")


	door1image = IMAGE_QUESTION		#Default Status, Door is questionable, so image is question mark
	door2image = IMAGE_QUESTION		#Default Status, Door is questionable, so image is question mark
	door3image = IMAGE_QUESTION		#Default Status, Door is questionable, so image is question mark

	# Check status of Door1
	if GPIO.input(D1_C_PIN) == GPIO.HIGH and GPIO.input(D1_O_PIN) == GPIO.HIGH:
		if SENSORS_PER_DOOR == 1:
			print("Door 1 is Open")
			door1image = IMAGE_OPEN
		else:
			print("Door 1 is Opening/Closing")
			door1image = IMAGE_QUESTION
		Any_Door_Open = 1
	else:
		if GPIO.input(D1_C_PIN) == GPIO.LOW:
			print("Door 1 is Closed")
			door1image = IMAGE_CLOSED
			Any_Door_Open = 0
		if GPIO.input(D1_O_PIN) == GPIO.LOW:
			print("Door 1 is Open")
			door1image = IMAGE_OPEN
			Any_Door_Open = 2

	# Check status of Door2
	if NUMBER_OF_DOORS > 1:
		if GPIO.input(D2_C_PIN) == GPIO.HIGH and GPIO.input(D2_O_PIN) == GPIO.HIGH:
			if SENSORS_PER_DOOR == 1:
				print("Door 2 is Open")
				door2image = IMAGE_OPEN
			else:
				print("Door 2 is Opening/Closing")
				door2image = IMAGE_QUESTION
			Any_Door_Open = Any_Door_Open + 1
		else:
			if GPIO.input(D2_C_PIN) == GPIO.LOW:
				print("Door 2 is Closed")
				door2image = IMAGE_CLOSED
			if GPIO.input(D2_O_PIN) == GPIO.LOW:
				print("Door 2 is Open")
				door2image = IMAGE_OPEN
				Any_Door_Open = Any_Door_Open + 2

	# Check status of Door3
	if NUMBER_OF_DOORS == 3:
		if GPIO.input(D3_C_PIN) == GPIO.HIGH and GPIO.input(D3_O_PIN) == GPIO.HIGH:
			if SENSORS_PER_DOOR == 1:
				print("Door 3 is Open")
				door3image = IMAGE_OPEN
			else:
				print("Door 3 is Opening/Closing")
				door3image = IMAGE_QUESTION
			Any_Door_Open = Any_Door_Open + 1
		else:
			if GPIO.input(D3_C_PIN) == GPIO.LOW:
				print("Door 3 is Closed")
				door3image = IMAGE_CLOSED
			if GPIO.input(D3_O_PIN) == GPIO.LOW:
				print("Door 3 is Open")
				door3image = IMAGE_OPEN
				Any_Door_Open = Any_Door_Open + 2

	if Any_Door_Open == 0:
		bgcolor = BG_COLOR_CLOSED
	if Any_Door_Open == 1:
		bgcolor = BG_COLOR_QUESTION
	if Any_Door_Open > 1:
		bgcolor = BG_COLOR_OPEN

	return render_template('doorstatus.txt',
		color = bgcolor,
		door1status = door1image,
		door2status = door2image,
		door3status = door3image,
		doorstatussize = imagesize,
		door1visable = door1,
		door2visable = door2,
		door3visable = door3,
		D1Name = DOOR_1_NAME,
		D2Name = DOOR_2_NAME,
		D3Name = DOOR_3_NAME)


# Code associated with displaying current settings  (Flask address is /Settings)
@app.route('/Settings', methods=['GET', 'POST'])
def settings():
	if request.method == 'POST':
		if request.form['ADMIN'] == ADMIN and request.form['ADMIN_PASS'] == ADMIN_PASS:
			#open text file in read mode
			AutoStart = open("/etc/rc.local", "r")

			#read whole file to a string
			AutoStartFile = AutoStart.read()

			#close file
			AutoStart.close()
 
			if ENABLE_PASSWORD == "YES":
				ENABLE_PASSWORD_YES = " Checked"
				ENABLE_PASSWORD_NO = ""
			else:
				ENABLE_PASSWORD_YES = ""
				ENABLE_PASSWORD_NO = " Checked"

			if ENABLE_SIRI == "YES":
				ENABLE_SIRI_YES = " Checked"
				ENABLE_SIRI_NO = ""
			else:
				ENABLE_SIRI_YES = ""
				ENABLE_SIRI_NO = " Checked"

			return render_template('settings.txt',
				PORT = PORT,
				ENABLE_PASSWORD_YES = ENABLE_PASSWORD_YES,
				ENABLE_PASSWORD_NO = ENABLE_PASSWORD_NO,
				PASSWORD = PASSWORD,
				ENABLE_SIRI_YES = ENABLE_SIRI_YES,
				ENABLE_SIRI_NO = ENABLE_SIRI_NO,
				SIRI_PASSWORD = SIRI_PASSWORD,
				BG_COLOR_QUESTION = BG_COLOR_QUESTION,
				BG_COLOR_OPEN = BG_COLOR_OPEN,
				BG_COLOR_CLOSED = BG_COLOR_CLOSED,
				IMAGE_QUESTION = IMAGE_QUESTION,
				IMAGE_OPEN = IMAGE_OPEN,
				IMAGE_CLOSED = IMAGE_CLOSED,
				NUMBER_OF_DOORS = NUMBER_OF_DOORS,
				DOOR_1_NAME = DOOR_1_NAME,
				DOOR_2_NAME = DOOR_2_NAME,
				DOOR_3_NAME = DOOR_3_NAME,
				SENSORS_PER_DOOR = SENSORS_PER_DOOR,
				ADMIN = ADMIN,
				ADMIN_PASS = ADMIN_PASS,
				APP_PATH = APP_PATH,
				LOG_FILE = LOG_FILE,
				AutoStartFile = AutoStartFile)
		else:
			return app.send_static_file('admin_login.html')
	else:
		return app.send_static_file('admin_login.html')

# Code to capture new settings from the form and save them to config.py (Flask address is /ChangeSettings)
@app.route('/ChangeSettings', methods=['POST'])
def ChangeSettings():

	PORT = request.form['PORT']
	ENABLE_PASSWORD = request.form['ENABLE_PASSWORD']
	PASSWORD = request.form['PASSWORD']
	ENABLE_SIRI = request.form['ENABLE_SIRI']
	SIRI_PASSWORD = request.form['SIRI_PASSWORD']
	NUMBER_OF_DOORS = request.form['NUMBER_OF_DOORS']
	DOOR_1_NAME = request.form['DOOR_1_NAME']
	DOOR_2_NAME = request.form['DOOR_2_NAME']
	DOOR_3_NAME = request.form['DOOR_3_NAME']
	SENSORS_PER_DOOR = request.form['SENSORS_PER_DOOR']
	ADMIN = request.form['ADMIN']
	ADMIN_PASS = request.form['ADMIN_PASS']

	#open text file in write mode (this will erase current file)
	ConfigFile = open("config.py", "w")

	#writes whole string to file
	ConfigFile.write('PORT = ' + PORT + '\n')
	ConfigFile.write('ENABLE_PASSWORD  = "' + ENABLE_PASSWORD + '"\n')
	ConfigFile.write('PASSWORD = "' + PASSWORD + '"\n')
	ConfigFile.write('ENABLE_SIRI = "' + ENABLE_SIRI + '"\n')
	ConfigFile.write('SIRI_PASSWORD = "' + SIRI_PASSWORD + '"\n')
	ConfigFile.write('BG_COLOR_QUESTION = "' + BG_COLOR_QUESTION + '"\n')
	ConfigFile.write('BG_COLOR_OPEN = "' + BG_COLOR_OPEN + '"\n')
	ConfigFile.write('BG_COLOR_CLOSED = "' + BG_COLOR_CLOSED + '"\n')
	ConfigFile.write('IMAGE_QUESTION = "' + IMAGE_QUESTION + '"\n')
	ConfigFile.write('IMAGE_OPEN  = "' + IMAGE_OPEN + '"\n')
	ConfigFile.write('IMAGE_CLOSED = "' + IMAGE_CLOSED + '"\n')
	ConfigFile.write('NUMBER_OF_DOORS = ' + NUMBER_OF_DOORS + '\n')
	ConfigFile.write('DOOR_1_NAME = "' + DOOR_1_NAME + '"\n')
	ConfigFile.write('DOOR_2_NAME = "' + DOOR_2_NAME + '"\n')
	ConfigFile.write('DOOR_3_NAME = "' + DOOR_3_NAME + '"\n')
	ConfigFile.write('SENSORS_PER_DOOR = ' + SENSORS_PER_DOOR + '\n')
	ConfigFile.write('ADMIN = "' + ADMIN + '"\n')
	ConfigFile.write('ADMIN_PASS = "' + ADMIN_PASS + '"\n')

	#close file
	ConfigFile.close()

	return app.send_static_file('Settings_Saved.html')

# Code to delete the log file (Flask address is /Delete_Log_File)
@app.route('/Delete_Log_File', methods=['POST'])
def Delete_Log_File():

	#open text file in write mode (this will erase current file)
	DeleteLogFile = open("static/log.txt", "w")

	DeleteLogFile.write(datetime.now().strftime("Log File Erased -- %Y/%m/%d -- %H:%M \n"))

	#close file
	DeleteLogFile.close()

	return app.send_static_file('Settings_Saved.html')


#Code to get the status of all garage doors as a status string (Flask address is /GarageDoorStatus)
@app.route('/Siri/GarageDoorStatus', methods=['GET'])
def GarageDoorStatus():
	siri_door1_message = ""
	siri_door2_message = ""
	siri_door3_message = ""
	Any_Door_Open = 0

	if GPIO.input(D1_C_PIN) == GPIO.HIGH and GPIO.input(D1_O_PIN) == GPIO.HIGH: #Door 1 Unknown
		if SENSORS_PER_DOOR == 1:
			siri_door1_message = DOOR_1_NAME + " is open"
		else:
			siri_door1_message = DOOR_1_NAME + " is questionable"
		Any_Door_Open = 1
	else:
		if GPIO.input(D1_C_PIN) == GPIO.LOW: # Door 1 Closed
			siri_door1_message = ""
		if GPIO.input(D1_O_PIN) == GPIO.LOW: # Door 1 Open
			siri_door1_message = DOOR_1_NAME + " is open"
			Any_Door_Open = 1

	if NUMBER_OF_DOORS > 1:
		if GPIO.input(D2_C_PIN) == GPIO.HIGH and GPIO.input(D2_O_PIN) == GPIO.HIGH:
			if SENSORS_PER_DOOR == 1:
				siri_door2_message = DOOR_2_NAME + " is open"
			else:
				siri_door2_message = DOOR_2_NAME + " is questionable"
			Any_Door_Open = Any_Door_Open + 1
		else:
			if GPIO.input(D2_C_PIN) == GPIO.LOW:
				siri_door2_message = ""
			if GPIO.input(D2_O_PIN) == GPIO.LOW:
				siri_door2_message = DOOR_2_NAME + " is open"
				Any_Door_Open = Any_Door_Open + 1

	if NUMBER_OF_DOORS == 3:
		if GPIO.input(D3_C_PIN) == GPIO.HIGH and GPIO.input(D3_O_PIN) == GPIO.HIGH:
			if SENSORS_PER_DOOR == 1:
				siri_door3_message = DOOR_3_NAME + " is open"
			else:
				siri_door3_message = DOOR_3_NAME + " is questionable"
			Any_Door_Open = Any_Door_Open + 1
		else:
			if GPIO.input(D3_C_PIN) == GPIO.LOW:
				siri_door3_message = ""
			if GPIO.input(D3_O_PIN) == GPIO.LOW:
				siri_door3_message = DOOR_1_NAME + " is open"
				Any_Door_Open = Any_Door_Open + 1

	if Any_Door_Open == 0:
		return 'All Doors are Closed'
	return ", ".join([siri_door1_message, siri_door2_message, siri_door3_message])

"""	if Any_Door_Open != 0:

		if siri_door1_message != "":
			siri_message = siri_door1_message
		if siri_door2_message != "":
			if siri_message == "":
				siri_message = siri_door2_message
			else:
				siri_message = siri_message + ', ' + siri_door2_message
		if siri_door3_message != "":
			if siri_message == "":
				siri_message = siri_door3_message
			else:
				siri_message = siri_message + ', ' + siri_door3_message

		return siri_message
"""


# Code to respond to Siri requests to open/close garage doors  (Flask address is /Siri/Garage)
@app.route('/Siri/Garage', methods=['POST'])
def GarageSiri():
	# Get the 3 field values from the form or POST request
	ps = request.form.get('ps',"NA")
	what_door = request.form.get('door',"NA")
	dowhat = request.form.get('dowhat',"NA")

	if ps == "NA":
		printLOG(request, "GarageSiri():Password not retrieved. Using NA")
	if what_door == "NA":
		printLOG(request, "GarageSiri():door not retrieved. Using NA")
	if dowhat == "NA":
		printLOG(request, "GarageSiri():dowhat not retrieved. Using NA")

	if ps == SIRI_PASSWORD:
		printLOG(request, "GarageSiri():Garage Door Operated via Siri") 

		if dowhat == "Light":
			printLOG(request, "Toggling light.")
			activateDoor(3)
			return 'Garage Light Toggled'
		if what_door == "Door1" and dowhat == "Open":
			if GPIO.input(D1_C_PIN) == GPIO.LOW:
				printLOG(request, "Door 1 is currently Closed, let's open it.")
				activateDoor(1)
				return 'Garage Door Opening'
			if GPIO.input(D1_C_PIN) == GPIO.HIGH:
				printLOG(request, "Garage is already open, do nothing.")
				return 'Door 1 is already open'
		if what_door == "Door1" and dowhat == "Close":
			if GPIO.input(D1_O_PIN) == GPIO.LOW:
				printLOG(request, "Garage is currently Open, let's close it.")
				activateDoor(1)
				return 'Garage Door Closing'
			if GPIO.input(D1_O_PIN) == GPIO.HIGH:
				printLOG(request, "Garage is already closed, do nothing.")
				return 'Door 1 is already closed'

		if what_door == "Door2" and dowhat == "Open":
			if GPIO.input(D2_C_PIN) == GPIO.LOW:
				printLOG(request, "Door 2 is currently Closed, let's open it.")
				activateDoor(2)
				return 'Garage Door Opening'
			if GPIO.input(D2_C_PIN) == GPIO.HIGH:
				printLOG(request, "Garage is already open, do nothing.")
				return 'Door 2 is already open'
		if what_door == "Door2" and dowhat == "Close":
			if GPIO.input(D2_O_PIN) == GPIO.LOW:
				printLOG(request, "Garage is currently Open, let's close it.")
				activateDoor(2)
				return 'Garage Door Closing'
			if GPIO.input(D2_O_PIN) == GPIO.HIGH:
				printLOG(request, "Garage is already closed, do nothing.")
				return 'Door 2 is already closed'

		if what_door == "Door3" and dowhat == "Open":
			if GPIO.input(D3_C_PIN) == GPIO.LOW:
				printLOG(request, "Door 2 is currently Closed, let's open it.")
				activateDoor(3)
				return 'Garage Door Opening'
			if GPIO.input(D3_C_PIN) == GPIO.HIGH:
				printLOG(request, "Garage is already open, do nothing.")
				return 'Door 2 is already open'
		if what_door == "Door3" and dowhat == "Close":
			if GPIO.input(D3_O_PIN) == GPIO.LOW:
				printLOG(request, "Garage is currently Open, let's close it.")
				activateDoor(3)
				return 'Garage Door Closing'
			if GPIO.input(D3_O_PIN) == GPIO.HIGH:
				printLOG(request, "Garage is already closed, do nothing.")
				return 'Door 2 is already closed'

		return 'GarageSiri() DEBUG: We have a problem with your Siri shortcut entries' 
	else:
		printLOG(request, "GarageSiri(): SIRI Password rejected\nSIRI Password entered: " + ps)
		return "GarageSiri(): We have a problem with the password."

@app.route('/stylesheet.css')
def stylesheet():
	return app.send_static_file('stylesheet.css')

@app.route('/Log')
def logfile():
	return app.send_static_file('log.txt')

@app.route('/images/<path:subpath>')
def SiriPics(subpath):
	return app.send_static_file('images/' + subpath)

@app.route('/page/<sendpage>')
def page(sendpage):
	return app.send_static_file(sendpage)

if __name__ == '__main__':
	app.run(debug=True, host=ip_address, port=PORT)

#!/usr/bin/env python

'''
	Zeta robot protocol between main_board and controller_board.
	Server Program : running on controller_board
	(using Python 2.7)

	History:
		20181007 Geonhee Lee - Redefine the protocol
        20180730 Geonhee LEE - Reconstruction with the ROS platform
		20180715 kyuhsim - new protocol implementation
		20180529 kyuhsim - created.
'''
import rospy
from std_msgs.msg import String

import sys
import socket
from SocketServer import ThreadingTCPServer, StreamRequestHandler
#import logging

import json

from threading import Timer
import threading
import time
import math


### configurations that can be changed
gHost = 'localhost'
gPort = 9006
gRepeatTime = 1				# send status packet in every 2 sec., will be 1 sec.

### global variables
gSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 	# create socket (SOCK_STREAM means TCP socket) 

gConn = None				# init for only type matching. it will be changed after connection

gCache = {
	'status' : 'stopped'	# moving status : stopped, moving, suspended
}

gQueue = []					# list as move queue

gSendPacket = {
	'response': {
		'request': {
			'command' : 'NONE',
			'speed' : None,
			'idRequest' : 0,
			'sender' : 0,
			'position' : None,
			'velocity' : None,
			'led' : None
		}
	},
	'battery': '0.0',
	'bumper': 'off', 
	'sonar': ['off', 'off', 'off', 'off', 'off', 'off', 'off'],
	'led': ['off', 'off', 'off', 'off'], 
	'lidar': None, 
	'position': {'x': '0', 'y': '0', 'theta': '0'},
	'velocity': {'v': '0', 'w': '0'},
	'aircondition': {'h': '-', 't': '-', 'p': '-', 'p2':'-', 'c':'-', 'f':'-', 'co':'-', 'no':'-','r':'-','v':'-'}
}

gRecvPacket = { 
	'command' : 'NONE',
	'speed' : None,
	'idRequest' : 0,
	'sender' : 0,
	'position' : None,
	'velocity' : None,
	'led' : None
}

gRecvPacketSave = {
	'command' : 'NONE',
	'speed' : None,
	'idRequest' : 0,
	'sender' : 0,
	'position' : None,
	'velocity' : None,
	'led' : None
}

class RepeatTimer():
	def __init__(self, seconds, target):
		self._should_continue = False
		self.is_running = False
		self.seconds = seconds
		self.target = target
		self.thread = None

	def _handle_target(self):
		self.is_running = True
		self.target()
		self.is_running = False
		self._start_timer()

	def _start_timer(self):
		if self._should_continue: 			# Code could have been running when cancel was called.
			self.thread = Timer(self.seconds, self._handle_target)
			self.thread.start()

	def start(self):
		if not self._should_continue and not self.is_running:
			self._should_continue = True
			self._start_timer()
		else:
			print("* Timer already started or running, please wait if you're restarting.")

	def cancel(self):
		if self.thread is not None:
			self._should_continue = False 	# Just in case thread is running and cancel fails.
			self.thread.cancel()
		else:
			print("* Timer never started or failed to initialize.")


# get controller status and update gSendPacket and send_packet()

def repeated_processing():
	send_packet()
    
def send_packet():
	global gConn
	print ('>>>>> Sending Packet >>>>> %d' % threading.current_thread().ident)
	pkt = json.dumps( gSendPacket )				# serialize dict to json string
	gConn.send( pkt )


def air_callback(air_data):
	#air_data.data	
	#gSendPacket['aircondition'] 
	airp,airp2,airc,airf,airco,airno,airr,airv,airt,airh,tem = air_data.data.split('|')
	
	#'aircondition': {'h': '-', 't': '-', 'p': '-', 'p2':'-', 'c':'-', 'f':'-', 'co':'-', 'no':'-','r':'-''v':'-'}

	gSendPacket['aircondition']['t'] = airt
	gSendPacket['aircondition']['h'] = airh
	gSendPacket['aircondition']['p'] = airp
	gSendPacket['aircondition']['p2'] = airp2
	gSendPacket['aircondition']['c'] = airc
	gSendPacket['aircondition']['f'] = airf
	gSendPacket['aircondition']['co'] = repr(float(airco)/1000)
	print(airco)
	#print(float(airco)/1000)
	gSendPacket['aircondition']['no'] = repr(float(airno)/1000)
	#print (float(airno)/1000)
	print(airno)
	gSendPacket['aircondition']['r'] = airr
	gSendPacket['aircondition']['v'] = airv	# dict
	if  gConn  != None :
		send_packet()


### <-- simulations

class RequestHandler( StreamRequestHandler ):
	def handle( self ):
		global gConn
		print ('- Connection from : '), (self.client_address)
		conn = self.request
		gConn = conn								# make send_packet() can use conn
		#rt = RepeatTimer(gRepeatTime, repeated_processing)	# repeat every 2 sec., send gSendPacket. repeate time will be 1 sec. later.
		#rt.start()

		while True:
			try:
				conn.settimeout(None)
				msg = conn.recv(1024)
						
			except Exception, e:
				#logger.error('Failed to upload to ftp: '+ str(e))
				print ('* conn.recv made exception. connection is broken.\n- Waiting another connection...')
				print e
				rt.cancel()
				conn.close()
				break

			if not msg:
				StopRepeatTimer()
				rt.cancel()
				conn.close()
				print ('! Disconnected from : ', self.client_address)
				break
			print ('<<<<<< [Recieve msg from Client] <<<<< \n'), (msg)
			#process_message( conn, msg )			# conn.send( msg )		




       

if __name__ == '__main__':
	rospy.init_node('zetabank_air_test')
	#subscribe_status()
	rospy.Subscriber("/air", String, air_callback) # It receives the status data through topic
	# Load the parameter values from Xmlserver
	gPort = 9006

	# Declare the Class SocketServer.ThreadTCPServer
	server = ThreadingTCPServer(("", gPort), RequestHandler)
	print('wait....')

	# serve_forever(poll_interval=0.5)
	# Handle requests until an explicit shutdown() request. 
	# Poll for shutdown every poll_interval seconds. 
	# Ignores the timeout attribute. 
	# If you need to do periodic tasks, do them in another thread.
	server.serve_forever()


	thread = threading.Thread(target = rospy.spin())
	thread.start()

# End of File
        

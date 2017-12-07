import sys
import time

def getTime(epoch):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(epoch)))

def getType(msgType):
	if msgType == '-p':
		return 'private'
	elif msgType == '-b':
		return 'broadcast'
	return 'query'

def displayMessage(message):
	message = eval(message)
	m = '<{}>:  {} \t\t(as {} on {})'.format(message['fromUser'],message['msgData'], getType(message['msgType']), getTime(str(message['created'])))
	print m

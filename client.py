import socket
import sys
import getpass
import time
from threading import Thread
import pymongo
import select
import struct
from util import *
from Tkinter import *
import inputGUI

PRIVATE = '-p'
BROADCAST = '-b'
WHOELSE = 'whoelse'
WOISTHERE = 'whoisthere'
LOGOUT = 'logout'
msgLock = 'askUnread'
isLoggedIn = False
userDetails = {}
userInput = None

def help():
    # print all help material here
    print("Usage: help")
    sys.exit()


def UserPacket(arguments):

    # print(arguments)
    if len(arguments) < 2:
        help()
    # Create complete packet to be sent
    Packet = {}
    # Read and create packet according to the arguments
    if arguments[1] == "-l":
        Packet['cmd'] = 'login'
        Packet['username'] = raw_input('Please enter your username:\n')
        Packet['password'] = getpass.getpass(prompt='Please enter your password:\n')
    elif arguments[1] == "-r":
        Packet['cmd'] = 'register'
        Packet['username'] = raw_input('Please enter your username:\n')
        Packet['password'] = getpass.getpass(prompt='Please enter your password:\n')
    else:
        help()

    return Packet


def messagePacket(userInput, userDetails):
    # print userDetails
    if not userInput:
        return None
    cmd = userInput[0]
    if cmd == PRIVATE:
        toUser = userInput[1]
        msgData = ' '.join(userInput[2:])
        created = time.time()
        msg = {'cmd': 'send', 'msgType': cmd, 'toUser': toUser, 'msgData': msgData,\
               'created': created, 'fromUser': userDetails['username']}
        return len(str(msg)), msg
    elif cmd == BROADCAST:
        msgData = ' '.join(userInput[1:])
        created = time.time()
        msg = {'cmd': 'send', 'msgType': cmd, 'msgData': msgData,\
               'created': created, 'fromUser': userDetails['username']}
        return len(str(msg)), msg
    elif cmd == WHOELSE:
        msg = {'cmd': cmd}
        return len(str(msg)), msg
    elif cmd == WOISTHERE:
        msg = {'cmd': cmd}
        return len(str(msg)), msg
    elif cmd == LOGOUT:
        msg = {'cmd': cmd}
        return len(str(msg)), msg
    else:
        return None


def displayError(ack, cmd):

    print(ack)
    if cmd == 'login':
        if ack.split()[0] == '1':
            print("No such User Exists")
        elif ack.split()[0] == '2':
            print("Incorrect username/password")
        elif ack.split()[0] == '3':
            print("User already logged in from a different system")
        elif ack.split()[0] == '4':
            print("Password wrong, exceeded number of incorrect attempts. Retry after 60 secs")
        elif ack.split()[0] == '5':
            print("You have been blocked. Try after "+ ack.split()[1])

    elif cmd == 'register':
        if ack.split()[0] == '1':
            print("Username is taken")
        elif ack.split()[0] == '2':
            print("You are registered")

    return


def serverInput(server):
    global isLoggedIn
    while True:
        if not isLoggedIn:
            break
        sockets_list = [server]
        read_sockets, write_socket, error_socket = select.select(sockets_list,[],[])

        for socks in read_sockets:
            if socks == server:
                lenmsg = socks.recv(8)
                if not lenmsg:
                    continue
                lenmsg = struct.unpack(">q", lenmsg)[0]
                message = socks.recv(lenmsg)
                displayMessage(message)

def userInput(server, userDetails):
    rt = Tk()
    m=inputGUI.mainWindow(rt, server, userDetails)
    rt.bind('<Return>', m.sendToMain)
    rt.mainloop()
    print '---exiting---'
    global isLoggedIn
    isLoggedIn = False


def startChat(server, userDetails):
    global isLoggedIn
    isLoggedIn = True
    userInputThread = Thread(target=userInput, args=(server, userDetails,))
    serverInputThread =  Thread(target=serverInput, args=(server, ))
    userInputThread.start()
    serverInputThread.start()

def main():

    # create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # getServerAddress(), get local machine name
    host = socket.gethostname()
    port = 9999
    # connection to hostname on the port.
    s.connect((host, port))
    # Create a packet using the command line args
    userDetails = UserPacket(sys.argv)
    # send it to server address
    s.sendall(str(userDetails))
    # receive validation from server (continue)
    ack = s.recv(1024)
    # if authenticated
    if ack == '0':
        print("Successfully Authenticated")
        startChat(s, userDetails)
    else:
        displayError(ack, userDetails['cmd'])
        s.close()

if __name__ == '__main__':
    main()

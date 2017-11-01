import socket
import sys
import getpass
import time
from threading import Thread

PRIVATE = 'private'
BROADCAST = 'broadcast'
LOGOUT = 'logout'
isLoggedIn = False

def help():
    # print all help material here
    print "Usage: help"
    sys.exit()


def UserPacket(arguments):

    print arguments
    if len(arguments) < 2:
        help()

    # Create complete packet to be sent
    Packet = {}

    # Read and create packet according to the arguments
    if arguments[1] == "-l":
        Packet['purpose'] = 'login'
        Packet['username'] = raw_input('Please enter your username:\n')
        Packet['password'] = getpass.getpass(prompt='Please enter your password:\n')

    elif arguments[1] == "-r":
        Packet['purpose'] = 'register'
        Packet['username'] = raw_input('Please enter your username:\n')
        Packet['password'] = getpass.getpass(prompt='Please enter your password:\n')

    else:
        help()

    return Packet

def messagePacket(userInput):
    cmd = userInput[0]
    ack = {'cmd': cmd}
    message = {}
    if cmd == 'send':
        msgType = userInput[1]
        if msgType == BROADCAST:
            msgContent = userInput[2]
            msgLen = len(msgContent)
            ack['msgType'] = msgType
            ack['msgLen'] = msgLen
            message['msgContent'] = msgContent
            message['created'] = int(time.time())
            ack['msgLen'] = len(str(message))
            return ack, message
        else:
            toUser = userInput[2]
            msgContent = userInput[3]
            ack['msgType'] = msgType
            message['toUser'] = toUser
            message['msgContent'] = msgContent
            message['created'] = int(time.time())
            ack['msgLen'] = len(str(message))
            return ack, message
    elif cmd == LOGOUT:
        return ack, None

def sendMsg(s):
    global isLoggedIn
    while True:
        userInput = raw_input().split()
        ack, message = messagePacket(userInput)
        print ack, message
        s.sendall(str(ack))
        s.recv(1024)
        if ack['cmd'] == 'send':
            s.sendall(str(message))
        if ack['cmd'] == LOGOUT:
            isLoggedIn = False
            s.close()

def recvMsg(s):
    global isLoggedIn
    while isLoggedIn:
        # handle receiving messages
        # display
		# handle receiving messages
        msgAck = eval(s.recv(1024))
        print msgAck
        msgAck = eval(s.recv(1024))
        s.sendall('1')
        if msgAck['cmd'] == 'send':
            msgLen = msgAck['msgLen']
            msgType = msgAck['msgType']
            msg = eval(s.recv(msgLen))
            print msg
        # display
        pass

def displayError(ack, purpose):

    print ack
    if purpose == 'login':
        if ack.split()[0] == '1':
            print "No such User Exists"
        elif ack.split()[0] == '2':
            print "Incorrect username/password"
        elif ack.split()[0] == '3':
            print "User already logged in from a different system"
        elif ack.split()[0] == '4':
            print "Password wrong, exceeded number of incorrect attempts. Retry after 60 secs"
        elif ack.split()[0] == '5':
            print "You have been blocked. Try after "+ ack.split()[1]

    elif purpose == 'register':
        if ack.split()[0] == '1':
            print "Username is taken"
        elif ack.split()[0] == '2':
            print "You are registered"

    return

def main():
    # create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # getServerAddress()
    # get local machine name
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
        print "Successfully Authenticated"
        global isLoggedIn
        isLoggedIn = True
        sendThread = Thread(target=sendMsg, args=(s, ))
        recvThread = Thread(target=recvMsg, args=(s, ))
        sendThread.start()
        recvThread.start()

    else:
        #if not authenticated
        displayError(ack, userDetails['purpose'])
        s.close()




    # while True:
        # user is logged in
        # connect to DB
        # read messages from user and send it to server
        # pass


    # tm = s.recv(1024)
    # print("The time got from the server is %s" % tm.decode('ascii'))

if __name__ == '__main__':
    main()

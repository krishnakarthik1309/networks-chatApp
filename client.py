import socket
import sys
import getpass
import time
from threading import Thread
import pymongo

PRIVATE = 'private'
BROADCAST = 'broadcast'
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

    print(arguments)
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
    global userDetails
    cmd = userInput[0]
    if cmd == 'send':
        msgType = userInput[1]
        if msgType == PRIVATE:
            toUser = userInput[2]
            msgData = ' '.join(userInput[3:])
            created = time.time()
            msg = {'cmd': cmd, 'msgType': msgType, 'toUser': toUser, 'msgData': msgData, 'created': created, 'fromUser': userDetails['username']}
            return len(str(msg)), msg
        elif msgType == BROADCAST:
            pass
    elif cmd == 'view' or cmd == LOGOUT:
        return len(str(cmd)), {'cmd': cmd}


def readInput():
    global userInput
    userInput = None
    userInput = raw_input().split()

def sendMsg(s):
    global msgLock, userInput
    '''
    blocked till we have some message in queue
    before returning give lock to recvMsg
    '''
    while True:
        # userInput = raw_input().split()
        inputThread = Thread(target=readInput, args=())
        inputThread.start()
        startTime = int(time.time())
        while userInput is None:
            # wait for user to type
            if int(time.time()) - startTime >= 2:
                msgLock = 'askUnread'
                ask = {'cmd': 'timeout'}
                s.sendall(str(len(str(ask))))
                askUnread(s)
                startTime = int(time.time())
        msgLen, msg = messagePacket(userInput)
        while msgLock == 'askUnread':
            # wait
            pass
        s.sendall(str(msgLen))
        while not msgLock == 'sendMsg':
            pass
        s.sendall(str(msg))
        if msg['cmd'] == LOGOUT:
            s.close()
            isLoggedIn = LOGOUT
            msgLock = 'recvMsg'
            break
        msgLock = 'recvMsg'

def askUnread(s):
    global msgLock
    '''
    blocked tilll msgLock is with askUnread
    before returning give lock to recvMsg
    '''
    ask = {'cmd': 'view'}
    s.sendall(str(ask))
    msgLen = eval(s.recv(1024))
    s.sendall('__RECEIVED_LEN')
    msgs = eval(s.recv(int(msgLen)))
    for msg in msgs:
        print msg
    msgLock = 'recvMsg'

def recvMsg(s):
    global msgLock, isLoggedIn
    '''
    always running except when sendMsg is operating
    Need to maintain lock: say msgLock
    give msgLock to askUnread when receivedMsg == '__UNREAD'
    if userInput is finished push it to queue and give msgLock to sendMsg
    '''
    while not msgLock == 'recvMsg':
        # wait
        k = 1
    recvData = s.recv(1024)
    while isLoggedIn:
        if recvData == '__UNREAD':
            while msgLock == 'sendMsg':
                pass
            msgLock = 'askUnread'
            askUnread(s)
        elif recvData == '__SEND_MESSAGE':
            msgLock = 'sendMsg'

        while not msgLock == 'recvMsg':
            # wait till lock is back
            k = 1
        if not isLoggedIn:
            break
        recvData = s.recv(1024)

def displayError(ack, purpose):

    print(ack)
    if purpose == 'login':
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

    elif purpose == 'register':
        if ack.split()[0] == '1':
            print("Username is taken")
        elif ack.split()[0] == '2':
            print("You are registered")

    return

def main():
    global userDetails, isLoggedIn
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
        print("Successfully Authenticated")
        isLoggedIn = True
        askUnread(s)
        sendThread = Thread(target=sendMsg, args=(s, ))
        recvThread = Thread(target=recvMsg, args=(s, ))
        sendThread.start()
        recvThread.start()
    else:
        #if not authenticated
        displayError(ack, userDetails['purpose'])
        s.close()

if __name__ == '__main__':
    main()

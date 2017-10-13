import socket
import sys
import getpass

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

def chat():
    while True:
        k = 1
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
        chat()
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

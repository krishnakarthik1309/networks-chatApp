import socket
import time

def main():
    # create a socket object
    serversocket = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM)

    # get local machine name
    host = socket.gethostname()

    port = 9999

    # bind to the port
    serversocket.bind((host, port))

    # queue up to 5 requests
    serversocket.listen(5)

    while True:
            # establish a connection
            clientsocket,addr = serversocket.accept()
            print("Got a connection from %s" % str(addr))
            currentTime = time.ctime(time.time()) + "\r\n"
            # receive username password

            # validate in DB

            # send ack
            clientsocket.send(currentTime.encode('ascii'))
            clientsocket.close()

if __name__ == 'main':
    main()

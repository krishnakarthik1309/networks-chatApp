import socket

def main():
    # create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # getServerAddress()
    # get local machine name
    host = socket.gethostname()
    port = 9999

    # connection to hostname on the port.
    s.connect((host, port))
    while True:
        k = 1

    # read flag (-l)
    # if l then read username password
    # send it to server address

    # receive validation from server (continue)
    # print user authenticated
    s.close()


if __name__ == '__main__':
    main()

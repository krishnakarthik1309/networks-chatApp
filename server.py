import socket
import time
import threading
import SocketServer

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = "testing the asumption"
        cur_thread = threading.current_thread()
        response = bytes("{}: {}".format(cur_thread.name, data))
        print response
        while True:
            k = 1

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def main():
    HOST = socket.gethostname()
    PORT = 9999
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # start a thread with the server.
    # the thread will then start one more thread for each request.
    server_thread = threading.Thread(target=server.serve_forever)
    # exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()   # equivalent to serversocket.listen()

    while True:
        # do nothing
        couunt = 1

    server.shutdown()


if __name__ == '__main__':
    main()

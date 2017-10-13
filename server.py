import socket
import time
import threading
import SocketServer
import sys
import pymongo
import time

class DB(object):
    def __init__(self):
        mongoServer = 'localhost'
        mongoPort = 27017
        dbName = 'serverDB'
        userDataCollection = 'userData'
        userBlockCollection = 'userBlockList'

        connection = pymongo.MongoClient(mongoServer, mongoPort)
        db = connection[dbName]
        self.userData = db[userDataCollection]
        self.userBlockList = db[userBlockCollection]

    def getUserData(self, username):
        return self.userData.find_one({'username': username})

    def getUserBlockList(self, username):
        return self.userBlockList.find_one({'username': username})

    def updateUserData(self, updatedData):
        username = updatedData['username']
        oldData = self.getUserData(username)
        self.userData.replace_one(oldData, updatedData)

    def updateUserBlockList(self, updatedData):
        username = updatedData['username']
        oldData = self.getUserData(username)
        self.userBlockList.replace_one(oldData, updatedData)


class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    
    def handle(self):

        # Receive special userPacket for login/register
        userPacket = eval(self.request.recv(1024))

        # user socket is tuple (user ip addr, user port num)
        userSocket = self.request.getpeername()

        # get the dict for the user
        userDB = DB()
        userDict = userDB.userData(userPacket['username'])
        userBlocked = userDB.userBlockList(userPacket['username'])

        if userPacket['purpose'] == 'register':
            if userDict:
                # send user already exists
                self.request.sendall(str(0))
                exit()
            else:
                # register
                userDB.register(userPacket['username'], userPacket['password'])
                # send you are registered
                self.request.sendall(str(1))
                exit()


        if  not userDict:
            # send 1 : no such username exists
            self.request.sendall(str(1))
            exit()

        elif userBlocked:
            # if next possible login time is in future
            if userBlocked['initialFailedLoginTime'] > time.time():
                self.request.sendall(str(5) + " " + str(userBlocked['initialFailedLoginTime']))
                exit()
        
        elif userDict['loggedin']:
            self.request.sendall(str(3))
            exit()

        elif userDict['password'] == userPacket['password']:
            self.request.sendall(str(0))
            # IMP : connection is live
            # goto chat now

        elif userDict['password'] != userPacket['password']:

            if not userBlocked or (time.time() - userBlocked['initialFailedLoginTime'] > 60):
                if not userBlocked:
                    userBlocked = {'username':userPacket['username']}
                userBlocked['numAttempts'] = 1
                userBlocked['initialFailedLoginTime'] = time.time()
            else:
                userBlocked['numAttempts'] += 1

            if userBlocked['numAttempts'] > 3:
                userBlocked['initialFailedLoginTime'] = time.time() + 60
                # send password wrong, you are blocked, retry after 
                self.request.sendall(str(4) + " " + str(userBlocked['initialFailedLoginTime']))
                
            else:
                # send password did not match
                self.request.sendall(str(2))
            
            # Update  userBlockList
            userDB.updateUserBlockList(userBlocked)
            exit()


    def exit():
        sys.exit()



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
        count = 1

    server.shutdown()


if __name__ == '__main__':
    main()

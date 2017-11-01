import time
import socket
import threading
import SocketServer
from DB import UserDB
from DB import MessageDB

# register constants
USER_ALREADY_EXISTS = '1'
YOU_ARE_REGISTERED = '2'

# login constants
SUCCESSFULLY_AUTHENTICATED = '0'
NO_SUCH_USER_EXISTS = '1'
PASSWORD_WRONG = '2'
USER_ALREADY_LOGGED_IN = '3'
PASSWORD_WRONG_YOU_ARE_BLOCKED = '4'
YOU_HAVE_BEEN_BLOCKED = '5'

FAILED = 0
SUCCESS = 1
MAX_ATTEMPTS = 3
BLOCK_TIME = 60

PRIVATE = 'private'
BROADCAST = 'broadcast'
LOGOUT = 'logout'


class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        # Receive special userPacket for login/register
        userPacket = eval(self.request.recv(1024))
        # get the dict for the user
        userDB = UserDB()
        userDict = userDB.getUserData(userPacket['username'])
        userBlocked = userDB.getUserBlockList(userPacket['username'])

        status = FAILED
        if userPacket['purpose'] == 'register':
            status = self.handleRegister(userPacket, userDB, userDict)
        elif userPacket['purpose'] == 'login':
            status = self.handleLogin(userPacket, userDB, userDict, userBlocked)

        if status == SUCCESS:
            # TODO 0: save client socket value in userDict and update it in userDB

            print status
            # messageDB = MessageDB()
            # TODO 1: retrieve old unread messages if any
            # self.handleUnread(userDict, messageDB)
            # TODO 2: chat now
            while True:
                self.handleChat(userDB, userDict, messageDB)

    def handleRegister(self, userPacket, userDB, userDict):
        if userDict:
            self.request.sendall(USER_ALREADY_EXISTS)
            return FAILED
        else:
            # register
            userDB.register(userPacket['username'], userPacket['password'])
            self.request.sendall(YOU_ARE_REGISTERED)

            # user is auto-logged-in if registration is success
            return SUCCESS

    def handleLogin(self, userPacket, userDB, userDict, userBlocked):
        if not userDict:
            self.request.sendall(NO_SUCH_USER_EXISTS)
            return FAILED
        elif userBlocked:
            # Block check: if next possible login time is in future
            if userBlocked['initialFailedLoginTime'] > time.time():
                self.request.sendall(YOU_HAVE_BEEN_BLOCKED
                                     + " " + str(userBlocked['initialFailedLoginTime']))
                return FAILED

        # check password match
        if userDict['password'] == userPacket['password']:
            # check already logged in
            if userDict['isLoggedIn']:
                self.request.sendall(USER_ALREADY_LOGGED_IN)
                return FAILED
            else:
                self.request.sendall(SUCCESSFULLY_AUTHENTICATED)
                userDict['isLoggedIn'] = True
                userDB.updateUserData(userDict)
                return SUCCESS
        else:
            if not userBlocked or (time.time() - userBlocked['initialFailedLoginTime'] > 60):
                if not userBlocked:
                    userBlocked = {'username': userPacket['username']}
                userBlocked['numAttempts'] = 1
                userBlocked['initialFailedLoginTime'] = time.time()
            else:
                userBlocked['numAttempts'] += 1

            if userBlocked['numAttempts'] > MAX_ATTEMPTS:
                # block user for BLOCK_TIME
                userBlocked['initialFailedLoginTime'] = time.time() + BLOCK_TIME
                self.request.sendall(PASSWORD_WRONG_YOU_ARE_BLOCKED +
                                     " " + str(userBlocked['initialFailedLoginTime']))
            else:
                self.request.sendall(PASSWORD_WRONG)

            # Update userBlockList
            userDB.updateUserBlockList(userBlocked)
            return  FAILED

    # TODO 1:
    def handleUnread(self, userDict, messageDB):
        # search in DB(messageDB) for old messages: messageDB.getUnreadMessages(username)
        # if present send it to client
        #   -- and update the DB(messageDB) messageDB.removeUnreadMessage(username)
        pass

    # TODO 2.0:
    def handleChat(self, userDB, userDict, messageDB):
        # messageType = PRIVATE
        # first receive type of message(broadcast/private/logout), length of message
        # update messageType
        try:
            msgAck = eval(self.request.recv(1024))
            if msgAck['purpose'] == 'RCV_MSG':
                msgPacket = eval(self.request.recv(msgAck['MSG_LEN']))

                message = msgPacket['MSG_BODY']
                if msgPacket['MSG_TYPE'] == PRIVATE:
                    toUser = msgPacket['toUser']
                    self.handlePrivateMessage(userDB, userDict, toUser, message, messageDB)

                elif msgPacket['MSG_TYPE'] == BROADCAST:
                    self.handleBroadcastMessage(userDB, message)

                elif msgPacket['MSG_TYPE'] == LOGOUT:
                    self.handleLogout(UserDB, userDict)

                else:
                    pass

        except socket.error, e:
            pass


    # TODO 2.1:
    def handlePrivateMessage(self, userDB, userDict, toUser, message, messageDB):
        # check toUser exists or not
        # check whether toUser is logged in or not
        # if logged in send him the message using userDB.getUserData(toUser)['socket']
        # otherwise store it in DB [toUser, fromUser, message, time?]
        #   -- messageDB.addUnreadMessage(toUser, fromUser, message)
        receiver = userDB.getUserData(toUser)
        if not receiver:
            # receiver d.n.e
            pass
        if receiver['isLoggedIn']:
            # write to socket
            host, port = receiver['socket'][0], receiver['socket'][1] 
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((host, port))
                msgPacket = str({'purpose':'MSG_INCOMING', 'MSG_BODY':message, })
                msgAck = str({'purpose':'RCV_MSG', 'MSG_LEN':len(msgPacket)})
                s.sendall(msgAck)
                s.sendall(msgPacket)
            except socket.error:
                self.handleLogout(userDB, receiver)
                self.handlePrivateMessage(userDB, userDict, toUser, message, messageDB)                

        else:
            messageDB.addUnreadMessage(toUser, userDict['username'], message)


    # TODO 2.2:
    def handleBroadcastMessage(self, userDB, message):
        # get all usernames/sockets who are loggedin: userDB.getAllUsersLoggedIn()
        #   -- and send them message
        pass

    # TODO 2.3:
    def handleLogout(self, userDB, userDict):
        pass

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def main():
    HOST = socket.gethostname()
    PORT = 9999
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)

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

import time
import socket
import threading
from threading import Thread
import SocketServer
from DB import UserDB
from DB import MessageDB
import struct

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

PRIVATE = '-p'
BROADCAST = '-b'
WHOELSE = 'whoelse'
WHOISTHERE = 'whoisthere'
LOGOUT = 'logout'
BLOCK = '-block'
UNBLOCK = '-unblock'

MQueue = {}
UsersOnline = {}
UsersRegistered = [False, {}]

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        # Receive special userPacket for login/register
        userPacket = eval(self.request.recv(1024))
        userSocket = self.request.getpeername()
        print(userSocket)

        # get the dict for the user
        userDB = UserDB()
        userDict = userDB.getUserData(userPacket['username'])
        userBlocked = userDB.getUserLoginBlockList(userPacket['username'])

        status = FAILED
        if userPacket['cmd'] == 'register':
            status = self.handleRegister(userPacket, userDB, userDict)
        elif userPacket['cmd'] == 'login':
            status = self.handleLogin(userPacket, userDB, userDict, userBlocked, userSocket)

        if status == SUCCESS:

            #TODO: what happens to loop after logging out
            messageDB = MessageDB()

            self.handleUnread(userDict, messageDB)

            global MQueue, UsersOnline
            MQueue[userPacket['username']] = False
            UsersOnline[userPacket['username']] = True
            self.getRegisteredUsers(userDB, userDict)

            pingThread = Thread(target=self.pingClient, args=(messageDB, userDict))
            pingThread.start()

            while userDict['isLoggedIn']:
                self.handleChat(userDB, userDict, messageDB)

            UsersOnline[userPacket['username']] = False
            time.sleep(0.2)
            self.request.close()

    def handleRegister(self, userPacket, userDB, userDict):
        if userDict:
            self.request.sendall(USER_ALREADY_EXISTS)
            return FAILED
        else:
            # register
            userDB.register(userPacket['username'], userPacket['password'])
            self.request.sendall(YOU_ARE_REGISTERED)
            # user is auto-logged-in if registration is success
            return FAILED

    def handleLogin(self, userPacket, userDB, userDict, userBlocked, userSocket):
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
                userDict['socket'] = userSocket
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
            userDB.updateUserLoginBlockList(userBlocked)
            return  FAILED

    def handleUnread(self, userDict, messageDB):
        print userDict['username'], "handleUnread"
        msgs = messageDB.getUnreadMessages(userDict['username'])
        for msg in msgs:
            msg = str(msg)
            lenmsg = len(msg)
            lenmsg = str(struct.pack(">q", lenmsg))
            msg = lenmsg + msg
            self.request.send(msg)
        messageDB.removeUnreadMessages(userDict['username'])
        global MQueue
        MQueue[userDict['username']] = False

    def handleChat(self, userDB, userDict, messageDB):

        print "in handleChat"
        lenmsg = self.request.recv(8)
        lenmsg = struct.unpack(">q", lenmsg)[0]
        print lenmsg
        msg = eval(self.request.recv(lenmsg))

        if msg['cmd'] == 'send':
            if msg['msgType'] == PRIVATE:
                self.handlePrivateMessage(userDB, userDict, msg, messageDB, broadcast=False)
            elif msg['msgType'] == BROADCAST:
                self.handleBroadcastMessage(userDB, userDict, msg, messageDB)
        elif msg['cmd'] == BLOCK:
            # update userBlockList
            userBlockSet = userDB.getUserBlockList(userDict['username'])
            print 'enetered block <', userBlockSet, '>'
            if userBlockSet is not None:
                if msg['blockedUser'] not in userBlockSet['blockSet']:
                    userBlockSet['blockSet'].append(msg['blockedUser'])
                    userDB.updateUserBlockList(userBlockSet)
                    print 'userBlockSet is not None'
            else:
                userBlockSet = {'username': userDict['username'], 'blockSet': [msg['blockedUser']]}
                userDB.updateUserBlockList(userBlockSet)
                print 'userBlockSet is None, but added now'
                print userDB.getUserBlockList(userDict['username'])
        elif msg['cmd'] == UNBLOCK:
            # update userBlockList
            userBlockSet = userDB.getUserBlockList(userDict['username'])
            if userBlockSet is not None:
                if msg['unblockedUser'] in userBlockSet['blockSet']:
                    print userBlockSet['blockSet']
                    userBlockSet['blockSet'].remove(msg['blockedUser'])
                    userDB.updateUserBlockList(userBlockSet)
                    print userBlockSet['blockSet'], " after"
        elif msg['cmd'] == LOGOUT:
            self.handleLogout(userDB, userDict)
        elif msg['cmd'] == WHOISTHERE:
            self.handleWhoIsThere(userDB, userDict, messageDB)
        elif msg['cmd'] == WHOELSE:
            self.handleWhoElse(userDB, userDict, messageDB)

        # elif msg['cmd'] == 'timeout' or msg['cmd'] == 'view':
        #     self.handleUnread(userDict, messageDB)

    def handlePrivateMessage(self, userDB, userDict, msgPacket, messageDB, broadcast=False):
        toUser = msgPacket['toUser']
        receiver = userDB.getUserData(toUser)
        if not receiver:
            return
        # if toUser is blocked then simply exit this method else continue to next step
        uBlockList = userDB.getUserBlockList(toUser)
        print '<', uBlockList, '>'
        if uBlockList is None or userDict['username'] not in uBlockList['blockSet']:
            messageDB.addUnreadMessage(toUser, userDict['username'], msgPacket)
            global MQueue
            if toUser in MQueue:
                MQueue[toUser] = True
        else:
            print 'blocked user: ', userDict['username'], ' by: ', toUser

    def handleBroadcastMessage(self, userDB, userDict, msgPacket, messageDB):
        activeUsers = userDB.getAllUsersLoggedIn()
        for receiver in activeUsers:
            msgPacket['toUser'] = receiver
            self.handlePrivateMessage(userDB, userDict, msgPacket, messageDB, broadcast=True)

    def handleLogout(self, userDB, userDict):
        print "logging Out", userDict['username']
        userDict['isLoggedIn'] = False
        userDict['lastActive'] = time.time()
        userDB.updateUserData(userDict)

    def handleWhoIsThere(self, userDB, userDict, messageDB):
        global UsersOnline, MQueue
        msgData = 'Online Users are\n'
        for u in UsersOnline:
            if UsersOnline[u]:
                msgData += '\t\t' + u + '\n'
        toUser = userDict['username']
        created = time.time()
        msgPacket = {'msgType': 'query', 'msgData': msgData,\
               'created': created, 'fromUser': 'server'}
        messageDB.addUnreadMessage(toUser, 'server', msgPacket)
        MQueue[toUser] = True

    def handleWhoElse(self, userDB, userDict, messageDB):
        global UsersRegistered, MQueue
        msgData = 'Registered Users are\n'
        for u in UsersRegistered[1]:
            msgData += '\t\t' + u + '\n'
        toUser = userDict['username']
        created = time.time()
        msgPacket = {'msgType': 'query', 'msgData': msgData,\
               'created': created, 'fromUser': 'server'}
        messageDB.addUnreadMessage(toUser, 'server', msgPacket)
        MQueue[toUser] = True

    def getRegisteredUsers(self, userDB, userDict):
        global UsersRegistered
        UsersRegistered[1][userDict['username']] = True
        if UsersRegistered[0]:
            return
        else:
            allUsers = userDB.getAllUsers()
            for u in allUsers:
                UsersRegistered[1][u] = True
            UsersRegistered[0] = True

    def pingClient(self, messageDB, userDict):
        global MQueue
        start = time.time()
        while True:
            if time.time()-start >= 0.1:
                if MQueue[userDict['username']]:
                    self.handleUnread(userDict, messageDB)
                start = time.time()

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

def main():
    global MQueue
    HOST = socket.gethostname()
    PORT = 9998
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

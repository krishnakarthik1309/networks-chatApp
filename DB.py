import pymongo
import time
from copy import deepcopy

class UserDB(object):
    def __init__(self):
        mongoServer = 'localhost'
        mongoPort = 27017
        dbName = 'userDB'
        userDataCollection = 'userData'
        userLoginBlockListCollection = 'userLoginBlockList'
        userBlockListCollection = 'userBlockList'

        connection = pymongo.MongoClient(mongoServer, mongoPort)
        db = connection[dbName]
        self.userData = db[userDataCollection]
        self.userLoginBlockList = db[userLoginBlockListCollection]
        self.userBlockList = db[userBlockListCollection]

    def getUserData(self, username):
        return self.userData.find_one({'username': username})

    def getUserLoginBlockList(self, username):
        return self.userLoginBlockList.find_one({'username': username})

    def updateUserData(self, updatedData):
        username = updatedData['username']
        oldData = self.getUserData(username)
        self.userData.replace_one(oldData, updatedData)

    def updateUserLoginBlockList(self, updatedData):
        username = updatedData['username']
        oldData = self.getUserLoginBlockList(username)
        if oldData is None:
            self.userLoginBlockList.insert(updatedData)
        else:
            self.userLoginBlockList.replace_one(oldData, updatedData)

    def register(self, username, password):
        self.userData.insert({'username': username, 'password': password, 'isLoggedIn': False, 'socket': [-1, -1]})

    def getAllUsersLoggedIn(self):
        active = []
        for user in self.userData.find({'isLoggedIn': True}):
            active.append(user['username'])
        return active

    def getAllUsers(self):
        allU = []
        for user in self.userData.find({}):
            allU.append(user['username'])
        return allU

    def getUserBlockList(self, username):
        print 'get'
        return self.userBlockList.find_one({'username': username})

    def updateUserBlockList(self, updatedData):
        print 'update'
        username = updatedData['username']
        oldData = self.getUserLoginBlockList(username)
        if oldData is None:
            self.userBlockList.insert(updatedData)
        else:
            self.userBlockList.replace_one(oldData, updatedData)

class MessageDB(object):
    def __init__(self):
        mongoServer = 'localhost'
        mongoPort = 27017
        dbName = 'messageDB'
        messageCollection = 'messageCollection'

        connection = pymongo.MongoClient(mongoServer, mongoPort)
        db = connection[dbName]
        self.messages = db[messageCollection]

    def getUnreadMessages(self, username):
        msgs = []
        for msg in self.messages.find({'toUser': username}, {'_id': False}):
            msgs.append(msg)
        return msgs

    def removeUnreadMessages(self, username):
        self.messages.delete_many({'toUser': username})

    def addUnreadMessage(self, toUser, fromUser, message):
        # self.messages.insert({'toUser': toUser, 'fromUser': fromUser, 'message': message, 'time': int(time.time())})
        M = deepcopy(message)
        M['toUser'] = toUser
        M['fromUser'] = fromUser
        M['time'] = time.time()
        #print message
        self.messages.insert(M)

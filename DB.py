import pymongo
import time

class UserDB(object):
    def __init__(self):
        mongoServer = 'localhost'
        mongoPort = 27017
        dbName = 'userDB'
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
        oldData = self.getUserBlockList(username)
        if oldData is None:
            self.userBlockList.insert(updatedData)
        else:
            self.userBlockList.replace_one(oldData, updatedData)

    def register(self, username, password):
        self.userData.insert({'username': username, 'password': password, 'isLoggedIn': False})

    def getAllUsersLoggedIn(self):
        active = []
        for user in self.userData.find({'isLoggedIn': True}):
            active.append(user['username'])
        return active


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
        return self.messages.find({'toUser': username})

    def removeUnreadMessages(self, username):
        self.messages.delete_many({'toUser': username})

    def addUnreadMessage(self, toUser, fromUser, message):
        self.messages.insert({'toUser': toUser, 'fromUser': fromUser, 'message': message, 'time': int(time.time())})

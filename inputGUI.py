from Tkinter import *
import sys
import struct
import socket
from client import messagePacket

class mainWindow(object):
    def __init__(self,master, server, userDetails):
        self.master=master
        self.server=server
        self.userDetails=userDetails
        self.l=Label(master,text="Enter your command here")
        self.l.pack()
        self.e=Entry(master)
        self.e.pack()
        self.b=Button(master,text='Ok',command=self.sendToMain)
        self.b.pack()

    def sendToMain(self, event=None):
        message = self.e.get()
        if message == 'logout':
            self.master.quit()
        sys.stdout.write("<{}(you)>:  {}\n".format(self.userDetails['username'], message))
        self.e.delete(0, 'end')
        packet = messagePacket(message.strip().split(), self.userDetails)
        if not packet:
            return
        l, message =  packet
        #print l, message
        l = str(struct.pack(">q", l))
        message = l + str(message)
        self.server.send(message)
        # self.master.destroy()

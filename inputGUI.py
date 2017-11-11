from Tkinter import *
import sys
import struct
import socket
from client import messagePacket

class mainWindow(object):
    def __init__(self,master, server, userDetails):
        self.master=master
        master.minsize(width=640, height=480)
        self.server=server
        self.userDetails=userDetails
        self.l=Label(master,text="Enter your command here")
        self.l.pack()
        self.e = Text(master, height=15, width=100)
        self.e.configure(font=("Helvetica", 12))
        self.e.pack()
        self.b=Button(master,text='Ok',command=self.sendToMain)
        self.b.pack()
        self.master.title("CS425A Chat Application :\t Client \t{}(you)".format(userDetails['username']))


    def sendToMain(self, event=None):
        message = self.e.get(1.0,END)
        if message == 'logout':
            self.master.quit()
        sys.stdout.write("<{}(you)>:  {}".format(self.userDetails['username'], message))
        self.e.delete(1.0, 'end')
        packet = messagePacket(message.strip().split(), self.userDetails)
        if not packet:
            return
        l, message =  packet
        # print l, message
        l = str(struct.pack(">q", l))
        message = l + str(message)
        self.server.send(message)
        # self.master.destroy()

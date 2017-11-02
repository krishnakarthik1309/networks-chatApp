import sys

# assumption: no need for acks
def wrapSend(s, packet):
    data = str(packet)
    s.sendall(str(len(data)))
    s.sendall(data)

def wrapRecv(s):
    dataLen = int(s.recv(sys.getsizeof(int())))
    if dataLen == 0:
        return -1
    return eval(s.recv(dataLen))

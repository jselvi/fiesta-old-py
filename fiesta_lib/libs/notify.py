from .message import Message
from time import time
#from queue import Queue

class QueueNotify:
    def __init__(self):
        self.msg_queue = None

    def set_queue( self, msg_queue ):
        self.msg_queue = msg_queue

    def notify( self, tag, data ):
        return self.notify2( self.client_address[0], self.client_address[1], tag, data )

    def notify2( self, host, port, tag, data ):
        msg = Message()
        msg.tag = tag 
        msg.timestamp = int( time() * 1000 )
        msg.host = host
        msg.port = port
        msg.data = int(data)
        self.msg_queue.put( msg )

import socket
from .notify import QueueNotify
from socketserver import BaseRequestHandler, ThreadingMixIn, TCPServer
from threading import Thread
from queue import Queue
from hashlib import md5
from time import time,sleep

class cProxyClient(Thread,QueueNotify):
    def __init__(self, source):
        super(cProxyClient, self).__init__()
        Thread.__init__(self)
        self.source = source
        self.config = None
        self.client_address = None
        self.dest = None
        self.out = None
        self.bytes_received = 0
        self.current_connection = 0

    def set_parent( self, parent ):
        self.client_address = parent.client_address

    def set_output( self, out ):
        self.out = out

    def configure( self, config ):
        self.config = config

    def run(self):
        self.dest = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.dest.connect((self.config.relay_host, self.config.relay_port))

        while True:
            try:
                data = self.dest.recv(4096)
            except:
                break
            if len(data) == 0:
                break
            datalen = self.ssl_data(data)
            self.bytes_received += datalen
            self.out.console_print("[???] res: "+str(len(data))+'('+str(datalen)+')')
            if datalen != 0:
                self.notify("RES",str(datalen))

            try:
                self.source.sendall(data)   # TEST
            except:
                pass

            if self.config.http2 == None:
                self.config.http2 = self.is_http2(data)
                if self.config.http2 == True:
                    self.out.console_print("[??] HTTP/2 connection detected: "+self.client_address[0]+":"+str(self.client_address[1]))
                    self.notify("VER",2)

        try:
            self.source.shutdown(socket.SHUT_RDWR)
            self.source.close()
        except:
            self.notify("ACC",str(self.bytes_received))

    def write(self, data):
        # Try to write 3 times, since sometimes fails in the first connection
        for i in [1, 2, 3]:
            try:
                self.dest.send(data)
                break
            except:
                sleep(1)
        datalen = self.ssl_data(data)
        port = str(self.client_address[1])
        if datalen > self.config.min_request:
            self.current_connection += 1
            self.out.console_print("[???] connection ("+port+"): "+str(self.current_connection))
        self.out.console_print("[???] req("+port+"): "+str(len(data))+'('+str(datalen)+')')
        if datalen != 0:
            if (self.config.control not in ["img"]) and (self.config.oracle not in ["connections"]) and ( self.current_connection > self.config.connection):
                self.out.console_print("[???] ign("+port+"): "+str(len(data))+'('+str(datalen)+')')
                self.stop()
                return
            self.notify("ACC",str(self.bytes_received))
            self.notify("REQ",str(datalen))
            self.bytes_received = 0

    def stop(self):
        try:
            self.dest.shutdown(socket.SHUT_RDWR)
            self.dest.close()
        except:
            pass
        self.notify("ACC",str(self.bytes_received))

    def ssl_data( self, data ):
        if len(data) == 0:
            return 0
        # If it is invalid, count the full packet as data
        if data[0] < 20 or data[0] > 24:
            return len(data)
        # If valid, get length
        l = int.from_bytes(data[3:5], 'big')
        # And continue with the rest of the packet
        end = l + 5 # SSL data header + data
        more = self.ssl_data( data[end:] )
        # If not data, ignore it
        if data[0] != 0x17:
            return more
        else:
            return ( l + more )

    def ssl_data_split( self, data ):
        ld = len(data)
        if ld == 0:
            return 1
        # If it is invalid, count the full packet as data
        if data[0] < 20 or data[0] > 24:
            return ld
        # If valid, get length
        l = int.from_bytes(data[3:5], 'big')
        # Calculate end of SSL Data packet
        end = l + 5 # SSL data header + data
        if end > ld:
            return ld
        else:
            return end

    def is_http2(self, data):
        if self.ssl_data(data) > 0:
            return None
        if (b'h2' in data):
            return True
        else:
            return False

class cProxyHandler(BaseRequestHandler, QueueNotify):

    accept_more_requests = True

    def handle(self):

        self.config    = self.server.config
        self.msg_queue = self.server.msg_queue

        self.server.out.console_print("[??] SSL Proxy from: "+self.client_address[0]+":"+str(self.client_address[1]))

        if self.server.config.oracle == "connections":
            timestamp = int( time() * 1000 )
            self.notify("CONN",timestamp)

        if self.server.config.action == "drop":
            self.request.close()
            return

        f = cProxyClient(self.request)
        f.set_parent(self)
        f.set_queue(self.server.msg_queue)
        f.set_output(self.server.out)
        f.configure(self.server.config)
        f.start()

        while True:
            try:
                data = self.request.recv(4096)
            except:
                data = ""
            if len(data) == 0:
                break

            #datalen = f.ssl_data(data)

            #if (datalen > 0) and not self.accept_more_requests:
            #    break

            if self.server.config.demultiplex:
                first_byte = 0
                while ( first_byte < len(data) ):
                    end = f.ssl_data_split(data[first_byte:])
                    end += first_byte
                    f.write(data[first_byte:end])
                    sleep(0.1) # Improve this at some point
                    first_byte = end
            else:
                f.write(data)

            ## We only allow a single request per connection
            ## Now we can track connections using the source port
            #if (self.config.oracle == "response") and (datalen > 0):
            #    print("NO MORE REQUESTS") # JSELVI
            #    self.accept_more_requests = False

        f.stop()
        self.request.close()

class cProxyServer(ThreadingMixIn, TCPServer, QueueNotify):
    def __init__( self, binder, handler ):
        super(cProxyServer, self).__init__( binder, handler )
        self.config    = None
        self.daemon_threads = True
        self.out       = None
    
    def set_output( self, out ):
        self.out = out

    def configure( self, config ):
        self.config = config

class cProxy(QueueNotify):

    def __init__( self ):
        super(cProxy, self).__init__()
        self.config    = None
        self.server    = None
        self.out       = None
        self.thread_server = None

    def set_output( self, out ):
        self.out = out

    def configure( self, config ):
        self.config = config

    def start( self ):
        self.server = cProxyServer(('0.0.0.0', 443), cProxyHandler)
        self.server.set_queue( self.msg_queue )
        self.server.set_output( self.out )
        self.server.configure( self.config )
        self.thread_server = Thread(target=self.server.serve_forever,daemon=True).start()
        self.server.out.console_print("[*] Proxy Server started 0.0.0.0:443")

    def stop( self ):
        self.server.shutdown()
        #self.thread_server.stop()
        self.server = None

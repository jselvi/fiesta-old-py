import curses, curses.panel, math
class FOutput:
    def __init__( self ):
        self.is_text = True
        self.stdscr  = None
        self.text    = None
        self.logo    = None
        self.verbose = 0
        self.counter = 0
        self.maxx    = 0
        self.maxy    = 0
        self.set_banner()

    def set_banner( self ):
        self.logox   = 30
        self.logoy   = 37
        self.banner = list()
        self.banner.append("    ODZ")
        self.banner.append("    :8,")
        self.banner.append("     D")
        self.banner.append("     .")
        self.banner.append("     7D")
        self.banner.append("     NMD.")
        self.banner.append("      NM7 :....")
        self.banner.append("      ZNN:,Z8O$.")
        self.banner.append("       DM8 +DDO,")
        self.banner.append("        8MM.MM+.")
        self.banner.append("       8O+O.8M  ,ZZ,")
        self.banner.append("      Z8?I=.D?DDDDM$")
        self.banner.append("     :DMM=D D=MNNNMMD+")
        self.banner.append("     7DMD8+8M=DMMM 8MMDM")
        self.banner.append("     $NN$MZNN~DM8,   N8ND")
        self.banner.append("     IMN$MZMN~NMD.    MZM:")
        self.banner.append("     ONM?DONN~D8D      =MN.")
        self.banner.append("     MNN?D$MMMMMDZ      NM$")
        self.banner.append("     ZMD??~M8=:8NN.     ,M~")
        self.banner.append("       :8N?ZMMMNMMN     :D+")
        self.banner.append("          NM:8NDMMM$    NM+")
        self.banner.append("        ?MMM8MMD8MOO")
        self.banner.append("       DNMMMND DMN+8")
        self.banner.append("      NDMNDD    MMMN~")
        self.banner.append("     MDMND+      NMND")
        self.banner.append("    NMNDN,       MDMM")
        self.banner.append("   ,MNN+          DMDI")
        self.banner.append("   MMMM?          7MNN,")
        self.banner.append("   8MDN           ,ONNN")
        self.banner.append("   MNMO            MMNND")
        self.banner.append("  +DDD:            INNMM.")
        self.banner.append("  DN8D,             D8ND.")
        self.banner.append("  N8ND:             :8MM8")
        self.banner.append(" :8DDO,              ONDN=.")
        self.banner.append("                     8NNND,")

    def set_verbose( self, level ):
        if level > 3:
            level = 3
        if level < 0:
            level = 0
        self.verbose = level

    def set_text( self ):
        self.is_text = True

    def set_curses( self ):
        self.is_text = False

    def maxrows( self ):
        return self.maxy*10

    def maxcols( self ):
        return self.maxx-self.logox

    def start( self ):
        if not self.is_text:
            self.counter = 0
            curses.wrapper( self.start_curses )

    def start_curses( self, stdscr ):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.maxy,self.maxx = self.stdscr.getmaxyx()
        self.logo = curses.newwin( self.logoy, self.logox, 0, 0 )
        self.logo.erase()
        logolines = 0
        for line in self.banner:
            logolines += 1
            if logolines <= self.maxrows():
                self.logo.addstr(line+"\n")
        self.plogo = curses.panel.new_panel(self.logo)

        self.text = curses.newpad( self.maxrows(), self.maxcols() )
        self.stdscr.refresh()

    def console_print( self, s ):
        if (self.verbose > 0) and s.startswith('[') and (']' in s):
            tag = s.split('[')[1].split(']')[0]
            l = len(tag)
            if self.verbose < l:
                return
        if (self.verbose == 0) and s.startswith('[?'):
            return

        if len(s) == 0:
            return

        if self.is_text:
            print(s)
        else:
            self.maxy,self.maxx = self.stdscr.getmaxyx()
            maxstring = self.maxx - self.logox - 1
            l = len(s)
            if l > maxstring:
                ss = s[maxstring+1:]
                s  = s[:maxstring]
            self.counter += 1
            if self.counter >= self.maxrows():
                self.start()
            self.text.addstr( s + "\n" )
            scroll_point = max( 0, self.counter-self.maxy )
            self.text.refresh( scroll_point, 0, 0, 30, self.maxy-1, self.maxx-1 )
            curses.panel.update_panels()
            self.stdscr.refresh()
            #if l > maxstring:
            #    self.console_print("Hi")

    def __del__( self ):
        if not self.is_text:
            curses.endwin()

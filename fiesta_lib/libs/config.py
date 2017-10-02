from math import ceil

class Config:

    def __init__( self ):
        
        # General config
        self.comment     = "Please intercept the proper connection"
        
        # cServer config
        self.cserver_ip  = None
        self.control_options = ["img", "open", "iframe"]
        self.control     = self.control_options[0] # Technique used 
        self.guess_delay = 2
        self.test_delay  = 4
        self.url         = None
        self.post_data   = None
        self.wrong_term  = "^^^"

        # cProxy config
        self.relay_host     = "" 
        self.relay_port     = 0
        self.http2          = None
        self.action_options = ["relay", "drop", "ignore", "delay", "drop_until_connection"]
        self.action         = self.action_options[0]
        self.demultiplex    = False
        
        # Fiesta config
        self.connection     = 1
        self.method_options = ["GET", "POST", "all"]
        self.method         = self.method_options[2]
        self.oracle_options = ["response", "connections"]
        self.oracle         = self.oracle_options[0]
        self.size_threshold = 30
        self.min_request    = 0
        self.max_retry_wait = 100
        self.dev            = False

        # Tmp
        self.term            = ""
        self.charset         = ""

    def config( self, yaml ):
        if not yaml:
            yaml = {}
            yaml["fakeoption"] = 0  # avoid further error

        if "comment" in yaml:
            if isinstance(yaml["comment"],str):
                self.comment = yaml["comment"]
            else:
                raise ValueError("comment should be a string")

        if "control" in yaml:
            if isinstance(yaml["control"],str):
                if yaml["control"] in self.control_options:
                    self.control = yaml["control"]
                else:
                    raise ValueError("Unknown control server option")
            else:
                raise ValueError("control should be a string")

        if "guess_delay" in yaml:
            if isinstance(yaml["guess_delay"],int):
                if yaml["guess_delay"] > 0:
                    self.guess_delay = yaml["guess_delay"]
                else:
                    raise ValueError("guess_delay should be an integer greater than 0")
            else:
                raise ValueError("guess_delay should be an integer greater than 0")

        if "test_delay" in yaml:
            if isinstance(yaml["test_delay"],int):
                if (self.control == "img") or (yaml["test_delay"] > self.guess_delay):
                    self.test_delay = yaml["test_delay"]
                else:
                    raise ValueError("test_delay should be an integer bigger than guess_relay")
            else:
                raise ValueError("test_delay should be an integer bigger than guess_relay")

        # Open to discussion...
        self.between_guess_test_delay = self.test_delay - ceil( (self.test_delay-self.guess_delay)/2 )

        if "url" in yaml:
            if isinstance(yaml["url"],str):
                if yaml["url"].startswith("https://"):
                    self.url = yaml["url"]
                else:
                    raise ValueError("url should be: https://whatever.com/blablabla/")
            else:
                raise ValueError("url should be a string")
        else:
            raise ValueError("a target url is mandatory")

        if "post_data" in yaml:
            if isinstance(yaml["post_data"],str):
                self.post_data = yaml["post_data"]
            else:
                raise ValueError("post_data should be a string")

        if self.post_data:
            full_request = self.url + self.post_data
        else:
            full_request = self.url
        if (full_request).count('§1§') != 1:
            raise ValueError("§1§ was not properly configured")

        if "wrong_term" in yaml:
            if isinstance(yaml["wrong_term"],str):
                self.wrong_term = yaml["wrong_term"]
            else:
                raise ValueError("wrong_term should be a string")

        if "relay_host" in yaml:
            if isinstance(yaml["relay_host"],str):
                self.relay_host = yaml["relay_host"]
            else:
                raise ValueError("relay_host should be a hostname or IP address")

        if "relay_port" in yaml:
            if isinstance(yaml["relay_port"],int):
                if yaml["relay_port"] > 0:
                    self.relay_port = yaml["relay_port"]
                else:
                    raise ValueError("relay_port should be an integer bigger than 0")
            else:
                raise ValueError("relay_port should be an integer bigger than 0")

        if "action" in yaml:
            if isinstance(yaml["action"],str):
                if yaml["action"] in self.action_options:
                    self.action = yaml["action"]
                else:
                    raise ValueError("Unknown control server option")
            else:
                raise ValueError("action should be a string")

        if "demultiplex" in yaml:
            if isinstance(yaml["demultiplex"],bool):
                self.demultiplex = yaml["demultiplex"]
            else:
                raise ValueError("demultiplex should be boolean")

        if "connection" in yaml:
            if isinstance(yaml["connection"],int):
                if yaml["connection"] > 0:
                    self.connection = yaml["connection"]
                else:
                    raise ValueError("connection should be an integer bigger than 0")
            else:
                raise ValueError("connection should be an integer bigger than 0")
        
        if self.control == "img" and self.connection > 1:
            raise ValueError("Technique with IMG tag can only get 1 connection")

        if "method" in yaml:
            if isinstance(yaml["method"],str):
                if yaml["method"] in self.method_options:
                    self.method = yaml["method"]
                else:
                    raise ValueError("method is invalid")
            else:
                raise ValueError("method should be a string")

        if "oracle" in yaml:
            if isinstance(yaml["oracle"],str):
                if yaml["oracle"] in self.oracle_options:
                    self.oracle = yaml["oracle"]
                else:
                    raise ValueError("oracle technique invalid")
            else:
                raise ValueError("oracle should be a string")

        if "dev" in yaml:
            if isinstance(yaml["dev"],bool):
                self.dev = yaml["dev"]
            else:
                raise ValueError("dev should be boolean")

        if "min_request" in yaml:
            if isinstance(yaml["min_request"],int):
                if yaml["min_request"] > 0:
                    self.min_request = yaml["min_request"]
                else:
                    raise ValueError("min_request should be an integer bigger than 0")

            else:
                raise ValueError("min_request should be an integer bigger than 0")

        if "size_threshold" in yaml:
            if isinstance(yaml["size_threshold"],int):
                if yaml["size_threshold"] > 0:
                    self.size_threshold = yaml["size_threshold"]
                else:
                    raise ValueError("size_threshold should be an integer bigger than 0")

            else:
                raise ValueError("size_threshold should be an integer bigger than 0")

        if "term" in yaml:
            if isinstance(yaml["term"],str):
                self.term = yaml["term"]
            else:
                raise ValueError("term should be a string")

        if "charset" in yaml:
            if isinstance(yaml["charset"],str) or isinstance(yaml["charset"],list):
                if len(yaml["charset"]) > 0:
                    self.charset = yaml["charset"]
                else:
                    raise ValueError("charset too short")
            else:
                raise ValueError("charset should be a string")

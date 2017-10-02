class Message:
    msg_type = ""
    timestamp = 0
    url  = ""
    host = ""
    port = 0
    data = 0

    def __str__(self):
        if len(self.url) > 0:
            message = self.tag+"|"+str(self.timestamp)+"|"+str(self.data)
        else:
            message = self.tag+"-"+str(self.port)+"|"+str(self.timestamp)+"|"+str(self.data)
        return message

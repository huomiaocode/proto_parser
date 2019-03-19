#!/usr/bin/python
# -*- coding:utf-8 -*-


import os
import re


class ProtoEnumItem:
    def __init__(self, name="", value=0, comments=""):
        self.name = name
        self.value = value
        self.comments = comments

class ProtoEnum:
    def __init__(self, name="", comments=""):
        self.name = name
        self.comments = comments
        self.items = []
        
    def addEnumItem(self, enumItem):
        self.items.append(enumItem)

class ProtoMessageItem:
    def __init__(self, optType="optional", fieldType="uint32", name="", serial=1, comments=""):
        self.optType = optType
        self.fieldType = fieldType
        self.name = name
        self.serial = serial
        self.comments = comments

class ProtoMessage:
    def __init__(self, name="", comments=""):
        self.name = name
        self.comments = comments
        self.items = []
        
    def addMessageItem(self, messageItem):
        self.items.append(messageItem)     


class ProtoInfo:

    opt_arr = ["required", "optional", "repeated"]
    dk_l = "大括左"
    dk_r = "大括右"
    
    def __init__(self):
        self.protoFile = ""
        self.protoContent = ""
        self.enumInfos = []
        self.messageInfos = []
        
    def parseProto(self, protoFile):
        if not os.path.exists(protoFile):
            print("proto file is not exist, %s" % protoFile)
            return
        
        protoContent = ""
        with open(protoFile) as f:
            protoContent = f.read()
        
        if protoContent == "":
            print("proto file content is null, %s" % protoFile)
            return
        
        self.protoFile = protoFile
        self.protoContent = protoContent
        self.enumInfos = []
        self.messageInfos = []

        parseContent = protoContent

        # 替换注释里的 { 和 }
        c = re.compile("//[^\n]*?\n", flags=re.M|re.S)
        def rep_func(x):
            return x.group(0).replace("{", self.dk_l).replace("}", self.dk_r)
        parseContent = re.sub(c, rep_func, parseContent)

        # 查找枚举
        c = re.compile("(//[^\{]*?(?=enum))?(enum\s+\w+\s*\{[^\}]*?\})", flags=re.M|re.S)
        enums = c.findall(parseContent)
        parseContent = re.sub(c, "", parseContent)

        # 查找消息，循环遍历，处理message嵌套
        messages = []
        while True:
            c = re.compile("(//[^\{]*?(?=message))?(message\s+\w+\s*\{[^\{\}]*?\})", flags=re.M|re.S)
            messages_ = c.findall(parseContent)
            if len(messages_) == 0:
                break
            messages.extend(messages_)
            parseContent = re.sub(c, "", parseContent)

        # 解析枚举
        for comments, enumStr in enums:
            info = self._parseEnum(comments, enumStr)
            if info != None:
                self.enumInfos.append(info)

        # 解析消息
        for comments, messageStr in messages:
            info = self._parseMessage(comments, messageStr)
            if info != None:
                self.messageInfos.append(info)

        print("parse_proto end.")

    def _parseEnum(self, comments, enumStr):
        comments = comments.strip()[2:].lstrip().replace(self.dk_l, "{").replace(self.dk_r, "}")

        rets = re.compile("enum\s+(\w+)\s*\{([^\}]*?)\}", flags=re.M|re.S).findall(enumStr)
        if len(rets) == 0:
            return None
        
        enumName, enumContent = rets[0]
        print("find enum, %s %s" % (enumName, comments))
        
        protoEnum = ProtoEnum(enumName, comments)

        lines = enumContent.split("\n")
        for line in lines:
            line = line.strip()
            if line == "":
                continue
            
            commentsLine = ""
            if "//" in line:
                idx = line.index("//")
                commentsLine = line[idx + 2:].strip().replace(self.dk_l, "{").replace(self.dk_r, "}")

            rets2 = re.compile("(\w*?)\s*?=\s*?(\d+)\s*?;", re.S).findall(line)
            if len(rets2) == 0:
                continue
            
            rets20 = rets2[0]
            enumItem = ProtoEnumItem(rets20[0], int(rets20[1]), commentsLine)
            protoEnum.addEnumItem(enumItem)

        return protoEnum

    def _parseMessage(self, comments, messageStr):
        comments = comments.strip()[2:].lstrip().replace(self.dk_l, "{").replace(self.dk_r, "}")

        rets = re.compile("message\s+(\w+)\s*\{([^\}]*?)\}", flags=re.M|re.S).findall(messageStr)
        if len(rets) == 0:
            return None
        
        messageName, messageContent = rets[0]
        print("find message, %s %s" % (messageName, comments))
        
        protoMessage = ProtoMessage(messageName, comments)

        lines = messageContent.split("\n")
        for line in lines:
            line = line.strip()
            if line == "":
                continue

            commentsLine = ""
            if "//" in line:
                idx = line.index("//")
                commentsLine = line[idx + 2:].strip().replace(self.dk_l, "{").replace(self.dk_r, "}")

            # 如果省掉 optional 的话，这里要加上去
            findIt = False
            for t in self.opt_arr:
                if line[:len(t)] == t:
                    findIt = True
                    break
            if not findIt:
                line  = "optional " + line

            rets2 = re.compile("(\w*?)\s+(\w*?)\s+(\w*?)\s*?=\s*?(\d+)\s*?;", re.S).findall(line)
            if len(rets2) == 0:
                continue
            
            rets20 = rets2[0]
            messageItem = ProtoMessageItem(rets20[0], rets20[1], rets20[2], int(rets20[3]), commentsLine)
            protoMessage.addMessageItem(messageItem)

        return protoMessage


if __name__ == "__main__":
    protoInfo = ProtoInfo()
    protoInfo.parseProto("%s/test.proto" % (os.path.dirname(__file__), ))
    print(protoInfo)
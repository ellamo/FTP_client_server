# -*- coding: utf-8 -*-
"""
Homework 6 - FTP Client Program : Comp 431 : Molly Moore (moorem24) : PID 730134118

Interoperablitity testing assignment  

"""


import sys
from socket import *
import re


######################### VARS ################################
### command line argument of initial port number for a "welcoming" socket with server
welcomePort = int(sys.argv[1])
### global for last reply code seen
global prevCode
### file counter for retreived files
fileCount = 1
# flag for valid connection encountered 
connected = False
### start index for generating <port-number>
portIndex = welcomePort
################### END VARIABLES #############################




################### FUNCTION ##################################
def check_reply(line):
    global prevCode
    
    # echo line
    #sys.stdout.write(line)
    
    # bool flag for validity and CRLF
    isvalid = True
    goodEOL = False
    
    # break out line components
    code = line[:4]
    text = line[4:]
    if (line[-2:] == "\r\n"):
        goodEOL = True
        text = text[:-2]
    elif (line[-2:] == "\n\r"):
        text = text[:-2]
    elif (line[-1:] in ["\r", "\n"]):
        text = text[:-1]
    
    # check <reply-code>
    result = re.match("^[1-5][0-9][0-9][\s]$", code)
    if (result == None):
        print("ERROR -- reply-code")
        isvalid = False
    else:
        prevCode = code
    
    # check <reply-text>
    if (isvalid == True):
        for char in text:
            if (ord(char) > 127) or (char in ["\r", "\n"]):
                isvalid = False
                print("ERROR -- reply-text")
                break
    
    # check <CRLF>
    if (goodEOL == False):
        print("ERROR -- <CRLF>")
        isvalid = False
    
    # valid reply line
    ### added return statements
    if (isvalid == True):
        return "FTP reply " + code + "accepted. Text is: " + text
    else:
        return ""
############## END CHECK_REPLY FUNCTION #######################




###################### MAIN ###################################
# loop through input
for line in sys.stdin:

    # echo line
    sys.stdout.write(line)
    
    # strip EOL chars <CR> <LF>
    if (line[-2:] == "\r\n") or (line[-2:] == "\n\r"):
        line = line[:-2]
    elif (line[-1:] == "\r") or (line[-1:] == "\n"):
        line = line[:-1]
        
        
    ######################## CASE 1 ###########################    
    # evaluate by case: CONNECT
    if (line[:8].upper() == "CONNECT "):
        
        # Bool flag for invalid command
        invalid = False
        # trim command and leading whitespaces
        line = line[7:].lstrip(" ")
        # find index of first whitespace between <server-host> and <server-port>
        index = line.find(" ")
        # break out host and port
        host = line[:index]
        port = line[index:].lstrip(" ")
        
        #check <server-host> for errors
        result = re.match("^[A-Z|a-z][A-Z|a-z|0-9]*(.[A-Z|a-z][A-Z|a-z|0-9]*)*$", host)
        if (result == None):
            print("ERROR -- server-host")
            invalid = True
        
        # check <server-port> for errors
        if (invalid == False):
            result = re.match("^[1-9][0-9]*$|^[0]$", port)
            if (result == None):
                print("ERROR -- server-port")
                invalid = True
            elif (int(port) > 65535):
                print("ERROR -- server-port")
                invalid = True

        # CONNECT valid    
        if (invalid == False):
            print("CONNECT accepted for FTP server at host " + host + " and port " + port)
            ### close previous socket if valid CONNECT already exists
            if (connected == True):
                ctrSocket.close()
            try:
                ### connect to server
                ctrSocket = socket(AF_INET, SOCK_STREAM)
                ctrSocket.connect((host, int(port)))
    
                ### check response from server
                reply = ctrSocket.recv(1024)
                response = check_reply(reply.decode())
                if (response != ""):
                    # set flag for sequential line handling 
                    connected = True
                    # print success line 
                    print(response)
                    ### generate and send FTP lines
                    FTPlines = ["USER anonymous\r\n", "PASS guest@\r\n", "SYST\r\n", "TYPE I\r\n"]
                    for l in FTPlines:
                        sys.stdout.write(l)
                        ctrSocket.send(l.encode())
                        reply = ctrSocket.recv(1024)
                        response = check_reply(reply.decode())
                        if response != "":
                            print(response)
                    # reset portIndex
                    #portIndex = welcomePort
            except:
                print("CONNECT failed")
    #################### END CONNECT CASE ##################### 
            
            
    
    ##################### CASE 2 ##############################         
    # evaluate by case: GET
    elif (line[:4].upper() == "GET "):
        
        # Bool flag for invalid command
        invalid = False
        
        # trim command and leading whitespaces
        path = line[4:].lstrip(" ")
        
        # check <pathname>
        for char in line:
            if (ord(char) > 127) or (char == "\r") or (char == "\n"):
                invalid = True
                break
        if (invalid == True):
            print("ERROR -- pathname")
        
        # check for bad sequence
        if (invalid == False) and (connected == False):
            print("ERROR -- expecting CONNECT")
            invalid = True
        
        # valid GET
        if (invalid == False):
            # print success line
            print("GET accepted for " + path)
            
            # determine <host-address>
            myIP = gethostbyname(gethostname())
            address = myIP.replace('.', ',')
            
            # calculate <port-number>
            f = int(portIndex / 256)
            r = portIndex % 256
            port = str(f) + "," + str(r)
            
            try:
                ### set up UDP Socket
                dataSocket = socket(AF_INET, SOCK_STREAM)
                dataSocket.bind(('', int(portIndex)))
                dataSocket.listen(1)
                
                ### generate FTP commands
                FTPlines = ["PORT " + address + "," + port + "\r\n", "RETR " + path + "\r\n"]
                for l in FTPlines:
                    sys.stdout.write(l)
                    ctrSocket.send(l.encode())
                    reply = ctrSocket.recv(1024)
                    response = check_reply(reply.decode())
                    if response != "":
                        print(response)
                        
                ### check that last reply code allows for transmission
                if (int(prevCode) <= 500):
                    dataSocket, addr = dataSocket.accept()
                    reply = ctrSocket.recv(1024)
                    response = check_reply(reply.decode())
                    if (response != ''):
                        print(response)
                    
                    
                    # increment port index
                    portIndex += 1
                    
            except Exception as e:
                print(e)
                print("GET failed, FTP-data port not allocated.")
                
            ### read files retrieved 
            if (int(prevCode) <= 500):
                file = open("retr_files/file"+str(fileCount), "wb")
                ln = dataSocket.recv(2048)
                while(ln):
                    file.write(ln)
                    ln = dataSocket.recv(2048)
                dataSocket.close()
                
                ### increment file counter
                fileCount += 1

    #################### END GET CASE ########################  
        
    
    
    #################### CASE 3 ############################## 
    # evaluate by case: QUIT
    elif (line[:4].upper() == "QUIT"):
        
        # check for extra characters between command and <EOL>
        if (len(line) > 4):
            print("ERROR -- request")
            
        # check for bad sequence
        elif (connected == False):
            print("ERROR -- expecting CONNECT")
            
        # valid line
        else:
            # output success line
            print("QUIT accepted, terminating FTP client")
            ### generate FTP send
            sys.stdout.write("QUIT\r\n")
            ctrSocket.send("QUIT\r\n".encode())
            reply = ctrSocket.recv(1024)
            response = check_reply(reply.decode())
            if (response != ""):
                print(response)
            
            # exit
            exit()
    #################### END QUIT CASE ########################
         
    
    
    
    ################### CASE 4 ################################        
    # evaluate by case:  UNRECOGNIZED COMMAND
    else:
        print("ERROR -- request")
    #################### END UNRECOGNIZED CASE ################
    
####################### END MAIN ##############################       
    

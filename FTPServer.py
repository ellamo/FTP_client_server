# -*- coding: utf-8 -*-
"""
Homework 6 - FTP Server Program : Comp 431 : Molly Moore (moorem24) : PID 730134118

Interoperablitity testing assignment

Changes made:
    1. added "502" error coded for unrecognized commands of lenght 3 or 4
    2. corrected logic of how input lines were parsed

"""



import sys
import os
import shutil
from socket import *

### command line port variable and global control socket
srvPort = int(sys.argv[1])
global ctrSocket
global dataSocket
fileFound = False


#################### socket send function #####################
def sockSend(message):
    global ctrSocket
    sys.stdout.write(message)
    ctrSocket.send(message.encode())
###############################################################
       

### initiate server socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) 
serverSocket.bind(('', srvPort))         
serverSocket.listen(1)                     

while True:
    
    # establish control socket and send welcome response
    ctrSocket, addr = serverSocket.accept()
    sockSend("220 COMP 431 FTP server ready.\r\n")
    
    
    # variables for sequential command verification and use
    userName = ""
    password = ""
    validLogin = False
    prevCMD = ""
    portADR = ""
    host = ""
    port = ""
    retrCount = 1
    fileFound = False
    
    # read input lines from control socket
    line = ctrSocket.recv(1024).decode()
    while(line):   
        # echo line
        sys.stdout.write(line)

        #### fixing command prompt issues
        # strip left leading spaces
        ln = line.lstrip(' ')
        # strip end of line characters
        if (ln[-2:] == "\r\n") or (ln[-2:] == "\n\r"):
            ln = ln[:-2]
        elif (ln[-1:] == "\r") or (ln[-1:] == "\n"):
            ln = ln[:-1]
        # find first space
        sp1 = ln.find(' ')
        # set command and parameter
        if (sp1 < 0):
            command = ln
            param = ""
        else:
            command = ln[:sp1]
            param = ln[sp1:].lstrip(' ')
        # check for bad characters in parameter
        badChar = False
        for char in param:
            if (ord(char) > 127) or (char == '\r') or (char == '\n'):
                badChar = True
        

#        # vars for later use
#        ln = line.lstrip(' ')
#        command = ln[:4].upper()
#        # check end of line for purpose of extracting parameter
#        if (ln[-2:] == "\r\n") or (ln[-2:] == "\n\r"):
#            param = ln[4:-2].lstrip(' ')
#        elif (ln[-1:] == "\r") or (ln[-1:] == "\n"):
#            param = ln[4:-1].lstrip(' ')
#        else:
#            param = ln[4:].lstrip(' ')
#        # check for bad characters in parameter
#        badChar = False
#        for char in param:
#            if (ord(char) > 127) or (char == '\r') or (char == '\n'):
#                badChar = True
    
        
        # EVALUATION BY CASES
        
        # COMMAND CASE:  USER
        if (command == "USER"):
            # check for whitespace following command
            if (ln[4] != " "):
                sockSend("500 Syntax error, command unrecognized.\r\n")
            # check for characters with ascii value > 127 after command and CRLF terminator
            elif (badChar == True) or (param == "") or (line[-2:] != "\r\n"):
                sockSend("501 Syntax error in parameter.\r\n")
            # USER command ok: 
            else:
                # reply line
                sockSend("331 Guest access OK, send password.\r\n")
                # set userName
                userName = param
                # set previous command variable
                prevCMD = command
                
                
        # COMMAND CASE:  PASS
        elif (command == "PASS"):
            # check for whitespace following command
            if (ln[4] != " "):
                sockSend("500 Syntax error, command unrecognized.\r\n")
            # check for characters with ascii value > 127 after command and CRLF terminator
            elif (badChar == True) or (param == "") or (line[-2:] != "\r\n"):
                sockSend("501 Syntax error in parameter.\r\n")
            # check valid USER/PASS sequence
            elif (prevCMD != "USER"):
                sockSend("503 Bad sequence of commands.\r\n")
            # PASS command ok: 
            else:
                # reply line
                sockSend("230 Guest login OK.\r\n")
                # set flag to show valid login sequence executed
                validLogin = True
                # set password
                password = param
                # set previous command variable
                prevCMD = command
                
                
        # COMMAND CASE:  TYPE    
        elif (command == "TYPE"):
            # check for whitespace following command
            if (ln[4] != " "):
                sockSend("500 Syntax error, command unrecognized.\r\n")
            # check for valid typecode, CRLF terminator and no chars between typecode and CRLF
            elif (param[0] not in ["A", "I"]) or (line[-2:] != "\r\n") or (len(param) > 1):
                sockSend("501 Syntax error in parameter.\r\n")
            # check for bad sequence
            elif (prevCMD == "USER"):
                sockSend("503 Bad sequence of commands.\r\n")
            # check for valid login
            elif (validLogin == False):
                sockSend("530 Not logged in.\r\n")
            # TYPE command ok
            else:
                # reply lines
                if (param[0] == "A"):
                    sockSend("200 Type set to A.\r\n")
                else:
                    sockSend("200 Type set to I.\r\n")
                # set previous command variable
                prevCMD = command
               
                    
        # COMMAND CASE:  PORT            
        elif (command == "PORT"):
            # check for whitespace following command
            if (ln[4] != " "):
                sockSend("500 Syntax error, command unrecognized.\r\n")
            # process parameter and check for syntax errors
            else:
                # create list for numbers and check for non-digits and within range
                nums = param.split(',')
                badNum = False
                for num in nums:
                    badChar = False
                    for char in num:
                         if (ord(char) < 48) or (ord(char) > 57):
                             badChar = True
                    if (badChar == False):
                        if (int(num) < 0) or (int(num) > 255):
                            badNum = True
                    else:
                        badNum = True
                # check for bad address or missing CRLF terminator
                if (badNum == True) or (len(nums) != 6) or (line[-2:] != "\r\n"):
                    sockSend("501 Syntax error in parameter.\r\n")
                # check for bad sequence
                elif (prevCMD == "USER"):
                    sockSend("503 Bad sequence of commands.\r\n")
                # check for valid login
                elif (validLogin == False):
                    sockSend("530 Not logged in.\r\n")
                # command ok 
                else:
                    # convert host and port data
                    host = '.'.join(nums[:4:1])
                    port = (int(nums[4]) * 256) + int(nums[5])
                    # update port address variable
                    portADR = str(host) + "," + str(port)
                    # reply line
                    sockSend("200 Port command successful (" + portADR + ").\r\n")
                    # set previous command variable
                    prevCMD = command
    
            
        # COMMAND CASE:  RETR
        elif (command == "RETR"):
            # check for whitespace following command
            if (ln[4] != " "):
                sockSend("500 Syntax error, command unrecognized.\r\n")
            # check for characters with ascii value > 127 after command and CRLF terminator
            elif (badChar == True) or (param == "") or (line[-2:] != "\r\n"):
                sockSend("501 Syntax error in parameter.\r\n")
            # check for bad sequence or no preceding unpaired PORT command
            elif (prevCMD == "USER"):
                sockSend("503 Bad sequence of commands.\r\n")
            # check for valid login
            elif (validLogin == False):
                sockSend("530 Not logged in.\r\n")
            # check for unpaired port
            elif (portADR == ""):
                sockSend("503 Bad sequence of commands.\r\n")
            # command ok
            else:
                # trim leading forward slash or backslash
                if (param[0] == "/") or (param[0] == "\\"):
                    param = param[1:]
                # get absolute file path
                currDir = os.getcwd()
                print(currDir)   #------------------------testing
                src = currDir + os.sep + param
                print(src)    #---------------------------testing
                ### try file transfer
                try:
                    file = open(src, "rb")
                    sockSend("150 File status okay.\r\n")
                    fileFound = True
                    ### send data through data socket
                    try:
                        dataSocket = socket(AF_INET, SOCK_STREAM)
                        dataSocket.connect((host, int(port)))
                    except Exception as e:
                        #print(e)
                        sockSend("425 Can not open data connection.")
                    # nulify port address
                    portADR = ""
                    # increment counter
                    retrCount += 1
                    # set previous command variable
                    prevCMD = command
                except Exception as e:
                    #print(e)
                    sockSend("550 File not found or access denied.\r\n")
                    
                    
                ### send file through data socket
                if(fileFound):
                    ln = file.read(2048)
                    while (ln):
                        dataSocket.send(ln)
                        ln = file.read(2048)
                    file.close()
                    dataSocket.close()
                    
                    sockSend("250 Requested file action completed.\r\n")
                    
                ### reset fileFound flag to false
                fileFound = False
                                           
                
            
        # COMMAND CASE:  NOOP
        elif (command == "NOOP"):
            # check for valid CRLF terminator and no chars between command and CRLF
            if (line[-2:] != "\r\n") or (len(ln) > 6):
                sockSend("501 Syntax error in parameter.\r\n")
            # check for bad sequence
            elif (prevCMD == "USER"):
                sockSend("503 Bad sequence of commands.\r\n")
            # check for valid login
            elif (validLogin == False):
                sockSend("530 Not logged in.\r\n")
            # command ok
            else:
                sockSend("200 Command OK.\r\n")
                # set previous command variable
                prevCMD = command
                
                
        # COMMAND CASE:  SYST
        elif (command == "SYST"):
            # check for valid CRLF terminator and no chars between command and CRLF
            if (line[-2:] != "\r\n") or (len(ln) > 6):
                sockSend("501 Syntax error in parameter.\r\n")
            # check for bad sequence
            elif (prevCMD == "USER"):
                sockSend("503 Bad sequence of commands.\r\n")
            # check for valid login
            elif (validLogin == False):
                sockSend("530 Not logged in.\r\n")
            
            # command ok
            else:
                sockSend("215 UNIX Type: L8.\r\n")
                # set previous command variable
                prevCMD = command
                
                
        # COMMAND CASE:  QUIT        
        elif (command == "QUIT"):
            # check for valid CRLF terminator and no chars between command and CRLF
            if (line[-2:] != "\r\n") or (len(ln) > 6):
                sockSend("501 Syntax error in parameter.\r\n")
            ### Command ok --- this reply is new to HWK 5
            else:
                sockSend("221 Goodbye.\r\n")
                
            
        # COMMAND CASE:  UNRECOGNIZED 
        else:
            if ( (len(command) == 3) or (len(command) == 4) ):
                if (command != "OPTS"):
                    sockSend("502 Command not implemented.\r\n")
            else:
                sockSend("500 Syntax error, command unrecognized.\r\n")
            
            
        
            
        ### retrieve next line from control socket
        line = ctrSocket.recv(1024).decode()
        
        
        
        


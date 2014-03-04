#!/usr/bin/python

#This script performs the following tasks:
#1. scans through a directory provided
#2. identifies the relevant log files
#3. unzips any zipped files
#4. searches for entries that match a list
#5. log any matches to a CSV results file

#Functionality Note - Current version logs to a Results csv file, integration to SQLite is still being worked on as well as breaking up the log file hits into separate result files / tables
#Additional log entry types will be added in the future
#Currently does a check to ensure there are logs named "system.log" in the log directory
#Only works on OS X "darwin"

#Copyright Mike Dadouche- 2014


#Import the necessary libraries

import os
import re
import sqlite3 #Will be implemented in the future
import time
import datetime
import gzip
import sys
import logging
import csv
import socket


#Global Variables, These are used throughout the script

#Initiate empty globals that will be changed in the script
dirToScan = ''
fileOpened = ''


#Regular Expressions for Key Log Entries - To expand, add a regular expression variable and add it to the keywordList list

#Time Machine Backups
timeMachineBackup = "com\.apple\.backupd\[\d+\]\:\sMounted\snetwork\sdestination\sat\smount\spoint\:\s\/Volumes\/Time\sMachine"
timeMachineFilesToBackup = "com\.apple\.backupd\[\d+\].+Found\s\d+\sfiles\s\("

#USB Devices
usbDeviceConnected = "kernel\[\d+\]\:\sUSBMSC\sIdentifier\s"

#Sudo Usage
sudoCmdUsage = "sudo\[\d+\].+TTY\=.+PWD\=.+USER\=.+COMMAND\="

#Startup and Shutdown Times
systemStartTime = "localhost\sbootlog\[\d+\]\s\<Notice\>\:\sBOOT\_TIME"
systemShutdownTime = "shutdown\[\d+\]\s\<Notice\>\:\sSHUTDOWN\_TIME\:"

#Google Drive Artifacts
googleDriveExtension = "Finder\[\d+\].+Loading\sGoogle\sDrive\sFinder\sextension"

#User Login
userLogin = "SecurityAgent\[\d+\].+Login\sWindow\slogin\sproceeding"

#List of all keywords
keywordList = [timeMachineBackup,timeMachineFilesToBackup,usbDeviceConnected,sudoCmdUsage,systemStartTime,systemShutdownTime,userLogin,googleDriveExtension]





#Function Definitions

#Validate we are on OS X
def validateSys():
    if sys.platform == "darwin":
        print("System is OS X, continuting")
    else:
        print("System is not OS X, The script only works on OS X, exiting")
        sys.exit()


#Function to get the user input and validate that the directory exists
def getDirToProc():
    #Get the Input
    dirToProc = raw_input("Please Enter a Log Directory to Scan: ")
    #Validate the dir is real
    if os.path.isdir(dirToProc):
        return dirToProc
    else:
        print("Not a Valid Directory, Please Ruh the Script with a Valid Directory")
        sys.exit()



#Function to search the line and print the entries found
def searchLine(file,rKeyword,writer):
    systemHostName = (socket.gethostname())
    try:
        #For loop to interate through lines of the log file
        for line in file:
            if re.search(rKeyword,line):
                #set the regular expression groups for the log file line
                matchObject = re.match(r"^([A-Z][a-z][a-z]\s\d+\s\d+\:\d+\:\d+)(.+\[\d+\])\:(.+)$",line)
                #Write the results to a CSV file by match group
                if matchObject:
                    writer.writerow( (matchObject.group(1),systemHostName,fileOpened,matchObject.group(2),matchObject.group(3)) )
                #writer.writerow((matchObject.group(1),fileOpened,matchObject.group(2),matchObject.group(3)))
                else:
                    pass
    #If we run into an error, print it out in reference to the log file being searched
    except:
        logging.exception("Error Searching file: " + fileOpened)



#Function to search the files in a directory for a specific log type, and if found call the searchLine function for that file
def searchFileForKeyword(logFile,rKeyword,writer):
    #Throw this into a try/except to catch any errors
    try:
        #Open the log file to search
        #If the file is gzipped, use the zip library to access it.
        if logFile.lower().endswith(".gz"):
            with gzip.open(logFile) as file:
                searchLine(file,rKeyword,writer)
        #Otherwise we have regular file
        else:
            with open(logFile) as file:
            #For each file, search for the keyword
                searchLine(file,rKeyword,writer)
        #outFile.write(matchString)
        #Close the files
        file.close()
    #If we run into an error, print it out
    except:
        logging.exception("Error processing file: ")


#Function to find the system log files and if needed, unzip them and pass them to the search function
def processLogFiles():
    #Global Variables Getting Changed
    global fileOpened
    #Set the string for the system log, these are the files we are going to search
    systemLogFile = "system\.log"
    #Lets try to do some searching in the files we want
    try:
        #Open the output File
        #Get Current DateTimeStampt
        ts = time.time()
        timeStampNow = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H%M%S')
        #Open the output file for writing
        outFileName = (timeStampNow+"_Results.csv")
        outFile = open(outFileName,'wb')
        #initiate the CSV writer
        writer = csv.writer(outFile)
        #Write the headers
        writer.writerow(("Time Stamp","Hostname","Log File","System and Service","Log Message"))
        #Walk the directory given to us at the prompt
        for root,dirs,files in os.walk(dirToScan):
            #For each file
            for file in files:
                #Set the full path file name
                fileName = os.path.join(root,file)
                #If the file name contains our string
                if re.search(systemLogFile,file):
                    #For each keyword we have in our list, lets run a search on the file itself
                    fileOpened = fileName
                    for keyword in keywordList:
                        searchFileForKeyword(fileName,keyword,writer)
        #Close the outfile
        outFile.close()
    #If we run into an error, print it out
    except:
        logging.exception("Error processing directory of log files: ")



#Main Function
def main():
    #Global Variables Getting Changed
    global dirToScan
    
    #Validate the system
    validateSys()
    #Set the directory to process
    dirToScan = getDirToProc()
    #Process the Files in the Directory
    processLogFiles()


#If main, then main
if __name__ == "__main__":
    main()



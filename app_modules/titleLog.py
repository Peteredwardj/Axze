import sys
from sys import platform
import os
import ctypes



running,transactionSuccess,transactionFailed,submittedTransactions,pending = 0,0,0,0,0

class classUpdateTitle():
    def __init__(self,mode):
        self.mode=mode
    
    def addRun(self):
        global running
        running+=1
        self.updateTitle()
    
    def addSubmitted(self):
        global submittedTransactions
        submittedTransactions+=1
        self.updateTitle()
    
    def addPending(self):
        global pending
        pending+=1
        self.updateTitle()
    
    def addSuccess(self):
        global transactionSuccess,submittedTransactions,running
        submittedTransactions=submittedTransactions-1
        if (submittedTransactions<0):
            submittedTransactions=0
        running=running-1
        if (running<0):
            running=0
        transactionSuccess+=1
        self.updateTitle()
    
    def addFail(self):
        global transactionFailed
        transactionFailed+=1
        self.updateTitle() 
        
    
    def updateTitle(self):
        try:
            if (self.mode=="Mint"): 
                if platform == "darwin":
                    sys.stdout.write("\x1b]2;{} | Running Tasks : {} | Submitted Transactions : {}| Pending Transactions : {}| Successful : {} | Failed : {}\x07".format(self.mode,running,submittedTransactions,pending,transactionSuccess,transactionFailed))
                else:
                    ctypes.windll.kernel32.SetConsoleTitleW("{} | Running Tasks : {} | Submitted Transactions : {}| Pending Transactions : {}| Successful : {} | Failed : {}\x07".format(self.mode,running,submittedTransactions,pending,transactionSuccess,transactionFailed))
            elif ("Discord" in self.mode or "Premint" in self.mode):
                if platform == "darwin":
                    sys.stdout.write("\x1b]2;{} | Running Tasks : {} | Successful : {}| Failed : {}\x07".format(self.mode,running,transactionSuccess,transactionFailed))
                else:
                    ctypes.windll.kernel32.SetConsoleTitleW("{} | Running Tasks : {} | Successful : {}| Failed : {}\x07".format(self.mode,running,transactionSuccess,transactionFailed))
        except:
            pass
from web3 import Web3
from app_modules.taskLogger import taskLogger
from app_modules.apiModules import checkNode
from app_modules.titleLog import classUpdateTitle
import time

updateTitleCall=classUpdateTitle("ETH consolidation")
transactionCounterETH = 0 
printedDisplayETH = False
taskDictETH = {} 
continueTransferETH = "noInput"


class consolidateETH():
    def __init__(self,walletAddress,walletKey,destAddress,minimumBalance,maxGasFee,maxPriorityFee,taskId):
        self.contract = None
        self.walletAddress = Web3.toChecksumAddress(walletAddress)
        self.walletKey = walletKey
        self.maxGasFee = maxGasFee
        self.maxPriorityFee = maxPriorityFee
        self.taskId = taskId
        self.maxGasUsed = str(self.maxGasFee) + "," + str(self.maxPriorityFee)
        self.cancel=False
        self.updated=0
        self.current = 0
        self.nonce = 0
        self.profileName = taskId
        self.minimumBalance = minimumBalance
        self.destAddress = Web3.toChecksumAddress(destAddress)

    def checkBalance(self):
        currBalance = web3Connection.eth.get_balance(Web3.toChecksumAddress(self.walletAddress))
        if (currBalance<=0):
            return False
        amount = web3Connection.fromWei(currBalance- web3Connection.toWei(self.maxGasFee,'gwei')*21000,'ether')
        if (amount>self.minimumBalance):
            #taskLogger({"status" : "process","message":"wallet has minimum balance [{}E]".format(amount),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return True
        else:
            return False
    
    def order(self):
        global web3Connection,taskDictETH
        taskDictETH[self.walletAddress] = 'pending'
        try:
            web3Connection = Web3(Web3.HTTPProvider(checkNode()))
        except Exception as e:
            taskLogger({"status" : "error","message":"Check if you have correctly set up your node in settings! - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            time.sleep(10000)
        minimumBalanceFulfilled = self.checkBalance()
        taskDictETH[self.walletAddress] = 'completed'
        if (minimumBalanceFulfilled == False):
            return
        continueModule = self.planTransactions()
        updateTitleCall.addRun()
        if (continueModule == False):
            taskLogger({"status" : "error","message":"Rejected transaction, killed","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return
        self.transfer()
        

    
    def planTransactions(self):
        global continueTransferETH,printedDisplayETH,taskDictETH,transactionCounterETH
        transactionCounterETH += 1
        if (printedDisplayETH == False):
            printedDisplayETH = True
            while True:
                if (len(list(set(list(taskDictETH.values())))) ==1): #wait until all tasks have been calculated
                    break
            taskLogger({"status" : "process","message":"Found {} wallet(s) meeting the {}E minimum requirement".format(transactionCounterETH,self.minimumBalance),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"ETH Consolidation Task")
            taskLogger({"status" : "warn","message":"Number of transactions to carry out is : {} transaction(s)".format(transactionCounterETH),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"ETH Consolidation Task")
            continueTransferETH = input('Would you like to proceed? [y/n]: ')
            if (continueTransferETH.lower() == "y"):
                continueTransferETH = True
            else:
                continueTransferETH = False
        else:
            while (True):
                if (continueTransferETH != "noInput"):
                    break
        
        return continueTransferETH
    
    def getNonce(self):
        taskLogger({"status" : "process","message":"Fetching Nonce","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        try:
            return web3Connection.eth.get_transaction_count(self.walletAddress)
        except Exception as e:
            print(e)
            time.sleep(1)
            self.getNonce()

    def transfer(self):
        destAddress = self.destAddress
        maxGasFee = self.maxGasFee
        maxPriorityFee = self.maxPriorityFee
        amount = web3Connection.fromWei(web3Connection.eth.get_balance(Web3.toChecksumAddress(self.walletAddress)) - web3Connection.toWei(maxGasFee,'gwei')*21000,'ether')
        taskLogger({"status" : "process","message":"Calculated max Eth transfer :{}E".format(amount),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)

        body = {
            'nonce' : self.getNonce(),
            'to' : destAddress,
            'value' : web3Connection.toWei(amount,'ether'),
            'gas' : 21000,
            'maxFeePerGas': web3Connection.toWei(maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(maxPriorityFee,'gwei'),
            'chainId':1
        }
        try:
            taskLogger({"status" : "warn","message":"Signing Transaction","prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
            signedTransaction = web3Connection.eth.account.sign_transaction(body,self.walletKey)
            taskLogger({"status" : "process","message":"Submitting Transaction [{} ETH -> {}]".format(amount,destAddress),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
            result = web3Connection.eth.send_raw_transaction(signedTransaction.rawTransaction)
            statusTrack = web3Connection.eth.wait_for_transaction_receipt(result,timeout=300)
            if (statusTrack['status']==1): #successful transfer 
                taskLogger({"status" : "success","message":"Succesful Transaction [{} ETH -> {}]".format(amount,destAddress),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
                updateTitleCall.addSuccess()
                return True
            else: 
                taskLogger({"status" : "error","message":"Failed Transaction [{} ETH -> {}]".format(amount,destAddress),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
                updateTitleCall.addFail()
                return False
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed Transaction [{} ETH -> {}] - {}".format(amount,destAddress,str(e)),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
            updateTitleCall.addFail()
            return False



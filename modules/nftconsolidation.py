import os,json,time,requests
from web3 import Web3
from app_modules.taskLogger import taskLogger
from app_modules.apiModules import etherScanApi,checkNode,alchemyK
from app_modules.titleLog import classUpdateTitle
from app_modules.hoardDat import batchTransferABI


global web3Connection
etherScanApi = 'RITWHK4P371RN5G4PY1WGMNT3XQ32M9BVU'
batchTransferContract = "0xF849de01B080aDC3A814FaBE1E2087475cF2E354"
updateTitleCall=classUpdateTitle("NFT consolidation")
cachedContracts = {}
cachedContractProperty = {}
cachedFlip = {}
submittingArr = []
fetchedTokens = None
firstScrape = True
printedDisplay = False
transactionCounter = 0
tokenCounter = 0
continueTransfer = "noInput"
taskDict = {} #{'wallet1':'pending','wallet2':'pending'}

class consolidateNFT():
    def __init__(self,walletAddress,walletKey,contractAddress,destAddress,maxGasFee,maxPriorityFee,taskId):
        self.contract = None
        self.contractAddress = contractAddress
        self.contractAbi = None
        self.walletAddress = Web3.toChecksumAddress(walletAddress)
        self.walletKey = walletKey
        self.maxGasFee = maxGasFee
        self.maxPriorityFee = maxPriorityFee
        self.taskId = taskId
        self.strAddress = contractAddress
        self.maxGasUsed = str(self.maxGasFee) + "," + str(self.maxPriorityFee)
        self.cancel=False
        self.updated=0
        self.current = 0
        self.nonce = 0
        self.minted=False
        self.imageUrl = None
        self.mintName = "Token"
        self.profileName = taskId
        self.osLink = "https://opensea.io/collection/"
        self.proof = None
        self.inputStuct = None
        self.special = False
        self.mintFunction = None
        self.transferContract = None
        self.tokenArrs = []
        self.destAddress = Web3.toChecksumAddress(destAddress)

    def fetchTokens(self):
        global fetchedTokens,firstScrape
        if (firstScrape):
            firstScrape = False
            endpoint = "https://eth-mainnet.g.alchemy.com/nft/v2/{}/getOwnersForCollection?contractAddress={}&withTokenBalances=true".format(alchemyK,self.contractAddress)
            while True:
                taskLogger({"status" : "process","message":"Fetching Tokens","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"NFT Consolidation Task")
                try:
                   headers = {"accept": "application/json"}
                   response = requests.get(endpoint, headers=headers)
                   if (response.status_code == 200):
                       responseJson = json.loads(response.text)
                       fetchedTokens = responseJson['ownerAddresses']
                       taskLogger({"status" : "success","message":"Fetched tokens","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"NFT Consolidation Task")
                       taskLogger({"status" : "warn","message":"Module will exit if no tokens found for wallets!","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"NFT Consolidation Task")
                       return                
                except Exception as e:
                    taskLogger({"status" : "error","message":"Failed fetching tokens - {}".format(str(e)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)

        else:
            while (True):
                if (fetchedTokens!=None):
                    break
       

    def fetchProperties(self):
        while True:
            try:
                taskLogger({"status" : "process","message":"Fetching contract properties","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"NFT Consolidation Task")
                response = requests.get("https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}".format(self.contractAddress,etherScanApi),timeout=5)
                if (response.status_code == 200):
                    return (json.loads(response.text)['result'])
                else:
                    taskLogger({"status" : "error","message":"Failed to fetch contract properties - {}".format(response.status_code),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"NFT Consolidation Task")
                    time.sleep(2)
                    
            except Exception as e: 
                taskLogger({"status" : "error","message":"Failed to fetch contract properties - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"NFT Consolidation Task")
                time.sleep(2)
    
    def generateStructure(self):
        for obj in fetchedTokens:
            if (obj['ownerAddress'].lower() == self.walletAddress.lower()):
                tokenObjArr = obj['tokenBalances']
                for tokenObj in tokenObjArr:
                    tokenHex = tokenObj['tokenId']
                    tokenId = int(tokenHex[-4:],16)
                    self.tokenArrs.append(tokenId)
                return True #found
        return False #not found
    
    
    def order(self):
        global web3Connection,taskDict
        taskDict[self.walletAddress] = 'pending'
        try:
            web3Connection = Web3(Web3.HTTPProvider(checkNode()))
        except Exception as e:
            taskLogger({"status" : "error","message":"Check if you have correctly set up your node in settings! - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            time.sleep(10000)
        self.connect()
        self.fetchTokens()
        foundTokens = self.generateStructure()
        taskDict[self.walletAddress] = 'completed'
        if (foundTokens == False):
            return
        
        continueModule = self.planTransactions()
        updateTitleCall.addRun()
        if (continueModule == False):
            taskLogger({"status" : "error","message":"Rejected transaction, killed","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return
        self.transferTokens()

    def connect(self):
        global cachedContracts
        first = False
        try:
            self.contractAddress = Web3.toChecksumAddress(self.contractAddress)
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed initializing contract- {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        
        if (self.contractAddress not in cachedContracts):
            cachedContracts[self.contractAddress] = None
            contractAbi = self.fetchProperties()
            cachedContracts[self.contractAddress] = contractAbi
            self.contractAbi = cachedContracts[self.contractAddress]
        else:
            while (cachedContracts[self.contractAddress] == None):
                if (not first):
                    first = True
                
            self.contractAbi = cachedContracts[self.contractAddress] 

        self.contract = web3Connection.eth.contract(address = self.contractAddress, abi = self.contractAbi)
        self.transferContract = web3Connection.eth.contract(address = batchTransferContract, abi = batchTransferABI)
    
    def planTransactions(self):
        global transactionCounter,tokenCounter,continueTransfer,printedDisplay,taskDict
        noOfTokens = len(self.tokenArrs)
        if (noOfTokens == 1):
            transactionCounter += 1  #1 token only = invoke safeTransferFrom
        else: #>1 tokens
            transactionCounter += 2  #>1 token = set approval for all + batchTransfer
        
        tokenCounter+=noOfTokens
        if (printedDisplay == False):
            printedDisplay = True
            while True:
                if (len(list(set(list(taskDict.values())))) ==1): #wait until all tasks have been calculated
                    break
            taskLogger({"status" : "process","message":"Found total number of {} tokens to transfer to : {}".format(tokenCounter,self.destAddress),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"NFT Consolidation Task")
            taskLogger({"status" : "warn","message":"Maximum number of transactions to transfer {} token(s) is : {} transactions".format(tokenCounter,transactionCounter),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},"NFT Consolidation Task")
            continueTransfer = input('Would you like to proceed? [y/n]: ')
            if (continueTransfer.lower() == "y"):
                continueTransfer = True
            else:
                continueTransfer = False
        else:
            while (True):
                if (continueTransfer != "noInput"):
                    break
        
        return continueTransfer
    
    def transferTokens(self):
        noOfTokens = len(self.tokenArrs)
        body = {
            'from' : self.walletAddress,
            'nonce' : self.getNonce(),
            'value' : web3Connection.toWei(0,'ether'),
            'maxFeePerGas': web3Connection.toWei(self.maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(self.maxPriorityFee,'gwei'),
            'chainId' : 1 #change to 1 for main net
        }
        successTxn = False
        try:
            if (noOfTokens == 1):
                contractCall = self.contract.functions['safeTransferFrom'](self.walletAddress,self.destAddress,self.tokenArrs[0]).buildTransaction(body)
            else: #>1 tokens
                tupleObj = []
                for token in self.tokenArrs:
                    tupleObj.append([self.contractAddress,token])
                isApproved = self.contract.functions['isApprovedForAll'](self.walletAddress,batchTransferContract).call()
                if (isApproved == False):
                    taskLogger({"status" : "process","message":"Not yet approved transfer contract, building approval transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    contractCall = self.contract.functions['setApprovalForAll'](Web3.toChecksumAddress(batchTransferContract),True).buildTransaction(body) #approval to use our contract
                    successTxn = self.sendTxn(contractCall,"setApprovalForAll transaction")
                else:
                    successTxn = True
                if (successTxn):
                    taskLogger({"status" : "process","message":"Transfer contract is already approved, building transfer transaction!","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    body['nonce'] = self.getNonce()
                    contractCall = self.transferContract.functions['transferBatch'](tupleObj,self.destAddress).buildTransaction(body)
                else:
                    taskLogger({"status" : "error","message":"Error setApprovalForAll transaction, killing task","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    
        except Exception as e:
            taskLogger({"status" : "error","message":"Error estimating transaction - {}".format(str(e)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return False

        self.sendTxn(contractCall,"transfer transaction of {} token(s)".format(noOfTokens))
    
    def getNonce(self):
        taskLogger({"status" : "process","message":"Fetching Nonce","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        try:
            return web3Connection.eth.get_transaction_count(self.walletAddress)
        except Exception as e:
            print(e)
            time.sleep(1)
            self.getNonce()

    def sendTxn(self,contractCall,transactionMessage):        
        try:
            taskLogger({"status" : "warn","message":"Signing Transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            signedTransaction = web3Connection.eth.account.sign_transaction(contractCall,self.walletKey)
            taskLogger({"status" : "process","message":"Submitting Transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            result = web3Connection.eth.send_raw_transaction(signedTransaction.rawTransaction)
            updateTitleCall.addPending()
            taskLogger({"status" : "warn","message":"Pending - {}".format(self.getNonce()),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            statusTrack = web3Connection.eth.wait_for_transaction_receipt(result,timeout=300)
            if (statusTrack['status']==1): #successful transfer 
                taskLogger({"status" : "success","message":"Successful {}".format(transactionMessage),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                return True
            else: 
                taskLogger({"status" : "error","message":"Failed Transaction, check etherscan","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                updateTitleCall.addFail()
                return False
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed Transaction - {}".format(str(e)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            updateTitleCall.addFail()
            return False
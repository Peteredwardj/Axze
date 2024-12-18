import json,time,requests,cloudscraper
from pandas import reset_option
from web3 import Web3
from app_modules.taskLogger import taskLogger
from app_modules.discordLog import webhookLog
from app_modules.apiModules import etherScanApi,checkNode
from app_modules.titleLog import classUpdateTitle
from app_modules.hoardDat import hoardABI,randABI
from bs4 import BeautifulSoup


global web3Connection
etherScanApi = 'RITWHK4P371RN5G4PY1WGMNT3XQ32M9BVU'
hoardContract = '0x1D4F2182475bb9985BfE7a756f5B2e003e0Bc4d5'
updateTitleCall=classUpdateTitle("Hoard")
cachedContracts = {}
cachedContractProperty = {}
cachedFlip = {}
submittingArr = []

class hoard():
    def __init__(self,amount,quantity,walletAddress,walletKey,contractAddress,mintFunc,maxGasFee,maxPriorityFee,gasMode,iterations,mode,retryBool=False):
        self.amount = amount
        self.quantity = quantity
        self.contract = None
        
        try:
            self.contractAddress = Web3.toChecksumAddress(contractAddress)
            self.walletAddress = Web3.toChecksumAddress(walletAddress)
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed initializing contract/wallet, check contract/wallet input - {}".format(str(e)),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},"Hoard Wallet")
        self.contractAbi = None
        self.walletKey = walletKey
        self.maxGasFee = maxGasFee
        self.maxPriorityFee = maxPriorityFee
        self.mintFunctionCall =mintFunc
        self.taskId = "Hoard Wallet"
        self.strAddress = contractAddress
        self.gasMode = gasMode
        self.maxGasUsed = str(self.maxGasFee) + "," + str(self.maxPriorityFee)
        self.cancel=False
        self.updated=0
        self.current = 0
        self.nonce = 0
        self.minted=False
        self.imageUrl = None
        self.mintName = "{} Tokens".format(quantity*iterations)
        self.profileName = walletAddress
        self.osLink = "https://opensea.io/collection/"
        self.proof = None
        self.inputStuct = None
        self.special = False
        self.mintFunction = None
        self.totalTxnAmount = amount*iterations
        self.iterations = int(iterations)
        self.hoardContract = None
        self.mode = mode
        self.needToTransfer = False
        self.retryBool = retryBool
        self.mintArgs = None

        


    def contractPropertyScrape(self):
        try:
            endpoint = "https://api.opensea.io/api/v1/asset_contract/{}".format(self.contractAddress)
            headers = {"X-API-KEY": "a4dc98c6cd5b429a8a9ba947c4aceb91"}
            response = requests.get(endpoint, headers=headers)
            responseJson = json.loads(response.text)
            self.mintName = responseJson['collection']['name']
            self.imageUrl = responseJson['image_url']
            self.osLink = "https://opensea.io/collection/"+responseJson['collection']['slug']
        except Exception as e:
            taskLogger({"status":"warn", "message": "Failed to retrieve collection data - {}".format(str(e)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            cachedContractProperty[self.contractAddress] = {"mintName": self.mintName,"imageUrl":self.imageUrl,"osLink":self.osLink}

    def fetchProperties(self):
        while True:
            try:
                taskLogger({"status" : "process","message":"Fetching contract properties","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                response = requests.get("https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}".format(self.contractAddress,etherScanApi),timeout=5)
                if (response.status_code == 200):
                    return (json.loads(response.text)['result'])
                else:
                    taskLogger({"status" : "error","message":"Failed to fetch contract properties - {}".format(response.status_code),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    time.sleep(2)
                    
            except Exception as e: 
                taskLogger({"status" : "error","message":"Failed to fetch contract properties - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                time.sleep(2)
    

    def order(self):
        global web3Connection

        try:
            web3Connection = Web3(Web3.HTTPProvider(checkNode()))
        except Exception as e:
            taskLogger({"status" : "error","message":"Check if you have correctly set up your node in settings! - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            time.sleep(10000)

        self.loadContract()

        if (self.mode == "add"): #add helper 
            self.addHelper()
        
        elif (self.mode == "check"):
            self.checkHelper()

        elif (self.mode == "mint"): #execute exploit 
            self.connect()
            self.mint()
        
        elif (self.mode == "withdrawNFT"):
            self.contractAddress = Web3.toChecksumAddress(self.contractAddress)
            self.withdrawNFT()
        
        elif (self.mode == "withdrawFunds"):
            self.withdrawFunds()

    def loadContract(self):
        self.hoardContract = web3Connection.eth.contract(address = hoardContract, abi = hoardABI)
    
    def checkHelper(self):
        lengthResponse = len(self.hoardContract.functions['getHelpers'](self.walletAddress).call())
        taskLogger({"status" : "process","message":"Found {} hoarders for {}".format(lengthResponse,self.walletAddress),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
    
    def withdrawFunds(self):
        body = {
            'from' : self.walletAddress,
            'nonce' : self.getNonce(),
            'value' : web3Connection.toWei(0,'ether'),
            'maxFeePerGas': web3Connection.toWei(self.maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(self.maxPriorityFee,'gwei'),
            'chainId' : 1 #change to 1 for main net
        }

        try:
            contractCall = self.hoardContract.functions['recoverFundsFromChilds']().buildTransaction(body)
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed to generate hoarders - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return False
        
        totalEstimatedGas = str(contractCall['gas']*self.maxGasFee*10**-9)[:6]
        taskLogger({"status" : "warn","message":"Estimated maximum spending cost to withdraw all funds from all hoarders is : {}E".format(totalEstimatedGas),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        continueTxn = input("Would you like to continue withdrawing funds from hoarders? [y/n] : ")
        self.sendTxn(continueTxn,contractCall)


    def generateWithdrawDat(self):
        tupleDict = {}
        tupleDat = []
        transactionURL = input("Please input Etherscan URL of the Mint transaction : ")
        session = cloudscraper.create_scraper(
                browser={
                            'browser': 'firefox',
                            'platform': 'windows',
                            'mobile': False
                }
            )
        while True:
            try:
                #print("fetching txn")
                response = session.get(transactionURL)
                if (response.status_code == 200): 
                    responseText = response.text
                    soup = BeautifulSoup(responseText,'html.parser')
                    tokenList = soup.find_all("span",{"class": "hash-tag text-truncate tooltip-address"}) #get all the tokens
                    addressList = soup.find_all("span",{"class":"hash-tag text-truncate hash-tag-custom-to-721 tooltip-address"}) #get all the address transfer
                    for i in range (0,len(tokenList)):
                        token = int(tokenList[i].text)
                        addressowner = addressList[i].text
                        addressowner = Web3.toChecksumAddress(addressowner)
                        if (addressowner not in tupleDict):
                            tupleDict[addressowner] = [token]
                        else:
                            tupleDict[addressowner].append(token)
                    break
                else:
                    print("failed fetching txn info - {}".format(response.status_code))
                    time.sleep(3)
            except Exception as e:
                print("Failed fetching txn info - {}".format(str(e)))
                time.sleep(3)
        for tuple in tupleDict: #format it in array of an array 
            tupleDat.append([tuple,tupleDict[tuple]])
        withdrawDat = json.dumps(tupleDat) #format it properly
        return withdrawDat 


    def withdrawNFT(self):
        tokenArr = []
        withdrawDat = self.generateWithdrawDat()
        withdrawJson = json.loads(withdrawDat)
        firstToken = withdrawJson[0][1][0]
        lastToken = withdrawJson[-1][1][-1]
        taskLogger({"status" : "warn","message":"Found token ID of {} - {} for this transaction".format(firstToken,lastToken),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        body = {
            'from' : self.walletAddress,
            'nonce' : self.getNonce(),
            'value' : web3Connection.toWei(0,'ether'),
            'maxFeePerGas': web3Connection.toWei(self.maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(self.maxPriorityFee,'gwei'),
            'chainId' : 1 #change to 1 for main net
        }
        try:
            tempArr = withdrawJson[:]
            while True:
                taskLogger({"status" : "warn","message":"Generating best transaction with lowest gas cost","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                contractCall = self.hoardContract.functions['withdrawNFTsFromChilds'](self.contractAddress,tempArr).buildTransaction(body)
                if (contractCall['gas'] >= 30000000 ): 
                    for _ in range (10):
                        tempArr.pop()
                else:
                    '''splitIDX = len(tempArr)
                    if (splitIDX == len(withdrawJson)):
                        txnList = [tempArr]
                    else:'''
                    splitIDX = len(tempArr)
                    txnList = list(self.splitter(withdrawJson,splitIDX))
                    taskLogger({"status" : "success","message":"Found optimum transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    break

        except Exception as e:
            taskLogger({"status" : "error","message":"Failed to withdraw NFTs from hoarders - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return False
        
        contractCallArr = []
        gasEstArr = []
        totalEstimatedGas = 0

        for i in range (0,len(txnList)):
            try:
                body['nonce'] = self.getNonce() + i
                contractCallArr.append(self.hoardContract.functions['withdrawNFTsFromChilds'](self.contractAddress,txnList[i]).buildTransaction(body))
                estGas = contractCallArr[i]['gas']*self.maxGasFee*10**-9
                gasEstArr.append(estGas)
                totalEstimatedGas = totalEstimatedGas + estGas
            except Exception as e:
                taskLogger({"status" : "error","message":"Error estimating gas for withdraw - {}".format(str(e)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)

        taskLogger({"status" : "warn","message":"Estimated maximum spending to withdraw {} tokens is : {}E".format(len(tokenArr),str(totalEstimatedGas)[:6]),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        txnListString = ''
        for i in range (0,len(txnList)):
            txnListString = txnListString + "Transaction {} : {} tokens [{}E]\n".format(i+1,len(txnList[i]),str(gasEstArr[i])[:6])
        print("Generated optimum transactions:\n{}".format(txnListString[:-1]))
        continueTxn = input("Would you like to continue withdrawing ({}E maximum spending)? [y/n] : ".format(str(totalEstimatedGas)[:6]))

        for i in range (0,len(contractCallArr)):
            self.sendTxn(continueTxn,contractCallArr[i],len(txnList[i]))

    def splitter(self,tokenArr,splitIDX):
        for i in range(0,len(tokenArr),splitIDX):
            yield tokenArr[i:i + splitIDX]
      
    
    def addHelper(self):
        body = {
            'from' : self.walletAddress,
            'nonce' : self.getNonce(),
            'value' : web3Connection.toWei(0,'ether'),
            'maxFeePerGas': web3Connection.toWei(self.maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(self.maxPriorityFee,'gwei'),
            'chainId' : 1 #change to 1 for main net
        }
        try:
            self.checkHelper()
            contractCall = self.hoardContract.functions['createHelpers'](self.iterations).buildTransaction(body)
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed to generate hoarders - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return False
        
        totalEstimatedGas = str(contractCall['gas']*self.maxGasFee*10**-9)[:6]
        taskLogger({"status" : "warn","message":"Estimated maximum spending cost to generate {} hoarders is : {}E".format(self.iterations,totalEstimatedGas),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        continueTxn = input("Would you like to continue generating {} hoarders? [y/n] : ".format(self.iterations))
        self.sendTxn(continueTxn,contractCall)
        
    def getNonce(self):
        taskLogger({"status" : "process","message":"Fetching Nonce","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        try:
            return web3Connection.eth.get_transaction_count(self.walletAddress)
        except Exception as e:
            print(e)
            time.sleep(1)
            self.getNonce()

    def connect(self):
        global cachedContracts
        updateTitleCall.addRun()
        taskLogger({"status":"process","message":"Starting Task","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        try:
            self.contractAddress = Web3.toChecksumAddress(self.contractAddress)
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed initializing Mint contract- {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        
        self.contractAbi = self.fetchProperties()         #self.contractAbi = randABI
        #self.contractAbi = randABI
        try:
            self.contract = web3Connection.eth.contract(address = self.contractAddress, abi = self.contractAbi)
        except:
            taskLogger({"status" : "error","message":"Failed to load Mint contract ABI [Initialization]","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            time.sleep(3600)
        self.mintFunctionCall = self.functionLogicScrape()
        taskLogger({"status" : "success","message":"Initialized Mint contract - {}".format(self.mintFunctionCall),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)

    def functionLogicScrape(self): #Seach for a possible function here 
        functionNameDict={}
        try:
            contractWorker = json.loads(self.contractAbi)
        except :
            taskLogger({"status" : "error","message":"Failed to load Mint contract ABI","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        negative = ['presale','whitelist','owner','admin','allow','owner','dev']
        continueVar = True

        for func in contractWorker:
            if ('name' in func):
                if (func['type'] =="function"): #and func['stateMutability'] == "payable"):
                    #functionNameArr.append(func['name'])
                    functionNameDict[func['name']] = {}
                    functionNameDict[func['name']] = func['inputs']
        if ((self.mintFunctionCall).lower() == "default"):
            if (self.amount ==0): #free mint
                taskLogger({"status" : "process","message":"Free mint scrape","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                for func in functionNameDict:
                    if ("free" in func.lower() and "mint" in func.lower()):
                        mintOption = func
                        self.inputStuct = functionNameDict[func]
                        continueVar = False
                        break
            if (continueVar):    
                if ('mint' in functionNameDict):
                    mintOption = 'mint'
                    self.inputStuct = functionNameDict['mint']
                else:
                    for func in contractWorker:
                        if ('name' in func):
                            if (not any(keyNegative in func['name'].lower() for keyNegative in negative) and func['type']=="function"):
                                if ('mint' in func['name'].lower()): #mint should be priority, if found break
                                    mintOption =func['name']
                                    self.inputStuct = func['inputs']
                                    break
                                if ('buy' in func['name'].lower() or 'purchase' in func['name']):
                                    mintOption =func['name']
                                    self.inputStuct = func['inputs']
                                    break
        else: #already set function name by input
            mintOption = self.mintFunctionCall
            try:
                self.inputStuct = functionNameDict[mintOption]
            except:
                taskLogger({"status" : "warn","message":"Empty struct, setting to empty arguments ","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                self.inputStuct = []

        try:
            return mintOption
        except:
            taskLogger({"status" : "warn","message":"Could not scrape function , forcing `mint` ","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return 'mint'


    def buildTxn(self,body):
        taskLogger({"status" : "process","message":"Encoding mint transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        argsOrder = []

        if (self.inputStuct == None): #might never happen
            mintFunction = self.contract.functions[self.mintFunctionCall](int(self.quantity)).buildTransaction(body)
            return mintFunction
        
        for i in self.inputStuct:
            if ("bytes" in i['type']):
                if (self.special == True and self.proof == None):
                    self.getProof()
                elif (self.special == False and i['type'] == "bytes"):
                    taskLogger({"status" : "process","message":"Generating bytes proof","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    self.proof = "0x"
                elif (self.special == False and i['type'] == "bytes32[]"):
                    taskLogger({"status" : "process","message":"Generating bytes32 proof","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    self.proof = []
                else:
                    taskLogger({"status" : "process","message":"Using prior generated proof","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                argsOrder.append(self.proof)
            elif (i['type'] == "uint256" or i['type'] == "uint16"):
                argsOrder.append(int(self.quantity))
            elif (i['type'] == "address"):
                argsOrder.append(self.walletAddress)

        try:
            self.mintArgs = argsOrder
            mintFunction = self.contract.encodeABI(fn_name=self.mintFunctionCall,args=argsOrder)
            taskLogger({"status" : "success","message":"Encoded mint transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return mintFunction
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed encoding mint transaction - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            time.sleep(10000)


    
    def buildBody(self):
        nonce = self.getNonce()
        self.nonce = nonce

        body = {
            'from' : self.walletAddress,
            'nonce' : nonce,
            'value' : web3Connection.toWei(self.amount,'ether'),
            'maxFeePerGas': web3Connection.toWei(self.maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(self.maxPriorityFee,'gwei')
        }

        return body

        
    def mint(self):
        body = self.buildBody()
        mintHexData = self.buildTxn(body)
        body = {
            'from' : self.walletAddress,
            'nonce' : self.getNonce(),
            'value' : web3Connection.toWei(self.amount*self.iterations,'ether'),
            'maxFeePerGas': web3Connection.toWei(self.maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(self.maxPriorityFee,'gwei'),
            'chainId' : 1 #change to 1 for main net
        }
         #check if we can mint one token or not

        while True:
            try:
                argNum = len(self.mintArgs)
                if (argNum == 0):
                    mintLive = self.contract.functions[self.mintFunctionCall]().buildTransaction(body)
                elif (argNum == 1):
                    mintLive = self.contract.functions[self.mintFunctionCall](self.mintArgs[0]).buildTransaction(body)
                elif (argNum == 2):
                    mintLive = self.contract.functions[self.mintFunctionCall](self.mintArgs[0],self.mintArgs[1]).buildTransaction(body)
                elif (argNum == 3):
                    mintLive = self.contract.functions[self.mintFunctionCall](self.mintArgs[0],self.mintArgs[1],self.mintArgs[2]).buildTransaction(body)
                elif (argNum == 4):
                    mintLive = self.contract.functions[self.mintFunctionCall](self.mintArgs[0],self.mintArgs[1],self.mintArgs[2],self.mintArgs[3]).buildTransaction(body)
                else:
                    taskLogger({"status" : "error","message":"Function structure is unknowned - {}, killing task".format(len(self.mintArgs)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    return False
                break
            except Exception as e:
                if (self.retryBool == False):
                    taskLogger({"status" : "error","message":"Error - {}. Retry is set to False, killing hoard task!".format(str(e)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    return False
                else:
                    taskLogger({"status" : "warn","message":"Monitoring sale - {}".format(str(e)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    time.sleep(2)
        try:
            self.checkHelper()
            contractCall = self.hoardContract.functions['startExploit'](self.contractAddress,mintHexData,self.iterations,True).buildTransaction(body)
        except Exception as e:
            try:
                contractCall = self.hoardContract.functions['startExploit'](self.contractAddress,mintHexData,self.iterations,False).buildTransaction(body)
                taskLogger({"status" : "warn","message":"Cannot autotransfer in a single transaction, you would have to run the withdraw module to collect your tokens after minting!","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                self.needToTransfer = True
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to start Hoard txn - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                updateTitleCall.addFail()
                return False
        
        if (contractCall['gas'] >=30000000):
            taskLogger({"status" : "error","message":"Failed to start Hoard txn - exceeds block gas limit. Reduce the number of hoarders!","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            updateTitleCall.addFail()

        else:
            totalEstimatedGas = str(contractCall['gas']*self.maxGasFee*10**-9)[:6]
            taskLogger({"status" : "warn","message":"Estimated maximum spending cost to mint {} tokens is : {}E".format(self.quantity*self.iterations,totalEstimatedGas),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            continueTxn = input("Would you like to continue Hoard mode? [y/n] : ")
            self.sendTxn(continueTxn,contractCall)
    
    def sendTxn(self,continueTxn,contractCall,tokenCtr = 0):
        if (continueTxn.lower() == "n"):
            taskLogger({"status" : "error","message":"Terminated transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            return False
        
        try:
            taskLogger({"status" : "warn","message":"Signing Transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            signedTransaction = web3Connection.eth.account.sign_transaction(contractCall,self.walletKey)
            taskLogger({"status" : "process","message":"Submitting Transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            result = web3Connection.eth.send_raw_transaction(signedTransaction.rawTransaction)
            updateTitleCall.addPending()
            taskLogger({"status" : "warn","message":"Pending - {}".format(self.getNonce()),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            statusTrack = web3Connection.eth.wait_for_transaction_receipt(result,timeout=300)
            if (statusTrack['status']==1): #successful transfer 
                if (self.mode == "add"):
                    taskLogger({"status" : "success","message":"Succesfully generated {} hoarders!".format(self.iterations),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    updateTitleCall.addSuccess()
                    self.checkHelper()
                elif (self.mode == "mint"):
                    taskLogger({"status" : "success","message":"Succesfully hoarded {} tokens!".format(self.quantity*self.iterations),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    if (self.needToTransfer):
                        taskLogger({"status" : "warn","message":"Tokens need to be withdrawn. Run the [Emergency Function] Force withdraw NFTS from all my Hoarders module!".format(self.quantity*self.iterations),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    gasUsed = statusTrack['gasUsed']
                    gasPrice = web3Connection.eth.get_transaction(result)['gasPrice']
                    transactionCost = gasUsed * gasPrice
                    transactionCost = web3Connection.fromWei(transactionCost,'ether')
                    transactionCost = str(transactionCost)[:6]
                    transactionHash = statusTrack['transactionHash'].hex()
                    updateTitleCall.addSuccess()
                    self.amount = self.amount*float(self.iterations)
                    self.contractPropertyScrape()
                    taskObject = {"status": "success","taskType": "Mint","receiver": self.contractAddress,"value": self.amount,"gas" : transactionCost , "mode": "Hoard" , "maxFee" : self.maxGasUsed, "wallet" : self.profileName, "transaction" : transactionHash , "osLink":self.osLink, "image":self.imageUrl,"mintName":self.mintName,"quickMintLink":"https://api.axze.io/share?contractAddress={}&func={}&qty={}&price={}".format(self.contractAddress,self.mintFunctionCall,self.quantity,self.amount)}
                    webhookLog(taskObject)
                elif (self.mode == "withdrawNFT"):
                    taskLogger({"status" : "success","message":"Succesfully withdrew {} tokens from hoarders!".format(tokenCtr),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                elif (self.mode == "withdrawFunds"):
                    taskLogger({"status" : "success","message":"Succesfully withdrew funds from hoarders!","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                return True
            else: 
                taskLogger({"status" : "error","message":"Failed Transaction, check etherscan","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                updateTitleCall.addFail()
                return False
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed Transaction - {}".format(str(e)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            updateTitleCall.addFail()
            return False

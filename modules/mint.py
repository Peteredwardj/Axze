import os,json,time,requests
from web3 import Web3
from app_modules.taskLogger import taskLogger
from app_modules.discordLog import webhookLog
from app_modules.apiModules import nodeProvider,etherScanApi,alternative,checkNode,cfNode
from app_modules.titleLog import classUpdateTitle
import cloudscraper

global web3Connection
updateTitleCall=classUpdateTitle("Mint")
cachedContracts = {}
cachedContractProperty = {}
submittingArr = []

class mint():
    def __init__(self,amount,quantity,walletAddress,walletKey,contractAddress,mintFunc,maxGasFee,maxPriorityFee,absoluteMax,autoAdjust,taskId,gasMode,mode):
        self.amount = amount
        self.quantity = quantity
        self.contract = None
        self.contractAddress = contractAddress
        self.contractAbi = None
        self.walletAddress = walletAddress
        self.walletKey = walletKey
        self.maxGasFee = maxGasFee
        self.maxPriorityFee = maxPriorityFee
        self.mintFunctionCall =mintFunc
        self.absoluteMax = absoluteMax
        self.autoAdjust=autoAdjust
        self.taskId = taskId
        self.strAddress = contractAddress
        self.gasMode = gasMode
        self.mode = mode
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

    def getProof(self): #to be changed according to drop
        session = cloudscraper.create_scraper()
        try:
            body = {"address":self.walletAddress}
            while True:
                taskLogger({"status" : "warn","message":"Getting proof","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                response = session.post("https://wzrds.xyz/mint/proof",json=body)
                responseJson = json.loads(response.text)
                proof = responseJson['proof']
                if (proof!= None):
                    taskLogger({"status" : "success","message":"Got proof","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    self.proof = proof
                    break
                else:
                    taskLogger({"status" : "warn","message":"Waiting for proof","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    time.sleep(1)

        except Exception as e:
            taskLogger({"status" : "warn","message":"Failed to get proof - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            self.getProof()
            
    def update(self,maxGasFee,maxPriorityFee,cancel):
        if (self.minted == False):
            self.updated+=1
            self.maxGasFee = maxGasFee
            self.maxPriorityFee = maxPriorityFee
            self.cancel = cancel
            taskLogger({"status" : "process","message":"Updating task state","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        else:
            pass


    def contractPropertyScrape(self):
        try:
            first = False
            global cachedContractProperty
            if (self.contractAddress not in cachedContractProperty):
                cachedContractProperty[self.contractAddress] = None
                looksRare = "https://api.looksrare.org/api/v1/collections?address={}".format(self.contractAddress)
                response = requests.get(looksRare)
                responseJson = json.loads(response.text)
                contractOwner = responseJson["data"]["owner"]
                opensea = "https://api.opensea.io/api/v1/collections?asset_owner={}&offset=0&limit=300".format(contractOwner)
                response = requests.get(opensea)
                responseJson = json.loads(response.text)
                self.mintName = responseJson[0]['primary_asset_contracts'][0]['name']
                self.imageUrl = responseJson[0]['primary_asset_contracts'][0]['image_url']
                self.osLink = "https://opensea.io/collection/"+responseJson[0]['slug']
                cachedContractProperty[self.contractAddress] = {"mintName": self.mintName,"imageUrl":self.imageUrl,"osLink":self.osLink}
            else:
                while (cachedContractProperty[self.contractAddress] == None):
                    if (not first):
                        taskLogger({"status" : "warn","message":"Waiting for cached data","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                        first = True

                self.imageUrl = cachedContractProperty[self.contractAddress]['imageUrl']
                self.mintName = cachedContractProperty[self.contractAddress]['mintName']
                self.osLink = cachedContractProperty[self.contractAddress]['osLink'] 
                taskLogger({"status":"success", "message": "Retrieved contract data from Cache","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        except Exception as e:
            taskLogger({"status":"warn", "message": "Failed to retrieve collection data - {}".format(str(e)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            cachedContractProperty[self.contractAddress] = {"mintName": self.mintName,"imageUrl":self.imageUrl,"osLink":self.osLink}

    def fetchProperties(self):
        while True:
            try:
                taskLogger({"status" : "process","message":"Fetching contract properties","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                response = requests.get("https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}".format(self.contractAddress,etherScanApi))
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
        if (self.mode=="default"):
            web3Connection = Web3(Web3.HTTPProvider(nodeProvider))
        else: #experimental
            taskLogger({"status" : "process","message":"Experimental mode","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            web3Connection = Web3(Web3.HTTPProvider(checkNode()))
        self.connect()
        self.mint()

    def connect(self):
        global cachedContracts
        updateTitleCall.addRun()
        first = False
        taskLogger({"status":"process","message":"Starting Task","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
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
                    taskLogger({"status" : "warn","message":"Waiting for cached data","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    first = True
                
            self.contractAbi = cachedContracts[self.contractAddress] 
            taskLogger({"status":"success", "message": "Retrieved data from Cache","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)

        self.contract = web3Connection.eth.contract(address = self.contractAddress, abi = self.contractAbi)
        self.mintFunctionCall = self.functionLogicScrape()
        taskLogger({"status" : "success","message":"Initialized Contract - {}".format(self.mintFunctionCall),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)

    def getGas(self):
        while True:
            try:
                response = requests.get('https://ethgasstation.info/json/ethgasAPI.json')
                responseJson = json.loads(response.text)
                return int(responseJson['fast']/10)
            except Exception as e:
                taskLogger({"status" : "error","message":"Error estimating Gas - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                time.sleep(2)

    
    def getNonce(self):
        taskLogger({"status" : "process","message":"Fetching Nonce","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        try:
            return web3Connection.eth.get_transaction_count(self.walletAddress)
        except Exception as e:
            print(e)
            time.sleep(1)
            self.getNonce()

    def functionLogicScrape(self): #Seach for a possible function here 
        functionNameDict={}
        contractWorker = json.loads(self.contractAbi)
        negative = ['presale','whitelist','owner','admin','allow','owner','dev']
        continueVar = True

        for func in contractWorker:
            if ('name' in func):
                if (func['type'] =="function" and func['stateMutability'] == "payable"):
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
        taskLogger({"status" : "process","message":"Building transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)

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
                    self.proof = "[]"
                else:
                    taskLogger({"status" : "process","message":"Using prior generated proof","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                argsOrder.append(self.proof)
            elif (i['type'] == "uint256"):
                argsOrder.append(int(self.quantity))
            elif (i['type'] == "address"):
                argsOrder.append(self.walletAddress)
        if (len(self.inputStuct) == 0): #no arguments
            mintFunction = self.contract.functions[self.mintFunctionCall]().buildTransaction(body)
        elif (len(self.inputStuct) == 1): 
            mintFunction = self.contract.functions[self.mintFunctionCall](argsOrder[0]).buildTransaction(body)
        elif (len(self.inputStuct) == 2): 
            mintFunction = self.contract.functions[self.mintFunctionCall](argsOrder[0],argsOrder[1]).buildTransaction(body)
        else:
            mintFunction = None
        
        self.mintFunction = mintFunction


    def sendTxn(self,body):

        '''if (self.contractAddress==Web3.toChecksumAddress("0xe5e771bc685c5a89710131919c616c361ff001c6")):
            self.getProof()''' #use same logic here for force update (i.e set self.special = True , change the getProof() function)
        
        if (self.mintFunction == None):
            self.buildTxn(body)

        if (self.mintFunction == None):
            taskLogger({"status" : "error","message":"Unknown function structure!\n - {}".format(self.inputStuct),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            time.sleep(10000)

        taskLogger({"status" : "process","message":"Authorizing Transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        signedTransaction = web3Connection.eth.account.sign_transaction(self.mintFunction,self.walletKey)
        taskLogger({"status" : "process","message":"Submitting Transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        result = web3Connection.eth.send_raw_transaction(signedTransaction.rawTransaction)
        updateTitleCall.addSubmitted()
        return result


    def cancelTxn(self):
        self.maxGasFee = self.maxGasFee+20
        self.maxPriorityFee = self.maxGasFee
        body = {
            'nonce' : self.nonce,
            'to' : self.walletAddress,
            'value' : web3Connection.toWei(0,'ether'),
            'gas' : 21000,
            'maxFeePerGas': web3Connection.toWei(self.maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(self.maxPriorityFee,'gwei'),
            'chainId':1
        }
        taskLogger({"status" : "warn","message":"Cancelling Transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        signedTransaction = web3Connection.eth.account.sign_transaction(body,self.walletKey)
        taskLogger({"status" : "process","message":"Submitting Transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        result = web3Connection.eth.send_raw_transaction(signedTransaction.rawTransaction)
        updateTitleCall.addSubmitted()
        return result
        
    def mint(self):
        statusTrack = None 
        nonce = self.getNonce()
        self.nonce = nonce
        body = {
            'from' : self.walletAddress,
            'nonce' : nonce,
            'value' : web3Connection.toWei(self.amount,'ether'),
            'maxFeePerGas': web3Connection.toWei(self.maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(self.maxPriorityFee,'gwei')
        }
        if (self.gasMode == "auto"):
            taskLogger({"status":"process","message":"Auto Gas selected","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            del body['maxFeePerGas']
            del body['maxPriorityFeePerGas']

        while True:
            try:
                if (self.minted):
                    break  #prevent sending the same txn
                if (self.updated>self.current):
                    self.current = self.updated
                    if (not self.cancel):
                        taskLogger({"status" : "process","message":"Speeding Up Transaction..","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                        body['maxFeePerGas'] = web3Connection.toWei(self.maxGasFee,'gwei')
                        body['maxPriorityFeePerGas'] = web3Connection.toWei(self.maxPriorityFee,'gwei')
                        result = self.sendTxn(body)
                    else:
                        result = self.cancelTxn()
                else:
                    result = self.sendTxn(body)
                taskLogger({"status" : "warn","message":"Pending - Nonce : {}".format(nonce),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                updateTitleCall.addPending()
                #statusTrack = web3Connection.eth.wait_for_transaction_receipt(result)
                while True: #Poll
                    try:
                        statusTrack = web3Connection.eth.get_transaction_receipt(result)
                    except:
                        statusTrack = None

                    if statusTrack is not None and statusTrack['blockHash'] is not None:
                        self.minted=True
                        break
                    else:
                        if (self.updated>self.current):                      #check if speed up or cancellation has been made here
                            self.current = self.updated
                            if (not self.cancel):
                                taskLogger({"status" : "process","message":"Speeding Up Transaction..","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                                body['maxFeePerGas'] = web3Connection.toWei(self.maxGasFee,'gwei')
                                body['maxPriorityFeePerGas'] = web3Connection.toWei(self.maxPriorityFee,'gwei')
                                result = self.sendTxn(body)
                            else:
                                result = self.cancelTxn()
                    time.sleep(0.1)
                
                if (statusTrack!=None):
                    transactionHash = statusTrack['transactionHash'].hex()
                    blockNumber = statusTrack['blockNumber']
                    gasUsed = statusTrack['gasUsed']
                    self.contractPropertyScrape()
                    taskObject = {"status": "success","taskType": "Mint","receiver": self.contractAddress,"value": self.amount,"gas" : gasUsed , "mode": self.mode , "maxFee" : self.maxGasUsed, "wallet" : self.profileName, "transaction" : transactionHash , "osLink":self.osLink, "image":self.imageUrl,"mintName":self.mintName,"quickMintLink":"http://localhost:8080/qm?contractAddress={}&func={}&qty={}&price={}".format(self.contractAddress,self.mintFunctionCall,self.quantity,self.amount)}
                    if (not self.cancel):
                        if (statusTrack['status']==1): #successful mint 
                            taskLogger({"status" : "success","message":"Succesfully Minted, included in block : {}".format(blockNumber),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                            updateTitleCall.addSuccess()
                        else: 
                            taskObject['status'] = "fail"
                            taskLogger({"status" : "error","message":"Failed Minting - Reverted","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                            updateTitleCall.addFail()
                        webhookLog(taskObject)
                        break
                    else:
                        taskLogger({"status" : "success","message":"Succesfully cancelled, included in block : {}".format(blockNumber),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                        break
                else:
                    taskLogger({"status" : "error","message":"Failed Minting - Empty TXN","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    updateTitleCall.addFail()
                    break

            except Exception as e:
                if ('insufficient funds' in str(e)):
                    taskObject = {"status": "revert","taskType": "Mint - Reverted","receiver": self.contractAddress,"value": self.amount,"gas" : 0 , "mode": self.mode , "wallet" : self.profileName , "reason":str(e) , "maxFee" :self.maxGasUsed,"quickMintLink":"http://localhost:8080/qm?contractAddress={}&func={}&qty={}&price={}".format(self.contractAddress,self.mintFunctionCall,self.quantity,self.amount)}
                    taskLogger({"status" : "error","message":"Failed Minting - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    updateTitleCall.addFail()
                    webhookLog(taskObject)
                    break
                elif ('max fee per gas less than block base fee' in str(e)):
                    if (self.autoAdjust):
                        gasEst = self.getGas()
                        if (gasEst+10 > self.absoluteMax):
                            taskLogger({"status" : "error","message":"Current Gas too high, exceeds absolute Max - Stopping Task","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                            break
                        else:
                            self.maxGasFee = gasEst+10
                            taskLogger({"status" : "error","message":"Max Fee too low, increasing to - {}".format(self.maxGasFee),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    else:
                        taskLogger({"status" : "error","message":"Current Gas higher than set gas, auto adjust not enabled - Stopping Task","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                        break
                else:     
                    e = str(e)
                    try:
                        e = e.split("execution reverted: ")[1]   
                    except:
                        pass                      
                    taskLogger({"status" : "warn","message":"Monitoring - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    time.sleep(0.5)
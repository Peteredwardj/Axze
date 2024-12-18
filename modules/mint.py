import os,json,time,requests
from statistics import mode
from web3 import Web3
from app_modules.taskLogger import taskLogger
from app_modules.discordLog import webhookLog
from app_modules.apiModules import nodeProvider,etherScanApi,alternative,checkNode,cfNode
from app_modules.titleLog import classUpdateTitle
import cloudscraper
from blocknative.stream import Stream
from bs4 import BeautifulSoup


global web3Connection
etherScanApi = 'RITWHK4P371RN5G4PY1WGMNT3XQ32M9BVU'
natApi = 'ed896734-eebe-413a-a8b7-62f5f7a699d8'
stream  = Stream(natApi,network_id=4)
updateTitleCall=classUpdateTitle("Mint")
cachedContracts = {}
cachedContractProperty = {}
cachedFlip = {}
submittingArr = []

class mint():
    def __init__(self,amount,quantity,walletAddress,walletKey,contractAddress,mintFunc,maxGasFee,maxPriorityFee,absoluteMax,autoAdjust,taskId,gasMode,mode,gasLimit=None,functionToMonitor=None,paramToMonitor = None):
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
        self.gasLimit = gasLimit
        self.functionToMonitor = functionToMonitor
        self.paramToMonitor = paramToMonitor


    async def handleTxn(self,transaction,unsubscribe):
        global cachedFlip
        inputData = transaction["input"]
        match = False

        try: #matching logic
            decodedFunc,decodedParams= self.contract.decode_function_input(inputData)
            decodedFunc = str(decodedFunc).split()[1].split('(')[0]
            if(decodedFunc == self.functionToMonitor):
                if (self.paramToMonitor != "none"):
                    for param in self.paramToMonitor:
                        if (decodedParams[param] == self.paramToMonitor[param] or str(decodedParams[param]).lower() == str(self.paramToMonitor[param]).lower()):
                            match = True
                else:
                    match = True
    
        except Exception as e:
            taskLogger({"status" : "error","message":"Flipstate error - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)


        if (match):
            transactionTo = transaction["to"]
            maxFeePerGas = transaction["maxFeePerGasGwei"]
            maxPriorityFeePerGas = transaction["maxPriorityFeePerGasGwei"]
            cachedFlip[self.contractAddress]['maxFeePerGas'] = float(maxFeePerGas)
            cachedFlip[self.contractAddress]['maxPriorityFeePerGas'] = float(maxPriorityFeePerGas)
            cachedFlip[self.contractAddress]['proceed'] = True
            self.maxGasFee = cachedFlip[self.contractAddress]['maxFeePerGas']
            self.maxPriorityFee = cachedFlip[self.contractAddress]['maxPriorityFeePerGas']
            taskLogger({"status" : "warn","message":"Picked up matching transaction","prefix":"({},{}) GWEI".format(maxFeePerGas,maxPriorityFeePerGas)},self.taskId)
            unsubscribe()
            self.mint()
        else:
            taskLogger({"status" : "warn","message":"Pending transaction not matched, ignoring! {} : {}".format(decodedFunc,decodedParams),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)

    def monitor(self):
        while True:
            try:
                response = self.contract.functions[self.functionToMonitor]().call()
                if (str(response) == str(self.paramToMonitor)):
                    taskLogger({"status" : "success","message":"Matched monitor response - {}".format(str(response)),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    break
                else:                
                    taskLogger({"status" : "warn","message":"Monitoring function {} , current response: {}".format(self.functionToMonitor,response),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    time.sleep(0.2)
            except Exception as e:
                taskLogger({"status" : "warn","message":"Failed monitoring function - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                time.sleep(0.2)

        self.mint()

    def startStream(self,addressToMonitor):
        stream.subscribe_address(addressToMonitor, self.handleFlip)
        stream.connect()

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
                endpoint = "https://api.opensea.io/api/v1/asset_contract/{}".format(self.contractAddress)
                headers = {"X-API-KEY": "a4dc98c6cd5b429a8a9ba947c4aceb91"}
                response = requests.get(endpoint, headers=headers)
                responseJson = json.loads(response.text)
                self.mintName = responseJson['collection']['name']
                self.imageUrl = responseJson['image_url']
                self.osLink = "https://opensea.io/collection/"+responseJson['collection']['slug']
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
                response = requests.get("https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}".format(self.contractAddress,etherScanApi),timeout=5)
                if (response.status_code == 200):
                    return (json.loads(response.text)['result'])
                else:
                    taskLogger({"status" : "error","message":"Failed to fetch contract properties - {}".format(response.status_code),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    time.sleep(2)
                    
            except Exception as e: 
                taskLogger({"status" : "error","message":"Failed to fetch contract properties - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                time.sleep(2)
    
    def fetchContractOwner(self):
        while True:
            try:
                ses = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
                )
                taskLogger({"status" : "process","message":"Fetching contract owner","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                response = ses.get("https://etherscan.io/address/{}".format(self.contractAddress))
                if (response.status_code == 200):
                    soup = BeautifulSoup(response.text,"html.parser")
                    creatorAddress = soup.find("a",{"title":"Creator Address"})
                    if (creatorAddress == None):
                        creatorAddress = soup.find("a",{"title":"Public Name Tag (viewable by anyone)"})

                    #creatorAddress = creatorAddress.text
                    creatorAddress = creatorAddress['href'].replace("/address/","")
                    creatorAddress = Web3.toChecksumAddress(creatorAddress.replace(" ",""))
                    taskLogger({"status" : "success","message":"Fetched contract owner - {}".format(creatorAddress),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    return creatorAddress
                else:
                    taskLogger({"status" : "error","message":"Failed to fetch contract owner - {}".format(response.status_code),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    time.sleep(2)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to fetch contract owner - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                time.sleep(2)

    def Startflipstate(self):
        global cachedFlip
        body  = self.buildBody()
        self.buildTxn(body) 
        if (self.contractAddress not in cachedFlip):
            cachedFlip[self.contractAddress] = {}
            cachedFlip[self.contractAddress]['proceed'] = False
            addressToMonitor = self.fetchContractOwner()
            stream.subscribe_address(addressToMonitor, self.handleTxn)
            taskLogger({"status" : "process","message":"Flipstate active","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            stream.connect()

        else:
            taskLogger({"status" : "process","message":"Flipstate subtask active","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            while True:
                if (cachedFlip[self.contractAddress]['proceed'] == True):
                    self.maxGasFee = cachedFlip[self.contractAddress]['maxFeePerGas']
                    self.maxPriorityFee = cachedFlip[self.contractAddress]['maxPriorityFeePerGas']
                    taskLogger({"status" : "warn","message":"Picked up matching transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    break
            self.mint()

    def order(self):
        global web3Connection

        try:
            web3Connection = Web3(Web3.HTTPProvider(checkNode()))
        except Exception as e:
            taskLogger({"status" : "error","message":"Check if you have correctly set up your node in settings! - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            time.sleep(10000)
        

        taskLogger({"status" : "process","message":"Running {} mode".format(self.mode),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        self.connect()
        if (self.mode == "flipstate"):
            self.Startflipstate()
        elif (self.mode == "monitor"):
            self.monitor()
        else:
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
        forceTxnModes = ['flipstate','monitor']
        taskLogger({"status" : "process","message":"Building transaction","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
        argsOrder = []

        if (self.inputStuct == None): #might never happen
            mintFunction = self.contract.functions[self.mintFunctionCall](int(self.quantity)).buildTransaction(body)
            return mintFunction
        
        if (self.contractAddress == Web3.toChecksumAddress("0x49adcc97404c197190a5866885018c558006974a")):
            taskLogger({"status" : "process","message":"Encoding release data","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            mintFunction = self.contract.functions['mint']([],'0x',int(self.quantity),3).buildTransaction(body)
            self.mintFunction = mintFunction
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
        if (self.mode not in forceTxnModes):
            if (len(self.inputStuct) == 0): #no arguments
                mintFunction = self.contract.functions[self.mintFunctionCall]().buildTransaction(body)
            elif (len(self.inputStuct) == 1): 
                mintFunction = self.contract.functions[self.mintFunctionCall](argsOrder[0]).buildTransaction(body)
            elif (len(self.inputStuct) == 2): 
                mintFunction = self.contract.functions[self.mintFunctionCall](argsOrder[0],argsOrder[1]).buildTransaction(body)
            else:
                mintFunction = None
        else:
            taskLogger({"status" : "process","message":"Encoding data","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            data=self.contract.encodeABI(fn_name=self.mintFunctionCall,args=argsOrder)
            body['data'] = data
            body['gas'] = self.gasLimit
            body['to'] =  self.contractAddress
            body['chainId']= 1 
            mintFunction = body

        self.mintFunction = mintFunction


    def sendTxn(self,body):

        '''if (self.contractAddress==Web3.toChecksumAddress("0xe5e771bc685c5a89710131919c616c361ff001c6")):
            self.getProof()''' #use same logic here for force update (i.e set self.special = True , change the getProof() function)
        
        if (self.mintFunction == None):
            self.buildTxn(body)

        if (self.mintFunction == None):
            taskLogger({"status" : "error","message":"Unknown function structure!\n - {}".format(self.inputStuct),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            time.sleep(10000)
        
        if (self.mode == "flipstate"):
            taskLogger({"status" : "process","message":"Updating gas [Flipstate]","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            self.mintFunction['maxFeePerGas'] =  web3Connection.toWei(self.maxGasFee,'gwei'),
            self.mintFunction['maxPriorityFeePerGas'] =  web3Connection.toWei(self.maxPriorityFee,'gwei')

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

        if (self.gasMode == "auto" and self.mode!="flipstate"):
            taskLogger({"status":"process","message":"Auto Gas selected","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
            del body['maxFeePerGas']
            del body['maxPriorityFeePerGas']
        
        return body

        
    def mint(self):
        statusTrack = None 
        body = self.buildBody()
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
                taskLogger({"status" : "warn","message":"Pending - Nonce : {}".format(self.nonce),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
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
                    transactionCost = gasUsed
                    try:
                        gasPrice = web3Connection.eth.get_transaction(result)['gasPrice']
                        transactionCost = gasUsed * gasPrice
                        transactionCost = web3Connection.fromWei(transactionCost,'ether')
                        transactionCost = str(transactionCost)[:6]
                    except:
                        pass
                    self.contractPropertyScrape()
                    taskObject = {"status": "success","taskType": "Mint","receiver": self.contractAddress,"value": self.amount,"gas" : transactionCost , "mode": self.mode , "maxFee" : self.maxGasUsed, "wallet" : self.profileName, "transaction" : transactionHash , "osLink":self.osLink, "image":self.imageUrl,"mintName":self.mintName,"quickMintLink":"https://api.axze.io/share?contractAddress={}&func={}&qty={}&price={}".format(self.contractAddress,self.mintFunctionCall,self.quantity,self.amount)}
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
                    taskObject = {"status": "revert","taskType": "Mint - Reverted","receiver": self.contractAddress,"value": self.amount,"gas" : 0 , "mode": self.mode , "wallet" : self.profileName , "reason":str(e) , "maxFee" :self.maxGasUsed,"quickMintLink":"https://api.axze.io/share?contractAddress={}&func={}&qty={}&price={}".format(self.contractAddress,self.mintFunctionCall,self.quantity,self.amount)}
                    taskLogger({"status" : "error","message":"Failed Minting - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    updateTitleCall.addFail()
                    webhookLog(taskObject)
                    break
                elif ('max fee per gas less than block base fee' in str(e)):
                    taskLogger({"status" : "error","message":"Current set gas is too low for the current network condition","prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    time.sleep(0.5)
                else:     
                    e = str(e)
                    try:
                        e = e.split("execution reverted: ")[1]   
                    except:
                        pass                      
                    taskLogger({"status" : "warn","message":"Failed sending transaction - {}".format(e),"prefix":"({},{}) GWEI".format(self.maxGasFee,self.maxPriorityFee)},self.taskId)
                    time.sleep(0.5)

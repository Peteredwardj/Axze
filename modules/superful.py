import os,json,time,requests,re,string,names,random,tweepy,cloudscraper
from socket import timeout
from xmlrpc.client import FastMarshaller
from web3 import Web3
from app_modules.taskLogger import taskLogger
from app_modules.discordLog import webhookLog
from app_modules.apiModules import nodeProvider,etherScanApi,alternative,checkNode,capKey,cfNode,checkCapMonster
from app_modules.titleLog import classUpdateTitle
from app_modules.proxy import proxy_choice
from modules.twitter import browserTask,fileBrowser,followTwitter,connectDiscordRequestSuperful,connectTwitterSuperful
from modules.discordModule import inviteTask
from eth_account.messages import encode_defunct
from fake_useragent import UserAgent
ua = UserAgent()


global web3Connection
updateTitleCall=classUpdateTitle("Superful")
siteKey = "6Lf9ZCYgAAAAANbod3nwYtteIUlNGmrmoKnwu5uW"
workingProxy = []

class superful():
    def __init__(self,targetUrl,wallet,walletKey,twitterToken,twitterPassword,discordToken,accessToken,accessTokenSecret,consumerKey,consumerSecret,mode,taskId,transferTask,customField,discordMode="default",reactParam =None):
       self.targetUrl = targetUrl
       self.wallet = Web3.toChecksumAddress(wallet)
       self.walletKey = walletKey
       self.twitterToken = twitterToken
       self.discordToken = discordToken
       self.taskId = taskId
       self.session = None
       self.nonce = None
       self.message = None
       self.signature = None
       self.csrfToken = None
       self.twitterReq = "None"
       self.discordReq = "None"
       self.minimumBalance = None
       self.mode = mode
       self.submitLoad = None
       self.captchaReq = False
       self.first = True
       self.proceed = False
       self.image = "None"
       self.proxy = "None"
       self.name = "None"
       self.password = twitterPassword
       self.params=""
       self.accessToken = accessToken
       self.accessTokenSecret = accessTokenSecret
       self.consumerKey = consumerKey
       self.consumerSecret = consumerSecret
       self.prefix = "@"+twitterToken
       self.nonce = 0
       self.proxObj = None
       self.discordMode = discordMode
       self.reactParam = reactParam
       self.likeReq = "unspecified"
       self.transferTask = transferTask
       self.customField = customField
       self.token = ''
       self.raffId = ''

    def connect(self):
        global web3Connection
        taskLogger({"status" : "process","message":"Connecting to node","prefix":self.prefix},self.taskId)
        web3Connection = Web3(Web3.HTTPProvider(cfNode))
        taskLogger({"status":"success", "message": "Connected to node","prefix":self.prefix},self.taskId)
        updateTitleCall.addRun()
        return self.initialize()

    def rotateProxy(self,retry=False):
        if (self.session != None):
            self.session.cookies.clear()

        taskLogger({"status":"process", "message": "Rotating proxy","prefix":self.prefix},self.taskId)
        self.session = cloudscraper.create_scraper(
               browser={
                        'browser': 'firefox',
                        'platform': 'windows',
                        'mobile': False
            }
        )
        self.session.headers['User-Agent'] = ua['firefox']
        chosenProxy=proxy_choice()
        self.proxObj = chosenProxy
        self.session.proxies.update(chosenProxy)
        self.proxy = str(self.session.proxies['http'])



    def initialize(self):  
        self.rotateProxy() #initialize session

        self.login()


        if ("disconnect" in self.mode):
            res = self.disconnect()
            if (res):
                updateTitleCall.addSuccess()
        elif ("connect" in self.mode):
            res,message = self.checkConnected()
            if (message != "connected-before"):
                #res,message = browserTask(self.twitterToken,self.password,self.discordToken,"twitterAcc",self.prefix,self.taskId,self.session,self.mode)
                if (res == True):
                    taskObject = {'url':self.targetUrl,'name':"@{}".format(self.twitterToken),'status': "success",'taskType':"Superful Connect",'statusMessage':'Successfully connected socials','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"None",'twitterProj':"none",'discordProj':"none",'image':"https://cdn.discordapp.com/attachments/837783679810928671/999220088903319612/AXZE_PFP_FIX.jpg"}
                    updateTitleCall.addSuccess()
                else:
                    taskObject = {'url':self.targetUrl,'name':"@{}".format(self.twitterToken),'status': "error",'taskType':"Superful Connect",'statusMessage':'Failed connecting socials','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':"none",'discordProj':"none",'image':"https://cdn.discordapp.com/attachments/837783679810928671/999220088903319612/AXZE_PFP_FIX.jpg"}
                    updateTitleCall.addFail()
                webhookLog(taskObject,self.session)  
            else:
                updateTitleCall.addSuccess()

        else:
            verifiedEntry = self.verify()
            if (verifiedEntry == False):
                self.fetchRaffleInfo()
                if (self.discordReq != "None"):          #fulfill requirements
                    if (self.discordToken == "Unspecified"):
                        taskLogger({"status" : "error","message":"No discord token supplied for task but joining server is required!","prefix":self.prefix},self.taskId)
                    else:
                        inviteTaskInstance = inviteTask(self.discordToken,self.discordReq,self.proxy,self.taskId,self.discordMode,self.reactParam)
                        inviteTaskInstance.main()
                if (not self.twitterMethod()):
                    return 
                self.submit()

    def checkConnected(self):
        while (True):
            try:
                taskLogger({"status" : "process","message":"Checking if socials are connected","prefix":self.prefix},self.taskId)
                response = self.session.get("https://www.superful.xyz/superful-api/v1/account/settings")
                if (response.status_code == 200):
                    responseData = json.loads(response.text)
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed socials account check - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(2)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed socials account check  - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)

        connectedAccounts = responseData['account_connections']
        connectedDiscord = connectedAccounts[0]['username']
        connectedTwitter = connectedAccounts[1]['username']
    
        if (connectedTwitter!=None):
                if (connectedDiscord == None):
                    if (self.discordToken == "Unspecified"):
                        taskLogger({"status" : "success","message":"Twitter connected and discord token is not supplied, skipping account!","prefix":self.prefix},self.taskId)
                        return True,"connected-before"
                else:
                    taskLogger({"status" : "success","message":"All socials connected, skipping account!","prefix":self.prefix},self.taskId)
                    return True,"connected-before"

        if (connectedTwitter == None):
            if (fileBrowser(self.twitterToken) == False): #profile not found ,save cookie here
                res,message = browserTask(self.twitterToken,self.password,self.discordToken,"axzeio",self.prefix,self.taskId,self.session,self.mode)
                if (res!= True):
                    taskLogger({"status" : "error","message":"Failed Twitter setup - {}".format(message),"prefix":self.prefix},self.taskId)
                    return False,"Failed Twitter setup - {}".format(message)
            taskLogger({"status" : "warn","message":"Twitter is not connected!","prefix":self.prefix},self.taskId)
            res,message = connectTwitterSuperful(self.twitterToken,self.session,self.prefix,self.taskId)
            if (res == False):
                return res,message #return on fail

        if (connectedDiscord == None and self.discordToken!="Unspecified"):
            taskLogger({"status" : "warn","message":"Discord is not connected and token is supplied in excel file!","prefix":self.prefix},self.taskId)
            res,message = connectDiscordRequestSuperful(self.discordToken,self.prefix,self.session,self.taskId)

        return res,message   

    def disconnect(self):
        orderArr = ['Twitter','Discord']
        endpointArr = ['https://www.superful.xyz/superful-api/v1/account/login/twitter/v1/revoke','https://www.superful.xyz/superful-api/v1/account/login/discord/revoke']        #400 status = account connection not found
        for endpoint in range(0,len(endpointArr)):
            while True:
                try:
                    taskLogger({"status" : "process","message":"Disconnecting {}".format(orderArr[endpoint]),"prefix":self.prefix},self.taskId)
                    response  = self.session.delete(endpointArr[endpoint])
                    if (response.status_code == 200):
                        taskLogger({"status" : "success","message":"Succesfully disconnected {}".format(orderArr[endpoint]),"prefix":self.prefix},self.taskId)
                        break
                    elif (response.status_code == 400):
                        responseJson = json.loads(response.text)
                        message = responseJson['message']
                        if (message == "Account connection not found."):
                            taskLogger({"status" : "warn","message":"{} connection not found for this wallet,skipping".format(orderArr[endpoint]),"prefix":self.prefix},self.taskId)
                            break
                    else:
                        taskLogger({"status" : "error","message":"Failed disconnecting {} - {}".format(orderArr[endpoint],response.url),"prefix":self.prefix},self.taskId)
                        time.sleep(3)
                except Exception as e:
                    taskLogger({"status" : "error","message":"Failed disconnecting {} - {}".format(orderArr[endpoint],e),"prefix":self.prefix},self.taskId)
                    time.sleep(3)
        return True
                    
    def login(self):
        self.session.headers['content-type'] = 'application/json'
        data = {"address":self.wallet,"signature":None}
        while (True):
            try:
                taskLogger({"status" : "process","message":"Fetching session","prefix":self.prefix},self.taskId)
                response = self.session.post("https://www.superful.xyz/superful-api/v1/account/login",data = json.dumps(data))
                if (response.status_code == 200):
                    message = json.loads(response.text)["sign_message"]
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed fetching session - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(2)
                    self.refreshSession(True)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed fetching session - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)
                self.refreshSession(True)

        taskLogger({"status" : "success","message":"Fetched session","prefix":self.prefix},self.taskId)
        message = encode_defunct(text=message)
        taskLogger({"status" : "process","message":"Signing session","prefix":self.prefix},self.taskId)
        signed_message = web3Connection.eth.account.sign_message(message, private_key=self.walletKey)
        self.signature = web3Connection.toHex(signed_message['signature'])
        taskLogger({"status" : "success","message":"Signed session","prefix":self.prefix},self.taskId)
        self.authenticate()

    def authenticate(self):
        while (True):

            payload = {
                    "address":self.wallet,
                    "signature": self.signature
            }

            try:
                taskLogger({"status" : "process","message":"Logging in","prefix":self.prefix},self.taskId)
                response = self.session.post("https://www.superful.xyz/superful-api/v1/account/login",data = json.dumps(payload))
                if (response.status_code == 200):
                    responseJson = json.loads(response.text)
                    self.token = responseJson['token']
                    self.session.headers['Authorization'] = self.token
                    taskLogger({"status" : "success","message":"Succesfully logged in","prefix":self.prefix},self.taskId)
                    break
                    
                else:
                    taskLogger({"status" : "error","message":"Failed login - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed login - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)

    def fetchRaffleInfo(self):
        _,_,_,_,projectUser,_,slug = self.targetUrl.split("/")
        endpoint = "https://www.superful.xyz/superful-api/v1/project/{}?event_slug={}".format(projectUser,slug)
        while True:
            try:
                response = self.session.get(endpoint)
                if (response.status_code == 200):
                    responseData = json.loads(response.text)
                    taskLogger({"status" : "success","message":"Fetched raffle properties","prefix":self.prefix},self.taskId)
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed fetching properties - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed fetching raffle properties - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)
        
        try:
            taskLogger({"status" : "process","message":"Extracting properties","prefix":self.prefix},self.taskId)
            self.image = responseData['project']['logo_url']
            events = responseData['events']
            projDat = None
            for event in range(0,len(events)):
                if (events[event]['slug'] == slug):
                    projDat = events[event]
                    break
            if (projDat!=None):
                self.raffId = projDat['id']
                self.name = projDat['name']    #extract project name
                self.twitterReq = projDat['twitter_requirements'] #extract twitter follow requirement
                discordReq = projDat['discord_requirements']['requirements']
                if (len(discordReq)>0):
                    self.discordReq = discordReq[0]['server_invite_code']
               
                taskLogger({"status" : "success","message":"Extracted properties","prefix":self.prefix},self.taskId)
                
            else:
                taskLogger({"status" : "error","message":"Failed to fetch property data","prefix":self.prefix},self.taskId)
                return False

        except Exception as e:
            taskLogger({"status" : "error","message":"Failed to fetch property data - {}".format(e),"prefix":self.prefix},self.taskId)

        

    def requestSolutionMon(self):
        global siteKey
        endPoint="https://api.capmonster.cloud/createTask"
        payload = {
                    "clientKey":checkCapMonster(),
                    "task":
                    {
                        "type":"NoCaptchaTask",
                        "websiteURL":self.targetUrl,
                        "websiteKey": siteKey
                    }
                }

        while True:
            try:
                response=requests.post(endPoint,data = json.dumps(payload))
                if (response.status_code==200):
                    taskLogger({"status" : "process","message":"Beginning solve","prefix":self.prefix},self.taskId)
                    responseJson=json.loads(response.text)
                    if (responseJson['errorId']==0):
                        dataDomeTask=responseJson['taskId']
                        break
                    else:
                        taskLogger({"status" : "error","message":"Failed to create solution task - {}".format(responseJson['errorId']),"prefix":self.prefix},self.taskId)
                        time.sleep(4)
                else:
                    taskLogger({"status" : "error","message":"Failed to request challenge task - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(4)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to request challenge task - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(5)

        solvedToken=self.getSolutionMon(dataDomeTask)
        if (solvedToken!= False):
            self.submitLoad["captcha"] = solvedToken
        else:
            self.requestSolutionMon()
    
    def getSolutionMon(self,dataDomeTask):
        endPoint = "https://api.capmonster.cloud/getTaskResult"
        payload = {
                    "clientKey":checkCapMonster(),
                    "taskId": dataDomeTask
                }
        timeoutThresh = 7
        timeoutCtr = 0
        while True:
            timeoutCtr+=1
            taskLogger({"status" : "process","message":"Solving captcha","prefix":self.prefix},self.taskId)
            try:
                response=requests.post(endPoint,data = json.dumps(payload))
                responseJson=json.loads(response.text)
                if (responseJson["status"]=="ready"):
                    solvedPayload=responseJson
                    taskLogger({"status" : "success","message":"Challenge solved","prefix":self.prefix},self.taskId)
                    break
                time.sleep(5)
                if (timeoutCtr == timeoutThresh):
                    taskLogger({"status" : "error","message":"Timeout solving, restarting captcha service","prefix":self.prefix},self.taskId)
                    return False
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed solving poll - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(7)
        return solvedPayload['solution']['gRecaptchaResponse']


    def submit(self):
       
        self.submitLoad = {
            "id" : self.raffId,
            "mint_address" :self.wallet
        }

        self.requestSolutionMon()

        retryCount = 0
        retryTreshold = 3
        self.session.headers['Referer'] = 'https://www.superful.xyz/project/outside-yc/wallet_submission/outside-yacht-club-early-access'
        while True:
            if (retryCount >= retryTreshold):
                taskLogger({"status" : "error","message":"Exceeded max of {} retries, killing task!".format(retryTreshold),"prefix":self.prefix},self.taskId)
                break
            try:
                taskLogger({"status" : "process","message":"Submitting entry","prefix":self.prefix},self.taskId)
                response = self.session.post("https://www.superful.xyz/superful-api/v1/project/event/register",data = json.dumps(self.submitLoad),allow_redirects = True)
                if (response.status_code ==200):
                    updateTitleCall.addSuccess()
                    taskLogger({"status" : "success","message":"Succesfully submitted entry","prefix":self.prefix},self.taskId)
                    taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"Superful",'statusMessage':'Successfully submitted entry','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':None,'twitterProj':self.twitterReq[0],'discordProj':self.discordReq,'image':self.image}
                    webhookLog(taskObject,self.session)  
                    break
                else: #extract the error message
                        responseData = json.loads(response.text)
                        details = responseData['details']
                        updateTitleCall.addFail()
                       
                        if (details == None):
                            resMsg = "Undefined Error"
                        else:
                            resMsg = details
                        taskLogger({"status" : "error","message":"Failed submitting entry - {}".format(resMsg),"prefix":self.prefix},self.taskId)
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"Superful",'statusMessage':'Failed submitting entry','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':resMsg,'twitterProj':self.twitterReq[0],'discordProj':self.discordReq,'image':self.image}
                        webhookLog(taskObject,self.session)  
                        retryCount = 3
                        break
            except Exception as e:
                updateTitleCall.addFail()
                taskLogger({"status" : "error","message":"Failed submitting entry - {}!".format(e),"prefix":self.prefix},self.taskId)
                retryCount += 1
                self.requestSolutionMon()

        if (self.transferTask!=None):
            forceTransfer = self.transferTask['forceTransfer']
            if (retryCount >= retryTreshold and forceTransfer == False):
                taskLogger({"status" : "error","message":"Superful Chain task killed, force transfer is not active","prefix":self.prefix},self.taskId)
                return False
            return self.transfer()
           
    def verify(self):
        pageSize = 100
        endpoint = "https://www.superful.xyz/superful-api/v1/project/event/submissions?type=raffle&page=1&page_size={}&status=joined".format(pageSize)
        _,_,_,_,projectUser,_,slug = self.targetUrl.split("/")

        while True:
            taskLogger({"status" : "process","message":"Verifying entry","prefix":self.prefix},self.taskId)
            response = self.session.get(endpoint)
            if (response.status_code == 200):
                responseData = json.loads(response.text)
                break
            else:
                taskLogger({"status" : "process","message":"Failed verifying entry - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                time.sleep(3)
        resultsArr = responseData['results']
        status = "notFound"
        for r in range(0,len(resultsArr)):
            if (resultsArr[r]['event_slug'] == slug):
                status = resultsArr[r]['status']
                break
        
        if (status == "notFound"):
            taskLogger({"status" : "error","message":"Entry not found".format(self.twitterReq[0]),"prefix":self.prefix},self.taskId)
            return False
        elif (status == "pending"):
            taskLogger({"status" : "success","message":"Verified Entry".format(self.twitterReq[0]),"prefix":self.prefix},self.taskId)
            return True
        elif (status == "won" or status == "selected"):
            updateTitleCall.addSuccess()
            taskLogger({"status" : "success","message":"Won raffle!","prefix":self.prefix},self.taskId)
            taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"SuperfulWin",'statusMessage':'🏆 Won Raffle 🏆','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"You were selected!",'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
            webhookLog(taskObject,self.session)
            return True 
        elif (status == "lost"):
            updateTitleCall.addFail()
            taskLogger({"status" : "error","message":"Lost raffle!","prefix":self.prefix},self.taskId)
            return True #we don't want to run the next modules
            
        else:
            taskLogger({"status" : "warn","message":"Undefined status - {}".format(status),"prefix":self.prefix},self.taskId)
            taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"Superful",'statusMessage':'Unknown response','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"Undefined status - {}".format(status),'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
            webhookLog(taskObject,self.session)
            return True 


    def twitterMethod(self):
        if (self.password == "api"):
            auth= tweepy.auth.OAuthHandler(self.consumerKey, self.consumerSecret)
            auth.set_access_token(self.accessToken, self.accessTokenSecret)
            api=tweepy.API(auth,retry_count=5,retry_delay=1,retry_errors=set([401, 404, 500, 503]))
            taskLogger({"status" : "process","message":"Following account - @{}".format(self.twitterReq[0]),"prefix":self.prefix},self.taskId)
            api.create_friendship(screen_name=self.twitterReq[0])
            taskLogger({"status" : "success","message":"{} followed account - @{}".format(self.twitterToken,self.twitterReq[0]),"prefix":self.prefix},self.taskId)
            return True
        else: #manually login 
            if (fileBrowser(self.twitterToken) == False): #profile not found ,save cookie here
                res,message = browserTask(self.twitterToken,self.password,self.discordToken,self.twitterReq,self.prefix,self.taskId,self.session,self.mode)
                if (res!= True):
                    taskObject = {'url':self.targetUrl,'name':self.targetUrl,'status': "error",'taskType':"Superful",'statusMessage':'Failed twitter follow','wallet':str(self.wallet),'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':"https://pbs.twimg.com/profile_images/1505785782002339840/mgeaHOqx_400x400.jpg"}
                    webhookLog(taskObject,self.session)
                    return False
            res,message = followTwitter(self.twitterToken,self.twitterReq,self.session,self.prefix,self.taskId)
            if (res!= True):
                taskObject = {'url':self.targetUrl,'name':self.targetUrl,'status': "error",'taskType':"Superful",'statusMessage':'Failed twitter follow','wallet':str(self.wallet),'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':"https://pbs.twimg.com/profile_images/1505785782002339840/mgeaHOqx_400x400.jpg"}
                webhookLog(taskObject,self.session)
            return res
        
    
    def getNonce(self):
        taskLogger({"status" : "process","message":"Fetching Nonce","prefix":"({},{}) GWEI".format(self.transferTask['maxGasFee'],self.transferTask['maxPriorityFee'])},self.taskId)
        try:
            return web3Connection.eth.get_transaction_count(Web3.toChecksumAddress(self.wallet))
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed fetching nonce - {}".format(str(e)),"prefix":"({},{}) GWEI".format( self.transferTask['maxGasFee'], self.transferTask['maxPriorityFee'])},self.taskId)
            time.sleep(1)
            self.getNonce()

    def transfer(self):
        nextWallet = self.transferTask['nextWallet']
        maxGasFee = self.transferTask['maxGasFee']
        maxPriorityFee = self.transferTask['maxPriorityFee']
        amount = web3Connection.fromWei(web3Connection.eth.get_balance(Web3.toChecksumAddress(self.wallet)) - web3Connection.toWei(maxGasFee,'gwei')*21000,'ether')
        taskLogger({"status" : "process","message":"Calculated max Eth transfer :{}E".format(amount),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)

        body = {
            'nonce' : self.getNonce(),
            'to' : nextWallet,
            'value' : web3Connection.toWei(amount,'ether'),
            'gas' : 21000,
            'maxFeePerGas': web3Connection.toWei(maxGasFee,'gwei'),
            'maxPriorityFeePerGas' : web3Connection.toWei(maxPriorityFee,'gwei'),
            'chainId':1
        }
        try:
            taskLogger({"status" : "warn","message":"Signing Transaction","prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
            signedTransaction = web3Connection.eth.account.sign_transaction(body,self.walletKey)
            taskLogger({"status" : "process","message":"Submitting Transaction [{} ETH -> {}]".format(amount,nextWallet),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
            result = web3Connection.eth.send_raw_transaction(signedTransaction.rawTransaction)
            statusTrack = web3Connection.eth.wait_for_transaction_receipt(result,timeout=300)
            if (statusTrack['status']==1): #successful transfer 
                taskLogger({"status" : "success","message":"Succesful Transaction [{} ETH -> {}]".format(amount,nextWallet),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
                return True
            else: 
                taskLogger({"status" : "error","message":"Failed Transaction [{} ETH -> {}]".format(amount,nextWallet),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
                taskObject = {"status": "revert","taskType": "Superful Chain - Reverted","receiver": nextWallet,"value": 0,"gas" : 21000 , "mode": "Superful Chain" , "wallet" : self.wallet , "reason":"Unespecified" , "maxFee" :str(maxGasFee) + "," + str(maxPriorityFee)}
                webhookLog(taskObject,self.session)
                return False
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed Transaction [{} ETH -> {}] - {}".format(amount,nextWallet,str(e)),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
            taskObject = {"status": "revert","taskType": "Superful Chain - Reverted","receiver": nextWallet,"value": 0,"gas" : 21000 , "mode": "Superful Chain" , "wallet" : self.wallet , "reason":str(e) , "maxFee" :str(maxGasFee) + "," + str(maxPriorityFee)}
            webhookLog(taskObject,self.session)
            return False
from datetime import datetime
import os,json,time,requests,re,string,names,random,tweepy,cloudscraper
from socket import timeout
from xmlrpc.client import FastMarshaller
from web3 import Web3
from app_modules.taskLogger import taskLogger
from app_modules.discordLog import webhookLog
from app_modules.apiModules import nodeProvider,etherScanApi,alternative,checkNode,capKey,cfNode,checkCapMonster
from app_modules.titleLog import classUpdateTitle
from app_modules.proxy import proxy_choice
from modules.twitter import browserTask,fileBrowser,followTwitter,connectTwitterHeyMint
from modules.discordModule import inviteTask
from eth_account.messages import encode_defunct
from bs4 import BeautifulSoup
import dateutil.parser as parser
try:
    from fake_useragent import UserAgent
except:
    pass
ua = UserAgent()


global web3Connection
updateTitleCall=classUpdateTitle("HeyMint")
siteKey = "6Lf9ZCYgAAAAANbod3nwYtteIUlNGmrmoKnwu5uW"
workingProxy = []

class heyMint():
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
       self.issuedTime = None

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
        self.getToken()
        self.fetchRaffleInfo()
        verifiedEntry = self.verify()
        if (self.mode=="check"):
            return
        if (verifiedEntry == True):
            return        
        if (fileBrowser(self.twitterToken) == False): #profile not found ,save cookie here
            res,message = browserTask(self.twitterToken,self.password,self.discordToken,self.twitterReq,self.prefix,self.taskId,self.session,self.mode+"local")
            if (res==False):
                taskLogger({"status" : "error","message":"Failed to login to Twitter , killing task - {}".format(message),"prefix":self.prefix},self.taskId)
                updateTitleCall.addFail()
                return
        self.twitterLogin()
        self.login()

        if ("disconnect" in self.mode):
            '''res = self.disconnect()
            if (res):
                updateTitleCall.addSuccess()'''
            print("Not implemented yet")
        elif ("connect" in self.mode):
            res,message = self.checkConnected()
            if (message != "connected-before"):
                #res,message = browserTask(self.twitterToken,self.password,self.discordToken,"twitterAcc",self.prefix,self.taskId,self.session,self.mode)
                if (res == True):
                    taskObject = {'url':self.targetUrl,'name':"@{}".format(self.twitterToken),'status': "success",'taskType':"HeyMint Connect",'statusMessage':'Successfully connected socials','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"None",'twitterProj':"none",'discordProj':"none",'image':"https://cdn.discordapp.com/attachments/837783679810928671/999220088903319612/AXZE_PFP_FIX.jpg"}
                    updateTitleCall.addSuccess()
                else:
                    taskObject = {'url':self.targetUrl,'name':"@{}".format(self.twitterToken),'status': "error",'taskType':"HeyMint Connect",'statusMessage':'Failed connecting socials','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':"none",'discordProj':"none",'image':"https://cdn.discordapp.com/attachments/837783679810928671/999220088903319612/AXZE_PFP_FIX.jpg"}
                    updateTitleCall.addFail()
                webhookLog(taskObject,self.session)  
            else:
                updateTitleCall.addSuccess()

        else:
            if (verifiedEntry == False):
                if (self.discordReq != "None"):          #fulfill requirements
                    if (self.discordToken == "Unspecified"):
                        taskLogger({"status" : "error","message":"No discord token supplied for task but joining server is required!","prefix":self.prefix},self.taskId)
                    else:
                        inviteTaskInstance = inviteTask(self.discordToken,self.discordReq,self.proxy,self.taskId,self.discordMode,self.reactParam)
                        inviteTaskInstance.main()
                if (not self.twitterMethod()):
                    updateTitleCall.addFail()
                    return 
                self.submit()

    def disconnect(self):
        orderArr = ['Twitter','Discord']
        endpointArr = ['https://www.HeyMint.xyz/HeyMint-api/v1/account/login/twitter/v1/revoke','https://www.HeyMint.xyz/HeyMint-api/v1/account/login/discord/revoke']        #400 status = account connection not found
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

    def getToken(self):
        endpoint = "https://heymint.xyz/api/auth/csrf"
        while (True):
            try:
                taskLogger({"status" : "process","message":"Initializing token","prefix":self.prefix},self.taskId)
                response = self.session.get(endpoint)
                if (response.status_code == 200):
                    message = json.loads(response.text)
                    self.csrfToken = message['csrfToken']
                    issuedTime = str(response.headers['date'])
                    #issuedTime = datetime.now()
                    #date = parser.parse(issuedTime)
                    #date = date.isoformat()
                    #print(date)
                    #self.issuedTime = str(date).replace('+00:00', 'Z')
                    #self.issuedTime = issuedTime.isoformat()
                    date = datetime.utcnow()
                    date = date.isoformat()
                    date = date[:-3]
                    self.issuedTime = date+"Z"
                    taskLogger({"status" : "success","message":"Initialized token","prefix":self.prefix},self.taskId)
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed initializing token - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(2)
                    self.rotateProxy()
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed initializing token - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)
                self.rotateProxy()

    def twitterLogin(self):
        self.session.headers['content-type'] = 'application/json'
        endpoint = "https://heymint.xyz/api/auth/signin/twitter"
        data = {
            "csrfToken":self.csrfToken,
            "callbackUrl":self.targetUrl,
            "json":"true"
        }
        while (True):
            try:
                taskLogger({"status" : "process","message":"Fetching Twitter login","prefix":self.prefix},self.taskId)
                response = self.session.post(endpoint,data = json.dumps(data))
                if (response.status_code == 200):
                    responseData = json.loads(response.text)
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed fetching Twitter login - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(2)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed fetching Twitter login - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)
        
        twitterEnd = responseData['url']
        res,message = connectTwitterHeyMint(self.twitterToken,self.session,self.prefix,self.taskId,twitterEnd)

        
    def login(self):
        message = '''heymint.xyz wants you to sign in with your Ethereum account:\n0xfA35DcBFFBcb4cA39F9667bC1272Fbba8F4497Fe\n\nSigning is the only way to prove that you are the owner of your wallet. It does not grant HeyMint permission to perform any transactions. Signing is safe and costs no gas.\n\nURI: https://heymint.xyz\nVersion: 1\nChain ID: 1\nNonce: 8c6868ba55077e181b55b4f742d92c60ca8fb2c7fc5afe6c8519e2ebd2b5ceae\nIssued At: 2022-10-22T04:49:52.437Z'''
        message = '''heymint.xyz wants you to sign in with your Ethereum account:\n{}\n\nSigning is the only way to prove that you are the owner of your wallet. It does not grant HeyMint permission to perform any transactions. Signing is safe and costs no gas.\n\nURI: https://heymint.xyz\nVersion: 1\nChain ID: 1\nNonce: {}\nIssued At: {}'''.format(web3Connection.toChecksumAddress(self.wallet),self.csrfToken,self.issuedTime)
        message = encode_defunct(text=message)
        taskLogger({"status" : "process","message":"Signing session","prefix":self.prefix},self.taskId)
        signed_message = web3Connection.eth.account.sign_message(message, private_key=self.walletKey)
        self.signature = web3Connection.toHex(signed_message['signature'])
        taskLogger({"status" : "success","message":"Signed session","prefix":self.prefix},self.taskId)
        self.authenticate()

    def authenticate(self):
        self.session.headers['content-type'] = "application/json; charset=utf-8"
        messagePayload = '''{"statement":"Signing is the only way to prove that you are the owner of your wallet. It does not grant HeyMint permission to perform any transactions. Signing is safe and costs no gas.","domain":"heymint.xyz","address":'''+"\"{}\"".format(web3Connection.toChecksumAddress(self.wallet))+''',"uri":"https://heymint.xyz","version":"1","chainId":1,"nonce":'''+'''\"{}\"'''.format(self.csrfToken)+''',"issuedAt":"'''+self.issuedTime+'''\"}'''      
        while (True):
            payload = {
                    "message":messagePayload,
                    "redirect":"false",
                    "signature": self.signature,
                    "csrfToken":self.csrfToken,
                    "callbackUrl":self.targetUrl,
                    "json":"true"
            }
            try:
                taskLogger({"status" : "process","message":"Logging in","prefix":self.prefix},self.taskId)
                response = self.session.post("https://heymint.xyz/api/auth/callback/credentials?blockchain=ETH",data = json.dumps(payload))
                if (response.status_code == 200):
                    responseJson = json.loads(response.text)
                    if ("error" not in responseJson['url']):
                        taskLogger({"status" : "success","message":"Succesfully logged in","prefix":self.prefix},self.taskId)
                        break
                    else:
                        taskLogger({"status" : "error","message":"Failed login - {}".format(responseJson['url']),"prefix":self.prefix},self.taskId)
                        time.sleep(3)
                else:
                    taskLogger({"status" : "error","message":"Failed login - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed login - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)

    def fetchRaffleInfo(self):
        endpoint = self.targetUrl
        while True:
            try:
                response = self.session.get(endpoint)
                if (response.status_code == 200):
                    responseData = response.text
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
            soup = BeautifulSoup(responseData,'html.parser')
            twitterLinks = soup.find_all('a',{'class':'font-medium text-primary-500 no-underline'})
            twitterArr = []
            for twitterLink in twitterLinks:
                twitterUser = twitterLink['href'].split("https://twitter.com/intent/user?screen_name=")[1]
                twitterArr.append(twitterUser)
            
            self.twitterReq = twitterArr
            self.image = "https://heymint.xyz"+soup.find('img',{'class':"rounded-2xl"})['src']
            #self.name = soup.find('h1',{'class':"font-bold text-3xl pt-5"}).text
            scriptDat = soup.find("script",{"id":"__NEXT_DATA__"})
            raffleJson = json.loads(scriptDat.text)
            self.name = raffleJson['props']['pageProps']['title']
            self.raffId = raffleJson['props']['pageProps']['project']['id']
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
        endpoint = "https://heymint.xyz/api/trpc/entry.create?batch=1"
    
        self.submitLoad = {"0":{"json":{"projectId":self.raffId,"collabId":None,"email":"","shareEmail":False,"responses":[],"password":"","mintWalletId":None,"assetWalletId":None},"meta":{"values":{"mintWalletId":["undefined"],"assetWalletId":["undefined"]}}}}
        retryCount = 0
        retryTreshold = 3
        self.session.headers['Referer'] = self.targetUrl
        while True:
            if (retryCount >= retryTreshold):
                taskLogger({"status" : "error","message":"Exceeded max of {} retries, killing task!".format(retryTreshold),"prefix":self.prefix},self.taskId)
                break
            try:
                taskLogger({"status" : "process","message":"Submitting entry","prefix":self.prefix},self.taskId)
                response = self.session.post(endpoint,data = json.dumps(self.submitLoad),allow_redirects = True)
                if (response.status_code ==200):
                    responseJson = json.loads(response.text)
                    status = responseJson[0]['result']['data']['json']['status']
                    if (status == "Successfully created entry" or "entryId" in responseJson[0]['result']['data']['json']):
                        updateTitleCall.addSuccess()
                        taskLogger({"status" : "success","message":"Succesfully submitted entry","prefix":self.prefix},self.taskId)
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"HeyMint",'statusMessage':'Successfully submitted entry','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':None,'twitterProj':self.twitterReq[0],'discordProj':self.discordReq,'image':self.image}
                        webhookLog(taskObject,self.session)  
                        break
                    else:
                        taskLogger({"status" : "error","message":"Failed submitting entry - {}".format(status),"prefix":self.prefix},self.taskId)
                        time.sleep(3)
                else: #extract the error message
                        responseData = json.loads(response.text)
                        details = responseData['details']
                        updateTitleCall.addFail()
                       
                        if (details == None):
                            resMsg = "Undefined Error"
                        else:
                            resMsg = details
                        taskLogger({"status" : "error","message":"Failed submitting entry - {}".format(resMsg),"prefix":self.prefix},self.taskId)
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"HeyMint",'statusMessage':'Failed submitting entry','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':resMsg,'twitterProj':self.twitterReq[0],'discordProj':self.discordReq,'image':self.image}
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
                taskLogger({"status" : "error","message":"HeyMint Chain task killed, force transfer is not active","prefix":self.prefix},self.taskId)
                return False
            return self.transfer()
           
    def verify(self):
        pageSize = 100
        endpoint = "https://heymint.xyz/api/trpc/entry.verify-status?batch=1"
        payload = {"0":{"json":{"walletAddress":self.wallet.lower(),"projectId":self.raffId}}}
        while True:
            taskLogger({"status" : "process","message":"Verifying entry","prefix":self.prefix},self.taskId)
            response = self.session.post(endpoint,data = json.dumps(payload))
            if (response.status_code == 200):
                responseData = json.loads(response.text)
                break
            else:
                taskLogger({"status" : "process","message":"Failed verifying entry - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                time.sleep(3)
       
        responseData = responseData[0]['result']['data']['json']
        if (responseData == None):
            taskLogger({"status" : "error","message":"Entry not found".format(self.twitterReq[0]),"prefix":self.prefix},self.taskId)
            return False
        status = responseData['status'].lower()
        if (status == "pending"):
            taskLogger({"status" : "success","message":"Verified Entry".format(self.twitterReq[0]),"prefix":self.prefix},self.taskId)
            return True
        elif (status == "accepted" or status == "selected" or "won"):
            updateTitleCall.addSuccess()
            taskLogger({"status" : "success","message":"Won raffle!","prefix":self.prefix},self.taskId)
            taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"HeyMintWin",'statusMessage':'🏆 Won Raffle 🏆','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"You were selected!",'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
            webhookLog(taskObject,self.session)
            return True 
        elif (status == "rejected"):
            updateTitleCall.addFail()
            taskLogger({"status" : "error","message":"Lost raffle!","prefix":self.prefix},self.taskId)
            return True #we don't want to run the next modules
            
        else:
            taskLogger({"status" : "warn","message":"Undefined status - {}".format(status),"prefix":self.prefix},self.taskId)
            taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"HeyMint",'statusMessage':'Unknown response','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"Undefined status - {}".format(status),'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
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
                    taskObject = {'url':self.targetUrl,'name':self.targetUrl,'status': "error",'taskType':"HeyMint",'statusMessage':'Failed twitter follow','wallet':str(self.wallet),'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':"https://pbs.twimg.com/profile_images/1505785782002339840/mgeaHOqx_400x400.jpg"}
                    webhookLog(taskObject,self.session)
                    return False
            res,message = followTwitter(self.twitterToken,self.twitterReq,self.session,self.prefix,self.taskId)
            if (res!= True):
                taskObject = {'url':self.targetUrl,'name':self.targetUrl,'status': "error",'taskType':"HeyMint",'statusMessage':'Failed twitter follow','wallet':str(self.wallet),'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':"https://pbs.twimg.com/profile_images/1505785782002339840/mgeaHOqx_400x400.jpg"}
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
                taskObject = {"status": "revert","taskType": "HeyMint Chain - Reverted","receiver": nextWallet,"value": 0,"gas" : 21000 , "mode": "HeyMint Chain" , "wallet" : self.wallet , "reason":"Unespecified" , "maxFee" :str(maxGasFee) + "," + str(maxPriorityFee)}
                webhookLog(taskObject,self.session)
                return False
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed Transaction [{} ETH -> {}] - {}".format(amount,nextWallet,str(e)),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
            taskObject = {"status": "revert","taskType": "HeyMint Chain - Reverted","receiver": nextWallet,"value": 0,"gas" : 21000 , "mode": "HeyMint Chain" , "wallet" : self.wallet , "reason":str(e) , "maxFee" :str(maxGasFee) + "," + str(maxPriorityFee)}
            webhookLog(taskObject,self.session)
            return False
    



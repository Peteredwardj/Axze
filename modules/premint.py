import os,json,time,requests,re,string,names,random,tweepy,cloudscraper
from socket import timeout
from xmlrpc.client import FastMarshaller
from web3 import Web3
from app_modules.taskLogger import taskLogger
from app_modules.discordLog import webhookLog
from app_modules.apiModules import nodeProvider,etherScanApi,alternative,checkNode,capKey,cfNode,checkCapMonster
from app_modules.titleLog import classUpdateTitle
from app_modules.proxy import proxy_choice
from modules.twitter import browserTask,fileBrowser,followTwitter,connectTwitter,connectDiscordRequest,disconnectSocial,likeTweet
from modules.discordModule import inviteTask
from eth_account.messages import encode_defunct
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
ua = UserAgent()


global web3Connection
stagger = 0
updateTitleCall=classUpdateTitle("Premint")
siteKey = "6Lf9yOodAAAAADyXy9cQncsLqD9Gl4NCBx3JCR_x"
workingProxy = []

class premint():
    def __init__(self,targetUrl,wallet,walletKey,twitterToken,twitterPassword,discordToken,accessToken,accessTokenSecret,consumerKey,consumerSecret,mode,taskId,transferTask,customField,discordMode="default",reactParam =None):
       self.targetUrl = targetUrl
       self.wallet = wallet.lower()
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

    def connect(self):
        global web3Connection
        taskLogger({"status" : "process","message":"Connecting to node","prefix":self.prefix},self.taskId)
        web3Connection = Web3(Web3.HTTPProvider(cfNode))
        taskLogger({"status":"success", "message": "Connected to node","prefix":self.prefix},self.taskId)
        updateTitleCall.addRun()
        return self.initialize()

    def rotateProxy(self,retry=False):
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
    
    def refreshSession(self,retry=False):        
        self.rotateProxy(retry)    
        self.session.cookies.clear()
        while True:
            taskLogger({"status" : "process","message":"Initializing session","prefix":self.prefix},self.taskId)

            try:
                response = self.session.get("http://www.premint.xyz/")
                if (response.status_code == 200):
                    matchedToken=re.findall("CSRF_TOKEN = (.*)",response.text)
                    matchedToken = matchedToken[0]
                    matchedToken = matchedToken.replace("\'","")
                    matchedToken = matchedToken.replace(";","")
                    #self.csrfToken = response.cookies['csrftoken']
                    self.csrfToken = matchedToken
                    self.session.headers['X-CSRFToken'] = self.csrfToken
                    taskLogger({"status" : "process","message":"Initialized session","prefix":self.prefix},self.taskId)
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed initializing session - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    self.rotateProxy()
                    #time.sleep(5)
                    
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed initializing session - {}".format(e),"prefix":self.prefix},self.taskId)
                self.rotateProxy()
           
                time.sleep(5)


    def initialize(self):   
        global stagger 
        '''while True:
            if (stagger <= 5):
                break
            else:
                #taskLogger({"status" : "process","message":"Waiting for stagger start","prefix":self.prefix},self.taskId)
                time.sleep(3)'''

        stagger += 1
        self.refreshSession()
        if (self.mode == "check"):
            self.verify()
        elif (self.mode == "connect" or self.mode == "connect-local"):
            self.register()
            self.login()
            res,message = self.checkConnected()
            if (message != "connected-before"):
                #res,message = browserTask(self.twitterToken,self.password,self.discordToken,"twitterAcc",self.prefix,self.taskId,self.session,self.mode)
                if (res == True):
                    taskObject = {'url':self.targetUrl,'name':"@{}".format(self.twitterToken),'status': "success",'taskType':"Premint Connect",'statusMessage':'Successfully connected socials','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"None",'twitterProj':"none",'discordProj':"none",'image':"https://cdn.discordapp.com/attachments/837783679810928671/999220088903319612/AXZE_PFP_FIX.jpg"}
                    updateTitleCall.addSuccess()
                else:
                    taskObject = {'url':self.targetUrl,'name':"@{}".format(self.twitterToken),'status': "error",'taskType':"Premint Connect",'statusMessage':'Failed connecting socials','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':"none",'discordProj':"none",'image':"https://cdn.discordapp.com/attachments/837783679810928671/999220088903319612/AXZE_PFP_FIX.jpg"}
                    updateTitleCall.addFail()
                webhookLog(taskObject,self.session)  
            else:
                updateTitleCall.addSuccess()

        elif("disconnect" in self.mode):
            self.prefix = '@-'
            self.register()
            self.login()
            res,message = disconnectSocial(self.session,self.prefix,self.taskId)
            if (res == True):
                updateTitleCall.addSuccess()
            else:
                taskObject = {'url':self.targetUrl,'name':"@{}".format(self.twitterToken),'status': "error",'taskType':"Premint Disconnect",'statusMessage':'Failed disconnecting socials','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':"none",'discordProj':"none",'image':"https://cdn.discordapp.com/attachments/837783679810928671/999220088903319612/AXZE_PFP_FIX.jpg"}
                updateTitleCall.addFail()
        else:
            if (self.verify()):
                return True
            self.register() #Account check
            if (self.proceed):
                time.sleep(2)
                self.login()
                return self.scrape()
        

    def register(self): #check if wallet already exist , if not -> register
        payload = {"username":str(self.wallet).lower()}
        header = {"referer": "https://www.premint.xyz/v1/login_api/"}
        while (True):
            try:
                taskLogger({"status" : "process","message":"Checking Premint account","prefix":self.prefix},self.taskId)
                response = self.session.post("https://www.premint.xyz/v1/signup_api/",data = payload , headers = header)
                if (response.status_code == 200):
                    responseJson = json.loads(response.text)
                    proceed = responseJson['success']
                    if (proceed):
                        taskLogger({"status" : "success","message":"Succesfully registered Premint account!","prefix":self.prefix},self.taskId)
                        break
                    else: #fail
                        responseJsonStr = str(responseJson)
                        if ("A user with that username already exists." in responseJsonStr):
                            taskLogger({"status" : "success","message":"Account already exist for wallet","prefix":self.prefix},self.taskId)
                            break
                        else:
                            taskLogger({"status" : "success","message":"Checking Premint account failure - {}".format(responseJsonStr),"prefix":self.prefix},self.taskId)
                            time.sleep(3)
                else:
                    taskLogger({"status" : "error","message":"Failed Premint account check - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(2)
                    break
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed Premint account check  - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)
                break
            
    def checkConnected(self):
        twitterString = "Connect Twitter"
        discordString = "Connect Discord"
        while (True):
            try:
                header = {"referer": "https://www.premint.xyz/v1/login_api/"}
                taskLogger({"status" : "process","message":"Checking if socials are connected","prefix":self.prefix},self.taskId)
                response = self.session.get("https://www.premint.xyz/profile/",headers = header)
                if (response.status_code == 200):
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed socials account check - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(2)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed socials account check  - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)
            
        if (twitterString not in response.text):
            if (discordString in response.text):
                if (self.discordToken == "Unspecified"):
                    taskLogger({"status" : "success","message":"Twitter connected and discord token is not supplied, skipping account!","prefix":self.prefix},self.taskId)
                    return True,"connected-before"
            else:
                taskLogger({"status" : "success","message":"All socials connected, skipping account!","prefix":self.prefix},self.taskId)
                return True,"connected-before"

        if (twitterString in response.text):
            if (fileBrowser(self.twitterToken) == False): #profile not found ,save cookie here
                res,message = browserTask(self.twitterToken,self.password,self.discordToken,"axzeio",self.prefix,self.taskId,self.session,self.mode)
                if (res!= True):
                    taskLogger({"status" : "error","message":"Failed Twitter setup - {}".format(message),"prefix":self.prefix},self.taskId)
                    return False,"Failed Twitter setup - {}".format(message)
            taskLogger({"status" : "warn","message":"Twitter is not connected!","prefix":self.prefix},self.taskId)
            res,message = connectTwitter(self.twitterToken,self.session,self.prefix,self.taskId)

        if (discordString in response.text and self.discordToken!="Unspecified"):
            taskLogger({"status" : "warn","message":"Discord is not connected and token is supplied in excel file!","prefix":self.prefix},self.taskId)
            res,message = connectDiscordRequest(self.discordToken,self.prefix,self.session,self.taskId)

        return res,message

                    
    def login(self):
        global workingProxy
        while (True):
            try:
                taskLogger({"status" : "process","message":"Fetching session","prefix":self.prefix},self.taskId)
                response = self.session.get("http://www.premint.xyz/v1/login_api/")
                if (response.status_code == 200):
                    responseJson = json.loads(response.text)
                    proceed = responseJson['success']
                    if(proceed):
                        self.nonce = responseJson['data']
                        break
                else:
                    taskLogger({"status" : "error","message":"Failed fetching session - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(2)
                    self.refreshSession(True)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed fetching session - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)

        taskLogger({"status" : "success","message":"Fetched session","prefix":self.prefix},self.taskId)
        workingProxy.append(self.proxObj)
        msg = "Welcome to PREMINT!" + "\n\n" + "Signing is the only way we can truly know \nthat you are the owner of the wallet you \nare connecting. Signing is a safe, gas-less \ntransaction that does not in any way give \nPREMINT permission to perform any \ntransactions with your wallet." + "\n\n"
        msg = msg+"Wallet address:" + "\n" + self.wallet + "\n\n" +"Nonce: " + self.nonce
        message = encode_defunct(text=msg)
        taskLogger({"status" : "process","message":"Signing session","prefix":self.prefix},self.taskId)
        signed_message = web3Connection.eth.account.sign_message(message, private_key=self.walletKey)
        self.signature = web3Connection.toHex(signed_message['signature'])
        taskLogger({"status" : "success","message":"Signed session","prefix":self.prefix},self.taskId)
        self.authenticate()

    def authenticate(self):
        while (True):
            payload = {
                    "web3provider":"metamask",
                    "address":self.wallet,
                    "signature":self.signature
            }
            self.session.headers['X-CSRFToken'] = self.csrfToken
            self.session.headers['referer'] = self.targetUrl

            try:
                taskLogger({"status" : "process","message":"Logging in","prefix":self.prefix},self.taskId)
                response = self.session.post("https://www.premint.xyz/v1/login_api/",data = payload)
                if (response.status_code == 200):
                    responseJson = json.loads(response.text)
                    proceed = responseJson['success']
                    if(proceed):
                        taskLogger({"status" : "success","message":"Succesfully logged in","prefix":self.prefix},self.taskId)
                        break
                    else:
                        taskLogger({"status" : "error","message":"Failed login - {}".format(responseJson['error']),"prefix":self.prefix},self.taskId)
                        time.sleep(2)
                        self.refreshSession()
                else:
                    taskLogger({"status" : "error","message":"Failed login - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed login - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)

    def scrape(self): #scrape premint info 
        global stagger
        responseData = None
        retryCount = 0
        retryThreshold = 2
        while True:
            if (retryCount > retryThreshold):
                taskLogger({"status" : "error","message":"Exceeded max of {} retries, killing task!".format(retryThreshold),"prefix":self.prefix},self.taskId)
                break
            try:
                taskLogger({"status" : "success","message":"Fetching page","prefix":self.prefix},self.taskId)
                response = self.session.get(self.targetUrl)
                if (response.status_code == 200):
                    responseData = response.text
                    taskLogger({"status" : "success","message":"Fetched page","prefix":self.prefix},self.taskId)
                    try:
                        soup = BeautifulSoup(responseData, "html.parser")
                        tokRes = soup.find("input",{"name":"csrfmiddlewaretoken"})
                        self.csrfToken = tokRes['value']
                        break
                    except Exception as e:
                        retryCount +=1
                        errMsg = str(e)
                        if ("Cannot register until you connect accounts above" in responseData):
                            errMsg = "Disconnected Socials"
                        taskLogger({"status" : "error","message":"Failed fetching token - {}".format(errMsg),"prefix":self.prefix},self.taskId)
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"Premint",'statusMessage':'Failed fetching token','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"Failed fetching Token - {}".format(errMsg),'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
                        webhookLog(taskObject,self.session)  
                        time.sleep(3)
                else:
                    retryCount +=1
                    taskLogger({"status" : "error","message":"Failed fetching page - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(3)
            except Exception as e:
                retryCount +=1
                taskLogger({"status" : "error","message":"Failed fetching page - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)

        if (retryCount >= retryThreshold and self.transferTask!=None):
            forceTransfer = self.transferTask['forceTransfer']
            if (forceTransfer):
                taskLogger({"status" : "error","message":"Premint Chain task killed, force transfer is not active","prefix":self.prefix},self.taskId)
                return False
            else:
                return self.transfer()

        if ("class=\"g-recaptcha\"" in responseData):
            taskLogger({"status" : "process","message":"Captcha required","prefix":self.prefix},self.taskId)
            self.captchaReq = True
        else:
            pass
        
        #find params here 
        paramRes = soup.find("input",{"name":"params_field"})
        self.params = paramRes['value']

        #res = soup.find_all("li",{"class": "mt-1"}) #res = soup.find_all("a",{"class": "c-base-1 strong-700 text-underline"}) #returns links and roles
        res = soup.find_all("a",{'class':'c-base-1 strong-700 text-underline'})
        twitterUserArr = []
        for r in res:
            try:
                if ("status" in r['href']):
                    self.likeReq = r['href']
                    taskLogger({"status" : "process","message":"Found twitter like&RT requirements - {}".format(self.likeReq),"prefix":self.prefix},self.taskId)

                elif ("twitter" in r['href']):
                    taskLogger({"status" : "process","message":"Found twitter requirement - {}".format(r['href']),"prefix":self.prefix},self.taskId)
                    twitterUserArr.append(r['href'])
                    

                elif ("discord" in r['href']):
                    self.discordReq = r['href']
                    self.discordReq = self.discordReq.replace("https://discord.gg/","")
                    taskLogger({"status" : "process","message":"Found discord requirement - {}".format(self.discordReq),"prefix":self.prefix},self.taskId)
                    if (self.discordToken == "Unspecified"):
                        taskLogger({"status" : "error","message":"No discord token supplied for task but joining server is required!","prefix":self.prefix},self.taskId)
                        
                    else:
                        inviteTaskInstance = inviteTask(self.discordToken,self.discordReq,self.proxy,self.taskId,self.discordMode,self.reactParam)
                        inviteTaskInstance.main()
            except:
                pass
        
        self.twitterReq = twitterUserArr
        if (not self.twitterMethod()):
            return
        
        if (self.likeReq != "unspecified"):
            _,_,_,_,_,reqTweet = self.likeReq.split("/")
            res,message = likeTweet(self.twitterToken,reqTweet,self.session,self.prefix,self.taskId)
            if (res == False):
                taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"Premint - Twitter Like/RT",'statusMessage':'Failed liking/Rting Tweet','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"Failed liking/Rting tweet - {}".format(message),'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
                webhookLog(taskObject,self.session)  
                return

        res = soup.find("span",{"class":"strong c-black"})
        if (res!= None):
            self.minimumBalance = res.text
            taskLogger({"status" : "process","message":"Found required minimum ETH balance- {}".format(self.minimumBalance),"prefix":self.prefix},self.taskId)

        if (self.discordReq == None):
            taskLogger({"status" : "warn","message":"Could not extract discord invite, skipping","prefix":self.prefix},self.taskId)

        return self.submit()
        

    def requestSolutionMon(self):
        endPoint="https://api.capmonster.cloud/createTask"
        payload = {
                    "clientKey":checkCapMonster(),
                    "task":
                    {
                        "type":"NoCaptchaTask",
                        "websiteURL":self.targetUrl,
                        "websiteKey":"6Lf9yOodAAAAADyXy9cQncsLqD9Gl4NCBx3JCR_x"
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
        self.submitLoad["g-recaptcha-response"] =solvedToken
    
    def getSolutionMon(self,dataDomeTask):
        endPoint = "https://api.capmonster.cloud/getTaskResult"
        payload = {
                    "clientKey":checkCapMonster(),
                    "taskId": dataDomeTask
                }
        while True:
            
            taskLogger({"status" : "process","message":"Solving captcha","prefix":self.prefix},self.taskId)
            try:
                response=requests.post(endPoint,data = json.dumps(payload))
                responseJson=json.loads(response.text)
                if (responseJson["status"]=="ready"):
                    solvedPayload=responseJson
                    taskLogger({"status" : "success","message":"Challenge solved","prefix":self.prefix},self.taskId)
                    break
                time.sleep(5)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed solving poll - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(7)
        return solvedPayload['solution']['gRecaptchaResponse']
    
    def generateEmail(self):
        provider = [self.customField['content']]
        randomLen = random.randint(2,4)
        letters = string.ascii_lowercase
        randomLast= random.choice(letters)
        randomNumApp = ''.join(str(random.randint(1,9)) for i in range (randomLen))
        randomEmail = names.get_first_name()+randomLast+randomNumApp+"@{}".format(random.choice(provider))
        taskLogger({"status" : "success","message":"Generated email : {}".format(randomEmail),"prefix":self.prefix},self.taskId)
        return randomEmail

    def submit(self):
        global stagger 
        stagger-=1
        self.submitLoad = {
            "csrfmiddlewaretoken":self.csrfToken,
            "holdings_wallet" : self.wallet,
            "minting_wallet" :self.wallet,
            "params_field":self.params,  #"{\"regdone\":+\"1\"}"
            "registration-form-submit":""}

        '''if (self.mode == "default"):
            self.submitLoad["params_field"] = ""'''

        if (self.customField!= None):
            taskLogger({"status" : "process","message":"Setting custom field","prefix":self.prefix},self.taskId)

            if (self.customField['type'] == 'email'):
                toInput = self.generateEmail()

            self.submitLoad['custom_field'] = toInput

        if (self.captchaReq):
            self.requestSolutionMon()

        retryCount = 0
        retryTreshold = 3
        while True:
            if (retryCount >= retryTreshold):
                taskLogger({"status" : "error","message":"Exceeded max of {} retries, killing task!".format(retryTreshold),"prefix":self.prefix},self.taskId)
                break
            try:
                taskLogger({"status" : "process","message":"Submitting entry","prefix":self.prefix},self.taskId)
                response = self.session.post(self.targetUrl,data = self.submitLoad,allow_redirects = True)
                if (response.status_code ==200):
                    redirect = response.url
                    #if ("regpending" in redirect):
                    time.sleep(2.5)
                    if (self.verify()):#check if it is submitted
                        updateTitleCall.addSuccess()
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"Premint",'statusMessage':'Successfully submitted entry','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':None,'twitterProj':self.twitterReq[0],'discordProj':self.discordReq,'image':self.image}
                        webhookLog(taskObject,self.session)  
                        break
                    else: #extract the error message
                        updateTitleCall.addFail()
                        soup = BeautifulSoup(response.text, "html.parser")
                        res = soup.find("div",{"class":"alert alert-danger alert-dismissible fade show"})
                        if (res == None):
                            resMsg = "Undefined Error"
                        else:
                            resMsg = res.text
                        taskLogger({"status" : "error","message":"Failed submitting entry - {}".format(resMsg),"prefix":self.prefix},self.taskId)
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"Premint",'statusMessage':'Failed submitting entry','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':resMsg,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
                        webhookLog(taskObject,self.session)  
                        retryCount = 3
                        break
                    '''else:
                        updateTitleCall.addFail()
                        taskLogger({"status" : "error","message":"Failed submitting entry, redirect invalid - {}".format(response.url),"prefix":self.prefix},self.taskId)
                        time.sleep(3)'''
                else:
                    updateTitleCall.addFail()
                    taskLogger({"status" : "error","message":"Failed submitting entry - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    retryCount += 1
                    time.sleep(3)
            except Exception as e:
                updateTitleCall.addFail()
                taskLogger({"status" : "error","message":"Failed submitting entry - {}. Try to check requirements!".format(e),"prefix":self.prefix},self.taskId)
                retryCount += 1
                time.sleep(3)

        if (self.transferTask!=None):
            forceTransfer = self.transferTask['forceTransfer']
            if (retryCount >= retryTreshold and forceTransfer == False):
                taskLogger({"status" : "error","message":"Premint Chain task killed, force transfer is not active","prefix":self.prefix},self.taskId)
                return False
            return self.transfer()
           

    
    def verify(self):
        global stagger
        targetUrl = self.targetUrl

        if (self.targetUrl[-1] != "/"):
            targetUrl = self.targetUrl+"/verify"
        else:
            targetUrl = self.targetUrl+"verify"
        

        if (self.mode == "check" or self.first):
            #targetUrl = targetUrl + "/?wallet={}".format(self.wallet)
            targetUrl = targetUrl+"/?wallet={}".format(self.wallet)
            self.first = False

        while True:
            try:
                taskLogger({"status" : "process","message":"Verifying entry","prefix":self.prefix},self.taskId)
                response = self.session.get(targetUrl)
                if (response.status_code == 200):
                    responseData = response.text
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed verification - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed verification - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)

        soup = BeautifulSoup(responseData, "html.parser")
        res = soup.find("div",{"class":"heading heading-3 mb-3"})
        respMessage = res.text
        res = soup.find("img",{"class":"mt-0 bg-white border-white"})
        self.image = res['src']
        res = soup.find("h1",{"class":"heading heading-1"})
        self.name = res.text

        try:
            res = soup.find("div",{"class":"heading heading-1"})  
            respSymbol = res.text
        except:
            res = soup.find("div",{"class":"heading heading-1 mb-3"})  
            respSymbol = res.text

        if ("You aren't registered." in respMessage):
            taskLogger({"status" : "error","message":"Failed verification - {}".format("No entry found for wallet"),"prefix":self.prefix},self.taskId)
            self.proceed = True     
            return False
        elif ("You are registered." in respMessage or respSymbol == "👍"):
            taskLogger({"status" : "success","message":"Verified entry","prefix":self.prefix},self.taskId)
            stagger -= 1
            return True
        elif ("You were not selected!" in respMessage or respSymbol == "😢"): 
            updateTitleCall.addFail()
            taskLogger({"status" : "error","message":"Lost raffle","prefix":self.prefix},self.taskId)
            taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"Premint",'statusMessage':'😢 Lost Raffle 😢','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"You were not selected!",'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
            #webhookLog(taskObject,self.session) don't send lost raffle webhook
            stagger -= 1
            return True #we don't want to loop retry for a lost raffle
        elif ("You were selected!" in respMessage or respSymbol =="🏆"):
            updateTitleCall.addSuccess()
            taskLogger({"status" : "success","message":"Won raffle","prefix":self.prefix},self.taskId)
            taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"PremintWin",'statusMessage':'🏆 Won Raffle 🏆','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':"You were selected!",'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
            webhookLog(taskObject,self.session)
            stagger -=1 
            return True 
        else:
            taskLogger({"status" : "warn","message":"Unknown response - {}".format(respMessage),"prefix":self.prefix},self.taskId)
            taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"Premint",'statusMessage':'Unknown response','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':respMessage,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
            webhookLog(taskObject,self.session)
            self.proceed = True
            stagger -= 1
            return True

    def twitterMethod(self):
        for i in range (0,len(self.twitterReq)):
            self.twitterReq[i] = self.twitterReq[i].replace("https://twitter.com/","")
            #twitterAcc = (self.twitterReq).replace("https://twitter.com/","")
        if (self.password == "api"):
            auth= tweepy.auth.OAuthHandler(self.consumerKey, self.consumerSecret)
            auth.set_access_token(self.accessToken, self.accessTokenSecret)
            api=tweepy.API(auth,retry_count=5,retry_delay=1,retry_errors=set([401, 404, 500, 503]))
            taskLogger({"status" : "process","message":"Following account - @{}".format(self.twitterReq[i]),"prefix":self.prefix},self.taskId)
            api.create_friendship(screen_name=self.twitterReq[i])
            taskLogger({"status" : "success","message":"{} followed account - @{}".format(self.twitterToken,self.twitterReq[i]),"prefix":self.prefix},self.taskId)
            return True
        else: #manually login 
            if (fileBrowser(self.twitterToken) == False): #profile not found ,save cookie here
                res,message = browserTask(self.twitterToken,self.password,self.discordToken,self.twitterReq,self.prefix,self.taskId,self.session,self.mode)
                if (res!= True):
                    taskObject = {'url':self.targetUrl,'name':self.targetUrl,'status': "error",'taskType':"Premint",'statusMessage':'Failed twitter follow','wallet':str(self.wallet),'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':"https://pbs.twimg.com/profile_images/1505785782002339840/mgeaHOqx_400x400.jpg"}
                    webhookLog(taskObject,self.session)
                    return False
            res,message = followTwitter(self.twitterToken,self.twitterReq,self.session,self.prefix,self.taskId)
            if (res!= True):
                taskObject = {'url':self.targetUrl,'name':self.targetUrl,'status': "error",'taskType':"Premint",'statusMessage':'Failed twitter follow','wallet':str(self.wallet),'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':message,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':"https://pbs.twimg.com/profile_images/1505785782002339840/mgeaHOqx_400x400.jpg"}
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
        #amount = self.transferTask['amount']
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
                taskObject = {"status": "revert","taskType": "Premint Chain - Reverted","receiver": nextWallet,"value": 0,"gas" : 21000 , "mode": "Premint Chain" , "wallet" : self.wallet , "reason":"Unespecified" , "maxFee" :str(maxGasFee) + "," + str(maxPriorityFee)}
                webhookLog(taskObject,self.session)
                return False
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed Transaction [{} ETH -> {}] - {}".format(amount,nextWallet,str(e)),"prefix":"({},{}) GWEI".format(maxGasFee,maxPriorityFee)},self.taskId)
            taskObject = {"status": "revert","taskType": "Premint Chain - Reverted","receiver": nextWallet,"value": 0,"gas" : 21000 , "mode": "Premint Chain" , "wallet" : self.wallet , "reason":str(e) , "maxFee" :str(maxGasFee) + "," + str(maxPriorityFee)}
            webhookLog(taskObject,self.session)
            return False
        
       
        
from genericpath import exists
import os,json,time,requests,re,string,names,random,tweepy,cloudscraper
from bs4 import BeautifulSoup
from socket import timeout
from xmlrpc.client import FastMarshaller
from web3 import Web3
from app_modules.taskLogger import taskLogger
from app_modules.discordLog import webhookLog
from app_modules.apiModules import nodeProvider,etherScanApi,alternative,checkNode,capKey,cfNode,checkCapMonster
from app_modules.titleLog import classUpdateTitle
from app_modules.proxy import proxy_choice
from eth_account.messages import encode_defunct
from fake_useragent import UserAgent
ua = UserAgent()


global web3Connection
updateTitleCall=classUpdateTitle("Custom Raffle")
siteKey = "6LdIP1ceAAAAAIuZYr5mIBZeOxvSN7tdMV3Z02Pt" 
workingProxy = []

class humanKind():
    def __init__(self,targetUrl,wallet,walletKey,twitterToken,discordToken,emailObj,taskId):
       self.targetUrl = targetUrl
       self.wallet = Web3.toChecksumAddress(wallet)
       self.walletKey = walletKey
       self.twitterToken = twitterToken
       self.taskId = taskId
       self.session = None
       self.nonce = None
       self.message = None
       self.signature = None
       self.csrfToken = None
       self.twitterReq = "https://twitter.com/humankindart"
       self.minimumBalance = None
       self.submitLoad = None
       self.captchaReq = False
       self.first = True
       self.proceed = False
       self.image = "https://assets.bueno.art/images/QmSWV2BstFKNpXez9XbZoiVHJrNC5YSgaAAFNAPNERs9K8?w=600&s=716b8d5892ac5503c3a754d6b52bfbd5"
       self.proxy = "None"
       self.name = "Humankind Waitlist"
       self.params=""
       self.prefix = "@"+twitterToken
       self.nonce = 0
       self.proxObj = None
       self.token = ''
       self.raffId = ''
       if (emailObj['catchall']):
        self.email = self.generateEmail(emailObj['content'])
       else:
        self.email = emailObj['content']
       self.discordToken = None
       self.discordReq = None

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
        verifiedEntry = self.verify()
        if (verifiedEntry == False):
            self.authenticate()
            self.submit()
        else:
            taskLogger({"status" : "success","message":"Verified entry","prefix":self.prefix},self.taskId)
            return
    
    def getToken(self):
        endpoint = "https://forms.bueno.art/humankind"
        while (True):
            try:
                taskLogger({"status" : "process","message":"Fetching session","prefix":self.prefix},self.taskId)
                response = self.session.get(endpoint)
                if (response.status_code == 200):
                    responseText = response.text
                    taskLogger({"status" : "process","message":"Getting Token","prefix":self.prefix},self.taskId)
                    soup = BeautifulSoup(responseText,"html.parser")
                    js = soup.find("script",{"id":"__NEXT_DATA__"})
                    jsonObj = json.loads(js.text)
                    self.token = jsonObj['props']['pageProps']['form']['sk']
                    taskLogger({"status" : "success","message":"Got Token","prefix":self.prefix},self.taskId)
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed fetching session - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(2)
                    self.refreshSession(True)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed fetching session - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(3)
                self.refreshSession(True)

    def authenticate(self):
        message = "Signing this message will submit your entry to the form."
        message = encode_defunct(text=message)
        taskLogger({"status" : "process","message":"Signing session","prefix":self.prefix},self.taskId)
        signed_message = web3Connection.eth.account.sign_message(message, private_key=self.walletKey)
        self.signature = web3Connection.toHex(signed_message['signature'])
        taskLogger({"status" : "success","message":"Signed session","prefix":self.prefix},self.taskId)

    def requestSolutionMon(self):
        global siteKey
        endPoint="https://api.capmonster.cloud/createTask"
        payload = {
                    "clientKey":checkCapMonster(),
                    "task":
                    {
                        "type":"RecaptchaV3TaskProxyless",
                        "websiteURL":"https://forms.bueno.art/humankind",
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
            return solvedToken
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
                    return solvedPayload['solution']['gRecaptchaResponse']
                if (timeoutCtr == timeoutThresh):
                    taskLogger({"status" : "error","message":"Timeout solving, restarting captcha service","prefix":self.prefix},self.taskId)
                    return False
                time.sleep(5)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed solving poll - {}".format(e),"prefix":self.prefix},self.taskId)
                time.sleep(7)
    
    def generateEmail(self,provider):
        randomLen = random.randint(2,4)
        letters = string.ascii_lowercase
        randomLast= random.choice(letters)
        randomNumApp = ''.join(str(random.randint(1,9)) for i in range (randomLen))
        randomEmail = names.get_first_name()+randomLast+randomNumApp+"@{}".format(provider)
        taskLogger({"status" : "success","message":"Generated email : {}".format(randomEmail),"prefix":self.prefix},self.taskId)
        return randomEmail

    def submit(self):
        while True:
            captchaToken = self.requestSolutionMon()
            if (captchaToken!=None):
                break
            else:
                taskLogger({"status" : "error","message":"Invalid Captcha Token","prefix":self.prefix},self.taskId)
        payload = {"formSk":self.token,"signature":self.signature,"address":self.wallet,"message":"Signing this message will submit your entry to the form.","captchaToken":captchaToken,"formValues":{"twitter":"@{}".format(self.twitterToken),"email":self.email}}
        endpoint = "https://forms.bueno.art/api/forms/{}/entries".format(self.token)
        self.session.headers['Referer'] = 'https://forms.bueno.art/humankind'
        self.session.headers['Content-Type'] = "application/json; charset=utf-8"
        while True:
            try:
                taskLogger({"status" : "process","message":"Submitting entry","prefix":self.prefix},self.taskId)
                response = self.session.post(endpoint,data = json.dumps(payload),allow_redirects = True)
                if (response.status_code ==200):
                    updateTitleCall.addSuccess()
                    taskLogger({"status" : "success","message":"Succesfully submitted entry","prefix":self.prefix},self.taskId)
                    taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"Custom Raffle",'statusMessage':'Successfully submitted entry','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':None,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
                    webhookLog(taskObject,self.session)  
                    break
                else: #extract the error message
                        details = response.text
                        updateTitleCall.addFail()
                       
                        if (details == None):
                            resMsg = "Undefined Error"
                        else:
                            resMsg = details
                        taskLogger({"status" : "error","message":"Failed submitting entry [{}] - {}".format(response.status_code,resMsg),"prefix":self.prefix},self.taskId)
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"Custom Raffle",'statusMessage':'Failed submitting entry','wallet':self.wallet,'discord':self.discordToken,'twitter':self.twitterToken,'proxy':self.proxy,'errorMessage':resMsg,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
                        webhookLog(taskObject,self.session)  
                        break
            except Exception as e:
                print(str(e))
                updateTitleCall.addFail()
                taskLogger({"status" : "error","message":"Failed submitting entry - {}!".format(e),"prefix":self.prefix},self.taskId)
                captchaToken = self.requestSolutionMon()

           
    def verify(self):
        endpoint = "https://forms.bueno.art/api/forms/{}/entries/{}".format(self.token,self.wallet)
        while True:
            taskLogger({"status" : "process","message":"Verifying entry","prefix":self.prefix},self.taskId)
            response = self.session.get(endpoint)
            if (response.status_code == 200):
                responseData = json.loads(response.text)
                exist = responseData['exists']
                if (exist == True):
                    return True
                else:
                    return False
            else:
                taskLogger({"status" : "process","message":"Failed verifying entry - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                time.sleep(3)
from genericpath import exists
import os,json,time,requests,re,string,names,random,tweepy,cloudscraper
from tempfile import TemporaryFile
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
siteKey = "6LcpgnoiAAAAAPJJCcHhoKjqrB_ADEJZp4TNFfHL" 
workingProxy = []

class pencil():
    def __init__(self,targetUrl,wallet,emailObj,taskId):
       self.targetUrl = targetUrl
       self.wallet = str(Web3.toChecksumAddress(wallet))
       self.taskId = taskId
       self.session = None
       self.nonce = None
       self.message = None
       self.signature = None
       self.csrfToken = None
       self.twitterReq = "https://twitter.com/pencilcaseproj"
       self.minimumBalance = None
       self.submitLoad = None
       self.captchaReq = False
       self.first = True
       self.proceed = False
       self.image = "https://pbs.twimg.com/profile_images/1565381851161804801/CRJY5LKr_400x400.jpg"
       self.proxy = "None"
       self.name = "The Pencil Case Project"
       self.params=""
       self.prefix = ""
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
       self.formId = 9091
       self.author = 6
       self.postId = 9164
       self.token = "44d72b8b407069b903e221d375f74116"
       self.pageTitle = "The Pencil Case Project"
       self.pageId = 9164


    def rotateProxy(self,retry=False):
        if (self.session != None):
            self.session.cookies.clear()

        taskLogger({"status":"process", "message": "Initializing session","prefix":self.prefix},self.taskId)
        self.session = cloudscraper.create_scraper(
               browser={
                        'browser': 'firefox',
                        'platform': 'windows',
                        'mobile': False
            }
        )
        self.session.headers['User-Agent'] = ua['firefox']
        '''chosenProxy=proxy_choice()
        self.proxObj = chosenProxy
        self.session.proxies.update(chosenProxy)
        self.proxy = str(self.session.proxies['http'])'''

    def initialize(self):  
        updateTitleCall.addRun()
        self.rotateProxy() #initialize session
        '''verifiedEntry = self.verify()
        if (verifiedEntry):
            return'''
        self.submit()

    def requestSolutionMon(self):
        global siteKey
        endPoint="https://api.capmonster.cloud/createTask"
        payload = {
                    "clientKey":checkCapMonster(),
                    "task":
                    {
                        "type":"NoCaptchaTask",
                        "websiteURL":"https://pencilcase.co/",
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
    
    def verify(self):
        endpoint = "https://pencilcase.co/api/fetchEmailAddress"
        payload = {'wallet_address': (self.wallet).upper()}
        #payload = {"wallet_address":"\"0x6856522A47dA76BE33f0F1fCaA519D2A1449AA16\""}
        payload = '''{"wallet_address":"0x6856522A47dA76BE33f0F1fCaA519D2A1449AA16"}'''
        while True:
            try:
                taskLogger({"status" : "process","message":"Verifying entry","prefix":self.prefix},self.taskId)
                response = self.session.post(endpoint,data = json.dumps(payload))
                if (response.status_code == 200):
                    responseJson = json.loads(response.text)
                    foundEmail = responseJson['email_address']
                    taskLogger({"status" : "success","message":"Verified entry - {}".format(foundEmail),"prefix":self.prefix},self.taskId)
                    return True
                else:
                    taskLogger({"status" : "error","message":"Entry not found - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    return False
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed verifying entry - {}".format(str(e)),"prefix":self.prefix},self.taskId)
                time.sleep(3)
    
    def payloadGenerator(self):
        endpoint ="https://pencilcase.co/api/has-entered-raffle?wallet_address={}".format(self.wallet)
        payload = {"wallet_address": self.wallet}
        while True:
            try:
                taskLogger({"status" : "process","message":"Initializing Entry","prefix":self.prefix},self.taskId)
                response = self.session.post(endpoint,data = json.dumps(payload))
                if (response.status_code == 201):
                    responseJson = json.loads(response.text)
                    if (responseJson['hasEntered'] == False):
                        taskLogger({"status" : "success","message":"Initialized entry","prefix":self.prefix},self.taskId)
                        break
                    else:
                        taskLogger({"status" : "success","message":"Verified Entry".format(response.status_code),"prefix":self.prefix},self.taskId)
                        return False
                else:
                    taskLogger({"status" : "error","message":"Failed to initialize entry - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed initializing entry - {}".format(str(e)),"prefix":self.prefix},self.taskId)
                time.sleep(3)

        while True:
            captchaToken = self.requestSolutionMon()
            if (captchaToken!=None):
                break
            else:
                taskLogger({"status" : "error","message":"Invalid Captcha Token","prefix":self.prefix},self.taskId)
        
        payload = {"email_address":self.email,"wallet_address":self.wallet,"captchaResponse":captchaToken}
        return payload
        


    def submit(self):
        while True:
            payload = self.payloadGenerator()
            if (payload == False):
                return
            endpoint = "https://pencilcase.co/api/enter-raffle"
            self.session.headers['Referer'] = 'https://pencilcase.co/'
            self.session.headers['Origin'] = 'https://pencilcase.co'
            self.session.headers['Content-Type'] = 'application/json'
            self.session.headers['Cookie'] = ''
            try:
                taskLogger({"status" : "process","message":"Submitting entry","prefix":self.prefix},self.taskId)
                response = self.session.post(endpoint, data = json.dumps(payload))
                if (response.status_code ==201):
                    respJson = json.loads(response.text)
                    success = respJson['success']
                    if (success == True):
                        updateTitleCall.addSuccess()
                        taskLogger({"status" : "success","message":"Succesfully submitted entry","prefix":self.prefix},self.taskId)
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"Custom Raffle - Pencil Case",'statusMessage':'Successfully submitted entry','wallet':self.wallet,'discord':self.discordToken,'twitter':"N/A",'proxy':self.proxy,'errorMessage':None,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
                        webhookLog(taskObject,self.session)  
                        break
                    else:
                        taskLogger({"status" : "error","message":"Error submitting entry - {}".format(response.status_code),"prefix":self.prefix},self.taskId)
                        time.sleep(2)
                else: #extract the error message
                        details = response.text
                        updateTitleCall.addFail()
                       
                        if (details == None):
                            resMsg = "Undefined Error"
                        else:
                            resMsg = details
                        taskLogger({"status" : "error","message":"Failed submitting entry [{}] - {}".format(response.status_code,resMsg),"prefix":self.prefix},self.taskId)
                        if ("Unauthorized" not in response.text):
                            taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"Custom Raffle - Pencil Case",'statusMessage':'Failed submitting entry','wallet':self.wallet,'discord':self.discordToken,'twitter':"N/A",'proxy':self.proxy,'errorMessage':resMsg,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
                            webhookLog(taskObject,self.session)  
                            break
                        else:
                            time.sleep(3)
            except Exception as e:
                updateTitleCall.addFail()
                taskLogger({"status" : "error","message":"Failed submitting entry - {}!".format(e),"prefix":self.prefix},self.taskId)


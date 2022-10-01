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
siteKey = "6Lc6tKAcAAAAAGXbFVOCdvrBGY6ofO2Rg8HLCkYx" 
workingProxy = []

class orangeComet():
    def __init__(self,targetUrl,wallet,emailObj,taskId):
       self.targetUrl = targetUrl
       self.wallet = str(Web3.toChecksumAddress(wallet))
       self.taskId = taskId
       self.session = None
       self.nonce = None
       self.message = None
       self.signature = None
       self.csrfToken = None
       self.twitterReq = "https://twitter.com/orangecometnft"
       self.minimumBalance = None
       self.submitLoad = None
       self.captchaReq = False
       self.first = True
       self.proceed = False
       self.image = "https://pbs.twimg.com/profile_images/1573187602404245504/ie4N3PqC_400x400.jpg"
       self.proxy = "None"
       self.name = "Anthony Hopkins Premint Registration 2022"
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
       self.pageTitle = "Anthony Hopkins Premint Registration 2022"
       self.pageId = 9164


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

    def payloadGenerator(self):
        operatorArr = ['+','-','*']
        operator_functions = {
            '+': lambda a, b: a + b, 
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b, 
        }
        randomNumber1 = random.randint(1,15)
        randomNumber2 = random.randint(1,15)
        operator = random.choice(operatorArr)
        generatedAnswer = operator_functions[operator](randomNumber1, randomNumber2)
        taskLogger({"status" : "success","message":"Generated operation answer - {}".format(generatedAnswer),"prefix":self.prefix},self.taskId)
        
        while True:
            captchaToken = self.requestSolutionMon()
            if (captchaToken!=None):
                break
            else:
                taskLogger({"status" : "error","message":"Invalid Captcha Token","prefix":self.prefix},self.taskId)
        
        files = {
            'wpforms[fields][14]':(None, self.email),
            'wpforms[fields][12]':(None,self.wallet),
            'wpforms[fields][15][a]':(None, generatedAnswer),
            'wpforms[fields][15][cal]':(None, str(operator)),
            'wpforms[fields][15][n2]' : (None,randomNumber1),
            'wpforms[fields][15][n1]': (None,randomNumber2),
            'g-recaptcha-response':(None, captchaToken),
            'g-recaptcha-hidden':(None,1),
            'wpforms[id]':(None,self.formId),
            'wpforms[author]':(None,self.author),
            'wpforms[post_id]':(None,self.postId),
            'wpforms[submit]':(None,"wpforms-submit"),
            'wpforms[token]':(None,self.token),
            'action': (None,"wpforms_submit"),
            'page_url' : (None,self.targetUrl),
            'page_title' :  (None,self.pageTitle),
            'page_id' : (None,self.pageId)
        }

        return files
        

    def initialize(self):  
        updateTitleCall.addRun()
        self.rotateProxy() #initialize session
        self.submit()

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
            payload = self.payloadGenerator()
            endpoint = "https://orangecomet.com/wp-admin/admin-ajax.php"
            self.session.headers['Referer'] = self.targetUrl
            self.session.headers['x-requested-with'] = 'XMLHttpRequest'
            self.session.headers['Origin'] = 'https://orangecomet.com'
            try:
                taskLogger({"status" : "process","message":"Submitting entry","prefix":self.prefix},self.taskId)
                response = self.session.post(endpoint, files = payload,allow_redirects = True)
                if (response.status_code ==200):
                    respJson = json.loads(response.text)
                    success = respJson['success']
                    if (success == True):
                        updateTitleCall.addSuccess()
                        taskLogger({"status" : "success","message":"Succesfully submitted entry","prefix":self.prefix},self.taskId)
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "success",'taskType':"Custom Raffle - Orange Comet",'statusMessage':'Successfully submitted entry','wallet':self.wallet,'discord':self.discordToken,'twitter':"N/A",'proxy':self.proxy,'errorMessage':None,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
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
                        taskObject = {'url':self.targetUrl,'name':self.name,'status': "error",'taskType':"Custom Raffle - Orange Comet",'statusMessage':'Failed submitting entry','wallet':self.wallet,'discord':self.discordToken,'twitter':"N/A",'proxy':self.proxy,'errorMessage':resMsg,'twitterProj':self.twitterReq,'discordProj':self.discordReq,'image':self.image}
                        webhookLog(taskObject,self.session)  
                        break
            except Exception as e:
                updateTitleCall.addFail()
                taskLogger({"status" : "error","message":"Failed submitting entry - {}!".format(e),"prefix":self.prefix},self.taskId)
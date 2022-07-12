from  app_modules.proxy import proxy_choice
from  app_modules.taskLogger import taskLogger
from  app_modules.discordLog import webhookLog
from app_modules.titleLog import classUpdateTitle
import requests,json


updateTitleCall=classUpdateTitle("Discord Invites")

class inviteTask():
    def __init__(self,discordToken,inviteCode):
        self.token = discordToken
        self.inviteCode = inviteCode
        self.session= None
    
    def initialize(self):
        updateTitleCall.addRun()
        self.session=requests.session()
        headers = {'Authorization' :self.token, 'User-Agent': "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Mobile Safari/537.36" , 'content-type': 'application/json', 'origin': 'https://discord.com',
        'referer': "https://discord.com/channels/@me",'sec-ch-ua': '''" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"''','sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': "Android"}
        self.session.headers.update(headers)
        chosenProxy=proxy_choice()
        taskLogger({'status':"process",'message':"Connecting to Proxy"},self.token)
        self.session.proxies.update(chosenProxy)
        self.join()
    
    def join(self):
        URL = "https://discord.com/api/v9/invites/{}".format(self.inviteCode)
        taskLogger({'status':"process",'message':"Joining server.."},self.token)
        while True:
            try:
                response = self.session.post(URL,json={},timeout= 10)
                if (response.status_code == 200):
                    taskLogger({'status':"success",'message':"Succesfully Joined Server!"},self.token)
                    responseJson = json.loads(response.text)
                    try:
                        iconUrl = "https://cdn.discordapp.com/icons/{}/{}.png".format(responseJson['guild']['id'],responseJson['guild']['icon'])
                    except:
                        iconUrl = None
                    updateTitleCall.addSuccess()
                    taskObject = {'status':"success",'taskType':"Discord",'server':responseJson['guild']['name'],'token':self.token,'inviteCode':self.inviteCode,'statusCode': response.status_code,'mode':'Mass Invite','image': iconUrl}
                else:
                    print(response.text)
                    taskLogger({'status':"error",'message': "Failed to join server! - {}".format(response.status_code)},self.token)
                    taskObject = {'status':"fail",'taskType':"Discord",'server':'Undefined','token':self.token,'inviteCode':self.inviteCode,'statusCode': response.status_code,'mode':'Mass Invite','image': None}
                    updateTitleCall.addFail()
                webhookLog(taskObject)
                break
            except Exception as e:
                updateTitleCall.addFail()
                taskLogger({'status':"error",'message':"Failed to join server - {}".format(e)},self.token)
                taskObject = {'status':"fail",'taskType':"Discord",'server':'Undefined','token':self.token,'inviteCode':self.inviteCode,'statusCode': str(e),'mode':'Mass Invite','image': None}
                taskLogger({'status':"process",'message':"Rotating proxies"},self.token)
                chosenProxy=proxy_choice()
                self.session.proxies.update(chosenProxy)



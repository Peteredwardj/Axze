import base64
import requests
import json
import time
from app_modules.titleLog import classUpdateTitle
from  app_modules.taskLogger import taskLogger
from  app_modules.discordLog import webhookLog

updateTitleCall=classUpdateTitle("Discord Invites")

class inviteTask():
    def __init__(self,discordToken,inviteCode,proxy,taskId,mode,reactParam=None):
        self.token = discordToken
        self.inviteCode = inviteCode
        self.session= None
        self.proxy = {'http': proxy, 'https': proxy}
        self.taskId = taskId
        self.mode = mode
        if (self.mode == "react"):
            self.messageLink = reactParam['messageLink']
            self.emoji = reactParam['emoji']
    
    def cf_cookies(self): #function to get CF cookies
        while True:
            taskLogger({'status':"process",'message':"Getting cookies",'prefix':self.token},self.taskId)
            try:
                headers = {
                    'authorization': self.token,
                    'content-type': 'application/json',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
                }

                response = self.session.get("https://discord.com/",headers=headers)
                cookies_raw = response.cookies.get_dict()
                cookies = ""
                for cookie in cookies_raw:
                    cookies = cookies + cookie + "=" + cookies_raw[cookie] + "; "

                return cookies

            except Exception as e:
                taskLogger({'status':"error",'message':"Failed getting cookies - {}".format(e), 'prefix':self.token},self.taskId)
                time.sleep(3)

    def user_guilds(self) :     # function to get all user guilds/ server
        user_guild_list = []
        try:
            header = {"authorization": self.token, 
                "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"}

            response = self.session.get(f"https://discord.com/api/v9/users/@me/guilds",headers=header)
            response_json = response.json()

            for i in response_json:
                guild_id = i["id"]
                user_guild_list.append(guild_id)
            return user_guild_list
        except Exception as e:
            return user_guild_list #return empty list, just assume that we are not in the server
    
    def acceptRules(self,guildId,inviteCode):
        try:
            while True:
                params = {
                    'with_guild': 'false',
                    'invite_code': inviteCode
                }

                response = self.session.get(f'https://discord.com/api/v9/guilds/{guildId}/member-verification', params=params)

                if (response.status_code == 200):
                    taskLogger({'status':"success",'message':"Succesfully fetched rules", 'prefix':self.token},self.taskId)
                    break
                
                else:
                    taskLogger({'status':"warn",'message':"Rules not found - {}".format(response.status_code), 'prefix':self.token},self.taskId)
                    return True

            data = response.json()
            data['form_fields'][0]["response"] = "true"

            while True:
                taskLogger({'status':"process",'message':"Accepting rule", 'prefix':self.token},self.taskId)
                response = self.session.put(f'https://discord.com/api/v9/guilds/{guildId}/requests/@me', json=data)

                if (response.status_code == 201):
                    taskLogger({'status':"success",'message':"Succesfully accepted rules", 'prefix':self.token},self.taskId)
                    return True
                else:
                    taskLogger({'status':"warn",'message':"Failed to accept rule / rules not found - {}".format(response.status_code), 'prefix':self.token},self.taskId)
                    #time.sleep(3)
                    break
        except Exception as e:
            taskLogger({'status':"error",'message':"Failed to accept rule - {}".format(e), 'prefix':self.token},self.taskId)

    
    def reactFunc(self):
        try:
            headers = {
                    'authority': 'discord.com',
                    'accept': '*/*',
                    'authorization': self.token,
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
            
            }
            _,_,_,_,_,channel_id,message_id = self.messageLink.split("/")
            typeOfEmoji = "standard"
            if (len(self.emoji)>1):
                self.emoji = self.emoji.replace(":","%3A")
                typeOfEmoji = "custom"

            endPoint = f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{self.emoji}/%40me?location=Message"
            while True:
                taskLogger({'status':"process",'message':"Reacting with {} emoji".format(typeOfEmoji), 'prefix':self.token},self.taskId)
                response = self.session.put(endPoint,headers=headers)

                if (response.status_code == 204):
                    taskLogger({'status':"success",'message':"Succesfully reacted", 'prefix':self.token},self.taskId)
                    return True
                else:
                    taskLogger({'status':"error",'message':"Failed to react - {}".format(response.status_code), 'prefix':self.token},self.taskId)
                    time.sleep(3)
        except Exception as e:
            taskLogger({'status':"error",'message':"Failed to react - {}".format(e), 'prefix':self.token},self.taskId)



    def main(self):
        updateTitleCall.addRun()
        taskLogger({'status':"process",'message':"Initializing Session",'prefix':self.token},self.taskId)
        self.session = requests.session() #create a session obj
        if (self.proxy != None):
            proxy = self.proxy  
            self.session.proxies.update(proxy) 

        # this can be adjust later by function   
        super_properties_data_format = '{"os":"Windows","browser":"Chrome","device":"","system_locale":"en-US","browser_user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36","browser_version":"103.0.0.0","os_version":"10","referrer":"","referring_domain":"","referrer_current":"","referring_domain_current":"","release_channel":"stable","client_build_number":135402,"client_event_source":null}'
        super_properties = base64.b64encode(super_properties_data_format.encode("utf-8")).decode()

        url = f"https://discord.com/api/v9/invites/{self.inviteCode}"

        headers = {'authority': 'discord.com',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/json',
                'origin': 'https://discord.com',
                'sec-ch-ua': '\'.Not/A)Brand\';v=\'99\', \'Google Chrome\';v=\'103\', \'Chromium\';v=\'103\'',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '\'Windows\'',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                'x-debug-options': 'bugReporterEnabled',
                'x-discord-locale': 'en-US',
                'x-kl-ajax-request': 'Ajax_Request',
                }
            
        self.session.headers.update(headers)
        while True:
            try:
                taskLogger({'status':"process",'message':"Getting server details",  'prefix':self.token},self.taskId)
                response = self.session.get(url,headers=headers)
                response = response.json()
                user_guild_list = self.user_guilds()    #handler to verify user already join the server or not
                guildId = response["guild"]["id"]
                if response["guild"]["id"] in user_guild_list:
                    taskLogger({'status':"warn",'message':"You are already in the server sir, stopping task!", 'prefix':self.token},self.taskId)
                    break
                else:
                    x_context_properties_invite_page_format =  f'{{"location":"Accept Invite Page","location_guild_id":"{response["guild"]["id"]}","location_channel_id":"{response["channel"]["id"]}","location_channel_type":0}}'
                    x_context_properties = base64.b64encode(x_context_properties_invite_page_format.encode("utf-8")).decode()
                    self.session.headers.update({
                        "authorization" : self.token,
                        'cookie': self.cf_cookies(),
                        "x-context-properties" : x_context_properties,
                        "x-super-properties" : super_properties,
                    })
                    #time.sleep(3) #maybe this delay doesnt matter? 
                    taskLogger({'status':"process",'message':"Joining server",  'prefix':self.token},self.taskId)
                    response = self.session.post(url,headers=headers,json={},timeout=10)
                    if (response.status_code == 200):
                        responseJson = json.loads(response.text)
                        if responseJson.get("new_member"):
                            try:
                                iconUrl = "https://cdn.discordapp.com/icons/{}/{}.png".format(responseJson['guild']['id'],responseJson['guild']['icon'])
                            except:
                                iconUrl = None
                            updateTitleCall.addSuccess()
                            taskLogger({'status':"success",'message': "Succesfully joined server : {}!".format(responseJson['guild']['name']),  'prefix':self.token},self.taskId)
                            taskObject = {'status':"success",'taskType':"Discord",'server':responseJson['guild']['name'],'token':self.token,'inviteCode':self.inviteCode,'statusCode': response.status_code,'mode':'Mass Invite','image': iconUrl}
                            webhookLog(taskObject)
                            break
                        else:
                            taskLogger({'status':"error",'message': "Failed to join server! - {}".format(response.status_code),  'prefix':self.token},self.taskId)
                            taskObject = {'status':"fail",'taskType':"Discord",'server':'Undefined','token':self.token,'inviteCode':self.inviteCode,'statusCode': response.status_code,'mode':'Mass Invite','image': None}
                            updateTitleCall.addFail()
                            webhookLog(taskObject)
                            time.sleep(3)
                    else:
                        taskLogger({'status':"error",'message': "Failed to join server! - {}".format(response.status_code),  'prefix':self.token},self.taskId)
                        taskObject = {'status':"fail",'taskType':"Discord",'server':'Undefined','token':self.token,'inviteCode':self.inviteCode,'statusCode': response.status_code,'mode':'Mass Invite','image': None}
                        updateTitleCall.addFail()
                        webhookLog(taskObject)
                        if (response.status_code == 403): #most likely token banned, just kill task
                            break
                        else: #retry 
                            time.sleep(3)

            except Exception as e:
                taskLogger({'status':"error",'message':"Failed invite task - {}".format(e),  'prefix':self.token},self.taskId)
                time.sleep(3) #retry delay 

        self.acceptRules(guildId,self.inviteCode)
        if (self.mode == "react"):
            self.reactFunc()
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
import time
from app_modules.taskLogger import taskLogger
import os,pickle,requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException


instanceCtr = 0 

def cf_cookies(token,session,taskId,url): #function to get CF cookies
    while True:
        taskLogger({'status':"process",'message':"Getting cookies",'prefix':token},taskId)
        try:
            headers = {
                'authorization': token,
                'content-type': 'application/json',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0'
            }

            session.headers.update(headers)
            response = session.get("https://discord.com/")
            if (response.status_code == 200):
                taskLogger({'status':"success",'message':"Got cookies",'prefix':token},taskId)
                break
            else:
                taskLogger({'status':"error",'message':"Failed to get cookies",'prefix':token},taskId)
                time.sleep(3)
        except Exception as e:
            taskLogger({'status':"error",'message':"Failed getting cookies - {}".format(e), 'prefix':token},taskId)
            time.sleep(3)


def submitDisconnect(session,responseText,prefix,taskId,ctr):
    try:
        endpoint = "https://www.premint.xyz/accounts/social/connections/"
        soup = BeautifulSoup(responseText,'html.parser')
        foundInputs = soup.find('input',{'type':'radio'})
        if (foundInputs == None):
            taskLogger({"status" : "success","message":"All accounts disconnected","prefix":prefix},taskId)
            return True,"success"
        else:
            toRemove = foundInputs['value']
            token = soup.find('input',{'name':'csrfmiddlewaretoken'})['value']  
            payload = {
                "csrfmiddlewaretoken" : token,
                "account":toRemove
            }         

            while True:
                taskLogger({"status" : "process","message":"Disconnecting social account #{}".format(ctr),"prefix":prefix},taskId)
                response = session.post(endpoint,data = payload)
                if (response.status_code == 200):
                    ctr += 1
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed disconnecting social account - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(3)
            return submitDisconnect(session,response.text,prefix,taskId,ctr)
    except Exception as e:
        taskLogger({"status" : "error","message":"Failed disconnecting social account - {}".format(e),"prefix":prefix},taskId)
        return False,str(e)



def disconnectSocial(session,prefix,taskId): #disconnects twitter and discord from premint
    try:
        while True:
            endpoint = "https://www.premint.xyz/accounts/social/connections/"
            taskLogger({"status" : "process","message":"Fetching social account details","prefix":'-'},taskId)
            response = session.get(endpoint)
            if (response.status_code == 200):
                break
            else:
                taskLogger({"status" : "error","message":"Failed fetching social account details - {}".format(response.status_code),"prefix":prefix},taskId)
                time.sleep(3)
        
        res,message = submitDisconnect(session,response.text,'-',taskId,1)
        return res,message

    except Exception as e:
        taskLogger({"status" : "error","message":"Failed disconnecting socials - {}".format(e),"prefix":prefix},taskId)



def connectDiscordRequest(token,prefix,session,taskId):
    discordString = "Connect Discord"
    try:
        taskLogger({"status" : "process","message":"Connecting Discord Account","prefix":token},taskId)
        
        while True:
            taskLogger({"status" : "process","message":"Getting Authorization redirect","prefix":prefix},taskId)
            response = session.get("https://www.premint.xyz/accounts/discord/login/?process=connect&scope=guilds.members.read&next=%2Fprofile%2F")
            if (response.status_code == 200):
                authLink = response.url
                authLink =  authLink.replace("%3A",":")
                authLink = authLink.replace("%2F", "/")
                authState = authLink.split("state=")[1]
                authLink = authLink.replace("https://discord.com/oauth2/authorize?","https://discord.com/api/oauth2/authorize?")
                taskLogger({"status" : "success","message":"Got redirect","prefix":token},taskId)
                break
            else:
                taskLogger({"status" : "error","message":"Failed to get redirect : {}".format(response.status_code),"prefix":token},taskId)
                time.sleep(3)

        #authentication request module        
        ses = requests.session()
        ses.proxies.update(session.proxies)
        refLink = 'https://discord.com/oauth2/authorize?client_id=897003204598980619&redirect_uri=https%3A%2F%2Fwww.premint.xyz%2Faccounts%2Fdiscord%2Flogin%2Fcallback%2F&scope=identify+guilds+guilds.members.read&response_type=code&state={}'.format(authState)
        cf_cookies(token,ses,taskId,refLink) #get cf cookies here
        headers = {
            'Accept-Language' : 'en-US,en;q=0.5',
            'Alt-Used' : 'discord.com',
            'Authorization' : token,
            'DNT' : "1",
            'Host':'discord.com',
            'Origin':'https://discord.com',
            'Referer': refLink,
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0',
            'X-Debug-Options':'bugReporterEnabled',
            'X-Discord-Locale': 'en-US',
            'X-Super-Properties':'eyJvcyI6Ik1hYyBPUyBYIiwiYnJvd3NlciI6IkZpcmVmb3giLCJkZXZpY2UiOiIiLCJzeXN0ZW1fbG9jYWxlIjoiZW4tVVMiLCJicm93c2VyX3VzZXJfYWdlbnQiOiJNb3ppbGxhLzUuMCAoTWFjaW50b3NoOyBJbnRlbCBNYWMgT1MgWCAxMC4xNTsgcnY6MTAyLjApIEdlY2tvLzIwMTAwMTAxIEZpcmVmb3gvMTAyLjAiLCJicm93c2VyX3ZlcnNpb24iOiIxMDIuMCIsIm9zX3ZlcnNpb24iOiIxMC4xNSIsInJlZmVycmVyIjoiIiwicmVmZXJyaW5nX2RvbWFpbiI6IiIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjoxMzc2NTAsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9'
        }
        ses.headers.update(headers)    
        payload = {"permissions":"0","authorize":True}

        while True:
            headers['Content-Type'] = 'application/json'
            taskLogger({"status" : "process","message":"Authorizing Premint [Discord]","prefix":token},taskId)
            response = ses.post(authLink,data=json.dumps(payload),headers=headers)
            if (response.status_code == 200):
                responseJson = json.loads(response.text)
                redirectTo = responseJson['location']
                taskLogger({"status" : "success","message":"Authorized, redirecting [Discord]","prefix":token},taskId)
                break
            else:
                taskLogger({"status" : "error","message":"Failed authorizing Discord - {}".format(response.status_code),"prefix":token},taskId)
                time.sleep(3)
        
        while True:
            try:
                taskLogger({"status" : "process","message":"Confirming Premint","prefix":prefix},taskId)
                response = session.get(redirectTo)
                if (response.status_code == 200):
                        if (discordString not in response.text):
                            taskLogger({"status" : "success","message":"Succesfully connected Discord account to Premint","prefix":prefix},taskId)
                            return True,"success"
                        else:
                            taskLogger({"status" : "error","message":"Failed to connect Discord account to Premint , redirect : {}".format(response.url),"prefix":prefix},taskId)
                            return False,"Failed to connect Discord account to Premint , redirect : {}".format(response.url)
                            #time.sleep(3)
                else:
                    taskLogger({"status" : "error","message":"Failed to connect Discord account to Premint - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to authorize Discord account- {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)
        
    except Exception as e:
        taskLogger({"status" : "error","message":"Failed connecting Discord Account - {}".format(e),"prefix":token},taskId)
        return False,"Failed connecting Discord Account - {}".format(e)


def twitterSessionHandler(user,ses,prefix,taskId,connect=False):
    if (connect == True):
        session = ses
    else:
        session = requests.session()
        session.proxies.update(ses.proxies)
    cookies = pickle.load(open("./chrome/prof/{}.pkl".format(user), "rb"))
    taskLogger({"status" : "process","message":"Loading Twitter session","prefix":prefix},taskId)
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'],domain=".twitter.com")
    taskLogger({"status" : "success","message":"Loaded Twitter session","prefix":prefix},taskId)
    return session


def getCookies(cookie_jar, domain):
    cookie_dict = cookie_jar.get_dict(domain=domain)
    found = ['%s=%s' % (name, value) for (name, value) in cookie_dict.items()]
    return ';'.join(found)

def likeTweet(user,likeReq,ses,prefix,taskId):
    userAgent= 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Mobile Safari/537.36'
    session = twitterSessionHandler(user,ses,prefix,taskId)
    ctCookie = session.cookies['ct0']
    headers = {
    'authorization' : 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'Content-Type' :'application/json',
    "DNT":"1",
    'Origin':'https://twitter.com',
    'Referer':'https://twitter.com/home',
    'sec-ch-ua': '''".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"''',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': "macOS",
    'user-agent': userAgent,
    'x-csrf-token':ctCookie,
    'x-twitter-active-user':'yes',
    'x-twitter-auth-type' :'OAuth2Session',
    'x-twitter-client-language' : 'en'
    }
    while True:
        payload = {"variables":{"tweet_id":likeReq},"queryId":"lI07N6Otwv1PhnEgXILM7A"}

        try:
            taskLogger({"status" : "process","message":"Liking tweet","prefix":prefix},taskId)
            response = session.post("https://twitter.com/i/api/graphql/lI07N6Otwv1PhnEgXILM7A/FavoriteTweet",headers = headers, data = json.dumps(payload))
            if (response.status_code == 200):
                taskLogger({"status" : "success","message":"Succesfully liked tweet","prefix":prefix},taskId)
                break
            else:
                taskLogger({"status" : "error","message":"Failed to like tweet - {}".format(response.status_code),"prefix":prefix},taskId)
                if(response.status_code == 403 or response.status_code == 401):
                    return False,"Failed to like tweet - {}".format(response.status_code)
                else:
                    time.sleep(3)
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed to like tweet - {}".format(e),"prefix":prefix},taskId)
            time.sleep(3)

    while True:
        payload = {"variables":{"tweet_id":likeReq,"dark_request":False},"queryId":"ojPdsZsimiJrUGLR1sjUtA"}
        try:
            taskLogger({"status" : "process","message":"Retweeting tweet","prefix":prefix},taskId)
            response = session.post("https://twitter.com/i/api/graphql/ojPdsZsimiJrUGLR1sjUtA/CreateRetweet",headers = headers, data = json.dumps(payload))
            if (response.status_code == 200):
                taskLogger({"status" : "success","message":"Succesfully retweeted tweet","prefix":prefix},taskId)
                break
            else:
                taskLogger({"status" : "error","message":"Failed retweeting - {}".format(response.status_code),"prefix":prefix},taskId)
                if(response.status_code == 403 or response.status_code == 401):
                    return False,"Failed to  retweet - {}".format(response.status_code)
                else:
                    time.sleep(3)
        except Exception as e:
            taskLogger({"status" : "error","message":"Failed to  retweet - {}".format(e),"prefix":prefix},taskId)
            time.sleep(3)
    
    return True,"success"
    



def followTwitter(user,twitterReq,ses,prefix,taskId):
    userAgent= 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Mobile Safari/537.36'
    try:
        session = twitterSessionHandler(user,ses,prefix,taskId)
        header = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        ctCookie = session.cookies['ct0']

        for twitterUser in twitterReq:
            headers = {
            'authorization' : 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'Content-Type' :'application/x-www-form-urlencoded',
            "DNT":"1",
            'Origin':'https://twitter.com',
            'Referer':'https://twitter.com/{}'.format(twitterUser),
            'sec-ch-ua': '''".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"''',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': "macOS",
            'user-agent': userAgent,
            'x-csrf-token':ctCookie,
            'x-twitter-active-user':'yes',
            'x-twitter-auth-type' :'OAuth2Session',
            'x-twitter-client-language' : 'en'
            }
            payload = {
                "include_profile_interstitial_type": "1",
                "include_blocking":"1",
                "include_blocked_by":"1",
                "include_followed_by":"1",
                "include_want_retweets":"1",
                "include_mute_edge":"1",
                "include_can_dm":"1",
                "include_can_media_tag":"1",
                "include_ext_has_nft_avatar":"1",
                "skip_status":"1",
                "screen_name" : twitterUser
                #"user_id":str(userId)
            }
            while True:
                try:
                    taskLogger({"status" : "process","message":"Following {}".format(twitterUser),"prefix":prefix},taskId)
                    response = session.post("https://twitter.com/i/api/1.1/friendships/create.json",headers = headers, data = payload)
                    if (response.status_code == 200):
                        taskLogger({"status" : "success","message":"Succesfully followed {}".format(twitterUser),"prefix":prefix},taskId)
                        break
                    else:
                        taskLogger({"status" : "error","message":"Failed to follow - {}".format(response.status_code),"prefix":prefix},taskId)
                        if(response.status_code == 403 or response.status_code == 401):
                            return False,"Failed to follow - {}".format(response.status_code)
                        else:
                            time.sleep(3)
                except Exception as e:
                    taskLogger({"status" : "error","message":"Failed to follow - {}".format(e),"prefix":prefix},taskId)
                    time.sleep(3)
            time.sleep(1)
        
        return True,"Succesfully followed twitter users"

            
    except Exception as e:
        taskLogger({"status" : "error","message":"Failed to follow - {}".format(e),"prefix":prefix},taskId)
        return False,"Failed to follow - {}".format(response.status_code)



def connectTwitter(user,ses,prefix,taskId):
    try:
        session = twitterSessionHandler(user,ses,prefix,taskId,True) #connect is true
        endpoint = "https://www.premint.xyz/accounts/twitter/login/?process=connect&next=%2Fprofile%2F"
        while True:
            try:
                taskLogger({"status" : "process","message":"Fetching Twitter Auth","prefix":prefix},taskId)
                response = session.get(endpoint)
                if (response.status_code == 200):
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed to fetch Twitter Auth - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to fetch Twitter Auth - {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)

        soup = BeautifulSoup(response.text,"html.parser")
        formItems = soup.find_all('input',{'type':"hidden"}) 
        dictObj = {}
        for item in formItems:
            dictObj[item['name']] = item['value']
        parsed = urlparse(dictObj['referer'])
        oauthToken = parse_qs(parsed.query)['oauth_token'][0]

        payload = {
            "authenticity_token" : dictObj['authenticity_token'],
            "redirect_after_login" :"https://api.twitter.com/oauth/authorize?oauth_token={}".format(oauthToken),
            "oauth_token" : oauthToken
        }

        headers = {
            'Content-Type' :'application/x-www-form-urlencoded',
            'Origin':'https://api.twitter.com',
            'Referer':"https://api.twitter.com"+dictObj['referer'],
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0"
        }

        while True:
            try:
                taskLogger({"status" : "process","message":"Authorizing Twitter account","prefix":prefix},taskId)
                response = session.post("https://api.twitter.com/oauth/authorize",data = payload, headers = headers)
                if (response.status_code == 200):
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed to authorize Twitter account - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to authorize Twitter account- {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)

        soup = BeautifulSoup(response.text,"html.parser")
        banItems = soup.find("meta",{'http-equiv':"refresh"}) 
        link = banItems['content'].replace("0;url=","")
        twitterString = "Connect Twitter"
        while True:
            try:
                taskLogger({"status" : "process","message":"Confirming Premint","prefix":prefix},taskId)
                response = session.get(link)
                if (response.status_code == 200):
                        if (twitterString not in response.text):
                            taskLogger({"status" : "success","message":"Succesfully connected Twitter account to Premint","prefix":prefix},taskId)
                            return True,"success"
                        else:
                            taskLogger({"status" : "error","message":"Failed to connect Twitter account to Premint , redirect : {}".format(response.url),"prefix":prefix},taskId)
                            time.sleep(3)
                else:
                    taskLogger({"status" : "error","message":"Failed to connect Twitter account to Premint - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to authorize Twitter account- {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)
    except Exception as e:
        taskLogger({"status" : "error","message":"Failed connecting Twitter Account - {}".format(e),"prefix":prefix},taskId)
        return False,"Failed connecting Twitter Account - {}".format(e)


def fileBrowser(user):
    dirPath = "./chrome/prof"
    profDirExist = os.path.exists(dirPath)
    if (profDirExist == False):
        os.makedirs(dirPath)
        
    fileAddr = "{}/{}.pkl".format(dirPath,user)
    found = os.path.isfile(fileAddr) 
    return found


def browserTask(user,password,discord,twitterReq,prefix,taskId,session,mode): #Logins to twitter and save the cookie
    global instanceCtr
    while True:
        if (instanceCtr <= 5):
            break
        else:
            taskLogger({"status" : "process","message":"Waiting for stagger start","prefix":prefix},taskId)
            time.sleep(5)
    try:
        instanceCtr += 1 #add instance
        userAgent= 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Mobile Safari/537.36'
        ignored_exceptions=(NoSuchElementException,StaleElementReferenceException,)
        opts = webdriver.ChromeOptions()
        opts.add_argument("user-agent={}".format(userAgent))
        opts.add_argument("--headless")
        opts.add_experimental_option('excludeSwitches', ['enable-logging'])
        if ("local" not in mode):
            proxy = str(session.proxies['http'])
            options = {
                'proxy': {
                    'http': proxy,
                    'https': proxy,
                    'no_proxy': 'localhost,127.0.0.1'
                }
            }
            taskLogger({"status" : "process","message":"Loading Proxies","prefix":prefix},taskId)
            browser = webdriver.Chrome(options=opts,seleniumwire_options=options,executable_path='./chrome/chromedriver')
        else:
            browser = webdriver.Chrome(options=opts,executable_path='./chrome/chromedriver')

        if (fileBrowser(user) == False): #profile not found 
            taskLogger({"status" : "process","message":"Beginning one time twitter profile setup - User {}".format(user),"prefix":prefix},taskId)
            browser.get("https://twitter.com/i/flow/login")
            loginDial = WebDriverWait(browser, 20,ignored_exceptions=ignored_exceptions).until(EC.element_to_be_clickable((By.TAG_NAME, 'input')))
            loginDial.send_keys(user)
            taskLogger({"status" : "process","message":"Logging user {}".format(user),"prefix":prefix},taskId)
            browser.find_element('xpath','//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div/div[6]/div').click() #next button
            #time.sleep(2)
            if ("Enter your phone number or username" in browser.page_source):
                taskLogger({"status" : "process","message":"Solving twitter challenge","prefix":prefix},taskId)
                instanceCtr -= 1
                return False,"Failed to solve twitter challenge - phone number"

            taskLogger({"status" : "process","message":"Logging password","prefix":prefix},taskId)
            passButt = WebDriverWait(browser, 20,ignored_exceptions=ignored_exceptions).until(EC.element_to_be_clickable((By.NAME,'password')))
            #passButt = browser.find_element_by_name("password")
            passButt.send_keys(password)
            taskLogger({"status" : "process","message":"Authenticating","prefix":prefix},taskId)
            browser.find_element('xpath','//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]').click() #login button
            WebDriverWait(browser,10).until(EC.url_contains("home"))
            if ("home" not in browser.current_url):
                taskLogger({"status" : "error","message":"Failed to login as : {} , redirected back to {}".format(user,browser.current_url),"prefix":prefix},taskId)
                message = "redirected back to {}".format(browser.current_url)
                instanceCtr -= 1
                return False,message
            else:
                taskLogger({"status" : "success","message":"Logged in as : {}".format(user),"prefix":prefix},taskId)
                pickle.dump( browser.get_cookies() , open("./chrome/prof/{}.pkl".format(user),"wb"))
                instanceCtr -= 1
                return True,"success"
        
    except Exception as e:
        taskLogger({"status" : "error","message":"Failed Twitter Task with user {}  - {} ".format(user,e),"prefix":prefix},taskId)
        message = "{} ".format(e)
        instanceCtr -= 1
        return False,message


def connectTwitterSuperful(user,ses,prefix,taskId):
    try:
        session = twitterSessionHandler(user,ses,prefix,taskId,True) #connect is true
        endpoint = "https://www.superful.xyz/superful-api/v1/account/login/twitter/v1?next=https://www.superful.xyz/settings"
        while True:
            try:
                taskLogger({"status" : "process","message":"Fetching Twitter Auth","prefix":prefix},taskId)
                response = session.get(endpoint)
                if (response.status_code == 200):
                    responseData = json.loads(response.text)
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed to fetch Twitter Auth - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to fetch Twitter Auth - {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)

        twitterEnd = responseData['url']
        headers = {
            'Content-Type' :'application/x-www-form-urlencoded',
            'Origin':'https://api.twitter.com',
            'Referer':"https://www.superful.xyz/",
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0"
        }

        while True:
            try:
                taskLogger({"status" : "process","message":"Fetching Twitter authprization","prefix":prefix},taskId)
                response = session.get(twitterEnd, headers = headers)
                if (response.status_code == 200):
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed to authorize Twitter authorization - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to authorize Twitter authorization- {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)

        soup = BeautifulSoup(response.text,"html.parser")
        formItems = soup.find_all('input',{'type':"hidden"}) 
        dictObj = {}
        for item in formItems:
            dictObj[item['name']] = item['value']
        parsed = urlparse(dictObj['referer'])
        oauthToken = parse_qs(parsed.query)['oauth_token'][0]

        payload = {
            "authenticity_token" : dictObj['authenticity_token'],
            "redirect_after_login" :"https://api.twitter.com/oauth/authorize?oauth_token={}".format(oauthToken),
            "oauth_token" : oauthToken
        }

        headers = {
            'Content-Type' :'application/x-www-form-urlencoded',
            'Origin':'https://api.twitter.com',
            'Referer':"https://api.twitter.com"+dictObj['referer'],
            'user-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0"
        }

        while True:
            try:
                taskLogger({"status" : "process","message":"Authorizing Twitter account","prefix":prefix},taskId)
                response = session.post("https://api.twitter.com/oauth/authorize",data = payload, headers = headers)
                if (response.status_code == 200):
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed to authorize Twitter account - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to authorize Twitter account- {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)

        soup = BeautifulSoup(response.text,"html.parser")
        banItems = soup.find("meta",{'http-equiv':"refresh"}) 
        link = banItems['content'].replace("0;url=","")
       
        while True:
            try:
                taskLogger({"status" : "process","message":"Confirming Superful","prefix":prefix},taskId)
                response = session.get(link)
                if (response.status_code == 200):
                    if ("settings" in response.url):
                        break
                    else:
                        taskLogger({"status" : "error","message":"Wrong redirect - {}".format(response.url),"prefix":prefix},taskId)
                        time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to confirm Superful- {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)
        
        while (True):
            try:
                taskLogger({"status" : "process","message":"Checking if socials are connected","prefix":prefix},taskId)
                response = session.get("https://www.superful.xyz/superful-api/v1/account/settings")
                if (response.status_code == 200):
                    responseData = json.loads(response.text)
                    break
                else:
                    taskLogger({"status" : "error","message":"Failed socials account check - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(2)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed socials account check  - {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)

        connectedAccounts = responseData['account_connections']
        connectedTwitter = connectedAccounts[1]['username']

        if (connectedTwitter!=None):
            taskLogger({"status" : "success","message":"Succesfully connected Twitter account to Superful","prefix":prefix},taskId)
            return True,"success"
                        
        else:
            taskLogger({"status" : "error","message":"Failed to connect Twitter account to Superful - {}".format(response.status_code),"prefix":prefix},taskId)
            return False,"Twitter account not connected"
    except Exception as e:
        taskLogger({"status" : "error","message":"Failed connecting Twitter Account - {}".format(e),"prefix":prefix},taskId)
        return False,"Failed connecting Twitter Account - {}".format(e)



def connectDiscordRequestSuperful(token,prefix,session,taskId):
    discordString = "Connect Discord"
    try:
        taskLogger({"status" : "process","message":"Connecting Discord Account","prefix":token},taskId)
        
        while True:
            taskLogger({"status" : "process","message":"Getting Authorization redirect","prefix":prefix},taskId)
            response = session.get("https://www.superful.xyz/superful-api/v1/account/login/discord?next=https://www.superful.xyz/settings")
            if (response.status_code == 200):
                '''authLink = response.url
                authLink =  authLink.replace("%3A",":")
                authLink = authLink.replace("%2F", "/")
                authState = authLink.split("state=")[1]
                authLink = authLink.replace("https://discord.com/oauth2/authorize?","https://discord.com/api/oauth2/authorize?")'''
                responseData = json.loads(response.text)
                authLink = responseData['url']
                taskLogger({"status" : "success","message":"Got redirect","prefix":token},taskId)
                break
            else:
                taskLogger({"status" : "error","message":"Failed to get redirect : {}".format(response.status_code),"prefix":token},taskId)
                time.sleep(3)

        #authentication request module        
        ses = requests.session()
        ses.proxies.update(session.proxies)
        refLink = authLink.replace("/api","")
        cf_cookies(token,ses,taskId,refLink) #get cf cookies here
        headers = {
            'Accept-Language' : 'en-US,en;q=0.5',
            'Alt-Used' : 'discord.com',
            'Authorization' : token,
            'DNT' : "1",
            'Host':'discord.com',
            'Origin':'https://discord.com',
            'Referer': refLink,
            'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:102.0) Gecko/20100101 Firefox/102.0',
            'X-Debug-Options':'bugReporterEnabled',
            'X-Discord-Locale': 'en-US',
            'X-Super-Properties':'eyJvcyI6Ik1hYyBPUyBYIiwiYnJvd3NlciI6IkZpcmVmb3giLCJkZXZpY2UiOiIiLCJzeXN0ZW1fbG9jYWxlIjoiZW4tVVMiLCJicm93c2VyX3VzZXJfYWdlbnQiOiJNb3ppbGxhLzUuMCAoTWFjaW50b3NoOyBJbnRlbCBNYWMgT1MgWCAxMC4xNTsgcnY6MTAyLjApIEdlY2tvLzIwMTAwMTAxIEZpcmVmb3gvMTAyLjAiLCJicm93c2VyX3ZlcnNpb24iOiIxMDIuMCIsIm9zX3ZlcnNpb24iOiIxMC4xNSIsInJlZmVycmVyIjoiIiwicmVmZXJyaW5nX2RvbWFpbiI6IiIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjoxMzc2NTAsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9'
        }
        ses.headers.update(headers)    
        payload = {"permissions":"0","authorize":True}

        while True:
            headers['Content-Type'] = 'application/json'
            taskLogger({"status" : "process","message":"Authorizing Superful [Discord]","prefix":token},taskId)
            response = ses.post(authLink,data=json.dumps(payload),headers=headers)
            if (response.status_code == 200):
                responseJson = json.loads(response.text)
                redirectTo = responseJson['location']
                taskLogger({"status" : "success","message":"Authorized, redirecting [Discord]","prefix":token},taskId)
                break
            else:
                taskLogger({"status" : "error","message":"Failed authorizing Discord - {}".format(response.status_code),"prefix":token},taskId)
                time.sleep(3)
        
        while True:
            try:
                taskLogger({"status" : "process","message":"Confirming Superful","prefix":prefix},taskId)
                response = session.get(redirectTo)
                if (response.status_code == 200):
                        if ("/settings" in response.url):
                            taskLogger({"status" : "success","message":"Succesfully connected Discord account to Superful","prefix":prefix},taskId)
                            return True,"success"
                        else:
                            taskLogger({"status" : "error","message":"Failed to connect Discord account to Superful , redirect : {}".format(response.url),"prefix":prefix},taskId)
                            return False,"Failed to connect Discord account to Superful , redirect : {}".format(response.url)
                            #time.sleep(3)
                else:
                    taskLogger({"status" : "error","message":"Failed to connect Discord account to Superful - {}".format(response.status_code),"prefix":prefix},taskId)
                    time.sleep(3)
            except Exception as e:
                taskLogger({"status" : "error","message":"Failed to authorize Discord account- {}".format(e),"prefix":prefix},taskId)
                time.sleep(3)
        
    except Exception as e:
        taskLogger({"status" : "error","message":"Failed connecting Discord Account - {}".format(e),"prefix":token},taskId)
        return False,"Failed connecting Discord Account - {}".format(e)
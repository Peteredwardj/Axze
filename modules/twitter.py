from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
from app_modules.taskLogger import taskLogger
import os,pickle

instanceCtr = 0 


def fileBrowser(user):
    dirPath = "./chrome/prof"
    profDirExist = os.path.exists(dirPath)
    if (profDirExist == False):
        os.makedirs(dirPath)
        
    fileAddr = "{}/{}.pkl".format(dirPath,user)
    found = os.path.isfile(fileAddr) 
    return found

def manualFollow(user,password,twitterReq,prefix,taskId):
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
        opts = webdriver.ChromeOptions()
        opts.add_argument("user-agent={}".format(userAgent))
        opts.add_argument("--headless")
        opts.add_experimental_option('excludeSwitches', ['enable-logging'])
        browser = webdriver.Chrome(options=opts,executable_path='./chrome/chromedriver')
        if (fileBrowser(user) == False): #profile not found 
            taskLogger({"status" : "process","message":"Beginning one time twitter profile setup - User {}".format(user),"prefix":prefix},taskId)
            browser.get("https://twitter.com/i/flow/login")
            time.sleep(3)
            loginDial = browser.find_element_by_tag_name("input")
            loginDial.send_keys(user)
            taskLogger({"status" : "process","message":"Logging user {}".format(user),"prefix":prefix},taskId)
            browser.find_element_by_xpath('//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div/div[6]/div').click() #next button
            time.sleep(2)
            if ("Enter your phone number or username" in browser.page_source):
                taskLogger({"status" : "process","message":"Solving twitter challenge","prefix":prefix},taskId)
                instanceCtr -= 1
                return

            taskLogger({"status" : "process","message":"Logging password","prefix":prefix},taskId)
            passButt = browser.find_element_by_name("password")
            passButt.send_keys(password)
            taskLogger({"status" : "process","message":"Authenticating","prefix":prefix},taskId)
            browser.find_element_by_xpath('//*[@id="layers"]/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]').click() #login button
            time.sleep(2.5)
            if ("home" not in browser.current_url):
                taskLogger({"status" : "error","message":"Failed to login as : {} , redirected back to {} - check credentials!".format(user,browser.current_url),"prefix":prefix},taskId)
                message = "redirected back to {}".format(browser.current_url)
                instanceCtr -= 1
                return False,message
            else:
                taskLogger({"status" : "success","message":"Logged in as : {}".format(user),"prefix":prefix},taskId)
                pickle.dump( browser.get_cookies() , open("./chrome/prof/{}.pkl".format(user),"wb"))
        else:
            taskLogger({"status" : "process","message":"Loading existing profile {}".format(user),"prefix":prefix},taskId)
            cookies = pickle.load(open("./chrome/prof/{}.pkl".format(user), "rb"))
            browser.get("https://twitter.com/")
            for cookie in cookies:
                browser.add_cookie(cookie)

        taskLogger({"status" : "process","message":"Fetching page","prefix":prefix},taskId)
        browser.get("https://twitter.com/intent/user?screen_name={}".format(twitterReq))
        time.sleep(2)
        taskLogger({"status" : "process","message":"Following {}".format(twitterReq),"prefix":prefix},taskId)
        browser.find_element_by_xpath('/html/body/div[1]/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div[2]/div[1]/div').click()
        taskLogger({"status" : "success","message":"{} followed {}".format(user,twitterReq),"prefix":prefix},taskId)
        message = "success"
        instanceCtr -=1 
        return True,message
    except Exception as e:
        taskLogger({"status" : "error","message":"Failed Twitter Task with user {}  - {} ".format(user,e),"prefix":prefix},taskId)
        message = "{} ".format(e)

    instanceCtr -= 1
    return False,message




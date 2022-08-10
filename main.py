from __future__ import print_function, unicode_literals
from cmath import nan
from turtle import clear
from PyInquirer import prompt, Separator,Token,style_from_dict
from colored import fg, attr
import datetime,os,threading,json,time,re,uuid,requests
import pandas as pd
import xlwings as xw
import csv
from sys import platform
from modules.mint import mint
from modules.invite import inviteTask
from modules.premint import premint
from app_modules.discordLog import testLog
from app_modules.version import version
from app_modules.taskLogger import lightblue,green,red,yellow,reset,expColor,yellow2
from app_modules.apiModules import checkNode,checkCapMonster
from app_modules.profileUtils  import profileManager
from app_modules.splashScreen import loadSplash
from app_modules.clearCache import clearCache
from pypresence import Presence
from datetime import date
from eth_account import Account
from flask import Flask,jsonify,request
from waitress import serve
from flask_restful import Resource,Api
import shutil,tempfile


global licenseUser,currentSheet,quickMintSheet,quickTaskThreads
currentObjectSet = []
quickTaskThreads=[]
exitVar = False
premintTask = False
quickMintTask = False
serverQuickMint = False
serverActive = False
threadsArr=[]
profileDict = {}

style = style_from_dict({
    Token.QuestionMark: '#01b3b6',
    Token.Selected: '#2488cf bold',
    Token.Instruction: '#01b3b6 ',  # default
    Token.Answer: '#01b3b6',
    Token.Question: '#01b3b6 ',   #2488cf
})



mainMenu = [
    {
        'type': 'list',
        'name': 'main',
        'message': 'Choose an option',
        'choices': [
            'Start Mint Tasks [ETH]',
            'Start Quick Mint [ETH]',
            #'Start Smart Quick Mint [ETH]',
            'Start Wallet Generator [ETH]',
            'Start Premint Modules',
            'Profile Management',
            'Settings'
        ]
    }
]


app = Flask(__name__)
api =Api(app)


def server_start():
    global serverActive
    try:
        serverActive = True
        serve(app, host="0.0.0.0", port=7373)

    except:
        serverActive = False



@app.route("/")
def index():
    return "<h1>Axze Quick Mint QT</h1>"

@app.route("/qm",methods=['GET'])
def update():
    global quickTaskThreads
    if request.method=="GET":
        clearConsole()
        contractToRun = request.args.get('contractAddress')
        quantity = request.args.get('qty')
        price = request.args.get('price')
        mintFunc = request.args.get('func')
        additionalParam = {'quantity':quantity,'price':price,'func':mintFunc}
        taskHandler('quickMint',contractToRun,additionalParam)
        return "<h1>Starting Axze One click mint..</h1>"

def osResize():
    if platform == "darwin":
        os.system('$eclipse >/dev/null resize -s 40 130')
    elif platform == "win32":
        os.system('mode con: cols=130 lines=4000')

def clearConsole():
    if platform == "darwin":
        os.system('clear')
    elif platform == "win32":
        os.system('cls')

def questionPrompt(questions):
    answers = prompt(questions, style=style)
    if (len(answers)!=0):
        optionHandler(answers)

def taskChecker():
    global currentSheet,currentObjectSet
    PATH = 'files/tasks.xlsx'
    assert os.path.isfile(PATH)
    
    while True:
        try:    
            tmp = tempfile.NamedTemporaryFile(delete=False , dir='cache')
            try:
                shutil.copyfile(os.path.abspath(PATH), tmp.name)
            except:
                print(yellow+"Live control error - check that none of the fields are empty and try again!"+reset)
                continue
            tempPath = tmp.name
            sheetData = pd.read_excel(tempPath,engine='openpyxl',header = 0,names=['profile','contractAddress','mintFunc','quantity','amount','maxFeePerGas','maxPriorityFee','mode','monitorFunction','params','gasLimit','cancel'],converters={'amount': lambda x: str(x),'params': lambda x: str(x),'cancel':lambda x:str(x)})
            sheetData = sheetData.dropna()
            if (not sheetData.equals(currentSheet)):
                currentSheet = sheetData
                counter = 0
                for i in sheetData.itertuples():
                    maxFeePerGas = i.maxFeePerGas
                    maxPriorityFee = i.maxPriorityFee
                    try:
                        if ((i.cancel).lower()=="n"):
                            cancel = False
                        else:
                            cancel = True
                    except:
                        cancel = False
                    if (currentObjectSet[counter]['maxFeePerGas']!=maxFeePerGas or currentObjectSet[counter]['maxPriorityFee']!=maxPriorityFee or currentObjectSet[counter]['cancel']!=cancel):
                        currentObjectSet[counter]['object'].update(maxFeePerGas,maxPriorityFee,cancel)
                    counter+=1
            tmp.close()
            os.unlink(tmp.name)
        except PermissionError:
            print(yellow+"Live control error - Permission Error"+reset)
        

def quickMintChecker():
    global quickMintSheet,currentObjectSet
    PATH = 'files/quickMintControl.xlsx' 
    assert os.path.isfile(PATH)
    while True:
        try:    
            tmp = tempfile.NamedTemporaryFile(delete=False,  dir='cache')
            try:
                shutil.copyfile(os.path.abspath(PATH), tmp.name)
            except:
                print(yellow+"Live Control Error -check that none of the fields are empty and try again!"+reset)
                continue
            tempPath = tmp.name
            sheetData = pd.read_excel(tempPath,engine='openpyxl',header = 0,names=['maxFeePerGas','maxPriorityFee','cancel'])
            sheetData = sheetData.dropna()
            if (not sheetData.equals(quickMintSheet)):
                quickMintSheet = sheetData
                counter = 0
                for i in sheetData.itertuples():
                    maxFeePerGas = i.maxFeePerGas
                    maxPriorityFee = i.maxPriorityFee
                    try:
                        if ((i.cancel).lower()=="n"):
                            cancel = False
                        else:
                            cancel = True
                    except:
                        cancel = False
                    if (currentObjectSet[counter]['maxFeePerGas']!=maxFeePerGas or currentObjectSet[counter]['maxPriorityFee']!=maxPriorityFee or currentObjectSet[counter]['cancel']!=cancel):
                        currentObjectSet[counter]['object'].update(maxFeePerGas,maxPriorityFee,cancel)
                    counter+=1
                
            tmp.close()
            os.unlink(tmp.name)
        except PermissionError:
            print(yellow+"Live control error - Permission Error"+reset)
            

def profileHandler():
    global profileDict
    print(lightblue+"Loading Profiles..\nPlease input your wallet.xlsx password on the pop out window!"+reset)
    PATH = 'files/wallet.xlsx'
    wb = xw.Book(PATH)
    sheet = wb.sheets['Sheet1']
    df = sheet['A1:C2000'].options(pd.DataFrame, index=False, header=True).value
    df = df.dropna()
    if (len(df) ==0):
        print(red + "No Profiles created yet!" + reset)
    else:
        for i in df.itertuples():
            profile= i._1
            wallet = i._2
            apiKey = i._3
            profileDict[profile] = {'wallet' : wallet,'apiKey' :apiKey}
        print(green + "Succesfully loaded profiles. Hit Ctrl+C anytime to go back to the menu!"+reset)


def taskHandler(mode,inputUrl,additionalParam = None):
    global threadsArr,exitVar,currentSheet,currentObjectSet,premintTask,quickMintTask,quickMintSheet
    try:
        if (len(profileDict)==0):
            print(red+ "No profiles created yet, create some to start tasks!"+reset)
            profileHandler()
            return
        profiles = profileDict
        if (mode=="ethMint"):
            PATH = 'files/tasks.xlsx'
            sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile','contractAddress','mintFunc','quantity','amount','maxFeePerGas','maxPriorityFee','mode','monitorFunction','params','gasLimit','cancel'],converters={'amount': lambda x: str(x),'params': lambda x: str(x),'cancel':lambda x:str(x)})
            #sheetData = sheetData.dropna()
            currentSheet = sheetData
            for i in sheetData.itertuples():
                profile = i.profile
                contractAddress = i.contractAddress
                mintFunc = i.mintFunc
                quantity = i.quantity
                amount = float(i.amount)
                maxFeePerGas = i.maxFeePerGas
                maxPriorityFee = i.maxPriorityFee
                absoluteMax = 0
                autoAdjust = False
                gasConfig = "default"
                mode = (i.mode).lower()

                if (mode == "flipstate" or mode == "monitor"):
                    functionToMonitor = i.monitorFunction
                    monitorParams = i.params
                    gasLimit = i.gasLimit

                    if (monitorParams == "none" or monitorParams == "None"):
                        paramToMonitor = "none"
                    elif ("=" not in monitorParams):
                        paramToMonitor = monitorParams
                    else:
                        paramToMonitor = {}
                        splitParams = monitorParams.replace(" ","").split(",")
                        for param in splitParams:
                            extractedParams = param.split("=")
                            paramToMonitor[extractedParams[0]] = extractedParams[1]
                else:
                    gasLimit = None
                    functionToMonitor = None
                    monitorParams = None
                
                try:
                    if ((i.cancel).lower() =='n'):
                        cancel = False
                    else:
                        cancel = True
                except:
                    cancel = False
                
                if (maxFeePerGas == 0 or maxPriorityFee==0):
                    gasConfig = "auto"
                if (profile not in profiles):
                    print(red+"{} not found in wallet.xlsx, skipping!".format(profile)+reset)
                else:
                    objectDict = {"object":mint(amount,quantity,profiles[profile]['wallet'],profiles[profile]['apiKey'],contractAddress,mintFunc,maxFeePerGas,maxPriorityFee,absoluteMax,autoAdjust,profile,gasConfig,mode,gasLimit,functionToMonitor,paramToMonitor),"maxFeePerGas" : maxFeePerGas, "maxPriorityFee": maxPriorityFee , "cancel" : cancel}
                    currentObjectSet.append(objectDict)
                    #t = threading.Thread(target=mint(amount,quantity,profiles[profile]['wallet'],profiles[profile]['apiKey'],contractAddress,mintFunc,maxFeePerGas,maxPriorityFee,absoluteMax,autoAdjust,profile,gasConfig,mode).order)
                    t = threading.Thread(target=objectDict['object'].order)
                    threadsArr.append(t)
        elif (mode == "quickMint"):
            quickMintTask = True
            maxFeePerGas = 0
            maxPriorityFee = 0
            absoluteMax = 0
            autoAdjust = False
            gasConfig = "auto"
            PATH = 'files/quickProfiles.xlsx'
            sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile'])
            sheetData = sheetData.dropna()
            
            #initialize quickmint control sheet here : 
            PATH = 'files/quickMintControl.xlsx'
            controlSheet = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['maxFeePerGas','maxPriorityFee','cancel'])
            controlSheet = controlSheet.dropna()
            quickMintSheet = controlSheet

            wb = xw.Book(PATH) #forces open quick mint control center if not opened yet

            if (inputUrl != None):
                print(lightblue+"Axze is minting contract : {}".format(inputUrl)+reset)

            profileGroupDict = {}
            profileGroups = profileManager("read",profileDict)     #profile group screen 
            if (len(profileGroups) == 0):
                print(lightblue+"Running all Quick Profiles!"+reset)
                profileGroupArr = profiles
            else:
                ctrGroup = 0 
                for profileGroup in profileGroups:   #read existing profile groups
                    ctrGroup += 1 
                    profileGroupDict[str(ctrGroup)] = profileGroup
                    print("[{}] - {}".format(ctrGroup,profileGroup))
                profileGroupDict[str(ctrGroup+1)] = "quickProfiles"
                print("[{}] - {}".format(ctrGroup+1,"Run all quick profiles"))

                runChoice = input(lightblue+"Input profile group to run Quick Mint for: "+reset)
                if (profileGroupDict[runChoice] == "quickProfiles"):
                    if (len(sheetData) ==0):
                        print(red+"No Quick Profiles made!"+reset)
                        return
                    print(lightblue + "Running all quick profiles" +reset)
                    profileGroupArr = profiles
                else:
                    profileGroupArr = profileGroups[profileGroupDict[runChoice]]
                    
            if (inputUrl=="none"):
                contractAddress = input(lightblue+"Enter contract to run: "+reset)
            else:
                contractAddress = inputUrl
            
            if (additionalParam == None):
                skipQuick = False
                amount = float(input(lightblue+"Enter Amount per task (Ether): "+reset))
                quantity = int(input(lightblue+"Enter Quantity to run per task: "+reset))
                mintFunc = input(lightblue+ "Input mint function, hit Enter to skip and do autoscrape: "+reset)
                if (mintFunc == ""):
                    mintFunc = "default"
                
            else:
                amount = additionalParam['price']
                quantity = additionalParam ['quantity']
                mintFunc = additionalParam['func']
                skipQuick = True
            
            autoGas = input(lightblue+ "Run custom gas? input y or hit Enter to skip and run auto: "+reset)
            if (autoGas=="y"):
                gasConfig = "manual"
                maxFeePerGas = float(input(lightblue+ "Enter Max Fee per gas in GWEI : "+reset))
                maxPriorityFee = float(input(lightblue+"Enter Max Priority Fee in GWEI : "+reset))

            if (profileGroupArr == profiles):
                for i in sheetData.itertuples():
                    profile = i.profile
                    if (profile not in profiles):
                        print(red+"{} not found in wallets.xlsx, skipping!".format(profile)+reset)
                    else:
                        objectDict = {"object":mint(amount,quantity,profiles[profile]['wallet'],profiles[profile]['apiKey'],contractAddress,mintFunc,maxFeePerGas,maxPriorityFee,absoluteMax,autoAdjust,profile,gasConfig,"experimental"),"maxFeePerGas" : maxFeePerGas, "maxPriorityFee": maxPriorityFee , "cancel" : False}
                        currentObjectSet.append(objectDict)
                        t = threading.Thread(target=objectDict['object'].order)
                        threadsArr.append(t)
            else:
                for profile in profileGroupArr:
                    if (profile not in profiles):
                        print(red+"{} not found in wallet.xlsx, skipping!".format(profile)+reset)
                    else:
                        objectDict = {"object":mint(amount,quantity,profiles[profile]['wallet'],profiles[profile]['apiKey'],contractAddress,mintFunc,maxFeePerGas,maxPriorityFee,absoluteMax,autoAdjust,profile,gasConfig,"experimental"),"maxFeePerGas" : maxFeePerGas, "maxPriorityFee": maxPriorityFee , "cancel" : False}
                        currentObjectSet.append(objectDict)
                        t = threading.Thread(target=objectDict['object'].order)
                        threadsArr.append(t)

            if (skipQuick):
                clearConsole()
                for t in threadsArr:
                    t.start()
                exitVar = False

        elif (mode == "disconnect"):
            premintTask = True
            PATH = 'files/premintDisconnect.xlsx'
            sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile'])
            sheetData = sheetData.dropna()
            for i in sheetData.itertuples():
                    profile = i.profile
                    if (profile not in profiles):
                        print(red+"{} not found in wallet.xlsx, skipping!".format(profile)+reset)
                    else:
                        t = threading.Thread(target=premint(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],'-','password','discord','accessToken','accessSecret','consumerKey','consumerSecret',mode,profile,None,None).connect)
                        threadsArr.append(t)
        else:
            premintTask = True
            '''if (mode == "check" or mode == "connect" or mode == "connect-local"):
                pass
            else:
                mode = "default"'''

            PATH = 'files/premintProfiles.xlsx'
            taskCtr = 0
            sourceWallet = ""
            transferProfileArr = []

            sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile','discord','twitter','loginMode','password','consumerKey','consumerSecret','accessToken','accessSecret'],na_filter=False)
            for i in sheetData.itertuples():
                if (i.profile == ''):
                    continue

                profile = i.profile
                if (profile not in profiles):
                    pass
                else:
                    wallet = profiles[profile]['wallet']
                    if (sourceWallet == ""):
                        sourceWallet = wallet
                    else:
                        transferProfileArr.append(wallet)
                    taskCtr += 1
            transferProfileArr.append(sourceWallet)
            discordMode = 'default'
            reactParam = None
            runPremintChain = False
            forceTransfer = False
            customField = None
            if ("premint" in mode):
                premintChain = input(lightblue+"Run Premint Chain? [y/n]: "+reset)
                if (premintChain.lower() == "y"):
                    amount = 0
                    maxFeePerGas = float(input(yellow2+ "Enter Max Fee per gas in GWEI : "+reset))
                    maxPriorityFee = float(input(yellow2+"Enter Max Priority Fee in GWEI : "+reset))
                    totalEstimatedGas = str(taskCtr*21000*maxFeePerGas*10**-9)[:6]
                    agreeGas = input(yellow2+"Estimated max total gas spent for {} tasks is {}E\nContinue Premint Chain?[y/n]: ".format(taskCtr,totalEstimatedGas)+reset)
                    if (agreeGas.lower() == "y"):
                        forceTransferChoice= input(yellow2+"Force transfer to next wallet on submit failure?[y/n]: "+reset)
                        if (forceTransferChoice.lower() == "y"):
                            forceTransfer = True
                        else:
                            forceTransfer = False
                        runPremintChain = True
                runDiscord = input(lightblue+"Run Discord Modules for this premint? [y/n]: "+reset)
                if (runDiscord.lower() == "y"):
                    discordChoiceInput = input(yellow2+"[1] Message React [2] Wick [Coming Soon] [3] Captcha Bot [Coming Soon]\nChoose Discord verification method: "+reset)
                    if (discordChoiceInput == "1"):
                        reactParam = {}
                        messageInputLink = input("Input the message link to react to: ")
                        emojiId = input(yellow2+"Input the emoji ID for custom emojis (i.e axzelogo:1001971513513214075) OR Copy paste the emoji for standard emojis\n"+reset+"Input here (Ignore the weird characters): ")
                        reactParam['messageLink'] = messageInputLink
                        reactParam['emoji'] = emojiId
                        discordMode = "react"
                runCustomField = input(lightblue+"Run Custom Field module? [y/n]:  "+reset)
                if (runCustomField.lower() == "y"):
                    customFieldChoiceInput = input(yellow2+"[1] Email custom field\nChoose custom field type: "+reset)
                    if (customFieldChoiceInput == "1"):
                        catchallInput = input("Input catchall domain (e.x customDomain.com): ")
                        catchallInput = catchallInput.replace(" ","")
                        customField = {}
                        customField['type'] = 'email'
                        customField['content'] = catchallInput

            sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile','discord','twitter','loginMode','password','consumerKey','consumerSecret','accessToken','accessSecret'],na_filter=False)
            #sheetData = sheetData.dropna()

            currentSheet = sheetData
            profileIterator = 0
            for i in sheetData.itertuples():
                if (i.profile == ''):
                    continue

                profile = i.profile
                if (i.discord == ''):
                    discord = "Unspecified"
                else:
                    discord = i.discord
                twitter = i.twitter
                loginMode = i.loginMode
                loginMode = str((i.loginMode)).lower()
                if (loginMode.replace(" ","") =="man"):
                    password = i.password
                    consumerKey = ""
                    consumerSecret = ""
                    accessToken = ""
                    accessSecret =""
                else: #api login
                    password ="api"
                    consumerKey = i.consumerKey
                    consumerSecret = i.consumerSecret
                    accessToken = i.accessToken
                    accessSecret = i.accessSecret
                
                if (profile not in profiles):
                    pass
                    #print(red+"{} not found in wallets.xlsx, skipping!".format(profile)+reset)
                else:
                    if (runPremintChain == False):
                        t = threading.Thread(target=premint(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],twitter,password,discord,accessToken,accessSecret,consumerKey,consumerSecret,mode,profile,None,customField,discordMode,reactParam).connect)
                        threadsArr.append(t)
                    else:
                        if (profileIterator == 0):
                            clearConsole()
                        transferTask = {'forceTransfer' : forceTransfer,'nextWallet':transferProfileArr[profileIterator],'maxGasFee':maxFeePerGas,'maxPriorityFee':maxPriorityFee,'amount':amount}
                        premintObj = premint(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],twitter,password,discord,accessToken,accessSecret,consumerKey,consumerSecret,mode,profile,transferTask,customField,discordMode,reactParam)
                        continueTasks = premintObj.connect()
                        if (continueTasks):
                            profileIterator += 1
                        else:
                            print(red+"\nPremint chain stopped"+reset)
                            time.sleep(1000000)
                        


        exitVar=True
    except Exception as e:
        print(red+"Task handler error - {}".format(e)+reset)

    

def writeConfig(dataObject):
    with open('app_data/config.json') as f:
        data = json.load(f)
        if (dataObject['type'] == "webhook"):
            data["Webhook"] = dataObject['content']
        elif (dataObject['type'] == "capMonster"):
            data["capMonster"] = dataObject['content']
        else: #write node config here
            data["Node"] = dataObject['content']

        with open('app_data/config.json','w') as p:
            json.dump(data, p,indent=4)
            p.close
    f.close()

def discordModules(mode):
    global threadsArr,exitVar
    clearConsole()
    f=open('files/discordAccounts.txt',"r")
    if ('invites' in mode):
        inviteCode = mode['invites']
        delay = mode['delay']
    tasks = (f.read()).split("\n")
    tasks=[task for task in tasks if task!='']
    for task in range (0,len(tasks)):
        if (mode['mode'] == "safe"):
            inviteTaskObj = inviteTask(tasks[task],inviteCode)
            inviteTaskObj.initialize()
            time.sleep(delay)
        else:
            t = threading.Thread(target=inviteTask(tasks[task],inviteCode).initialize)
            threadsArr.append(t)
    f.close()
    
    exitVar=True



def optionHandler(answer):
    global exitVar,threadsArr,serverQuickMint
    if ("main" in answer): #main menu option
        option = answer['main']
        if (option == "Start Mint Tasks [ETH]"):
            taskHandler("ethMint","none")
        elif (option =="Start Quick Mint [ETH]"):
            taskHandler("quickMint","none")
        elif (option == 'Start Smart Quick Mint [ETH]'):
            t=threading.Thread(target=server_start)
            threadsArr.append(t)
            serverQuickMint = True
            exitVar = True
        elif (option =="Start Wallet Generator [ETH]"):
            numToGen = int(input(lightblue+"Input number of wallets to generate : "+reset))
            walletGenerator(numToGen)
        elif (option == "Start Discord Modules"):
            question = [{
                'type' : 'list',
                'name' : 'Discord Menu',
                'message' : 'Choose module to run',
                'choices' : [
                    'Invites'
            ]
            }]
            questionPrompt(question)
        elif (option == "Settings"):
            question = [{
                'type' : 'list',
                'name' : 'settings',
                'message' : 'Choose configuration to change',
                'choices' : [
                    'Discord Webhook',
                    'Node Configuration',
                    'Capmonster API configuration'
                ]
            }]
            questionPrompt(question)
        elif (option == "Start Premint Modules"):
            question = [{
                'type' : 'list',
                'name' : 'Premint Menu',
                'message' : 'Choose module to run',
                'choices' : [
                    'Premint Entry',
                    'Premint Connect',
                    'Premint Disconnect',
                    'Winner Check',
            ]
            }]
            questionPrompt(question)
        elif (option == "Profile Management"):
            profileOption = input(lightblue+"[1] Create/Edit profile groups [2] View profile groups: "+reset)
            if profileOption == "1":
                profileManager("write",profileDict)
            else:
                profileManager("read",profileDict)
    elif ("settings" in answer):
        option = answer['settings']
        if (option == "Discord Webhook"):
            configureOption = input(lightblue+"[1] Configure Webhook [2] Test Webhook : "+reset)
            if (configureOption == "1"):
                '''question = [ {
                        'type': 'input',
                        'name': '{} Setting'.format(option),
                        'message': 'Input {}'.format(option)
                    }]
                questionPrompt(question)'''
                discordInput = input(lightblue+ "Enter your Dicord Webhook URL : "+reset)
                dataObject = {'type' : "webhook", 'content': discordInput}
                writeConfig(dataObject)
                print(yellow + "Sending test webhook.."+reset)
                testLog()
            else:
                print(yellow + "Sending test webhook.."+reset)
                testLog()

        elif (option == "Capmonster API configuration"):
            capMonsterInput = input(lightblue+"Input Capmonster API Key : "+reset)
            dataObject = {'type' : "capMonster", 'content': capMonsterInput}
            writeConfig(dataObject)
            result = checkCapMonster()
            print(green+"Updated CapMonster API Key - {}!".format(result)+reset)

        else:
            nodeOption = input(lightblue+"Input RPC Node URL : "+reset)
            dataObject = {'type' : "node", 'content': nodeOption}
            writeConfig(dataObject)
            checkNode()
            print(green+"Updated RPC Node!"+reset)
    elif ("Discord Menu" in answer):
        if (answer["Discord Menu"] == "Invites"):
            delay = 2
            simult= input(lightblue+"[1] Fast Mode [2] Safe Mode : "+reset)
            discInviteLink = input(lightblue+ "Input discord invite code (i.e : rwqDjWJy) : "+reset)
            if (simult == "2"):
                delay= float(input(lightblue+"Input custom delay between each joins (In seconds, i.e : 2) : "+reset))
                mode = "safe"
            else:
                mode = "fast"
            discordModules({'invites':discInviteLink,'delay':delay,'mode':mode})
    elif ("Premint Menu" in answer):
        if (answer["Premint Menu"] == "Premint Connect"):
            modeChoice= input(lightblue+"Run One time Twitter accounts setup with Proxies?[y/n]: "+reset)
            if (modeChoice.lower() == "y"):
                mode = "connect"
            else:
                mode = "connect-local"

            taskHandler(mode,"https://www.premint.xyz/home/")
        elif (answer["Premint Menu"] == "Premint Disconnect"):
            taskHandler("disconnect","https://www.premint.xyz/home/")
        else:
            inputUrl = input(lightblue+ "Input Premint link : "+reset)
            if (answer["Premint Menu"] == "Premint Entry"):
                modeChoice= input(lightblue+"Run One time Twitter accounts setup with Proxies?[y/n]: "+reset)
                if (modeChoice.lower() == "y"):
                    mode = "premint"
                else:
                    mode = "premint-local"
                taskHandler(mode,inputUrl)
            else:
                print(lightblue+ "Checking entries result for : {}".format(inputUrl)+reset)
                taskHandler("check",inputUrl)
            
    elif ("Discord Webhook Setting" in answer):
        dataObject = {'type' : "webhook", 'content': answer["Discord Webhook Setting"]}
        writeConfig(dataObject)
        print(yellow + "Sending test webhook.."+reset)
        testLog()
    
    else:
        print(answer)
        pass

def discordPresence():
    try:
        client_id = '990843620183650304' 
        startTime=time.time()
        RPC = Presence(client_id)  
        RPC.connect() 
        RPC.update(state="v{}".format(version),large_image="axze",start=startTime)
    except Exception as e:
        pass

def authenticate(licenseKey):
    global licenseUser
    try:
        hardware_id = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        payload={
            "key":licenseKey,
            "hwid":str(hardware_id),
            "version":str(version)
        }
        headers={'Content-Type':'application/json'}
        authUrl = "https://api.exath.io/api/nexusAuth"
        response=requests.post(authUrl,data=json.dumps(payload),headers=headers)
        if (response.status_code == 200):
            licenseUser=json.loads(response.text)["user"]
            print(green+"Succesfully Authenticated"+reset)
            return True
        elif (response.status_code ==429):
            print(red + " You are not running the newest version, you are currently running : v{}".format(version))
            return False
        elif (response.status_code == 403):
            print(red + " Key invalid, or key already binded to another machine!"+reset)
            return False
    except Exception as e:
        print(red+"An error occured, retrying authentication - {}".format(e)+reset)
        time.sleep(1)
        authenticate(licenseKey)


def login():
    toReturn = False
    with open('app_data/license.json') as f:
        data = json.load(f)
        if (data['License']==''):
            licenseKey=input(yellow+ "Please input your license Key : "+reset)
            toReturn = authenticate(licenseKey)
            if (toReturn):
                data['License'] = licenseKey
                with open('app_data/license.json','w') as p:
                    json.dump(data, p,indent=4)
                    p.close()
        else:
            print(yellow+"Verifying license.."+reset)
            toReturn = authenticate(data['License'])
    f.close()
    return toReturn


def walletGenerator(numToGen):
    header = ['Wallet Address','Private Key']
    generatedData = []
    for _ in range(numToGen):
        walletArr = []
        acct = Account.create('KEYSMASH FJAFJKLDSKF7JKFDJ 1530')
        walletArr.append(acct.address)
        walletArr.append(acct.key.hex())
        generatedData.append(walletArr)

    today = date.today()
    dateStr = today.strftime("%b-%d-%Y")
    fileName = "./files/generatedWallets-{}.csv".format(dateStr)

    with open(fileName, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(generatedData)
    f.close()
    print(green+"Generated {} wallets, saved in {}".format(numToGen,fileName)+reset)


def menuInitializer():
    osResize()
    clearConsole()
    if (serverActive == False):
        serverStr = "OCQM Inactive"
        colorStr = red
    else:
        serverStr = "OCQM Active"
        colorStr = green


    print(loadSplash(licenseUser))
    continueVar = input("")
    clearConsole()

    print(expColor+'''
 ___  _ _  ____ _____ 
||=|| \\//   //  ||==  
|| || //\\  //__ ||___ '''+yellow2+'v{}'.format(version)+colorStr+" {}\n".format(serverStr)+reset)
    print('Welcome to AXZE {}!'.format(licenseUser)+reset)



def main():
    clearCache()
    if (not login()):
        time.sleep(100000)
    discordPresence()
    #fire up server
    t=threading.Thread(target=server_start)
    t.start()
    clearConsole()

    menuInitializer()
    profileHandler()

    
    while True:
        try:
            if (not exitVar):
                questionPrompt(mainMenu)
            else:
                break
        except KeyboardInterrupt:
            pass
    
    if (len(threadsArr)>0):
        clearConsole()

        '''if (serverQuickMint):
            clearConsole()
            print(lightblue+"Exath Smart Quick Mint Read"+reset)'''

        if (quickMintTask == True):
            threadsArr.append(threading.Thread(target = quickMintChecker))
        
        if (premintTask == False and quickMintTask ==False and serverQuickMint==False):
            threadsArr.append(threading.Thread(target = taskChecker))

        for t in threadsArr:
            t.start()

        for t in threadsArr:
            t.join()      

        time.sleep(1000000)
    else:
        print(red+"No Tasks found!"+reset)
    

    


if __name__ == "__main__":
    main()


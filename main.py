from __future__ import print_function, unicode_literals
from cmath import nan
from email.policy import default
from queue import PriorityQueue
from PyInquirer import prompt, Separator,Token,style_from_dict
from colored import fg, attr
import datetime,os,threading,json,time,re,uuid,requests
import pandas as pd
import xlwings as xw
import csv
from sys import platform
from modules.mint import mint
from modules.invite import inviteTask
from modules.pencil import pencil
from modules.premint import premint
from modules.superful import superful
from modules.hoard import hoard
from modules.humanKind import humanKind
from modules.nftconsolidation import consolidateNFT
from modules.ethconsolidation import consolidateETH
from modules.orangeComet import orangeComet
from modules.heyMint import heyMint
from app_modules.discordLog import testLog,remoteWebhook
from app_modules.version import version
from app_modules.taskLogger import lightblue,green,red,yellow,reset,expColor,yellow2
from app_modules.apiModules import checkNode,checkCapMonster,checkRemoteProfileGroup,p_subscribe_key
from app_modules.profileUtils  import profileManager
from app_modules.splashScreen import loadSplash
from app_modules.clearCache import clearCache
from app_modules.protect import initializeUser,checker
from app_modules.setupPrompt import basicCheck
from pypresence import Presence
from datetime import date
from eth_account import Account
from flask import Flask,jsonify,request
from waitress import serve
from flask_restful import Resource,Api
import shutil,tempfile
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration,PNReconnectionPolicy
from pubnub.exceptions import PubNubException
from pubnub.enums import PNStatusCategory
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub, SubscribeListener
from pubnub.callbacks import SubscribeCallback


global licenseUser,currentSheet,quickMintSheet,quickTaskThreads,licenseKeyGlobal
currentObjectSet = []
quickTaskThreads=[]
exitVar = False
premintTask = False
quickMintTask = False
serverQuickMint = False
serverActive = False
threadsArr=[]
profileDict = {}
timeoutExit = 1000000
hoardWalletDict = {"wallet" : "" , "key": ""}

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
            'Start Mint Tasks',
            'Start Quick Mint',
            'Start Hoard Modules',
            #'Start Smart Quick Mint',
            'Start Wallet Generator',
            'Start Premint Modules',
            'Start Superful Modules',
            'Start HeyMint Modules',
            'Start Custom Raffle Modules',
            'Start Consolidation Modules',
            'Axze Remote Task',
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

###connector setup###
global pubnub
class MySubscribeCallback(SubscribeCallback):
    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            print(red+"Axze Remote Mint disconnected, attempting to reconnect!"+reset)
            pubnub.reconnect()    #Attempt To reconnect 
        elif status.category == PNStatusCategory.PNTimeoutCategory:
            print(red+"Axze Remote Mint disconnected, attempting to reconnect!"+reset)
            pubnub.reconnect()
 
    def presence(self, pubnub, presence):
        pass
 
    def message(self, pubnub, message):
        messageObj = message.message
        licenseKey = messageObj['license']
        profileGroup = checkRemoteProfileGroup()            
        if (licenseKey == licenseKeyGlobal): #for user
            amount = float(messageObj['value'])
            quantity = messageObj['qty']
            contractAddress = messageObj['contractAddress']
            mintFunc = messageObj['function']
            maxFeePerGas = float(messageObj['maxGasFee'])
            maxPriorityFee = float(messageObj['maxPriorityFee'])
            absoluteMax = 0
            autoAdjust = False
            gasLimit = None
            functionToMonitor = None
            paramToMonitor = None
            mode = "Axze Remote Mint"
            if (maxFeePerGas == 0 or maxPriorityFee==0):
                gasConfig = "auto"
            else:
                gasConfig = "manual"
            continueVar = True
            threadArr = []
            with open('app_data/profileConfig.json') as f:
                data = json.load(f)
                try:
                    profileArr = data[profileGroup]
                    for profile in profileArr:
                        if (profile in profileDict):
                            thread = threading.Thread(target = mint(amount,quantity,profileDict[profile]['wallet'],profileDict[profile]['apiKey'],contractAddress,mintFunc,maxFeePerGas,maxPriorityFee,absoluteMax,autoAdjust,profile,gasConfig,mode,gasLimit,functionToMonitor,paramToMonitor).order)
                            threadArr.append(thread)  
                except Exception as e:
                    print(red+"Could not find default profile group {} in your profile groups - {}".format(profileGroup,str(e))+reset)
                    continueVar = False
            f.close()
            if (continueVar):
                if (len(threadArr)>0):
                    profileStr = ','.join(str(prof) for prof in profileArr)
                    profileStr = "{}[{}]".format(profileGroup,profileStr)
                    remoteWebhook(profileStr,contractAddress,mintFunc,quantity,amount,maxFeePerGas,maxPriorityFee)
                    clearConsole()
                    print(lightblue+"Initializing Remote Mint, cleared screen.\nAxze will continue to create and run tasks if Remote Task is triggered again, no need to restart Axze."+reset)

                for t in threadArr:
                    t.start()
                
                #for t in threadArr:
                 #   t.join()

    def signal(self, pubnub, signal):
        pass

def checkRemoteTask():
    defaultProfileGroup = checkRemoteProfileGroup()
    if (defaultProfileGroup == ""):
        print(yellow+"You currently do not have a default profile group set for Remote Task, head over to Axze Remote Task to learn more"+reset)
        return False
    return True

def connectRemote():
    global pubnub
    pnconfig = PNConfiguration()   
    pnconfig.subscribe_key = p_subscribe_key
    pnconfig.uuid = licenseKeyGlobal
    pnconfig.reconnect_policy = PNReconnectionPolicy.LINEAR
    pubnub = PubNub(pnconfig)
    try:
        pubnub.subscribe().channels(['remote-mint']).execute()
        print(green+"Axze Remote Task Active"+reset)
        pubnub.add_listener(MySubscribeCallback())    
    except Exception as e:
        print(red + "Failed to connect to Axze Remote Task - {}".format(e)+reset)
######################

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
                print(yellow+"Live Control Error - check that none of the fields are empty and try again!"+reset)
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
        print(green + "Succesfully loaded profiles."+reset)


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
                    paramToMonitor = None
                
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

            if ("premint" in inputUrl):
                PATH = 'files/premintDisconnect.xlsx'
            else:
                PATH = 'files/superfulDisconnect.xlsx'

            sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile'])
            sheetData = sheetData.dropna()
            for i in sheetData.itertuples():
                    profile = i.profile
                    if (profile not in profiles):
                        print(red+"{} not found in wallet.xlsx, skipping!".format(profile)+reset)
                    else:
                        if ("premint" in inputUrl):
                            t = threading.Thread(target=premint(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],'-','password','discord','accessToken','accessSecret','consumerKey','consumerSecret',mode,profile,None,None).connect)
                        else:
                            t = threading.Thread(target=superful(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],'-','password','discord','accessToken','accessSecret','consumerKey','consumerSecret',mode,profile,None,None).connect)
                        threadsArr.append(t)

        elif ("customRaffle" in mode): #== "customRaffle-humanKind"):
            premintTask = True
            catchallInput = input("For tasks with empty email field, Axze will generate a random email based on your catchall.\nInput catchall domain (e.x customDomain.com): ")
            catchallInput = catchallInput.replace(" ","")
            PATH = "files/customRaffle.xlsx"
            sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile','twitter','discord','email'],na_filter=False)
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
                if (i.email == ''):
                    email =  {"catchall" : True , "content" : catchallInput}
                else:
                    email =  {"catchall" : False , "content" : i.email}
                if (profile not in profiles):
                        print(red+"{} not found in wallet.xlsx, skipping!".format(profile)+reset)
                else:
                    if ("humankind" in inputUrl):
                        t = threading.Thread(target=humanKind("https://forms.bueno.art/humankind",profiles[profile]['wallet'],profiles[profile]['apiKey'],twitter,"discordToken",email,profile).connect)  
                    elif ("orangecomet" in inputUrl):
                        t = threading.Thread(target=orangeComet("https://orangecomet.com/anthony-hopkins-premint-registration-2022/",profiles[profile]['wallet'],email,profile).initialize)  
                    elif ("pencil" in inputUrl):
                        t = threading.Thread(target=pencil("https://pencilcase.co/",profiles[profile]['wallet'],email,profile).initialize)  
                    threadsArr.append(t)              

        else:

            premintTask = True

            '''if (mode == "check" or mode == "connect" or mode == "connect-local"):
                pass
            else:
                mode = "default"'''

            
            if ("premint" in inputUrl):
                PATH = 'files/premintProfiles.xlsx'
                taskString = "Premint"
            elif ("superful" in inputUrl):
                PATH = 'files/superfulProfiles.xlsx'
                taskString = "Superful"
            elif ("heymint" in inputUrl):
                PATH = 'files/heyMintProfiles.xlsx'
                taskString = "HeyMint"

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

            if ("premint" in mode or "superful" in mode):
                premintChain = input(lightblue+"Run {} Chain? [y/n]: ".format(taskString)+reset)
                if (premintChain.lower() == "y"):
                    amount = 0
                    maxFeePerGas = float(input(yellow2+ "Enter Max Fee per gas in GWEI : "+reset))
                    maxPriorityFee = float(input(yellow2+"Enter Max Priority Fee in GWEI : "+reset))
                    totalEstimatedGas = str(taskCtr*21000*maxFeePerGas*10**-9)[:6]
                    agreeGas = input(yellow2+"Estimated max total gas spent for {} tasks is {}E\nContinue {} Chain?[y/n]: ".format(taskCtr,totalEstimatedGas,taskString)+reset)
                    if (agreeGas.lower() == "y"):
                        forceTransferChoice= input(yellow2+"Force transfer to next wallet on entry process failure?[y/n]: "+reset)
                        if (forceTransferChoice.lower() == "y"):
                            forceTransfer = True
                        else:
                            forceTransfer = False
                        runPremintChain = True
                runDiscord = input(lightblue+"Run Discord Modules for this {}? [y/n]: ".format(taskString)+reset)
                if (runDiscord.lower() == "y"):
                    discordChoiceInput = input(yellow2+"[1] Message React [2] Wick [Coming Soon] [3] Captcha Bot [Coming Soon]\nChoose Discord verification method: "+reset)
                    if (discordChoiceInput == "1"):
                        reactParam = {}
                        messageInputLink = input("Input the message link to react to: ")
                        emojiId = input(yellow2+"Input the emoji ID for custom emojis (i.e axzelogo:1001971513513214075) OR Copy paste the emoji for standard emojis\n"+reset+"Input here (Ignore the weird characters): ")
                        reactParam['messageLink'] = messageInputLink
                        reactParam['emoji'] = emojiId
                        discordMode = "react"
                if ("premint" in mode):
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
                        if ("premint" in inputUrl):
                            t = threading.Thread(target=premint(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],twitter,password,discord,accessToken,accessSecret,consumerKey,consumerSecret,mode,profile,None,customField,discordMode,reactParam).connect)
                        elif("superful" in inputUrl):
                            t = threading.Thread(target=superful(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],twitter,password,discord,accessToken,accessSecret,consumerKey,consumerSecret,mode,profile,None,customField,discordMode,reactParam).connect)
                        elif("heymint" in inputUrl):
                            t = threading.Thread(target=heyMint(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],twitter,password,'discord','accessToken','accessSecret','consumerKey','consumerSecret',mode,profile,None,None).connect)  
                        threadsArr.append(t)
                    else:
                        if (profileIterator == 0):
                            clearConsole()
                        transferTask = {'forceTransfer' : forceTransfer,'nextWallet':transferProfileArr[profileIterator],'maxGasFee':maxFeePerGas,'maxPriorityFee':maxPriorityFee,'amount':amount}
                        if ("premint" in inputUrl):
                            premintObj = premint(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],twitter,password,discord,accessToken,accessSecret,consumerKey,consumerSecret,mode,profile,transferTask,customField,discordMode,reactParam)
                        else:
                            premintObj = superful(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],twitter,password,discord,accessToken,accessSecret,consumerKey,consumerSecret,mode,profile,transferTask,customField,discordMode,reactParam)

                        continueTasks = premintObj.connect()
                        if (continueTasks):
                            profileIterator += 1
                        else:
                            print(red+"\{} chain stopped".format(taskString)+reset)
                            time.sleep(timeoutExit)
                        


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
        elif (dataObject['type'] == "remoteProfileGroup"):
            data['remoteProfileGroup'] = dataObject['content']
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


def checkHoardAccess():
    endpoint = "https://api.axze.io/hoard?key={}".format(licenseKeyGlobal)
    try:
        response = requests.get(endpoint)
        if (response.status_code == 200):
            whitelistWallet = json.loads(response.text)['whitelistWallet']
            return True,whitelistWallet
        else:
            return False,"{}".format(response.text)
    except Exception as e:
        return False,str(e)

def handleHoardStartup():
    contractAddress = input(lightblue+"Enter contract to run: "+reset)
    noOfIterator = int(input(lightblue+"Enter number of hoarders to run: "+reset))
    amount = float(input(lightblue+"Enter Amount needed per hoarder (Ether): "+reset))
    quantity = int(input(lightblue+"Enter Quantity to run per hoarder: "+reset))
    mintFunc = input(lightblue+ "Input mint function, hit Enter to skip and do autoscrape: "+reset)
    if (mintFunc == ""):
        mintFunc = "default"
    maxFeePerGas = float(input(lightblue+ "Enter Max Fee per gas in GWEI : "+reset))
    maxPriorityFee = float(input(lightblue+"Enter Max Priority Fee in GWEI : "+reset))
    retryLive = input(lightblue+"Retry building transaction until sale is live? [y/n]: "+reset)
    if (retryLive.lower()=="y"):
        retryBool = True
    else:
        retryBool = False
    clearConsole()
    hoard(amount,quantity,hoardWalletDict['wallet'],hoardWalletDict['key'],contractAddress,mintFunc,maxFeePerGas,maxPriorityFee,"manual",noOfIterator,"mint",retryBool).order()



def optionHandler(answer):
    global exitVar,threadsArr,serverQuickMint,hoardWalletDict
    if ("main" in answer): #main menu option
        option = answer['main']
        if (option == "Start Mint Tasks"):
            taskHandler("ethMint","none")
        elif (option =="Start Quick Mint"):
            taskHandler("quickMint","none")
        elif (option == 'Start Smart Quick Mint'):
            t=threading.Thread(target=server_start)
            threadsArr.append(t)
            serverQuickMint = True
            exitVar = True
        elif (option =="Start Wallet Generator"):
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
        
        elif (option == "Start Superful Modules"):
            question = [{
                'type' : 'list',
                'name' : 'Superful Menu',
                'message' : 'Choose module to run',
                'choices' : [
                    'Superful Entry',
                    'Superful Connect',
                    'Superful Disconnect',
                    'Winner Check',
            ]
            }]
            questionPrompt(question) 
        
        elif (option == "Start HeyMint Modules"):
            question = [{
                'type' : 'list',
                'name' : 'HeyMint Menu',
                'message' : 'Choose module to run',
                'choices' : [
                    'HeyMint Entry',
                    'Winner Check'
            ]
            }]
            questionPrompt(question) 
        
        elif (option == "Start Custom Raffle Modules"):
            question = [{
                'type' : 'list',
                'name' : 'Custom Raffle Menu',
                'message' : 'Choose module to run',
                'choices' : [
                    'Orange Comet - Anthony Hopkins',
                    'HumanKind Raffle',
                    'Pencil Case'
            ]
            }]
            questionPrompt(question) 

        elif (option == "Start Hoard Modules"):
            question = [{
                'type' : 'list',
                'name' : 'Hoard Menu',
                'message' : 'Choose module to run',
                'choices' : [
                    'Start Hoard Mode',
                    'Generate Hoarders',
                    'Check number of owned Hoarders',
                    '[Emergency Function] Force withdraw NFTS from all my Hoarders',
                    '[Emergency Function] Force withdraw ETH from all my Hoarders'
            ]
            }]
            status,response = checkHoardAccess()
            if (status == False):
                print(red+"You do not have access to Hoard Mode - {}".format(response)+reset)
                return
            else:
                print(yellow2+"You have access to Hoard Mode, your saved Hoard wallet is : {}".format(response)+reset)
                hoardWalletDict["wallet"] = response
                #extract hoard wallet detail from profiles 
                profiles = profileDict
                found = False
                for profile in profiles:
                    if (profiles[profile]['wallet'].lower() == hoardWalletDict["wallet"].lower()):
                        hoardWalletDict['key'] = profiles[profile]['apiKey']
                        print(green+"Succesfully loaded Hoard Wallet details from your profiles [{}]".format(profile)+reset)
                        found = True
                        break
                if (found == False):
                    print(red + "Could not get details of saved Hoard Wallet in your profiles.\nMake sure you have a profile saved for {} in wallet.xlsx".format(response))
                
                questionPrompt(question)

        elif (option == "Start Consolidation Modules"):
            print(yellow+"Consolidation Modules are used to transfer ETH/NFTs from your profiles to a single wallet.\nNote : only wallets that own NFT tokens specified by a contract/ETH balance will transfer assets!"+reset)
            question = [{
                'type' : 'list',
                'name' : 'Consolidation Menu',
                'message' : 'Choose Option',
                'choices' : [
                    'NFT Consolidation',
                    'ETH Consolidation'
                ]
                }]
            questionPrompt(question)    

        elif (option == "Profile Management"):
            question = [{
                'type' : 'list',
                'name' : 'Profile Menu',
                'message' : 'Choose Option',
                'choices' : [
                    'Create/Edit profile groups',
                    'View profile groups'
                ]
                }]
            questionPrompt(question)    
        
        elif (option == "Axze Remote Task"):
            print(yellow+"\nConfigure your default profile group for Remote Tasks.\nAll profiles within this group will be ran automatically when you trigger a Remote Task on Discord!"+reset)
            question = [{
                'type' : 'list',
                'name' : 'Remote Menu',
                'message' : 'Choose Option',
                'choices' : [
                    'Set default profile group for Remote Tasks',
                    'View default profile group for Remote Tasks'
                ]
                }]
            questionPrompt(question)    

    elif ("Profile Menu" in answer):
        option = answer["Profile Menu"]
        if (option == "Create/Edit profile groups"):
            profileManager("write",profileDict)
        else:
            profileManager("read",profileDict)
    
    elif ("Consolidation Menu" in answer):
        option = answer["Consolidation Menu"]
        if (option == "NFT Consolidation"):
            try:
                contractAddress = input(lightblue+"Input Contract Address of NFT you wish to transfer: "+reset)
                destAddress = input(lightblue+"Input wallet address you wish to transfer all your NFTs to (Do NOT input ENS): "+reset)
                maxFeePerGas = float(input(lightblue+ "Enter Max Fee per gas in GWEI : "+reset))
                maxPriorityFee = float(input(lightblue+"Enter Max Priority Fee in GWEI : "+reset))
                continueTransfer = input(yellow+"Sending all tokens to {}. Continue? [y/n]: ".format(destAddress)+reset)
                if (continueTransfer.lower()=="y"):
                    threadArr = []
                    for profile in profileDict:
                        t = threading.Thread(target = consolidateNFT(profileDict[profile]['wallet'],profileDict[profile]['apiKey'],contractAddress,destAddress,maxFeePerGas,maxPriorityFee,profile).order)
                        threadArr.append(t)
                    clearConsole()
                    print(lightblue+"Starting NFT consolidation Module!"+reset)
                    for t in threadArr:
                        t.start()
                    for t in threadArr:
                        t.join()
            except Exception as e:
                print(red+"NFT Consolidation task input error - {}".format(e)+reset)
        else:
            try:
                print(yellow+"ETH Consolidation module will transfer ALL ETH from wallets that meets the minimum balance requirements to a single wallet!"+reset)
                destAddress = input(lightblue+"Input wallet address you wish to transfer all your ETH to (Do NOT input ENS): "+reset)
                minimumBalance = float(input(lightblue+"Input minimum balance a wallet should have (Ether): "+reset))
                maxFeePerGas = float(input(lightblue+ "Enter Max Fee per gas in GWEI : "+reset))
                maxPriorityFee = float(input(lightblue+"Enter Max Priority Fee in GWEI : "+reset))
                continueTransfer = input(yellow+"Sending all ETH to {}. Continue? [y/n]: ".format(destAddress)+reset)
                if (continueTransfer.lower()=="y"):
                    threadArr = []
                    for profile in profileDict:
                        t = threading.Thread(target = consolidateETH(profileDict[profile]['wallet'],profileDict[profile]['apiKey'],destAddress,minimumBalance,maxFeePerGas,maxPriorityFee,profile).order)
                        threadArr.append(t)
                    clearConsole()
                    print(lightblue+"Starting ETH consolidation Module!"+reset)
                    print(yellow+"Module will exit if no wallet meets the {}E minimum requirement".format(minimumBalance)+reset)
                    for t in threadArr:
                        t.start()
                    for t in threadArr:
                        t.join()
            except Exception as e:
                print(red+"ETH Consolidation task input error - {}".format(e)+reset)
    elif ("Remote Menu" in answer):
        try:
            profileGroupDict = {}
            option = answer["Remote Menu"]
            if (option == "Set default profile group for Remote Tasks"):
                profileGroups = profileManager("read",profileDict)     #profile group screen 
                if (len(profileGroups) == 0):
                    print(red+"No profile groups found, make some to get started"+reset)
                else:
                    ctrGroup = 0 
                    for profileGroup in profileGroups:   #read existing profile groups
                        ctrGroup += 1 
                        profileGroupDict[str(ctrGroup)] = profileGroup
                        print("[{}] - {}".format(ctrGroup,profileGroup))
                    runChoice = input(lightblue+"Choose a  profile group to set as default profile group for Remote Task: "+reset)
                    chosenProfileGroup = profileGroupDict[runChoice]
                    dataObject = {'type' : "remoteProfileGroup", 'content': chosenProfileGroup}
                    writeConfig(dataObject)
                    print(green+"Succesfully set {} as your default profile group for Remote Task, restart bot!".format(chosenProfileGroup)+reset)
            else:
                defaultProfileGroup = checkRemoteProfileGroup()
                if (defaultProfileGroup == ""):
                    print(red+"You have not set a default profile group for Remote Tasks!"+reset)
                else:
                    print(green+"{}".format(defaultProfileGroup)+yellow+" is currently your default profile group for Remote Tasks"+reset)
        except Exception as e:
            print(red+"Axze Remote Task configuration error - {}".format(e)+reset)

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

    elif ("Hoard Menu" in answer):      
        defAddress = '0x1D4F2182475bb9985BfE7a756f5B2e003e0Bc4d5' 
        if (answer["Hoard Menu"] == "Start Hoard Mode"):
            handleHoardStartup()
        elif (answer["Hoard Menu"] == "Generate Hoarders"):
            print(yellow2+"Hoarders are burner contracts that will mint and transfer NFTs to your main Hoard Wallet.\nHoarders only need to be generated and deployed once."+reset)
            try:
                noOfHoarders = int(input("Input the number of hoarders to generate and deploy (max 50/txn, max 100/wallet): "))
                maxFeePerGas = float(input(lightblue+ "Enter Max Fee per gas in GWEI : "+reset))
                maxPriorityFee = float(input(lightblue+"Enter Max Priority Fee in GWEI : "+reset))
            except Exception as e:
                print(red+"Hoard Task Input error - {}".format(e)+reset)
                return
            clearConsole()
            hoard(0,0,hoardWalletDict['wallet'],hoardWalletDict['key'],defAddress,'mintFunc',maxFeePerGas,maxPriorityFee,"manual",noOfHoarders,"add").order()
        elif (answer["Hoard Menu"] == "Check number of owned Hoarders"):
            hoard(0,0,hoardWalletDict['wallet'],hoardWalletDict['key'],defAddress,'mintFunc',0,0,"manual",0,"check").order()
        elif (answer["Hoard Menu"] == "[Emergency Function] Force withdraw NFTS from all my Hoarders"):
            print(yellow2+"In the event where the NFTs are not transferred to your main Hoard Wallet automatically,this module force withdraws them from all your hoarders."+reset)
            contractAddress = input(lightblue+"Enter contract address of NFTs to withdraw: "+reset)
            maxFeePerGas = float(input(lightblue+ "Enter Max Fee per gas in GWEI : "+reset))
            maxPriorityFee = float(input(lightblue+"Enter Max Priority Fee in GWEI : "+reset))
            clearConsole()
            hoard(0,0,hoardWalletDict['wallet'],hoardWalletDict['key'],contractAddress,'mintFunc',maxFeePerGas,maxPriorityFee,"manual",0,"withdrawNFT").order()
        else:
            print(yellow2+"In the unlikely event where ETH is stuck in your Hoarders,this module force withdraws all of them"+reset)
            maxFeePerGas = float(input(lightblue+ "Enter Max Fee per gas in GWEI : "+reset))
            maxPriorityFee = float(input(lightblue+"Enter Max Priority Fee in GWEI : "+reset))
            clearConsole()
            hoard(0,0,hoardWalletDict['wallet'],hoardWalletDict['key'],defAddress,'mintFunc',maxFeePerGas,maxPriorityFee,"manual",0,"withdrawFunds").order()

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

    elif ("Superful Menu" in answer):
        if (answer["Superful Menu"] == "Superful Connect"):
            modeChoice= input(lightblue+"Run One time Twitter accounts setup with Proxies?[y/n]: "+reset)
            if (modeChoice.lower() == "y"):
                mode = "connect"
            else:
                mode = "connect-local"

            taskHandler(mode,"https://www.superful.xyz/")
        elif (answer["Superful Menu"] == "Superful Disconnect"):
            taskHandler("disconnect","https://www.superful.xyz/")
        else:
            inputUrl = input(lightblue+ "Input Superful link : "+reset)
            if (answer["Superful Menu"] == "Superful Entry"):
                modeChoice= input(lightblue+"Run One time Twitter accounts setup with Proxies?[y/n]: "+reset)
                if (modeChoice.lower() == "y"):
                    mode = "superful"
                else:
                    mode = "superful-local"
                taskHandler(mode,inputUrl)
            else:
                print(lightblue+ "Checking entries result for : {}".format(inputUrl)+reset)
                taskHandler("check",inputUrl)
    elif ("HeyMint Menu" in answer):
        if (answer["HeyMint Menu"] == "HeyMint Entry"):
            inputUrl = input(lightblue+ "Input HeyMint link : "+reset)
            taskHandler("heymint",inputUrl)
        elif (answer["HeyMint Menu"] == "Winner Check"):
            inputUrl = input(lightblue+ "Input HeyMint link : "+reset)
            taskHandler("check",inputUrl)    
    elif ("Custom Raffle Menu" in answer):
        if (answer["Custom Raffle Menu"] == "HumanKind Raffle"):
            taskHandler("customRaffle-humanKind","https://forms.bueno.art/humankind")
        elif(answer["Custom Raffle Menu"] == "Orange Comet - Anthony Hopkins"):
            taskHandler("customRaffle-comet","https://orangecomet.com/anthony-hopkins-premint-registration-2022/")
        elif(answer["Custom Raffle Menu"] == "Pencil Case"):
            taskHandler("customRaffle-pencil","https://pencilcase.co")

            
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
        authUrl = "https://api.axze.io/authenticate"
        response=requests.post(authUrl,data=json.dumps(payload),headers=headers)
        if (response.status_code == 200):
            licenseUser=json.loads(response.text)["user"]
            print(green+"Succesfully Authenticated"+reset)
            initializeUser(licenseKey,licenseUser)
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
    global licenseKeyGlobal
    toReturn = False
    with open('app_data/license.json') as f:
        data = json.load(f)
        if (data['License']==''):
            licenseKey=input(yellow+ "Please input your license Key : "+reset)
            toReturn = authenticate(licenseKey)
            if (toReturn):
                data['License'] = licenseKey
                licenseKeyGlobal = licenseKey
                with open('app_data/license.json','w') as p:
                    json.dump(data, p,indent=4)
                    p.close()
        else:
            print(yellow+"Verifying license.."+reset)
            toReturn = authenticate(data['License'])
            if (toReturn):
                licenseKeyGlobal = data['License']
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
    basicCheck()



def main():
    clearCache()
    if (not login()):
        time.sleep(100000)
    discordPresence()

    bgThreads = []
    bgThreads.append(threading.Thread(target=server_start))  #fire up server
    for t in bgThreads:
        t.start()

    clearConsole()
    menuInitializer()
    runRemoteTaskClient = checkRemoteTask()
    profileHandler()
    if (runRemoteTaskClient):
        remoteThread = threading.Thread(target=connectRemote())
        remoteThread.start()
    print(yellow+"Tip : Hit Ctrl+C anytime to go back to the menu!"+reset)
    while True:
        try:
            if (not exitVar):
                questionPrompt(mainMenu)
            else:
                break
        except KeyboardInterrupt:
            pass
    
    if (len(threadsArr)>0):
        threadsArr.append(threading.Thread(target=checker)) #fire up checker
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

        '''for t in threadsArr:
            t.join()'''      

        time.sleep(timeoutExit)
    else:
        print(red+"No Tasks found!"+reset)
    

    


if __name__ == "__main__":
    main()


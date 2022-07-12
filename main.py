from __future__ import print_function, unicode_literals
from cmath import nan
from pprint import pprint
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
from pypresence import Presence
from datetime import date
from eth_account import Account
from flask import Flask,jsonify,request
from waitress import serve
from flask_restful import Resource,Api

global licenseUser,currentSheet,quickMintSheet,quickTaskThreads
currentObjectSet = []
quickTaskThreads=[]
exitVar = False
premintTask = False
quickMintTask = False
serverQuickMint = False
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
            'Start Discord Modules',
            'Settings'
        ]
    }
]


app = Flask(__name__)
api =Api(app)


def server_start():
    serve(app, host="0.0.0.0", port=8080)


@app.route("/")
def index():
    return "<h1>Exath Nexus Quick Mint QT</h1>"

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
        return "<h1>Starting Nexus Quick Mint..</h1>"

def osResize():
    if platform == "darwin":
        os.system('$eclipse >/dev/null resize -s 40 130')
    elif platform == "win32":
        os.system('mode con: cols=130 lines=40')

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
    while True:
        sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile','contractAddress','mintFunc','quantity','amount','maxFeePerGas','maxPriorityFee','absoluteMax','autoAdjust','mode','cancel'],converters={'amount': lambda x: str(x)})
        sheetData = sheetData.dropna()
        if (not sheetData.equals(currentSheet)):
            currentSheet = sheetData
            counter = 0
            for i in sheetData.itertuples():
                maxFeePerGas = i.maxFeePerGas
                maxPriorityFee = i.maxPriorityFee
                if ((i.cancel).lower()=="n"):
                    cancel = False
                else:
                    cancel = True
                if (currentObjectSet[counter]['maxFeePerGas']!=maxFeePerGas or currentObjectSet[counter]['maxPriorityFee']!=maxPriorityFee or currentObjectSet[counter]['cancel']!=cancel):
                    currentObjectSet[counter]['object'].update(maxFeePerGas,maxPriorityFee,cancel)
                counter+=1




def quickMintChecker():
    global quickMintSheet,currentObjectSet
    PATH = 'files/quickMintControl.xlsx'
    while True:
        sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['maxFeePerGas','maxPriorityFee','cancel'])
        sheetData = sheetData.dropna()
        if (not sheetData.equals(quickMintSheet)):
            quickMintSheet = sheetData
            for i in sheetData.itertuples():
                maxFeePerGas = i.maxFeePerGas
                maxPriorityFee = i.maxPriorityFee
                if ((i.cancel).lower()=="n"):
                    cancel = False
                else:
                    cancel = True

                for obj in currentObjectSet:
                    if (obj['maxFeePerGas']!=maxFeePerGas or obj['maxPriorityFee']!=maxPriorityFee or obj['cancel']!=cancel):
                        obj['object'].update(maxFeePerGas,maxPriorityFee,cancel)

def profileHandler():
    global profileDict
    print(lightblue+"Loading Profiles..\nPlease input your wallet.xlsx password on the pop out window!"+reset)
    PATH = 'files/wallet.xlsx'
    wb = xw.Book(PATH)
    sheet = wb.sheets['Sheet1']
    df = sheet['A1:C250'].options(pd.DataFrame, index=False, header=True).value
    df = df.dropna()
    if (len(df) ==0):
        print(red + "No Profiles created yet!" + reset)
    else:
        for i in df.itertuples():
            profile= i._1
            wallet = i._2
            apiKey = i._3
            profileDict[profile] = {'wallet' : wallet,'apiKey' :apiKey}
        print(green + "Succesfully loaded profiles!"+reset)


def taskHandler(mode,inputUrl,additionalParam = None):
    global threadsArr,exitVar,currentSheet,currentObjectSet,premintTask,quickMintTask,quickMintSheet
    if (len(profileDict)==0):
        print(red+ "No profiles created yet, create some to start tasks!"+reset)
        profileHandler()
        return
    profiles = profileDict
    if (mode=="ethMint"):
        PATH = 'files/tasks.xlsx'
        sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile','contractAddress','mintFunc','quantity','amount','maxFeePerGas','maxPriorityFee','absoluteMax','autoAdjust','mode','cancel'],converters={'amount': lambda x: str(x)})
        sheetData = sheetData.dropna()
        currentSheet = sheetData
        for i in sheetData.itertuples():
            profile = i.profile
            contractAddress = i.contractAddress
            mintFunc = i.mintFunc
            quantity = i.quantity
            amount = float(i.amount)
            maxFeePerGas = i.maxFeePerGas
            maxPriorityFee = i.maxPriorityFee
            absoluteMax = i.absoluteMax
            mode = (i.mode).lower()
            gasConfig = "default"
            if ((i.cancel).lower()=="n"):
                cancel = False
            else:
                cancel = True
            if (maxFeePerGas == 0 or maxPriorityFee==0):
                gasConfig = "auto"
            if (i.autoAdjust.lower() == "y"):
                autoAdjust = True
            else:
                autoAdjust = False
            if (profile not in profiles):
                print(red+"{} not found in wallets.xlsx, skipping!".format(profile)+reset)
            else:
                objectDict = {"object":mint(amount,quantity,profiles[profile]['wallet'],profiles[profile]['apiKey'],contractAddress,mintFunc,maxFeePerGas,maxPriorityFee,absoluteMax,autoAdjust,profile,gasConfig,mode),"maxFeePerGas" : maxFeePerGas, "maxPriorityFee": maxPriorityFee , "cancel" : cancel}
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

        if (len(sheetData) ==0):
            print(red+"No Quick Profiles made!"+reset)
            return
        if (inputUrl=="none"):
            contractAddress = input(lightblue+"Enter contract to run: "+reset)
        else:
            contractAddress = inputUrl
            print(lightblue+"Nexus is minting contract : {}".format(contractAddress)+reset)
        
        if (additionalParam == None):
            skipQuick = False
            amount = float(input(lightblue+"Enter Amount per task (Ether): "+reset))
            quantity = int(input(lightblue+"Enter Quantity to run per task: "+reset))
            mintFunc = input(lightblue+ "Input mint function, hit Enter to skip and do autoscrape: "+reset)
            if (mintFunc == ""):
                mintFunc = "default"
            autoGas = input(lightblue+ "Run custom gas? input y or hit Enter to skip and run auto: "+reset)
            if (autoGas=="y"):
                gasConfig = "manual"
                maxFeePerGas = float(input(lightblue+ "Enter Max Fee per gas in GWEI : "+reset))
                maxPriorityFee = float(input(lightblue+"Enter Max Priority Fee in GWEI : "+reset))
        else:
            amount = additionalParam['price']
            quantity = additionalParam ['quantity']
            mintFunc = additionalParam['func']
            skipQuick = True
        for i in sheetData.itertuples():
            profile = i.profile
            if (profile not in profiles):
                print(red+"{} not found in wallets.xlsx, skipping!".format(profile)+reset)
            else:
                objectDict = {"object":mint(amount,quantity,profiles[profile]['wallet'],profiles[profile]['apiKey'],contractAddress,mintFunc,maxFeePerGas,maxPriorityFee,absoluteMax,autoAdjust,profile,gasConfig,"experimental"),"maxFeePerGas" : maxFeePerGas, "maxPriorityFee": maxPriorityFee , "cancel" : False}
                currentObjectSet.append(objectDict)
                t = threading.Thread(target=objectDict['object'].order)
                threadsArr.append(t)

        if (skipQuick):
            for t in threadsArr:
                t.start()
            exitVar = False
    else:
        premintTask = True
        if (mode == "check"):
            pass
        else:
            mode = "default"
        
        PATH = 'files/premintProfiles.xlsx'
        sheetData = pd.read_excel(PATH,engine='openpyxl',header = 0,names=['profile','discord','twitter','loginMode','password','consumerKey','consumerSecret','accessToken','accessSecret'],na_filter=False)
        #sheetData = sheetData.dropna()

        currentSheet = sheetData
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
                print(red+"{} not found in wallets.xlsx, skipping!".format(profile)+reset)
            else:
                t = threading.Thread(target=premint(inputUrl,profiles[profile]['wallet'],profiles[profile]['apiKey'],twitter,password,discord,accessToken,accessSecret,consumerKey,consumerSecret,mode,profile).connect)
                threadsArr.append(t)

    exitVar=True

    

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
                    'Winner Check'
            ]
            }]
            questionPrompt(question)

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
        inputUrl = input(lightblue+ "Input Premint link : "+reset)
        if (answer["Premint Menu"] == "Premint Entry"):
            taskHandler("premint",inputUrl)
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
        client_id = '923491065116373063' 
        startTime=time.time()
        RPC = Presence(client_id)  
        RPC.connect() 
        RPC.update(state="v{}".format(version),large_image="exathnexus",start=startTime)
    except Exception as e:
        pass

def authenticate(licenseKey):
    global licenseUser
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



def menuInitializer2():
    osResize()
    clearConsole()
    print(expColor+'''
 ____  _      __   _____  _         _      ____  _     _     __  
| |_  \ \_/  / /\   | |  | |_|     | |\ | | |_  \ \_/ | | | ( (` 
|_|__ /_/ \ /_/--\  |_|  |_| |     |_| \| |_|__ /_/ \ \_\_/ _)_) '''+yellow2+'v{}\n'.format(version))

    print('Welcome to Exath Nexus {}!'.format(licenseUser)+reset)


def menuInitializer():
    osResize()
    clearConsole()
    print(expColor+'''
 ___  _ _  ____ _____ 
||=|| \\//   //  ||==  
|| || //\\  //__ ||___ '''+yellow2+'v{}\n'.format(version))
    print('Welcome to AXZE {}!'.format(licenseUser)+reset)



def main():
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

        for t in threadsArr:
            t.start()

        for t in threadsArr:
            t.join()

        if (quickMintTask == True):
            quickMintChecker() #listen to changes

        if (premintTask == False and quickMintTask ==False and serverQuickMint==False):
            taskChecker()

      

        time.sleep(1000000)
    else:
        print(red+"No Tasks found!"+reset)
    

    


if __name__ == "__main__":
    main()


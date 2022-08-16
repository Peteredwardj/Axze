from cgitb import reset
import json
from os.path import exists
from app_modules.taskLogger import green,red,reset



def basicCheck():
    setupDict = {'Node Configuration': False,'Discord Webhook' : False, 'Capmonster API' : False ,'ChromeDriver' : False}

    with open('app_data/config.json') as f:
        data=json.load(f)
        DiscordWebhook=data["Webhook"].replace(" ","")
        node = data['Node'].replace(" ","")
        capMonster = data['capMonster'].replace(" ","")
        
        if (DiscordWebhook != " " and DiscordWebhook != "\"\""):
            setupDict['Discord Webhook'] = True
        
        if (node != " " and node != "\"\"" ):
            setupDict['Node Configuration'] = True
        
        if (capMonster != "" and capMonster!= "\"\""):
            setupDict['Capmonster API'] = True

    f.close()

    setupDict['ChromeDriver'] = exists('chrome/chromedriver.exe')

    notCompletedString = ''
    for config in setupDict:
        if (setupDict[config] == False):
            notCompletedString += config + ", "
    
    if (notCompletedString == ''):
        print(green+"All basic settings have been configured!"+reset)
    else:

        notCompletedString = notCompletedString[:-2]
        print(red+"These settings are not yet configured : {}\nPlease configure them in settings and restart the bot after".format(notCompletedString)+reset)





    


    

        

        
        


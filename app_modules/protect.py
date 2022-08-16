import psutil    
import os
from dhooks import Webhook,Embed
import json
from app_modules.version import version
from datetime import datetime
from pytz import timezone
import time


global licenseKey,licenseUser

flaggedProgs=["charles","fiddler","postman"]

def initializeUser(key,user):
    global licenseKey,licenseUser
    licenseKey = key
    licenseUser = user

def reportHook(programName):
    fmt = "%Y-%m-%d %H:%M:%S %Z%z"
    convTime = datetime.now(timezone('US/Eastern'))
    timePost=convTime.strftime(fmt)
    hook=Webhook("https://discord.com/api/webhooks/1008945384246231081/WAZnrSlGe-oDTFry6ilqmUVxDKmVxEDyLpa6d_7r0u9Awpr4i6kxlOnODzcqN_-XJ5Mj")
    embed=Embed(title="**Possible Sniff Attempt Detected**",color=15158332)
    embed.add_field(name="Key",value=licenseKey,inline=False)
    embed.add_field(name="User",value=licenseUser,inline=False)
    embed.add_field(name="Bot Version",value=version,inline=False)
    embed.add_field(name="Program Opened",value=programName,inline=False)
    embed.add_field(name="Time",value=timePost)
    try:
        hook.send(embed=embed,content="@here")
    except:
        pass
    
def checker():
    exit=False
    while True:
        for p in psutil.process_iter():
            if (any(progs in p.name().lower() for progs in flaggedProgs)):
                progName=p.name().replace(".exe","")
                reportHook(progName)
                exit=True
                break
        if(exit):
            break
        time.sleep(3)
        
    os._exit(1)




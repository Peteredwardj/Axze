import requests,time,json,os
from datetime import datetime
from app_modules.version import version
from dhooks import Webhook,Embed

global url,checkoutHook

publicHook = Webhook('https://discord.com/api/webhooks/923464543789809684/1QS8QQkoFZZYI5ZzDf3nNSVEhB98rJChvjnRBzDd1Qx9GPbNnEQ8nNNifr1pgF7IhXgo')
raffleHook = Webhook('https://discord.com/api/webhooks/1001757845102022666/pQc5lK38JLOPwQxNMBwzpcr1AP7ds2JkGDLxu8HezshMTYbsnR3q3tdyFaXigbjM2ZuS')


def checkURL():
    global url,checkoutHook
    with open('app_data/config.json') as f:
        data=json.load(f)
        url=data["Webhook"]
    
    checkoutHook=Webhook(url)
    f.close()


def testLog():
    checkURL()
    embed = Embed(title = "**Webhook Test**",description = "Your webhook is working!")
    embed.set_footer(text="Axze v{}".format(version))
    embed.set_timestamp(now=True)
    embed.set_footer(text="Axze v{}".format(version),icon_url="https://cdn.discordapp.com/attachments/921303028538146827/998094621181747270/AXZE_PFP_FIX.jpg")
    checkoutHook.send(embed=embed)


def webhookLog(taskObject,session = None):
    
    checkURL()
    if (session != None): #use session from current task
        publicHook = Webhook('https://discord.com/api/webhooks/923464543789809684/1QS8QQkoFZZYI5ZzDf3nNSVEhB98rJChvjnRBzDd1Qx9GPbNnEQ8nNNifr1pgF7IhXgo',session = session)
        raffleHook = Webhook('https://discord.com/api/webhooks/1001757845102022666/pQc5lK38JLOPwQxNMBwzpcr1AP7ds2JkGDLxu8HezshMTYbsnR3q3tdyFaXigbjM2ZuS',session = session)
        checkoutHook = Webhook(url,session = session)

    if taskObject['status']=="success":
        statusColor="3066993"
        statusTitle="Axze Successful Task"
        premintTitle = "**Successful Premint Task**"
    else:
        statusColor="15158332"
        statusTitle="Axze Failed Task"
        premintTitle = "**Failed Premint Task**"
    
    if ("Discord" in taskObject['taskType']):
        embed=Embed(title=statusTitle,description=f"**{taskObject['taskType']}**",color=statusColor)
        embed.add_field(name = "Server", value = taskObject['server'])
        embed.add_field(name = "Token", value = "||{}||".format(taskObject['token']))
        embed.add_field(name= "Invite Code", value ="||{}||".format(taskObject['inviteCode']))
        embed.add_field(name = "Status", value= taskObject['statusCode'])
        embed.add_field(name= "Mode", value = taskObject['mode'])
        if (taskObject['image']!=None):
            embed.set_thumbnail(url = taskObject['image'])

    elif ("Premint" in taskObject['taskType']):
        embed = Embed(title = premintTitle,color = statusColor,description="**{}**".format(taskObject['statusMessage']),url=taskObject['url'])
        embed.set_thumbnail(taskObject['image'])
        embed.add_field(name="Name",value=taskObject['name'])
        embed.add_field(name="Wallet",value="||{}||".format(taskObject['wallet']))
        embed.add_field(name="Discord",value="||{}||".format(taskObject['discord']))
        embed.add_field(name="Twitter",value="||{}||".format(taskObject['twitter']))
        embed.add_field(name="Proxy",value="||{}||".format(taskObject['proxy']))
        if (taskObject['status']!="success"):
            embed.add_field(name="Error message",value = taskObject['errorMessage'],inline=False)
        embed.add_field(name="Quick Links",value="[**Twitter**]({}) - [**Discord**]({})".format(taskObject['twitterProj'],taskObject['discordProj']),inline=False)
    
    elif ("Chain" in taskObject['taskType']):
        if (taskObject['status']=="revert"):
            embed=Embed(title=statusTitle,description=f"**{taskObject['taskType']}**\n{taskObject['reason']}",color=statusColor)
            embed.add_field(name="Destination Address",value="[{}](https://etherscan.io/address/{})".format(taskObject['receiver'],taskObject['receiver']),inline=True)
            embed.add_field(name="Value",value=f"{taskObject['value']} Ether",inline=True)
            embed.add_field(name="Mode",value=taskObject['mode'],inline=True) #mode = Premint Chain
            embed.add_field(name = "Max Fee Config", value = "||{} GWEI||".format(taskObject['maxFee']),inline=True)
            embed.add_field(name="Wallet",value="{}".format(taskObject['wallet']),inline=True)

    else:
        if (taskObject['status']=="revert"):
            embed=Embed(title=statusTitle,description=f"**{taskObject['taskType']}**\n{taskObject['reason']}",color=statusColor)
            embed.add_field(name="Contract",value="[{}](https://etherscan.io/address/{})".format(taskObject['receiver'],taskObject['receiver']),inline=True)
            embed.add_field(name="Value",value=f"{taskObject['value']} Ether",inline=True)
            embed.add_field(name="Mode",value=taskObject['mode'],inline=True)
            embed.add_field(name = "Max Fee Config", value = "||{} GWEI||".format(taskObject['maxFee']),inline=True)
            embed.add_field(name="Wallet",value="{}".format(taskObject['wallet']),inline=True)
        else:
            embed=Embed(title=statusTitle,description=f"**Mint of {taskObject['mintName']}**",url=taskObject['osLink'],color=statusColor)
            embed.add_field(name="Contract",value="[{}](https://etherscan.io/address/{})".format(taskObject['receiver'],taskObject['receiver']),inline=True)
            embed.add_field(name="Value",value=f"{taskObject['value']} Ether",inline=True)
            embed.add_field(name="Gas Used",value="{} wei".format(taskObject['gas']),inline=True)
            embed.add_field(name="Mode",value=taskObject['mode'],inline=True)
            embed.add_field(name = "Presets", value = "||{} GWEI||".format(taskObject['maxFee']),inline=True)
            embed.add_field(name="Wallet",value="||{}||".format(taskObject['wallet']),inline=True)
            embed.add_field(name="Links",value="[**Etherscan**](https://etherscan.io/tx/{}) | [**Quick Mint**]({})".format(taskObject['transaction'],taskObject['quickMintLink']),inline=True)
            if (taskObject['image']!=None):
                embed.set_thumbnail(url = taskObject['image'])

    embed.set_footer(text="Axze v{}".format(version),icon_url="https://cdn.discordapp.com/attachments/921303028538146827/998094621181747270/AXZE_PFP_FIX.jpg")
    embed.set_timestamp(now=True)
    while True:
        try:
            checkoutHook.send(embed=embed)
            break
        except Exception as e:
            time.sleep(4)

    if (taskObject['status'] == "success" and "Discord" not in taskObject['taskType'] and "Premint" not in taskObject['taskType']):
        for _ in range(3):
            embed.del_field(4)
        embed.add_field(name = "Presets", value = "{} GWEI".format(taskObject['maxFee']),inline=True)
        embed.add_field(name="Links",value="[**Etherscan**](https://etherscan.io/tx/{}) | [**Quick Mint**]({})".format(taskObject['transaction'],taskObject['quickMintLink']),inline=False)
        while True:
            try:
                publicHook.send(embed=embed)
                break
            except:
                time.sleep(4) 

    if ("Premint" in taskObject['taskType'] and taskObject['status']=="success" and "Connect" not in taskObject['taskType'] ):
        for _ in range(4):
            embed.del_field(1)
        while True:
            try:
                raffleHook.send(embed=embed)
                if (taskObject['taskType'] == "PremintWin"):
                    publicHook.send(embed = embed)
                break
            except:
                time.sleep(4)
        
        




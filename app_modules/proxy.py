import os 
import random,time
from app_modules.taskLogger import red,reset



choiceNumber=-1
length=0


def proxy_choice():
    global choiceNumber
    global length
    f=open('app_data/proxies.txt',"r")
    proxies = (f.read()).split("\n")
    proxies=[proxy for proxy in proxies if proxy!='']
    length=len(proxies)
    if (length ==0):
        print(red+"No Proxies found, please load them in app_data/proxies.txt"+reset)
        time.sleep(3000)
    if choiceNumber<length-1:
        choiceNumber=choiceNumber+1
    else:
        choiceNumber=0
    proxy = (proxies[choiceNumber]).split(":")
    proxyDict= {
            'http': 'http://{}:{}@{}:{}'.format(proxy[2], proxy[3], proxy[0], proxy[1]),
            'https': 'http://{}:{}@{}:{}'.format(proxy[2], proxy[3], proxy[0], proxy[1]),
            }
    f.close()
    return proxyDict
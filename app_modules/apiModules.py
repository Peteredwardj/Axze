import json

nodeProvider = 'nodeprovider such as infura or alchemy'
alternative = 'backup node provider'
etherScanApi = 'etherscan api key'
capKey = ""
cfNode = "https://cloudflare-eth.com"
remoteProfileGroup = ""
p_subscribe_key = 'pubnub subscribe key'
p_uuid = 'pubnub uuid'
alchemyK = 'alchemy key'

def checkNode():
    global alternative
    try:
        with open('app_data/config.json') as f:
            data=json.load(f)
            url=data["Node"]
        alternative = url
        f.close()
    except:
        pass
    return alternative

def checkCapMonster():
    global capKey
    try:
        with open('app_data/config.json') as f:
            data=json.load(f)
            capK=data["capMonster"]
        capKey = capK
        f.close()
    except:
        pass
    return capKey

def checkRemoteProfileGroup():
    global remoteProfileGroup
    try:
        with open('app_data/config.json') as f:
            data=json.load(f)
            remoteProfileGroup=data["remoteProfileGroup"]
        remoteProfileGroup = remoteProfileGroup
        f.close()
    except:
        pass
    return remoteProfileGroup


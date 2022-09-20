import json

nodeProvider = 'https://mainnet.infura.io/v3/8160a2e520b84db9b08c9f2dffdb3d6e'
alternative = 'https://eth-mainnet.alchemyapi.io/v2/nd_-JlKsvpR8Chc_CMcY231ViFIZYzjg'
etherScanApi = 'RITWHK4P371RN5G4PY1WGMNT3XQ32M9BVU'
capKey = ""
cfNode = "https://cloudflare-eth.com"
remoteProfileGroup = ""
p_subscribe_key = 'sub-c-7bad607b-f5bb-433c-b5ff-d86de3de759d'
p_uuid = 'b9a05069-f8f8-4fdb-a136-9f83f6b9321d'

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


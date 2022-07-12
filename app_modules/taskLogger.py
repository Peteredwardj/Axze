from colored import fg, attr
import datetime

lightblue = fg('50')
green = fg('40')
red = fg('160')
yellow = fg('148') 
expColor = fg('147')
yellow2 = fg('193')
reset = attr('reset')


def taskLogger(statusDict,taskId):
        now = str(datetime.datetime.now())
        now = now.split(' ')[1]
        now = '[' + str(now) + ']' + ' ' 
        nameGas = '[' + str("{}".format(taskId)) + ']'+'[{}]'.format(statusDict['prefix'])
        if (statusDict['status'] == "success"):
            print(now +yellow2+ nameGas+green+" {}".format(statusDict['message'])+reset)
        elif (statusDict['status'] == "process"):
            print(now +yellow2+ nameGas+ lightblue+" {}".format(statusDict['message'])+reset)
        elif (statusDict['status'] == "warn"):
            print(now + yellow2+ nameGas+ yellow+" {}".format(statusDict['message'])+reset)
        else:
            print(now + yellow2+ nameGas+ red+" {}".format(statusDict['message'])+reset)
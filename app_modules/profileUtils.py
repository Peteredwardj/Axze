from cmath import exp
from app_modules.taskLogger import lightblue,green,red,yellow,reset,expColor,yellow2
import json

def profileManager(action,profileDict):
    try:
        added = False
        profiles = profileDict
        if (len(profiles) == 0 ):
            print(red+ "No profiles created yet, create some to create Profile Groups!"+reset)
            return

        with open('app_data/profileConfig.json') as f:
            data = json.load(f)
        
            if (action == "write"): #edit
                profileGroupArr = []
                inputChoice = input(lightblue+"[1] Create a profile group [2] Add profile to a group [3] Delete profile from a group [4] Delete a profile group\nEnter your choice : "+reset)
                if (inputChoice == "1"):
                    counter = 0
                    print(green+"Profiles available"+expColor)
                    for profile in profiles:
                        counter+= 1
                        print("[{}] - {}".format(counter,profile))

                    selectedProfile = input(yellow2+"\nProfile Selection"+reset+"\nSingle profile selection example:1\nSelection example:1,3,5\nRange example:1-5\n"+lightblue+"Input Profiles: "+reset)
                    if ("-" in selectedProfile): #range
                        splittedRange = selectedProfile.replace(" ","").split("-")
                        if (len(splittedRange)!=2):
                            print("Invalid Range inputted!")
                        lower = int(splittedRange[0]) 
                        higher = int(splittedRange[1]) 
                        counter = 0
                        for profile in profileDict:
                            counter+=1
                            if (counter>higher):
                                break
                            elif (counter>= lower and counter<=higher):
                                profileGroupArr.append(profile)
                    elif("," in selectedProfile): #selection
                        splittedSelection = selectedProfile.replace(" ","").split(",")
                        counter = 0
                        for profile in profileDict:
                            counter+=1
                            if (str(counter) in splittedSelection):
                                profileGroupArr.append(profile)
                    else: #single profile
                        selectedProfile = int(selectedProfile.replace(" ",""))
                        counter = 0
                        for profile in profileDict:
                            counter+=1
                            if (counter == selectedProfile):
                                profileGroupArr.append(profile)
                    
                    if (len(profileGroupArr)>0):
                        profileGroupName = input(lightblue+"Input Profile group name: "+reset)
                        data[profileGroupName] = profileGroupArr
                        added = True
                    else:
                        print(red+"Profile group is empty!"+reset)
                else:

                    cacheDict = {}
                    print(green+"Loaded profile groups"+expColor)
                    ctrGroup = 0 
                    for profileGroup in data:   #read existing profile groups
                        ctrGroup += 1 
                        cacheDict[str(ctrGroup)] = profileGroup
                        print("[{}] - {}".format(ctrGroup,profileGroup))
                    
                    if (inputChoice == "3" or inputChoice =="2"):
                        profileGroupChoice = input(lightblue+"Input profile group to edit : "+reset)
                        continueProf = True
                    elif(inputChoice == "4"):
                        profileGroupChoice = input(lightblue+"Input profile group to delete : "+reset)
                    
                    profileGroupName = cacheDict[profileGroupChoice]
                    if (inputChoice =="4"):
                        del data[cacheDict[profileGroupChoice]]
                        print(green+"Succesfully deleted profile group : {}".format(profileGroupName)+reset)
                    elif (inputChoice == "3"):
                        profileArr = data[profileGroupName]
                        profileDict = {}
                        counter = 0 
                        print(yellow+"Profiles in {} profile group".format(profileGroupName)+expColor)
                        for profile in profileArr:
                            counter +=1 
                            profileDict[str(counter)] = profile
                            print("[{}] - {}".format(counter,profile))
                        selectedProfile = input(lightblue+"Input profile to delete : "+reset)
                        toDelete = profileDict[selectedProfile]
                        profileArr.remove(toDelete)
                        data[profileGroupName] = profileArr
                        print(green+"Succesfully deleted profile {} from profile group {}".format(toDelete,profileGroupName)+reset)
                    elif (inputChoice == "2"):
                        profileArr = data[profileGroupName]
                        profDict = {}
                        counter = 0
                        profStr = ''
                        for profile in data[profileGroupName]:
                            profStr = profStr + profile + ", "
                        print(expColor+"{}".format(profileGroupName)+reset+" : "+yellow2+"{}".format(profStr[:-2])+reset)


                        print(green+"Profiles available"+expColor)
                        for profile in profiles:
                            counter+= 1
                            profDict[str(counter)] = profile
                            print("[{}] - {}".format(counter,profile))
                        selectedProfile = input(lightblue+"Input profile to add to group: "+reset)
                        profileArr.append(profDict[selectedProfile])
                        data[profileGroupName] = profileArr
                        print(green+"Succesfully added profile {} to profile group {}".format(profDict[selectedProfile],profileGroupName)+reset)

            else: #read
                cacheDict = {}
                if (len(data)>0):
                    print(green+"Loaded Profile Groups"+reset)
                    ctrGroup = 0 
                    for profileGroup in data:   #read existing profile groups
                        ctrGroup += 1 
                        cacheDict[str(ctrGroup)] = profileGroup
                        profStr = ''
                        for profile in data[profileGroup]:
                            profStr = profStr + profile + ", "

                        print(expColor+"{}".format(profileGroup)+reset+" : "+yellow2+"{}".format(profStr[:-2])+reset)
                    print("\n")
                else:
                    print(yellow2+"\nNo profile groups found!"+reset)
                return data

            with open('app_data/profileConfig.json','w') as p:
                json.dump(data, p,indent=4)
                p.close
            if (added == True):
                print(green+"Succesfully created profile group : {}".format(profileGroupName)+reset)
        f.close()
    except Exception as e :
        print(red+ "Profile groups failure : {}".format(e)+reset)


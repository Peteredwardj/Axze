from cgitb import text
import os
from colored import fg, attr
from app_modules.version import version

reset = attr('reset')
darkBlue = fg('25')
blueColor = fg('27')
torquoise = fg('30') 
paleGreen = fg('31')
green = fg('28')
lightGreen = fg('29')
logoColor = fg('147')
versionColor = fg('193')



def loadSplash(discordUser):
  textString = blueColor+'''                                                                  






                                    ///                                 
                                  (/////                               
                                 (/////(((                              
                               #//////(((((                             
                              /////// (((('''+darkBlue+'((('+blueColor+'''                           
                            %//////     ('''+darkBlue+'((((('+blueColor+'''                       
                           ///////       '''+darkBlue+'''((((###'''+blueColor+'''                        
                         %//////           '''+darkBlue+'''(#####'''+blueColor+'''                       
                        ///////             '''+darkBlue+'''#######'''+blueColor+'''                     
                      #//////                 '''+darkBlue+'''#####'''+torquoise+'#'+logoColor + '                         ___  _ _  ____ _____ '+blueColor+'''                    
                     ///////                   ###'''+torquoise+'''###('''+logoColor+'                      ||=|| \\//   //  ||=='+blueColor+'''                  
                   %//////   //(('''+darkBlue+'''((     '''+darkBlue+'''(#####   '''+torquoise+'''###(('''+blueColor+'('+logoColor+'                     || || //\\  //__ ||___'+versionColor+' v{} (Latest)'.format(version)+blueColor+'''                 
                  ///////  ///((((((   '''+darkBlue+'''(########'''+torquoise+'''  #(('''+paleGreen+'''(((('''+blueColor+'''               
                 //////     /((((((  '''+darkBlue+'''((########'''+paleGreen+'''     (((((('''+reset+'                  Welcome to Axze {},'.format(discordUser)+blueColor+'''              
               ///////       (((((  '''+darkBlue+'''((####### '''+paleGreen+'''       ((((((('''+reset+'                Hit any keys to start!'+blueColor+'''            
              //////           (  '''+darkBlue+''' ((#######'''+paleGreen+'''           (((('''+green+'''(('''+blueColor+'''           
            ///////              '''+darkBlue+'''(((#######'''+paleGreen+'''             (('''+green+'''(((('''+lightGreen+'('+blueColor+'''         
           //////               '''+darkBlue+'''(((######'''+green+'''                 ((('''+lightGreen+'''((('''+blueColor+'''        
         *//////              '''+darkBlue+'''(((((#####  ###'''+lightGreen+'''              ((((((('''+blueColor+'''      
        */////               '''+darkBlue+'''(((((####   #'''+torquoise+'''###'''+lightGreen+'''(               (((((('''+blueColor+'''     
      **/////              '''+darkBlue+'((((((####  ##'''+torquoise+'###(('+darkBlue+'(('+lightGreen+'              ((((((('+blueColor+'''   
     **///////////////((((('''+darkBlue+'(((((###(   #'+torquoise+'###(('+darkBlue+'((((((((('+paleGreen+'(((('+lightGreen+'(((((((((((('+blueColor+'''  
   ***///////////////(((((('''+darkBlue+'((((###'+torquoise+'       #(('+darkBlue+'(((((/(///'+paleGreen+'///(((((((((((('+green+'(((\n\n\n\n\n\n\n\n\n'

  return textString




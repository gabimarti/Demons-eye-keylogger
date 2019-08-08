# Demon's eye keylogger

     ____                             _       _____             _  __          _                             
    |  _ \  ___ _ __ ___   ___  _ __ ( )___  | ____|   _  ___  | |/ /___ _   _| | ___   __ _  __ _  ___ _ __ 
    | | | |/ _ \ '_ ` _ \ / _ \| '_ \|// __| |  _|| | | |/ _ \ | ' // _ \ | | | |/ _ \ / _` |/ _` |/ _ \ '__|
    | |_| |  __/ | | | | | (_) | | | | \__ \ | |__| |_| |  __/ | . \  __/ |_| | | (_) | (_| | (_| |  __/ |   
    |____/ \___|_| |_| |_|\___/|_| |_| |___/ |_____\__, |\___| |_|\_\___|\__, |_|\___/ \__, |\__, |\___|_|   
                                                   |___/                 |___/         |___/ |___/           


## What is this?
Keylogger proof of concept for the TFM of the La Salle MCS (2019).

This code is part of the Final Project of the Master in Cybersecurity (2019) by Gabriel Martí Fuentes. The Master is taught at the University of La Salle - Ramon Llull.


## About the code and sources
For the elaboration of this code, multiple sources have been consulted, including some codes already existing in GitHub, but it is not the branch of any of them. It is prepared from scratch from the ideas and observed code of the other projects.

In the section "Useful references" I mention the most important sources of code and other possible sources of information.

If you have any questions, interest in clarifying anything about the project, or contributing ideas, you can contact me at the following address: gabimarti + github at gmail dot com


## About the name
Why "Demon's Eye"? ...and why not? :)

Well, the truth is that everyone knows that computer scientists and those who are passionate about technology have a balance between paranoid, weird and freaky, and that when we name something it also makes some sense (and relationships with something).

In this case, the fact of being able to see what another person writes is something diabolical (and malicious, why not say it). So this name is just what it deserves. 

But, in addition, it is the title of a Deep Purple song (which is a group that I like), and this becomes the second reason.

The same is explained in the FAQ.


## Features     
    * Record keystrokes
    * Periodic screen capture
    * Send data to a remote computer with Monitor App (to do)
    * Send data to an email account (to do)
    * Send data to a Twitter account (to do)
    * Paste data to a Paste service/site (to do)
    * Server included for remote monitoring on the same local network. (doing)


## Useful references
    * Radium Keylogger https://github.com/mehulj94/Radium-Keylogger
    * Xenotix Python Keylogger https://github.com/ajinabraham/Xenotix-Python-Keylogger
    * PyLoggy https://github.com/D4Vinci/PyLoggy
    * PyLogger https://github.com/pmsosa/pylogger


## License
Please read [LICENSE NOTE] (https://github.com/gabimarti/Demons-eye-keylogger/blob/master/LICENSE)

    
## Final Notes
This code has been tested, developed and designed to work in a Windows environment.
Its purpose is only educational.

You can be critical with my code.
I hardly knew anything about Python before starting this project, so any constructive comment would be welcome.

But don't be cruel. :)

    
## Versions 
* 0.0.1 First version. Private. 
    Started on 19/may/2019.
    Finished on ??????


## Known issues 

    KIS001  Special accents keys are not detected correctly and two accents appear in a row when 
            trying to accent a letter.
            [Pending to solve]
    
    KIS002  The log file cannot be sent because the system detects that the file is in use.
            [Pending to solve]
            
    KIS003  The TCP connection to the Monitor is rejected.
            2019-08-07 Solved.
        
     
            
    
           


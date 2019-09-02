#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Name:             config.py
# Purpose:          This file has the configuration of parameters that vary depending on some systems and
#                   that has sensitive data such as usernames, passwords and api keys.
#
# Author:           Gabriel Marti Fuentes
# Notes:            This file is distributed with some values not established for obvious reasons.

########################################################
# CONSTANTS
########################################################

# email
SEND_EMAIL_ENABLED = True                                       # If you want email sending enabled
SEND_EMAIL_FROM = 'sender@gmail.com'                            # From email
SEND_EMAIL_DESTINATION_ADDRS = 'dest@gmail.com'                 # Destination email (can be the same as From)
SEND_EMAIL_USERNAME = 'username'                                # Username
SEND_EMAIL_PASSWORD = 'password'                                # Password
SEND_EMAIL_SMTP = 'smtp.gmail.com'                              # SMTP Server, like smtp.gmail.com
SEND_EMAIL_PORT = '587'                                         # SMTP Port, like 587
SEND_EMAIL_TLS = True                                           # Can be True or False

# paste services ids
PASTE_PASTEBIN = 1                                              # Pastebin
PASTE_PASTECODE = 2                                             # Pastecode

# Pastebin
PASTEBIN_ENABLED = True                                         # Enable or disable Pastebin send
PASTEBIN_POST_URL = 'https://pastebin.com/api/api_post.php'     # Post url
PASTEBIN_API_DEV_KEY = ''                                       # Your Pastebin API key
PASTEBIN_USER_NAME = ''                                         # Username - if not set, then anonymous paste is made
PASTEBIN_PASSWORD = ''                                          # Password
PASTEBIN_OPTION = 'paste'                                       # Option
PASTEBIN_FORMAT = 'text'                                        # Content type
PASTEBIN_POST_EXPIRE = '6M'                                     # 6 Months
PASTEBIN_PRIVATE = 2                                            # public = 0, unlisted = 1, private = 2

# Pastecode
PASTECODE_ENABLED = True                                        # Enable or disable
PASTECODE_POST_URL = 'https://pastecode.xyz/api/create'         # Post url
PASTECODE_POST_FORMAT = 'text'                                  # Content type
PASTECODE_POST_EXPIRE = 260000                                  # About 6 months (number of minutes)
PASTECODE_PRIVATE = 1                                           # Paste is private

# Telegram Bot / Channel - Created with Bofather https://core.telegram.org/bots#3-how-do-i-create-a-bot
# http://t.me/DemonsEyebot
# Info API https://core.telegram.org/bots/api
# https://api.telegram.org/bot[BOT_API_KEY]/sendMessage?chat_id=[MY_CHANNEL_NAME]&text=[MY_MESSAGE_TEXT]
TELEGRAM_BOT_ENABLED = True                                     # Enable or disable
TELEGRAM_BOT_NAME = 'DemonsEye'                                 # Name > not used
TELEGRAM_BOT_USERNAME = '@DemonsEyeKeylogger'                   # Username > not used
TELEGRAM_BOT_CHANNELID = -1001185988695                         # Important. Read docs folder
TELEGRAM_BOT_TOKEN = ''                                         # Important. Read docs folder
TELEGRAM_BOT_URL = 'https://api.telegram.org/bot' + TELEGRAM_BOT_TOKEN + '/'
TELEGRAM_BOT_GETME = 'getMe'                                    # To get info about Bot
TELEGRAM_BOT_UPDATES = 'getUpdates'                             # To get channel updates > not user
TELEGRAM_BOT_SEND = 'sendMessage'                               # To send a message to channel
TELEGRAM_BOT_SENDPHOTO = 'sendPhoto'                            # To send a photo to channel
TELEGRAM_BOT_SENDFILE = 'sendFile'                              # To send a file to channel



#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to handle '(my_)chat_member' updates.
Greets new users & keeps track of which chats the bot is in.

Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from datetime import datetime
import requests
import urllib.request
import time
from bs4 import BeautifulSoup
from selenium import webdriver

import time

import csv
import logging
from typing import Tuple, Optional

from telegram import Update, Chat, ChatMember, ParseMode, ChatMemberUpdated
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackContext,
    ChatMemberHandler,
)


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def scraperBUY():
    
    driver = webdriver.Chrome()
    driver.get('https://p2p.binance.com/en/trade/sell/USDT?fiat=RUB&payment=ALL')

    time.sleep(5) 

    prices = driver.find_elements_by_xpath("//div[@class='css-1m1f8hn']")

    for i in prices:
        print(i.text)
        a1.append(i.text)

    driver.close()
    
    
def scraperSELL():
    
    driver = webdriver.Chrome()
    driver.get('https://p2p.binance.com/en/trade/all-payments/USDT?fiat=RUB')

    time.sleep(5) 

    prices = driver.find_elements_by_xpath("//div[@class='css-1m1f8hn']")

    for i in prices:
        print(i.text)
        a2.append(i.text)

    driver.close()
      
    
def cbrates():
    data = requests.get(url="https://www.cbr-xml-daily.ru/daily_json.js").json()
    cbrate = float(data["Valute"]["USD"]["Value"])
    return cbrate
      
    
def clean(a1,a2):
    ratesBUY = []
    ratesSELL= []
    
    for i in a1:
        if i == '':
            break
        else:
            num = float(i)
            ratesBUY.append(num)
            
    for i in a2:
        if i == '':
            break
        else:
            num = float(i)
            ratesSELL.append(num)
                  
    rateBUY = sum(ratesBUY)/len(ratesBUY)
    rateSELL= sum(ratesSELL)/len(ratesSELL)
    
    rateBUY = round(rateBUY, 2)
    rateSELL= round(rateSELL, 2)
    
    return (rateBUY, rateSELL)


def handler():
    
    global a1
    a1 = []
    global a2
    a2 = []
    
    scraperBUY()
    scraperSELL()
    
    global rateBUY
    global rateSELL
    global cbrate
    
    rateBUY, rateSELL = clean(a1,a2)
    
    cbrate = cbrates()
    

def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = (
        old_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    )
    is_member = (
        new_status
        in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ]
        or (new_status == ChatMember.RESTRICTED and new_is_member is True)
    )

    return was_member, is_member


def track_chats(update: Update, context: CallbackContext) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name

    # Handle chat types differently:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            logger.info("%s started the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info("%s added the bot to the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    else:
        if not was_member and is_member:
            logger.info("%s added the bot to the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
            context.bot_data.setdefault("channel_ids", set()).discard(chat.id)


def show_chats(update: Update, context: CallbackContext) -> None:
    """Shows which chats the bot is in"""
    user_ids = ", ".join(str(uid) for uid in context.bot_data.setdefault("user_ids", set()))
    group_ids = ", ".join(str(gid) for gid in context.bot_data.setdefault("group_ids", set()))
    channel_ids = ", ".join(str(cid) for cid in context.bot_data.setdefault("channel_ids", set()))
    text = (
        f"@{context.bot.username} is currently in a conversation with the user IDs {user_ids}."
        f" Moreover it is a member of the groups with IDs {group_ids} "
        f"and administrator in the channels with IDs {channel_ids}."
    )
    update.effective_message.reply_text(text)


def greet_chat_members(update: Update, context: CallbackContext) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    if not was_member and is_member:
        update.effective_chat.send_message(
            f"Добро пожаловать {cause_name} в чат! Если у вас есть какие-либо вопросы, связанные с блокчейном или каналом, вы можете задать их здесь. Введите /jobs чтобы просмотреть текущие объявления о вакансиях.",
            parse_mode=ParseMode.HTML,
        )     


def rates(update, context):
    
    message = "USD/RUB rates:\nSell USDT: {0} \nBuy USDT: {1} \nCBRF rate: {2}".format(rateBUY,rateSELL,cbrate)

    update.effective_chat.send_message(message,parse_mode=ParseMode.MARKDOWN,)
    
    
def send_rate():
    
    message = "USD/RUB exchange rate:\nSell USDT: {0} \nBuy USDT: {1} \n".format(77,64)
    
    bot.send_message("someusernameorid", message,parse_mode=ParseMode.MARKDOWN)


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("your token here")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Keep track of which chats the bot is in
    dispatcher.add_handler(ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER))


    dispatcher.add_handler(CommandHandler("rates", rates))
    
    
    now = datetime.now()
    current_time = now.strftime("%M")

    if current_time == "13":
        handler()

    else:
        pass


    # Handle members joining/leaving chats.
    dispatcher.add_handler(ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    # Start the Bot
    # We pass 'allowed_updates' handle *all* updates including `chat_member` updates
    # To reset this, simply pass `allowed_updates=[]`
    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    updater.idle()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3.5
import sys
import asyncio
import logging
# from systemd.journal import JournalHandler
import telepot
import telepot.aio
from telepot.namedtuple import InlineQueryResultArticle
from telepot.namedtuple import InputTextMessageContent
from telepot.aio.routing import by_chat_command
from telepot.aio.helper import Router
import subprocess
from bs4 import BeautifulSoup
import urllib.parse, urllib.request

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s' +
                           '- %(name)-14s: %(message)s')


def search_rooms(name):
    parameters = {
                  'pStart': '1',
                  'pSuchbegriff': name
                 }
    url = 'https://online.tugraz.at/tug_online/'
    parameters = bytes(urllib.parse.urlencode(parameters).encode())
    handler = urllib.request.urlopen(url + 'wbSuche.raumSuche', parameters)
    soup = BeautifulSoup(handler.read(), 'html.parser')

    table = soup.find('table', attrs={'class': 'list'})
    if table is None:
        return []
    rooms = []
    rows = table.findAll('tr')
    for tr in rows:
        cols = tr.findAll('td')
        if(len(cols) > 5):
            rooms.append((cols[3].find(text=True), cols[5].find(text=True),
                         url + cols[5].find('a')['href']))
    return rooms

async def on_room_handler(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    args = msg['text'].split(' ', 1)
    searchstr = ''
    output = ''
    if len(args) > 1:
        searchstr = args[1]
    rooms = search_rooms(searchstr)
    on_room_handler.log.info("string: " + searchstr + " from: " + 
                             msg['from'].get('first_name') + " " 
                             + msg['from'].get('last_name') + " " + chat_type)
    if len(rooms) == 0:
        await bot.sendMessage(chat_id, 'Nothing found')
    else:
        for room in rooms:
            output = (output + str(room[0]) + ' | ' + str(room[1]) + '\n' + str(room[2]) + '\n\n')
        await bot.sendMessage(chat_id, output)
on_room_handler.log = logging.getLogger('room')


async def on_myip_handler(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if msg['from']['id'] != 263054564:
        on_myip_handler.log.info("/blocked")
        await bot.sendMessage(chat_id, 'this command is not public')
        return
    ip = subprocess.check_output(['dig', '+short', 'myip.opendns.com', '@resolver1.opendns.com'])
    on_myip_handler.log.info("answered")
    await bot.sendMessage(chat_id, ip.decode())
on_myip_handler.log = logging.getLogger('myip')

async def on_slap_handler(msg):
    args = msg['text'].split(' ', 1)
    content_type, chat_type, chat_id = telepot.glance(msg)
    caption = msg['from']['first_name'] + " slaps " + args[1] + " around a bit with a large trout"
    try:
        await bot.sendPhoto(chat_id, on_slap_handler.file_id, caption=caption)
    except telepot.exception.TelegramError:
        on_slap_handler.log.info("upload trout")
        ret = await bot.sendPhoto(chat_id, open('trout.png', 'rb'), caption=caption)
        on_slap_handler.file_id = ret['photo'][0]['file_id']

on_slap_handler.log = logging.getLogger('slap')
on_slap_handler.file_id = ""


async def default_chat_handler(msg):
    if not msg['text'].startswith('/'):
        return
    content_type, chat_type, chat_id = telepot.glance(msg)
    if chat_type == 'private':
        await bot.sendMessage(chat_id, "unknown command")
default_chat_handler.log = logging.getLogger('default chat')


def on_edited_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg, flavor='edited_chat')
    info = ('Edited chat: ' + content_type + ' ' + chat_type + ' ' + str(chat_id))
    on_edited_chat_message.log.info(info)
on_edited_chat_message.log = logging.getLogger('chat edit')


async def on_callback_query(msg):
    query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
    on_callback_query.log.info('Callback query:', query_id, from_id, data)

    if data == 'notification':
        await bot.answerCallbackQuery(query_id,
                                      text='Notification at top of screen')
    elif data == 'alert':
        await bot.answerCallbackQuery(query_id, text='Alert!', show_alert=True)
    elif data == 'edit':
        global message_with_inline_keyboard

        if message_with_inline_keyboard:
            msg_idf = telepot.message_identifier(message_with_inline_keyboard)
            await bot.editMessageText(msg_idf, 'NEW MESSAGE HERE!!!!!')
        else:
            await bot.answerCallbackQuery(query_id,
                                          text='No previous message to edit')
on_callback_query.log = logging.getLogger('callback query')


def on_inline_query(msg):
    def compute():
        query_id, from_id, query_string = telepot.glance(msg,
                                                         flavor='inline_query')
        on_inline_query.log.info('Computing for: ' + query_string)

        rooms = search_rooms(query_string)
        articles = []
        i=0
        for room in rooms:
            if room[0] is None or room[1] is None or room[2] is None:
                continue
            i += 1
            articles.append(InlineQueryResultArticle(
                        id=str(i),
                        title=room[0],
                        input_message_content=InputTextMessageContent(
                            message_text=(room[0] + ' | ' + room[1] + '\n' + room[2]))))
        return articles
    answerer.answer(msg, compute)
on_inline_query.log = logging.getLogger('inline query')


def on_chosen_inline_result(msg):
    flavor = 'chosen_inline_result'
    result_id, from_id, query_string = telepot.glance(msg, flavor=flavor)
    on_chosen_inline_result.log.info('Chosen:',
                                     result_id, from_id, query_string)
on_chosen_inline_result.log = logging.getLogger('inline result')


logger = logging.getLogger('main')

if(len(sys.argv) < 2):
    logger.error('Token is missing! usage: ' + sys.argv[0] + ' <TOKEN>')
    exit(-1)

TOKEN = sys.argv[1]

if(len(TOKEN) != 45):
    logger.error('Wrong Token length! usage: ' + sys.argv[0] + ' <TOKEN>')
    exit(-1)

bot = telepot.aio.Bot(TOKEN)
answerer = telepot.aio.helper.Answerer(bot)

chat_router = Router(by_chat_command(), 
                                    {'myip': on_myip_handler,
                                     'room': on_room_handler,
                                     'slap': on_slap_handler,
                                     None : default_chat_handler
                                     })

loop = asyncio.get_event_loop()
loop.create_task(bot.message_loop({'chat': chat_router.route,
                                   'edited_chat': on_edited_chat_message,
                                   'callback_query': on_callback_query,
                                   'inline_query': on_inline_query,
                                   'chosen_inline_result': on_chosen_inline_result}))
                                   
logger.info('Listening ...')
loop.run_forever()

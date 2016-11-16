#!/usr/bin/env python3.5
import sys
import asyncio
import logging
# from systemd.journal import JournalHandler
import telepot
import telepot.aio
from telepot.namedtuple import InlineQueryResultArticle
from telepot.namedtuple import InputTextMessageContent
import subprocess
from bs4 import BeautifulSoup
import urllib

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


async def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    info = content_type + ' ' + chat_type + ' ' + str(chat_id)
    if(msg.get('chat').get('last_name')):
        info += (' ' + msg['chat']['first_name'] +
                 ' ' + msg['chat']['last_name'])

    if content_type != 'text':
        on_chat_message.log.info(info)
        return

    args = msg['text'].split(' ', 1)
    command = args[0].lower()

    info += ': ' + msg['text']
    on_chat_message.log.info(info)
    if command == '/myip':
        if msg['from']['id'] != 263054564:
            await bot.sendMessage(chat_id, 'this command is not public')
            return
        ip = subprocess.check_output(['dig', '+short', 'myip.opendns.com',
                                      '@resolver1.opendns.com'])
        await bot.sendMessage(chat_id, ip.decode())

    elif command == '/hofer_wählen?':
        await bot.sendMessage(chat_id, "Nein!")

    elif command == '/room':
        searchstr = ''
        output = ''
        if len(args) > 1:
            searchstr = args[1]
        rooms = search_rooms(searchstr)
        if len(rooms) == 0:
            await bot.sendMessage(chat_id, 'Nothing found')
        else:
            for room in rooms:
                output = (output + room[0] + ' | ' +
                          room[1] + '\n' + room[2] + '\n\n')
            await bot.sendMessage(chat_id, output)
on_chat_message.log = logging.getLogger('chat')


def on_edited_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg,
                                                      flavor='edited_chat')
    info = ('Edited chat: ' + content_type + ' ' + chat_type + ' ' +
            str(chat_id))
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
        for room in rooms:
            if room[0] is None or room[1] is None or room[2] is None:
                continue
            articles.append(InlineQueryResultArticle(
                        id=room[0],
                        title=room[0],
                        input_message_content=InputTextMessageContent(
                            message_text=(room[0] + ' | ' + room[1] + '\n' +
                                          room[2]))))
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

loop = asyncio.get_event_loop()
loop.create_task(bot.message_loop({'chat': on_chat_message,
                                   'edited_chat': on_edited_chat_message,
                                   'callback_query': on_callback_query,
                                   'inline_query': on_inline_query,
                                   'chosen_inline_result':
                                   on_chosen_inline_result}))
logger.info('Listening ...')
loop.run_forever()

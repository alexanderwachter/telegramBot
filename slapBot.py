#!/usr/bin/env python3.5
import sys
import asyncio
import logging
import telepot
import telepot.aio
from telepot.namedtuple import InlineQueryResultArticle, InlineQueryResultPhoto
from telepot.namedtuple import InputTextMessageContent
from telepot.aio.routing import by_chat_command
from telepot.aio.helper import Router

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s' +
                           '- %(name)-14s: %(message)s')


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


def on_inline_query(msg):
    def compute():
        query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
        url = "https://en.wikipedia.org/wiki/Wikipedia:Whacking_with_a_wet_trout#/media/File:Rainbow_trout_transparent.png"
        caption = msg['from']['first_name'] + " slaps " + query_string + " around a bit with a large trout"
        slap = [InlineQueryResultPhoto(
                      id='1', photo_url=url, thumb_url=url, caption=caption)
                ]
        return slap
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
                                    {
                                     'slap': on_slap_handler,
                                     None : default_chat_handler
                                     })

loop = asyncio.get_event_loop()
loop.create_task(bot.message_loop({'chat': chat_router.route,
                                   'inline_query': on_inline_query,
                                   'chosen_inline_result': on_chosen_inline_result}))
                                   
logger.info('Listening ...')
loop.run_forever()

import motor.motor_asyncio

from bson.objectid import ObjectId
from fastapi import Request

from ..libs.utils import verify_password
from ..libs.utils import get_password_hash
import httpx
from ..schemas.user_model import UserRegisterForm, UserInDB
from ..schemas.space_model import CreateSpaceForm, SpaceModel, CreateSceneForm, UpdateSceneForm
from ..instance.config import TELEGRAM_TOKEN

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

class tele_manager(object):
    t_updater = None
    
    @classmethod
    def echo(cls, update: Update, context: CallbackContext) -> None:
        """Echo the user message."""   
        update.message.reply_text(update.message.text)

    @classmethod
    def init(cls):
        cls.t_updater = Updater(TELEGRAM_TOKEN)

        # Get the dispatcher to register handlers
        dispatcher = cls.t_updater.dispatcher

        # on non command i.e message - echo the message on Telegram
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, cls.echo))

        # Start the Bot
        cls.t_updater.start_polling()

        pass

    @classmethod
    def sendMsg(cls, chatid,msg):
        cls.t_updater.bot.sendMessage(chatid, msg)
    @classmethod
    async def sendTgMessage(cls,chatid:str,message: str):
        tg_msg = {"chat_id": chatid, "text": message, "parse_mode": "Markdown"}
        API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        async with httpx.AsyncClient() as client:
            await client.post(API_URL, json=tg_msg)
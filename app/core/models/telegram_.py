import motor.motor_asyncio
from pymongo import MongoClient

from bson.objectid import ObjectId
from fastapi import Request

from app.core.models.database import db_manager
#from .database import db_manager

from ..libs.utils import verify_password
from ..libs.utils import get_password_hash
import httpx
from ..schemas.user_model import UserRegisterForm, UserInDB
from ..schemas.space_model import CreateSpaceForm, SpaceModel, CreateSceneForm, UpdateSceneForm
from ..instance.config import TELEGRAM_TOKEN,MONGODB_URL

from telegram import *
from telegram.ext import *
from telegram.ext import filters

MENU,SELECT_BUTTON,SALE= range(3)

class tele_manager(object):
    t_updater = None

    @classmethod
    def echo(cls, update: Update, context: CallbackContext) -> None:
        """Echo the user message."""   
        update.message.reply_text(update.message.text)

    @classmethod 
    def start(cls, update: Update, context: CallbackContext) -> int:

        scene = cls.get_collection("users").find_one({"chatid": str(update.effective_user.id)})
        context.user_data['_id']=scene['_id']
        context.user_data['chatid']=update.effective_user.id

        show_list = []
        show_list.append([InlineKeyboardButton("MENU", callback_data="menu")])
        show_list.append([InlineKeyboardButton("종료", callback_data="no")])
        show_markup =InlineKeyboardMarkup(show_list)
        context.bot.send_photo(chat_id=update.effective_user.id,photo=open('/Users/seni/han30_project/Homeless-Cow-Helperlverse/app/core/templates/KakaoTalk_Image_2022-10-30-16-50-47.png','rb'))
        update.message.reply_text(f"Hello {scene['userid']}!\nSelect Button",reply_markup=show_markup)
    
        return MENU

    @classmethod 
    def menu(cls, update: Update, context: CallbackContext) -> int:
        update.callback_query.message.edit_text("[Menu]")

        query = update.callback_query
        if query.data == 'menu':
            show_list =[]
            show_list.append([InlineKeyboardButton("My Space List", callback_data="msl")])
            show_list.append([InlineKeyboardButton("Public Space List", callback_data="psl")])
            show_list.append([InlineKeyboardButton("Veterinarian List", callback_data="vl")])
            show_list.append([InlineKeyboardButton("Crop Sales", callback_data="cs")])
            show_list.append([InlineKeyboardButton("종료", callback_data="no")])
            show_markup =InlineKeyboardMarkup(show_list)
            context.bot.send_message(chat_id=context.user_data['chatid'],text=f"Select Button you need",reply_markup=show_markup)
            return SELECT_BUTTON
        else:
            return ConversationHandler.END

    @classmethod 
    def select(cls, update: Update, context: CallbackContext) -> int:
        query = update.callback_query

        if query.data == 'msl':
            update.callback_query.message.edit_text("[Your Space List]")
            a= cls.get_collection("users").find_one({"chatid": str(context.user_data['chatid'])})
            print(a['spaces'])
            j=1
            for i in a['spaces']:
                temp = cls.get_collection("spaces").find_one({"_id": ObjectId(i)})
            
                name = temp['name']
                explain = temp['explain']
                agreement = temp['agreement']
                context.bot.send_message(chat_id=context.user_data['chatid'],text=f"{j}. ({agreement}){name} : {explain}")
                j+=1
            return ConversationHandler.END
        elif query.data == "psl":
            update.callback_query.message.edit_text("[Public Space List]")
            temp = cls.get_collection("spaces").find({"agreement": "public"})
            j=1
            for i in temp:
                name = i['name']
                explain = i['explain']
                agreement = i['agreement']
                context.bot.send_message(chat_id=context.user_data['chatid'],text=f"{j}. ({agreement}){name} : {explain}")
                j+=1
            return ConversationHandler.END
        elif query.data == "vl":
            context.bot.send_message(chat_id=context.user_data['chatid'],text=f"000-0000-0000 : location ~ , name~")
            return ConversationHandler.END
        elif query.data == "cs":
            show_list=[]
            show_list.append([InlineKeyboardButton("SALE", callback_data="sale")])
            show_list.append([InlineKeyboardButton("BUY", callback_data="buy")])
            show_list.append([InlineKeyboardButton("종료", callback_data="no")])
            show_markup =InlineKeyboardMarkup(show_list)
            context.bot.send_message(chat_id=context.user_data['chatid'],text=f"Select Button you need",reply_markup=show_markup)
            return SALE
        else:
            return ConversationHandler.END

    @classmethod 
    def sale(cls, update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        update.callback_query.message.edit_text("[SELECT Button]")
        if query.data == 'sale':
            context.bot.send_message(chat_id=context.user_data['chatid'],text=f"판매할 작물을 등록할 수 있습니다")
            return ConversationHandler.END
        elif query.data == 'buy':
            context.bot.send_message(chat_id=context.user_data['chatid'],text=f"구매할 작물을 선택할 수 있습니다")
            return ConversationHandler.END
        else:
            return ConversationHandler.END

    @classmethod 
    def cancel(cls, update: Update, context: CallbackContext) -> int:
        """Display the gathered info and end the conversation."""
        context.user_data.clear()
        update.message.reply_text("Cancel!")
        return ConversationHandler.END

    @classmethod
    def init(cls):

        cls.client = MongoClient(MONGODB_URL)
        cls.db = cls.client["simulverse"]


        cls.t_updater = Updater(TELEGRAM_TOKEN)

        # Get the dispatcher to register handlers
        dispatcher = cls.t_updater.dispatcher

        # on non command i.e message - echo the message on Telegram
        #dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, cls.echo))

        dispatcher.add_handler(ConversationHandler(
            entry_points=[CommandHandler('start',cls.start)],
            states={
                MENU : [CallbackQueryHandler(cls.menu)],
                SELECT_BUTTON : [CallbackQueryHandler(cls.select)],
                SALE : [CallbackQueryHandler(cls.sale)]

            },
            fallbacks=[CommandHandler('cancel', cls.cancel)],
        ))
        # Start the Bot
        cls.t_updater.start_polling()

        pass
    @classmethod
    def get_uinfo(cls,chat_id:int):
        
        a= cls.get_collection("users").find_one({"chatid": str(chat_id)})
        return a

    def get_sinfo(cls,id:int):
        return cls.get_collection("spaces").find_one({"_id": id})

    @classmethod
    def get_collection(cls, name):
        return cls.db[name]

    @classmethod
    def sendMsg(cls, chatid,msg):
        cls.t_updater.bot.sendMessage(chatid, msg)

    @classmethod
    async def sendTgMessage(cls,chatid:str,message: str):
        tg_msg = {"chat_id": chatid, "text": message, "parse_mode": "Markdown"}
        API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        async with httpx.AsyncClient() as client:
            await client.post(API_URL, json=tg_msg)
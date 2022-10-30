import motor.motor_asyncio

from bson.objectid import ObjectId
from fastapi import Request

from ..libs.utils import verify_password
from ..libs.utils import get_password_hash
import httpx
from ..schemas.user_model import UserRegisterForm, UserInDB
from ..schemas.space_model import CreateSpaceForm, SpaceModel, CreateSceneForm, UpdateSceneForm
from ..instance.config import TELEGRAM_TOKEN

class tele_manager(object):

    @classmethod
    async def sendTgMessage(cls,chatid:str,message: str):
        tg_msg = {"chat_id": chatid, "text": message, "parse_mode": "Markdown"}
        API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        async with httpx.AsyncClient() as client:
            await client.post(API_URL, json=tg_msg)
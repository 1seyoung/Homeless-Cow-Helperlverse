
from fastapi.responses import HTMLResponse
from os.path import dirname, abspath
from pathlib import Path
from fastapi import APIRouter, Depends, Request, Response, responses, HTTPException, status
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette.responses import StreamingResponse

from jose import JWTError, jwt
from bson.objectid import ObjectId

from ..models.database import db_manager
from ..instance import config
from ..models.auth_manager import get_current_user
from ..schemas.space_model import CreateSpaceForm, SpaceModel
from ..models.telegram_ import tele_manager

router = APIRouter(include_in_schema=False)

db_manager.init_manager(config.MONGODB_URL, "simulverse")
BASE_DIR = dirname(dirname(abspath(__file__)))

from fastapi.responses import StreamingResponse

import io

@router.get("/asset/image/{image_id}", 
        responses = {
            200: {
                "content": {"video/mp4": {}}}
        }, response_class=Response)
       
async def image(request: Request, image_id:str, auth_user= Depends(get_current_user)):
    token = request.cookies.get('access_token')
    payload = jwt.decode(token.split()[1], config.JWT_SECRET_KEY, algorithms=[config.ALGORITHM])
    userid: str = payload.get("sub")
    
    tele_manager.sendMsg(await db_manager.get_chatid(userid),f"enter scene({image_id}): {userid}")    
    image_bytes, content_type = await db_manager.download_file(ObjectId(image_id))
    return Response(content=image_bytes, media_type=content_type)


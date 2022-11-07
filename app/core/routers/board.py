from fastapi.responses import HTMLResponse
from os.path import dirname, abspath
from pathlib import Path
from fastapi import APIRouter, Depends, Request, responses, HTTPException, status
from fastapi.templating import Jinja2Templates
from jose import jwt

from starlette.responses import RedirectResponse
from bson.objectid import ObjectId

from ..models.database import db_manager
from ..instance import config
from ..models.auth_manager import auth_manager, get_current_user
from ..schemas.space_model import CreateSpaceForm
from ..libs.resolve_error import resolve_error

router = APIRouter(include_in_schema=False)

db_manager.init_manager(config.MONGODB_URL, "simulverse")
BASE_DIR = dirname(dirname(abspath(__file__)))

templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'templates')))

@router.get("/", response_class=HTMLResponse)
async def root(request: Request, auth_user= Depends(get_current_user)):
    if not auth_user :
        data = {'text': '<h1>Welcome to the Simulverse Management System </h1>\n', 'spaces':{}}  
        return templates.TemplateResponse("page.html", {"request": request, "data": data, "login": False})
    else:
        token = request.cookies.get('access_token')
        payload = jwt.decode(token.split()[1], config.JWT_SECRET_KEY, algorithms=[config.ALGORITHM])
        userid: str = payload.get("sub")
        user_name= await db_manager.get_name(userid)
        data = {'text': f'<div style="text-align: center" ;><h1>Welcome {user_name}! </h1></div>\n', 'spaces':{}}  
        return templates.TemplateResponse("page.html", {"request": request, "data": data, "login": True})
    

@router.get("/board/", response_class=HTMLResponse)
async def view(request: Request, auth_user= Depends(get_current_user)):
    if not auth_user :
        data = {'text': '<h1>Welcome to the Simulverse Management System </h1>\n<p>Please Log-in or Sign-up.</p>', 'spaces':{}}  
        return templates.TemplateResponse("board.html", {"request": request, "data": data, "login": False})
    else:
        token = request.cookies.get('access_token')
        payload = jwt.decode(token.split()[1], config.JWT_SECRET_KEY, algorithms=[config.ALGORITHM])
        userid: str = payload.get("sub")
        user_name= await db_manager.get_name(userid)
        spaces = await db_manager.get_public_spaces()
        data = {'text':f'<div style="text-align: center" ;><h1>Welcome {user_name}! </h1>\n<h1>-Public Board-</h1></div>', 'spaces':spaces} 
        
        errors = []
        if 'error' in request.query_params:
            errors = [ resolve_error(x) for x in request.query_params['error'].split('.')]
        
        #print(errors)
        return templates.TemplateResponse("board.html", {"request": request, "data": data, "login": True, "errors":errors})

@router.get("/board/view/{space_id}", response_class=HTMLResponse)
async def space(request: Request, space_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        space = await db_manager.get_space(ObjectId(space_id))
        if space:
            if str(auth_user.id) in space.viewers:
                data = {'text':f"<h1>{space.name}</h1><p/><h3>{space.explain}</h3>",
                        'role':space.viewers[str(auth_user.id)], 'scenes':space.scenes, 'space_id':space.id}
                
                '''
                data.text = space explain
                data.scenes
                data.space_id
                data.role
                '''
                return templates.TemplateResponse("space/view_board.html", {"request": request, "data": data, "login":True})
            else:
                data = {'text':f"<h1>{space.name}</h1><p/><h3>{space.explain}</h3>",
                        'role':"viewer", 'scenes':space.scenes, 'space_id':space.id}
                
                #return templates.TemplateResponse("space/view_space.html", {"request": request, "data": data, "login":True})
                return templates.TemplateResponse("space/onlyview.html", {"request": request, "data": data, "login":True})
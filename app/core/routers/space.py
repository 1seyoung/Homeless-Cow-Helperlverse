from fastapi.responses import HTMLResponse
from os.path import dirname, abspath
from pathlib import Path
from fastapi import APIRouter, Depends, Request, status
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from bson.objectid import ObjectId

from ..models.database import db_manager
from ..instance import config
from ..models.auth_manager import get_current_user
from ..schemas.space_model import CreateSceneForm, CreateSpaceForm, UpdateSceneForm

import json

router = APIRouter(include_in_schema=False)

db_manager.init_manager(config.MONGODB_URL, "simulverse")
BASE_DIR = dirname(dirname(abspath(__file__)))

templates = Jinja2Templates(directory=str(Path(BASE_DIR, 'templates')))

@router.get("/space/view/{space_id}", response_class=HTMLResponse)
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
                return templates.TemplateResponse("space/view_space.html", {"request": request, "data": data, "login":True})
            else:
                data = {'text':f"<h1>{space.name}</h1><p/><h3>{space.explain}</h3>",
                        'role':"viewer", 'scenes':space.scenes, 'space_id':space.id}
                
                #return templates.TemplateResponse("space/view_space.html", {"request": request, "data": data, "login":True})
                return templates.TemplateResponse("space/onlyview.html", {"request": request, "data": data, "login":True})

@router.get("/space/insert/{space_id}", response_class=HTMLResponse)        
async def insert_scene(request: Request, space_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        scenes = await db_manager.get_scenes_from_space(ObjectId(space_id))
        
        data = {"scenes":scenes}
        return templates.TemplateResponse("space/create_scene.html", {"request": request, "data":data, "login":True})

@router.post("/space/insert/{space_id}", response_class=HTMLResponse)        
async def handle_insert_scene(request: Request, space_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        form = CreateSceneForm(request)
        await form.load_data()
        if await form.is_valid():
            await db_manager.create_scene(form, ObjectId(space_id))

            response = RedirectResponse(f"/space/view/{space_id}", status_code=status.HTTP_302_FOUND)
            return response
        else:
            form.__dict__.update(request=request)
            form.__dict__.update(data={})
            return templates.TemplateResponse(f"space/create_scene.html", form.__dict__)

@router.get("/space/scene/{space_id}/{scene_id}", response_class=HTMLResponse)
async def scene(request: Request, space_id: str, scene_id:str, auth_user= Depends(get_current_user)):
    '''
    Fetch scene data
    :param request:browser's request, scene_id: id of a scene with ObjectID, auth_user: authuentication
    '''
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        scene = await db_manager.get_scene(ObjectId(scene_id))
        space = await db_manager.get_space(ObjectId(space_id))
        print(scene)
        
        links = []
        # objects = []
        # linkObjs = []
        
        for link in scene["links"]:
            target_link = await db_manager.get_collection("links").find_one({'_id':link})
            target_name = await db_manager.get_scene(target_link['target_id'])
            
            links.append([target_name['name'], target_link['target_id']
                                             , target_link['x']
                                             , target_link['y']
                                             , target_link['z']
                                             , target_link['yaw']
                                             , target_link['pitch']
                                             , target_link['roll']
                                             , target_link['_id']])
            
        # for object in scene["objects"]:
        #     target_object = await db_manager.get_collection("objects").find_one({'_id':object})
        #     # target_name = await db_manager.get_scene(target_objects['target_id'])
            
        #     objects.append([   target_object['x']
        #                      , target_object['y']
        #                      , target_object['z']
        #                      , target_object['yaw']
        #                      , target_object['pitch']
        #                      , target_object['roll']
        #                      , target_object['xscale']
        #                      , target_object['yscale']
        #                      , target_object['zscale']
        #                      , target_object['getmetry']
        #                      , target_object['color']
        #                      , target_object['opacity']
        #                      , target_object['_id']])
            
        # for linkObj in scene["linkObjs"]:
        #     target_linkObj = await db_manager.get_collection("objects").find_one({'_id':linkObj})
        #     # target_name = await db_manager.get_scene(target_objects['target_id'])
            
        #     linkObjs.append([target_linkObj['name'], target_linkObj['x']
        #                                         , target_linkObj['y']
        #                                         , target_linkObj['z']
        #                                         , target_linkObj['yaw']
        #                                         , target_linkObj['pitch']
        #                                         , target_linkObj['roll']
        #                                         , target_linkObj['xscale']
        #                                         , target_linkObj['yscale']
        #                                         , target_linkObj['zscale']
        #                                         , target_linkObj['getmetry']
        #                                         , target_linkObj['color']
        #                                         , target_linkObj['opacity']
        #                                         , target_linkObj['_id']])


        data = {'space_id':space_id, 'background':scene['image_id'], 'links':links, 'space_data':space}
        return templates.TemplateResponse("aframe/scene.html", {"request": request, "data": data, "login":True})

@router.get("/space/scene/edit/{space_id}/{scene_id}", response_class=HTMLResponse)
async def scene_edit(request: Request, scene_id:str, space_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        '''
        {'_id': ObjectId('632f2186b763ee36b2407771'), 'target_id':ObjectId('632f21a1b763ee36b2407785'), 'x':'0', 'y':'1', 'z':'-6'}
        '''

        scene = await db_manager.get_scene(ObjectId(scene_id))

        scenes = await db_manager.get_scenes_from_space(ObjectId(space_id))
        
        link_info = []
        for l in scene["links"]:
            link = await db_manager.get_link(l)
            print(link)
            link_info.append(link)
        
        data = {'name': scene['name'], 'image_id':scene['image_id'], "scenes":scenes, "links":link_info}
        return templates.TemplateResponse("space/update_scene.html", {"request": request, "data": data, "login":True})

@router.post("/space/scene/edit/{space_id}/{scene_id}", response_class=HTMLResponse)
async def handle_scene_edit(request: Request, scene_id:str, space_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        form = UpdateSceneForm(request)
        await form.load_data()
        
        if await form.is_valid():
            await db_manager.update_scene(form, space_id=ObjectId(space_id), scene_id=ObjectId(scene_id))

            response = RedirectResponse(f"/space/view/{space_id}", status_code=status.HTTP_302_FOUND)
            return response
        else:
            return templates.TemplateResponse(f"/space/scene/edit/{space_id}/{scene_id}", form.__dict__)

@router.get("/space/edit/{space_id}", response_class=HTMLResponse)
async def edit_space(request: Request, space_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        space = await db_manager.get_space(ObjectId(space_id))
        if space.viewers[str(auth_user.id)] == 'Editor' or str(auth_user.id) in space.viewers:
            viewers = {}
            for user, val in space.viewers.items():
                #print(user, val)
                _user = await db_manager.get_user_by_id(ObjectId(user))
                if auth_user.email != _user.email:
                    viewers[_user.email] = val
            
            #print(viewers)
            
            data = {'space_name':space.name, 'space_explain':space.explain, 'invite_lists':viewers, 'agreement' : space.agreement}
            return templates.TemplateResponse("space/update_space.html", {"request": request, "data": data, "login":True})
        else:
            # raise Exception
           return templates.TemplateResponse("space/create_space.html", {"request": request, "data": {}, "login":True})

@router.post("/space/edit/{space_id}", response_class=HTMLResponse)
async def handle_update_space(request: Request, space_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        form = CreateSpaceForm(request)
        await form.load_data()
        
        response = None
        if await form.is_valid():
            await db_manager.update_space(auth_user, ObjectId(space_id), form)
            response = RedirectResponse(f"/view/", status_code=status.HTTP_302_FOUND)
        else:
            response = RedirectResponse(f"/view/?error=c01", status_code=status.HTTP_302_FOUND)
        return response

@router.post("/space/delete/scene/{space_id}/{scene_id}", response_class=HTMLResponse)
async def handle_delete_scene(request: Request, space_id:str, scene_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        # delete scene
        await db_manager.delete_scene(ObjectId(space_id), ObjectId(scene_id))

        response = RedirectResponse(f"/view/", status_code=status.HTTP_302_FOUND)
        return response

@router.post("/space/delete/space/{space_id}")
async def handle_delete_space(request: Request, space_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        # delete scene
        result = await db_manager.get_collection('spaces').find_one({'_id':ObjectId(space_id)})
        for scene in result['scenes']:
            await db_manager.delete_scene(ObjectId(space_id), ObjectId(scene))

        await db_manager.get_collection('spaces').delete_one({'_id':ObjectId(space_id)})
        await db_manager.get_collection('users').update_many({}, {'$unset':{f"spaces.{str(space_id)}":""}})
        
        response = RedirectResponse(f"/", status_code=status.HTTP_302_FOUND)
        return response

@router.put("/space/scene/link/update/{space_id}")
async def handle_link_update(request: Request, space_id:str, auth_user= Depends(get_current_user)):
    if not auth_user :
        response = RedirectResponse("/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        return response
    else:
        # check ownership
        spaces = await db_manager.get_spaces(auth_user)
        
        #spaces)
        if spaces[space_id][2] == 'Editor':
            _body = await request.body()
            _body = result = json.loads(_body.decode('utf-8'))
            print(_body)
            for key, val in _body.items():
                # print(key)
                if key == 'objects':
                    for i in range(len(val)):
                        print(val[i][0]["x"])
                        print(val[i][0]["y"])
                        print(val[i][0]["z"]) # position x, y, z
                        print(val[i][1]["x"])
                        print(val[i][1]["y"])
                        print(val[i][1]["z"]) # rotation x, y, z
                        print(val[i][2]["x"])
                        print(val[i][2]["y"])
                        print(val[i][2]["z"]) # scale x, y, z
                        print(val[i][3])      # material geometry
                        print(val[i][4]["color"]) # color
                        print(val[i][4]["opacity"]) # opacity
                        print(val[i][5]) # class
                elif key == 'linkObjs':
                    for i in range(len(val)):
                        data = {
                            'x':val[i][0]["x"], 
                            'y':val[i][0]["y"], 
                            'z':val[i][0]["z"], 
                            'yaw':val[i][1]["x"], 
                            'pitch':val[i][1]["y"], 
                            'roll':val[i][1]["z"], 
                            'xscale' : val[i][2]["x"], 
                            'yscale' : val[i][2]["y"], 
                            'zscale' : val[i][2]["x"], 
                            'geometry': val[i][3], 
                            'color' : val[i][4]["color"], 
                            'opacity' : val[i][4]["opacity"], 
                            'class' : val[i][5], 
                            'href' : val[i][6], 
                            'value' : val[i][7]["value"]
                            }
                        
                        res = await db_manager.get_collection('linkObjs').insert_one(data)
                        await db_manager.get_collection('scenes').update_one({'_id':ObjectId(scene_id)}, {'$push':{'linkObjs':ObjectId(res.inserted_id)}})
                        
                        print(val[i][0]["x"])
                        print(val[i][0]["y"])
                        print(val[i][0]["z"]) # position x, y, z
                        print(val[i][1]["x"])
                        print(val[i][1]["y"])
                        print(val[i][1]["z"]) # rotation x, y, z
                        print(val[i][2]["x"])
                        print(val[i][2]["y"])
                        print(val[i][2]["z"]) # scale x, y, z
                        print(val[i][3])      # material geometry
                        print(val[i][4]["color"]) # color
                        print(val[i][4]["opacity"]) # opacity
                        print(val[i][5]) # class
                        print(val[i][6]) # href
                        print(val[i][7]["value"]) # nametag value
                else:
                    data = {'x':val[0]["x"], 'y':val[0]["y"], 'z':val[0]["z"], 'yaw':val[1]["x"], 'pitch':val[1]["y"], "roll":val[1]["z"]}
                    link = await db_manager.get_collection('links').update_one({'_id':ObjectId(key)}, {'$set':data})
            
            return 'done'
        else:
            return 'Not authorized'
       
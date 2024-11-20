from fastapi import FastAPI
from pymongo import MongoClient
from fastapi import HTTPException
from fastapi import Form
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from fastapi import Request
import json
from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pyfcm import FCMNotification

uri = "mongodb+srv://chen:2744805546@chatroom.13sv1.mongodb.net/?retryWrites=true&w=majority&appName=Chatroom"
fcm = FCMNotification(service_account_file="service_account_file.json", project_id="chatroom-ed57d")
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["MobileDemo"]
Chatrooms = db["Chatroom"]
Messages = db["Message"]
Tokens = db["Tokens"]
# define a Fast API app
app = FastAPI()

@app.get("/demo/")
async def get_demo(a: int = 0, b: int = 0, status_code=200):
  sum = a+b
  data = {"sum": sum, "date": datetime.today()}
  return JSONResponse(content=jsonable_encoder(data))

@app.get("/get_chatrooms")
async def get_chatrooms():
    chatrooms = list(Chatrooms.find({}, {"_id": 0}))
    return {"data": chatrooms, "status": "OK"}

@app.get("/get_messages")
async def get_messages(chatroom_id: int):
    messages = list(Messages.find({"chatroom_id": chatroom_id}, {"_id": 0, "chatroom_id": 0}))
    if not messages:
        raise HTTPException(status_code=404, detail="未找到聊天室")
    return {"data": {"messages": messages}, "status": "OK"}

@app.post("/send_message/")
async def send_message(request: Request):
    item = await request.json()
    print(request, "\n", item)
    list_of_keys = list(item.keys())

    if len(list_of_keys) != 4:
        data = {"status": "ERROR"}
        return JSONResponse(content=jsonable_encoder(data), status_code=400)
        
    if "name" not in item.keys() or len(item["name"]) > 20:
        data = {"status": "ERROR"}
        return JSONResponse(content=jsonable_encoder(data), status_code=400)  

    if "message" not in item.keys() or len(item["message"]) > 200:
        data = {"status": "ERROR"}
        return JSONResponse(content=jsonable_encoder(data), status_code=400) 
    
    chatroom = Chatrooms.find_one({"id": item["chatroom_id"]})
    if not chatroom:
        data = {"status": "ERROR"}
        return JSONResponse(content=jsonable_encoder(data), status_code=404)

    Messages.insert_one({
        "chatroom_id": item["chatroom_id"],
        "message": item["message"],
        "name": item["name"],
        "message_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "user_id": item["user_id"]
    })

    fcm_token = Tokens.find_one({"user_id": item["user_id"]}, {"_id": 0, "token": 1}).get("token")
    notification_title = item["chatroom_id"]
    notification_body = item["message"]
    result = fcm.notify(fcm_token=fcm_token, notification_title=notification_title, notification_body=notification_body)

    data = {"status": "OK"}
    return JSONResponse(content=jsonable_encoder(data))


@app.post("/submit_push_token/")
async def submit_push_token(request: Request):
    item = await request.json()
    print(request, "\n", item)

    existing_user = Tokens.find_one({"user_id": item["user_id"]}) 
    if existing_user:
        Tokens.update_one({"user_id": item["user_id"]}, {"$set": {"token": item["token"]}})
        data = {"status": "OK"}
        return JSONResponse(content=jsonable_encoder(data))
    else:
        Tokens.insert_one({
            "user_id": item["user_id"],
            "token": item["token"]
        })
        data = {"status": "OK"}
        return JSONResponse(content=jsonable_encoder(data))
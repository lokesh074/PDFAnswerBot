from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import shutil
import os
from queue import Queue
from langchain_community.vectorstores import FAISS
import datetime
import sys
from pydantic import BaseModel
import traceback
from chatbot import *
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class UserQuestion(BaseModel):
    question: str

word_queue = Queue()

async def generate_responses(query: str, vectorename: str):
    try:
        vectorstore = FAISS.load_local(f"vector/{vectorename}", embeddings, allow_dangerous_deserialization=True)
        docs = vectorstore.similarity_search(query, K=1)
        as_output = docs[0].page_content
        model = genai.GenerativeModel("gemini-pro")
        chat = model.start_chat(history=[])
        question = f"{as_output} \n--Please consider above text and give me an answer to the following question --\n{query}"
        response = chat.send_message(question, stream=True)
        for word in response:
            word_queue.put(word.text)
        # word_queue.put("job_done")
    except Exception as e:
        print("Error in generate_responses:", e)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

doc = {"file":''}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        allowed_extensions = {".pdf", ".docx"}
        ext = os.path.splitext(file.filename)[1]
        if ext.lower() in allowed_extensions:
            doc['file'] = file.filename
            if not os.path.exists(f"documents/{file.filename}"):
                print("Creating New file")
                with open(f"documents/{file.filename}", "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                docs = "documents/"+doc['file']
                if ext.lower() =='.pdf':
                    raw_text = get_pdf_text(docs)
                else:
                    raw_text = get_Docs_text(docs)
                text_chunks = get_text_chunks(raw_text)
                vectorstore = get_vectorstore(text_chunks,file.filename)
                print("Vector embedding is stored")
            return {"filename": file.filename, "saved_path": f"documents/{file.filename}","Status":"Successfully uploaded"}
        else:
            return {"Status":"Extension of file is not allowed"}
    except Exception as e:
        print("Error in upload api :",e)
        return {"Error: ","Sorry ! unable to get your document"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            docs = doc['file']
            await generate_responses(data.strip(), docs)
            while True:
                word = word_queue.get()
                if word == "job_done":
                    await websocket.send_text("job_done")
                    break
                else:
                    await websocket.send_text(word)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        errorString = "\r\nFunction Name: WebSocket endpoint ErrorDateTime:" + str(
            datetime.datetime.now()) + "\tError Code:" + str(sys.exc_info()[0]) + "\tError Description:" + str(
            traceback.format_exc()).replace('"', ' ') + "\r\n"
        print(errorString)
        print("Error", str(e))

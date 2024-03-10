from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import shutil,os
from chatbot import *
from fastapi import FastAPI, WebSocket, Request  # Add this line
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from queue import Queue
import datetime
import sys
import traceback

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates1")

class UserQuestion(BaseModel):
    question: str

doc = {"file":''}
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    doc = {"file":''}
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/reset-file/")
async def reset_file_value():
    try:
        doc['file'] = ''  # Reset the value of doc['file'] to an empty string
        return {"Status": "File value reset successfully"}
    except Exception as e:
        return {"Error": str(e)}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        allowed_extensions = {".pdf", ".docx"}
        allowed_img_extensions = {".png",".jpg",".jpeg"}
        ext = os.path.splitext(file.filename)[1]
        if ext.lower() in allowed_extensions:
            print("Pdf file uploading")
            doc['file'] = file.filename
            if not os.path.exists(f"documents/{file.filename}"):
                print("Creating New pdf file")
                with open(f"documents/{file.filename}", "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                docs = "documents/" + doc['file']
                if ext.lower() =='.pdf':
                   print("Pdf function calling")
                   raw_text = get_pdf_text(docs)
                else:
                    raw_text = get_Docs_text(docs)
                text_chunks = get_text_chunks(raw_text)
                vectorstore = get_vectorstore(text_chunks,file.filename)
                print("Vectore embedding is stored")
            return {"filename": file.filename, "saved_path": f"documents/{file.filename}","Status":"Successfully uploaded"}
        elif ext.lower() in allowed_img_extensions:
            doc['file'] = file.filename
            with open(os.path.join("documents", file.filename), "wb") as buffer:
                buffer.write(await file.read())
            print("saving New image file")
            return {"filename": file.filename, "saved_path": f"documents/{file.filename}","Status":"Successfully uploaded"}
        else:
            return {"Status":"Extension of file is not allowed"}
    except Exception as e:
        print("error in upload api :",e)
        return {"Status: ","Sorry ! unable to get your document"}

@app.post("/ask-question/")
async def ask_question(user_question: UserQuestion):
    try:
        allowed_img_extensions = {".png",".jpg",".jpeg"}
        ext = os.path.splitext(doc['file'])[1]
        if doc['file']:
            if ext.lower() not in allowed_img_extensions:
                # docs = "documents/"+doc['file']
                response = query_data(user_question.question,doc['file'])
                return {"Answer": response}
            else:
                print("a image found")
                response = query_image(user_question.question,doc['file'])
                return {"Answer": response}
        else:
            return {"Status": "Please Upload a file with extension .pdf or .docx OR upload a Image"}
    except Exception as e:
        print("Error in ask question api: ",str(e))
        return {"Status":"Sorry ! I am not able to generate answer for you query"}


  


import streamlit as st
# from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_community.embeddings import HuggingFaceEmbeddings
import streamlit as st
import os
import PIL
from docx import Document
import google.generativeai as genai
genai.configure(api_key='AIzaSyA-PRFGyZSt8K0p88FZ9foewDM4R9etuos')


embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')


def get_pdf_text(pdf_docs):
    text = ""
    # for pdf in pdf_docs:
    pdf_reader = PdfReader(pdf_docs)
    for page in pdf_reader.pages:
        text += page.extract_text()
    # print(text)
    return text

def get_Docs_text(docs): 
    # Load the .docx file
    doc = Document(docs)
    # Initialize an empty string to store the text
    text = ''
    # Iterate through each paragraph in the document and extract text
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'    
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n", #This parameter specifies the separator used to split the text. In this case, it's set to \n, which indicates a newline character. This means the text will be split whenever there's a newline in the input text
        chunk_size=1000,  #This parameter sets the maximum size of each chunk of text. Chunks larger than this size will be split further.
        chunk_overlap=100,#Certainly! Let's say you have a text with 1000 characters. If you split this text into chunks with a chunk_size of 2000 and a chunk_overlap of 200, here's what happens:
# The first chunk will contain characters from 1 to 1000.
# The second chunk will start at character 801 (1000 - 200 + 1) and end at character 2000.
# Since the overlap is 200 characters, the last 200 characters of the first chunk will be repeated in the beginning of the second chunk.
# So, the second chunk will contain characters from 801 to 2000, but characters 801 to 1000 will be repeated from the end of the first chunk. This ensures that no information is lost between chunks and allows for better context preservation when processing the text in chunks.
        length_function=len)
    chunks = text_splitter.split_text(text)
    # print(chunks)
    return chunks


def get_vectorstore(text_chunks,filename):
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    # vectorstore = FAISS.from_documents(text_chunks, embeddings)
    vectorstore.save_local(f"vector/{filename}")
    # print(vectorstore)
    return vectorstore


# def get_conversation_chain(vectorstore):
#     llm = genai.GenerativeModel("gemini-pro") 
#     # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})

#     memory = ConversationBufferMemory(
#         memory_key='chat_history', return_messages=True)
#     conversation_chain = ConversationalRetrievalChain.from_llm(
#         llm=llm,
#         retriever=vectorstore.as_retriever(),
#         memory=memory
#     )
#     return conversation_chain

def query_data(query,vectorename):  
    vectorstore = FAISS.load_local(f"vector/{vectorename}", embeddings,allow_dangerous_deserialization=True)
    docs = vectorstore.similarity_search(query) ##K =1 return 1 most text
    # docs = vectorstore.similarity_search_with_score(query, K=1)
    ##similarity_search_with_score
    as_output = docs[0].page_content
    model=genai.GenerativeModel("gemini-pro") 
    chat = model.start_chat(history=[])
    print("previous chat:",chat.history)
    question = f"your task is to generate answer according to question from given text\n--{as_output} \n--Please consider above text and give me answer of following question --\n{query}"
    print("Question:: ",question)
    # response=chat.send_message(question,stream=True)
    response=chat.send_message(question)
    print(response.text)
    return response.text


def query_image(query,image):
    print("Content generating from image ")
    img = PIL.Image.open(f"documents/{image}")
    model = genai.GenerativeModel('gemini-pro-vision')
    response = model.generate_content([f"{query}", img])
    print(response.text)
    return response.text

                
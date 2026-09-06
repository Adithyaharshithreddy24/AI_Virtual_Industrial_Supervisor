from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from Utils.Voice_Processor import process_input
from Utils.transcriber import transcribe_all


app = FastAPI(title="AI Virtual Supervisor API")

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "AI Virtual Supervisor API is running"
    }

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):

    chunks = process_input(file)

    transcript = transcribe_all(chunks)

    return {
        "data": transcript  
    }
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from Models.Voice_Call_Model import CallRequest
from fastapi.responses import Response
from xml.sax.saxutils import escape

from Utils.Transcriber import transcribe_all
from Utils.Voice_Calls import make_call
from Utils.Voice_Processor import process_input

app = FastAPI(title="AI Virtual Supervisor API")

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
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

@app.post("/call")
def call_technician(request: CallRequest):

    result = make_call(
        message=request.message,
        to_phone_number=request.to_phone_number
    )

    return result

@app.post("/twiml")
def twiml(message: str):
    safe_message = escape(message)

    twiml_response = f"""
    <Response>
        <Say>{safe_message}</Say>
    </Response>
    """

    return Response(
        content=twiml_response,
        media_type="application/xml"
    )
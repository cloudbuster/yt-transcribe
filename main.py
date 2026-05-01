import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transcription import transcribe_audio_video
from youtube import check_youtube_transcript

app = FastAPI()

class TranscriptionRequest(BaseModel):
    url: str

@app.post("/transcribe")
def transcribe(request: TranscriptionRequest):
    try:
        transcription = transcribe_audio_video(request.url)
        return {"transcription": transcription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/youtube/transcript")
def youtube_transcript(url: str):
    try:
        has_transcript = check_youtube_transcript(url)
        return {"has_transcript": has_transcript}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

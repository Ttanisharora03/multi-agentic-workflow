import os
import httpx
import structlog

logger = structlog.get_logger(__name__)

async def transcribe_audio(file_path: str) -> str:
    """
    Transcribe an audio file using Groq's whisper-large-v3 model.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set")

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f)
            }
            data = {
                "model": "whisper-large-v3",
                "response_format": "json"
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, files=files, data=data)
                
                if response.status_code != 200:
                    logger.error("audio_transcription_failed", status_code=response.status_code, text=response.text)
                    raise Exception(f"Failed to transcribe audio: {response.text}")
                
                result = response.json()
                return result.get("text", "")
    except Exception as e:
        logger.error("audio_transcription_error", error=str(e))
        raise

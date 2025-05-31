from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import os
import json
from typing import List, Dict
import PyPDF2
import logging

app = FastAPI()
# Sử dụng OLLAMA_URL từ môi trường hoặc fallback về localhost
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_cv_content() -> str:
    cv_path = "template/static/cv/VuongNguyenTrung_Tester_QC_CV.pdf"
    if not os.path.exists(cv_path):
        return ""

    try:
        with open(cv_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return ""

# Initialize message history
messages_history: List[Dict[str, str]] = []

# Get CV content for personalized context
cv_content = get_cv_content()

# System prompt to give context to the AI
SYSTEM_PROMPT = f"""
- Sử dụng tiếng Việt là chủ yếu, nếu nhà tuyển dụng dùng tiếng Anh thì mởi thay đổi.
- Chỉ trả lời theo câu hỏi của nhà tuyển dụng, không trả lời câu hỏi khác.
- Trả lời lễ phép, lịch sự và chuyên nghiệp.
- Không sử dụng từ ngữ thô tục, không lịch sự.
- Không nói về các vấn đề chính trị, tôn giáo, hay các vấn đề nhạy cảm khác.
- Chỉ tập trung vào công việc và kỹ năng.
- Hãy xưng hô với nhà Tuyển dụng là "Anh/Chị" hoặc cách khác khi trả lời.

Lưu ý quan trọng:
- Hãy suy luận từng bước, kiểm tra kỹ lưỡng, và đưa ra câu trả lời chính xác nhất.

Thông tin về bạn:
Bạn là Vương Nguyên Trung, một Software Tester (Manual) với gần hai năm kinh nghiệm. Bạn nên hành động như tôi khi nói chuyện với các nhà tuyển dụng.

Here's your background and experience:
{cv_content}"""

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chunn241529.github.io",  # GitHub Pages domain
        "https://chunn241529.github.io/portfolio",  # GitHub Pages project domain
        "http://localhost:5500",  # Local development
        "http://127.0.0.1:5500"   # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint to download CV
@app.get("/download-cv")
async def download_cv():
    cv_path = "template/static/cv/VuongNguyenTrung_Tester_QC_CV.pdf"
    if not os.path.exists(cv_path):
        raise HTTPException(status_code=404, detail="CV file not found")
    return FileResponse(cv_path, media_type="application/pdf", filename="VuongNguyenTrung_CV.pdf")

# Endpoint for chat with Ollama
@app.post("/chat")
async def chat_with_ollama(data: dict):
    message = data.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    logger.debug(f"Received message: {message}")

    # Add user message to history
    messages_history.append({"role": "user", "content": message})

    # Construct the full conversation context
    conversation = f"{SYSTEM_PROMPT}\n\nConversation history:\n"
    for msg in messages_history[-5:]:
        conversation += f"{msg['role']}: {msg['content']}\n"

    logger.debug(f"Sending prompt to Ollama")

    async def stream_response():
        async with aiohttp.ClientSession() as session:
            try:
                logger.debug(f"Making request to Ollama at {OLLAMA_URL}")
                async with session.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": "gemma3:12b-it-qat",
                        "prompt": conversation,
                        "stream": True,
                        "options": {
                            "temperature": 0.4,
                            "max_tokens": -1
                        }
                    }
                ) as response:
                    logger.debug(f"Ollama response status: {response.status}")
                    async for line in response.content:
                        if line:
                            try:
                                json_response = json.loads(line.decode('utf-8'))
                                if 'response' in json_response:
                                    logger.debug(f"Received chunk: {json_response['response'][:50]}...")
                                    yield json_response['response'].encode('utf-8')
                            except json.JSONDecodeError as je:
                                logger.error(f"JSON decode error: {str(je)}")
                                yield f"Error decoding JSON: {str(je)}".encode()
            except Exception as e:
                logger.error(f"Error in stream_response: {str(e)}")
                yield f"Error: {str(e)}".encode()

    return StreamingResponse(stream_response(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import os
import json
from typing import List, Dict
import PyPDF2

app = FastAPI()

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
- Chỉ trả lời theo câu hỏi của nhà Tuyển dụng. Không trả lời dư thừa.

Thông tin về bạn:
You are Vuong Nguyen Trung, a Software Tester (Manual) with nearly two years of experience. You should act as me when talking to recruiters. Here's your background and experience:

Education:
- Graduated from FPT Polytechnic College (09/2020 - 12/2022) in Software Application
- GPA: 3.3/4.0
- Was President of the Tester Club at the university

Work Experience:
- Software Quality Control | Business Analyst at Sunshine Software Solution Co., Ltd (09/2022 - 07/2024)
- Led quality control in 10 projects and supported testing in multiple others
- Analyzed requirements, created test plans, wrote test cases, executed tests
- Collaborated with teams and tested APIs using Postman
- Assisted customers in setting up test environments and handled feedback/bug tracking
- Acted as Business Analyst, creating wireframes and gathering requirements

Skills:
- Testing: Test planning, test case development, API testing with Postman
- Programming: HTML/CSS, JavaScript, SQL, Java, Python
- Platforms: Spring Boot, Git, SQL Server, MySQL
- Analysis: Requirements gathering, stakeholder interviews, documentation
- Project Management: Waterfall, Scrum, Agile methodologies

When responding to recruiters:
1. Be professional and confident but humble
2. Draw from your actual experience at Sunshine Software Solution
3. Provide specific examples from your projects when relevant
4. Focus on your strengths in manual testing and business analysis
5. Show enthusiasm for learning and growth
6. Be honest about your experience level

Location: District 12, HCMC
Contact: 0358570211 | trungvn.tester@gmail.com

Note: Always maintain a professional tone and focus on your testing and QA expertise."""

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],  # Add your frontend URL
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

    # Add user message to history
    messages_history.append({"role": "user", "content": message})

    # Construct the full conversation context
    conversation = f"{SYSTEM_PROMPT}\n\nConversation history:\n"
    for msg in messages_history[-5:]:  # Only include last 5 messages for context
        conversation += f"{msg['role']}: {msg['content']}\n"

    async def stream_response():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "gemma3:4b-it-qat",
                        "prompt": conversation,
                        "stream": True,
                        "options": {
                            "temperature": 0.7,
                            "max_tokens": -1
                        }
                    }
                ) as response:
                    async for line in response.content:
                        if line:
                            try:
                                json_response = json.loads(line.decode('utf-8'))
                                if 'response' in json_response:
                                    yield json_response['response'].encode('utf-8')
                            except json.JSONDecodeError as je:
                                yield f"Error decoding JSON: {str(je)}".encode()
            except Exception as e:
                yield f"Error: {str(e)}".encode()

    return StreamingResponse(stream_response(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"before": "", "after": ""}
    )

@app.post("/convert", response_class=HTMLResponse)
async def convert(request: Request, statement: str = Form(...)):
    prompt = f"""
반드시 한국어로만 답변하세요. 다른 언어는 절대 사용하지 마세요.

당신은 법률 문서 작성 전문가입니다.
아래 피해자의 감정적인 진술을 육하원칙(누가, 언제, 어디서, 무엇을, 어떻게, 왜) 기반의
객관적이고 법적으로 유효한 문체로 변환해주세요.

규칙:
- 감정적 표현 제거
- 육하원칙 기반으로 구조화
- 객관적 사실만 서술
- 법률 문서 형식으로 작성

피해자 진술:
{statement}

법률 문체로 변환:
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    after = response.choices[0].message.content

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"before": statement, "after": after}
    )
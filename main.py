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
You must respond in Korean only. Do not use any other language including Japanese, Chinese characters, or English.

당신은 한국 법률 문서 전문가입니다.
아래 피해자의 진술을 읽고, 진술에 포함된 실제 내용을 바탕으로 법률 문체로 변환하세요.

절대 규칙:
- 오직 한국어(한글)만 사용. 한자, 일본어, 영어 절대 금지
- 한글 자모(가-힣) 이외의 문자는 숫자와 punctuation(. , ! ? 등)을 제외하고 절대 사용 금지
- 진술에 없는 내용을 (미상)으로 채우지 말 것
- 진술에 있는 내용만 사용해서 작성할 것
- 육하원칙 중 진술에 있는 항목만 포함할 것
- 감정적 표현을 객관적 사실로 변환할 것
- 법률 문서 형식으로 작성할 것

피해자 진술:
{statement}

위 진술을 한국어 법률 문체로 변환:
"""
    response = client.chat.completions.create(
        model="gemma2-9b-it",
        messages=[{"role": "user", "content": prompt}]
    )
    after = response.choices[0].message.content

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"before": statement, "after": after}
    )
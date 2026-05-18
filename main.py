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
        context={"before": "", "after": "", "error": ""}
    )

@app.post("/convert", response_class=HTMLResponse)
async def convert(request: Request, statement: str = Form(...)):

    # 1. 길이 검증
    if len(statement.strip()) < 20:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "before": statement,
                "after": "",
                "error": "진술 내용이 너무 짧습니다. 구체적인 피해 상황을 20자 이상 입력해주세요."
            }
        )

    # 2. AI로 피해 진술 여부 검증
    check_prompt = f"""
아래 텍스트가 피해 사실을 설명하는 진술인지 판단하세요.
피해 진술이면 "YES", 아니면 "NO"만 답하세요. 다른 말은 절대 하지 마세요.

텍스트: {statement}
"""
    check_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": check_prompt}],
        max_tokens=5
    )
    is_valid = check_response.choices[0].message.content.strip().upper()

    if "NO" in is_valid:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "before": statement,
                "after": "",
                "error": "피해 사실과 관련된 내용을 입력해주세요. 언제, 어디서, 누가, 어떤 행동을 했는지 구체적으로 작성해주세요."
            }
        )

    # 3. 정상 변환
    prompt = f"""
You must respond in Korean (Hangul) ONLY. 
Using any other language (Japanese, Chinese characters, Russian, English, etc.) is strictly forbidden.

당신은 한국 법률 문서 전문가입니다.
아래 피해자의 진술을 읽고, 진술에 포함된 실제 내용을 바탕으로 법률 문체로 변환하세요.

[언어 규칙 - 절대 위반 금지]
- 한국어(한글)만 사용
- 한자 절대 금지 (예: 不, 愉, 快 등)
- 일본어 절대 금지
- 러시아어 절대 금지
- 영어 절대 금지
- 허용 문자: 한글, 숫자, 문장부호(. , ? ! 등)만 허용

[작성 규칙]
- 진술에 있는 내용만 사용
- 진술에 없는 내용 추가 금지
- (미상) 표현 사용 금지
- 감정적 표현을 객관적 사실로 변환
- 육하원칙 중 진술에 있는 항목만 포함
- 법률 문서 형식으로 작성

피해자 진술:
{statement}

위 진술을 한국어 법률 문체로 변환 (한글만 사용):
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    after = response.choices[0].message.content

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"before": statement, "after": after, "error": ""}
    )
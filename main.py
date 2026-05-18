from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from groq import Groq
from dotenv import load_dotenv
import os
import re

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
절대 규칙: 한자(CJK 통합 한자 포함)는 단 한 글자도 사용 금지.
You must respond in Korean Hangul only. CJK characters are strictly forbidden.

당신은 한국 법률 문서 전문가입니다.
반드시 아래 형식 그대로만 출력하세요. 형식 외 내용 절대 금지.

■ 육하원칙 정리
- 누가:
- 언제:
- 어디서:
- 무엇을:
- 어떻게:
- 왜:

■ 사건 개요

■ 행위 내용

■ 피해 결과

위 4개 항목만 출력. 다른 문장, 머리말, 맺음말 절대 금지.

[작성 규칙]
- 한글, 숫자, 문장부호만 사용
- 한자 절대 금지
- 진술에 없는 내용은 "확인되지 않음"으로 표기
- 감정적 표현 제거
- 객관적 사실만 서술

피해자 진술:
{statement}

위 형식대로 한국어로만 작성:
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    # 4. 한글 외 문자 제거 (한자 유니코드 범위 포함)
    after = response.choices[0].message.content
    after = re.sub(r'[^\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F0-9\s\.\,\!\?\:\;\-\(\)\"\'\n■]', '', after)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"before": statement, "after": after, "error": ""}
    )
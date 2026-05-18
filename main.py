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

당신은 대한민국 법원에 제출하는 진술서를 작성하는 법률 전문가입니다.
반드시 아래 형식 그대로만 출력하세요. 형식 외 내용 절대 금지.

■ 육하원칙 정리
- 누가: (행위자 명칭)
- 언제: (구체적 일시)
- 어디서: (구체적 장소)
- 무엇을: (피해 대상 또는 행위 객체)
- 어떻게: (구체적 행위 방법)
- 왜: (행위 목적 또는 동기)

■ 사건 개요
(법원 제출용 객관적 문체로 사건 전체 흐름을 2-3문장으로 요약. "~하였습니다", "~된 바 있습니다" 등 법률 문체 사용)

■ 행위 내용
(가해자의 구체적 행위를 법률 문체로 서술. "피해자에게 ~을 행하였음", "~를 통해 ~을 가하였음" 형식)

■ 피해 결과
(피해자가 입은 신체적, 정신적, 재산적 피해를 법률 문체로 서술. "피해자는 ~한 피해를 입었음" 형식)

[작성 규칙]
- 한글, 숫자, 문장부호만 사용
- 한자 절대 금지
- 진술에 없는 내용은 "확인되지 않음"으로 표기
- 감정적 표현 완전 제거
- 법원 제출 가능한 객관적 문체로만 작성

피해자 진술:
{statement}

위 형식대로 한국어 법률 문체로만 작성:
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
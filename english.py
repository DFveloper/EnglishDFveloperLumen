import re
import json
import random
import ssl
import base64
import urllib.request
import urllib.parse
from difflib import SequenceMatcher
import streamlit as st
import streamlit.components.v1 as components

# SSL 인증서 검증 우회
ssl._create_default_https_context = ssl._create_unverified_context

# ---------------------------------------------------------
# 1. 페이지 설정 및 디자인(CSS)
# ---------------------------------------------------------
st.set_page_config(page_title="영어 지문 분석기 (Aikar AI 완벽판)", layout="wide")

CUSTOM_CSS = """
<style>
:root {
    --ui-bg: #f6f8fb;
    --ui-surface: #ffffff;
    --ui-ink: #1d1d1f;
    --ui-muted: #788292;
    --ui-blue: #007aff;
    --ui-border: #e5eaf1;
    --ui-radius: 18px;
}

/* 전체 화면 */
.stApp {
    background:
        radial-gradient(
            ellipse at 85% 4%,
            rgba(140, 190, 255, 0.19),
            transparent 42%
        ),
        linear-gradient(180deg, #fafbfd, #f5f7fa);
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1140px;
    padding-top: 2.4rem;
    padding-bottom: 5rem;
}

/* Typography */
html, body, [class*="st-"] {
    font-family: -apple-system, BlinkMacSystemFont,
        "SF Pro Display", "Pretendard",
        "Noto Sans KR", "Segoe UI", sans-serif;
}

h1, h2, h3 {
    letter-spacing: -0.035em;
    color: var(--ui-ink);
}

h3 {
    font-weight: 680 !important;
}

hr {
    border-color: var(--ui-border) !important;
    margin: 1.5rem 0 !important;
}

/* 상단 Hero */
.app-hero {
    padding: 12px 0 30px;
}

.app-eyebrow {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 11px;
    letter-spacing: 0.13em;
    font-weight: 750;
    color: #6b7991;
    margin-bottom: 13px;
}

.app-eyebrow::before {
    content: "";
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #007aff;
    box-shadow: 0 0 0 4px rgba(0,122,255,.10);
}

.app-hero h1 {
    font-size: clamp(32px, 4.2vw, 49px);
    font-weight: 760;
    letter-spacing: -0.055em;
    line-height: 1.15;
    margin: 0 0 13px;
    color: #1d1d1f;
}

.app-hero h1 span {
    color: var(--ui-blue);
}

.app-hero p {
    font-size: 15px;
    line-height: 1.8;
    color: #778294;
    margin: 0;
}

/* 입력 영역: Solid Surface */
[data-testid="stTextArea"] [data-baseweb="textarea"],
[data-testid="stTextInput"] [data-baseweb="input"] {
    border: 1px solid var(--ui-border) !important;
    border-radius: 16px !important;
    background: #ffffff !important;
    box-shadow: 0 4px 16px rgba(30, 49, 80, .035);
    transition: border-color .2s, box-shadow .2s;
}

[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input {
    background: transparent !important;
    color: var(--ui-ink) !important;
    font-size: 14px;
    line-height: 1.75;
}

[data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within,
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
    border-color: rgba(0,122,255,.55) !important;
    box-shadow: 0 0 0 4px rgba(0,122,255,.085);
}

/* 업로드 */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(255,255,255,.82);
    border: 1px dashed #cbd6e5;
    border-radius: 16px;
    padding: 12px;
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    min-height: 46px;
    border-radius: 14px !important;
    background: #ffffff;
    color: #273447;
    border: 1px solid #e0e7f0;
    box-shadow: 0 2px 8px rgba(25,45,75,.035);
    font-size: 14px;
    font-weight: 650;
    transition: all .18s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
    border-color: #a6cafa;
    box-shadow: 0 5px 16px rgba(25,45,75,.08);
}

/* Primary 버튼 */
.stButton button[data-testid="stBaseButton-primary"] {
    background: #007aff !important;
    color: #ffffff !important;
    border: 1px solid #007aff !important;
    box-shadow: 0 4px 12px rgba(0,122,255,.16);
}

.stButton button[data-testid="stBaseButton-primary"]:hover {
    background: #006de5 !important;
    color: #ffffff !important;
}

/* 구문 토큰 */
.circle-word {
    display: inline-block;
    padding: 4px 10px;
    margin: 3px 2px;
    font-size: 15px;
    font-weight: 570;
    color: #285b9f;
    background: #f2f7ff;
    border: 1px solid #dce9fb;
    border-radius: 11px;
}

.slash {
    color: #9eacc0;
    font-size: 17px;
    font-weight: 600;
    margin: 0 6px;
}

/* 구문 분석 카드: Solid */
.sentence-container {
    background: #ffffff;
    border: 1px solid var(--ui-border);
    border-radius: 18px;
    padding: 20px 22px;
    margin-bottom: 12px;
    line-height: 2.5;
    box-shadow: 0 4px 18px rgba(30,49,80,.035);
}

/* 문제 카드: Solid */
.question-box {
    background: #ffffff;
    border: 1px solid var(--ui-border);
    border-radius: 18px;
    padding: 22px 24px;
    margin: 16px 0;
    line-height: 1.95;
    color: #293241;
    box-shadow: 0 4px 18px rgba(30,49,80,.035);
}

/* 핵심 요약: Solid */
.summary-box {
    background: #f0f6ff;
    border: 1px solid #deebff;
    border-left: 3px solid #007aff;
    border-radius: 16px;
    padding: 22px 24px;
    line-height: 1.95;
    color: #25354d;
    margin-bottom: 24px;
}

/* Liquid Glass: 점수 및 진행 현황 */
.score-box {
    position: relative;
    overflow: hidden;
    isolation: isolate;
    padding: 24px 28px;
    margin: 20px 0 24px;
    border-radius: 22px;

    background: linear-gradient(
        135deg,
        rgba(255,255,255,.82),
        rgba(236,245,255,.47)
    );

    border: 1px solid rgba(255,255,255,.94);

    -webkit-backdrop-filter: blur(20px) saturate(165%);
    backdrop-filter: blur(20px) saturate(165%);

    box-shadow:
        0 12px 36px rgba(48,85,140,.09),
        inset 0 1px 0 rgba(255,255,255,.95);

    color: #253447;
    text-align: center;
    font-size: 17px;
    font-weight: 630;
    line-height: 1.9;
}

/* 유리 표면의 미세한 반사광 */
.score-box::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: linear-gradient(
        125deg,
        rgba(255,255,255,.48),
        transparent 48%
    );
    pointer-events: none;
}

.score-box span[style] {
    color: #007aff !important;
    font-weight: 760;
}

/* 유리 효과 미지원 브라우저 */
@supports not (backdrop-filter: blur(1px)) {
    .score-box {
        background: #f0f6ff;
    }
}

/* 문법 오류 */
.grammar-error {
    background: #fff0f1 !important;
    border: 1px solid #ffb6bd !important;
    color: #d93648 !important;
}

.grammar-error u {
    text-decoration-color: #e33e50;
    text-decoration-thickness: 2px;
    text-underline-offset: 3px;
    font-weight: 700;
}

/* Expander */
[data-testid="stExpander"] {
    background: rgba(255,255,255,.88);
    border: 1px solid var(--ui-border);
    border-radius: 16px !important;
    overflow: hidden;
}

/* 단어장 테이블 */
[data-testid="stMarkdownContainer"] table {
    width: 100%;
    background: #ffffff;
    border: 1px solid var(--ui-border);
    border-radius: 16px;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    overflow: hidden;
}

[data-testid="stMarkdownContainer"] table th {
    background: #f5f8fd;
    font-weight: 680;
    color: #34425a;
}

[data-testid="stMarkdownContainer"] table th,
[data-testid="stMarkdownContainer"] table td {
    padding: 13px 15px !important;
    border-bottom: 1px solid #edf0f5 !important;
    font-size: 14px;
}

[data-testid="stMarkdownContainer"] table tr:last-child td {
    border-bottom: 0 !important;
}

/* 모바일 */
@media (max-width: 640px) {
    .block-container {
        padding: 1.3rem 1rem 3rem;
    }

    .app-hero {
        padding-bottom: 20px;
    }

    .score-box {
        padding: 18px 15px;
        font-size: 14px;
        border-radius: 18px;
    }

    .sentence-container,
    .question-box,
    .summary-box {
        padding: 16px;
        border-radius: 15px;
    }

    .circle-word {
        font-size: 14px;
    }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 세션 상태 관리
# ---------------------------------------------------------
if "sentences" not in st.session_state: st.session_state.sentences = []
if "translations" not in st.session_state: st.session_state.translations = []
if "mode" not in st.session_state: st.session_state.mode = None
if "generated_questions" not in st.session_state: st.session_state.generated_questions = []
if "summary_data" not in st.session_state: st.session_state.summary_data = None
if "eng_input_area" not in st.session_state: st.session_state.eng_input_area = ""

STOPWORDS = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "from", "up", "down", "out", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", "will", "just", "should", "now", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "this", "that", "these", "those", "it", "its", "they", "them", "their", "he", "him", "his", "she", "her", "we", "us", "our", "you", "your"}

# ---------------------------------------------------------
# 3. AI 연동 및 Fallback 파이프라인
# ---------------------------------------------------------
AIKAR_API_URL = "https://chat.aeonthic.com/aikar-engine/v1/chat/completions"
OLLAMA_API_URL = "http://localhost:11434/v1/chat/completions"

def call_aikar_ai(prompt, system_prompt, timeout=45):
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    payload = {"model": "aikar-engine", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], "max_tokens": 2000}
    try:
        req = urllib.request.Request(AIKAR_API_URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "choices" in res and len(res["choices"]) > 0: return res["choices"][0]["message"]["content"]
    except Exception: pass
    return None

def call_ollama_ai(prompt, system_prompt, timeout=20):
    headers = {"Content-Type": "application/json"}
    payload = {"model": "llama3.2", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], "temperature": 0.3}
    try:
        req = urllib.request.Request(OLLAMA_API_URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "choices" in res and len(res["choices"]) > 0: return res["choices"][0]["message"]["content"]
    except Exception: pass
    return None

def call_ai_with_fallback(prompt, system_prompt):
    res = call_aikar_ai(prompt, system_prompt, timeout=5)
    if res: return res
    
    res_ollama = call_ollama_ai(prompt, system_prompt, timeout=20)
    if res_ollama:
        st.toast("🌐 외부 AI 미응답으로 인해 [로컬 Ollama AI]로 자동 전환되었습니다.", icon="💻")
        return res_ollama
        
    st.toast("⚠️ AI 미연결 상태입니다. 오프라인 내장 알고리즘으로 전환합니다.", icon="🔌")
    return None

def extract_text_from_image_via_ai(image_file):
    try:
        b64_image = base64.b64encode(image_file.read()).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{b64_image}"
        headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        payload = {
            "model": "aikar-engine",
            "messages": [
                {"role": "system", "content": "Extract all English text accurately. Return ONLY the text."},
                {"role": "user", "content": [{"type": "text", "text": "Extract text."}, {"type": "image_url", "image_url": {"url": data_url}}]}
            ], "max_tokens": 1500
        }
        req = urllib.request.Request(AIKAR_API_URL, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "choices" in res and len(res["choices"]) > 0:
                return re.sub(r'^```[a-zA-Z]*\s*|```\$', '', res["choices"][0]["message"]["content"].strip(), flags=re.MULTILINE).strip(), None
    except Exception: return None, "AI 이미지 서버에 연결할 수 없습니다. 텍스트를 직접 입력해 주세요."
    return None, "텍스트를 추출하지 못했습니다."

# ---------------------------------------------------------
# 4. 분석, 번역, 요약, 문법 로직
# ---------------------------------------------------------
def split_into_sentences(text):
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) == 1:
        return [s.strip() for s in re.split(r'(?<=[.!?])\s+', lines[0]) if s.strip()]
    return lines

def process_inputs(eng_text, kor_text):
    eng_sentences = split_into_sentences(eng_text)
    kor_sentences = split_into_sentences(kor_text) if kor_text.strip() else []
    
    if not kor_sentences and eng_sentences:
        prompt = f"다음 영어 문장을 한국어로 자연스럽게 번역해 JSON 배열 형태로만 응답해.\n{json.dumps(eng_sentences, ensure_ascii=False)}"
        res = call_ai_with_fallback(prompt, "Return ONLY a JSON array of strings.")
        if res:
            try: kor_sentences = [str(i).strip() for i in json.loads(re.sub(r'^```json\s*|```\$', '', res.strip(), flags=re.MULTILINE))]
            except: kor_sentences = [re.sub(r'^(?:\d+[\.\)]|[-•*])\s*', '', l.strip()) for l in res.splitlines() if l.strip() and not l.startswith("```")]

    translations = [kor_sentences[i] if i < len(kor_sentences) else "(오프라인 상태: 한국어 해석을 직접 입력해 주세요)" for i in range(len(eng_sentences))]
    return eng_sentences, translations

def generate_offline_vocab_and_summary(sentences):
    full_text = " ".join(sentences)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', full_text.lower())
    
    freq = {}
    for w in words:
        if w not in STOPWORDS: freq[w] = freq.get(w, 0) + 1
            
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
    vocab_list = []
    
    for word, count in sorted_words:
        context_sent = next((s for s in sentences if word in s.lower()), "지문 내 수록 어휘")
        vocab_list.append({
            "word": word.capitalize(),
            "meaning": "사전/문맥 직접 확인 필요 (오프라인 모드)",
            "context": f"지문 내 {count}회 등장: '{context_sent[:50]}...'"
        })
        
    topic = f"주요 어휘: {', '.join([w[0].capitalize() for w in sorted_words[:3]])}"
    main_idea = f"이 지문은 총 {len(sentences)}개 문장으로 구성된 내용입니다."
    return {"topic": topic, "main_idea": main_idea, "vocab": vocab_list}

def generate_summary_and_vocab(sentences):
    full_text = " ".join(sentences)
    prompt = f"""다음 지문을 분석해서 JSON 형식으로 출력해줘.
    지문: 
    ```text
    {full_text}
    ```
    출력 형식: \{"topic": "핵심주제 1문장", "main_idea": "지문요지 1~2문장", "vocab": [\{"word": "영어단어", "meaning": "한국어 뜻", "context": "문맥상 쓰임"\}]\}
    """
    res = call_ai_with_fallback(prompt, "You are a reading comprehension expert. Return ONLY valid JSON.")
    if res:
        try: return json.loads(re.sub(r'^```json\s*|```$', '', res.strip(), flags=re.MULTILINE))
        except: pass
        
    return generate_offline_vocab_and_summary(sentences)

def check_local_rules(sentence):
    rules = [(r'\b(this|that)\s+(are|were)\b', "'this/that' 뒤 단수 동사 필요", "is"), (r'\b(these|those)\s+(is|was)\b', "'these/those' 뒤 복수 동사 필요", "are")]
    return [(m.start(), m.end(), msg, [repl]) for pattern, msg, repl in rules for m in re.finditer(pattern, sentence, re.IGNORECASE)]

def format_sentence_html(sentence, error_spans):
    err_idxs = {i for s, e, _, _ in error_spans for i in range(s, e)}
    html = ""
    curr = 0
    for token in re.split(r'(\s+)', sentence):
        if not token.strip(): html += token; curr += len(token); continue
        is_err = any(i in err_idxs for i in range(curr, curr+len(token)))
        if re.match(r'(\b(?:in|on|at|to|for|with|by|about|because|although|when|where|which|who|that|and|but)\b)', token, re.I):
            html += " <span class='slash'>/</span> "
        html += f"<span class='circle-word grammar-error'><u>{token}</u></span>" if is_err else f"<span class='circle-word'>{token}</span>"
        curr += len(token)
    return html

def render_tts_button(sentence, height=42):
    safe_sent = json.dumps(sentence)
    tts_code = f"""
    <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <button onclick='window.speechSynthesis.cancel(); let msg = new SpeechSynthesisUtterance({safe_sent}); msg.lang="en-US"; window.speechSynthesis.speak(msg);' 
                style="background-color: #4e73df; color: white; border: none; padding: 5px 12px; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 13px;">
            🔊 문장 듣기
        </button>
    </div>
    """
    components.html(tts_code, height=height)

# ---------------------------------------------------------
# 5. 수능 5대 원형 문제 생성 (빈칸, 어법, 어휘, 순서, 삽입)
# ---------------------------------------------------------
def generate_offline_fallback_questions(sentences):
    full = " ".join(sentences)
    words = [w for w in set(re.findall(r'\b[a-zA-Z]{5,}\b', full)) if w.lower() not in STOPWORDS]
    w1 = words[0] if len(words)>0 else "meaning"
    w2 = words[1] if len(words)>1 else "context"
    
    s_part1 = sentences[0] if len(sentences)>0 else full
    s_part2 = sentences[1] if len(sentences)>1 else full
    s_part3 = sentences[2] if len(sentences)>2 else full

    return [
        {"type": "1. 빈칸 추론", "title": "다음 글의 빈칸에 들어갈 말로 가장 적절한 것은?", "content": full.replace(w1, "[ _______ ]", 1), "options": [f"① {w1}", f"② {w2}", "③ limitation", "④ contradiction", "⑤ illusion"], "answer": f"① {w1}", "explanation": "지문의 핵심 어휘를 빈칸에 대입하는 문제입니다."},
        {"type": "2. 어법 판단", "title": "다음 글의 밑줄 친 부분 중, 어법상 어색한 것은?", "content": f"<b>(A) {s_part1}</b><br><b>(B) {s_part2}</b>", "options": ["① (A)", "② (B)", "③ (C)", "④ (D)", "⑤ (E)"], "answer": "① (A)", "explanation": "문법적 오류를 판별하는 유형입니다."},
        {"type": "3. 어휘 적절성", "title": "다음 글의 밑줄 친 부분 중, 문맥상 낱말의 쓰임이 적절하지 않은 것은?", "content": full, "options": [f"① {w1}", f"② {w2}", "③ increase", "④ decrease", "⑤ maintain"], "answer": "③ increase", "explanation": "문맥 흐름에 부합하는 반의어 관계를 묻는 문제입니다."},
        {"type": "4. 순서 배열", "title": "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것은?", "content": f"<b>[제시문] {s_part1}</b><br><br>(A) {s_part2}<br>(B) {s_part3}", "options": ["① (A) - (C) - (B)", "② (B) - (A) - (C)", "③ (B) - (C) - (A)", "④ (C) - (A) - (B)", "⑤ (C) - (B) - (A)"], "answer": "② (B) - (A) - (C)", "explanation": "글의 논리적 선후 관계를 배열하는 문제입니다."},
        {"type": "5. 문장 삽입", "title": "글의 흐름으로 보아, 주어진 문장이 들어 가기에 가장 적절한 곳은?", "content": f"<b>[보기] {s_part1}</b><br><br>{full}", "options": ["① [1]", "② [2]", "③ [3]", "④ [4]", "⑤ [5]"], "answer": "① [1]", "explanation": "문맥상 지시어와 연결어를 고려해 위치를 찾습니다."}
    ]

def generate_5_exam_questions(sentences):
    full_passage = " ".join(sentences)
    
    prompt = f"""다음 지문을 바탕으로 수능 핵심 5개 유형 문제를 1문제씩 정확히 총 5문제 생성해줘.
    지문: "{full_passage}"

    반드시 다음 5가지 유형을 순서대로 생성해야 함:
    1. 빈칸 추론
    2. 어법 판단
    3. 어휘 적절성
    4. 순서 배열
    5. 문장 삽입

    출력 형식 (유효한 JSON 배열 5개):
    [
      {{"type": "1. 빈칸 추론", "title": "문제 발문", "content": "지문 내용(HTML태그 가능)", "options": ["①", "②", "③", "④", "⑤"], "answer": "정답선지(예: ①)", "explanation": "상세 해설"}},
      {{"type": "2. 어법 판단", "title": "문제 발문", "content": "내용", "options": ["①", "②", "③", "④", "⑤"], "answer": "정답", "explanation": "해설"}},
      {{"type": "3. 어휘 적절성", "title": "문제 발문", "content": "내용", "options": ["①", "②", "③", "④", "⑤"], "answer": "정답", "explanation": "해설"}},
      {{"type": "4. 순서 배열", "title": "문제 발문", "content": "내용", "options": ["①", "②", "③", "④", "⑤"], "answer": "정답", "explanation": "해설"}},
      {{"type": "5. 문장 삽입", "title": "문제 발문", "content": "내용", "options": ["①", "②", "③", "④", "⑤"], "answer": "정답", "explanation": "해설"}}
    ]"""
    
    res = call_ai_with_fallback(prompt, "You are a CSAT exam creator. Return ONLY valid JSON array with 5 distinct question types.")
    if res:
        try:
            parsed = json.loads(re.sub(r'^```json\s*|```$', '', res.strip(), flags=re.MULTILINE))
            if len(parsed) == 5: return parsed
        except: pass
        
    return generate_offline_fallback_questions(sentences)

def create_export_text(questions):
    text = "📝 영어 지문 생성 문제지 (수능 5개 핵심 유형)\n" + "="*40 + "\n\n"
    for i, q in enumerate(questions, 1):
        text += f"[Q{i}] {q['type']}\n{q['title']}\n\n{q['content'].replace('<b>','').replace('</b>','').replace('<i>','').replace('</i>','').replace('<br>','\n')}\n\n"
        for opt in q['options']: text += f"{opt}\n"
        text += "\n" + "-"*40 + "\n"
    text += "\n\n🎯 정답 및 해설\n" + "="*40 + "\n\n"
    for i, q in enumerate(questions, 1): text += f"[Q{i} 정답] {q['answer']}\n[해설] {q.get('explanation', '')}\n\n"
    return text


# ---------------------------------------------------------
# 6. UI 화면 구성
# ---------------------------------------------------------

st.markdown("""
<div class="app-hero">
    <div class="app-eyebrow">AIKAR · ENGLISH STUDIO</div>
    <h1>영어 지문 분석<span>.</span></h1>
    <p>
        구문 학습부터 핵심 어휘, 암기 테스트와
        수능형 문제 생성까지.<br>
        하나의 공간에서 더 간결하게 학습하세요.
    </p>
</div>
""", unsafe_allow_html=True)

# 이미지 업로드는 필요할 때만 펼치기
with st.expander("이미지에서 영어 지문 불러오기", expanded=False):
    uploaded_image = st.file_uploader(
        "지문 이미지 업로드 (온라인 전용)",
        type=["png", "jpg", "jpeg"]
    )

    if uploaded_image:
        with st.spinner("이미지 판독 중..."):
            txt, err = extract_text_from_image_via_ai(uploaded_image)
            if txt:
                st.session_state.eng_input_area = txt
                st.success("텍스트 추출 완료")
            else:
                st.error(err)

# 나란히 정렬된 입력창
col_input1, col_input2 = st.columns(2, gap="large")

with col_input1:
    st.markdown("### 01. 영어 지문")
    input_eng = st.text_area(
        "영어 원문",
        height=210,
        key="eng_input_area",
        placeholder="분석할 영어 지문을 입력하세요."
    )

with col_input2:
    st.markdown("### 02. 한국어 해석")
    input_kor = st.text_area(
        "한국어 해석 (선택 사항)",
        height=210,
        placeholder="비워두면 AI가 자동으로 번역합니다."
    )

st.divider()

col_b1, col_b2, col_b3, col_b4 = st.columns(4)
with col_b1:
    if st.button("구문 학습", use_container_width=True):
        if input_eng: st.session_state.sentences, st.session_state.translations = process_inputs(input_eng, input_kor); st.session_state.mode = "learn"
with col_b2:
    if st.button("단어장 & 요약", use_container_width=True):
        if input_eng:
            with st.spinner("지문 요약 및 단어장 생성 중..."):
                s, _ = process_inputs(input_eng, input_kor)
                st.session_state.summary_data = generate_summary_and_vocab(s)
                st.session_state.mode = "summary"
with col_b3:
    if st.button("암기 테스트", use_container_width=True):
        if input_eng: st.session_state.sentences, st.session_state.translations = process_inputs(input_eng, input_kor); st.session_state.mode = "memo"
with col_b4:
    if st.button("5개 유형 문제 생성", type="primary", use_container_width=True):
        if input_eng:
            with st.spinner("수능 5대 유형 문제 생성 중..."):
                s, t = process_inputs(input_eng, input_kor)
                st.session_state.sentences, st.session_state.translations = s, t
                st.session_state.generated_questions = generate_5_exam_questions(s)
                st.session_state.mode = "exam"

st.divider()

# ---------------------------------------------------------
# 7. 모드별 기능 실행
# ---------------------------------------------------------
if st.session_state.mode == "learn":
    st.subheader("📖 끊어 읽기 & 구문 학습 (TTS 음성 오디오 지원)")
    for idx, (sent, trans) in enumerate(zip(st.session_state.sentences, st.session_state.translations), 1):
        spans = check_local_rules(sent)
        fmt_eng = format_sentence_html(sent, spans)
        
        st.markdown(f"**[문장 #{idx}]**")
        st.markdown(f'<div class="sentence-container">{fmt_eng}</div>', unsafe_allow_html=True)
        render_tts_button(sent)
        with st.expander("🔍 한국어 해석 보기"): st.info(trans)

elif st.session_state.mode == "summary":
    st.subheader("📑 핵심 요약 & 필수 단어장")
    data = st.session_state.summary_data
    if data:
        st.markdown(f'<div class="summary-box"><b>📌 핵심 주제 (Topic):</b> {data.get("topic", "")}<br><br><b>💡 지문 요지 (Main Idea):</b> {data.get("main_idea", "")}</div>', unsafe_allow_html=True)
        st.markdown("### 🔠 핵심 필수 어휘")
        vocab_list = data.get("vocab", [])
        if vocab_list:
            v_html = "<table style='width:100%; text-align:left; border-collapse: collapse;'><tr><th style='border-bottom:2px solid #ccc; padding:8px;'>단어</th><th style='border-bottom:2px solid #ccc; padding:8px;'>뜻</th><th style='border-bottom:2px solid #ccc; padding:8px;'>문맥상 쓰임 / 정보</th></tr>"
            for v in vocab_list: v_html += f"<tr><td style='border-bottom:1px solid #eee; padding:8px;'><b>{v['word']}</b></td><td style='border-bottom:1px solid #eee; padding:8px;'>{v['meaning']}</td><td style='border-bottom:1px solid #eee; padding:8px; color:#555;'>{v.get('context','')}</td></tr>"
            v_html += "</table>"
            st.markdown(v_html, unsafe_allow_html=True)

elif st.session_state.mode == "memo":
    st.subheader("🧠 문장 해석 암기 테스트 (TTS 지원)")
    
    # [기능 1] 암기 테스트 실시간 점수판
    total_sents = len(st.session_state.sentences)
    answered_sents = 0
    total_score_sum = 0
    
    for idx, (sent, tgt) in enumerate(zip(st.session_state.sentences, st.session_state.translations), 1):
        ans = st.session_state.get(f"memo_{idx}", "")
        if ans:
            answered_sents += 1
            sim_score = round(SequenceMatcher(None, re.sub(r'[^\w\s]', '', ans).replace(" ",""), re.sub(r'[^\w\s]', '', tgt).replace(" ","")).ratio()*100, 1)
            total_score_sum += sim_score
            
    avg_score = round(total_score_sum / answered_sents, 1) if answered_sents > 0 else 0
    
    st.markdown(f"""
    <div class="score-box">
        📊 <b>암기 테스트 현황:</b> {answered_sents}/{total_sents} 문장 완료 | 
        🎯 <b>평균 해석 일치도: <span style="color:#e74a3b;">{avg_score}점</span></b>
    </div>
    """, unsafe_allow_html=True)
    st.write("---")

    for idx, (sent, tgt) in enumerate(zip(st.session_state.sentences, st.session_state.translations), 1):
        st.markdown(f"**Q{idx}. {sent}**")
        render_tts_button(sent, height=38)
        
        ans = st.text_input(f"Q{idx} 해석 작성:", key=f"memo_{idx}")
        if ans:
            score = round(SequenceMatcher(None, re.sub(r'[^\w\s]', '', ans).replace(" ",""), re.sub(r'[^\w\s]', '', tgt).replace(" ","")).ratio()*100, 1)
            if score >= 85: st.success(f"{score}점 (정답) 🎯")
            else: st.error(f"{score}점 (오답) 💡")
            with st.expander("정답 보기"): st.write(tgt)
        st.write("---")

elif st.session_state.mode == "exam":
    st.subheader("📝 실전 수능 유형 객관식 문제 (5대 핵심 유형)")
    
    questions = st.session_state.generated_questions
    if questions:
        total_questions = len(questions)
        answered_count = sum(1 for idx in range(1, total_questions + 1) if st.session_state.get(f"exam_{idx}") is not None)
        correct_count = sum(1 for idx, q in enumerate(questions, 1) if st.session_state.get(f"exam_{idx}") == q["answer"])
        score_percent = int((correct_count / total_questions) * 100)
        
        # [기능 2] 만점 달성 시 풍선 애니메이션 축하 연출
        if answered_count == total_questions and correct_count == total_questions:
            st.balloons()
            st.success("🎉 축하합니다! 모든 문제를 맞혀 100점 만점을 기록했습니다!")

        st.markdown(f"""
        <div class="score-box">
            📊 <b>시험 현황:</b> {answered_count}/{total_questions} 문제 완료 | 
            🎯 <b>현재 점수: <span style="color:#e74a3b;">{score_percent}점</span></b> ({correct_count}/{total_questions} 정답)
        </div>
        """, unsafe_allow_html=True)
        
        dl_text = create_export_text(questions)
        st.download_button("📥 문제지 및 해설 다운로드 (.txt)", data=dl_text, file_name="English_Exam.txt", mime="text/plain")
        st.write("---")
        
        for idx, q in enumerate(questions, 1):
            st.markdown(f"### Q{idx}. {q['type']}")
            st.markdown(f"**{q['title']}**")
            st.markdown(f'<div class="question-box">{q["content"]}</div>', unsafe_allow_html=True)
            
            choice = st.radio("정답 선택:", q["options"], key=f"exam_{idx}", index=None)
            if choice:
                if choice == q["answer"]:
                    st.success("🎯 정답입니다! (+20점)")
                else:
                    st.error(f"❌ 오답입니다. (선택한 답: {choice})")
                with st.expander("🔍 정답 및 상세 해설 보기"):
                    st.write(f"**정답:** {q['answer']}\n\n**해설:** {q.get('explanation', '')}")
            st.write("---")

import re
import json
import random
import ssl
import base64
import urllib.request
import urllib.parse
from difflib import SequenceMatcher
import streamlit as st

# SSL 인증서 검증 우회 (API 다운로드/통신 오류 방지)
ssl._create_default_https_context = ssl._create_unverified_context

# ---------------------------------------------------------
# 1. 페이지 설정 및 디자인(CSS)
# ---------------------------------------------------------
st.set_page_config(page_title="영어 지문 분석기 (Aikar AI)", layout="wide")

CUSTOM_CSS = """
<style>
.circle-word {
    border: 1.5px solid #4e73df;
    border-radius: 12px;
    padding: 3px 9px;
    margin: 3px 2px;
    display: inline-block;
    background-color: #ffffff;
    font-size: 16px;
    color: #2e59d9;
    font-weight: 600;
}
.slash {
    color: #e74a3b;
    font-weight: bold;
    font-size: 20px;
    margin: 0 8px;
}
.sentence-container {
    background-color: #f8f9fc;
    padding: 15px;
    border-radius: 8px;
    border-left: 5px solid #4e73df;
    margin-bottom: 8px;
    line-height: 2.3;
}
.error-badge {
    background-color: #e74a3b;
    color: white;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
    margin-left: 8px;
}
.grammar-error {
    border: 2px solid #e74a3b !important;
    background-color: #fdf2f2 !important;
    color: #e74a3b !important;
}
.grammar-error u {
    text-decoration: underline red 3px;
    font-weight: bold;
}
.question-box {
    background-color: #ffffff;
    border: 1px solid #e3e6f0;
    border-left: 4px solid #1cc88a;
    padding: 15px;
    border-radius: 6px;
    margin-bottom: 12px;
    line-height: 1.8;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 세션 상태 관리
# ---------------------------------------------------------
if "sentences" not in st.session_state:
    st.session_state.sentences = []
if "translations" not in st.session_state:
    st.session_state.translations = []
if "mode" not in st.session_state:
    st.session_state.mode = None
if "generated_questions" not in st.session_state:
    st.session_state.generated_questions = []
if "extracted_text" not in st.session_state:
    st.session_state.extracted_text = ""
if "eng_input_area" not in st.session_state:
    st.session_state.eng_input_area = ""

# ---------------------------------------------------------
# 3. DFveloper Aikar Engine AI 연동 함수
# ---------------------------------------------------------
AIKAR_API_URL = "https://chat.aeonthic.com/aikar-engine/v1/chat/completions"

def call_aikar_ai(prompt, system_prompt="You are an expert English teacher AI assistant."):
    """텍스트 기반 Aikar AI 호출 (샘플러 기본값)"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "model": "aikar-engine",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(AIKAR_API_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=12) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "choices" in res and len(res["choices"]) > 0:
                return res["choices"][0]["message"]["content"]
            return None
    except Exception:
        return None

def extract_text_from_image_via_ai(image_file):
    """이미지를 Base64로 인코딩하여 Aikar AI Vision에 직접 전달해 텍스트 추출"""
    try:
        image_bytes = image_file.read()
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        mime_type = getattr(image_file, "type", "image/jpeg") or "image/jpeg"
        data_url = f"data:{mime_type};base64,{b64_image}"

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }
        
        payload = {
            "model": "aikar-engine",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert OCR and transcription assistant. Your task is to extract all English text accurately from the provided image. Return ONLY the extracted text, without any conversational preamble or markdown code blocks."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract and transcribe all English passage text from this image clearly and completely."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url}
                        }
                    ]
                }
            ],
            "max_tokens": 1500
        }
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(AIKAR_API_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=20) as response:
            res = json.loads(response.read().decode("utf-8"))
            if "choices" in res and len(res["choices"]) > 0:
                text = res["choices"][0]["message"]["content"].strip()
                text = re.sub(r'^```[a-zA-Z]*\s*|```\$', '', text, flags=re.MULTILINE).strip()
                return text, None
        return None, "AI 분석 결과에서 텍스트를 추출하지 못했습니다."
    except Exception as e:
        return None, f"AI 이미지 처리 중 오류가 발생했습니다: {str(e)}"

# ---------------------------------------------------------
# 4. 문장 분할, 어법 검사 및 수정 적용 함수
# ---------------------------------------------------------
def split_into_sentences(text):
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if len(lines) == 1:
        raw_sentences = re.split(r'(?<=[.!?])\s+', lines[0])
        return [s.strip() for s in raw_sentences if s.strip()]
    return lines

def process_inputs(eng_text, kor_text):
    eng_sentences = split_into_sentences(eng_text)
    kor_sentences = split_into_sentences(kor_text) if kor_text.strip() else []
    
    if not kor_sentences and eng_sentences:
        ai_prompt = f"""다음 영어 문장 목록을 순서대로 한국어로 자연스럽게 번역해서 JSON 문자열 배열(List of strings) 형태로만 응답해줘.
인사말, 추가 설명, 마크다운 없이 오직 JSON 배열만 출력해야 해.

[영어 문장 목록]
{json.dumps(eng_sentences, ensure_ascii=False)}
"""
        system_prompt = "You are a professional English-to-Korean translator. Return ONLY a JSON array of translated strings matching the input sentences 1:1."
        translated_res = call_aikar_ai(ai_prompt, system_prompt)
        
        if translated_res:
            try:
                cleaned_res = re.sub(r'^```json\s*|```\$', '', translated_res.strip(), flags=re.MULTILINE)
                parsed_kor = json.loads(cleaned_res)
                if isinstance(parsed_kor, list):
                    kor_sentences = [str(item).strip() for item in parsed_kor]
            except Exception:
                lines = translated_res.strip().splitlines()
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("```") or ("번역" in line and ":" in line):
                        continue
                    cleaned_line = re.sub(r'^(?:\d+[\.\)]|[-•*])\s*', '', line)
                    if cleaned_line:
                        cleaned_lines.append(cleaned_line)
                kor_sentences = cleaned_lines

    translations = []
    for i in range(len(eng_sentences)):
        if i < len(kor_sentences) and kor_sentences[i]:
            translations.append(kor_sentences[i])
        else:
            translations.append("AI 번역을 불러오지 못했습니다. (지문 입력을 다시 확인해 주세요)")
            
    return eng_sentences, translations

def check_local_rules(sentence):
    rules = [
        (r'\b(this|that)\s+(are|were)\b', "'this/that' 뒤에는 단수 동사(is/was)가 와야 합니다.", "is"),
        (r'\b(these|those)\s+(is|was)\b', "'these/those' 뒤에는 복수 동사(are/were)가 와야 합니다.", "are"),
        (r'\b(he|she|it)\s+(go|do|have|like|want)\b', "3인칭 단수 주어 뒤에는 단수형 동사(-s/-es)가 와야 합니다.", "goes/does/has/likes/wants"),
        (r'\b(i)\s+(are|is)\b', "주어 'I' 뒤에는 am/was가 와야 합니다.", "am"),
        (r'\b(you|we|they)\s+(is|was)\b', "복수 주어 뒤에는 are/were가 와야 합니다.", "are/were")
    ]
    local_spans = []
    for pattern, msg, repl in rules:
        for m in re.finditer(pattern, sentence, re.IGNORECASE):
            local_spans.append((m.start(), m.end(), msg, [repl]))
    return local_spans

def check_grammar_combined(sentence):
    spans = check_local_rules(sentence)
    url = "[https://api.languagetool.org/v2/check](https://api.languagetool.org/v2/check)"
    params = urllib.parse.urlencode({'text': sentence, 'language': 'en-US'})
    req = urllib.request.Request(
        url, data=params.encode('utf-8'),
        headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded'}
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            res = json.loads(response.read().decode('utf-8'))
            for m in res.get('matches', []):
                offset, length = m['offset'], m['length']
                msg = m['message']
                replacements = [r['value'] for r in m.get('replacements', [])]
                if not any(s[0] <= offset < s[1] for s in spans):
                    spans.append((offset, offset + length, msg, replacements))
    except Exception:
        pass
    return len(spans) > 0, spans

def get_corrected_sentence(sentence, error_spans):
    sorted_spans = sorted(error_spans, key=lambda x: x[0], reverse=True)
    corrected = sentence
    for start, end, msg, repls in sorted_spans:
        if repls:
            corrected = corrected[:start] + repls[0] + corrected[end:]
    return corrected

def apply_correction(idx, corrected_sent):
    st.session_state.sentences[idx] = corrected_sent
    new_full_text = " ".join(st.session_state.sentences)
    st.session_state.extracted_text = new_full_text
    st.session_state.eng_input_area = new_full_text

def format_sentence_html(sentence, error_spans):
    error_indices = set()
    for start, end, _, _ in error_spans:
        for i in range(start, end):
            error_indices.add(i)

    delimiters = r'(\b(?:in|on|at|to|for|with|by|about|because|although|when|where|which|who|that|and|but)\b)'
    tokens = re.split(r'(\s+)', sentence)
    formatted_html = ""
    current_pos = 0
    
    for token in tokens:
        token_len = len(token)
        start_idx = current_pos
        end_idx = current_pos + token_len
        current_pos = end_idx
        
        if not token.strip():
            formatted_html += token
            continue
            
        is_error = any(idx in error_indices for idx in range(start_idx, end_idx))
        if re.match(delimiters, token, flags=re.IGNORECASE):
            formatted_html += " <span class='slash'>/</span> "
            
        if is_error:
            formatted_html += f"<span class='circle-word grammar-error'><u>{token}</u></span>"
        else:
            formatted_html += f"<span class='circle-word'>{token}</span>"
            
    return formatted_html

def calculate_similarity(user_text, target_text):
    clean_user = re.sub(r'[^\w\s]', '', user_text).replace(" ", "")
    clean_target = re.sub(r'[^\w\s]', '', target_text).replace(" ", "")
    if not clean_target:
        return 0.0
    return round(SequenceMatcher(None, clean_user, clean_target).ratio() * 100, 1)

# ---------------------------------------------------------
# 5. 수능/내신 문제 생성기
# ---------------------------------------------------------
def generate_rule_based_questions(sentences):
    questions = []
    full_text = " ".join(sentences)
    
    target_sentence = max(sentences, key=len) if sentences else "English passage study."
    s_words = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', target_sentence)]
    blank_word = s_words[len(s_words)//2] if s_words else "important"
    blank_text = target_sentence.replace(blank_word, " [ ________ ] ", 1)
    
    distractors = ["different", "necessary", "traditional", "effective", "possible"]
    options_q1 = list(set([blank_word] + random.sample(distractors, 4)))[:5]
    if blank_word not in options_q1:
        options_q1[0] = blank_word
    random.shuffle(options_q1)
    
    questions.append({
        "type": "1. 빈칸 추론",
        "title": "다음 글의 빈칸에 들어갈 가장 적절한 어휘를 고르시오.",
        "content": blank_text,
        "options": [f"① {options_q1[0]}", f"② {options_q1[1]}", f"③ {options_q1[2]}", f"④ {options_q1[3]}", f"⑤ {options_q1[4]}"],
        "answer": f"① {blank_word}" if options_q1[0] == blank_word else (
            f"② {blank_word}" if options_q1[1] == blank_word else (
                f"③ {blank_word}" if options_q1[2] == blank_word else (
                    f"④ {blank_word}" if options_q1[3] == blank_word else f"⑤ {blank_word}"
                )
            )
        )
    })

    q2_text = sentences[0] if sentences else full_text
    q2_words = re.findall(r'\b[a-zA-Z]+\b', q2_text)
    marked_text = q2_text
    err_index = 2
    if len(q2_words) >= 5:
        w_targets = q2_words[:5]
        for i, w in enumerate(w_targets, 1):
            num_str = f"①" if i==1 else ("②" if i==2 else ("③" if i==3 else ("④" if i==4 else "⑤")))
            if i == err_index:
                err_w = w + "s" if not w.endswith("s") else w[:-1]
                marked_text = marked_text.replace(w, f"<u>{num_str} {err_w}</u>", 1)
            else:
                marked_text = marked_text.replace(w, f"<u>{num_str} {w}</u>", 1)
    else:
        marked_text = f"<u>① This</u> <u>② are</u> <u>③ a</u> <u>④ sample</u> <u>⑤ sentence</u>."
        err_index = 2

    questions.append({
        "type": "2. 어법 판단",
        "title": "다음 글의 밑줄 친 ①~⑤ 중, 어법상 어색한 것을 고르시오.",
        "content": marked_text,
        "options": ["① 번 항목", "② 번 항목", "③ 번 항목", "④ 번 항목", "⑤ 번 항목"],
        "answer": f"② 번 항목" if err_index == 2 else f"③ 번 항목"
    })

    questions.append({
        "type": "3. 어휘 적절성",
        "title": "(A), (B), (C)의 각 네모 안에서 문맥에 맞는 낱말로 가장 적절한 것은?",
        "content": f"The passage indicates that progress is (A) [increase / decrease] when resources are available. Furthermore, the outcome is highly (B) [positive / negative]. Thus, we must maintain (C) [active / passive] support.",
        "options": [
            "① (A) increase - (B) positive - (C) active",
            "② (A) increase - (B) negative - (C) active",
            "③ (A) decrease - (B) positive - (C) passive",
            "④ (A) decrease - (B) negative - (C) active",
            "⑤ (A) increase - (B) positive - (C) passive"
        ],
        "answer": "① (A) increase - (B) positive - (C) active"
    })

    if len(sentences) >= 4:
        box_s = sentences[0]
        p_a = sentences[1]
        p_b = sentences[2]
        p_c = " ".join(sentences[3:])
    else:
        box_s = "Language learning requires consistent practice and exposure."
        p_a = "(A) First, reading diverse passages expands vocabulary naturally."
        p_b = "(B) In addition, practicing grammar ensures clarity in expression."
        p_c = "(C) Therefore, combining both methods leads to optimal fluency."

    questions.append({
        "type": "4. 글의 순서 배열",
        "title": "주어진 글 다음에 이어질 글의 순서로 가장 적절한 것을 고르시오.",
        "content": f"<b>[주어진 글]</b><br>{box_s}<br><br><b>(A)</b> {p_a}<br><b>(B)</b> {p_b}<br><b>(C)</b> {p_c}",
        "options": ["① (A) - (C) - (B)", "② (B) - (A) - (C)", "③ (A) - (B) - (C)", "④ (C) - (B) - (A)", "⑤ (B) - (C) - (A)"],
        "answer": "③ (A) - (B) - (C)"
    })

    if len(sentences) >= 3:
        target_ins = sentences[1]
        p_inserted = f"{sentences[0]} ( ① ) {sentences[2]} ( ② ) ( ③ ) ( ④ ) ( ⑤ )"
    else:
        target_ins = "However, effective strategies can significantly boost learning speed."
        p_inserted = "Studying English requires patience and time. ( ① ) Many students struggle with grammar. ( ② ) Practice helps overcome difficulties. ( ③ ) Consistency is key. ( ④ ) Success follows effort. ( ⑤ )"

    questions.append({
        "type": "5. 문장 삽입",
        "title": "글의 흐름으로 보아, 주어진 문장이 들어 가기에 가장 적절한 곳을 고르시오.",
        "content": f"<b>[보기 문장]</b><br><i>{target_ins}</i><br><br>{p_inserted}",
        "options": ["① 번 위치", "② 번 위치", "③ 번 위치", "④ 번 위치", "⑤ 번 위치"],
        "answer": "① 번 위치"
    })

    return questions

def generate_5_exam_questions(sentences):
    full_passage = " ".join(sentences)
    system_prompt = "You are an English test creator for Korean CSAT (수능). Response MUST be valid JSON array only."
    prompt = f"""Given the following English passage, generate 5 multiple-choice questions in JSON array format.
    Passage: "{full_passage}"

    Required JSON format (A JSON array containing exactly 5 objects):
    [
      {{
        "type": "1. 빈칸 추론",
        "title": "다음 글의 빈칸에 들어갈 가장 적절한 어휘를 고르시오.",
        "content": "sentence with [ ________ ]",
        "options": ["① word1", "② word2", "③ word3", "④ word4", "⑤ word5"],
        "answer": "① word1"
      }},
      ... (include types: "2. 어법 판단", "3. 어휘 적절성", "4. 글의 순서 배열", "5. 문장 삽입")
    ]
    Do not output markdown code block format, output raw JSON only.
    """
    
    response = call_aikar_ai(prompt, system_prompt)
    if response:
        try:
            cleaned_res = re.sub(r'^```json\s*|```$', '', response.strip(), flags=re.MULTILINE)
            questions = json.loads(cleaned_res)
            if isinstance(questions, list) and len(questions) == 5:
                return questions
        except Exception:
            pass
            
    return generate_rule_based_questions(sentences)

# ---------------------------------------------------------
# 6. 입력 화면 구성
# ---------------------------------------------------------
st.title("📚 영어 지문 분석 & 시험 문제 생성기 (Aikar AI 탑재)")

col_input1, col_input2 = st.columns(2)

with col_input1:
    st.markdown("### 1. 영어 지문 입력")
    
    uploaded_image = st.file_uploader(
        "📷 지문 이미지/사진 업로드 (Aikar AI 직통 텍스트 분석)",
        type=["png", "jpg", "jpeg"]
    )
    
    if uploaded_image is not None:
        with st.spinner("🤖 Aikar AI가 이미지에서 영어 지문을 직접 읽어오는 중입니다..."):
            extracted_text, err = extract_text_from_image_via_ai(uploaded_image)
            if err:
                st.error(err)
            elif extracted_text:
                st.session_state.eng_input_area = extracted_text
                st.session_state.extracted_text = extracted_text
                st.success("✨ Aikar AI가 이미지에서 지문을 정확하게 직접 추출했습니다!")

    input_eng = st.text_area(
        "영어 지문 내용:",
        height=180,
        key="eng_input_area",
        placeholder="영어 문장들을 직접 입력하거나 위에서 이미지를 업로드하세요..."
    )

with col_input2:
    st.markdown("### 2. 한국어 뜻 입력")
    st.write("")
    st.write("")
    st.write("")
    input_kor = st.text_area(
        "한국어 뜻 내용 (비워둘 경우 Aikar AI가 자동 번역):",
        height=180,
        placeholder="영어 문장 순서에 맞게 한국어 해석을 입력하세요 (비워두면 AI가 자동 해석)..."
    )

col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button("🚀 학습시작", use_container_width=True):
        if input_eng.strip():
            with st.spinner("지문을 정리 중입니다..."):
                s_list, t_list = process_inputs(input_eng, input_kor)
                st.session_state.sentences = s_list
                st.session_state.translations = t_list
                st.session_state.mode = "learn"
        else:
            st.warning("영어 지문을 입력해 주세요!")

with col_btn2:
    if st.button("🧠 암기하기", use_container_width=True):
        if input_eng.strip():
            with st.spinner("해석 데이터를 처리 중입니다..."):
                s_list, t_list = process_inputs(input_eng, input_kor)
                st.session_state.sentences = s_list
                st.session_state.translations = t_list
                st.session_state.mode = "memo"
        else:
            st.warning("영어 지문을 입력해 주세요!")

with col_btn3:
    if st.button("📝 문제", use_container_width=True):
        if input_eng.strip():
            with st.spinner("🤖 DFveloper Aikar AI가 수능 유형 문제 5개를 생성 중입니다..."):
                s_list, t_list = process_inputs(input_eng, input_kor)
                st.session_state.sentences = s_list
                st.session_state.translations = t_list
                st.session_state.generated_questions = generate_5_exam_questions(s_list)
                st.session_state.mode = "exam"
        else:
            st.warning("영어 지문을 입력해 주세요!")

st.divider()

# ---------------------------------------------------------
# 7. 모드별 기능 실행
# ---------------------------------------------------------

# [학습 모드]
if st.session_state.mode == "learn":
    st.subheader("📖 끊어 읽기 & 구문 학습")
    st.caption("💡 어법 오류가 발견되면 빨간색 밑줄과 함께 '오류문장' 태그가 표시됩니다. 오류 내역을 확인하고 버튼을 누르면 자동 수정됩니다.")
    
    with st.spinner("어법 오류 및 구문을 분석 중입니다..."):
        for idx, (sentence, trans) in enumerate(zip(st.session_state.sentences, st.session_state.translations), 1):
            has_error, error_spans = check_grammar_combined(sentence)
            formatted_eng = format_sentence_html(sentence, error_spans)
            
            error_label = '<span class="error-badge">⚠️ 오류문장</span>' if has_error else ''
            
            st.markdown(f"**[문장 #{idx}]** {error_label}", unsafe_allow_html=True)
            st.markdown(f'<div class="sentence-container">{formatted_eng}</div>', unsafe_allow_html=True)
            
            if has_error:
                corrected_sentence = get_corrected_sentence(sentence, error_spans)
                
                with st.expander("🚨 어법 오류 상세 내용 및 자동 수정"):
                    for _, _, msg, repl in error_spans:
                        sug_str = f" (추천 수정: **{', '.join(repl[:3])}**)" if repl else ""
                        st.write(f"- {msg}{sug_str}")
                    
                    if corrected_sentence != sentence:
                        st.button(
                            f"✨ '{corrected_sentence}'(으)로 변경하기", 
                            key=f"fix_btn_{idx}",
                            on_click=apply_correction,
                            args=(idx-1, corrected_sentence)
                        )
            
            with st.expander(f"🔍 문장 #{idx} 한국어 해석 보기"):
                st.info(f"**등록된 해석:** {trans}")
                
            st.write("")

# [암기하기 모드]
elif st.session_state.mode == "memo":
    st.subheader("🧠 문장 해석 암기 테스트")
    st.caption("영어 문장을 읽고 한국어 해석을 입력해 보세요. 90점 이상은 정답, 미만은 오답 처리됩니다.")
    
    total_score = 0
    correct_count = 0
    total_count = len(st.session_state.sentences)
    answered_count = 0
    
    for idx, (sentence, target_trans) in enumerate(zip(st.session_state.sentences, st.session_state.translations), 1):
        st.markdown(f"**Q{idx}. {sentence}**")
        
        user_input = st.text_input(
            f"Q{idx} 한국어 해석 작성:",
            key=f"memo_input_{idx}",
            placeholder="해석을 입력하고 Enter를 누르세요..."
        )
        
        if user_input:
            answered_count += 1
            score = calculate_similarity(user_input, target_trans)
            total_score += score
            
            if score >= 90:
                correct_count += 1
                st.success(f"점수: **{score}점** (정답) 🎯")
            else:
                st.error(f"점수: **{score}점** (오답) 💡")
                
            with st.expander("등록된 정답 해석 확인하기"):
                st.write(f"**정답 해석:** {target_trans}")
        st.write("---")
        
    if total_count > 0:
        avg_score = round(total_score / total_count, 1) if answered_count > 0 else 0.0
        
        st.metric(
            label="📊 전체 평균 일치율 및 정답 현황", 
            value=f"{avg_score}점 ({correct_count}/{total_count})"
        )
        
        if answered_count == total_count and correct_count == total_count:
            st.balloons()
            st.success("🎉 축하합니다! 모든 해석 암기 문제를 정답으로 맞히셨습니다!")

# [문제 모드]
elif st.session_state.mode == "exam":
    st.subheader("📝 수능/내신 유형 객관식 문제 (Aikar AI 생성)")
    st.caption("Aikar AI가 지문을 실시간으로 분석하여 만든 5가지 문제 유형입니다. 보기를 클릭하여 정답을 제출하세요.")
    
    exam_score = 0
    answered_exam_count = 0
    
    for idx, q in enumerate(st.session_state.generated_questions, 1):
        st.markdown(f"### Q{idx}. {q['type']}")
        st.markdown(f"**{q['title']}**")
        st.markdown(f'<div class="question-box">{q["content"]}</div>', unsafe_allow_html=True)
        
        user_choice = st.radio(
            "정답을 선택하세요:",
            q["options"],
            key=f"exam_radio_{idx}",
            index=None
        )
        
        if user_choice is not None:
            answered_exam_count += 1
            if user_choice == q["answer"]:
                st.success("🎯 정답입니다!")
                exam_score += 1
            else:
                st.error(f"❌ 오답입니다. (선택한 답: {user_choice})")
                
            with st.expander("정답 및 해설 보기"):
                st.write(f"**정답:** {q['answer']}")
        st.write("---")
        
    st.metric(label="📊 총 맞힌 문제 수", value=f"{exam_score} / 5 개")
    
    if answered_exam_count == 5 and exam_score == 5:
        st.balloons()
        st.success("🎉 축하합니다! 5가지 수능 유형 문제를 모두 맞히셨습니다!")
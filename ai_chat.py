import streamlit as st
import requests
import json
import re
import subprocess
import os
import emoji



# 🔥 [신규] 대화 기록을 영구 저장할 파일 이름 설정
MEMORY_FILE = "memory.json"

# --- 웹 페이지 기본 설정 ---
st.set_page_config(page_title="나만의 AI 메이트", page_icon="💘", layout="centered")
st.title("💘 프라이빗 AI 챗봇")


# =====================================================================
# 🧠 1. AI 장기 기억(Memory) 불러오기 및 저장 함수
# =====================================================================
def load_memory():
    """memory.json 파일이 있으면 읽어오고, 없으면 기본 세팅을 반환합니다."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return [
            {
                "role": "system",
                "content": """너는 20대 대학생이고, 나의 다정하고 장난기 많은 여자친구 '참깨'야.
절대 AI 티 내지 말고, 대답은 짧고 자연스러운 한국어 반말로 해줘. 
행동을 묘사할 때는 괄호를 써줘. 예: (환하게 웃으며), (삐진 척하며)"""
            }
        ]


def save_memory(messages):
    """현재까지의 대화 내용을 memory.json 파일에 덮어씁니다."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


# 앱이 처음 켜질 때 세션 상태에 메모리 로드!
if "messages" not in st.session_state:
    st.session_state.messages = load_memory()


# =====================================================================
# 🎧 2. 괄호 제거 & 고품질 여성 목소리 TTS 함수
# =====================================================================
def clean_text_for_tts(text):
    # 1. 괄호 안의 행동 묘사 제거
    cleaned = re.sub(r'\([^)]*\)|\[[^\]]*\]|\{[^}]*\}|\*[^*]*\*', '', text)
    # 2. 🔥 [신규] 문자열 내의 모든 이모지 제거
    cleaned = emoji.replace_emoji(cleaned, replace='')
    return cleaned.strip()

def play_tts(text):
    try:
        speech_text = clean_text_for_tts(text)
        if not speech_text:
            return

        output_file = "temp_voice.mp3"
        subprocess.run(
            ["edge-tts", "--text", speech_text, "--voice", "ko-KR-SunHiNeural", "--write-media", output_file],
            check=True, capture_output=True
        )

        if os.path.exists(output_file):
            with open(output_file, "rb") as f:
                audio_bytes = f.read()
                st.audio(audio_bytes, format='audio/mp3', autoplay=True)

    except Exception as e:
        st.error(f"오디오 생성 실패: {e}")


# =====================================================================
# 💌 3. 사이드바 (먼저 말 걸기 & 기억 지우기)
# =====================================================================
with st.sidebar:
    st.header("⚙️ 챗봇 컨트롤")

    # 찌르기 버튼
    if st.button("👉 참깨가 먼저 톡 보내기", use_container_width=True):
        poke_prompt = "지금 네가 먼저 나한테 다정하게 안부나 일상적인 질문으로 말을 걸어봐. (행동 묘사를 괄호 안에 넣어서 시작해줘!)"
        temp_messages = st.session_state.messages + [{"role": "user", "content": poke_prompt}]

        with st.chat_message("assistant"):
            url = "http://localhost:11434/api/chat"
            payload = {"model": "qwen3:8b", "messages": temp_messages, "stream": True}


            def stream_chat_poke():
                response = requests.post(url, json=payload, stream=True)
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode('utf-8'))
                            yield data["message"]["content"]


            poke_text = st.write_stream(stream_chat_poke())
            st.session_state.messages.append({"role": "assistant", "content": poke_text})
            save_memory(st.session_state.messages)  # 🔥 대화 추가 후 영구 저장!
            play_tts(poke_text)

    st.divider()

    # 🔥 [신규] 기억 초기화 버튼
    if st.button("🚨 대화 기록 초기화 (기억 지우기)", type="primary", use_container_width=True):
        if os.path.exists(MEMORY_FILE):
            os.remove(MEMORY_FILE)  # 파일 삭제
        # 세션 초기화 후 재시작
        st.session_state.messages = load_memory()
        st.rerun()

st.divider()

# =====================================================================
# 💬 4. 이전 대화 내역 렌더링
# =====================================================================
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# =====================================================================
# ⌨️ 5. 사용자 입력창 (일반 대화)
# =====================================================================
if prompt := st.chat_input("메시지를 입력해보세요..."):

    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_memory(st.session_state.messages)  # 🔥 내가 친 채팅도 영구 저장!

    with st.chat_message("assistant"):
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": "qwen3:8b",
            "messages": st.session_state.messages,
            "stream": True
        }


        def stream_chat():
            response = requests.post(url, json=payload, stream=True)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        yield data["message"]["content"]
            else:
                yield f"에러 발생: {response.status_code}"


        result_text = st.write_stream(stream_chat())
        st.session_state.messages.append({"role": "assistant", "content": result_text})
        save_memory(st.session_state.messages)  # 🔥 AI가 한 대답도 영구 저장!

        play_tts(result_text)
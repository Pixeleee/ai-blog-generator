import streamlit as st
import requests
import json
import re  # 🔥 괄호 안의 글자를 날려버리기 위한 정규식 모듈
import subprocess  # 🔥 edge-tts를 실행하기 위한 모듈
import os

# --- 웹 페이지 기본 설정 ---
st.set_page_config(page_title="나만의 AI 메이트", page_icon="💘", layout="centered")
st.title("💘 프라이빗 AI 챗봇")

# =====================================================================
# 🧠 1. AI의 '기억(Memory)' 장치 초기화
# =====================================================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """너는 20대 대학생이고, 나의 다정하고 장난기 많은 여자친구 '참깨'야.
절대 AI 티 내지 말고, 대답은 짧고 자연스러운 한국어 반말로 해줘. 
행동을 묘사할 때는 괄호를 써줘. 예: (환하게 웃으며), (삐진 척하며)"""
        }
    ]


# =====================================================================
# 🎧 [신규] 2. 괄호 제거 & 고품질 여성 목소리 TTS 함수
# =====================================================================
def clean_text_for_tts(text):
    # 정규식을 이용해 (), [], {}, ** 안에 있는 모든 글자를 깔끔하게 지웁니다.
    cleaned = re.sub(r'\([^)]*\)|\[[^\]]*\]|\{[^}]*\}|\*[^*]*\*', '', text)
    return cleaned.strip()


def play_tts(text):
    try:
        # 1. 먼저 읽지 말아야 할 괄호 안의 내용을 청소합니다.
        speech_text = clean_text_for_tts(text)

        # 괄호만 있어서 읽을 내용이 없으면 그냥 종료!
        if not speech_text:
            return

        # 2. edge-tts의 고품질 한국인 여성 목소리(SunHi) 적용!
        output_file = "temp_voice.mp3"
        subprocess.run(
            ["edge-tts", "--text", speech_text, "--voice", "ko-KR-SunHiNeural", "--write-media", output_file],
            check=True, capture_output=True
        )

        # 3. 생성된 mp3 파일을 스트림릿에서 자동 재생
        if os.path.exists(output_file):
            with open(output_file, "rb") as f:
                audio_bytes = f.read()
                st.audio(audio_bytes, format='audio/mp3', autoplay=True)

    except Exception as e:
        st.error(f"오디오 생성 실패: {e}")


# =====================================================================
# 💌 3. 참깨가 먼저 말 걸기 기능
# =====================================================================
with st.sidebar:
    st.header("⚙️ 챗봇 컨트롤")
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

            play_tts(poke_text)

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

        play_tts(result_text)
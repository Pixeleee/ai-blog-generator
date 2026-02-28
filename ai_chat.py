import streamlit as st
import requests
import json
from gtts import gTTS
import io

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
절대 AI 티 내지 말고, 대답은 짧고 자연스러운 한국어 반말로 해줘. 귀여운 이모지 필수!"""
        }
    ]


# 🎧 TTS(음성 합성) 함수: 텍스트를 받아서 즉시 오디오 플레이어로 띄워줍니다.
def play_tts(text):
    try:
        tts = gTTS(text=text, lang='ko', slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        # autoplay=True 를 주면 글씨가 써진 직후에 목소리가 바로 나옵니다!
        st.audio(fp, format='audio/mp3', autoplay=True)
    except Exception as e:
        st.error(f"오디오 생성 실패: {e}")


# =====================================================================
# 💌 [신규] 2. 참깨가 먼저 말 걸기 기능 (사이드바에 버튼 배치)
# =====================================================================
with st.sidebar:
    st.header("⚙️ 챗봇 컨트롤")
    if st.button("👉 참깨가 먼저 톡 보내기", use_container_width=True):
        # AI에게 몰래 "네가 먼저 대화를 시작해봐" 라고 찌르는(Poke) 역할입니다.
        poke_prompt = "지금 네가 먼저 나한테 다정하게 안부나 일상적인 질문으로 말을 걸어봐. (내가 한 말처럼 하지 말고, 네가 먼저 시작하는 느낌으로)"

        # 화면에 보이지 않게 임시로 AI를 자극합니다.
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


            # 먼저 말 거는 내용 생성 및 화면 출력
            poke_text = st.write_stream(stream_chat_poke())
            st.session_state.messages.append({"role": "assistant", "content": poke_text})

            # 🔥 생성된 텍스트를 목소리로 읽어주기!
            play_tts(poke_text)

st.divider()

# =====================================================================
# 💬 3. 이전 대화 내역 렌더링
# =====================================================================
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# =====================================================================
# ⌨️ 4. 사용자 입력창 (일반 대화)
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


        # 텍스트 렌더링
        result_text = st.write_stream(stream_chat())
        st.session_state.messages.append({"role": "assistant", "content": result_text})

        # 🔥 생성된 답변을 목소리로 읽어주기!
        play_tts(result_text)
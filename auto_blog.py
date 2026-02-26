import streamlit as st
import requests
import json
import os

# 웹 페이지 기본 설정
st.set_page_config(page_title="AI 블로그 에디터", page_icon="📝", layout="wide")

st.title("📝 나만의 AI 기술 블로그 에디터")
st.markdown("Ollama(Qwen3:8b)를 활용해 내 코드를 깃허브 블로그용 마크다운으로 변환합니다.")

# --- 사이드바: 설정 영역 ---
with st.sidebar:
    st.header("⚙️ 설정")
    output_dir = st.text_input("📁 마크다운 저장 폴더 경로", value="./posts")
    st.caption("지정한 폴더가 없으면 알아서 새로 만듭니다!")

# --- 메인 화면: 반으로 나누기 ---
col1, col2 = st.columns(2)

# [왼쪽 화면: 입력]
with col1:
    st.subheader("1. 코드 업로드")
    uploaded_file = st.file_uploader("분석할 파이썬 코드를 올려주세요", type=['py'])

    st.subheader("2. 프롬프트 튜닝")
    default_prompt = """너는 내 기술 블로그 전속 에디터야. 
아래 코드를 분석하고, 독자들이 이해하기 쉽게 마크다운(Markdown) 형식으로 기술 블로그 초안을 작성해 줘.
코드의 핵심 동작 원리를 친절하게 설명하고,이모지는 사용하지 말아줘."""
    prompt_input = st.text_area("AI에게 내릴 세부 지시사항", value=default_prompt, height=150)

# [오른쪽 화면: 결과]
with col2:
    st.subheader("3. 결과 확인")

    if st.button("🚀 마크다운 생성 시작!", use_container_width=True):
        if uploaded_file is None:
            st.warning("👈 먼저 왼쪽에서 코드를 업로드해주세요!")
        else:
            # 1. 파일 내용 읽기
            code_content = uploaded_file.getvalue().decode("utf-8")
            base_name = uploaded_file.name.split('.')[0]

            url = "http://localhost:11434/api/generate"
            full_prompt = f"{prompt_input}\n\n[내 코드]\n```python\n{code_content}\n```"

            # 🔥 핵심 1: stream 옵션을 True로 변경!
            payload = {"model": "qwen3:8b", "prompt": full_prompt, "stream": True}

            st.markdown("### ✨ 완성된 초안")


            # 🔥 핵심 2: 데이터를 조각조각 받아오는 제너레이터(Generator) 함수
            def stream_data():
                # stream=True로 요청을 보냅니다.
                response = requests.post(url, json=payload, stream=True)
                if response.status_code == 200:
                    # 서버에서 들어오는 데이터를 한 줄씩 읽어옵니다.
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode('utf-8'))
                            yield data.get("response", "")  # yield를 써서 데이터를 밖으로 톡톡 던져줍니다!
                else:
                    yield f"\n❌ API 에러 발생: {response.status_code}"


            try:
                # 🔥 핵심 3: st.write_stream이 제너레이터를 받아 타자 치듯 화면에 그려줍니다.
                # 게다가 화면에 다 그린 전체 텍스트를 result_text 변수에 예쁘게 모아줍니다!
                result_text = st.write_stream(stream_data())

                # 4. 파일 저장 로직 (이제 완성된 전체 텍스트를 저장합니다)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                output_path = os.path.join(output_dir, f"{base_name}_blog.md")

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result_text)

                st.success(f"✅ 생성 완료! 지정하신 경로에 파일이 저장되었습니다: `{output_path}`")

            except Exception as e:
                st.error(f"❌ Ollama 통신 에러: {e}")
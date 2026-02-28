import streamlit as st
import requests
import json
import os
from datetime import datetime
import subprocess
import pyperclip  # 🔥 클립보드 복사를 위한 신규 라이브러리!

# 프롬프트 폴더 경로
PROMPTS_DIR = "./prompts"

# --- 웹 페이지 기본 설정 ---
st.set_page_config(page_title="AI 멀티 퍼블리셔", page_icon="🐙", layout="wide")
st.title("🐙 AI 멀티 퍼블리셔 (GitHub & Naver)")
st.markdown("하나의 툴로 개발 블로그부터 일상 수익형 블로그까지 완벽하게 컨트롤합니다.")

# --- 사이드바: 설정 영역 ---
with st.sidebar:
    st.header("⚙️ 설정")
    output_dir = st.text_input("📁 결과물 저장 폴더 경로", value="./posts")
    st.caption("지정한 폴더가 없으면 알아서 새로 만듭니다!")

# --- 메인 화면: 반으로 나누기 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 템플릿 선택 및 편집")
    prompt_files = [f for f in os.listdir(PROMPTS_DIR) if f.endswith('.txt')]
    selected_preset = st.selectbox("📝 프롬프트 프리셋 선택", prompt_files)
    file_path = os.path.join(PROMPTS_DIR, selected_preset)

    with open(file_path, "r", encoding="utf-8") as f:
        preset_content = f.read()

    edited_prompt = st.text_area("불러온 프리셋 (입맛대로 수정하고 아래 저장 버튼을 누르세요!)", value=preset_content, height=250)

    if st.button("💾 현재 프롬프트 덮어쓰기 (영구 저장)"):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(edited_prompt)
        st.success(f"✅ '{selected_preset}' 파일에 변경사항이 완벽하게 저장되었습니다!")

    st.divider()

    st.subheader("2. 분석할 데이터 (코드 또는 키워드 텍스트)")
    uploaded_file = st.file_uploader("파이썬 파일(.py)이나 텍스트(.txt)를 올려주세요.", type=['py', 'txt'])

    st.subheader("3. 📸 첨부할 이미지 (네이버 블로그용)")
    uploaded_images = st.file_uploader("맛집, 매장 사진 등을 여러 장 올려주세요", type=['png', 'jpg', 'jpeg'],
                                       accept_multiple_files=True)

with col2:
    st.subheader("4. 결과 확인")

    if st.button("🚀 AI 생성 시작!", use_container_width=True):
        if uploaded_file is None:
            st.warning("👈 먼저 왼쪽에서 분석할 데이터 파일을 업로드해주세요!")
        else:
            file_content = uploaded_file.getvalue().decode("utf-8")
            base_name = uploaded_file.name.split('.')[0]

            url = "http://localhost:11434/api/generate"
            today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            final_prompt = edited_prompt.replace("{today_date}", today_date)

            image_info = f"\n[참고: 첨부된 사진 {len(uploaded_images)}장 있음. 글 중간중간 적절한 위치에 '[사진 들어갈 곳]' 이라고 표시해 줘!]" if uploaded_images else ""

            full_prompt = f"{final_prompt}{image_info}\n\n[제공된 데이터]\n```\n{file_content}\n```"
            payload = {"model": "qwen3:8b", "prompt": full_prompt, "stream": True}


            def stream_data():
                response = requests.post(url, json=payload, stream=True)
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode('utf-8'))
                            yield data.get("response", "")
                else:
                    yield f"\n❌ API 에러 발생: {response.status_code}"


            try:
                tab1, tab2 = st.tabs(["👁️ 블로그 미리보기", "📝 원본 마크다운 (코드)"])

                with tab1:
                    result_text = st.write_stream(stream_data())
                with tab2:
                    st.code(result_text, language="markdown")

                # 텍스트 파일 저장
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                output_path = os.path.join(output_dir, f"{base_name}_blog.md")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result_text)

                # 이미지 저장
                img_dir = ""
                if uploaded_images:
                    img_dir = os.path.join(output_dir, "images", base_name)
                    if not os.path.exists(img_dir):
                        os.makedirs(img_dir)
                    for img in uploaded_images:
                        img_path = os.path.join(img_dir, img.name)
                        with open(img_path, "wb") as f:
                            f.write(img.getvalue())

                st.success("✅ 생성 및 로컬 저장 완료!")

                # ==========================================================
                # 🔥 [신규] 네이버 퍼블리싱을 위한 마법의 버튼 영역
                # ==========================================================
                st.markdown("### 🎯 네이버 블로그 업로드 도구")
                btn_col1, btn_col2 = st.columns(2)

                with btn_col1:
                    if st.button("📋 본문 전체 복사하기", type="primary", use_container_width=True):
                        pyperclip.copy(result_text)
                        st.toast("✅ 클립보드에 복사되었습니다! 네이버 에디터에 Ctrl+V 하세요.")

                with btn_col2:
                    # 이미지가 업로드 된 경우에만 폴더 열기 버튼 활성화
                    if uploaded_images:
                        if st.button("📂 이미지 폴더 열기", use_container_width=True):
                            # 윈도우 탐색기에서 해당 폴더를 즉시 팝업!
                            os.startfile(os.path.realpath(img_dir))
                    else:
                        st.button("📂 이미지 폴더 열기 (첨부된 사진 없음)", disabled=True, use_container_width=True)

            except Exception as e:
                st.error(f"❌ 에러 발생: {e}")

st.divider()
st.subheader("🚀 5. 깃허브(GitHub) 원클릭 배포 (개발 블로그용)")
commit_msg = st.text_input("📝 커밋 메시지를 입력하세요", value="docs: 새로운 포스팅 업데이트")

if st.button("전 세계로 배포하기 (Git Push) 🌍"):
    with st.spinner("GitHub로 데이터를 전송하는 중입니다... 🚀"):
        try:
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
            try:
                subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                pass
            subprocess.run(["git", "push"], check=True, capture_output=True, text=True)
            st.success(f"🎉 성공적으로 배포되었습니다! 🌱")
            st.balloons()
        except Exception as e:
            st.error(f"❌ 에러가 발생했습니다: {e}")
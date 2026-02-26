import streamlit as st
import requests
import json
import os
from datetime import datetime
import subprocess  # 🔥 터미널 명령어를 파이썬에서 실행하기 위해 추가!

# --- 웹 페이지 기본 설정 ---
st.set_page_config(page_title="AI 블로그 에디터", page_icon="📝", layout="wide")
st.title("📝 나만의 AI 기술 블로그 에디터")
st.markdown("Ollama(Qwen3:8b)를 활용해 내 코드를 분석하고 깃허브에 원클릭으로 배포합니다.")

# --- 사이드바: 설정 영역 ---
with st.sidebar:
    st.header("⚙️ 설정")
    output_dir = st.text_input("📁 마크다운 저장 폴더 경로", value="./posts")
    st.caption("지정한 폴더가 없으면 알아서 새로 만듭니다!")

# --- 메인 화면: 반으로 나누기 ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 코드 업로드")
    uploaded_file = st.file_uploader("분석할 파이썬 코드를 올려주세요", type=['py'])

    st.subheader("2. 프롬프트 튜닝")
    today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    default_prompt = f"""너는 내 기술 블로그 전속 에디터야. 
아래 코드를 분석하고, 마크다운(Markdown) 형식으로 기술 블로그 초안을 작성해 줘.

[🔥 필수 규칙: 블로그 머리말(Frontmatter) 작성]
응답의 맨 첫 줄에는 반드시 아래와 같은 YAML 형식의 머리말을 포함해야 해.
---
title: "🚀 AI가 분석한 코드 리뷰"
date: {today_date}
tags: [Python, 자동화, 사이드프로젝트]
description: "AI가 자동으로 코드를 분석하고 작성한 포스팅입니다."
---

[본문 작성 규칙]
1. 머리말 작성 후 한 줄 띄우고 본문을 시작할 것.
2. 코드의 핵심 동작 원리를 친절하게 설명할 것.
3. 이모지는 최대한 적게 사용할 것."""

    prompt_input = st.text_area("AI에게 내릴 세부 지시사항", value=default_prompt, height=350)

with col2:
    st.subheader("3. 결과 확인")

    if st.button("🚀 마크다운 생성 시작!", use_container_width=True):
        if uploaded_file is None:
            st.warning("👈 먼저 왼쪽에서 코드를 업로드해주세요!")
        else:
            code_content = uploaded_file.getvalue().decode("utf-8")
            base_name = uploaded_file.name.split('.')[0]

            url = "http://localhost:11434/api/generate"
            full_prompt = f"{prompt_input}\n\n[내 코드]\n```python\n{code_content}\n```"
            payload = {"model": "qwen3:8b", "prompt": full_prompt, "stream": True}

            st.markdown("### ✨ 완성된 초안")


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
                result_text = st.write_stream(stream_data())

                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                output_path = os.path.join(output_dir, f"{base_name}_blog.md")

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result_text)

                st.success(f"✅ 파일 저장 완료: `{output_path}`")

            except Exception as e:
                st.error(f"❌ 통신 에러: {e}")

# =====================================================================
# 🔥 대망의 4단계: 깃허브 자동 배포 파트 (화면 맨 밑에 꽉 차게 배치)
# =====================================================================
st.divider()  # 가로줄 긋기
st.subheader("🚀 4. 깃허브(GitHub) 원클릭 배포")
st.markdown("생성된 마크다운 파일과 업데이트된 코드를 깃허브 저장소로 한 방에 밀어 넣습니다.")

# 커밋 메시지도 UI에서 직접 입력받습니다!
commit_msg = st.text_input("📝 커밋 메시지를 입력하세요", value="docs: 새로운 AI 블로그 포스팅 추가")

if st.button("전 세계로 배포하기 (Git Push) 🌍", type="primary"):  # type="primary"를 주면 버튼이 눈에 띄게 변합니다.
    with st.spinner("GitHub로 코드를 우주선에 태워 보내는 중입니다... 🚀"):
        try:
            # 1. git add . (모든 변경사항 추적)
            subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)

            # 2. git commit (변경사항이 없으면 여기서 에러가 날 수 있으므로 예외 처리)
            try:
                subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                # 'nothing to commit' 메시지가 뜨면 무시하고 넘어감
                if "nothing to commit" in e.stdout or "nothing to commit" in e.stderr:
                    pass
                else:
                    raise e

            # 3. git push (실제 깃허브로 전송!)
            subprocess.run(["git", "push"], check=True, capture_output=True, text=True)

            st.success(f"🎉 성공적으로 GitHub에 배포되었습니다! 잔디가 심어졌습니다 🌱 (커밋 메시지: {commit_msg})")
            st.balloons()  # 스트림릿의 숨겨진 귀여운 축하 애니메이션! 🎈

        except subprocess.CalledProcessError as e:
            st.error(f"❌ Git 명령어 실행 중 에러가 발생했습니다. 터미널 상태를 확인해주세요.\n\n에러 내용: {e.stderr}")
        except Exception as e:
            st.error(f"❌ 알 수 없는 에러가 발생했습니다: {e}")
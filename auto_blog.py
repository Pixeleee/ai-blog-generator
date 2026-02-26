import requests
import json
import os


def generate_blog_post(file_path):
    # 1. 내가 짠 코드 파일 읽어오기
    if not os.path.exists(file_path):
        print(f"오류: {file_path} 파일이 없습니다!")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        code_content = f.read()

    # 2. Ollama API 주소 및 모델 설정 (qwen3:8b 사용!)
    url = "http://localhost:11434/api/generate"

    # 3. 영혼을 갈아 넣은 프롬프트 (여기에 본인의 블로그 스타일을 묘사하세요)
    prompt = f"""
    너는 지금부터 내 IT 기술 블로그의 전속 에디터야. 
    아래 내가 파이썬으로 작성한 '멀티스레드 포트 스캐너' 코드를 분석하고, 
    독자들이 이해하기 쉽게 마크다운(Markdown) 형식으로 기술 블로그 초안을 작성해 줘.

    [규칙]
    1. 제목은 시선을 끄는 매력적인 제목으로 작성할 것.
    2. 코드가 어떤 원리로 동작하는지(특히 멀티스레딩 부분) 친절하게 설명할 것.
    4. 어투는 '~했습니다', '~해볼까요?' 처럼 친근한 존댓말을 사용할 것.

    [내 코드]
    ```python
    {code_content}
    ```
    """

    payload = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False
    }

    print("🚀 Qwen3:8b가 코드를 분석하며 블로그 글을 작성 중입니다... (약 10~30초 소요)")
    response = requests.post(url, json=payload)

    # 4. 결과물을 마크다운 파일로 저장하기
    if response.status_code == 200:
        result_text = response.json()['response']

        with open("blog_draft.md", "w", encoding="utf-8") as f:
            f.write(result_text)

        print("\n✅ 작성 완료! 'blog_draft.md' 파일을 확인해 보세요!")
    else:
        print(f"❌ API 호출 에러: {response.status_code}")


# 실행! (어제 만든 scanner.py를 타겟으로)
generate_blog_post("scanner.py")
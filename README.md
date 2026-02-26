# 🚀 AI-Powered Velog Auto-Publisher

로컬 LLM(Ollama)과 웹 리버스 엔지니어링을 활용한 기술 블로그 자동화 파이프라인 구축 프로젝트입니다.

## 💡 배경 및 목적
개발 과정에서 발생하는 소스코드와 작동 원리를 기술 블로그에 매번 문서화하는 번거로움을 해결하기 위해 개발했습니다. 
보안을 위해 외부 클라우드 AI가 아닌 **로컬 LLM**을 활용하여 코드를 분석하고, 공식 API를 지원하지 않는 **Velog의 통신 규격을 직접 스니핑하여 자동 퍼블리싱**하는 파이프라인을 완성했습니다.

## 🎯 핵심 기능 (Key Features)
* **Local AI 기반 자동 분석:** 소스 코드를 읽고 동작 원리와 핵심 로직(멀티스레딩 등)을 파악하여 마크다운(Markdown) 형식의 블로그 초안을 자동 생성합니다.
* **CLI 인터페이스:** `-f` 옵션으로 분석할 타겟 파일을 동적으로 입력받아 범용적으로 사용할 수 있습니다.
* **Velog 비공식 API 연동:** Chrome DevTools를 활용해 Velog의 숨겨진 GraphQL API를 리버스 엔지니어링하여 브라우저 없이도 포스팅을 업로드합니다.



## 🛠️ 기술 스택 (Tech Stack)
* **Language:** Python 3.x
* **AI / LLM:** Ollama (Qwen3:8b)
* **Network / HTTP:** `requests`, Payload Sniffing, Header Spoofing (User-Agent, Origin 위장)

## 🚧 트러블슈팅 (Troubleshooting)

### Issue: Velog 공식 API의 부재 및 HTTP 400 Bad Request 에러
Velog는 공식적인 글쓰기 API를 제공하지 않아 자동 업로드가 불가능한 상황이었습니다. 브라우저의 쿠키를 탈취해 POST 요청을 보냈으나 `400 Bad Request` 에러가 발생했습니다.

### Solution: 네트워크 패킷 스니핑 및 헤더 위장
1. **GraphQL 쿼리 분석:** 브라우저 개발자 도구의 [Network] 탭을 활용해 출간 버튼 클릭 시 발생하는 `WritePost` Mutation 쿼리를 캡처했습니다.
2. **Payload 재구성:** 단순히 본문만 보내는 것이 아니라, `url_slug`, `short_description` 등 서버가 요구하는 필수 파라미터 규격을 완벽히 파악하여 JSON 페이로드를 조작했습니다.
3. **Header Spoofing:** 봇(Bot) 차단을 우회하기 위해 HTTP 헤더에 `Origin`, `Referer`, `User-Agent`를 크롬 브라우저와 동일하게 세팅하여 서버를 속이는 데 성공했습니다.

## 🚀 사용 방법 (How to Use)

### 1. 환경 설정
```bash
# Python 가상환경 세팅 및 패키지 설치
uv init
uv add requests
2. 토큰 및 권한 설정
보안상 auto_blog.py 내의 my_access_token 변수에 본인의 Velog 세션 쿠키 값(access_token)을 직접 입력해야 작동합니다. (해당 토큰은 외부 유출에 주의하세요!)

3. 실행
터미널에서 분석할 파이썬 파일의 경로를 인자로 넘겨 실행합니다.
'
Bash
uv run auto_blog.py -f [분석할_파일_경로.py]
'

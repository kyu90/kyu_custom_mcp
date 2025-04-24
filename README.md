# MCP 클라이언트

Model Context Protocol(MCP)을 활용한 도구 호출 클라이언트입니다. 다양한 AI 모델과 도구를 쉽게 연결하여 사용할 수 있습니다.

## 목차

- [Model Context Protocol 소개](#model-context-protocol-소개)
- [기능](#기능)
- [아키텍처](#아키텍처)
- [필수 사항](#필수-사항)
- [설치 방법](#설치-방법)
- [실행 방법](#실행-방법)
- [사용 예시](#사용-예시)
- [지원 도구](#지원-도구)
- [확장 방법](#확장-방법)
- [문제 해결](#문제-해결)

## Model Context Protocol 소개

Model Context Protocol(MCP)은 AI 언어 모델(LLM)과 외부 도구/데이터 소스 간의 연결을 표준화하는 개방형 프로토콜입니다. MCP는 AI 모델이 외부 정보나 기능을 안전하고 일관되게 활용할 수 있도록 해주는 소프트웨어용 표준 인터페이스 역할을 합니다.

### MCP의 주요 특징

- **표준화된 통신**: JSON-RPC 2.0 기반 메시지 교환으로 AI와 도구 간 통신 표준화
- **동적 기능 확장**: AI가 필요한 데이터, 기능(도구), 템플릿 등을 필요할 때 외부에서 가져와 활용
- **구조화된 시스템**:
  - **호스트(Host)**: AI 모델을 운영하는 애플리케이션
  - **클라이언트(Client)**: MCP 서버와의 연결 담당 (본 프로젝트)
  - **서버(Server)**: 실제 데이터나 도구를 제공하는 역할
  - **컨텍스트(Context)**: 리소스(데이터), 도구(API/기능), 프롬프트(지침/템플릿) 등

### MCP 활용의 장점

- 다양한 외부 시스템과 통합이 간편해짐
- 동일한 인터페이스로 여러 도구를 활용 가능
- AI 기능을 쉽게 확장하고 외부 서비스와 연결 가능

## 기능

- 다양한 MCP 서버에 연결하여 도구 사용
- 다양한 형식의 도구 호출 구문 파싱 지원 (JSON, XML, 특수 패턴 등)
- Sequential Thinking 및 Perplexity Ask 도구 지원
- 대화형 인터페이스 제공
- 로컬 AI 모델(Ollama)과 연동하여 도구 사용 지원

## 아키텍처

### 주요 컴포넌트

![MCP 클라이언트 아키텍처](https://mermaid.ink/img/pako:eNqNklFrwjAUhf9KuM8K0to62D6IVgURJg62DGQPaXpnCzYNSSJI2X_fTWtna3Ew5OHmnnPu-RI6QKQpQgBTruw7Hg9FyHpQGpuXqRbG4GibTJ7Uo8LzWtdcJ_Okn1KbijThgkqc0wWniqb0eT2YWDvZRFGWZUF-CA7_usO7u8H46e7lbzXn0ioZ4vl5V9nYlZt1RJF3GZRIeQFzJ-M30jGxRrMxZI2I-yrFjCpMYZzCJ5qMGlxtBmPnNmnBnHPOtHUNDDVKH_A_YN19BEO1oJYreRiKFCZoNgEHTmzRTQXf9VCLOevgdq06LdEVK8HVZ_MNJuhUEaMrzLvTQBrWLLRtO4_KSrGQlY9xXBaGFDQRbKkVCQR7cZq4_-oDUXQl)

1. **MCPClient**: 핵심 클래스로, 다양한 서버 연결 및 도구 호출 관리
2. **도구 확장(Extensions)**: 특정 도구를 위한 확장 기능 제공
   - `SequentialThinkingExtension`: 단계별 추론 기능
   - `PerplexityExtension`: 웹 검색 기능
3. **MCP 서버**: 다양한 도구를 제공하는 서버 컴포넌트
   - 파일 관리자 서버: 파일 시스템 조작 도구 제공
   - Sequential Thinking 서버: 단계별 사고 처리 도구
   - Perplexity Ask 서버: 웹 검색 도구

### 소프트웨어 디자인

- **다중 서버 연결**: 여러 MCP 서버에 동시 연결하여 다양한 도구 사용
- **확장 가능한 구조**: 새로운 도구를 쉽게 추가할 수 있는 플러그인 아키텍처
- **비동기 처리**: `asyncio`를 사용한 비동기 도구 호출 처리
- **도구 확장 메커니즘**: 메서드 패치를 통한 도구별 맞춤 처리 지원

### 데이터 흐름

1. 사용자 쿼리 입력
2. AI 모델(Ollama)에 쿼리 전송
3. AI 모델이 도구 호출 명령 생성
4. 클라이언트가 도구 호출 명령 파싱
5. 적절한 MCP 서버에 도구 호출 요청 전송
6. 도구 실행 결과 수신
7. 결과를 AI 모델에 전달하여 최종 응답 생성
8. 사용자에게 결과 표시

## 필수 사항

- Python 3.8 이상
- Node.js 및 NPM (NPX 명령어 사용을 위함)
- Ollama (로컬 AI 모델 실행 도구)

## 설치 방법

### 1. 리포지토리 클론

```bash
git clone https://github.com/yourusername/mcp-client.git
cd mcp-client
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. Ollama 설치 및 모델 다운로드

1. [Ollama 설치](https://ollama.com/download)
2. 필요한 모델 다운로드:
```bash
ollama pull MFDoom/deepseek-r1-tool-calling:14b
```

### 4. Node.js 설치 (필요한 경우)

- [Node.js 다운로드](https://nodejs.org/)

### 5. 환경 변수 설정 (선택 사항)

`.env` 파일에 필요한 API 키 등을 설정:

```
PERPLEXITY_API_KEY=your_api_key
```

## 실행 방법

### 기본 실행 (모든 서버 연결)

```bash
python client.py
```

### 특정 서버만 연결

```bash
python client.py --server=file_manager
```

### 스크립트로 실행

```bash
chmod +x run_client.sh
./run_client.sh
```

### 상세 로그 출력

```bash
python client.py --verbose
```
또는
```bash
VERBOSE=true ./run_client.sh
```

## 사용 예시

클라이언트를 실행한 후 다음과 같이 쿼리를 입력할 수 있습니다:

```
쿼리: 현재 디렉토리의 파일 목록을 보여줘
```

AI 모델이 해당 쿼리를 처리하고 필요한 도구(예: get_local_file_list)를 호출하여 결과를 보여줍니다.

```
쿼리: 피보나치 수열의 첫 10개 항목을 계산하는 과정을 단계별로 설명해줘
```

Sequential Thinking 도구를 사용하여 단계별로 사고 과정을 보여줍니다.

```
쿼리: 최신 AI 기술 동향에 대해 알려줘
```

Perplexity API를 통해 웹 검색 결과를 바탕으로 정보를 제공합니다.

## 지원 도구

현재 다음 도구들을 지원합니다:

- **file_manager**: 파일 시스템 조작 (커스텀 MCP 서버 구현 예시)
  - `get_local_file_list`: 디렉토리 내용 조회
  - `write_text_to_file`: 파일 작성
  - `read_file_content`: 파일 내용 읽기

- **sequential-thinking**: 단계별 추론 기능
  - `sequentialthinking`: 복잡한 문제를 단계별로 사고

- **perplexity-ask**: 웹 검색 기능
  - `perplexity_ask`: 최신 정보를 웹에서 검색

- **everything**: 다양한 유틸리티 도구

## 확장 방법

### 새로운 MCP 서버 추가

1. 새로운 MCP 서버 코드 작성 (Python 또는 JavaScript)
2. `mcp-servers-config.json`에 서버 정보 추가:

```json
"new_server": {
    "command": "python",
    "args": [
        "new_server.py"
    ]
}
```

### 커스텀 MCP 서버 예시

가장 기본적인 커스텀 서버 구현 예시로 `mcp_server_file_manager.py`를 제공합니다. 이 파일은 Python에서 FastMCP를 사용하여 파일 시스템 처리 기능을 제공하는 서버 구현을 보여줍니다. 이를 참고하여 자신만의 커스텀 MCP 서버를 구현할 수 있습니다.

### 새로운 도구 확장 추가

1. 새로운 확장 클래스 작성 (예: `new_tool_extension.py`)
2. `client.py`의 `main` 함수에 확장 로드 코드 추가

## 문제 해결

### 서버 연결 실패

- 해당 서버가 올바르게 설치되어 있는지 확인
- NPX 명령이 작동하는지 확인
- 환경 변수가 올바르게 설정되어 있는지 확인

### 도구 호출 오류

- 모델이 올바른 형식으로 도구 호출 명령을 생성하는지 확인
- 필요한 매개변수가 모두 제공되었는지 확인
- `--verbose` 플래그를 사용하여 상세 로그 확인

### Ollama 모델 문제

- 필요한 모델이 설치되어 있는지 확인: `ollama list`
- Ollama 서비스가 실행 중인지 확인
# GitHub 리포지토리 생성 및 푸시 방법

이 문서는 MCP 클라이언트 코드를 GitHub에 푸시하는 방법을 안내합니다.

## 1. Git 초기화

현재 디렉토리에서 다음 명령어를 실행하여 Git 리포지토리를 초기화합니다.

```bash
git init
```

## 2. 파일 스테이징

모든 파일을 스테이징 영역에 추가합니다.

```bash
git add .
```

## 3. 첫 번째 커밋 생성

변경 사항을 커밋합니다.

```bash
git commit -m "Initial commit: MCP 클라이언트 코드 추가"
```

## 4. GitHub 리포지토리 생성

1. GitHub 웹사이트(github.com)에 로그인합니다.
2. 우측 상단의 '+' 버튼을 클릭하고 'New repository'를 선택합니다.
3. 리포지토리 이름을 'mcp-client'(또는 원하는 이름)으로 설정합니다.
4. 필요에 따라 설명을 추가하고 공개/비공개 설정을 선택합니다.
5. 'Create repository' 버튼을 클릭합니다.

## 5. 리모트 리포지토리 추가

GitHub에서 제공하는 URL을 사용하여 원격 리포지토리를 추가합니다.

```bash
git remote add origin https://github.com/yourusername/mcp-client.git
```

## 6. 로컬 변경 사항을 GitHub에 푸시

로컬 변경 사항을 GitHub 리포지토리로 푸시합니다.

```bash
git push -u origin main
```

> 참고: Git 버전 및 설정에 따라 기본 브랜치 이름이 'main' 대신 'master'일 수 있습니다. 
> 그런 경우 `git push -u origin master` 명령을 사용하세요.

## 7. 추가 사용자 설정 (선택 사항)

Git 사용자 정보를 아직 설정하지 않았다면, 다음 명령어로 설정할 수 있습니다.

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 8. 인증 정보 설정 (필요한 경우)

GitHub에 푸시할 때 인증이 필요합니다. 최근에는 개인 액세스 토큰(PAT)을 사용하는 것이 권장됩니다.

1. GitHub 웹사이트에서 Settings > Developer settings > Personal access tokens 메뉴로 이동합니다.
2. 'Generate new token'을 클릭하고 필요한 권한을 선택합니다(최소한 'repo' 권한 필요).
3. 생성된 토큰을 안전한 곳에 보관하고, 푸시할 때 비밀번호 대신 사용합니다.

## 9. SSH 키 설정 (더 안전한 방법)

반복적인 인증을 피하기 위해 SSH 키를 설정하는 것이 좋습니다.

1. SSH 키 생성:
```bash
ssh-keygen -t ed25519 -C "your.email@example.com"
```

2. 공개 키를 GitHub 계정에 추가:
   - Settings > SSH and GPG keys > New SSH key

3. 리모트 URL을 SSH 형식으로 변경:
```bash
git remote set-url origin git@github.com:yourusername/mcp-client.git
```

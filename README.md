# 💬 Chatbot Project 개발 가이드(임시)

1. 본 문서는 **Chatbot Project**의 환경 구성, 개발 흐름, 그리고 코드 관리 규칙을 안내합니다.
2. **나중에 수정합니다. 일단 임시용으로 사용**

---

## 🏗️ 환경 구성 및 배포 전략

### 배포 환경

| 환경 | 용도 | 상태 |
| :--- | :--- | :--- |
| **`prod`** | Production 환경 (실 서비스) | **현재 사용하지 않음** |
| **`stg`** | Staging 환경 (배포 전 최종 확인) | **AI 환경 변수 주입 에러 수정 중** |

### 개발 및 배포 흐름

1.  **로컬 개발**: 로컬 환경에서 기능 개발 및 단위 테스트를 진행합니다.
2.  **Staging 반영**: 개발 완료 후 **`stg` 브랜치**로 푸시($\text{push}$)하여 Staging 환경에서 최종 통합 테스트를 진행합니다.
3.  **Production 반영**: Staging 환경에서의 검증이 완료되면 `prod` 환경으로 푸시(배포)를 진행합니다.

---

## 💻 로컬 개발 환경 설정

로컬에서 개발을 시작하기 위한 필수 환경 및 준비 사항입니다.

### 1. 코드 준비 및 환경 변수 (`.env` 파일) 🔑

* **코드**: 깃허브의 최신화된 코드를 가져와 개발을 시작합니다.
* **환경 변수**: 프로젝트 실행에 필요한 환경 변수 파일은 **담당자(팀장)에게 별도 요청**하여 받아야 합니다.
    * **AI 서비스**의 환경 변수 파일 (예: `apikey.env`)은 **AI 폴더** 내에 위치해야 합니다.

### 2. 개발 환경 요구사항

* **운영체제**: **Linux** 환경에서 개발해야 합니다.
* **컨테이너**: **Docker**를 사용하여 개발 환경을 구축하고 실행합니다.
* **윈도우에서 할 수 있으면 해도 되는데, 안 해봐서 되는지 모르겠어요..**

---

## 🐳 Docker 개발 환경 구축

로컬 환경 구성을 위한 도커 명령어입니다. 네트워크는 프로젝트 전체에서 공유됩니다.

### 🛠️ 네트워크 설정

| 목적 | 명령어 |
| :--- | :--- |
| **네트워크 생성** | `docker network create chatbot-network` |

### 🚀 애플리케이션 실행

각 영역별로 이미지를 빌드하고 컨테이너를 실행합니다. **AI 실행 시에는 `--env-file apikey.env` 옵션을 사용해야 합니다.**

| 영역 | 이미지 빌드 명령어 | **컨테이너 실행 명령어** | 포트 |
| :--- | :--- | :--- | :--- |
| **Frontend** | `docker build -t chatbot-frontend:latest .` | `docker run -d -p 5173:80 --network chatbot-network --name chatbot-frontend-container chatbot-frontend:latest` | `5173` |
| **Backend** | `docker build -t chatbot-backend:latest .` | `docker run -d -p 8080:8000 --network chatbot-network --name chatbot-backend-container chatbot-backend:latest` | `8080` |
| **AI** | `docker build -t chatbot-ai:latest .` | `docker run -d -p 3000:8000 --network chatbot-network --name chatbot-ai-container --env-file apikey.env chatbot-ai:latest` | `3000` |

### 🧹 환경 정리 (전체 삭제 명령어)

| 목적 | 명령어 |
| :--- | :--- |
| **컨테이너 전체 정지** | `docker stop -f $(docker ps -aq)` |
| **컨테이너 전체 삭제** | `docker rm -f $(docker ps -aq)` |
| **도커 이미지 전체 삭제** | `docker rmi -f $(docker images -aq)` |
| **도커 네트워크 삭제** | `docker network rm chatbot-network` |

> **주의**: 위 명령들은 실행 중인 **모든** 컨테이너, 이미지, 네트워크를 삭제합니다. 필요한 경우 개별 지정하여 삭제하세요.

---

## 🌳 Git & Branch 관리 가이드

### 1. 개발 영역 분리

* **`admin`**: Frontend, Backend (각각 개발을 진행합니다.)

### 2. 브랜치 사용 규칙

* **`main` 브랜치에 직접 푸시하지 말아주세요.**
* 모든 개발은 **별도의 Feature 브랜치**를 생성하여 진행해야 합니다.

### 3. 브랜치 이름 형식

브랜치 이름은 다음 **`?-?-?`** 형식으로 통일해주세요.
* **예시**: `stg-backend-login` (Staging 환경, Backend 영역의 사용자 로그인 기능 개발)

| 섹션 | 의미 | 예시 |
| :--- | :--- | :--- |
| 1st | **타겟 환경** | `stg`, `prod` |
| 2nd | **개발 영역** | `frontend`, `backend`, `ai` |
| 3rd | **기능 요약** | `feature-name`, `bugfix-name` |

---

## 📢 협업 가이드라인

### 1. 본인 영역 책임

* 각 팀원은 **본인이 맡은 영역(Frontend, Backend, AI)** 내의 코드만 개발 및 수정해주세요.

### 2. 영향 범위 공유

* **타 영역에 영향을 끼치는 코드** (예: **API 명세 변경**, DB 스키마 수정 등)를 작성했을 경우, **반드시 관련 팀원에게 사전에 공유**해주세요.
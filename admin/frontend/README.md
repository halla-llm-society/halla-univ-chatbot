# 한라 쳇봇 프론트 레파지토리 입니다
**Vite**를 이용한 **React** 기반으로 구성되어 있으며, 코드의 **재사용성**과 **유지보수성**을 높이기 위해 아래와 같은 구조로 설계되었습니다.

## 참가자
<table>
 <tr>
    <td align="center"><a href="https://github.com/pwk0131"><img src="https://avatars.githubusercontent.com/pwk0131" width="200px;" alt=""></a></td>
    <td align="center"><a href="https://github.com/jiman0919"><img src="https://avatars.githubusercontent.com/jiman0919" width="200px;" alt=""></a></td>
    <td align="center"><a href="https://github.com/Unyuwaffle"><img src="https://avatars.githubusercontent.com/Unyuwaffle" width="200px;" alt=""></a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/pwk0131"><b>박웅기</b></a></td>
    <td align="center"><a href="https://github.com/jiman0919"><b>이지만</b></a></td>
    <td align="center"><a href="https://github.com/Unyuwaffle"><b>김범섭</b></a></td>
  </tr>
</table>

## **1. 📂 `src` : 핵심 코드 폴더**

모든 개발 작업은 `src` 폴더 안에서 이루어집니다. 주요 폴더들의 역할은 다음과 같습니다.

- **`components`**: 버튼, 헤더, 푸터처럼 여러 곳에서 **재사용될 수 있는 작은 UI 조각(컴포넌트)**들을 모아두는 곳입니다.
    - **`common`**: `Header`, `Footer`, `Sidemenu` 등 모든 페이지에서 공통적으로 사용되는 컴포넌트들이 여기에 위치합니다.
    
- **`layouts`**: 페이지들의 **전체적인 틀(레이아웃)**을 정의합니다. 예를 들어 `MainLayout.jsx`는 모든 페이지에 공통적으로 들어가는 `Header`, `Sidemenu`, `Footer`를 포함하고, 실제 페이지 내용이 들어갈 자리를 마련해 줍니다.

- **`pages`**: 사용자가 브라우저에서 보게 될 **개별 페이지 단위의 컴포넌트**들을 관리합니다. 각 페이지는 `layouts`가 제공하는 틀 안에서 자신만의 콘텐츠를 보여줍니다.
    - `UserQueryDataAnalysis.jsx` : 사용자 질의 데이터 분석 페이지
    - `UserStatistics.jsx` : 사용자 통계 확인 페이지
    - 등등 … 총 4개의 페이지 있습니다.
    
- **`router`**: 사용자가 접속하는 **URL 주소에 따라 어떤 페이지를 보여줄지 결정**하는 '교통정리' 역할을 합니다. `react-router-dom` 라이브러리를 사용해 페이지 간의 이동을 관리합니다.

- **`services`**: 백엔드 서버와 **API 통신을 하는 함수**들을 모아두는 곳입니다. `axios`를 사용하여 데이터를 요청하고 받아오는 로직이 `api.js` 파일에 들어있습니다.

- **`assets`**: 이미지, 폰트 등 코드 파일이 아닌 **정적 자원**들을 보관합니다.

## **2. ⚙️ 코드의 흐름**

사용자가 웹사이트에 접속했을 때 코드가 동작하는 순서는 다음과 같습니다.

1. **`main.jsx`** 파일이 가장 먼저 실행되어 리액트 앱의 최상위 컴포넌트인 **`App.jsx`*를 불러옵니다.
2. *`App.jsx`*는 별다른 UI 없이 오직 **`router/Router.jsx`*를 실행시켜 어떤 페이지를 보여줄지 결정하도록 합니다.
3. *`Router.jsx`*는 현재 URL을 확인하고, 해당 URL에 맞는 페이지를 **`layouts/MainLayout.jsx`*라는 '틀' 안에 넣어 화면에 보여줍니다.
4. 결과적으로 사용자는 `Header`, `Sidemenu`, `Footer`가 모두 갖춰진 상태에서 해당 페이지의 고유한 콘텐츠를 보게 됩니다.

## **2. ✅ 요약 **

```
my-react-app/
├── public/
├── src/
│   ├── 📂 assets/
│   │   └── images/
│   │       └── logo.png
│   ├── 📂 components/
│   │   ├── common/
│   │   │   ├── Footer.jsx
│   │   │   ├── Header.jsx
│   │   │   └── Sidemenu.jsx
│   │   └── styles/
│   │       ├── Footer.module.css
│   │       ├── Header.module.css
│   │       └── Sidemenu.module.css
│   ├── 📂 layouts/
│   │   ├── MainLayout.jsx
│   │   └── MainLayout.module.css
│   ├── 📂 pages/
│   │   ├── styles/
│   │   │   └── UserQueryDataAnalysis.module.css
│   │   ├── PageLayout.module.css
│   │   ├── TrafficInquiry.jsx
│   │   ├── UsageCostInquiry.jsx
│   │   ├── UserQueryDataAnalysis.jsx
│   │   └── UserStatistics.jsx
│   ├── 📂 router/
│   │   └── Router.jsx
│   ├── 📂 services/
│   │   └── api.js
│   ├── App.jsx
│   ├── index.css
│   └── main.jsx
│
├── .gitignore
├── eslint.config.js
├── index.html
├── package-lock.json
├── package.json
├── README.md
└── vite.config.js
```

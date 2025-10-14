// 언어
let language = "KOR";

// DOM 요소 선택
const chatbotContainer = document.getElementById("chatbot-container");
const chatbot = document.getElementById("chatbot");
const toggleBtn = document.getElementById("chatbot-toggle-btn");

const infoModal = document.getElementById("info-modal");
const resetModal = document.getElementById("reset-modal");

const langBtn = document.getElementById("lang-btn");
const infoBtn = document.getElementById("info-btn");
const resetBtn = document.getElementById("reset-btn");
const closeBtn = document.getElementById("close-btn");

const langDropdown = document.getElementById('lang-dropdown');
const langList = document.getElementById('lang-list');

const sendBtn = document.getElementById("send-btn");
const userInput = document.getElementById("user-input");
const messages = document.getElementById("chat-messages");


// 딜레이
const delay = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms));
}


// 초기화 및 기본 이벤트
window.addEventListener('DOMContentLoaded', () => {
  sendDefaultMesage();
  setModal();
  setUserInputPlaceHolder();

  setChatbotExpanded();
  setLangDropdown();
  setInputAndSend();
});


// 초기 메시지 생성
const sendDefaultMesage = () => {
  let defaultMsgElement = document.createElement('div');

  defaultMsgElement.innerHTML = `
  <div class="bot-message-container" id="default-message">
    <img class="bot-avatar" src="assets/bot-avatar.png" alt="bot" />
    <div class="message bot">${defaultMsgDict[language]}</div>
  </div>
  `;

  messages.appendChild(defaultMsgElement);
  messages.scrollTop = messages.scrollHeight;
};


// 모달 설정
const setModal = () => {
  setInfoModal();
  setResetModal();
}


// 정보 모달 설정
const setInfoModal = () => {
  infoModal.innerHTML = infoModalDict[language];
  let infoConfirmBtn = document.getElementById("confirm-info-btn");

  infoBtn.addEventListener("click", () => {   // 모달 열기
    infoModal.style.display = "flex";
    infoModal.classList.remove('fade-out');
    infoModal.classList.add('fade-in');
  });

  infoConfirmBtn.addEventListener("click", () => {   // 모달 닫기
    infoModal.classList.remove('fade-in');
    infoModal.classList.add('fade-out');
  });

  infoModal.addEventListener('animationend', (e) => {   // 모달 애니메이션 처리
    if (e.animationName === 'fadeOut') {
      infoModal.style.display = 'none';
      infoModal.classList.remove('fade-out');
    }
  });
}


// 초기화 모달 설정
const setResetModal = () => {
  resetModal.innerHTML = resetModalDict[language];
  let resetCancelBtn = document.getElementById("cancel-reset-btn");
  let resetConfirmBtn = document.getElementById("confirm-reset-btn");

  resetBtn.addEventListener("click", () => {   // 모달 열기
    resetModal.style.display = "flex";
    resetModal.classList.remove('fade-out');
    resetModal.classList.add('fade-in');
  });

  resetCancelBtn.addEventListener("click", () => {  // 초기화 취소
    resetModal.classList.remove('fade-in');
    resetModal.classList.add('fade-out');
  });

  resetConfirmBtn.addEventListener("click", () => {   // 초기화 확인
    let botMessages = document.querySelectorAll('.bot-message-container');
    let userMessages = document.querySelectorAll('.user');

    botMessages.forEach(msg => msg.remove());
    userMessages.forEach(msg => msg.remove());
    sendDefaultMesage();

    resetModal.classList.remove('fade-in');
    resetModal.classList.add('fade-out');
  });

  resetModal.addEventListener('animationend', (e) => {   // 모달 애니메이션 처리
    if (e.animationName === 'fadeOut') {
      resetModal.style.display = 'none';
      resetModal.classList.remove('fade-out');
    }
  });
}


// user-input placeholder 처리
const setUserInputPlaceHolder = () => {
  document.getElementById("user-input").placeholder = userInputPlaceHolderDict[language];
}


// 챗봇 UI 제어
const setChatbotExpanded = () => {
  toggleBtn.addEventListener("click", async () => {   // 챗봇 열기
    chatbotContainer.classList.add("expanded");
  });

  closeBtn.addEventListener("click", async () => {   // 챗봇 닫기
    chatbotContainer.classList.remove("expanded");
  });

}


// 언어 드롭다운
const setLangDropdown = () => {
  const toggleLangDropdown = (e) => {   // 드롭다운 토글 함수
    e.stopPropagation();

    if (langDropdown.classList.contains('fade-in')) {
      langDropdown.classList.remove('fade-in');
      langDropdown.classList.add('fade-out');

      setTimeout(() => {
        langDropdown.style.display = 'none';
        langDropdown.classList.remove('fade-out');
      }, 300);
    }
    else {
      langDropdown.style.display = 'block';
      langDropdown.classList.add('fade-in');
    }
  }

  document.addEventListener('click', (e) => {   // 외부 클릭 시 드롭다운 닫기
    if (!langDropdown.contains(e.target) && !langBtn.contains(e.target)) {  

      if (langDropdown.classList.contains('fade-in')) {
        langDropdown.classList.remove('fade-in');
        langDropdown.classList.add('fade-out');

        setTimeout(() => {
          langDropdown.style.display = 'none';
          langDropdown.classList.remove('fade-out');
        }, 300);
      }
    }
  });

  langList.querySelectorAll('li').forEach((item) => {   // 언어 선택 시 드롭다운 닫기 및 값 처리
    item.addEventListener('click', () => {
      let preLang = language;
      language = item.dataset.value;

      langDropdown.classList.remove('fade-in');
      langDropdown.classList.add('fade-out');

      setTimeout(() => {
        langDropdown.style.display = 'none';
        langDropdown.classList.remove('fade-out');
      }, 300);

      if (preLang !== language) {  
        if (!document.querySelector('.message.user')) {
          document.querySelector('.bot-message-container').remove(); 
        }

        sendDefaultMesage();
        setModal();
        setUserInputPlaceHolder();
      }
    });
  });

  langBtn.addEventListener('click', toggleLangDropdown);   // lang-btn 클릭 시 드롭다운 토글
}


// input, send etc...
const setInputAndSend = () => {
  userInput.addEventListener('input', () => {   // 텍스트 입력란 크기 조정
    let lineHeight = parseInt(getComputedStyle(userInput).lineHeight, 10);
    let currentRows = Math.floor(userInput.scrollHeight / lineHeight);

    if (currentRows > 2) {
      userInput.style.height = '45px';
      userInput.style.height = userInput.scrollHeight + 'px';
    }
  });

  // 메시지 전송 기능
  // 전송 버튼 및 Enter 키 처리
  sendBtn.addEventListener("click", () => {
    if (sendBtn.disabled) {
      return;
    }

    sendMessage()
  });

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();

      if (sendBtn.disabled) {
        return;
      }

      sendMessage();
    }
  });
}


// HTML 이스케이프 함수
const escapeHTML = (str) => {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
};


// 메시지 전송
const sendMessage = async () => {
  let userMsg = userInput.value.trim();

  if (!userMsg) {
    userInput.style.height = '45px';
    userInput.value = "";
    return;
  }
  else {
    userMsg = escapeHTML(userMsg).replace(/\n/g, '<br>');
  }

  sendBtn.disabled = true;
  langBtn.disabled = true; // [추가] 언어 변경 버튼 비활성화
  appendUserMessage(userMsg);
  await delay(1000);
  await appendBotMessage(userMsg);
  sendBtn.disabled = false;
  langBtn.disabled = false; // [추가] 언어 변경 버튼 다시 활성화
}


// 유저 메시지 추가
const appendUserMessage = (userMsg) => {
  // 입력창 초기화
  userInput.value = "";
  userInput.style.height = '45px';

  // 메시지 element 생성
  const msgElement = document.createElement("div");
  msgElement.innerHTML = `<div class="message user animate">${userMsg}</div>`;

  messages.appendChild(msgElement);
  messages.scrollTop = messages.scrollHeight;
}


const appendBotMessage = async (userMsg) => {
  // 응답 생성 메시지 띄우기
  let msgElement = document.createElement("div");
  let waitMsg = `<span class="wait-msg">${waitMsgDict[language]}</span><span class="loader"></span>`;

  msgElement.innerHTML = `
    <div class="bot-message-container animate">
      <img class="bot-avatar" src="assets/bot-avatar.png" alt="bot" />
      <div class="message bot">${waitMsg}</div>
    </div>
  `;

  messages.appendChild(msgElement);
  messages.scrollTop = messages.scrollHeight;

  const botMsgElement = msgElement.querySelector(".message.bot");   

  // 10초 단위로 wait message 변경
  let elapsedTime = 1;
  let messagesForLang = waitMsgDict[language];
  botMsgElement.innerHTML = `<span class="wait-msg">${messagesForLang[0]}</span><span class="loader"></span>`;

  const waitMessageInterval = setInterval(() => {
    messagesForLang = waitMsgDict[language];
    botMsgElement.innerHTML = `<span class="wait-msg">${messagesForLang[Math.min(elapsedTime, messagesForLang.length - 1)]}</span><span class="loader"></span>`;
    elapsedTime++;
  }, 10000);

  try {
    let baseURL = "";

    if (window.location.hostname.includes("localhost")) {
      baseURL = "http://localhost:8080";
    } 
    else if (window.location.pathname.startsWith("/stg")) {
      baseURL = "https://halla-chatbot.com/stg";
    } 
    else {
      baseURL = "https://halla-chatbot.com";
    }

    // request
    const resp = await fetch(`${baseURL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ "message": userMsg, "language": language })
    });

    // response
    let botMsg = "";
    const reader = resp.body.getReader();
    const decoder = new TextDecoder("utf-8");

    while (true) {
      const { done, value } = await reader.read();
      clearInterval(waitMessageInterval); 

      if (done) {
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      const characters = chunk.split('');

      for (const char of characters) {
        botMsg += char;
        botMsgElement.innerHTML = DOMPurify.sanitize(marked.parse(botMsg));
        messages.scrollTop = messages.scrollHeight;
        await new Promise(r => setTimeout(r, 10)); 
      }
    }
  } 
  catch (error) {
    botMsgElement.innerHTML = `❌ ${errorMsgDict[language]}:` + error.message;
  }

  messages.scrollTop = messages.scrollHeight;
};
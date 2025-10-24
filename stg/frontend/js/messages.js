// 메시지 관련 함수

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


// user-input placeholder 처리
const setUserInputPlaceHolder = () => {
    document.getElementById("user-input").placeholder = userInputPlaceHolderDict[language];
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


// 메시지 전송
const sendMessage = async () => {
    let userMsg = userInput.value.trim();

    if (!userMsg) {
        userInput.style.height = '45px';
        userInput.value = "";
        return;
    }
    else {
        // XSS 방지
        userMsg = escapeHTML(userMsg).replace(/\n/g, '<br>');
    }

    sendBtn.disabled = true;
    langBtn.disabled = true;
    appendUserMessage(userMsg);

    await delay(1000);
    await appendBotMessage(userMsg);

    sendBtn.disabled = false;
    langBtn.disabled = false;
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
                botMsgElement.innerHTML = escapeHTML(botMsg).replace(/\n/g, "<br>");
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
// 메시지 관련 함수

// 쿠키 가져오기
function getCookie(name) {
    const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? v[2] : null;
}
// 쿠키 설정하기
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}
// 쿠키 삭제하기
function deleteCookie(name) {
    document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:01 GMT; path=/;';
}

// 화면에 메시지 그리기
const renderMessage = (role, text) => {
    const msgDiv = document.createElement("div");

    const safeText = text.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");

    if (role === "user") {
        msgDiv.innerHTML = `<div class="message user animate">${safeText}</div>`;
    } else {
        msgDiv.innerHTML = `
            <div class="bot-message-container animate">
                <img class="bot-avatar" src="assets/bot-avatar.png" alt="bot" />
                <div class="message bot">${safeText}</div>
            </div>`;
    }
    messages.appendChild(msgDiv);
};

// 초기화 및 이전 대화 불러오기
window.addEventListener("DOMContentLoaded", async () => {
    setUserInputPlaceHolder();
    setInputAndSend();

    const storedId = getCookie("chatId");
    let hasHistory = false;

    if (storedId) {
        try {
            const res = await fetch(`${window.baseURL}/api/chat/history`, {
                credentials: 'include' 
            });
            if (res.ok) {
                const history = await res.json();
                
                if (history && history.length > 0) {

                    sendDefaultMessage();
                    
                    history.forEach(msg => {
                        renderMessage(msg.role, msg.content);
                    });
                    messages.scrollTop = messages.scrollHeight;
                    hasHistory = true;
                }
            }
        } catch (e) {
            console.error("History load failed:", e);
        }
    }

    if (!hasHistory) {
        sendDefaultMessage();
    }
});



// 초기 메시지 생성
const sendDefaultMessage = () => {
    let defaultMsgElement = document.createElement('div');

    defaultMsgElement.innerHTML = `
  <div class="bot-message-container animate" id="default-message">
    <img class="bot-avatar" src="assets/bot-avatar.png" alt="bot" />
    <div class="message bot">${defaultMsgDict[language]}</div>
  </div>
  `;

    messages.appendChild(defaultMsgElement);
    messages.scrollTop = messages.scrollHeight;
};


// user-input placeholder 처리
const setUserInputPlaceHolder = () => {
    const input = document.getElementById("user-input");
    if(input) input.placeholder = userInputPlaceHolderDict[language];
}


// input, send etc...
const setInputAndSend = () => {
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn"); 

    if (!userInput || !sendBtn) return;

    userInput.addEventListener('input', () => {  // 텍스트 입력란 크기 조정
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

// 메시지 전송
const sendMessage = async () => {
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const langBtn = document.getElementById("lang-btn"); // ID 확인 필요

    let userMsg = userInput.value.trim();
    if (!userMsg) {
        userInput.style.height = '45px';
        userInput.value = "";
        return;
    } else {
        userMsg = escapeHTML(userMsg).replace(/\n/g, '<br>');
    }

    sendBtn.disabled = true;
    if(langBtn) langBtn.disabled = true;
    isBotResponding = true;
    appendUserMessage(userMsg);

    await delay(500);
    await appendBotMessage(userMsg);

    sendBtn.disabled = false;
    if(langBtn) langBtn.disabled = false;
    isBotResponding = false;
}


// 메시지 전송
const appendBotMessage = async (userMsg) => {
    const botMsgElement = appendWaitMessage();
    const waitMessageInterval = initWaitMessageInterval(botMsgElement);

    try {
        // request
        const resp = await fetch(`${window.baseURL}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: 'include',
            body: JSON.stringify({ "user_input": userMsg, "language": language })
        });

        // response
        let botMsg = "";
        const reader = resp.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { done, value } = await reader.read();
            clearInterval(waitMessageInterval);

            if (done) {
                break;
            }

            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;

                try {
                    const json = JSON.parse(line);

                    // A. 답변 텍스트 (타이핑 효과)
                    if (json.type === "delta") {
                        const chunkContent = json.content;
                        for (const char of chunkContent) {
                            botMsg += char;
                            botMsgElement.innerHTML = escapeHTML(botMsg).replace(/\n/g, "<br>");
                            messages.scrollTop = messages.scrollHeight;
                            await new Promise(r => setTimeout(r, 10)); // 10ms 딜레이
                        }
                    } 
                    // B. 에러 메시지
                    else if (json.type === "error") {
                        botMsgElement.innerHTML += `<br><span class="error-msg" style="color:red;">⚠️ ${json.message}</span>`;
                    }
                    // C. 메타데이터 (ID 저장)
                    else if (json.type === "metadata") {
                        
                        if (json.data && json.data.chatId) {
                            setCookie("chatId", json.data.chatId, 1);
                            
                        }
                    }
                } catch (e) {
                    console.error("Stream parse error:", e);
                }
            }   

            
        }

        
    }
    catch (error) {
        clearInterval(waitMessageInterval);
        botMsgElement.innerHTML = `❌ ${errorMsgDict[language]}:` + error.message;
    }
    
    messages.scrollTop = messages.scrollHeight;
};


// 응답 생성 전 대기 메시지 추가
const appendWaitMessage = () => {
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

    return msgElement.querySelector(".message.bot");
}


// 10초 단위로 대기 메시지 변경
const initWaitMessageInterval = (botMsgElement) => {
    let elapsedTime = 1;
    let messagesForLang = waitMsgDict[language];
    botMsgElement.innerHTML = `<span class="wait-msg">${messagesForLang[0]}</span><span class="loader"></span>`;

    const waitMessageInterval = setInterval(() => {
        messagesForLang = waitMsgDict[language];
        botMsgElement.innerHTML = `<span class="wait-msg">${messagesForLang[Math.min(elapsedTime, messagesForLang.length - 1)]}</span><span class="loader"></span>`;
        elapsedTime++;
    }, 10000);

    return waitMessageInterval;
}


// 설문조사 메시지 추가
const appendSurveyMessage = (surveyMsg) => {
    let msgElement = document.createElement("div");
    
    msgElement.innerHTML = `
    <div class="bot-message-container animate">
        <img class="bot-avatar" src="assets/bot-avatar.png" alt="bot" />
        <div class="message bot">${surveyMsg}</div> 
    </div>
    `;

    messages.appendChild(msgElement);
    messages.scrollTop = messages.scrollHeight;
}
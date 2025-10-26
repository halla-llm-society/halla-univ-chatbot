// 사용자(session storage) 관련 함수


const setUserInfo = () => {
    sessionStorage.setItem("survey", "false");
    sessionStorage.setItem("message_history", JSON.stringify([]));
}


const getUserMessageHistory = () => {
    return JSON.parse(sessionStorage.getItem("message_history"));
}


const updateMsgHistory = (userMsg, botMsg) => {
    let messageHistory = JSON.parse(sessionStorage.getItem("message_history"));

    const newUserMsg = { "role": "user", "content": userMsg };
    const newBotMsg = { "role": "assistant", "content": botMsg };

    messageHistory.push(newUserMsg);
    messageHistory.push(newBotMsg);

    sessionStorage.setItem("message_history", JSON.stringify(messageHistory));
}
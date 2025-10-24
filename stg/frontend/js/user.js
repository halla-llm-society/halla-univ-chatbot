// 사용자(session storage) 관련 함수


const updateUserInfo = (userMsg) => {
    // 세션 스토리지에 정보가 없으면 새로 생성
    if (sessionStorage.getItem("survey") == null) {
        sessionStorage.setItem("survey", "false");
    }

    const storedMessages = sessionStorage.getItem("userMessages");
    let userMessages = storedMessages ? JSON.parse(storedMessages) : [];

    const newMessage = { num: userMessages.length + 1, message: userMsg };
    userMessages.push(newMessage);

    sessionStorage.setItem("userMessages", JSON.stringify(userMessages));

    return userMessages; 
}
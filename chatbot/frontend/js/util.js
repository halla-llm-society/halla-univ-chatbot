// 공용 함수

window.baseURL = "";

// 딜레이
const delay = (ms) => {
    return new Promise(resolve => setTimeout(resolve, ms));
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


const setBaseURL = () => {
    if (window.location.hostname.includes("localhost")) {
        window.baseURL = "http://localhost:8080";
    }
    else if (window.location.pathname.startsWith("/stg")) {
        window.baseURL = "https://halla-chatbot.com/stg";
    }
    else {
        window.baseURL = "https://halla-chatbot.com";
    }

    
}

setBaseURL();
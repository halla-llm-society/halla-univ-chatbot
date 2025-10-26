// 메인 함수

// 언어
let language = "KOR";

// 봇 답변 기다리는 중인지 체크
let isBotResponding = false

// local, docker, aws 호환
let baseURL = null;

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


// 초기화 및 기본 이벤트
window.addEventListener('DOMContentLoaded', () => {
    sendDefaultMessage();
    setModal();
    setUserInputPlaceHolder();

    setChatbotExpanded();
    setLangDropdown();
    setInputAndSend();

    setBaseURL();
    setUserInfo();
});
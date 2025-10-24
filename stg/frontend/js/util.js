// 공용 함수

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
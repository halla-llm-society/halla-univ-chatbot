// ui 관련 함수

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
        sendDefaultMessage();

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


// 챗봇 UI 제어
const setChatbotExpanded = () => {
    toggleBtn.addEventListener("click", () => {   // 챗봇 열기
        chatbotContainer.classList.add("expanded");
    });

    closeBtn.addEventListener("click", checkSurveyBeforeClose); // 챗봇 닫기
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

                sendDefaultMessage();
                setModal();
                setUserInputPlaceHolder();
            }
        });
    });

    langBtn.addEventListener('click', toggleLangDropdown);   // lang-btn 클릭 시 드롭다운 토글
}
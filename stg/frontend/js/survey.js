// 설문조사 관련 함수


// closeBtn에 리스너 추가
const checkSurveyBeforeClose = async () => {
  if(isBotResponding == true) {
    chatbotContainer.classList.remove("expanded");
    return;
  }

  if ((sessionStorage.getItem("survey") == "true") || (!shouldShowSurvey())) {
      chatbotContainer.classList.remove("expanded");
  }
  else {
      sessionStorage.setItem("survey", "true");
      const survey = new ChatbotSurvey();
      appendSurveyMessage(survey.surveyMsg);

      survey.startSurvey(); 
  }
}


// 채팅 1회당 설문조사 뜰 확률 20%씩 증가
const shouldShowSurvey = () => {
  const messageCnt = (JSON.parse(sessionStorage.getItem("userMessages") || "[]")).length;
  const probabilityIncrement = 20;
  const probability = Math.min(messageCnt * probabilityIncrement, 100);
  return Math.random() * 100 < probability;
}


class ChatbotSurvey {
  constructor() {
    this.surveyData = {
      userCategory: null,
      rating: null,
      responseSpeed: null,  
      responseQuality: null,
      comment: null
    };

    this.surveyMsg = `
      <div class="survey-container">
        <div class="survey-intro">
          🙏<br>${surveyStartDict[language]}
        </div>
      </div>
    `;
  }


  // 설문 부탁 페이지에서 0페이지로 이동
  async startSurvey() {
    const container = document.querySelector('.survey-container');

    await delay(2500);

    this.changeSurveyInnerHTML(container);
    this.bindEvents(container);
  }


  // survey 내부 html 변경
  changeSurveyInnerHTML(container) {
    container.innerHTML = `
      <div class="survey-progress">
        <div class="progress-bar" id="survey-progress-bar" style="width: 25%;"></div>
      </div>

      <div class="survey-page active" id="survey-page-0">
        ${this._getPage0()}
      </div>
      <div class="survey-page" id="survey-page-1">
        ${this._getPage1()}
      </div>
      <div class="survey-page" id="survey-page-2">
        ${this._getPage2()}
      </div>
      <div class="survey-page" id="survey-page-3">
        ${this._getPage3()}
      </div>
    `;

    messages.scrollTop = messages.scrollHeight;
  }


  // 0페이지
  _getPage0() {
    return `
      <div class="survey-question">${survey0Dict[language][0]}</div>

      <div class="survey-categories">
        <label class="category-card">
          <input type="radio" name="userCategory" value="1학년">
          <span>${survey0Dict[language][1]}</span>
        </label>

        <label class="category-card">
          <input type="radio" name="userCategory" value="2학년">
          <span>${survey0Dict[language][2]}</span>
        </label>

        <label class="category-card">
          <input type="radio" name="userCategory" value="3학년">
          <span>${survey0Dict[language][3]}</span>
        </label>

        <label class="category-card">
          <input type="radio" name="userCategory" value="4학년">
          <span>${survey0Dict[language][4]}</span>
        </label>

        <label class="category-card">
          <input type="radio" name="userCategory" value="대학원생">
          <span>${survey0Dict[language][5]}</span>
        </label>

        <label class="category-card">
          <input type="radio" name="userCategory" value="교직원">
          <span>${survey0Dict[language][6]}</span>
        </label>

        <label class="category-card">
          <input type="radio" name="userCategory" value="외부인">
          <span>${survey0Dict[language][7]}</span>
        </label>
      </div>

      <div class="survey-button-container">
        <button class="survey-button" id="survey-page0-prev" disabled>${surveyBtnDict[language][0]}</button>
        <button class="survey-button" id="survey-page0-next" disabled>${surveyBtnDict[language][1]}</button>
      </div>
  `;
  }


  // 1페이지
  _getPage1() {
    return `
      <div class="survey-question">${survey1Dict[language]}</div>
      <div class="star-rating">
        <input type="radio" id="star5" name="rating" value="5"><label for="star5">★</label>
        <input type="radio" id="star4" name="rating" value="4"><label for="star4">★</label>
        <input type="radio" id="star3" name="rating" value="3"><label for="star3">★</label>
        <input type="radio" id="star2" name="rating" value="2"><label for="star2">★</label>
        <input type="radio" id="star1" name="rating" value="1"><label for="star1">★</label>
      </div>

      <div class="survey-button-container">
        <button class="survey-button" id="survey-page1-prev">${surveyBtnDict[language][0]}</button>
        <button class="survey-button" id="survey-page1-next" disabled>${surveyBtnDict[language][1]}</button>
      </div>
    `;
  }


  // 2페이지
  _getPage2() {
    return `
      <div class="survey-question">${survey2Dict[language][0]}</div>

      <div class="survey-options" id="survey-feedback-metrics">
        <div class="feedback-metric">
          <span class="metric-label">${survey2Dict[language][1]}</span>
          <div class="metric-buttons">
            <button class="feedback-button high" data-metric="responseSpeed" data-value="high">😊</button>
            <button class="feedback-button mid" data-metric="responseSpeed" data-value="mid">😐</button>
            <button class="feedback-button low" data-metric="responseSpeed" data-value="low">😞</button>
          </div>
        </div>

        <div class="feedback-metric">
          <span class="metric-label">${survey2Dict[language][2]}</span>
          <div class="metric-buttons">
            <button class="feedback-button high" data-metric="responseQuality" data-value="high">😊</button>
            <button class="feedback-button mid" data-metric="responseQuality" data-value="mid">😐</button>
            <button class="feedback-button low" data-metric="responseQuality" data-value="low">😞</button>
          </div>
        </div>
      </div>

      <div class="survey-button-container">
        <button class="survey-button" id="survey-page2-prev">${surveyBtnDict[language][0]}</button>
        <button class="survey-button" id="survey-page2-next" disabled>${surveyBtnDict[language][1]}</button>
      </div>
    `;
  }


  // 3페이지
  _getPage3() {
    return `
      <div class="survey-question">${survey3Dict[language][0]}</div>
      <textarea id="survey-comment" class="survey-textarea" placeholder="${survey3Dict[language][1]}"></textarea>

      <div class="survey-button-container">
        <button class="survey-button" id="survey-page3-prev">${surveyBtnDict[language][0]}</button>
        <button class="survey-button" id="survey-submit">${surveyBtnDict[language][2]}</button>
      </div>
    `;
  }

  
  // 이벤트 연결
  bindEvents(container) {
    this.setupUserCategoryEvents(container);
    this.setupRatingEvents(container);
    this.setupFeedbackMetricEvents(container);
    this.setupNavigationEvents(container);
  }


  // 카테고리 선택 이벤트
  setupUserCategoryEvents(container) {
    container.querySelectorAll('input[name="userCategory"]').forEach(input => {
      input.addEventListener('change', (e) => {
        const nextBtn = container.querySelector('#survey-page0-next');
        nextBtn.disabled = false; 

        this.surveyData.userCategory = e.target.value;
      });
    });
  }


  // 별점 선택 이벤트
  setupRatingEvents(container) {
    container.querySelectorAll('input[name="rating"]').forEach(input => {
      input.addEventListener('change', (e) => {
        const nextBtn = container.querySelector('#survey-page1-next');
        nextBtn.disabled = false;

        this.surveyData.rating = Number(e.target.value);
      });
    });
  }


  // 상·중·하(응답 속도, 정확도) 클릭 이벤트 설정
  setupFeedbackMetricEvents(container) {
    container.querySelectorAll('.feedback-button').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const metric = e.target.dataset.metric;
        const value = e.target.dataset.value;
        const buttons = e.target.parentElement.querySelectorAll('.feedback-button');
        const nextButton = container.querySelector('#survey-page2-next');

        // 이미 active 상태면 취소 
        if (e.target.classList.contains('active')) {
          e.target.classList.remove('active');
          this.surveyData[metric] = null; 
        }
        else {
          // 동일 그룹의 다른 버튼 해제
          buttons.forEach(b => b.classList.remove('active'));
          e.target.classList.add('active');
          this.surveyData[metric] = value;
        }

        if (this.surveyData.responseSpeed && this.surveyData.responseQuality) {
          nextButton.disabled = false;
        } 
        else {
          nextButton.disabled = true;
        }
      });
    });
  }

  
  // 페이지 이동 버튼 이벤트
  setupNavigationEvents(container) {
    const pages = [
      { btn: '#survey-page0-next', to: 1 },
      { btn: '#survey-page1-prev', to: 0 },
      { btn: '#survey-page1-next', to: 2 },
      { btn: '#survey-page2-prev', to: 1 },
      { btn: '#survey-page2-next', to: 3 },
      { btn: '#survey-page3-prev', to: 2 },
    ];

    pages.forEach(({ btn, to }) => {
      const button = container.querySelector(btn);

      button.addEventListener('click', () => {
        const currentPage = container.querySelector(`.survey-page.active`);
        currentPage.classList.remove('active');

        const nextPage = container.querySelector(`#survey-page-${to}`);
        nextPage.classList.add('active');

        const progressBar = container.querySelector('#survey-progress-bar');
        progressBar.style.width = (to / 4) * 100 + '%';

        messages.scrollTop = messages.scrollHeight;
      });
    });

    // 제출 버튼
    container.querySelector('#survey-submit')?.addEventListener('click', () => {
      this.submitSurvey(container);
    });
  }


  // 설문조사 종료 후
  submitSurvey(container) {
    this.surveyData.comment = container.querySelector('#survey-comment').value;

    container.innerHTML = `
      <div class="survey-end">
        ${surveyEndDict[language]}

        <a href="https://docs.google.com/forms/d/e/1FAIpQLSeOav-Oe1Vovh-IwR8rAEZk9lTHrB1KX13f0pOfe9PIgxIIuQ/viewform" target="_blank" class="survey-link">
          👉 ${surveyBtnDict[language][3]}
        </a>
      </div>
    `;

    messages.scrollTop = messages.scrollHeight;

    // request
    fetch(`${baseURL}/api/survey`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: this.surveyData })
    })
  }
}
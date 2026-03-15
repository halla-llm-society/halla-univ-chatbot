// 다국어 메시지 모음

const defaultMsgDict = {
  "KOR": `안녕하세요! 한라대학교 챗봇이에요. 🤗<br><br>
          학교 생활, 학과 정보, 행사 등 궁금한 점이 있다면 무엇이든 저에게 물어보세요<br><br>
          📌 질문이 구체적일수록 더 정확한 답변을 드릴 수 있어요<br><br>
          📌 7개 언어(한국어, 영어, 중국어 등)를 지원합니다<br><br>
          📌 대화 내용은 서비스 품질 향상을 위해 저장되며, 개인정보는 수집하지 않으니 안심하고 사용하셔도 좋습니다`,

  "ENG": `Hello! I'm the Halla University chatbot. 🤗<br><br>
          Feel free to ask me anything about campus life, department information, events, etc<br><br>
          📌 The more specific your question is, the more accurate my answer can be<br><br>
          📌 I support 7 languages (Korean, English, Chinese, etc.)<br><br>
          📌 Conversations are saved to improve service quality, but personal information is not collected, so you can use it safely`,

  "VNM": `Xin chào! Tôi là chatbot của Đại học Halla. 🤗<br><br>
          Hãy thoải mái hỏi tôi bất cứ điều gì về cuộc sống trong trường, thông tin khoa, các sự kiện, v.v<br><br>
          📌 Câu hỏi của bạn càng cụ thể, tôi càng có thể đưa ra câu trả lời chính xác<br><br>
          📌 Tôi hỗ trợ 7 ngôn ngữ (tiếng Hàn, tiếng Anh, tiếng Trung, v.v.)<br><br>
          📌 Nội dung trò chuyện được lưu trữ để cải thiện chất lượng dịch vụ, nhưng thông tin cá nhân không được thu thập, vì vậy bạn có thể yên tâm sửS dụng`,

  "CHN": `您好！我是汉拿大学的聊天机器人。 🤗<br><br>
          关于校园生活、专业信息、活动等，有任何问题请随时问我<br><br>
          📌 您的问题越具体，我就能提供越准确的答复<br><br>
          📌 我支持7种语言（韩语、英语、中文等）<br><br>
          📌 对话内容将被保存以提高服务质量，但不会收集个人信息，请您放心使用`,

  "UZB": `Salom! Men Halla Universiteti chatbotiman. 🤗<br><br>
          Kampus hayoti, kafedra ma'lumotlari, tadbirlar haqida xohlagan narsangizni so'rashingiz mumkin<br><br>
          📌 Savolingiz qanchalik aniq bo'lsa, shunchalik to'g'ri javob bera olaman<br><br>
          📌 Men 7 tilni (koreys, ingliz, xitoy va b.) qo'llab-quvvatlayman<br><br>
          📌 Suhbatlar xizmat sifatini yaxshilash uchun saqlanadi, ammo shaxsiy ma'lumotlar yig'ilmaydi, shuning uchun bemalol foydalanishingiz mumkin`,

  "MNG": `Сайн уу! Би Халла их сургуулийн чатбот байна. 🤗<br><br>
          Сургуулийн амьдрал, тэнхимийн мэдээлэл, арга хэмжээний талаар юу ч хамаагүй асуугаарай<br><br>
          📌 Таны асуулт тодорхой байх тусам би илүү оновчтой хариулт өгөх болно<br><br>
          📌 Би 7 хэлийг (Солонгос, Англи, Хятад гэх мэт) дэмждэг<br><br>
          📌 Ярианы агуулга үйлчилгээний чанарыг сайжруулах зорилгоор хадгалагдах бөгөөд хувийн мэдээлэл цуглуулахгүй тул та итгэлтэйгээр ашиглаж болно`,

  "IDN": `Halo! Saya chatbot Universitas Halla. 🤗<br><br>
          Silakan tanyakan apa saja kepada saya tentang kehidupan kampus, info jurusan, acara, dll<br><br>
          📌 Semakin spesifik pertanyaan Anda, semakin akurat jawaban yang bisa saya berikan<br><br>
          📌 Saya mendukung 7 bahasa (Korea, Inggris, Mandarin, dll.)<br><br>
          📌 Percakapan disimpan untuk meningkatkan kualitas layanan, tetapi informasi pribadi tidak dikumpulkan, jadi Anda dapat menggunakannya dengan aman`
}


const waitMsgDict = {
    "KOR": [
        "⏳ 응답 생성 중입니다...",
        "🤔 조금 고민 중이에요",
        "🧐 품질 검토 중입니다",
        "🔍 최적의 답을 찾는 중",
        "🙏 거의 다 왔습니다",
        "💡 오래 걸리면 다시 시도해 보셔도 좋아요"
    ],
    "ENG": [
        "⏳ Generating response...",
        "🤔 Thinking it over",
        "🧐 Reviewing quality",
        "🔍 Looking for the best answer",
        "🙏 Almost there",
        "💡 If it takes too long, feel free to try again"
    ],
    "VNM": [
        "⏳ Đang tạo phản hồi...",
        "🤔 Đang suy nghĩ một chút",
        "🧐 Đang kiểm tra chất lượng",
        "🔍 Đang tìm câu trả lời tối ưu",
        "🙏 Sắp xong rồi",
        "💡 Nếu mất quá nhiều thời gian, bạn có thể thử lại"
    ],
    "CHN": [
        "⏳ 正在生成回复...",
        "🤔 正在稍微思考",
        "🧐 正在进行质量检查",
        "🔍 正在寻找最佳答案",
        "🙏 快完成了",
        "💡 如果花太长时间，可以重新尝试"
    ],
    "UZB": [
        "⏳ Javob yaratilmoqda...",
        "🤔 Biroz o‘ylab qolyapman",
        "🧐 Sifatni tekshirmoqda",
        "🔍 Eng yaxshi javobni qidirmoqda",
        "🙏 Tez orada tugaydi",
        "💡 Juda uzoq cho‘zilsa, qayta urinib ko‘rishingiz mumkin"
    ],
    "MNG": [
        "⏳ Хариу үүсгэж байна...",
        "🤔 Бага зэрэг бодож байна",
        "🧐 Чанарыг шалгаж байна",
        "🔍 Хамгийн сайн хариултыг хайж байна",
        "🙏 Бараг дууслаа",
        "💡 Хэрэв удаан байвал дахин оролдож болно"
    ],
    "IDN": [
        "⏳ Sedang membuat jawaban...",
        "🤔 Sedang mempertimbangkan sedikit",
        "🧐 Sedang meninjau kualitas",
        "🔍 Sedang mencari jawaban terbaik",
        "🙏 Hampir selesai",
        "💡 Jika terlalu lama, silakan coba lagi"
    ]
};


const errorMsgDict = {
    "KOR": "오류가 발생했습니다",
    "ENG": "An error has occurred.",
    "VNM": "Đã xảy ra lỗi.",
    "CHN": "发生错误。",
    "UZB": "Xatolik yuz berdi.",
    "MNG": "Алдаа гарлаа.",
    "IDN": "Terjadi kesalahan."
};


const infoModalDict = {
  "KOR": `<div class="modal">
            <div class="modal-title"><span class="highlight">한라대학교 챗봇</span> 이용 안내</div>
            <div class="modal-content scrollable">
              <ul>
                <li>이 챗봇은 <span class="highlight">한라대학교 LLM 동아리</span>에서 학생들의 편의를 위해 만들었습니다</li>
                <li>현재 <span class="highlight">학사 규칙, 오늘의 학식, 통학버스 시간</span> 등에 대해 답변해 드릴 수 있습니다</li>
                <li>안내된 기능 외의 질문이나, 제가 제공하는 정보는 <span class="highlight">부정확할 수 있습니다</span></li>
                <li>중요한 정보는 반드시 답변의 출처 또는 <span class="highlight">학교 공식 페이지</span>를 통해 다시 확인해 주세요</li>
                <li>여러분의 의견을 바탕으로 계속 개선해 나가겠습니다</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">확인</button>
            </div>
          </div>`,

  "ENG": `<div class="modal">
            <div class="modal-title"><span class="highlight">Halla University Chatbot</span> User Guide</div>
            <div class="modal-content scrollable">
              <ul>
                <li>This chatbot was created by the <span class="highlight">Halla University LLM Club</span> for the convenience of students</li>
                <li>Currently, I can answer questions about <span class="highlight">academic rules, today's cafeteria menu, shuttle bus schedules</span>, and more</li>
                <li>Questions outside of the guided features, or information I provide, <span class="highlight">may be inaccurate</span></li>
                <li>Please double-check important information via the answer's source or the <span class="highlight">official university page</span></li>
                <li>We will continue to improve based on your feedback</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">OK</button>
            </div>
          </div>`,

  "VNM": `<div class="modal">
            <div class="modal-title"><span class="highlight">Chatbot Đại học Halla</span> Hướng dẫn sử dụng</div>
            <div class="modal-content scrollable">
              <ul>
                <li>Chatbot này được tạo bởi <span class="highlight">Câu lạc bộ LLM Đại học Halla</span> vì sự tiện lợi của sinh viên</li>
                <li>Hiện tại, tôi có thể trả lời các câu hỏi về <span class="highlight">quy định học tập, thực đơn hôm nay, lịch xe buýt</span>, v.v</li>
                <li>Câu hỏi ngoài các tính năng được hướng dẫn hoặc thông tin tôi cung cấp <span class="highlight">có thể không chính xác</span></li>
                <li>Vui lòng kiểm tra lại thông tin quan trọng qua nguồn của câu trả lời hoặc <span class="highlight">trang web chính thức của trường</span></li>
                <li>Chúng tôi sẽ tiếp tục cải thiện dựa trên ý kiến của bạn</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">Xác nhận</button>
            </div>
          </div>`,

  "CHN": `<div class="modal">
            <div class="modal-title"><span class="highlight">汉拿大学聊天机器人</span> 使用指南</div>
            <div class="modal-content scrollable">
              <ul>
                <li>本聊天机器人由 <span class="highlight">汉拿大学 LLM 社团</span> 为方便学生而创建</li>
                <li>目前, 我可以回答有关 <span class="highlight">学籍规定、今日食堂菜单、校车时间表</span> 等问题</li>
                <li>超出指南功能的问题或我提供的信息 <span class="highlight">可能不准确</span></li>
                <li>重要信息请务必通过答案来源或 <span class="highlight">学校官方页面</span> 再次确认</li>
                <li>我们将根据您的反馈不断改进</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">确认</button>
            </div>
          </div>`,

  "UZB": `<div class="modal">
            <div class="modal-title"><span class="highlight">Halla Universiteti Chatboti</span> Foydalanish Qo'llanmasi</div>
            <div class="modal-content scrollable">
              <ul>
                <li>Ushbu chatbot talabalar qulayligi uchun <span class="highlight">Halla Universiteti LLM Klubi</span> tomonidan yaratilgan</li>
                <li>Hozirda men <span class="highlight">o'quv qoidalari, bugungi ovqat menyusi, avtobus jadvali</span> va boshqalar haqidagi savollarga javob bera olaman</li>
                <li>Ko'rsatilgan funksiyalardan tashqari savollar yoki men taqdim etgan ma'lumotlar <span class="highlight">noaniq bo'lishi mumkin</span></li>
                <li>Muhim ma'lumotlarni javob manbasi yoki <span class="highlight">universitetning rasmiy sahifasi</span> orqali qayta tekshirib ko'ring</li>
                <li>Sizning fikr-mulohazalaringiz asosida biz yaxshilanishda davom etamiz</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">Tushundim</button>
            </div>
          </div>`,

  "MNG": `<div class="modal">
            <div class="modal-title"><span class="highlight">Халла Их Сургуулийн Чатбот</span> Ашиглах заавар</div>
            <div class="modal-content scrollable">
              <ul>
                <li>Энэхүү чатботыг <span class="highlight">Халла Их Сургуулийн LLM Клуб</span> оюутнуудын тав тухтай байдлыг хангах үүднээс бүтээсэн</li>
                <li>Одоогоор <span class="highlight">сургалтын дүрэм, өнөөдрийн хоолны цэс, автобусны цагийн хуваарь</span> зэрэг асуултуудад хариулах боломжтой</li>
                <li>Заасан функцээс гадуурх асуулт эсвэл миний өгсөн мэдээлэл <span class="highlight">буруу байж болзошгүй</span></li>
                <li>Чухал мэдээллийг хариултын эх сурвалж эсвэл <span class="highlight">сургуулийн албан ёсны хуудаснаас</span> давхар нягталж үзнэ үү</li>
                <li>Бид та бүхний санал хүсэлтэд тулгуурлан үйлчилгээгээ үргэлжлүүлэн сайжруулах болно</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">Ойлголоо</button>
            </div>
          </div>`,

  "IDN": `<div class="modal">
            <div class="modal-title"><span class="highlight">Chatbot Universitas Halla</span> Panduan Penggunaan</div>
            <div class="modal-content scrollable">
              <ul>
                <li>Chatbot ini dibuat oleh <span class="highlight">Klub LLM Universitas Halla</span> untuk kenyamanan mahasiswa</li>
                <li>Saat ini, saya dapat menjawab pertanyaan tentang <span class="highlight">peraturan akademik, menu kafetaria hari ini, jadwal bus</span>, dll</li>
                <li>Pertanyaan di luar fitur yang disebutkan atau informasi yang saya berikan <span class="highlight">mungkin tidak akurat</span></li>
                <li>Harap periksa kembali informasi penting melalui sumber jawaban atau <span class="highlight">halaman resmi universitas</span></li>
                <li>Kami akan terus melakukan perbaikan berdasarkan masukan Anda</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">Mengerti</button>
            </div>
          </div>`
}


const resetModalDict = {
    "KOR": `<div class="modal">
            <div class="modal-title">대화 내용 초기화</div>
            <div class="modal-content">
              기존 대화 내용이 모두 삭제되고, <br/>
              처음부터 다시 시작됩니다. <br/>
              초기화 하시겠습니까?
            </div>
            <div class="modal-buttons">
              <button id="cancel-reset-btn">취소</button>
              <button id="confirm-reset-btn">초기화</button>
            </div>
          </div>`,

    "ENG": `<div class="modal">
            <div class="modal-title">Reset Conversation</div>
            <div class="modal-content">
              The previous conversation will be deleted, <br/>
              and it will start over from the beginning. <br/>
              Do you want to reset?
            </div>
            <div class="modal-buttons">
              <button id="cancel-reset-btn">Cancel</button>
              <button id="confirm-reset-btn">Reset</button>
            </div>
          </div>`,

    "VNM": `<div class="modal">
            <div class="modal-title">Đặt lại cuộc trò chuyện</div>
            <div class="modal-content">
              Nội dung cuộc trò chuyện trước sẽ bị xóa, <br/>
              và bắt đầu lại từ đầu. <br/>
              Bạn có muốn đặt lại không?
            </div>
            <div class="modal-buttons">
              <button id="cancel-reset-btn">Hủy</button>
              <button id="confirm-reset-btn">Đặt lại</button>
            </div>
          </div>`,

    "CHN": `<div class="modal">
            <div class="modal-title">重置对话</div>
            <div class="modal-content">
              之前的对话内容将被删除，<br/>
              并从头开始。 <br/>
              您要重置吗？
            </div>
            <div class="modal-buttons">
              <button id="cancel-reset-btn">取消</button>
              <button id="confirm-reset-btn">重置</button>
            </div>
          </div>`,

    "UZB": `<div class="modal">
            <div class="modal-title">Suhbatni tiklash</div>
            <div class="modal-content">
              Oldingi suhbatlar o‘chirilib, <br/>
              boshidan boshlanadi. <br/>
              Qayta tiklashni xohlaysizmi?
            </div>
            <div class="modal-buttons">
              <button id="cancel-reset-btn">Bekor qilish</button>
              <button id="confirm-reset-btn">Qayta tiklash</button>
            </div>
          </div>`,

    "MNG": `<div class="modal">
            <div class="modal-title">Яриаг дахин тохируулах</div>
            <div class="modal-content">
              Өмнөх ярианы агуулга устаж, <br/>
              шинээр эхэлнэ. <br/>
              Та дахин тохируулахыг хүсэж байна уу?
            </div>
            <div class="modal-buttons">
              <button id="cancel-reset-btn">Цуцлах</button>
              <button id="confirm-reset-btn">Дахин тохируулах</button>
            </div>
          </div>`,

    "IDN": `<div class="modal">
            <div class="modal-title">Atur Ulang Percakapan</div>
            <div class="modal-content">
              Percakapan sebelumnya akan dihapus, <br/>
              dan dimulai dari awal. <br/>
              Apakah Anda ingin mereset?
            </div>
            <div class="modal-buttons">
              <button id="cancel-reset-btn">Batal</button>
              <button id="confirm-reset-btn">Atur Ulang</button>
            </div>
          </div>`
}


const userInputPlaceHolderDict = {
    "KOR": "무엇이든 물어보세요!",
    "ENG": "Ask me anything!",
    "VNM": "Hãy hỏi tôi bất cứ điều gì!",
    "CHN": "有什么都可以问我！",
    "UZB": "Istagan narsangizni so'rashingiz mumkin!",
    "MNG": "Надаас юу ч асуугаарай!",
    "IDN": "Tanyakan apa saja kepada saya!"
}


const surveyStartDict = {
  "KOR": "잠깐만요! 간단한 설문 부탁드려요 :)",
  "ENG": "One moment! Could you please take a quick survey? :)",
  "VNM": "Xin chờ một lát! Bạn vui lòng làm một khảo sát ngắn nhé :)",
  "CHN": "请稍等！麻烦您做个简单的问卷调查 :)",
  "UZB": "Bir daqiqa! Iltimos, qisqa so'rovnomani to'ldiring :)",
  "MNG": "Түр хүлээнэ үү! Энгийн асуулгад хариулна уу :)",
  "IDN": "Tunggu sebentar! Mohon isi survei singkat kami :)"
}


const surveyBtnDict = {
  "KOR": [
    "이전",
    "다음",
    "제출하기",
    "추가 설문 참여하기"
  ],
  "ENG": [
    "Prev",  
    "Next",
    "Submit",
    "Take additional survey" 
  ],
  "VNM": [
    "Trước",
    "Tiếp",  
    "Gửi",   
    "Tham gia khảo sát thêm"
  ],
  "CHN": [
    "上一步",
    "下一步", 
    "提交",   
    "参与额外问卷"
  ],
  "UZB": [
    "Orqaga", 
    "Keyingisi", 
    "Yuborish",
    "Qo'shimcha so'rovnomada qatnashish"
  ],
  "MNG": [
    "Өмнөх", 
    "Дараах", 
    "Илгээх", 
    "Нэмэлт судалгаанд оролцох"
  ],
  "IDN": [
    "Kembali", 
    "Lanjut",   
    "Kirim",     
    "Ikuti survei tambahan"
  ]
}


const survey0Dict = {
  "KOR": [
    "현재 소속을 알려주세요!",
    "1학년",
    "2학년",
    "3학년",
    "4학년",
    "대학원생",
    "교직원",
    "외부인"
  ],
  "ENG": [
    "What is your affiliation?",
    "1st Year",
    "2nd Year",
    "3rd Year",
    "4th Year",
    "Graduate",
    "Staff",    
    "Visitor"
  ],
  "VNM": [
    "Bạn là ai?", 
    "Năm 1",    
    "Năm 2",
    "Năm 3",
    "Năm 4",
    "Cao học",  
    "Nhân viên", 
    "Khách"
  ],
  "CHN": [
    "您的身份是？", 
    "一年级",
    "二年级",
    "三年级",
    "四年级",
    "研究生",
    "教职员",
    "访客"    
  ],
  "UZB": [
    "Mansubligingiz?", 
    "1-kurs",
    "2-kurs",
    "3-kurs",
    "4-kurs",
    "Magistrant",
    "Xodim",    
    "Mehmon"   
  ],
  "MNG": [
    "Таны харьяалал?",
    "1-р курс",
    "2-р курс",
    "3-р курс",
    "4-р курс",
    "Магистрант", 
    "Ажилтан",   
    "Зочин"
  ],
  "IDN": [
    "Afiliasi Anda?", 
    "Thn 1", 
    "Thn 2",
    "Thn 3",
    "Thn 4",
    "Pasca",
    "Staf", 
    "Pengunjung"
  ]
}


const survey1Dict = {
  "KOR": "저희 서비스에 점수를 매겨주세요!",
  "ENG": "Please rate our service!",
  "VNM": "Vui lòng xếp hạng dịch vụ của chúng tôi!",
  "CHN": "请为我们的服务打分！",
  "UZB": "Bizning xizmatimizni baholang!",
  "MNG": "Манай үйлчилгээнд үнэлгээ өгнө үү!",
  "IDN": "Silakan beri nilai untuk layanan kami!"
}


const survey2Dict = {
  "KOR": [
    "챗봇의 응답 품질을 평가해주세요!",
    "답변 속도",
    "답변 정확도"
  ],
  "ENG": [
    "Please rate the response quality!",
    "Speed",   
    "Accuracy"  
  ],
  "VNM": [
    "Đánh giá chất lượng phản hồi!", 
    "Tốc độ",   
    "Độ chính xác" 
  ],
  "CHN": [
    "请评价回复质量！", 
    "速度",   
    "准确性" 
  ],
  "UZB": [
    "Javob sifatini baholang!", 
    "Tezlik",  
    "Aniqlik"  
  ],
  "MNG": [
    "Хариултын чанарыг үнэлнэ үү!",
    "Хурд",   
    "Оновч"   
  ],
  "IDN": [
    "Silakan nilai kualitas respons!",
    "Kecepatan", 
    "Akurasi"   
  ]
}


const survey3Dict = {
  "KOR": [
    "기타 의견이 있으신가요?",
    "자유롭게 의견을 남겨주세요..."
  ],
  "ENG": [
    "Do you have any other comments?",
    "Please leave your comments freely..."
  ],
  "VNM": [
    "Bạn có ý kiến nào khác không?",
    "Vui lòng để lại ý kiến của bạn..."
  ],
  "CHN": [
    "还有其他意见吗？",
    "请随意留言..."
  ],
  "UZB": [
    "Boshqa fikrlaringiz bormi?",
    "Fikrlaringizni erkin qoldiring..."
  ],
  "MNG": [
    "Бусад санал байна уу?",
    "Саналаа чөлөөтэй үлдээнэ үү..."
  ],
  "IDN": [
    "Ada masukan lain?",
    "Silakan sampaikan masukan Anda..."
  ]
}


const surveyEndDict = {
  "KOR": `
    <p>대화는 즐거우셨나요?<br>
    마지막으로 짧은 설문에 참여하시면<br>
    감사의 마음으로 <strong>기프티콘</strong>을 드려요!</p>
  `,
  "ENG": `
    <p>Did you enjoy the conversation?<br>
    Lastly, if you participate in a short survey,<br>
    we'll give you a <strong>gift certificate</strong> as a token of our appreciation!</p>
  `,
  "VNM": `
    <p>Cuộc trò chuyện có vui vẻ không?<br>
    Cuối cùng, nếu bạn tham gia một khảo sát ngắn,<br>
    chúng tôi sẽ tặng bạn một <strong>phiếu quà tặng</strong> (gifticon) như lời cảm ơn!</p>
  `,
  "CHN": `
    <p>对话愉快吗？<br>
    最后，如果您参加一个简短的问卷调查，<br>
    我们将赠送一张<strong>礼品卡</strong>以表感谢！</p>
  `,
  "UZB": `
    <p>Suhbat sizga yoqdimi?<br>
    So'ngida, agar qisqa so'rovnomada qatnashsangiz,<br>
    minnatdorchilik sifatida sizga <strong>sovg'a sertifikati</strong> (gifticon) taqdim etamiz!</p>
  `,
  "MNG": `
    <p>Яриа танд таалагдсан уу?<br>
    Эцэст нь, богино асуулгад оролцвол<br>талархал болгон <strong>бэлгийн карт</strong> (gifticon) өгөх болно!</p>
  `,
  "IDN": `
    <p>Apakah percakapan Anda menyenangkan?<br>
    Terakhir, jika Anda berpartisipasi dalam survei singkat,<br>
    kami akan memberikan <strong>voucher hadiah</strong> (gifticon) sebagai tanda terima kasih!</p>
  `
}
// 다국어 메시지 모음

const defaultMsgDict = {
    "KOR": `안녕하세요! 한라대학교 GPT 챗봇이에요. 🤗<br><br>
          학교 생활, 학과 정보, 행사 등 궁금한 점이 있으면 무엇이든 물어보세요.<br><br>
          질문이 구체적일수록 더 정확하고 유용한 답변을 드릴 수 있어요. ✨<br><br>
          📌 이 챗봇은 개인정보를 수집하지 않으니 안심하고 대화하실 수 있어요.<br><br>
          📌 한국어, 영어, 중국어 등 여러 언어로 편하게 질문하실 수 있어요.`,

    "ENG": `Hello! I'm the Halla University GPT chatbot. 🤗<br><br>
        Feel free to ask anything about campus life, departments, events, or anything you're curious about.<br><br>
        The more specific your question, the more accurate and useful my answer can be. ✨<br><br>
        📌 This chatbot does not collect any personal information, so you can chat safely.<br><br>
        📌 You can ask questions comfortably in multiple languages.`,

    "VNM": `Xin chào! Tôi là chatbot GPT của Đại học Halla. 🤗<br><br>
        Hãy thoải mái hỏi bất cứ điều gì về cuộc sống sinh viên, thông tin khoa, sự kiện hoặc bất kỳ thắc mắc nào bạn có.<br><br>
        Câu hỏi càng cụ thể, câu trả lời của tôi sẽ càng chính xác và hữu ích. ✨<br><br>
        📌 Chatbot này không thu thập thông tin cá nhân, bạn có thể yên tâm trò chuyện.<br><br>
        📌 Bạn có thể hỏi bằng nhiều ngôn ngữ khác nhau.`,

    "CHN": `您好！我是汉拿大学 GPT 聊天机器人。🤗<br><br>
        如果您对校园生活、专业信息、活动等有任何疑问，请随时提问。<br><br>
        问题越具体，我提供的回答就越准确、越有用。✨<br><br>
        📌 本聊天机器人不会收集任何个人信息，请放心使用。<br><br>
        📌 您可以使用多种语言自由提问。`,

    "UZB": `Salom! Men Halla Universiteti GPT chatbotiman. 🤗<br><br>
        Kampus hayoti, fakultetlar, tadbirlar yoki qiziqqan har qanday savolingizni bemalol so‘rashingiz mumkin.<br><br>
        Savolingiz qanchalik aniq bo‘lsa, javobim shunchalik to‘g‘ri va foydali bo‘ladi. ✨<br><br>
        📌 Ushbu chatbot shaxsiy ma’lumotlarni to‘plamaydi, shuning uchun xavfsiz suhbatlashishingiz mumkin.<br><br>
        📌 Siz savollaringizni bir nechta tillarda berishingiz mumkin.`,

    "MNG": `Сайн байна уу! Би Халла Их Сургуулийн GPT чатбот байна. 🤗<br><br>
        Сургуулийн амьдрал, тэнхимийн мэдээлэл, үйл явдлын талаар сонирхсон зүйлээ чөлөөтэй асуугаарай.<br><br>
        Асуулт чинь нарийн байх тусам би илүү зөв, ашигтай хариу өгч чадна. ✨<br><br>
        📌 Энэ чатбот нь хувийн мэдээллийг цуглуулдаггүй тул аюулгүйгээр чатлаж болно.<br><br>
        📌 Та олон хэл дээр чөлөөтэй асуулт асууж болно.`,

    "IDN": `Halo! Saya adalah chatbot GPT Universitas Halla. 🤗<br><br>
        Silakan tanyakan apa saja tentang kehidupan kampus, informasi jurusan, acara, atau hal-hal yang ingin Anda ketahui.<br><br>
        Semakin spesifik pertanyaan Anda, semakin akurat dan berguna jawaban yang saya berikan. ✨<br><br>
        📌 Chatbot ini tidak mengumpulkan informasi pribadi, jadi Anda bisa chat dengan aman.<br><br>
        📌 Anda dapat bertanya dalam berbagai bahasa.`

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
            <div class="modal-title"><span class="highlight">한라대학교 GPT</span> 이용 안내</div>
            <div class="modal-content scrollable">
              <ul>
                <li>단어가 아닌 <span class="highlight">대화형 문장으로 질문</span> 해주세요.</li>
                <li>제가 제공하는 정보는 <span class="highlight">부정확할 수 있어요.</span></li>
                <li>정확한 정보는 <span class="highlight">답변의 출처 및 해당 페이지 링크</span>를 통해 직접 확인해 주세요.</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">확인</button>
            </div>
          </div>`,

    "ENG": `<div class="modal">
            <div class="modal-title"><span class="highlight">Halla University GPT</span><br>User Guide</div>
            <div class="modal-content scrollable">
              <ul>
                <li>Please ask questions in <span class="highlight">conversational sentences</span>, not just single words.</li>
                <li>The information I provide <span class="highlight">may be inaccurate</span>.</li>
                <li>For accurate information, please <span class="highlight">check the sources and links</span> in my responses.</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">OK</button>
            </div>
          </div>`,

    "VNM": `<div class="modal">
          <div class="modal-title"><span class="highlight">Halla University GPT</span><br>Hướng dẫn sử dụng</div>
          <div class="modal-content scrollable">
            <ul>
              <li>Vui lòng đặt câu hỏi bằng <span class="highlight">câu hội thoại đầy đủ</span>, không chỉ bằng từ đơn.</li>
              <li>Thông tin tôi cung cấp <span class="highlight">có thể không chính xác</span>.</li>
              <li>Để có thông tin chính xác, vui lòng <span class="highlight">kiểm tra nguồn và liên kết</span> trong câu trả lời của tôi.</li>
            </ul>
          </div>
          <div class="modal-buttons single">
            <button id="confirm-info-btn">Xác nhận</button>
          </div>
        </div>`,

    "CHN": `<div class="modal">
          <div class="modal-title"><span class="highlight">Halla University GPT</span><br>使用指南</div>
          <div class="modal-content scrollable">
            <ul>
              <li>请使用<span class="highlight">对话式的完整句子</span>来提问，而不是单个词语。</li>
              <li>我提供的信息<span class="highlight">可能不准确</span>。</li>
              <li>如需准确的信息，请<span class="highlight">查看我的回答中的来源和链接</span>。</li>
            </ul>
          </div>
          <div class="modal-buttons single">
            <button id="confirm-info-btn">确认</button>
          </div>
        </div>`,

    "UZB": `<div class="modal">
            <div class="modal-title"><span class="highlight">Halla Universiteti GPT</span> foydalanish bo'yicha qo'llanma</div>
            <div class="modal-content scrollable">
              <ul>
                <li>Savollarni so‘zlardan ko‘ra <span class="highlight">tabiiy gaplar bilan</span> berishga harakat qiling.</li>
                <li>Men taqdim etadigan ma’lumotlar <span class="highlight">100% to‘g‘ri bo‘lmasligi</span> mumkin.</li>
                <li>Aniq ma’lumot olish uchun <span class="highlight">manbalarni yoki tegishli sahifa havolalarini</span> tekshiring.</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">Tushundim</button>
            </div>
          </div>`,

    "MNG": `<div class="modal">
            <div class="modal-title"><span class="highlight">Халла Их Сургуулийн GPT</span> ашиглах заавар</div>
            <div class="modal-content scrollable">
              <ul>
                <li>Асуултаа <span class="highlight">утга агуулсан энгийн өгүүлбэрээр</span> тавина уу.</li>
                <li>Миний өгч буй мэдээлэл <span class="highlight">100% зөв байж чадахгүй</span> юм.</li>
                <li>Нарийвчилсан мэдээллийг авахын тулд <span class="highlight">эх сурвалж эсвэл холбогдох холбоосыг</span> шалгана уу.</li>
              </ul>
            </div>
            <div class="modal-buttons single">
              <button id="confirm-info-btn">Ойлголоо</button>
            </div>
          </div>`,

    "IDN": `<div class="modal">
            <div class="modal-title"><span class="highlight">Halla University GPT</span> Panduan Penggunaan</div>
            <div class="modal-content scrollable">
              <ul>
                <li>Ajukan pertanyaan dengan <span class="highlight">kalimat lengkap, bukan hanya kata</span>.</li>
                <li>Informasi yang saya berikan <span class="highlight">mungkin tidak 100% akurat</span>.</li>
                <li>Untuk informasi yang tepat, silakan periksa <span class="highlight">sumber atau tautan halaman terkait</span>.</li>
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
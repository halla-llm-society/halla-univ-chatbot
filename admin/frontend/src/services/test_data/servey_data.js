// src/services/test_data/survey_data.js

/**
 * 필터에 따라 랜덤한 목업 데이터를 생성하는 함수
 * @param {string} userGroup - 필터링할 사용자 그룹
 */
export const getMockSurveyData = (userGroup) => {
  // userGroup 값에 따라 기본값을 다르게 설정하여 필터가 작동하는 것처럼 보이게 함
  const baseRating = userGroup === 'faculty' ? 4.1 : (userGroup === 'external' ? 3.5 : 3.8);
  const baseParticipants = userGroup === 'all' ? 580 : (userGroup.includes('grade') ? 120 : 80);

  const participants = Math.floor(baseParticipants + Math.random() * 50);
  const avgRating = Math.max(1, Math.min(5, baseRating + (Math.random() - 0.5)));
  
  const counts = [
    Math.floor(participants * (Math.random() * 0.05 + (5 - avgRating) * 0.05)), // 1점
    Math.floor(participants * (Math.random() * 0.05 + (5 - avgRating) * 0.05)), // 2점
    Math.floor(participants * (Math.random() * 0.1 + (5 - avgRating) * 0.1)),  // 3점
    Math.floor(participants * (Math.random() * 0.2 + avgRating * 0.1)),       // 4점
    0 // 5점은 나머지를 채움
  ];
  
  const sumCounts = counts.reduce((a, b) => a + b, 0);
  counts[4] = Math.max(0, participants - sumCounts); // 5점

  const mockFeedback = [
    { id: 1, rating: 5, feedback: "사용하기 매우 편리하고 좋습니다. 특히 UI가 직관적이라 마음에 듭니다." },
    { id: 2, rating: 3, feedback: "가끔 응답 속도가 느려질 때가 있습니다. 개선이 필요해 보입니다." },
    { id: 3, rating: 4, feedback: "전반적으로 만족하지만, XX 기능이 추가되었으면 좋겠습니다." },
    { id: 4, rating: 1, feedback: "오류가 너무 많아서 사용하기 힘듭니다." },
    { id: 5, rating: 5, feedback: "최고예요!" },
  ];

  // API 응답 DTO 구조에 맞춰 반환
  return {
    totalParticipants: participants,
    averageRating: avgRating,
    ratingDistribution: {
      labels: ["1점", "2점", "3점", "4점", "5점"],
      counts: counts,
    },
    // userGroup이 'all'일 때만 답변을 보여주도록 예시 설정
    feedbackEntries: userGroup === 'all' ? mockFeedback : mockFeedback.slice(0, 2),
  };
};
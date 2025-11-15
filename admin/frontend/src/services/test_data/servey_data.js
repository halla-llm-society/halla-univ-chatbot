// src/services/test_data/servey_data.js

// 목업 데이터 생성 로직 (필터 값에 따라 약간의 변화를 줌)
function generateMockStats(userGroup) {
  const total = userGroup === 'all' ? 250 : Math.floor(Math.random() * 50) + 20;
  
  const ratingCounts = [
    Math.floor(total * 0.05),
    Math.floor(total * 0.05),
    Math.floor(total * 0.1),
    Math.floor(total * 0.3),
    total - Math.floor(total * 0.05) * 2 - Math.floor(total * 0.1) - Math.floor(total * 0.3)
  ];
  
  const speedCounts = [
    Math.floor(total * 0.1), // low
    Math.floor(total * 0.2), // mid
    total - Math.floor(total * 0.1) - Math.floor(total * 0.2) // high
  ];
  
  const qualityCounts = [
    Math.floor(total * 0.05), // low
    Math.floor(total * 0.15), // mid
    total - Math.floor(total * 0.05) - Math.floor(total * 0.15) // high
  ];

  const avgRating = (1*ratingCounts[0] + 2*ratingCounts[1] + 3*ratingCounts[2] + 4*ratingCounts[3] + 5*ratingCounts[4]) / total;

  return {
    averageRating: avgRating,
    totalParticipants: total,
    
    responseSpeedHighPercent: (speedCounts[2] / total) * 100,
    responseQualityHighPercent: (qualityCounts[2] / total) * 100,

    responseSpeedDistribution: {
      labels: ["Low", "Mid", "High"],
      counts: speedCounts,
    },
    responseQualityDistribution: {
      labels: ["Low", "Mid", "High"],
      counts: qualityCounts,
    },

    // 기존 데이터
    ratingDistribution: {
      labels: ["1점", "2점", "3점", "4점", "5점"],
      counts: ratingCounts,
    },
    feedbackEntries: total > 5 ? [
      { id: 1, rating: 5, feedback: `${userGroup} 필터 테스트: 매우 만족합니다.` },
      { id: 2, rating: 4, feedback: "대체로 만족합니다." },
    ] : [],
  };
}

/**
 * 목업 설문 통계 데이터를 반환하는 함수
 * @param {string} userGroup - 필터링할 사용자 그룹
 */
export const getMockSurveyData = (userGroup) => {
  // 실제 API처럼 userGroup 파라미터를 받아 데이터를 생성
  return generateMockStats(userGroup);
};
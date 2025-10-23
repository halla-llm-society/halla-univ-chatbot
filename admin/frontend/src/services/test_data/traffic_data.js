// src/services/test_data/traffic_data.js

import { subDays, subHours, format, eachDayOfInterval, eachHourOfInterval } from 'date-fns';

// 랜덤 데이터를 생성하는 헬퍼 함수
const generateRandomData = (points, type) => {
  const isQuery = type === 'queries';
  let total = 0;

  // 하루(day) 데이터는 시간대별 사용량 패턴을 적용
  const isDailyPattern = points.length <= 24;
  const dailyPattern = [0.1, 0.1, 0.1, 0.1, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.5, 1.3, 1.4, 1.6, 1.8, 2.0, 1.8, 1.5, 1.2, 1, 0.8, 0.6, 0.4, 0.2]; // 24시간 패턴

  const dataPoints = points.map((point, index) => {
    // 수치를 현실적으로 조정합니다.
    const baseValue = isQuery ? 200 : 40000; // 하루 평균 질문 200개, 토큰 40,000개
    const randomFactor = Math.random() * 0.4 + 0.8; // 값에 약간의 변동성(±20%)을 줌
    const patternMultiplier = isDailyPattern ? (dailyPattern[index % 24] || 1) : 1;
    
    const value = Math.floor(baseValue * randomFactor * patternMultiplier);
    total += value;

    return { time: point, [isQuery ? 'count' : 'usage']: value };
  });

  return { total, points: dataPoints };
};

// Mock 데이터를 동적으로 생성하여 반환하는 메인 함수
export const getMockTrafficData = (type, period) => {
  const now = new Date();
  let interval;
  let timeFormat;

  switch (period) {
    case 'week':
      interval = eachDayOfInterval({ start: subDays(now, 6), end: now });
      timeFormat = 'MM-dd';
      break;
    case 'month':
      interval = eachDayOfInterval({ start: subDays(now, 29), end: now });
      timeFormat = 'MM-dd';
      break;
    case 'year':
      interval = eachDayOfInterval({ start: subDays(now, 364), end: now });
      timeFormat = 'MM-dd';
      break;
    case 'day':
    default:
      interval = eachHourOfInterval({ start: subHours(now, 23), end: now });
      timeFormat = 'HH:00';
      break;
  }

  const timePoints = interval.map(date => format(date, timeFormat));
  return generateRandomData(timePoints, type);
};
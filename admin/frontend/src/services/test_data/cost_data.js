// src/services/test_data/cost_data.js

import {
  format,
  eachDayOfInterval,
  eachHourOfInterval,
  startOfDay,
  endOfDay,
  startOfWeek,
  endOfWeek,
  startOfMonth,
  endOfMonth,
  subDays,
} from 'date-fns';

const generateRandomData = (points, type, period) => {
  const isDaily = period === 'day';
  const dailyPattern = [0.1, 0.1, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.5, 1.4, 1.6, 2.0, 1.8, 1.5, 1.2, 1, 0.8, 0.6, 0.4, 0.2, 0.1, 0.1, 0.1, 0.1];

  const dataPoints = points.map((pointDate, index) => {
    let baseValue;
    switch (type) {
      case 'server': baseValue = 0.5; break;
      case 'db': baseValue = 0.2; break;
      case 'llm': default: baseValue = 1.0; break;
    }
    
    const randomFactor = Math.random() * 0.4 + 0.8;
    const patternMultiplier = isDaily ? (dailyPattern[index % 24] || 1) : 1;
    const cost = parseFloat((baseValue * randomFactor * patternMultiplier).toFixed(2));
    
    const timeLabel = isDaily ? format(pointDate, 'HH:00') : format(pointDate, 'MM-dd');
    
    return { 
      time: timeLabel,
      value: cost 
    };
  });

  return dataPoints;
};

export const getMockCostData = (type, period) => {
  const now = new Date();
  let interval;

  switch (period) {
    case 'week':
      interval = eachDayOfInterval({ start: startOfWeek(now), end: endOfWeek(now) });
      break;
    case 'month':
      interval = eachDayOfInterval({ start: startOfMonth(now), end: endOfMonth(now) });
      break;
    case 'year':
      interval = eachDayOfInterval({ start: subDays(now, 364), end: now });
      break;
    case 'day':
    default:
      interval = eachHourOfInterval({ start: startOfDay(now), end: endOfDay(now) });
      break;
  }
  return generateRandomData(interval, type, period);
};
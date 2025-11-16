// src/pages/TrafficInquiry.jsx

import { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { getTrafficQueries, getTrafficTokens } from '../services/traffic'; // API 함수 import
import styles from './styles/TrafficInquiry.module.css';

import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler, Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler, Legend
);

// 재사용 가능한 차트 컴포넌트
const ChartComponent = ({ title, total, points = [], color, loading }) => {
  const data = {

    labels: points.map(p => p.time),

    datasets: [{
      label: title,
      data: points.map(p => p.count || p.usage),
      borderColor: color,
      backgroundColor: `${color}40`, // 색상 코드 뒤에 투명도 추가
      fill: true,
      borderWidth: 1.5, pointRadius: 2, pointHoverRadius: 5, tension: 0.1,
    }],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    // 마우스 상호작용 옵션
    interaction: {
      mode: 'index',      // 'index' 모드는 동일한 X축의 모든 데이터를 찾아 세로선을 만듭니다.
      intersect: false, // 마우스가 점에 정확히 닿지 않아도 툴팁이 활성화됩니다.
    },
    // 플러그인(부가 기능) 옵션
    plugins: {
      legend: {
        display: false, // 범례는 숨김
      },
      
      // 툴팁 상세 설정
      tooltip: {
        enabled: true,
        backgroundColor: '#333', // 툴팁 배경색
        titleColor: '#fff',      // 툴팁 제목 색상
        bodyColor: '#fff',       // 툴팁 본문 색상
        padding: 10,             // 툴팁 내부 여백
        cornerRadius: 6,         // 툴팁 모서리 둥글게
        displayColors: false,    // 툴팁 앞의 작은 색상 상자 숨기기
        callbacks: {

          // 툴팁에 표시될 텍스트를 직접 정의합니다.
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              // 숫자에 콤마(,)를 추가하여 가독성을 높입니다.
              label += context.parsed.y.toLocaleString();
            }
            return label;
          }

        }
      },
    },
    scales: {
      x: { grid: { display: false } },
      y: { ticks: { beginAtZero: true } },
    },
  };

  return (
    <div className={styles.chartSection}>

      <h3 className={styles.sectionTitle}>{title}</h3>

      <div className={styles.graphCard}>
        {loading ? (
          <p className={styles.loadingText}>데이터 로딩 중...</p>
        ) : (
          <>
            <p className={styles.graphValue}>{total?.toLocaleString()}</p>
            <div className={styles.chartArea}>
              <Line options={options} data={data} />
            </div>
          </>
        )}
      </div>

    </div>
  );
};

const TrafficInquiry = () => {
  // 'day', 'week', 'month', 'year' 상태를 관리
  const [period, setPeriod] = useState('day'); 
  const [queryData, setQueryData] = useState({ total: 0, points: [] });
  const [tokenData, setTokenData] = useState({ total: 0, points: [] });
  const [loading, setLoading] = useState(true);

  // API 데이터 호출 로직
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {

        // 두 API를 동시에 호출
        const [queries, tokens] = await Promise.all([
          getTrafficQueries({ period }),
          getTrafficTokens({ period })
        ]);
        
        console.log("✅ API 응답 데이터 (질문 수):", queries);
        console.log("✅ API 응답 데이터 (토큰량):", tokens);

        setQueryData(queries);
        setTokenData(tokens);
        
      } catch (error) {
        console.error("Failed to fetch traffic data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [period]); // period 상태가 바뀔 때마다 API를 다시 호출

  const filterButtons = [
    { label: '1일', value: 'day' },
    { label: '1주', value: 'week' },
    { label: '1개월', value: 'month' },
    { label: '1년', value: 'year' },
  ];

  return (
    <section className={styles.pageContainer}>
      <div className={styles.contentWrapper}>
        <header className={styles.pageHeader}>
          <h1>트래픽 조회</h1>
        </header>

        <div className={styles.smallTitle} > 
          <h3>필터</h3> 
        </div>
      

        <div className={styles.mainContent}>
          <div className={styles.filterContainer}>
            {filterButtons.map(btn => (
              <button
                key={btn.value}
                className={period === btn.value ? styles.activeButton : styles.filterButton}
                onClick={() => setPeriod(btn.value)}
              >
                {btn.label}
              </button>
            ))}
          </div>

          <div className={styles.chartsContainer}>
            <ChartComponent
              title="질문 수"
              total={queryData.total}
              points={queryData.points}
              color="#0070f3"
              loading={loading}
            />

            <ChartComponent
              title="사용 토큰량"
              total={tokenData.total}
              points={tokenData.points}
              color="#e03131"
              loading={loading}
            />
          </div>

        </div>
      </div>
    </section>
  );
};

export default TrafficInquiry;
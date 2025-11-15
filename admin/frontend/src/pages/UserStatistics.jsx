// src/pages/UserStatistics.jsx

import { useState, useEffect } from 'react';
import styles from './styles/UserStatistics.module.css'; //
import { getSurveyStatistics } from '../services/survey'; //

import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend
);

// --- 차트 컴포넌트 (재사용) ---
// 범용성을 위한 Chart컴포넌트
const StatBarChart = ({ data, loading }) => {

  const baseColor = 'rgba(0, 112, 243, 0.8)'; // 진한 파란색
  const borderColor = 'rgba(0, 112, 243, 1)'; // 테두리 색상 (더 진하게)

  const generateShades = (base, count) => {
    const colors = [];
    for (let i = 0; i < count; i++) {
      // 투명도를 조절하여 명암 차이 (예: 0.5 ~ 0.9)
      const alpha = 0.5 + (0.4 / (count > 1 ? count - 1 : 1)) * i;
      colors.push(base.replace(/0\.8\)/, `${alpha})`)); // baseColor의 투명도를 조절
    }
    return colors;
  };
  
  const chartData = {
    labels: data?.labels || [],
    datasets: [{
      label: '응답 수',
      data: data?.counts || [],
      backgroundColor: generateShades(baseColor, data?.counts.length),
      borderColor: borderColor,
      borderWidth: 1,
    }],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return ` ${context.parsed.y} 명`;
          }
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          // 데이터가 0, 1, 2 처럼 작은 단위일 경우 stepSize: 1 적용
          // (데이터 값에 따라 유동적으로 변경하거나 옵션에서 제거 가능)
          stepSize: data?.counts.every(val => val < 10) ? 1 : undefined,
        }
      },
    },
  };

  return (
    <div className={styles.graphCard}>
      {loading ? (
        <p className={styles.loadingText}>데이터 로딩 중...</p>
      ) : (
        <div className={styles.chartArea}>
          <Bar options={options} data={chartData} />
        </div>
      )}
    </div>
  );
};

// --- 메인 페이지 컴포넌트 ---
const UserStatistics = () => {
  const [activeFilter, setActiveFilter] = useState('all');
  const [statsData, setStatsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 필터
  const filterButtons = [
    { label: '전체', value: 'all' },
    { label: '1학년', value: 'grade1' },
    { label: '2학년', value: 'grade2' },
    { label: '3학년', value: 'grade3' },
    { label: '4학년', value: 'grade4' },
    { label: '대학원생', value: 'grad_student' },
    { label: '교직원', value: 'faculty' },
    { label: '외부인', value: 'external' },
  ];

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await getSurveyStatistics({ userGroup: activeFilter });
        setStatsData(response);
      } catch (err) {
        console.error("설문 통계 데이터를 가져오는 데 실패했습니다:", err);
        setError(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [activeFilter]);

  return (
    <section className={styles.pageContainer}>
      <div className={styles.contentWrapper}>
        <header className={styles.pageHeader}>
          <h1>사용자 설문조사 통계</h1>
        </header>

        <div className={styles.mainContent}>
          {/* --- 필터 섹션 --- */}
          <div className={styles.filterContainer}>
            {filterButtons.map(btn => (
              <button
                key={btn.value}
                className={activeFilter === btn.value ? styles.activeButton : styles.filterButton}
                onClick={() => setActiveFilter(btn.value)}
              >
                {btn.label}
              </button>
            ))}
          </div>

          {/* --- 통계 요약 섹션 --- */}
          <div className={styles.statsSummaryContainer}>
            <div className={styles.statBox}>
              <h2>평균 만족도</h2>
              <p>{loading ? '-' : statsData?.averageRating?.toFixed(1) || 'N/A'} <span> / 5</span></p>
            </div>
            
            {/* 응답속도 요약 */}
            <div className={styles.statBox}>
              <h2>응답 속도 (High)</h2>
              <p>{loading ? '-' : statsData?.responseSpeedHighPercent?.toFixed(1) || 'N/A'} <span>%</span></p>
            </div>

            {/* 응답 품질 요약 */}
            <div className={styles.statBox}>
              <h2>응답 품질 (High)</h2>
              <p>{loading ? '-' : statsData?.responseQualityHighPercent?.toFixed(1) || 'N/A'} <span>%</span></p>
            </div>

            <div className={styles.statBox}>
              <h2>총 참여 인원</h2>
              <p>{loading ? '-' : statsData?.totalParticipants?.toLocaleString() || 'N/A'} <span> 명</span></p>
            </div>
          </div>

          {/* --- 차트 섹션 (Grid로 묶음) --- */}
          <div className={styles.chartGridContainer}>
            {/* 1. 만족도 분포 차트 */}
            <div className={styles.chartSection}>
              <h2 className={styles.sectionTitle}>만족도 점수 분포</h2>
              <StatBarChart data={statsData?.ratingDistribution} loading={loading} />
            </div>

            {/* 2. 응답 속도 분포 차트 */}
            <div className={styles.chartSection}>
              <h2 className={styles.sectionTitle}>응답 속도 분포</h2>
              <StatBarChart data={statsData?.responseSpeedDistribution} loading={loading} />
            </div>

            {/* 3. 응답 품질 분포 차트  */}
            <div className={styles.chartSection}>
              <h2 className={styles.sectionTitle}>응답 품질 분포</h2>
              <StatBarChart data={statsData?.responseQualityDistribution} loading={loading} />
            </div>
          </div>


          {/* --- 주관식 답변 테이블 (기존과 동일) --- */}
          {!loading && statsData?.feedbackEntries && statsData.feedbackEntries.length > 0 && (
            <div className={styles.tableSection}>
              <h2 className={styles.sectionTitle}>코멘트</h2>
              <div className={styles.tableWrapper}>
                <table className={styles.dataTable}>
                  <thead>
                    <tr>
                      <th>순서</th>
                      <th>별점</th>
                      <th>코멘트</th>
                    </tr>
                  </thead>
                  <tbody>
                    {statsData.feedbackEntries.map((item, index) => (
                      <tr key={item.id}>
                        <td>{index + 1}</td>
                        <td>{item.rating}점</td>
                        {/* feedback -> comment (백엔드 응답 스키마에 맞춰야 함) */}
                        <td>{item.feedback || item.comment}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 에러 발생 시 메시지 표시 */}
          {error && <p className={styles.loadingText}>데이터를 불러오는 중 오류가 발생했습니다.</p>}
        </div>
      </div>
    </section>
  );
};

export default UserStatistics;
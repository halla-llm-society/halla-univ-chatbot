// 2. 사용자 통계 확인 페이지

// src/pages/UserStatistics.jsx

import { useState, useEffect } from 'react';
import styles from './styles/UserStatistics.module.css'; // 새로 생성할 CSS 파일
import { getSurveyStatistics } from '../services/survey'; // 새로 생성할 API 서비스 파일

import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend
);

// --- 차트 컴포넌트 ---
const RatingChart = ({ data, loading }) => {
  const chartData = {
    labels: data?.labels || [], // 예: ["1점", "2점", "3점", "4점", "5점"]
    datasets: [{
      label: '응답 수',
      data: data?.counts || [],
      backgroundColor: 'rgba(0, 112, 243, 0.6)',
      borderColor: 'rgba(0, 112, 243, 1)',
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
          stepSize: 1,
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

  // 요구사항에 명시된 필터 목록
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

  // 필터가 변경될 때마다 데이터를 다시 불러옴
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // API 호출 시 현재 활성화된 필터 값을 파라미터로 넘김
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
              <p>{loading ? '-' : statsData?.averageRating.toFixed(1) || 'N/A'} <span> / 5</span></p>
            </div>
            <div className={styles.statBox}>
              <h2>총 참여 인원</h2>
              <p>{loading ? '-' : statsData?.totalParticipants.toLocaleString() || 'N/A'} <span> 명</span></p>
            </div>
          </div>

          {/* --- 만족도 분포 차트 --- */}
          <div className={styles.chartSection}>
            <h2 className={styles.sectionTitle}>만족도 점수 분포</h2>
            <RatingChart data={statsData?.ratingDistribution} loading={loading} />
          </div>

          {/* --- 주관식 답변 테이블 (선택 사항) --- */}
          {/* 백엔드에서 feedbackEntries가 있고, 0개 이상일 때만 테이블을 표시 */}
          {!loading && statsData?.feedbackEntries && statsData.feedbackEntries.length > 0 && (
            <div className={styles.tableSection}>
              <h2 className={styles.sectionTitle}>질문에 대한 답변</h2>
              <div className={styles.tableWrapper}>
                <table className={styles.dataTable}>
                  <thead>
                    <tr>
                      <th>순서</th>
                      <th>별점</th>
                      <th>질문에 대한 답변</th>
                    </tr>
                  </thead>
                  <tbody>
                    {statsData.feedbackEntries.map((item, index) => (
                      <tr key={item.id}>
                        <td>{index + 1}</td>
                        <td>{item.rating}점</td>
                        <td>{item.feedback}</td>
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
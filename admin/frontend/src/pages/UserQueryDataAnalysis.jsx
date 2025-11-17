// 1. 사용자 질의 데이터 분석 페이지
// src/pages/UserQueryDataAnalysis.jsx

import { useState, useEffect } from 'react';
import { FaSortUp, FaSortDown } from 'react-icons/fa'; // 정렬 아이콘 import
import { getUserQueryData } from '../services/userQuery'; // API 함수 import
import styles from './styles/UserQueryDataAnalysis.module.css'

const UserQueryDataAnalysis = () => {

  // 1. 사용자의 검색관련 로직을 관리할 state
  const [searchTerm, setSearchTerm] = useState('');
  const [query, setQuery] = useState('');
  const [searchCategory, setSearchCategory] = useState('all');
  // 날짜 범위 상태를 관리할 state 추가
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);

  // 2. 툴팁의 상태를 관리할 state
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });

  // 3.데이터 및 페이지네이션을 위한 State
  const [tableData, setTableData] = useState([]); // 현재 페이지의 테이블 데이터
  const [currentPage, setCurrentPage] = useState(1); // 현재 페이지 번호
  const [totalPages, setTotalPages] = useState(0); // 전체 페이지 수 (API로부터 받음)
  const [loading, setLoading] = useState(true); // 로딩 상태
  const [error, setError] = useState(null); // 에러 상태
  const [sortOrder, setSortOrder] = useState('desc'); // 정렬 순서를 관리할 새로운 state ('asc': 오름차순, 'desc': 내림차순)
  
  // 4. 한 페이지에 보여줄 항목 수
  const ITEMS_PER_PAGE = 20;

  // 2-1. 마우스를 셀 위에 올렸을 때 실행될 함수
  const handleMouseEnter = (e, content) => {
    // 셀의 내용이 실제로 잘렸을 때만 툴팁을 보여주도록 함
    if (e.currentTarget.scrollWidth > e.currentTarget.clientWidth) {
      const rect = e.currentTarget.getBoundingClientRect(); // 셀의 위치와 크기 정보
      setTooltipContent(content);
      setTooltipPosition({ 
        top: rect.bottom + 5, // 셀 하단에서 5px 아래
        left: rect.left + 5    // 셀 좌측에서 5px 오른쪽
      });
      setTooltipVisible(true);
    }
  };

  // 2-1. 마우스가 셀을 벗어났을 때 실행될 함수
  const handleMouseLeave = () => {
    setTooltipVisible(false);
  };

  // 3-1. API 데이터 호출 로직
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // API 요청 파라미터
        const params = {
          page: currentPage,
          cnt: ITEMS_PER_PAGE,
          sort: sortOrder,
          search: query,
          category: searchCategory,
          startDate: startDate,
          endDate: endDate,
        };
        
        console.log("🚀 API 요청 데이터:", params);
        const response = await getUserQueryData(params);
        setTableData(response.data || []);
        setTotalPages(response.totalPages);
        
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [currentPage, sortOrder, query, startDate, endDate]); // currentPage가 바뀔 때마다 API를 다시 호출

  // 4-1. 페이지네이션 헨들러
  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  // 4-2. 정렬순서 헨들러
  const handleSort = () => {
    setSortOrder(currentOrder => (currentOrder === 'asc' ? 'desc' : 'asc'));
    setCurrentPage(1); // 정렬 순서가 바뀌면 1페이지부터 다시 보도록 설정
  };

  // 4-3. 검색 버튼 클릭 핸들러
  const handleSearch = () => {
    setCurrentPage(1); // 검색 시에는 1페이지부터 보도록 설정
    setQuery(searchTerm); // 현재 입력된 searchTerm을 확정된 query로 설정 -> useEffect 트리거

    // 입력값이 'YYYY-MM-DD ~ YYYY-MM-DD' 형식인지 정규식으로 확인
    const dateRangeRegex = /^\d{4}-\d{2}-\d{2}\s*~\s*\d{4}-\d{2}-\d{2}$/;
    const singleDateRegex = /^\d{4}-\d{2}-\d{2}$/;

    if (dateRangeRegex.test(searchTerm)) {
      // 케이스 1: 날짜 범위 검색 ("YYYY-MM-DD ~ YYYY-MM-DD")
      const [start, end] = searchTerm.split('~').map(s => s.trim());
      setStartDate(start);
      setEndDate(end);
      setQuery(''); // 일반 검색어는 비움
    } else if (singleDateRegex.test(searchTerm)) {
      // 케이스 2: 단일 날짜 검색 ("YYYY-MM-DD")
      // 시작일과 종료일을 같은 날짜로 설정하여 해당 날짜 하루만 검색
      setStartDate(searchTerm.trim());
      setEndDate(searchTerm.trim());
      setQuery(''); // 일반 검색어는 비움
    } else {
      // 일반 키워드 검색일 경우
      setQuery(searchTerm);
      setStartDate(null); // 날짜 검색 조건은 비움
      setEndDate(null);
    }

  };

  // 4-3-1. Enter 키로 검색 실행
  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  // 시간대 변환함수
  const formatKST = (isoString) => {
    if (!isoString) return 'N/A';
    try {
      const date = new Date(isoString);
      
      // 'ko-KR' 로캘과 'Asia/Seoul' 시간대를 사용해 KST로 변환
      // "2025. 11. 17. 19:00:00" 같은 형식으로 자동 변환됩니다.
      return date.toLocaleString('sv-SE', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false, // 24시간 표기
        timeZone: 'Asia/Seoul'
      });
    } catch (e) {
      return isoString; // 파싱 실패 시 원본 표시
    }
  };

  
  return (
    // 1. 외부 컨테이너: 페이지 전체를 감싸고 중앙 정렬을 담당
    <section className={styles.pageContainer}>
      
      {/* 2. 내부 컨테이너: 실제 콘텐츠를 담고 최대 너비를 가짐 */}
      <div className={styles.contentWrapper}>
        
        {/* 페이지 헤더: 제목과 버튼 등 */}
        <header className={styles.pageHeader}>
          <h1>사용자 질의 데이터 분석</h1>

          <div className={styles.searchContainer}>
            {/* 카테고리 선택 드롭다운 */}
            <select 
              className={styles.searchCategory} 
              value={searchCategory} 
              onChange={(e) => setSearchCategory(e.target.value)}
            >
              <option value="all">전체</option>
              <option value="question">사용자 질문</option>
              <option value="answer">AI 답변</option>
              <option value="decision">AI 판단 분기점</option>
            </select>

            <input 
              type="text" 
              className={styles.searchInput}
              placeholder="검색어 또는 YYYY-MM-DD"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button className={styles.searchButton} onClick={handleSearch}>
              검색
            </button>
          </div>

        </header>

        {/* 메인 콘텐츠 영역 */}
        <div className={styles.mainContent}>
          {/* 여기에 차트, 테이블 등 데이터 관련 컴포넌트가 들어감. */}
          <table className={styles.dataTable}>

            <thead>
              <tr>

                <th>
                  <button className={styles.sortButton} onClick={handleSort}>
                    날짜
                    {sortOrder === 'asc' ? <FaSortUp /> : <FaSortDown />}
                  </button>
                </th>

                <th>사용자 질문</th>
                <th>AI 답변</th>
                <th>AI 판단 분기점</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr><td colSpan="4">로딩 중...</td></tr>
              ) : error ? (
                <tr><td colSpan="4">오류가 발생했습니다: {error.message}</td></tr>
              ) : (
                tableData.map((rowData, index) => (
                  <tr key={index}>
                    <td onMouseEnter={(e) => handleMouseEnter(e, formatKST(rowData.date))} onMouseLeave={handleMouseLeave}>
                      {formatKST(rowData.date)}
                    </td>
                    <td onMouseEnter={(e) => handleMouseEnter(e, rowData.question)} onMouseLeave={handleMouseLeave}>{rowData.question}</td>
                    <td onMouseEnter={(e) => handleMouseEnter(e, rowData.answer)} onMouseLeave={handleMouseLeave}>{rowData.answer}</td>
                    <td onMouseEnter={(e) => handleMouseEnter(e, rowData.decision)} onMouseLeave={handleMouseLeave}>{rowData.decision}</td>
                  </tr>
                ))
              )}
            </tbody>

          </table>
        </div>

        {/* --- 페이지네이션 UI --- */}
        <div className={styles.paginationContainer}>
          {/* 맨 앞으로 가기 버튼 */}
          <button
            onClick={() => handlePageChange(1)}
            disabled={currentPage === 1 || loading}
            className={styles.pageButton}
          >
            &lt;&lt;
          </button>

          {/* 이전 페이지 버튼 */}
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1 || loading}
            className={styles.pageButton}
          >
            &lt;
          </button>

          {/* 페이지 번호 버튼들 */}
          {Array.from({ length: totalPages }, (_, index) => (
            <button
              key={index + 1}
              onClick={() => handlePageChange(index + 1)}
              className={`${styles.pageButton} ${currentPage === index + 1 ? styles.activePage : ''}`}
              disabled={loading}
            >
              {index + 1}
            </button>
          ))}

          {/* 다음 페이지 버튼 */}
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages || loading}
            className={styles.pageButton}
          >
            &gt;
          </button>

          {/* 맨 뒤로 가기 버튼 */}
          <button
            onClick={() => handlePageChange(totalPages)}
            disabled={currentPage === totalPages || loading}
            className={styles.pageButton}
          >
            &gt;&gt;
          </button>
        </div>
      </div>

      {/* --- 툴팁 부분 --- */}
      <div 
        className={`${styles.tooltipBox} ${tooltipVisible ? styles.visible : ''}`}
        style={{ top: `${tooltipPosition.top}px`, left: `${tooltipPosition.left}px` }}
      >
        {tooltipContent}
      </div>
      
    </section>
  );
};

export default UserQueryDataAnalysis;
import apiClient from './apiClient';

/**
 * 현재 서버에 설정된 데이터베이스 환경을 조회합니다. (stg 또는 prod)
 * @returns {Promise<{environment: string}>}
 */
export const getCurrentDatabaseEnv = async () => {
  try {
    const response = await apiClient.get('/api/current-database');
    return response.data; // { environment: "stg" } 또는 { environment: "prod" }
  } catch (error) {
    console.error("Error fetching current database environment:", error);
    // 오류 발생 시 기본값으로 'stg'를 반환하거나 예외를 다시 던질 수 있습니다.
    // 여기서는 UI가 'stg'를 기본으로 하도록 'stg'를 반환합니다.
    return { environment: 'stg' }; 
  }
};

/**
 * 서버의 데이터베이스 연결 환경을 전환합니다.
 * @param {('stg' | 'prod')} environment - 전환할 환경
 * @returns {Promise<any>}
 */
export const switchDatabaseEnv = async (environment) => {
  if (!['stg', 'prod'].includes(environment)) {
    throw new Error("Invalid environment. Must be 'stg' or 'prod'.");
  }
  
  try {
    const payload = { environment };
    const response = await apiClient.post('/api/switch-database', payload);
    return response.data;
  } catch (error) {
    console.error("Error switching database environment:", error);
    throw error; // 컴포넌트에서 오류를 처리할 수 있도록 다시 던짐
  }
};
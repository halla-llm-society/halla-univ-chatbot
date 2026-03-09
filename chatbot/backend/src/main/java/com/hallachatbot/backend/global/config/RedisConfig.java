package com.hallachatbot.backend.global.config;

import java.time.Duration;
import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.data.redis.connection.RedisClusterConfiguration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceClientConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import io.lettuce.core.cluster.ClusterClientOptions;
import io.lettuce.core.cluster.ClusterTopologyRefreshOptions;

/**
 * <b>Redis (AWS ElastiCache 호환) 전역 설정 클래스</b>
 *
 * <p>
 * 애플리케이션의 실행 환경(Profile)에 따라 Redis 연결 방식을 동적으로 구성합니다.
 * 운영 및 스테이징 환경에서는 클러스터 모드를 사용하며,
 * 로컬 개발 환경에서는 가벼운 단일 모드를 사용.
 * </p>
 */
@Configuration
public class RedisConfig {

	/**
	 * 운영 및 스테이징 환경용 Redis Cluster 커넥션 팩토리 빈을 생성.
	 * <p>
	 * <b>주요 설정 요소:</b>
	 * <ul>
	 * <li><b>Topology Refresh:</b> AWS ElastiCache(Valkey/Redis)의 노드 장애나 스케일 아웃 등으로 인한
	 * Failover 발생 시, 애플리케이션 재시작 없이 클러스터 맵을 자동으로 갱신.</li>
	 * <li><b>SSL 적용:</b> AWS 인프라의 '전송 중 암호화' 설정에 대응하기 위해 TLS 통신을 활성화.</li>
	 * </ul>
	 * </p>
	 *
	 * @param clusterNodes 환경변수 또는 Parameter Store를 통해 주입받은 클러스터 구성 엔드포인트 목록
	 * @return 자동 갱신 및 SSL 옵션이 적용된 {@link LettuceConnectionFactory} 객체
	 */
	@Bean
	@Profile({"stg", "prod"})
	public RedisConnectionFactory clusterRedisConnectionFactory(
		@Value("${spring.data.redis.cluster.nodes}") List<String> clusterNodes) {

		RedisClusterConfiguration clusterConfig = new RedisClusterConfiguration(clusterNodes);

		// AWS 클러스터 노드 변경 시 자동으로 연결을 갱신
		ClusterTopologyRefreshOptions refreshOptions = ClusterTopologyRefreshOptions.builder()
			.enablePeriodicRefresh(Duration.ofMinutes(10))
			.enableAllAdaptiveRefreshTriggers()
			.build();

		ClusterClientOptions clientOptions = ClusterClientOptions.builder()
			.topologyRefreshOptions(refreshOptions)
			.build();

		// 클라이언트 설정에 Refresh Options와 SSL 보안 적용
		LettuceClientConfiguration clientConfig = LettuceClientConfiguration.builder()
			.clientOptions(clientOptions)
			.useSsl()
			.build();

		return new LettuceConnectionFactory(clusterConfig, clientConfig);
	}

	/**
	 * 로컬 개발 환경용 Redis Standalone 커넥션 팩토리 빈을 생성.
	 *
	 * <p>
	 * 클러스터 토폴로지 갱신이나 SSL 암호화 등 무거운 설정 없이,
	 * Docker 등으로 띄운 로컬 단일 Redis 인스턴스에 빠르게 연결하기 위해 사용.
	 * </p>
	 *
	 * @param host Redis 서버 호스트 주소
	 * @param port Redis 서버 포트
	 * @return 단일 노드 연결 옵션이 적용된 {@link LettuceConnectionFactory} 객체
	 */
	@Bean
	@Profile("!stg && !prod")
	public RedisConnectionFactory standaloneRedisConnectionFactory(
		@Value("${spring.data.redis.host}") String host,
		@Value("${spring.data.redis.port}") int port) {

		return new LettuceConnectionFactory(new RedisStandaloneConfiguration(host, port));
	}

	/**
	 * 애플리케이션에서 Redis 데이터를 직렬화 및 역직렬화하기 위한 템플릿 빈을 생성.
	 * * <p>
	 * 스프링의 기본 직렬화 방식은 데이터를 이진 형태로 저장하여
	 * 직접 조회 시 가독성이 떨어지고, 다른 언어/플랫폼과의 데이터 호환이 어려움.
	 * 이를 해결하기 위해 Key는 문자열로, Value는 범용적인 JSON 형태로 변환하여 저장.
	 * </p>
	 *
	 * @param connectionFactory 현재 활성화된 프로파일에 따라 주입된 커넥션 팩토리
	 * @return 커스텀 직렬화 설정이 완료된 {@link RedisTemplate} 객체
	 */
	@Bean
	public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
		RedisTemplate<String, Object> template = new RedisTemplate<>();
		template.setConnectionFactory(connectionFactory);

		// 사람이 직접 읽을 수 있는 형태로 데이터 직렬화
		template.setKeySerializer(new StringRedisSerializer());
		template.setValueSerializer(new GenericJackson2JsonRedisSerializer());

		return template;
	}
}

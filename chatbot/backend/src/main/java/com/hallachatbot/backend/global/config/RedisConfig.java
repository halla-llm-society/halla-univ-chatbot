package com.hallachatbot.backend.global.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceClientConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

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
	 * 운영 및 스테이징 환경용 AWS Redis 커넥션 팩토리 빈을 생성.
	 * <p>
	 * <b>주요 설정 요소:</b>
	 * <ul>
	 * <li><b>Standalone 모드:</b> AWS ElastiCache 단일 연결 사용.</li>
	 * <li><b>SSL 적용:</b> AWS 인프라의 '전송 중 암호화' 필수 설정에 대응하기 위해 TLS 통신을 활성화.</li>
	 * </ul>
	 * </p>
	 */
	@Bean
	@Profile({"stg", "prod"})
	public RedisConnectionFactory awsRedisConnectionFactory(
		@Value("${REDIS_HOST}") String redisHostString) {

		String host = redisHostString;
		int port = 6379;

		// 호스트/포트 분리
		if (host.startsWith("rediss://")) {
			host = host.substring(9);
		} else if (host.startsWith("redis://")) {
			host = host.substring(8);
		}

		if (host.contains(":")) {
			String[] parts = host.split(":");
			host = parts[0];
			port = Integer.parseInt(parts[1]);
		}

		// 단일 노드 설정 구성
		RedisStandaloneConfiguration config = new RedisStandaloneConfiguration(host, port);

		// SSL 적용
		LettuceClientConfiguration clientConfig = LettuceClientConfiguration.builder()
			.useSsl()
			.build();

		return new LettuceConnectionFactory(config, clientConfig);
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

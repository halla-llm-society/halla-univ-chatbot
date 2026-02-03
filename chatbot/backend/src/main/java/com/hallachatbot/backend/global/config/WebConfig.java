package com.hallachatbot.backend.global.config;

import java.util.List;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import com.hallachatbot.backend.global.resolver.ChatSessionArgumentResolver;

import lombok.RequiredArgsConstructor;

/**
 * <b>웹 MVC 전역 설정 (WebConfig)</b>
 *
 * <p>
 * Spring MVC의 동작 방식을 커스터마이징하기 위한 설정 클래스임.
 * {@link WebMvcConfigurer}를 구현하여 커스텀 파라미터 리졸버를 추가하고,
 * 프론트엔드와의 통신을 위한 CORS 정책을 정의함.
 * </p>
 * @author pwk0131
 */
@Configuration
@RequiredArgsConstructor
public class WebConfig implements WebMvcConfigurer {

	@Value("${app.cors.allowed-origins:http://localhost:5173}")
	private List<String> allowedOrigins;

	private final ChatSessionArgumentResolver chatSessionArgumentResolver;

	/**
	 * 커스텀 Argument Resolver 등록
	 *
	 * <p>
	 * {@link com.hallachatbot.backend.global.annotation.ChatSession} 어노테이션 처리를 위한
	 * {@link ChatSessionArgumentResolver}를 MVC 파이프라인에 추가함.
	 * </p>
	 */
	@Override
	public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
		resolvers.add(chatSessionArgumentResolver);
	}

	/**
	 * CORS (Cross-Origin Resource Sharing) 설정
	 *
	 * <p>
	 * 프론트엔드 애플리케이션(React, Vue 등)과 백엔드 API 간의 자원 공유를 허용하기 위한 정책을 설정함.
	 * </p>
	 *
	 * <ul>
	 * <li><b>허용 Origin:</b> 로컬 개발 환경(3000, 5173 포트)</li>
	 * <li><b>허용 Method:</b> GET, POST, PUT, DELETE, OPTIONS</li>
	 * <li><b>Credentials:</b> 쿠키(Cookie) 기반 인증을 위해 true로 설정</li>
	 * </ul>
	 */
	@Override
	public void addCorsMappings(CorsRegistry registry) {
		registry.addMapping("/**")
			.allowedOriginPatterns(allowedOrigins.toArray(new String[0]))
			.allowedMethods("GET", "POST", "OPTIONS")
			.allowedHeaders("*")
			.allowCredentials(true)
			.maxAge(3600);
	}
}

package com.hallachatbot.backend.global.config;

import java.util.List;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import com.hallachatbot.backend.global.resolver.ChatSessionArgumentResolver;

import lombok.RequiredArgsConstructor;

@Configuration
@RequiredArgsConstructor
public class WebConfig implements WebMvcConfigurer {

	private final ChatSessionArgumentResolver chatSessionArgumentResolver;

	@Override
	public void addArgumentResolvers(List<HandlerMethodArgumentResolver> resolvers) {
		resolvers.add(chatSessionArgumentResolver);
	}

	@Override
	public void addCorsMappings(CorsRegistry registry) {
		registry.addMapping("/**") // 모든 경로에 대해
			.allowedOriginPatterns("http://localhost:3000", "http://localhost:5173") // 허용할 프론트엔드 주소
			.allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS") // 허용할 HTTP 메서드
			.allowedHeaders("*") // 모든 헤더 허용
			.allowCredentials(true) // 쿠키(Session ID) 인증 요청 허용
			.maxAge(3600); // 전송 요청(Preflight) 캐시 시간
	}
}

package com.hallachatbot.backend.global.resolver;

import java.time.Duration;

import org.bson.types.ObjectId;
import org.springframework.core.MethodParameter;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;

import com.hallachatbot.backend.global.annotation.ChatSession;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
public class ChatSessionArgumentResolver implements HandlerMethodArgumentResolver {

	@Override
	public boolean supportsParameter(MethodParameter parameter) {
		// @ChatSession 어노테이션이 붙어있고, 타입이 String인 경우에만 동작
		return parameter.hasParameterAnnotation(ChatSession.class)
			&& String.class.isAssignableFrom(parameter.getParameterType());
	}

	@Override
	public Object resolveArgument(MethodParameter parameter, ModelAndViewContainer mavContainer,
		NativeWebRequest webRequest, WebDataBinderFactory binderFactory) {

		HttpServletRequest request = (HttpServletRequest)webRequest.getNativeRequest();
		HttpServletResponse response = (HttpServletResponse)webRequest.getNativeResponse();

		String chatId = resolveChatIdFromCookie(request);

		// 유효한 chatId가 없으면 새로 생성 후 쿠키 발급
		if (chatId == null || !ObjectId.isValid(chatId)) {
			chatId = new ObjectId().toHexString();
			setCookie(response, chatId);
			log.info("New chat session created: {}", chatId);
		}

		return chatId;
	}

	private String resolveChatIdFromCookie(HttpServletRequest request) {
		Cookie[] cookies = request.getCookies();
		if (cookies == null) {
			return null;
		}
		for (Cookie cookie : cookies) {
			if ("chatId".equals(cookie.getName())) {
				return cookie.getValue();
			}
		}
		return null;
	}

	private void setCookie(HttpServletResponse response, String chatId) {
		if (response == null) {
			return;
		}

		ResponseCookie cookie = ResponseCookie.from("chatId", chatId)
			.maxAge(Duration.ofSeconds(86400)) // 1일
			.secure(true)     // HTTPS 적용 시 필수 (로컬 개발 환경에 따라 조정 필요)
			.httpOnly(false)  // JS 접근 허용 여부
			.path("/")
			.build();

		response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString());
	}
}

package com.hallachatbot.backend.global.resolver;

import java.time.Duration;
import java.util.Arrays;
import java.util.Optional;

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

/**
 * <b>ChatSession 파라미터 리졸버</b>
 *
 * <p>
 * 컨트롤러 메서드 파라미터 중 {@link ChatSession} 어노테이션이 부착된 대상에 대해
 * 사용자 세션 ID(chatId)를 추출하거나 생성하여 주입함.
 * </p>
 *
 * <ul>
 * <li><b>동작 원리:</b> HTTP 요청의 쿠키에서 'chatId' 값을 탐색.</li>
 * <li><b>신규 세션:</b> 유효한 쿠키가 없을 경우, 새로운 ObjectId를 생성하여 응답 쿠키(Set-Cookie)로 설정 후 반환.</li>
 * <li><b>적용 대상:</b> {@code @ChatSession} 어노테이션이 붙은 {@code String} 타입 파라미터.</li>
 * </ul>
 * @author pwk0131
 */
@Slf4j
@Component
public class ChatSessionArgumentResolver implements HandlerMethodArgumentResolver {

	/**
	 * 파라미터 지원 여부 확인
	 *
	 * <p>
	 * {@link ChatSession} 어노테이션이 존재하고, 파라미터 타입이 {@link String}인 경우에만 수행.
	 * </p>
	 *
	 * @param parameter 검사 대상 메서드 파라미터
	 * @return 지원 여부 (true/false)
	 */
	@Override
	public boolean supportsParameter(MethodParameter parameter) {
		// @ChatSession 어노테이션이 붙어있고, 타입이 String인 경우에만 동작
		return parameter.hasParameterAnnotation(ChatSession.class)
			&& String.class.isAssignableFrom(parameter.getParameterType());
	}

	/**
	 * 파라미터 값(chatId) 해석 및 주입
	 *
	 * <p>
	 * 1. 요청 쿠키에서 'chatId' 값 조회.<br>
	 * 2. 값이 없거나 유효하지 않은 포맷(ObjectId)일 경우 신규 ID 생성.<br>
	 * 3. 신규 생성 시 응답 헤더에 쿠키 설정 추가.
	 * </p>
	 *
	 * @return 컨트롤러 파라미터에 전달될 세션 ID 문자열
	 */
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
		return Optional.ofNullable(request.getCookies())
			.stream()
			.flatMap(Arrays::stream)
			.filter(cookie -> "chatId".equals(cookie.getName()))
			.map(Cookie::getValue)
			.findFirst()
			.orElse(null);
	}

	/**
	 * 클라이언트 브라우저에 쿠키 설정 (Set-Cookie)
	 *
	 * <ul>
	 * <li>Max-Age: 1일 (86400초)</li>
	 * <li>Secure: true (HTTPS 전용)</li>
	 * <li>HttpOnly: true (JS 접근 불가)</li>
	 * <li>Path: / (모든 경로)</li>
	 * </ul>
	 */
	private void setCookie(HttpServletResponse response, String chatId) {
		if (response == null) {
			return;
		}

		ResponseCookie cookie = ResponseCookie.from("chatId", chatId)
			.maxAge(Duration.ofSeconds(86400))
			.secure(true)
			.httpOnly(true)
			.path("/")
			.build();

		response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString());
	}
}

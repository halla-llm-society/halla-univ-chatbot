package com.hallachatbot.backend.chat.controller;

import java.time.Duration;
import java.util.Collections;
import java.util.List;

import org.bson.types.ObjectId;
import org.springframework.http.ResponseCookie;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hallachatbot.backend.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.chat.entity.ChatMessage;
import com.hallachatbot.backend.chat.repository.ChatMessageRepository;
import com.hallachatbot.backend.chat.service.ChatService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;

/**
 * 채팅 도메인 컨트롤러
 *
 * <p>
 * Python의 app/api/chat.py 리팩토링<br>
 * 엔드포인트: /api/chat
 * </p>
 *
 * @author pwk0131
 */
@Slf4j
@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

	private final ChatService chatService;
	private final ChatMessageRepository chatMessageRepository;

	/**
	 * 채팅 스트리밍 엔드포인트
	 *
	 * <p>
	 * POST /api/chat<br>
	 * 쿠키(chatId)를 확인하여 세션을 관리하고 AI 응답을 SSE로 반환
	 * </p>
	 *
	 * @param request 사용자 요청 DTO
	 * @param cookieChatId 쿠키에 저장된 chatId (없을 수 있음)
	 * @param response HTTP 응답 객체 (쿠키 설정용)
	 * @return SSE 스트림
	 */
	@PostMapping
	public Flux<ServerSentEvent<String>> chat(
		@Valid @RequestBody ChatRequest request,
		@CookieValue(value = "chatId", required = false) String cookieChatId,
		ServerHttpResponse response
	) {
		String currentChatId;
		boolean isNewUser = false;
		boolean isTampered = false;

		// 1. 쿠키 검증 및 ID 결정
		if (cookieChatId != null && ObjectId.isValid(cookieChatId)) {
			currentChatId = cookieChatId;
		} else {
			if (cookieChatId != null) {
				log.warn("잘못된 쿠키 감지됨: {}", cookieChatId);
				isTampered = true;
			}
			currentChatId = new ObjectId().toHexString();
			isNewUser = true;
		}

		// 2. 새로운 유저(또는 변조됨)라면 쿠키 재발급
		if (isNewUser) {
			ResponseCookie cookie = ResponseCookie.from("chatId", currentChatId)
				.maxAge(Duration.ofSeconds(86400))
				.secure(true)
				.httpOnly(false)
				.path("/")
				.build();
			response.addCookie(cookie);
		}

		// 3. 서비스 호출
		return chatService.startChat(request, currentChatId, isTampered);
	}

	/**
	 * 대화 히스토리 조회 엔드포인트
	 *
	 * <p>
	 * GET /api/chat/history<br>
	 * 현재 쿠키의 chatId를 기반으로 최근 대화 내역 반환
	 * </p>
	 *
	 * @param cookieChatId 쿠키에 저장된 chatId
	 * @return 대화 내역 리스트 (user/assistant 쌍)
	 */
	@GetMapping("/history")
	public List<ChatHistoryResponse> getHistory(
		@CookieValue(value = "chatId", required = false) String cookieChatId
	) {
		if (cookieChatId == null || !ObjectId.isValid(cookieChatId)) {
			return Collections.emptyList();
		}

		List<ChatMessage> rawHistory = chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(cookieChatId);

		Collections.reverse(rawHistory);

		return rawHistory.stream()
			.flatMap(msg -> java.util.stream.Stream.of(
				ChatHistoryResponse.user(msg.getQuestion()),
				ChatHistoryResponse.assistant(msg.getAnswer())
			))
			.toList();
	}
}

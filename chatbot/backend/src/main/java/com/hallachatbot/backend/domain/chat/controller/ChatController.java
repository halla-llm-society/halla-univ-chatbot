package com.hallachatbot.backend.domain.chat.controller;

import java.util.List;

import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.domain.chat.service.ChatService;
import com.hallachatbot.backend.global.annotation.ChatSession;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;

/**
 * <b>채팅 도메인 API 컨트롤러</b>
 *
 * <p>
 * 클라이언트의 채팅 요청을 처리하는 진입점.
 * AI 모델과의 실시간 대화 스트리밍(SSE) 및 과거 대화 이력 조회 기능을 제공함.
 * </p>
 *
 * <ul>
 * <li>Base URL: {@code /api/chat}</li>
 * <li>주요 기능: 메시지 전송(Streaming), 히스토리 조회</li>
 * </ul>
 *
 * @author pwk0131
 */
@Slf4j
@Tag(name = "Chat API", description = "AI 챗봇 대화 수행 및 히스토리 관리")
@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

	private final ChatService chatService;

	/**
	 * <b>채팅 메시지 전송 및 답변 스트리밍</b>
	 *
	 * <p>
	 * 사용자의 질문을 입력받아 AI 서비스의 답변을 Server-Sent Events(SSE) 방식으로 실시간 스트리밍함.<br>
	 * {@link ChatSession} 어노테이션을 통해 쿠키에서 세션 ID를 추출하거나 신규 발급하여 대화 맥락을 유지함.
	 * </p>
	 *
	 * @param request 사용자 질문 및 언어 설정이 포함된 요청 DTO
	 * @param chatId  사용자 식별 세션 ID (쿠키에서 자동 주입, Swagger 숨김 처리)
	 * @return AI 답변 데이터 스트림 (Flux&lt;ServerSentEvent&gt;)
	 * @see com.hallachatbot.backend.global.resolver.ChatSessionArgumentResolver
	 */
	@Operation(summary = "채팅 답변 스트리밍", description = "사용자의 질문을 입력받아 AI 답변을 SSE(Server-Sent Events)로 실시간 스트리밍합니다.")
	@ApiResponses(value = {
		@ApiResponse(
			responseCode = "200",
			description = "성공 (스트리밍 시작)",
			content = @Content(mediaType = "text/event-stream",
				schema = @Schema(implementation = ServerSentEvent.class))),
		@ApiResponse(responseCode = "400", description = "잘못된 요청 (필수 값 누락, 유효성 검증 실패)"),
		@ApiResponse(responseCode = "429", description = "요청 한도 초과"),
		@ApiResponse(responseCode = "500", description = "서버 내부 오류 또는 AI 서비스 연동 실패")
	})
	@PostMapping
	public Flux<ServerSentEvent<String>> chat(
		@Parameter(description = "채팅 요청 정보 (질문, 모델 설정 등)", required = true)
		@Valid @RequestBody ChatRequest request,
		@Parameter(hidden = true)
		@ChatSession String chatId
	) {
		return chatService.startChat(request, chatId);
	}

	/**
	 * <b>대화 히스토리 조회</b>
	 *
	 * <p>
	 * 현재 세션(Cookie: chatId)에 해당하는 최근 대화 내역을 조회함.<br>
	 * 기본적으로 최근 6건(User-Assistant 쌍)의 대화를 최신순으로 반환함.
	 * </p>
	 *
	 * @param chatId 사용자 식별 세션 ID (쿠키에서 자동 주입, Swagger 숨김 처리)
	 * @return 대화 내역 리스트 (Role, Content 구조)
	 */
	@Operation(summary = "대화 히스토리 조회", description = "쿠키에 저장된 chatId를 기반으로 최근 대화 내역을 조회합니다.")
	@ApiResponses(value = {
		@ApiResponse(responseCode = "200", description = "조회 성공"),
		@ApiResponse(responseCode = "401", description = "인증 실패 (쿠키 없음)")
	})

	@GetMapping("/history")
	public List<ChatHistoryResponse> getHistory(
		@Parameter(hidden = true)
		@ChatSession String chatId
	) {
		return chatService.getChatHistory(chatId);
	}
}

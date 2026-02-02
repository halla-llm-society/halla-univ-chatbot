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
 * 채팅 도메인 컨트롤러
 *
 * <p>
 * 엔드포인트: /api/chat
 * </p>
 *
 * @author pwk0131
 */
@Slf4j
@Tag(name = "Chat API", description = "AI 챗봇 대화 및 히스토리 관리")
@RestController
@RequestMapping("/api/chat")
@RequiredArgsConstructor
public class ChatController {

	private final ChatService chatService;

	/**
	 * 채팅 스트리밍 엔드포인트
	 *
	 * <p>
	 * POST /api/chat<br>
	 * 쿠키(chatId)를 확인하여 세션을 관리하고 AI 응답을 SSE로 반환
	 * </p>
	 *
	 * @param request 사용자 요청 DTO
	 * @return SSE 스트림
	 */
	@Operation(summary = "채팅 답변 스트리밍", description = "사용자의 질문을 입력받아 AI 답변을 SSE(Server-Sent Events)로 실시간 스트리밍합니다.")
	@ApiResponses(value = {
		@ApiResponse(
			responseCode = "200",
			description = "성공 (스트리밍 시작)",
			content = @Content(mediaType = "text/event-stream",
				schema = @Schema(implementation = ServerSentEvent.class))),
		@ApiResponse(responseCode = "400", description = "잘못된 요청 (입력값 누락 등)"),
		@ApiResponse(responseCode = "429", description = "요청 한도 초과 (일일/월간 사용량 제한)"),
		@ApiResponse(responseCode = "500", description = "서버 내부 오류")
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
	 * 대화 히스토리 조회 엔드포인트
	 *
	 * <p>
	 * GET /api/chat/history<br>
	 * 현재 쿠키의 chatId를 기반으로 최근 대화 내역 반환
	 * </p>
	 *
	 * @return 대화 내역 리스트 (user/assistant 쌍)
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

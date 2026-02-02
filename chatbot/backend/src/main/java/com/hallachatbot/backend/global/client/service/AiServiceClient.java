package com.hallachatbot.backend.global.client.service;

import java.util.List;

import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.global.client.dto.AiServiceResponse;

import reactor.core.publisher.Flux;

/**
 * <b>AI 서비스 연동 클라이언트</b>
 * <b><p>
 * SSE(또는 NDJSON) 스트림을 받아 처리함
 * </p></b>
 *
 * @author pwk0131
 */
public interface AiServiceClient {

	/**
	 * AI 챗봇 스트리밍 요청
	 *
	 * @param request 사용자 요청 정보
	 * @param history 대화 히스토리
	 * @return AI 응답 스트림 (Flux)
	 */
	Flux<AiServiceResponse> streamChat(ChatRequest request, List<ChatHistoryResponse> history);
}

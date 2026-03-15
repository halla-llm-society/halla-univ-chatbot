package com.hallachatbot.backend.domain.chat.client.service;

import java.util.List;

import com.hallachatbot.backend.domain.chat.client.dto.AiServiceResponse;
import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;

import reactor.core.publisher.Flux;

/**
 * <b>AI 서비스 연동 클라이언트 인터페이스</b>
 *
 * <p>
 * 외부 AI 모델 서버와의 HTTP 통신을 담당.
 * WebClient를 사용하여 논블로킹(Non-blocking) 방식의 스트리밍 응답을 처리.
 * </p>
 *
 * @author pwk0131
 */
public interface AiServiceClient {

	/**
	 * <b>AI 답변 스트리밍 요청</b>
	 *
	 * <p>
	 * 사용자 질문과 대화 내역을 기반으로 AI 서버에 질의하고,
	 * 실시간으로 생성되는 답변을 Flux 스트림으로 반환.
	 * </p>
	 *
	 * @param request 사용자 질문 및 설정 정보
	 * @param history 대화 문맥 유지를 위한 과거 메시지 리스트
	 * @return AI 응답 객체 스트림 (Flux&lt;AiServiceResponse&gt;)
	 */
	Flux<AiServiceResponse> streamChat(String chatId, ChatRequest request, List<ChatHistoryResponse> history);
}

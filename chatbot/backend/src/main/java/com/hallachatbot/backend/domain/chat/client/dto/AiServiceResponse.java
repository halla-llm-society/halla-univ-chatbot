package com.hallachatbot.backend.domain.chat.client.dto;

import java.util.Map;

/**
 * <b>AI 서비스 응답 DTO</b>
 *
 * <p>
 * AI 모델 서버로부터 수신되는 SSE(Server-Sent Events) 스트림의 데이터 단위.<br>
 * 스트리밍 특성상 완성된 문장이 아닌 조각(Delta) 또는 메타데이터 형태로 전달됨.
 * </p>
 *
 * @param type    응답 유형 (예: "delta", "metadata", "error")
 * @param content 답변 텍스트 조각 (type="delta"일 경우 존재)
 * @param data    추가 메타데이터 또는 에러 상세 정보 (Map 구조)
 * @param message 에러 메시지 (type="error"일 경우 존재)
 * @param code    에러 코드
 * @author pwk0131
 */
public record AiServiceResponse(
	String type,
	String content,
	Map<String, Object> data,
	String message,
	String code
) {
}

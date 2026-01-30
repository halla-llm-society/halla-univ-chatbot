package com.hallachatbot.backend.global.client.dto;

import java.util.Map;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.ToString;

/**
 * AI 서비스 스트리밍 응답 DTO
 * (NDJSON 라인 하나에 해당)
 */
@Getter
@NoArgsConstructor
@ToString
public class AiServiceResponse {

	/**
	 * 이벤트 타입 (delta, metadata, error)
	 */
	private String type;

	/**
	 * 채팅 내용 (type="delta" 일 때)
	 */
	private String content;

	/**
	 * 메타데이터 또는 에러 상세 (type="metadata" or "error" 일 때)
	 */
	private Map<String, Object> data;

	/**
	 * 에러 메시지 (type="error" 일 때 간혹 사용됨)
	 */
	private String message;

	private String code;
}

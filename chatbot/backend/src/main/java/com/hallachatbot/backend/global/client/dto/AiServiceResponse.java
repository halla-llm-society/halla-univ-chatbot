package com.hallachatbot.backend.global.client.dto;

import java.util.Map;

/**
 * AI 서비스 스트리밍 응답 DTO
 */
public record AiServiceResponse(
	String type,
	String content,
	Map<String, Object> data,
	String message,
	String code
) {
}

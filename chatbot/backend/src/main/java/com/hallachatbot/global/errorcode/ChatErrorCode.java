package com.hallachatbot.global.errorcode;

import static org.springframework.http.HttpStatus.BAD_REQUEST;
import static org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR;
import static org.springframework.http.HttpStatus.SERVICE_UNAVAILABLE;

import org.springframework.http.HttpStatus;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum ChatErrorCode implements ErrorCode {
	// [500] AI 서비스 응답 오류
	AI_SERVICE_ERROR(
		INTERNAL_SERVER_ERROR,
		"AI 응답 생성 중 오류가 발생했습니다.",
		"AI 서비스가 에러 상태 코드를 반환"),

	// [500] 스트리밍 데이터 파싱 실패
	AI_RESPONSE_PARSING_FAILED(
		INTERNAL_SERVER_ERROR,
		"AI 응답 처리 중 오류가 발생했습니다.",
		"AI 서비스로부터 받은 스트리밍 JSON 데이터 파싱 실패"),

	// [500] 스트리밍 도중 끊김
	STREAMING_INTERRUPTED(
		INTERNAL_SERVER_ERROR,
		"응답 스트리밍 중 연결이 끊겼습니다.",
		"클라이언트 또는 AI 서비스와의 스트리밍 연결이 예기치 않게 종료됨"),

	// [503] AI 서비스 연결 실패
	AI_SERVICE_UNAVAILABLE(
		SERVICE_UNAVAILABLE,
		"챗봇 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",
		"AI 서비스 엔드포인트 연결 실패 또는 타임아웃 발생"),

	// [400] 유효하지 않은 Chat ID
	INVALID_CHAT_ID(
		BAD_REQUEST,
		"이전 대화 내역을 불러올 수 없습니다.",
		"전달된 chatId가 유효한 ObjectId 형식이 아님");

	private final HttpStatus status;
	private final String message;
	private final String logMessage;
}

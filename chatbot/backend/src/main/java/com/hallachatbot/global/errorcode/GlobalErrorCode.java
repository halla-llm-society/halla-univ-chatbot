package com.hallachatbot.global.errorcode;

import static org.springframework.http.HttpStatus.*;

import org.springframework.http.HttpStatus;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum GlobalErrorCode implements ErrorCode {
	// [400] @Valid 검증 실패
	INVALID_INPUT_VALUE(
		BAD_REQUEST,
		"입력값이 올바르지 않습니다",
		"@Valid 검증 실패"),

	// [400] 타입 불일치 (Request Param 등)
	INVALID_TYPE_VALUE(
		BAD_REQUEST,
		"잘못된 타입이 포함되어 있습니다",
		"요청 값 타입 불일치"),

	// [400] JSON 형식 오류 또는 파싱 실패
	INVALID_REQUEST_FORMAT(
		BAD_REQUEST,
		"요청 데이터 형식이 올바르지 않습니다",
		"요청 데이터 형식 오류"),

	// [400] 필수 쿼리 파라미터 누락
	MISSING_REQUIRED_PARAMETER(
		BAD_REQUEST,
		"필수 요청 파라미터가 누락되었습니다",
		"필수 쿼리 파라미터 누락"),

	// [400] 필수 헤더 누락
	MISSING_REQUIRED_HEADER(
		BAD_REQUEST,
		"필수 요청 헤더가 누락되었습니다",
		"필수 요청 헤더 누락"),

	// [404] 매핑된 핸들러가 없는 URL 요청
	URL_NOT_FOUND(
		NOT_FOUND,
		"요청하신 URL을 찾을 수 없습니다",
		"매핑된 핸들러 없는 URL 요청"),

	// [405] 허용되지 않은 HTTP 메서드로 요청
	METHOD_NOT_ALLOWED(
		HttpStatus.METHOD_NOT_ALLOWED,
		"지원하지 않는 HTTP 메서드입니다",
		"허용되지 않은 HTTP 메서드 요청"),

	// [415] 지원하지 않는 Content-Type 헤더
	UNSUPPORTED_MEDIA_TYPE(
		HttpStatus.UNSUPPORTED_MEDIA_TYPE,
		"지원하지 않는 Content-Type 입니다",
		"지원하지 않는 Content-Type 요청"),

	// [500] DB 관련 에러
	DATABASE_ERROR(
		HttpStatus.INTERNAL_SERVER_ERROR,
		"데이터베이스 오류가 발생했습니다",
		"DB 관련 예외"),

	// [500] 기타 서버 오류
	INTERNAL_SERVER_ERROR(
		HttpStatus.INTERNAL_SERVER_ERROR,
		"서버 내부 오류가 발생했습니다",
		"기타 서버 예외");

	private final HttpStatus status;
	private final String message;
	private final String logMessage;
}

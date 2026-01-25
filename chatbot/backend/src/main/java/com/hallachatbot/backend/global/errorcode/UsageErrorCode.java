package com.hallachatbot.backend.global.errorcode;

import static org.springframework.http.HttpStatus.FORBIDDEN;

import org.springframework.http.HttpStatus;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * <b>비용(Cost) 도메인 관련 에러 코드 정의</b>
 * <p>
 * 비즈니스 로직 수행 중 발생하는 예외 상황을 체계적으로 관리하기 위한 Enum입니다.
 * </p>
 */
@Getter
@RequiredArgsConstructor
public enum UsageErrorCode implements ErrorCode {

	// [403] 예산 초과
	MONTHLY_LLM_BUDGET_EXCEEDED(
		FORBIDDEN,
		"이번 달 LLM 사용 한도를 초과하여 일시적으로 서비스 이용이 제한되었습니다.",
		"LLM 예산 초과로 인한 이용 제한");

	private final HttpStatus status;
	private final String message;
	private final String logMessage;
}

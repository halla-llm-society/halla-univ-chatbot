package com.hallachatbot.global.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.hallachatbot.global.errorcode.ErrorCode;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record ApiResponse<T>(
	boolean success,
	String name,
	String message,
	T data
) {

	// 1. 성공 응답 (데이터 있음)
	public static <T> ApiResponse<T> ok(T data) {
		return new ApiResponse<>(true, null, null, data);
	}

	// 2. 성공 응답 (데이터 없음)
	public static <T> ApiResponse<T> ok() {
		return new ApiResponse<>(true, null, null, null);
	}

	// 3. 실패 응답
	public static <T> ApiResponse<T> fail(ErrorCode errorCode) {
		return new ApiResponse<>(false, errorCode.name(), errorCode.getMessage(), null);
	}
}

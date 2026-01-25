package com.hallachatbot.backend.global.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.hallachatbot.backend.global.errorcode.ErrorCode;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record Response<T>(
	boolean isSuccess,
	String errorCode,
	String errorMessage,
	T data
) {

	// 1. 성공 응답 (데이터 있음)
	public static <T> Response<T> success(T data) {
		return new Response<>(true, null, null, data);
	}

	// 2. 성공 응답 (데이터 없음)
	public static <T> Response<T> success() {
		return new Response<>(true, null, null, null);
	}

	// 3. 실패 응답
	public static <T> Response<T> fail(ErrorCode errorCode) {
		return new Response<>(false, errorCode.name(), errorCode.getMessage(), null);
	}
}

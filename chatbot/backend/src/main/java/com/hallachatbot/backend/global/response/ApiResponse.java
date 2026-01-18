package com.hallachatbot.backend.global.response;

import org.springframework.http.HttpStatus;

import com.fasterxml.jackson.annotation.JsonInclude;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record ApiResponse<T>(
	boolean success,
	String message,
	T data
) {

	// 1. 성공 응답 (데이터 있음)
	public static <T> ApiResponse<T> ok(T data) {
		return new ApiResponse<>(true, "Success", data);
	}

	// 2. 성공 응답 (데이터 없음)
	public static <T> ApiResponse<T> ok() {
		return new ApiResponse<>(true, "Success", null);
	}

	// 3. 성공 응답 (커스텀 메시지 + 데이터)
	public static <T> ApiResponse<T> ok(T data, String message) {
		return new ApiResponse<>(true, message, data);
	}

	// 4. 실패 응답
	public static <T> ApiResponse<T> fail(HttpStatus status, String message) {
		return new ApiResponse<>(false, message, null);
	}
}

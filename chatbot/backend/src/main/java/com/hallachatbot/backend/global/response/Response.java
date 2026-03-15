package com.hallachatbot.backend.global.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.hallachatbot.backend.global.errorcode.ErrorCode;

/**
 * <b>API 공통 응답 포맷</b>
 *
 * <p>
 * 애플리케이션의 모든 REST API 응답을 감싸는 표준 규격 객체.
 * 성공 여부, 결과 데이터, 혹은 실패 시의 에러 상세 정보를 포함함.
 * </p>
 *
 * <ul>
 * <li><b>성공 시:</b> isSuccess=true, data={payload}</li>
 * <li><b>실패 시:</b> isSuccess=false, errorCode={code}, errorMessage={msg}</li>
 * </ul>
 * @author pwk0131
 *
 * @param isSuccess    요청 처리 성공 여부
 * @param errorCode    에러 식별 코드 (실패 시에만 포함, 성공 시 null)
 * @param errorMessage 에러 상세 메시지 (실패 시에만 포함, 성공 시 null)
 * @param data         응답 데이터 본문 (성공 시 포함, 데이터가 없으면 null)
 * @param <T>          응답 데이터(payload)의 타입
 */
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

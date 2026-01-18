package com.hallachatbot.backend.global.exception;

import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.NoHandlerFoundException;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import com.hallachatbot.backend.global.errorcode.ErrorCode;
import com.hallachatbot.backend.global.errorcode.GlobalErrorCode;
import com.hallachatbot.backend.global.response.ApiResponse;

import lombok.extern.slf4j.Slf4j;

/**
 * 전역 예외 처리 핸들러 (Global Exception Handler).
 * <p>
 * 애플리케이션 전역에서 발생하는 예외를 포착하여 표준화된 {@link ApiResponse} 포맷으로 응답합니다.
 * {@link ResponseEntityExceptionHandler}를 상속받아 Spring MVC 표준 예외를 커스터마이징하며,
 * 비즈니스 로직상의 {@link GlobalException} 및 기타 런타임 예외를 처리합니다.
 *
 */

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

	/**
	 * [Custom Exception] 비즈니스 로직 예외 처리.
	 * <p>
	 * 비즈니스 로직 수행 중 발생하는 '예측 가능한' 예외를 처리합니다.
	 * (예: 중복된 이메일 가입 시도, 포인트 부족, 존재하지 않는 게시글 조회 등)
	 * </p>
	 *
	 * <b>[사용 예시]</b>
	 * <pre>
	 * if (member == null) {
	 * throw new GlobalException(GlobalErrorCode.MEMBER_NOT_FOUND);
	 * }
	 * </pre>
	 *
	 * @param e 발생한 GlobalException
	 * @return ErrorCode에 정의된 상태 코드와 메시지를 담은 ResponseEntity
	 */
	// [Error Code] Custom Defined ErrorCode (GlobalErrorCode, ChatErrorCode 등)
	@ExceptionHandler(GlobalException.class)
	public ResponseEntity<Object> handleGlobalException(GlobalException error) {
		return handleExceptionInternal(error.getErrorCode(), error.getErrorCode().getLogMessage());
	}

	/**
	 * [500] 데이터베이스(DB) 관련 오류 처리.
	 * <p>
	 * JPA, MyBatis 등 DB 작업 중 발생하는 예외(SQL 문법 오류, 제약 조건 위반, 연결 실패 등)를 처리합니다.
	 * </p>
	 */
	// [Error Code] DATABASE_ERROR
	@ExceptionHandler(DataAccessException.class)
	public ResponseEntity<Object> handleDatabaseError(DataAccessException error) {
		return handleExceptionInternal(GlobalErrorCode.DATABASE_ERROR, error.getMessage());
	}

	/**
	 * [500] 서버 내부 오류 (Unhandled Exception) 처리.
	 * <p>
	 * 별도로 핸들링되지 않은 모든 예외(NullPointerException 등)를 처리합니다.
	 * </p>
	 */
	// [Error Code] INTERNAL_SERVER_ERROR
	@ExceptionHandler(Exception.class)
	public ResponseEntity<Object> handleAllException(Exception error) {
		return handleExceptionInternal(GlobalErrorCode.INTERNAL_SERVER_ERROR, error.getMessage());
	}

	// =================================================================================
	// Override ResponseEntityExceptionHandler (Spring MVC Standard Exceptions)
	// =================================================================================

	/**
	 * [400] @Valid 유효성 검사 실패 처리.
	 */
	// [Error Code] INVALID_INPUT_VALUE
	@Override
	protected ResponseEntity<Object> handleMethodArgumentNotValid(
		MethodArgumentNotValidException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.INVALID_INPUT_VALUE,
			ex.getBindingResult().getAllErrors().get(0).getDefaultMessage());
	}

	/**
	 * [400] JSON 파싱 실패 또는 잘못된 형식의 요청 데이터 처리.
	 * <p>
	 * Tip: DTO 작성 시 @NotBlank(message = "이메일은 필수입니다")와 같이 message 속성을 꼭 작성해주세요.
	 * 그래야 클라이언트에게 정확한 에러 원인을 전달할 수 있습니다.
	 * <p>
	 */
	// [Error Code] INVALID_REQUEST_FORMAT
	@Override
	protected ResponseEntity<Object> handleHttpMessageNotReadable(
		HttpMessageNotReadableException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.INVALID_REQUEST_FORMAT, ex.getMessage());
	}

	/**
	 * [400] 필수 쿼리 파라미터 누락 처리.
	 */
	// [Error Code] MISSING_REQUIRED_PARAMETER
	@Override
	protected ResponseEntity<Object> handleMissingServletRequestParameter(
		MissingServletRequestParameterException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.MISSING_REQUIRED_PARAMETER, ex.getMessage());
	}

	/**
	 * [404] 핸들러를 찾을 수 없는 URL 요청 처리.
	 */
	// [Error Code] URL_NOT_FOUND
	@Override
	protected ResponseEntity<Object> handleNoHandlerFoundException(
		NoHandlerFoundException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.URL_NOT_FOUND, ex.getMessage());
	}

	/**
	 * [405] 지원하지 않는 HTTP 메서드 요청 처리.
	 */
	// [Error Code] METHOD_NOT_ALLOWED
	@Override
	protected ResponseEntity<Object> handleHttpRequestMethodNotSupported(
		HttpRequestMethodNotSupportedException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.METHOD_NOT_ALLOWED, ex.getMessage());
	}

	/**
	 * [415] 지원하지 않는 Content-Type 요청 처리.
	 */
	// [Error Code] UNSUPPORTED_MEDIA_TYPE
	@Override
	protected ResponseEntity<Object> handleHttpMediaTypeNotSupported(
		HttpMediaTypeNotSupportedException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.UNSUPPORTED_MEDIA_TYPE, ex.getMessage());
	}

	// =================================================================================
	// Other Common Exceptions
	// =================================================================================

	/**
	 * [400] 파라미터 타입 불일치 처리.
	 */
	// [Error Code] INVALID_TYPE_VALUE
	@ExceptionHandler(MethodArgumentTypeMismatchException.class)
	public ResponseEntity<Object> handleMethodArgumentTypeMismatch(MethodArgumentTypeMismatchException error) {
		return handleExceptionInternal(GlobalErrorCode.INVALID_TYPE_VALUE, error.getMessage());
	}

	/**
	 * [400] 필수 헤더 누락 처리.
	 */
	// [Error Code] MISSING_REQUIRED_HEADER
	@ExceptionHandler(MissingRequestHeaderException.class)
	public ResponseEntity<Object> handleMissingRequestHeader(MissingRequestHeaderException error) {
		return handleExceptionInternal(GlobalErrorCode.MISSING_REQUIRED_HEADER, error.getMessage());
	}

	// =================================================================================
	// Common Handler Method (로그 및 응답 통합)
	// =================================================================================

	private ResponseEntity<Object> handleExceptionInternal(ErrorCode errorCode, String logDetail) {
		// [로깅 로직 중앙화 메서드]
		// 500번대 에러(Server Error)는 error 레벨로, 400번대(Client Error)는 warn 레벨로 로그 출력
		if (errorCode.getStatus().is5xxServerError()) {
			log.error("[Server Error] Code: {}, LogMsg: {}, Detail: {}",
				errorCode.name(), errorCode.getLogMessage(), logDetail);
		} else {
			log.warn("[Client Error] Code: {}, LogMsg: {}, Detail: {}",
				errorCode.name(), errorCode.getLogMessage(), logDetail);
		}

		return ResponseEntity
			.status(errorCode.getStatus())
			.body(ApiResponse.fail(errorCode));
	}
}

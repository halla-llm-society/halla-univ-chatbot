package com.hallachatbot.backend.global.exception;

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
 * </p>
 */

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

	/**
	 * [Custom Exception] GlobalException
	 */
	@ExceptionHandler(GlobalException.class)
	public ResponseEntity<Object> handleGlobalException(GlobalException error) {
		// GlobalException은 이미 ErrorCode 내부에 로그 메시지(getLogMessage)를 가지고 있음
		return handleExceptionInternal(error.getErrorCode(), error.getErrorCode().getLogMessage());
	}

	/**
	 * [500] Unhandled Exception
	 */
	@ExceptionHandler(Exception.class)
	public ResponseEntity<Object> handleAllException(Exception error) {
		// 예상치 못한 에러는 스택트레이스까지 찍기 위해 별도 처리하거나,
		// 여기서 메시지만 넘기고 로그 레벨 로직에 맡길 수 있음 (여기선 에러 메시지 전달)
		// 필요하다면 handleExceptionInternal에 Exception 객체를 받는 오버로딩을 추가하여 e.printStackTrace() 등을 처리 가능
		return handleExceptionInternal(GlobalErrorCode.INTERNAL_SERVER_ERROR, error.getMessage());
	}

	// =================================================================================
	// Override ResponseEntityExceptionHandler (Spring MVC Standard Exceptions)
	// =================================================================================

	@Override
	protected ResponseEntity<Object> handleMethodArgumentNotValid(
		MethodArgumentNotValidException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.INVALID_INPUT_VALUE,
			ex.getBindingResult().getAllErrors().get(0).getDefaultMessage());
	}

	@Override
	protected ResponseEntity<Object> handleHttpMessageNotReadable(
		HttpMessageNotReadableException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.INVALID_REQUEST_FORMAT, ex.getMessage());
	}

	@Override
	protected ResponseEntity<Object> handleMissingServletRequestParameter(
		MissingServletRequestParameterException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.MISSING_REQUIRED_PARAMETER, ex.getMessage());
	}

	@Override
	protected ResponseEntity<Object> handleNoHandlerFoundException(
		NoHandlerFoundException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.URL_NOT_FOUND, ex.getMessage());
	}

	@Override
	protected ResponseEntity<Object> handleHttpRequestMethodNotSupported(
		HttpRequestMethodNotSupportedException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.METHOD_NOT_ALLOWED, ex.getMessage());
	}

	@Override
	protected ResponseEntity<Object> handleHttpMediaTypeNotSupported(
		HttpMediaTypeNotSupportedException ex, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
		return handleExceptionInternal(GlobalErrorCode.UNSUPPORTED_MEDIA_TYPE, ex.getMessage());
	}

	// =================================================================================
	// Other Common Exceptions
	// =================================================================================

	@ExceptionHandler(MethodArgumentTypeMismatchException.class)
	public ResponseEntity<Object> handleMethodArgumentTypeMismatch(MethodArgumentTypeMismatchException error) {
		return handleExceptionInternal(GlobalErrorCode.INVALID_TYPE_VALUE, error.getMessage());
	}

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

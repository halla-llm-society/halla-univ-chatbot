package com.hallachatbot.backend.global.exception;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.validation.beanvalidation.LocalValidatorFactoryBean;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;

class GlobalExceptionHandlerTest {

	private MockMvc mockMvc;

	@BeforeEach
	void setup() {
		// Standalone 모드에서도 @Valid 검증을 작동시키기 위해 Validator를 수동으로 주입합니다.
		LocalValidatorFactoryBean validator = new LocalValidatorFactoryBean();
		validator.afterPropertiesSet();

		this.mockMvc = MockMvcBuilders.standaloneSetup(new TestController())
			.setControllerAdvice(new GlobalExceptionHandler()) // 핸들러 등록
			.setValidator(validator) // 유효성 검사기 등록
			.build();
	}

	// =================================================================================
	// 모든 에러 상황을 연출하기 위한 테스트용 컨트롤러
	// =================================================================================
	@RestController
	@RequestMapping("/test")
	static class TestController {

		@GetMapping("/db")
		public void db() {
			throw new DataIntegrityViolationException("DB 제약조건 위반");
		}

		@GetMapping("/runtime")
		public void runtime() {
			throw new RuntimeException("알 수 없는 에러");
		}

		// 1. 파라미터 타입 불일치 (int에 문자열 넣기)
		@GetMapping("/type-mismatch")
		public void typeMismatch(@RequestParam Integer num) {

		}

		// 2. 필수 파라미터 누락
		@GetMapping("/missing-param")
		public void missingParam(@RequestParam String required) {
		}

		// 3. 필수 헤더 누락
		@GetMapping("/missing-header")
		public void missingHeader(@RequestHeader("X-Token") String token) {
		}

		// 4. @Valid 유효성 검사 (@RequestBody)
		@PostMapping("/valid")
		public void valid(@RequestBody @Valid TestDto dto) {

		}

		// 5. HTTP Method 불일치 (POST만 허용)
		@PostMapping("/method")
		public void method() {
		}

		// 6. Content-Type 불일치 (JSON만 허용)
		@PostMapping(value = "/media", consumes = MediaType.APPLICATION_JSON_VALUE)
		public void media(@RequestBody TestDto dto) {
		}
	}

	// 검증용 DTO (Java 16+ record)
	record TestDto(@NotBlank(message = "공백일 수 없습니다") String name) {
	}

	// =================================================================================
	// 테스트 케이스
	// =================================================================================

	@Test
	@DisplayName("1. [DataAccessException] DB 관련 에러 500 처리 확인")
	void handleDatabaseError() throws Exception {
		mockMvc.perform(get("/test/db"))
			.andExpect(status().isInternalServerError())
			.andExpect(jsonPath("$.errorCode").value("DATABASE_ERROR"));
	}

	@Test
	@DisplayName("2. [Exception] 기타 서버 에러 500 처리 확인")
	void handleAllException() throws Exception {
		mockMvc.perform(get("/test/runtime"))
			.andExpect(status().isInternalServerError())
			.andExpect(jsonPath("$.errorCode").value("INTERNAL_SERVER_ERROR"));
	}

	@Test
	@DisplayName("3. [TypeMismatch] 파라미터 타입 불일치 400 처리 확인")
	void handleTypeMismatch() throws Exception {
		// int 파라미터에 "abc" 문자열 전송
		mockMvc.perform(get("/test/type-mismatch").param("num", "abc"))
			.andExpect(status().isBadRequest())
			.andExpect(jsonPath("$.errorCode").value("INVALID_TYPE_VALUE"));
	}

	@Test
	@DisplayName("4. [MissingParameter] 필수 파라미터 누락 400 처리 확인")
	void handleMissingParam() throws Exception {
		// required 파라미터 없이 요청
		mockMvc.perform(get("/test/missing-param"))
			.andExpect(status().isBadRequest())
			.andExpect(jsonPath("$.errorCode").value("MISSING_REQUIRED_PARAMETER"));
	}

	@Test
	@DisplayName("5. [MissingHeader] 필수 헤더 누락 400 처리 확인")
	void handleMissingHeader() throws Exception {
		// X-Token 헤더 없이 요청
		mockMvc.perform(get("/test/missing-header"))
			.andExpect(status().isBadRequest())
			.andExpect(jsonPath("$.errorCode").value("MISSING_REQUIRED_HEADER"));
	}

	@Test
	@DisplayName("6. [MethodArgumentNotValid] @Valid 유효성 실패 400 처리 확인")
	void handleValidation() throws Exception {
		// name이 빈 JSON 전송
		String json = "{\"name\": \"\"}";

		mockMvc.perform(post("/test/valid")
				.contentType(MediaType.APPLICATION_JSON)
				.content(json))
			.andExpect(status().isBadRequest())
			.andExpect(jsonPath("$.errorCode").value("INVALID_INPUT_VALUE"))
			.andExpect(jsonPath("$.errorMessage").value("입력값이 올바르지 않습니다"));
	}

	@Test
	@DisplayName("7. [HttpMessageNotReadable] JSON 형식이 깨졌을 때 400 처리 확인")
	void handleBrokenJson() throws Exception {
		// 닫는 괄호가 없는 잘못된 JSON
		String brokenJson = "{\"name\": \"test\"";

		mockMvc.perform(post("/test/valid")
				.contentType(MediaType.APPLICATION_JSON)
				.content(brokenJson))
			.andExpect(status().isBadRequest())
			.andExpect(jsonPath("$.errorCode").value("INVALID_REQUEST_FORMAT"));
	}

	@Test
	@DisplayName("8. [MethodNotSupported] 지원하지 않는 HTTP 메서드 405 처리 확인")
	void handleMethodNotSupported() throws Exception {
		// POST 메서드에 GET 요청
		mockMvc.perform(get("/test/method"))
			.andExpect(status().isMethodNotAllowed())
			.andExpect(jsonPath("$.errorCode").value("METHOD_NOT_ALLOWED"));
	}

	@Test
	@DisplayName("9. [MediaTypeNotSupported] 지원하지 않는 Content-Type 415 처리 확인")
	void handleMediaTypeNotSupported() throws Exception {
		// JSON을 받는 곳에 TEXT로 요청
		mockMvc.perform(post("/test/media")
				.contentType(MediaType.TEXT_PLAIN)
				.content("test"))
			.andExpect(status().isUnsupportedMediaType())
			.andExpect(jsonPath("$.errorCode").value("UNSUPPORTED_MEDIA_TYPE"));
	}
}

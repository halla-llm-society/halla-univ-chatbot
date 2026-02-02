package com.hallachatbot.backend.global.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.media.Schema;

@Target(ElementType.PARAMETER)
@Retention(RetentionPolicy.RUNTIME)
@Parameter(
	name = "chatId",
	description = "사용자 식별 쿠키 (자동 주입)",
	in = ParameterIn.COOKIE,
	schema = @Schema(type = "string"),
	hidden = true // Swagger에서 직접 입력받지 않고 쿠키로 처리됨을 명시하거나 숨김 처리
)
public @interface ChatSession {
}

package com.hallachatbot.backend.global.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.media.Schema;

/**
 * <b>사용자 채팅 세션(Chat ID) 주입 어노테이션</b>
 *
 * <p>
 * 컨트롤러 메서드의 파라미터에 이 어노테이션을 부착하면,
 * {@link com.hallachatbot.backend.global.resolver.ChatSessionArgumentResolver}가 동작하여
 * 쿠키(Cookie)에 저장된 'chatId' 값을 자동으로 파싱해 주입함
 * </p>
 *
 * <ul>
 * <li><b>자동 생성:</b> 쿠키에 chatId가 없는 경우, Resolver가 새로운 ID(ObjectId)를 생성하여 응답 쿠키로 설정하고 주입</li>
 * <li><b>Swagger 통합:</b> OpenAPI 문서(Swagger UI)상에서 해당 파라미터가 쿠키 영역에 위치함을 명시하거나, 직접 입력하지 않도록 숨김(hidden) 처리함</li>
 * </ul>
 *
 * @see com.hallachatbot.backend.global.resolver.ChatSessionArgumentResolver
 * @author pwk0131
 */

@Target(ElementType.PARAMETER)
@Retention(RetentionPolicy.RUNTIME)
@Parameter(
	name = "chatId",
	description = "사용자 식별 쿠키 (자동 주입)",
	in = ParameterIn.COOKIE,
	schema = @Schema(type = "string"),
	hidden = true
)
public @interface ChatSession {
}

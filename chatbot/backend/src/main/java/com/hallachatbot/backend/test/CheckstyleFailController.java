package com.hallachatbot.backend.test;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class CheckstyleFailController {

	@GetMapping("/fail")
	public String BadNamingMethod() { // [위반 2] 메서드 이름은 소문자로 시작해야 함 (MethodName)
		int a = 1 + 2; // [위반 3] 연산자 주변 공백 없음 (WhitespaceAround)

		if (true) {
			return "fail"; // [위반 4] if문 뒤에 공백 없음, 중괄호{} 생략 (NeedBraces)
		}

		return "fail";
	}
}

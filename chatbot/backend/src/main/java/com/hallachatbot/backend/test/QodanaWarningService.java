package com.hallachatbot.backend.test;

import org.springframework.stereotype.Service;

@Service
public class QodanaWarningService {

	public String potentialBugMethod(String input) {
		// [경고 1] Condition is always true
		// 10이 5보다 큰 것은 자명하므로 불필요한 조건문입니다.
		if (10 > 5) {
			System.out.println("Always printed");
		}

		String text = "Hello";

		// [경고 2] Result of method call ignored
		// replace를 했지만 그 결과를 변수에 할당하지 않아 아무 일도 일어나지 않습니다.
		text.replace("H", "h");

		// [경고 3] String comparison using '=='
		// 문자열 비교는 equals()를 써야 합니다. (잠재적 버그)
		if (input == "test") {
			return "Equal";
		}

		return text;
	}
}

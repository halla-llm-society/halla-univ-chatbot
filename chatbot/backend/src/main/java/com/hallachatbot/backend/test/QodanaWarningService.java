package com.hallachatbot.backend.test;

import java.util.ArrayList;

import org.springframework.stereotype.Service;

@Service
public class QodanaWarningService {

	public String badNamingVariable = "test";

	@SuppressWarnings("unused")
	private int unusedField = 100;

	public void dirtyMethod() {
		// [Qodana 타겟] 제네릭(<String>)을 안 씀 -> Type safety 경고
		ArrayList list = new ArrayList();
		list.add("Danger");

		// [Qodana 타겟] 무의미한 조건문
		if (true) {
			// [Qodana 타겟] 서버 코드에서 System.out 사용 (로깅 안 함)
			System.out.println("This is bad practice in server code");
		}

		try {
			// [Qodana 타겟] 0으로 나누기 (ArithmeticException) -> 심각한 버그
			int result = 10 / 0;
		} catch (Exception e) {
			// [Checkstyle] 빈 catch 블록은 보통 잡지만, 일단 넘어가는지 확인
		}
	}

	// 테스트 1
	// public 메서드인데 javadoc 없음 (Checkstyle 설정에 따라 경고 뜰 수 있음)
	public boolean check() {
		// [Qodana 타겟] 문자열 비교에 '==' 사용 (버그 유발)
		return badNamingVariable == "test";
	}
}

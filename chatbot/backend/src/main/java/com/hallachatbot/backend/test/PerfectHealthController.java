package com.hallachatbot.backend.test;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class PerfectHealthController {

	@GetMapping("/health-check")
	public String checkHealth() {
		return "OK";
	}

	public int addNumbers(int paramA, int paramB) {
		return paramA + paramB;
	}
}

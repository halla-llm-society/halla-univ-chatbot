package com.hallachatbot.backend.global.errorcode;

import org.springframework.http.HttpStatus;

public interface ErrorCode {
	HttpStatus getStatus();

	String getMessage();

	String getLogMessage();

	String name();
}

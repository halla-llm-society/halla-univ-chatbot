package com.hallachatbot.backend.global.exception;

import com.hallachatbot.backend.global.errorcode.ErrorCode;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public class GlobalException extends RuntimeException {
	private final transient ErrorCode errorCode;
}

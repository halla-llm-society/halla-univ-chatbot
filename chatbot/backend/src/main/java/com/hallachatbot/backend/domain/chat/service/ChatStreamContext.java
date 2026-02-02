package com.hallachatbot.backend.domain.chat.service;

import java.util.HashMap;
import java.util.Map;

import lombok.Getter;

@Getter
public class ChatStreamContext {
	private final String chatId;
	private final String question;
	private final StringBuilder answerBuilder = new StringBuilder();
	private Map<String, Object> metadataMap = new HashMap<>();

	// 추출된 주요 메타데이터
	private String decision = "";
	private String preset = "";
	private Integer totalTokens = 0;

	public ChatStreamContext(String chatId, String question) {
		this.chatId = chatId;
		this.question = question;
	}

	public void appendAnswer(String chunk) {
		this.answerBuilder.append(chunk);
	}

	public String getAnswer() {
		return this.answerBuilder.toString();
	}

	@SuppressWarnings("unchecked")
	public void updateMetadata(Map<String, Object> data) {
		if (data == null) {
			return;
		}
		this.metadataMap = data;

		// RAG Decision 추출
		if (data.get("rag") instanceof Map<?, ?> rag) {
			Object gateReason = rag.get("gate_reason");
			this.decision = gateReason != null ? gateReason.toString() : "";
		}

		// Token Usage 추출
		if (data.get("token_usage") instanceof Map<?, ?> usage) {
			Object presetObj = usage.get("preset");
			this.preset = presetObj != null ? presetObj.toString() : "";

			Object tokens = usage.get("total_tokens");
			if (tokens instanceof Number n) {
				this.totalTokens = n.intValue();
			} else if (tokens instanceof String s) {
				this.totalTokens = Integer.parseInt(s);
			}
		}
	}
}

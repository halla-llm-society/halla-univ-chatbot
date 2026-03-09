package com.hallachatbot.backend.domain.chat.service;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

import lombok.Getter;

/**
 * <b>채팅 스트림 컨텍스트 (State Object)</b>
 *
 * <p>
 * 단일 채팅 요청이 처리되는 동안(스트리밍 수명주기 내) 유지되는 상태 저장소
 * </p>
 *
 * <ul>
 * <li><b>데이터 누적:</b> 스트리밍으로 조각조각 들어오는 답변(Chunk)을 하나의 완성된 문자열로 조립</li>
 * <li><b>메타데이터 파싱:</b> AI 서비스로부터 넘어오는 원본 맵(Map) 데이터에서 RAG 결정 사유, 토큰 사용량 등 핵심 정보를 추출하여 관리.</li>
 * <li><b>임시 저장소:</b> 스트리밍이 끝난 후 {@link com.hallachatbot.backend.domain.chat.component.ChatWriter}가 DB에 저장할 때 이 객체를 참조
 * </li>
 * </ul>
 * @author pwk0131
 */

@Getter
public class ChatStreamContext {
	private final String chatId;
	private final String question;
	private final StringBuilder answerBuilder = new StringBuilder();
	private Map<String, Object> metadataMap = new HashMap<>();
	private BigDecimal cost = BigDecimal.ZERO;

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

	public boolean hasAnswer() {
		return this.answerBuilder.length() > 0;
	}

	public BigDecimal getCost() {
		return this.cost;
	}

	/**
	 * 메타데이터 갱신 및 주요 정보(토큰, RAG 사유) 추출
	 *
	 * @param data AI 서비스 응답의 'data' 필드 맵
	 */
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

		// Token Usage & total_cost_usd 추출
		if (data.get("token_usage") instanceof Map<?, ?> usage) {
			Object presetObj = usage.get("preset");
			this.preset = presetObj != null ? presetObj.toString() : "";

			Object tokens = usage.get("total_tokens");
			if (tokens instanceof Number n) {
				this.totalTokens = n.intValue();
			} else if (tokens instanceof String s) {
				try {
					this.totalTokens = Integer.parseInt(s);
				} catch (NumberFormatException e) {
					this.totalTokens = 0;
				}
			}

			Object costObj = null;
			for (Map.Entry<?, ?> entry : usage.entrySet()) {
				String key = String.valueOf(entry.getKey()).trim();
				if ("total_cost_usd".equals(key)) {
					costObj = entry.getValue();
					break;
				}
			}

			if (costObj != null) {
				try {
					this.cost = new BigDecimal(costObj.toString());
				} catch (NumberFormatException e) {
					this.cost = BigDecimal.ZERO;
				}
			}
		}
	}
}

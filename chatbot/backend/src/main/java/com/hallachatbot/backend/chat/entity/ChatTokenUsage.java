package com.hallachatbot.backend.chat.entity;

import java.time.LocalDateTime;

import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 대화별 토큰 사용량 관리 엔티티
 *
 * <p>
 * 컬렉션 : {@code token}<br>
 * 특정 대화({@link ChatMessage}) 발생 시 소모된 토큰 정보 저장
 * </p>
 *
 * @author pwk0131
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Document(collection = "token#{environment.getProperty('app.mongodb-suffix')}")
public class ChatTokenUsage {

	@Id
	private String id;

	/**
	 * 연관된 메시지 ID (ChatMessage의 _id)
	 * <p>
	 * 주의: Python 코드에서 message_id를 'chatId' 필드명으로 저장했음.
	 * </p>
	 */
	@Field("chatId")
	private String messageId;

	/**
	 * 사용된 LLM 프리셋 (모델명 등)
	 */
	private String preset;

	/**
	 * 총 사용 토큰 수
	 */
	private Integer totalTokens;

	@CreatedDate
	private LocalDateTime createdDate;

	@Builder
	public ChatTokenUsage(String messageId, String preset, Integer totalTokens) {
		this.messageId = messageId;
		this.preset = preset;
		this.totalTokens = totalTokens;
	}
}

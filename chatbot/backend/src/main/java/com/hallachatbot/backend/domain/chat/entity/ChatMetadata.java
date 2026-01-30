package com.hallachatbot.backend.domain.chat.entity;

import java.time.LocalDateTime;
import java.util.Map;

import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 대화 메타데이터 엔티티
 *
 * <p>
 * 컬렉션 : {@code metadata}<br>
 * AI 서비스로부터 반환된 원본 메타데이터 상세 정보를 저장 (디버깅 및 분석용)
 * </p>
 *
 * @author pwk0131
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Document(collection = "metadata#{environment.getProperty('app.mongodb-suffix')}")
public class ChatMetadata {

	@Id
	private String id;

	/**
	 * 연관된 메시지 ID (ChatMessage의 _id)
	 */
	@Field("chatId")
	private String messageId;

	/**
	 * 메타데이터 원본 (JSON 객체)
	 * <p>
	 * 구조가 가변적일 수 있으므로 Map으로 매핑
	 * </p>
	 */
	private Map<String, Object> metadata;

	@CreatedDate
	private LocalDateTime createdDate;

	@Builder
	public ChatMetadata(String messageId, Map<String, Object> metadata) {
		this.messageId = messageId;
		this.metadata = metadata;
	}
}

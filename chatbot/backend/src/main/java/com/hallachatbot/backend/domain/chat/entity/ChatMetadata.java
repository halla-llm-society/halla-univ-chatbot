package com.hallachatbot.backend.domain.chat.entity;

import java.time.LocalDateTime;
import java.util.Map;

import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;
import org.springframework.data.mongodb.core.mapping.FieldType;

import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * <b>대화 상세 메타데이터 엔티티</b>
 *
 * <p>
 * AI 서비스로부터 반환된 원본 메타데이터(JSON)를 보관하는 문서.
 * 디버깅, 품질 분석, 모델 성능 모니터링 목적으로 사용.
 * </p>
 *
 * <ul>
 * <li>Collection Name: {@code metadata}</li>
 * <li>Relation: {@link ChatMessage}와 1:1 대응</li>
 * </ul>
 *
 * @author pwk0131
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Document(collection = "metadata${app.mongodb-suffix}")
public class ChatMetadata {

	@Id
	private String id;

	/**
	 * 생성 날짜
	 */
	@CreatedDate
	@Field("date")
	private LocalDateTime createdDate;

	/**
	 * 연관된 대화 메시지 ID
	 * <p>
	 * {@link ChatMessage}의 PK(_id)를 참조
	 * </p>
	 */
	@Field(name = "chatId", targetType = FieldType.OBJECT_ID)
	private String messageId;

	/**
	 * 메타데이터 원본 (Key-Value)
	 * <p>
	 * AI 파이프라인의 단계별 처리 결과 및 디버그 정보를 포함
	 * </p>
	 */
	private Map<String, Object> metadata;

	@Builder
	public ChatMetadata(String messageId, Map<String, Object> metadata) {
		this.messageId = messageId;
		this.metadata = metadata;
	}
}

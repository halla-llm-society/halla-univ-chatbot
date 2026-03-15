package com.hallachatbot.backend.domain.survey.entity;

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
 * <b>챗봇 만족도 설문 엔티티</b>
 *
 * <ul>
 * <li><b>DB:</b> MongoDB</li>
 * <li><b>컬렉션:</b> {@code chat_survey}</li>
 * <li><b>특징:</b> 생성 시간 자동 기록</li>
 * </ul>
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Document(collection = "survey${app.mongodb.suffix:}")
public class ChatSurvey {

	@Id
	private String id;

	@Field("user_category")
	private String userCategory;

	private int rating;

	@Field("response_speed")
	private String responseSpeed;

	@Field("response_quality")
	private String responseQuality;

	private String comment;

	@CreatedDate
	@Field("date")
	private LocalDateTime date;

	@Builder
	private ChatSurvey(String userCategory, int rating, String responseSpeed, String responseQuality, String comment) {
		this.userCategory = userCategory;
		this.rating = rating;
		this.responseSpeed = responseSpeed;
		this.responseQuality = responseQuality;
		this.comment = comment;
	}

	public static ChatSurvey of(String userCategory, int rating, String responseSpeed,
		String responseQuality, String comment) {
		return ChatSurvey.builder()
			.userCategory(userCategory)
			.rating(rating)
			.responseSpeed(responseSpeed)
			.responseQuality(responseQuality)
			.comment(comment)
			.build();
	}
}

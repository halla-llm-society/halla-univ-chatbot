package com.hallachatbot.backend.domain.chat.component;

import java.util.Collections;
import java.util.List;
import java.util.stream.Stream;

import org.springframework.stereotype.Component;

import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.domain.chat.entity.ChatMessage;

/**
 * <b>채팅 데이터 변환 컴포넌트 (Mapper)</b>
 *
 * <p>
 * 데이터베이스 엔티티({@link ChatMessage})를 클라이언트 및 AI 서비스가 사용하는
 * DTO 포맷({@link ChatHistoryResponse})으로 변환하는 역할을 수행
 * </p>
 *
 * <ul>
 * <li><b>주요 기능:</b> DB에서 조회된 메시지 리스트를 AI 문맥(Context)에 맞는 순서(과거 -> 현재)로 재정렬하고 포맷팅</li>
 * </ul>
 *
 * @author pwk0131
 */

@Component
public class ChatMapper {

	public List<ChatHistoryResponse> toHistoryResponse(List<ChatMessage> rawHistory) {
		// 원본 리스트 보호를 위해 복사본 생성 후 역순 정렬 (과거 -> 현재)
		List<ChatMessage> sortedHistory = new java.util.ArrayList<>(rawHistory);
		Collections.reverse(sortedHistory);

		return sortedHistory.stream()
			.flatMap(msg -> Stream.of(
				ChatHistoryResponse.user(msg.getQuestion()),
				ChatHistoryResponse.assistant(msg.getAnswer())
			))
			.toList();
	}
}

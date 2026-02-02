package com.hallachatbot.backend.domain.chat.component;

import java.util.Collections;
import java.util.List;
import java.util.stream.Stream;

import org.springframework.stereotype.Component;

import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.domain.chat.entity.ChatMessage;

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

package com.hallachatbot.backend.domain.chat.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyBoolean;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.cookie;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Collections;

import org.bson.types.ObjectId;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.repository.ChatMessageRepository;
import com.hallachatbot.backend.domain.chat.service.ChatService;

import reactor.core.publisher.Flux;

@WebMvcTest(ChatController.class)
class ChatControllerTest {

	@Autowired
	private MockMvc mockMvc;

	@MockitoBean
	private ChatService chatService;

	@MockitoBean
	private ChatMessageRepository chatMessageRepository;

	@Autowired
	private ObjectMapper objectMapper;

	@Test
	@DisplayName("채팅 요청 시 쿠키가 없으면 새 chatId 쿠키를 발급한다")
	void chat_NoCookie_GeneratesNewCookie() throws Exception {
		// given
		ChatRequest request = new ChatRequest();
		ReflectionTestUtils.setField(request, "userInput", "안녕");
		ReflectionTestUtils.setField(request, "language", ChatRequest.Language.KOR);

		given(chatService.startChat(any(ChatRequest.class), any(), anyBoolean()))
			.willReturn(Flux.empty());

		// when & then
		mockMvc.perform(post("/api/chat")
				.contentType(MediaType.APPLICATION_JSON)
				.content(objectMapper.writeValueAsString(request)))
			.andExpect(status().isOk())
			.andExpect(cookie().exists("chatId")); // 응답 쿠키 확인
	}

	@Test
	@DisplayName("유효한 쿠키가 있으면 해당 chatId를 유지한다 (새 쿠키 미발급)")
	void chat_ValidCookie_MaintainsCookie() throws Exception {
		// given
		String existingChatId = new ObjectId().toHexString();
		ChatRequest request = new ChatRequest();
		ReflectionTestUtils.setField(request, "userInput", "안녕");
		ReflectionTestUtils.setField(request, "language", ChatRequest.Language.KOR);

		given(chatService.startChat(any(ChatRequest.class), eq(existingChatId), eq(false)))
			.willReturn(Flux.empty());

		// when & then
		mockMvc.perform(post("/api/chat")
				.cookie(new jakarta.servlet.http.Cookie("chatId", existingChatId)) // 요청 쿠키 설정
				.contentType(MediaType.APPLICATION_JSON)
				.content(objectMapper.writeValueAsString(request)))
			.andExpect(status().isOk())
			.andExpect(cookie().doesNotExist("chatId")); // 새 쿠키가 발급되지 않아야 함
	}

	@Test
	@DisplayName("대화 내역 조회 시 쿠키가 유효하면 성공한다")
	void getHistory_Success() throws Exception {
		// given
		String chatId = new ObjectId().toHexString();

		given(chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(chatId))
			.willReturn(Collections.emptyList());

		// when & then
		mockMvc.perform(get("/api/chat/history")
				.cookie(new jakarta.servlet.http.Cookie("chatId", chatId)))
			.andExpect(status().isOk());
	}
}

package com.hallachatbot.backend.domain.chat.repository;

import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import org.springframework.stereotype.Repository;

import com.hallachatbot.backend.domain.chat.entity.Chat;

import reactor.core.publisher.Flux;

@Repository
public interface ChatRepository extends ReactiveMongoRepository<Chat, String> {

	// chatId로 검색하고 날짜 내림차순 정렬 (최신순)
	Flux<Chat> findByChatIdOrderByDateDesc(String chatId, Pageable pageable);
}

package com.hallachatbot.backend.domain.chat.repository;

import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import org.springframework.stereotype.Repository;

import com.hallachatbot.backend.domain.chat.entity.Token;

@Repository
public interface TokenRepository extends ReactiveMongoRepository<Token, String> {
}

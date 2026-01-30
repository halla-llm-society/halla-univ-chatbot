package com.hallachatbot.backend.domain.usage.repository;

import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import com.hallachatbot.backend.domain.usage.entity.MonthlyLlmUsage;

@Repository
public interface MonthlyLlmUsageRepository extends CrudRepository<MonthlyLlmUsage, String> {

}

"""
비용 계산 모듈

토큰 사용량을 기반으로 LLM API 비용을 계산합니다.
pricing.yaml 파일에서 모델별 단가를 로드하여 사용합니다.
OpenAI와 Gemini API 모두 지원합니다.
"""

import yaml
from pathlib import Path
from decimal import Decimal
from typing import Dict, List
from collections import defaultdict


class CostCalculator:
    """비용 계산기
    
    토큰 사용량과 모델 ID를 기반으로 API 비용을 계산합니다.
    pricing.yaml에서 모델별 단가를 로드하며, 미등록 모델은 기본값을 사용합니다.
    Provider별 비용 집계 기능도 지원합니다.
    
    Decimal을 사용하여 소수점 정밀도를 유지합니다.
    """
    
    def __init__(self, pricing_path: str = "ai/config/pricing.yaml"):
        """비용 계산기 초기화
        
        Args:
            pricing_path: pricing.yaml 파일 경로 (프로젝트 루트 기준)
        
        Raises:
            FileNotFoundError: pricing.yaml 파일이 없을 때
        """
        # 절대 경로 또는 상대 경로 처리
        pricing_file = Path(pricing_path)
        if not pricing_file.is_absolute():
            # 상대 경로인 경우 app/ 디렉토리 기준으로 해석
            base_dir = Path(__file__).resolve().parent.parent.parent  # app/
            pricing_file = base_dir / pricing_path
        
        if not pricing_file.exists():
            raise FileNotFoundError(f"pricing.yaml not found: {pricing_file}")
        
        with open(pricing_file, 'r', encoding='utf-8') as f:
            self.pricing_data = yaml.safe_load(f)
        
        # 모델별 가격 맵 생성
        self.pricing_map = {}
        for model_entry in self.pricing_data.get("models", []):
            model_id = model_entry["id"]
            self.pricing_map[model_id] = {
                "input": Decimal(str(model_entry["input_per_1m_tokens_usd"])),
                "output": Decimal(str(model_entry["output_per_1m_tokens_usd"])),
                "cache_input": Decimal(str(model_entry.get("cache_input_per_1m_tokens_usd", model_entry["input_per_1m_tokens_usd"]))),
                "cache": Decimal(str(model_entry.get("cache_per_1m_tokens_usd", model_entry["input_per_1m_tokens_usd"]))),
                "currency": model_entry["currency"],
                "provider": model_entry.get("provider", "unknown"),
                "note": model_entry.get("note", "")
            }
        
        # 폴백 기본값
        default_entry = self.pricing_data.get("default", {})
        self.default_pricing = {
            "input": Decimal(str(default_entry.get("input_per_1m_tokens_usd", 2.50))),
            "output": Decimal(str(default_entry.get("output_per_1m_tokens_usd", 10.00))),
            "currency": default_entry.get("currency", "USD"),
            "provider": default_entry.get("provider", "unknown"),
        }
        
        # Provider별 비용 집계용 (선택적)
        self.cost_by_provider = defaultdict(lambda: {"input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0})
    
    def calculate(self, token_usage: Dict[str, int], model: str) -> Dict[str, float]:
        """토큰 사용량 → 비용 계산
        
        1M 토큰당 단가를 기준으로 비용을 계산합니다.
        모델이 pricing.yaml에 없으면 기본값을 사용합니다.
        
        Args:
            token_usage: 토큰 사용량 통계
                        {"input_tokens": N, "output_tokens": M, ...}
            model: 모델 ID (예: "gpt-4.1")
        
        Returns:
            Dict: 비용 통계
                {
                    "input_cost_usd": float,
                    "output_cost_usd": float,
                    "total_cost_usd": float,
                    "currency": "USD"
                }
        """
        pricing = self.pricing_map.get(model)
        if not pricing:
            print(f"[CostCalculator] 모델 {model}의 가격 정보 없음 → 기본값 사용")
            pricing = self.default_pricing
        
        input_tokens = Decimal(token_usage.get("input_tokens", 0))
        output_tokens = Decimal(token_usage.get("output_tokens", 0))
        
        # 비용 계산 (1M 토큰 기준)
        input_cost = (input_tokens / Decimal("1000000")) * pricing["input"]
        output_cost = (output_tokens / Decimal("1000000")) * pricing["output"]
        total_cost = input_cost + output_cost
        
        result = {
            "input_cost_usd": float(input_cost),
            "output_cost_usd": float(output_cost),
            "total_cost_usd": float(total_cost),
            "currency": pricing["currency"],
            "provider": pricing.get("provider", "unknown"),
        }
        
        # Provider별 비용 집계
        provider_name = pricing.get("provider", "unknown")
        self.cost_by_provider[provider_name]["input_cost"] += float(input_cost)
        self.cost_by_provider[provider_name]["output_cost"] += float(output_cost)
        self.cost_by_provider[provider_name]["total_cost"] += float(total_cost)
        
        return result
    
    def get_cost_by_provider(self) -> Dict[str, Dict[str, float]]:
        """
        Provider별 누적 비용 반환
        
        Returns:
            Dict: Provider별 비용 통계
                {
                    "openai": {"input_cost": 0.01, "output_cost": 0.02, "total_cost": 0.03},
                    "gemini": {"input_cost": 0.005, "output_cost": 0.01, "total_cost": 0.015},
                    ...
                }
        """
        return dict(self.cost_by_provider)
    
    def reset_provider_costs(self) -> None:
        """Provider별 비용 집계 초기화"""
        self.cost_by_provider.clear()
    
    def calculate_batch(
        self,
        usage_list: List[Dict[str, any]],
    ) -> Dict[str, any]:
        """
        여러 모델 사용량을 한번에 계산
        
        Args:
            usage_list: 사용량 리스트
                       예: [
                           {"model": "gpt-5-nano", "input_tokens": 100, "output_tokens": 50},
                           {"model": "gemini-1.5-flash", "input_tokens": 200, "output_tokens": 100},
                       ]
        
        Returns:
            Dict: 전체 비용 통계
                {
                    "total_cost_usd": float,
                    "by_provider": {provider: {...}},
                    "by_model": {model: {...}},
                    "currency": "USD"
                }
        """
        total_cost = 0.0
        by_model = {}
        
        self.reset_provider_costs()
        
        for usage in usage_list:
            model = usage.get("model")
            token_usage = {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            }
            
            cost_data = self.calculate(token_usage, model)
            total_cost += cost_data["total_cost_usd"]
            by_model[model] = cost_data
        
        return {
            "total_cost_usd": total_cost,
            "by_provider": self.get_cost_by_provider(),
            "by_model": by_model,
            "currency": "USD"
        }

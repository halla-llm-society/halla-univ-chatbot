"""
LLM Manager for selecting and routing LLM providers based on roles.

역할(role)에 따라 적절한 LLM Provider를 선택하고 관리합니다.
"""

from typing import Dict, Optional
from pathlib import Path

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .preset_manager import PresetManager


class LLMManager:
    """LLM Provider 선택 및 라우팅 관리자"""
    
    def __init__(self, config_path: str = "ai/config/llm_config.yaml"):
        """
        LLMManager 초기화
        
        Args:
            config_path: llm_config.yaml 파일 경로
        """
        # Preset Manager 초기화
        self.preset_manager = PresetManager(config_path)
        
        # Provider 인스턴스 캐시
        self._provider_cache: Dict[str, BaseLLMProvider] = {}
        
        # Fixed roles (OpenAI 전용, 교체 불가)
        self._fixed_roles = self._load_fixed_roles()
    
    def _load_fixed_roles(self) -> Dict[str, Dict[str, str]]:
        """
        교체 불가능한 고정 역할 로드 (OpenAI 전용)
        
        Returns:
            Dict: {role: {provider: str, model: str}}
        """
        config = self.preset_manager.config
        return config.get("fixed_roles", {
            "function_calling": {"provider": "openai", "model": "o3-mini"},
            "web_search": {"provider": "openai", "model": "gpt-4.1"},
            "streaming": {"provider": "openai", "model": "gpt-4.1"}
        })
    
    def get_provider(self, role: str) -> BaseLLMProvider:
        """
        역할에 맞는 LLM Provider 반환
        
        Args:
            role: 역할 이름 (예: "category", "condense", "gate", "function_calling")
        
        Returns:
            BaseLLMProvider: 해당 역할에 지정된 Provider 인스턴스
        
        Raises:
            ValueError: 역할 설정을 찾을 수 없을 때
            NotImplementedError: 지원하지 않는 Provider일 때
        """
        # Fixed roles 확인 (교체 불가)
        if role in self._fixed_roles:
            role_config = self._fixed_roles[role]
        else:
            # Preset에서 역할 설정 가져오기
            role_config = self.preset_manager.get_role_config(role)
            if not role_config:
                raise ValueError(f"Role '{role}' not found in active preset")
        
        provider_name = role_config.get("provider")
        model_name = role_config.get("model")
        
        if not provider_name or not model_name:
            raise ValueError(f"Invalid config for role '{role}': {role_config}")
        
        # 캐시 키 생성 (provider:model)
        cache_key = f"{provider_name}:{model_name}"
        
        # 캐시에서 찾기
        if cache_key in self._provider_cache:
            return self._provider_cache[cache_key]
        
        # Provider 인스턴스 생성
        provider = self._create_provider(provider_name, model_name)
        
        # 캐시에 저장
        self._provider_cache[cache_key] = provider
        
        return provider
    
    def _create_provider(
        self,
        provider_name: str,
        model_name: str
    ) -> BaseLLMProvider:
        """
        Provider 인스턴스 생성
        
        Args:
            provider_name: Provider 이름 ("openai", "gemini")
            model_name: 모델 ID
        
        Returns:
            BaseLLMProvider: Provider 인스턴스
        
        Raises:
            NotImplementedError: 지원하지 않는 Provider일 때
        """
        if provider_name == "openai":
            return OpenAIProvider(model_name=model_name)
        elif provider_name == "gemini":
            return GeminiProvider(model_name=model_name)
        else:
            raise NotImplementedError(
                f"Provider '{provider_name}' is not implemented. "
                f"Supported providers: openai, gemini"
            )
    
    def clear_cache(self) -> None:
        """
        Provider 캐시 초기화
        
        프리셋 전환 후 호출하여 새로운 Provider 인스턴스를 생성하도록 합니다.
        """
        self._provider_cache.clear()
        print("[LLMManager] Provider cache cleared")
    
    def get_active_preset(self) -> str:
        """현재 활성 프리셋 이름 반환"""
        return self.preset_manager.get_active_preset()
    
    def list_presets(self) -> list:
        """
        모든 프리셋 목록 반환
        
        Returns:
            List[Dict]: 프리셋 정보 리스트
        """
        return self.preset_manager.list_presets()
    
    def switch_preset(self, preset_name: str) -> bool:
        """
        프리셋 전환 및 캐시 초기화
        
        Args:
            preset_name: 전환할 프리셋 이름
        
        Returns:
            bool: 성공 여부
        """
        success = self.preset_manager.switch_preset(preset_name)
        if success:
            self.clear_cache()
        return success
    
    def get_provider_info(self, role: str) -> Dict[str, str]:
        """
        특정 역할의 Provider 정보 반환
        
        Args:
            role: 역할 이름
        
        Returns:
            Dict: {provider: str, model: str, is_fixed: bool}
        """
        is_fixed = role in self._fixed_roles
        
        if is_fixed:
            config = self._fixed_roles[role]
        else:
            config = self.preset_manager.get_role_config(role)
            if not config:
                return {"error": f"Role '{role}' not found"}
        
        return {
            "provider": config.get("provider"),
            "model": config.get("model"),
            "is_fixed": is_fixed
        }
    
    def get_all_roles_info(self) -> Dict[str, Dict[str, str]]:
        """
        모든 역할의 Provider 정보 반환
        
        Returns:
            Dict: {role: {provider: str, model: str, is_fixed: bool}}
        """
        result = {}
        
        # Fixed roles
        for role in self._fixed_roles:
            result[role] = self.get_provider_info(role)
        
        # Preset roles
        preset_roles = self.preset_manager.get_all_roles()
        for role in preset_roles:
            if role not in result:  # Fixed role이 아닌 경우만
                result[role] = self.get_provider_info(role)
        
        return result


# 전역 싱글톤 인스턴스
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """
    LLMManager 싱글톤 인스턴스 반환
    
    Returns:
        LLMManager: 전역 인스턴스
    """
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager


# 편의 함수
def get_provider(role: str) -> BaseLLMProvider:
    """
    역할에 맞는 Provider 반환 (편의 함수)
    
    Args:
        role: 역할 이름
    
    Returns:
        BaseLLMProvider: Provider 인스턴스
    """
    return get_llm_manager().get_provider(role)


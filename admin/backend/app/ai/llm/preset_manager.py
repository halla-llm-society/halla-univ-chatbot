"""
LLM Preset Manager for saving and switching model combinations.

프리셋 기반으로 LLM 조합을 저장하고 전환할 수 있습니다.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class PresetInfo:
    """프리셋 정보"""
    name: str
    description: str
    roles: Dict[str, Dict[str, str]]  # {role: {provider: str, model: str}}


class PresetManager:
    """LLM 조합 프리셋 관리자"""
    
    def __init__(self, config_path: str = "ai/config/llm_config.yaml"):
        """
        PresetManager 초기화
        
        Args:
            config_path: llm_config.yaml 파일 경로 (프로젝트 루트 기준)
        """
        # 절대 경로 처리
        self.config_path = Path(config_path)
        if not self.config_path.is_absolute():
            base_dir = Path(__file__).resolve().parent.parent.parent  # app/
            self.config_path = base_dir / config_path
        
        # 설정 로드
        self.config = self._load_config()
        
        # 현재 활성 프리셋
        self.active_preset_name = self.config.get("active_preset", "balanced")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        llm_config.yaml 파일 로드
        
        Returns:
            Dict: 설정 딕셔너리
        
        Raises:
            FileNotFoundError: 설정 파일이 없을 때
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"llm_config.yaml not found at: {self.config_path}\n"
                "llm_config.yaml 파일이 없습니다. 기본 프리셋을 사용하려면 파일을 생성하세요."
            )
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _save_config(self) -> None:
        """llm_config.yaml 파일 저장"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True, sort_keys=False)
    
    def get_active_preset(self) -> str:
        """
        현재 활성화된 프리셋 이름 반환
        
        Returns:
            str: 프리셋 이름 (예: "balanced", "budget", "premium")
        """
        return self.active_preset_name
    
    def switch_preset(self, preset_name: str) -> bool:
        """
        프리셋 전환
        
        Args:
            preset_name: 전환할 프리셋 이름
        
        Returns:
            bool: 성공 여부
        """
        # 프리셋 존재 확인
        if preset_name not in self.config.get("presets", {}):
            print(f"[PresetManager] Preset '{preset_name}' not found")
            return False
        
        # 활성 프리셋 변경
        self.active_preset_name = preset_name
        self.config["active_preset"] = preset_name
        
        # 설정 파일에 저장
        try:
            self._save_config()
            print(f"[PresetManager] Switched to preset: {preset_name}")
            return True
        except Exception as e:
            print(f"[PresetManager] Failed to save config: {e}")
            return False
    
    def get_preset_info(self, preset_name: str) -> Optional[PresetInfo]:
        """
        프리셋 정보 조회
        
        Args:
            preset_name: 조회할 프리셋 이름
        
        Returns:
            PresetInfo: 프리셋 정보 (없으면 None)
        """
        presets = self.config.get("presets", {})
        if preset_name not in presets:
            return None
        
        preset_data = presets[preset_name]
        return PresetInfo(
            name=preset_data.get("name", preset_name),
            description=preset_data.get("description", ""),
            roles=preset_data.get("roles", {})
        )
    
    def list_presets(self) -> List[Dict[str, Any]]:
        """
        모든 프리셋 목록 반환
        
        Returns:
            List[Dict]: 프리셋 정보 리스트
        """
        presets = self.config.get("presets", {})
        result = []
        
        for preset_name, preset_data in presets.items():
            result.append({
                "preset_name": preset_name,
                "name": preset_data.get("name", preset_name),
                "description": preset_data.get("description", ""),
                "is_active": preset_name == self.active_preset_name,
                "roles": preset_data.get("roles", {})
            })
        
        return result
    
    def save_current_as_preset(
        self,
        preset_name: str,
        description: str,
        roles: Dict[str, Dict[str, str]]
    ) -> bool:
        """
        현재 조합을 새 프리셋으로 저장
        
        Args:
            preset_name: 저장할 프리셋 이름 (예: "custom_1")
            description: 프리셋 설명
            roles: 역할별 모델 설정
        
        Returns:
            bool: 성공 여부
        """
        try:
            # presets 섹션이 없으면 생성
            if "presets" not in self.config:
                self.config["presets"] = {}
            
            # 새 프리셋 추가
            self.config["presets"][preset_name] = {
                "name": description,
                "description": description,
                "roles": roles
            }
            
            # 설정 파일에 저장
            self._save_config()
            print(f"[PresetManager] Saved preset: {preset_name}")
            return True
            
        except Exception as e:
            print(f"[PresetManager] Failed to save preset: {e}")
            return False
    
    def get_role_config(self, role: str) -> Optional[Dict[str, str]]:
        """
        특정 역할의 설정 가져오기 (활성 프리셋 기준)
        
        Args:
            role: 역할 이름 (예: "category", "condense", "gate")
        
        Returns:
            Dict: {provider: str, model: str} 또는 None
        """
        preset_info = self.get_preset_info(self.active_preset_name)
        if not preset_info:
            return None
        
        return preset_info.roles.get(role)
    
    def get_all_roles(self) -> Dict[str, Dict[str, str]]:
        """
        활성 프리셋의 모든 역할 설정 가져오기
        
        Returns:
            Dict: {role: {provider: str, model: str}}
        """
        preset_info = self.get_preset_info(self.active_preset_name)
        if not preset_info:
            return {}
        
        return preset_info.roles
    
    def estimate_cost(
        self,
        preset_name: str,
        token_usage: Dict[str, Dict[str, int]],
        pricing_data: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        특정 프리셋 사용 시 예상 비용 계산
        
        Args:
            preset_name: 프리셋 이름
            token_usage: 역할별 토큰 사용량
                        예: {"category": {"input": 100, "output": 50}, ...}
            pricing_data: 모델별 가격 정보
                        예: {"gpt-5-nano": {"input": 0.05, "output": 0.005}, ...}
        
        Returns:
            Dict: 비용 정보
                {
                    "total_cost": float,
                    "by_role": {role: cost},
                    "currency": "USD"
                }
        """
        preset_info = self.get_preset_info(preset_name)
        if not preset_info:
            return {"error": f"Preset '{preset_name}' not found"}
        
        total_cost = 0.0
        cost_by_role = {}
        
        for role, usage in token_usage.items():
            # 역할에 해당하는 모델 찾기
            role_config = preset_info.roles.get(role)
            if not role_config:
                continue
            
            model_id = role_config.get("model")
            if not model_id or model_id not in pricing_data:
                continue
            
            # 비용 계산 (1M 토큰 기준)
            pricing = pricing_data[model_id]
            input_tokens = usage.get("input", 0)
            output_tokens = usage.get("output", 0)
            
            input_cost = (input_tokens / 1_000_000) * pricing.get("input", 0)
            output_cost = (output_tokens / 1_000_000) * pricing.get("output", 0)
            role_cost = input_cost + output_cost
            
            cost_by_role[role] = role_cost
            total_cost += role_cost
        
        return {
            "total_cost": total_cost,
            "by_role": cost_by_role,
            "currency": "USD"
        }


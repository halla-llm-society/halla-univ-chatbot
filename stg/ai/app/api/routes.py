from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, List

from app.ai.chatbot import ChatbotStream, model
from app.ai.llm import get_llm_manager
from app.ai.events.chat_observer import admin_event_stream  # 협의 후 활성화 예정

class UserRequest(BaseModel):
    user_input: str  # message → user_input으로 변경 (지침 추가용)
    message_history: Optional[List[Dict[str, str]]] = None  # 프론트가 전달하는 대화 히스토리
    language: str = "KOR"

class PresetSwitchRequest(BaseModel):
    preset_name: str

class PresetSaveRequest(BaseModel):
    name: str
    description: str
    roles: Dict[str, Dict[str, str]]


router = APIRouter()

# ChatbotStream 인스턴스 생성
chatbot = ChatbotStream(
    model=model.advanced,
    system_role="""당신은 학교 생활, 학과 정보, 행사 등 사용자가 궁금한 점이 있으면 아는 범위 안에서 대답합니다. 단 절대 거짓내용을 말하지 않습니다. 아는 범위에서 말하고 부족한 부분은 인정하세요.
    당신은 실시간으로 검색하는 기능이있습니다.
    당신은 한라대 공지사항을 탐색할 수 있습니다.
    당신은 한라대 학식메뉴를 탐색할 수 있습니다.
    당신은 한라대 학사일정을 탐색할 수 있습니다.
    학교와 관련 없는 질문에는 정중하게 답변을 거절하고, 반드시 학내 정보로 유도하세요.""",
    instruction="당신은 사용자의 질문에 답변하는 역할을 합니다.",
    user="한라대 대학생",
    assistant="memmo"
)


@router.post("/chat")
async def chat_endpoint(user_input: UserRequest):
    """
    채팅 엔드포인트 - ChatbotStream.stream_chat()에 모든 로직 위임
    
    Args:
        user_input: {
            "user_input": "현재 사용자 질문 (지침 추가용)",
            "message_history": [이전 대화 내역],
            "language": "KOR"
        }
    """
    stream_generator = chatbot.stream_chat(
        message=user_input.user_input,  # message → user_input
        message_history=user_input.message_history,  # 히스토리 추가
        language=user_input.language
    )
    
    return StreamingResponse(
        stream_generator,
        media_type="application/x-ndjson"
    )


# ===== LLM 프리셋 관리 엔드포인트 =====

@router.get("/llm/presets")
async def list_llm_presets():
    """
    사용 가능한 모든 LLM 프리셋 목록 조회
    
    Returns:
        List[Dict]: 프리셋 정보 리스트
    """
    try:
        llm_manager = get_llm_manager()
        presets = llm_manager.preset_manager.list_presets()
        return {
            "success": True,
            "presets": presets,
            "active_preset": llm_manager.get_active_preset()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list presets: {str(e)}")


@router.post("/llm/preset/switch")
async def switch_llm_preset(request: PresetSwitchRequest):
    """LLM 조합 프리셋 전환"""
    try:
        llm_manager = get_llm_manager()
        success = llm_manager.switch_preset(request.preset_name)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Preset '{request.preset_name}' not found")
        
        return {
            "success": True,
            "active_preset": llm_manager.get_active_preset(),
            "message": f"Successfully switched to preset: {request.preset_name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch preset: {str(e)}")


@router.post("/llm/preset/save")
async def save_custom_preset(request: PresetSaveRequest):
    """현재 조합을 사용자 정의 프리셋으로 저장"""
    try:
        llm_manager = get_llm_manager()
        success = llm_manager.preset_manager.save_current_as_preset(
            preset_name=request.name,
            description=request.description,
            roles=request.roles
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save preset")
        
        return {
            "success": True,
            "preset_name": request.name,
            "message": f"Successfully saved preset: {request.name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save preset: {str(e)}")


@router.get("/llm/roles")
async def get_all_roles_info():
    """모든 역할의 현재 LLM Provider 정보 조회"""
    try:
        llm_manager = get_llm_manager()
        roles_info = llm_manager.get_all_roles_info()
        
        return {
            "success": True,
            "active_preset": llm_manager.get_active_preset(),
            "roles": roles_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get roles info: {str(e)}")


# 협의 후 활성화 예정
# @router.get("/admin/chat-events")
# async def admin_chat_events():
#     """
#     관리자용 실시간 채팅 이벤트 스트림 (SSE)
#     
#     사용자가 채팅을 완료할 때마다 관리자에게 실시간으로 알림을 보냅니다.
#     
#     Returns:
#         Server-Sent Events 스트림
#         - type: 'new_chat' - 새 채팅 완료
#         - type: 'heartbeat' - 연결 유지용
#         - type: 'connected' - 연결 확인
#     """
#     return StreamingResponse(
#         admin_event_stream(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "Access-Control-Allow-Origin": "*",
#             "Access-Control-Allow-Headers": "Cache-Control"
#         }
#     )

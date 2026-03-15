"""
채팅 이벤트 옵저버 패턴 구현

사용자 채팅이 완료되면 관리자 페이지로 실시간 알림을 보냅니다.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ChatEvent:
    """채팅 이벤트 데이터"""
    session_id: str
    user_message: str
    assistant_message: str
    timestamp: datetime
    metadata: Optional[Dict] = None
    language: str = "KOR"
    
    def to_dict(self) -> Dict:
        """JSON 직렬화용"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class ChatEventObserver:
    """채팅 이벤트 관찰자 (Singleton)"""
    
    _instance = None
    _observers: List[asyncio.Queue] = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._observers = []
        return cls._instance
    
    async def notify_chat_completed(self, event: ChatEvent):
        """채팅 완료 이벤트를 모든 관리자에게 알림"""
        print(f"[CHAT_OBSERVER] 새 채팅 완료: {event.user_message[:50]}...")
        
        # 모든 관리자 연결에 이벤트 전송
        dead_observers = []
        for observer_queue in self._observers:
            try:
                await observer_queue.put(event)
            except Exception as e:
                print(f"[CHAT_OBSERVER] 관리자 연결 오류: {e}")
                dead_observers.append(observer_queue)
        
        # 끊어진 연결 정리
        for dead in dead_observers:
            self._observers.remove(dead)
        
        print(f"[CHAT_OBSERVER] {len(self._observers)}명의 관리자에게 알림 전송")
    
    def add_observer(self, observer_queue: asyncio.Queue):
        """새 관리자 연결 추가"""
        self._observers.append(observer_queue)
        print(f"[CHAT_OBSERVER] 관리자 연결 추가. 총 {len(self._observers)}명")
    
    def remove_observer(self, observer_queue: asyncio.Queue):
        """관리자 연결 제거"""
        if observer_queue in self._observers:
            self._observers.remove(observer_queue)
            print(f"[CHAT_OBSERVER] 관리자 연결 제거. 총 {len(self._observers)}명")

# 전역 인스턴스
chat_observer = ChatEventObserver()

async def admin_event_stream() -> AsyncGenerator[str, None]:
    """관리자용 SSE 스트림 생성"""
    observer_queue = asyncio.Queue()
    chat_observer.add_observer(observer_queue)
    
    try:
        # 연결 확인용 heartbeat
        yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        while True:
            try:
                # 새 채팅 이벤트 대기 (30초 타임아웃)
                event = await asyncio.wait_for(observer_queue.get(), timeout=30.0)
                
                # SSE 형식으로 전송
                sse_data = {
                    'type': 'new_chat',
                    'data': event.to_dict()
                }
                yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"
                
            except asyncio.TimeoutError:
                # Heartbeat (연결 유지용)
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                
    except Exception as e:
        print(f"[ADMIN_STREAM] 오류: {e}")
    finally:
        chat_observer.remove_observer(observer_queue)

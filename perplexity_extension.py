import asyncio
import json
from typing import Dict, Any

class PerplexityExtension:
    """Perplexity Ask 도구를 위한 확장 클래스"""
    
    def __init__(self, client):
        """클라이언트 인스턴스 저장"""
        self.client = client
        
    async def patch_client(self):
        """클라이언트의 execute_tool 메서드를 패치하여 Perplexity 특별 처리 추가"""
        # 원본 메서드 저장
        original_execute_tool = self.client.execute_tool
        
        # 새로운 메서드 정의
        async def patched_execute_tool(tool_name: str, **kwargs) -> Any:
            """도구를 실행합니다. Perplexity 도구에 대한 특별 처리 추가."""
            session, server_name = await self.client.find_tool_server(tool_name)
            if session is None:
                raise ValueError(f"도구 '{tool_name}'를 찾을 수 없습니다. 연결된 서버: {', '.join(self.client.connected_servers)}")
            
            # Perplexity Ask 도구 특별 처리
            if tool_name == "perplexity_ask":
                return await self.handle_perplexity_ask(session, tool_name, kwargs)
            
            # 일반적인 도구 처리는 원본 메서드 사용
            return await original_execute_tool(tool_name, **kwargs)
        
        # 패치된 메서드로 교체
        self.client.execute_tool = patched_execute_tool
        print("> Perplexity Ask 확장 모듈이 로드되었습니다.")
    
    async def handle_perplexity_ask(self, session, tool_name, kwargs):
        """Perplexity Ask 도구를 특별하게 처리합니다."""
        start_time = asyncio.get_event_loop().time()
        
        # 시작 정보 표시
        messages = kwargs.get("messages", [])
        if messages and len(messages) > 0:
            # 사용자 질문 찾기
            user_question = None
            for msg in reversed(messages):  # 마지막 사용자 메시지 찾기
                if msg.get("role") == "user":
                    user_question = msg.get("content", "")
                    break
            
            # 사용자 질문이 있으면 표시
            if user_question:
                brief_question = user_question[:50] + "..." if len(user_question) > 50 else user_question
                print(f"> Perplexity-ask 실행 중: '{brief_question}'")
            else:
                print(f"> Perplexity-ask 실행 중...")
        else:
            print(f"> Perplexity-ask 실행 중...")
            
        # 상세 정보는 verbose 모드에서만 표시
        if self.client.verbose:
            print(f"  메시지: {messages}")
        
        # 도구 실행
        try:
            print(f"> Perplexity API 검색 중...")
            result = await session.call_tool(tool_name, kwargs)
            content = result.content
            
            # 실행 시간 계산
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            
            print(f"> Perplexity-ask 완료 ({execution_time:.2f}초)")
            
            return content
            
        except Exception as e:
            print(f"> Perplexity-ask 실패: {str(e)}")
            raise
import asyncio
import json
from typing import Dict, Any

class SequentialThinkingExtension:
    """Sequential Thinking 도구를 위한 확장 클래스"""
    
    def __init__(self, client):
        """클라이언트 인스턴스 저장"""
        self.client = client
        
    async def patch_client(self):
        """클라이언트의 execute_tool 메서드를 패치하여 Sequential Thinking 특별 처리 추가"""
        # 원본 메서드 저장
        original_execute_tool = self.client.execute_tool
        
        # 새로운 메서드 정의
        async def patched_execute_tool(tool_name: str, **kwargs) -> Any:
            """도구를 실행합니다. Sequential Thinking 도구에 대한 특별 처리 추가."""
            session, server_name = await self.client.find_tool_server(tool_name)
            if session is None:
                raise ValueError(f"도구 '{tool_name}'를 찾을 수 없습니다. 연결된 서버: {', '.join(self.client.connected_servers)}")
            
            # Sequential Thinking 도구 특별 처리
            if tool_name == "sequentialthinking":
                return await self.handle_sequential_thinking(session, tool_name, kwargs)
            
            # 일반적인 도구 처리는 원본 메서드 사용
            return await original_execute_tool(tool_name, **kwargs)
        
        # 패치된 메서드로 교체
        self.client.execute_tool = patched_execute_tool
        print("> Sequential Thinking 확장 모듈이 로드되었습니다.")
    
    async def handle_sequential_thinking(self, session, tool_name, kwargs):
        """Sequential Thinking 도구를 특별하게 처리합니다."""
        start_time = asyncio.get_event_loop().time()
        
        # 시작 정보 표시
        thought_number = kwargs.get("thoughtNumber", 0)
        total_thoughts = kwargs.get("totalThoughts", 0)
        thought = kwargs.get("thought", "")
        next_thought_needed = kwargs.get("nextThoughtNeeded", True)
        
        # 첫 번째 생각이면 작업 시작 메시지 표시
        if thought_number == 1:
            print(f"> Sequential-thinking 시작 (총 {total_thoughts}단계 예상)")
        
        # 현재 사고 단계 표시
        print(f"> Sequential-thinking 실행 중 ({thought_number}/{total_thoughts})")
        
        # 상세 정보는 verbose 모드에서만 표시
        if self.client.verbose:
            brief_thought = thought[:100] + "..." if len(thought) > 100 else thought
            print(f"  생각: {brief_thought}")
        
        # 도구 실행
        try:
            result = await session.call_tool(tool_name, kwargs)
            content = result.content
            
            # 실행 시간 계산
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time
            
            # 실행 결과에서 다음 사고 여부 확인
            try:
                result_data = json.loads(content) if isinstance(content, str) else content
                next_thought_needed = result_data.get("nextThoughtNeeded", False)
                
                # 마지막 사고인지 확인
                if not next_thought_needed:
                    print(f"> Sequential-thinking 완료 ({execution_time:.2f}초)")
                
            except (json.JSONDecodeError, TypeError, AttributeError):
                # JSON 파싱 실패 시 기본값 사용
                pass
            
            return content
            
        except Exception as e:
            print(f"> Sequential-thinking 실패: {str(e)}")
            raise
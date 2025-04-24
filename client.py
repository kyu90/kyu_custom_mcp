import asyncio
from typing import Optional, Dict, Any, List
from contextlib import AsyncExitStack
import json
import ollama
import sys
import os
import time
import re

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from dotenv import load_dotenv

# 도구별 확장 기능 모듈 가져오기
from sequential_thinking_extension import SequentialThinkingExtension
from perplexity_extension import PerplexityExtension

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self, verbose=False):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.ollama_client = ollama
        self.verbose = verbose
        self.server_tools_map = {}  # 서버별 도구 목록을 저장할 딕셔너리
        self.connected_servers = []  # 연결된 서버 목록
        
        print("MCPClient 초기화됨")

    async def connect_to_all_servers(self):
        """설정 파일에 있는 모든 서버에 연결합니다."""
        if not os.path.exists('mcp-servers-config.json'):
            print("오류: mcp-servers-config.json 파일이 없습니다.")
            return False
            
        try:
            with open('mcp-servers-config.json', 'r') as f:
                config = json.load(f)
            
            if 'mcpServers' not in config or not config['mcpServers']:
                print("오류: 서버 설정이 없습니다.")
                return False
                
            print("사용 가능한 서버 목록:")
            for server_name in config['mcpServers']:
                print(f"- {server_name}")
                
            for server_name, server_config in config['mcpServers'].items():
                await self.connect_to_server(server_name)
                
            return True
        except Exception as e:
            print(f"서버 연결 오류: {str(e)}")
            return False

    async def connect_to_server(self, server_name: str = None, server_script_path: str = None, max_retries: int = 3):
        """MCP 서버에 연결합니다

        Args:
            server_name: 설정 파일의 서버 이름
            server_script_path: 서버 스크립트 경로 (.py 또는 .js)
            max_retries: 최대 재시도 횟수
        """
        # 서버 연결 시작 표시
        display_name = server_name if server_name else os.path.basename(server_script_path).split('.')[0]
        print(f"> {display_name} 서버에 연결 중...")
        
        retries = 0
        while retries < max_retries:
            try:
                if server_name:
                    # 서버 설정 로드
                    if self.verbose:
                        print("서버 설정을 로드하는 중...")
                    with open('mcp-servers-config.json', 'r') as f:
                        config = json.load(f)
                    
                    if server_name not in config['mcpServers']:
                        raise ValueError(f"서버 {server_name}를 설정에서 찾을 수 없습니다")
                    
                    server_config = config['mcpServers'][server_name]
                    
                    # npx 명령어를 위한 환경 변수 설정
                    env = server_config.get('env', {})
                    if server_config['command'] == 'npx':
                        env = {
                            **env,
                            'NPM_CONFIG_YES': 'true',  # npm 설치 시 자동으로 yes
                            'NPX_FORCE': 'true'  # 패키지가 없을 경우 자동 설치
                        }
                    
                    server_params = StdioServerParameters(
                        command=server_config['command'],
                        args=server_config['args'],
                        env=env
                    )
                    if self.verbose:
                        print(f"서버 파라미터: {server_params}")
                else:
                    # 직접 스크립트 경로 사용
                    is_python = server_script_path.endswith('.py')
                    is_js = server_script_path.endswith('.js')
                    if not (is_python or is_js):
                        raise ValueError("서버 스크립트는 .py 또는 .js 파일이어야 합니다")

                    command = "python" if is_python else "node"
                    server_params = StdioServerParameters(
                        command=command,
                        args=[server_script_path],
                        env=None
                    )
                    server_name = os.path.basename(server_script_path).split('.')[0]

                if self.verbose:
                    print("stdio 전송 생성 중...")
                
                # 명시적인 단계 표시
                print(f"> {server_name} 서버 초기화 중...")    
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
                stdio, write = stdio_transport
                
                if self.verbose:
                    print("클라이언트 세션 생성 중...")
                session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
                
                if self.verbose:
                    print("세션 초기화 중...")
                await session.initialize()

                # 도구 목록 로딩 표시
                print(f"> {server_name} 서버의 도구 목록 로딩 중...")
                response = await session.list_tools()
                tools = response.tools
                
                # 서버 및 도구 정보 저장
                self.server_tools_map[server_name] = {
                    "session": session,
                    "tools": tools,
                    "write": write
                }
                
                self.connected_servers.append(server_name)
                
                print(f"> {server_name} 서버 연결 성공 ✓")
                print(f"  사용 가능한 도구: {', '.join([tool.name for tool in tools])}")
                return True
                
            except Exception as e:
                retries += 1
                if retries < max_retries:
                    wait_time = 2 ** retries  # 지수 백오프
                    print(f"> {server_name} 서버 연결 실패 ({retries}/{max_retries}). {wait_time}초 후 재시도...")
                    if self.verbose:
                        print(f"  오류 내용: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"> {server_name} 서버 연결 최종 실패. 최대 재시도 횟수 초과.")
                    print(f"  오류 내용: {str(e)}")
                    return False
        
        return False

    async def find_tool_server(self, tool_name: str) -> tuple:
        """지정된 도구를 제공하는 서버 세션을 찾습니다"""
        for server_name, server_info in self.server_tools_map.items():
            for tool in server_info["tools"]:
                if tool.name == tool_name:
                    return server_info["session"], server_name
        return None, None

    async def process_query(self, query: str, system_message: str = None, model: str = "MFDoom/deepseek-r1-tool-calling:14b", temperature: float = 0.7) -> Dict[str, Any]:
        """사용자 쿼리를 처리하고 도구 호출을 실행합니다.

        Args:
            query: 사용자 쿼리
            system_message: 시스템 메시지 (선택사항)
            model: 사용할 모델 이름
            temperature: 모델 temperature 값

        Returns:
            Dict: 처리 결과
        """
        if not self.connected_servers:
            raise RuntimeError("연결된 서버가 없습니다. connect_to_server()를 먼저 호출하세요.")

        # 모든 서버의 도구 목록 통합
        all_tools = []
        for server_info in self.server_tools_map.values():
            all_tools.extend(server_info["tools"])

        # 시스템 메시지 포맷팅
        if system_message is None:
            # 도구 형식 예시 추가
            system_message = """You are a helpful AI assistant that can use various tools to help users.
When using tools, use this format:

[TOOL]tool_name{"parameter1": "value1", "parameter2": "value2"}[/TOOL]

For example, to list files in the current directory:
[TOOL]get_local_file_list{"path": "."}[/TOOL]

Make sure to always include all required parameters for tools.

Available tools:
"""
            # 각 도구의 설명과 필수 매개변수를 명시적으로 추가
            for tool in all_tools:
                system_message += f"- {tool.name}: {tool.description}\n"
                # 필수 매개변수 표시
                required_params = tool.inputSchema.get("required", [])
                if required_params:
                    system_message += f"  Required parameters: {', '.join(required_params)}\n"
                # 매개변수 설명 추가
                if "properties" in tool.inputSchema:
                    for param_name, param_info in tool.inputSchema["properties"].items():
                        param_desc = param_info.get("description", "")
                        param_type = param_info.get("type", "")
                        system_message += f"  - {param_name} ({param_type}): {param_desc}\n"

        # 모델과 대화
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ]

        try:
            # 모델과 대화 시작 표시
            print(f"> {model} 모델에 쿼리 전송 중...")
            
            if self.verbose:
                print(f"모델 상세: {model}, 쿼리: {query}")
                print(f"시스템 메시지: {system_message}")
                
            response = self.ollama_client.chat(
                model=model,
                messages=messages,
                stream=False,
                options={"temperature": temperature}
            )
            
            print(f"> 모델 응답 완료")
            
            assistant_message = response["message"]["content"]
            
            if self.verbose:
                print(f"모델 응답: {assistant_message}")
            
            # 응답에서 text와 tool_use 파싱
            text = assistant_message
            tool_calls = self._parse_tool_calls(assistant_message)
            
            if self.verbose:
                print(f"파싱된 도구 호출: {tool_calls}")
            
            results = []
            
            # 도구 호출 개수 미리 표시
            if len(tool_calls) > 0:
                if len(tool_calls) > 1:
                    print(f"> 총 {len(tool_calls)}개의 도구 호출 실행 예정")
                
                for i, tool_call in enumerate(tool_calls):
                    tool_name = tool_call["name"]
                    parameters = tool_call["parameters"]
                    
                    # 여러 도구 호출일 경우 번호 표시
                    if len(tool_calls) > 1:
                        print(f"> 도구 호출 {i+1}/{len(tool_calls)}: {tool_name}")
                    
                    if self.verbose:
                        print(f"  매개변수: {parameters}")
                    
                    try:
                        result = await self.execute_tool(tool_name, **parameters)
                        results.append(result)
                        
                        if self.verbose:
                            print(f"도구 실행 결과: {result}")
                    except Exception as e:
                        error_msg = f"도구 '{tool_name}' 실행 중 오류 발생: {str(e)}"
                        results.append({"error": error_msg})
                        print(f"> 도구 {tool_name} 실행 실패: {str(e)}")
                        
                        if self.verbose:
                            print(f"도구 실행 오류: {error_msg}")

            # 도구 호출 결과가 있으면 후속 처리
            if tool_calls and results:
                # 도구 호출 결과를 포함한 새로운 메시지 작성
                follow_up_messages = messages.copy()
                
                # 도구 호출 결과 메시지 추가
                for i, (tool_call, result) in enumerate(zip(tool_calls, results)):
                    if "error" in result:
                        tool_result = f"Error: {result['error']}"
                    else:
                        tool_result = str(result)
                    
                    follow_up_messages.append({
                        "role": "user", 
                        "content": f"Tool '{tool_call['name']}' result: {tool_result}"
                    })
                
                # 후속 응답 가져오기 - 진행 상황 표시
                print(f"> 도구 실행 결과로 {model} 모델에 후속 응답 요청 중...")
                    
                if self.verbose:
                    print(f"후속 메시지: {follow_up_messages[-1]['content'][:100]}...")
                    
                follow_up_response = self.ollama_client.chat(
                    model=model,
                    messages=follow_up_messages,
                    stream=False,
                    options={"temperature": temperature}
                )
                
                print(f"> 후속 응답 완료")
                
                follow_up_text = follow_up_response["message"]["content"]
                
                if self.verbose:
                    print(f"후속 응답: {follow_up_text}")
                
                # 최종 텍스트를 후속 응답으로 업데이트
                text = follow_up_text

            return {
                "query": query,
                "text": text,
                "tool_calls": tool_calls,
                "results": results
            }

        except Exception as e:
            print(f"> 오류: 쿼리 처리 중 문제 발생")
            raise RuntimeError(f"쿼리 처리 중 오류 발생: {str(e)}")

    def _parse_tool_calls(self, message: str) -> List[Dict[str, Any]]:
        """Parse tool calls from a message.

        Args:
            message: The message to parse

        Returns:
            List[Dict]: List of parsed tool calls
        """
        if self.verbose:
            print(f"도구 호출 파싱 시작. 메시지: {message[:200]}...")
        
        tool_calls = []
        
        # 1. [TOOL]tool_name{...}[/TOOL] 형식 처리 (예상 응답 형식)
        tool_pattern = r'\[TOOL\](.*?)\{(.*?)\}\[/TOOL\]'
        matches = re.findall(tool_pattern, message, re.DOTALL)
        
        if matches:
            if self.verbose:
                print(f"[TOOL] 형식 도구 호출 감지됨: {matches}")
                
            for match in matches:
                tool_name = match[0].strip()
                params_json = '{' + match[1].strip() + '}'
                
                try:
                    parameters = json.loads(params_json)
                    tool_calls.append({"name": tool_name, "parameters": parameters})
                except json.JSONDecodeError as e:
                    if self.verbose:
                        print(f"JSON 파싱 오류: {str(e)}, 텍스트: {params_json}")
        
        # 2. 특정 도구 호출 패턴 직접 처리
        if not tool_calls and "get_local_file_list" in message:
            # get_local_file_list(path=".") 형식 파싱
            file_list_patterns = [
                r'get_local_file_list\s*\(\s*path\s*=\s*[\'"]([^\'"]+)[\'"]\s*\)',  # get_local_file_list(path=".")
                r'get_local_file_list\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',  # get_local_file_list(".")
                r'get_local_file_list\s*\(\s*\{\s*[\'"]path[\'"]\s*:\s*[\'"]([^\'"]+)[\'"]\s*\}\s*\)'  # get_local_file_list({"path": "."})
            ]
            
            for pattern in file_list_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    if self.verbose:
                        print(f"get_local_file_list 도구 호출 감지됨: {matches}")
                    
                    for path in matches:
                        tool_calls.append({
                            "name": "get_local_file_list",
                            "parameters": {"path": path}
                        })
                    break
            
            # 도구 이름이 있지만 매개변수가 명확하지 않은 경우, 기본값 사용
            if not tool_calls and "get_local_file_list" in message:
                if self.verbose:
                    print("매개변수 없는 get_local_file_list 도구 호출 감지됨, 기본 경로 '.' 사용")
                
                tool_calls.append({
                    "name": "get_local_file_list",
                    "parameters": {"path": "."}
                })
        
        # 3. XML 형식 처리 
        if not tool_calls and ('<function_calls>' in message or '<function_calls>' in message):
            if self.verbose:
                print("XML 형식 도구 호출 감지됨")
                
            xml_patterns = [
                r'<(?:antml:)?function_calls>.*?<(?:antml:)?invoke name="([^"]+)">(.*?)</(?:antml:)?invoke>.*?</(?:antml:)?function_calls>',
                r'<(?:antml:)?invoke name="([^"]+)">(.*?)</(?:antml:)?invoke>'
            ]
            
            for pattern in xml_patterns:
                matches = re.findall(pattern, message, re.DOTALL)
                for match in matches:
                    tool_name = match[0]
                    params_text = match[1]
                    parameters = {}
                    
                    # 매개변수 파싱
                    param_pattern = r'<(?:antml:)?parameter name="([^"]+)">(.*?)</(?:antml:)?parameter>'
                    param_matches = re.findall(param_pattern, params_text, re.DOTALL)
                    
                    for param_name, param_value in param_matches:
                        try:
                            # JSON 파싱 시도
                            parameters[param_name] = json.loads(param_value.strip())
                        except json.JSONDecodeError:
                            # 텍스트 그대로 사용
                            parameters[param_name] = param_value.strip()
                    
                    tool_calls.append({"name": tool_name, "parameters": parameters})
        
        # 4. JSON 형식 처리 
        # JSON 블록 찾기
        if not tool_calls:
            json_blocks = re.findall(r'```json\s*(.*?)\s*```', message, re.DOTALL)
            if not json_blocks:
                json_blocks = re.findall(r'{.*"type"\s*:\s*"tool_use".*}', message, re.DOTALL)
            
            if json_blocks:
                if self.verbose:
                    print("JSON 블록 도구 호출 감지됨")
                    
                for json_block in json_blocks:
                    try:
                        # 가능한 JSON 텍스트 정리
                        json_text = json_block.strip()
                        data = json.loads(json_text)
                        
                        # content 배열이나 직접 tool_use 객체 찾기
                        if "content" in data:
                            for item in data["content"]:
                                if item.get("type") == "tool_use":
                                    tool_calls.append({
                                        "name": item.get("name", ""),
                                        "parameters": item.get("input", {})
                                    })
                        elif data.get("type") == "tool_use":
                            tool_calls.append({
                                "name": data.get("name", ""),
                                "parameters": data.get("input", {})
                            })
                    except Exception as e:
                        if self.verbose:
                            print(f"JSON 파싱 오류: {str(e)}")
        
        # 5. 특수 패턴 처리 (예: "Tool: tool_name(param1=value1, param2=value2)")
        if not tool_calls:
            tool_pattern = r'Tool:\s*(\w+)\(([^)]*)\)'
            tool_matches = re.findall(tool_pattern, message, re.DOTALL)
            
            if tool_matches:
                if self.verbose:
                    print("특수 패턴 도구 호출 감지됨")
                    
                for tool_match in tool_matches:
                    tool_name = tool_match[0]
                    params_text = tool_match[1]
                    parameters = {}
                    
                    # 매개변수 파싱 (param1=value1, param2=value2 형식)
                    params_items = params_text.split(',')
                    for param_item in params_items:
                        if '=' in param_item:
                            param_name, param_value = param_item.split('=', 1)
                            param_name = param_name.strip()
                            param_value = param_value.strip()
                            
                            try:
                                # 따옴표 제거 후 JSON 파싱 시도
                                if param_value.startswith('"') and param_value.endswith('"'):
                                    param_value = param_value[1:-1]
                                parameters[param_name] = json.loads(param_value)
                            except json.JSONDecodeError:
                                # 텍스트 그대로 사용
                                parameters[param_name] = param_value
                    
                    tool_calls.append({"name": tool_name, "parameters": parameters})
        
        if self.verbose:
            print(f"파싱 결과: {len(tool_calls)}개의 도구 호출 발견: {tool_calls}")
            
        return tool_calls

    async def chat_loop(self):
        """대화형 채팅 루프 실행"""
        print("\nMCP 클라이언트가 시작되었습니다!")
        print("쿼리를 입력하거나 'quit'을 입력해 종료하세요.")
        print("로그를 보려면 '로그 보기'를 쿼리에 포함시키세요.")

        while True:
            try:
                query = input("\n쿼리: ").strip()

                if query.lower() == 'quit':
                    break

                show_logs = '로그' in query or 'log' in query.lower()
                result = await self.process_query(query)
                
                if not show_logs:
                    # 도구 실행 결과 출력
                    for i, tool_result in enumerate(result.get('results', [])):
                        tool_name = result.get('tool_calls', [])[i]['name'] if i < len(result.get('tool_calls', [])) else 'unknown'
                        if isinstance(tool_result, dict) and 'error' in tool_result:
                            print(f"\n도구 '{tool_name}' 오류: {tool_result['error']}")
                        else:
                            print(f"\n도구 '{tool_name}' 결과:\n{tool_result}")
                    
                    # 모델 응답 출력
                    if 'text' in result:
                        print(f"\n{result['text']}")
                else:
                    # 전체 응답 표시
                    print("\n" + json.dumps(result, ensure_ascii=False, indent=2))

            except Exception as e:
                print(f"\n오류: {str(e)}")

    async def cleanup(self):
        """리소스 정리"""
        try:
            await self.exit_stack.aclose()
        except Exception as e:
            print(f"정리 중 오류 발생: {str(e)}")

    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """도구를 실행합니다."""
        session, server_name = await self.find_tool_server(tool_name)
        if session is None:
            raise ValueError(f"도구 '{tool_name}'를 찾을 수 없습니다. 연결된 서버: {', '.join(self.connected_servers)}")
        
        # 도구 실행 시작을 항상 표시 (verbose 모드가 아니어도)
        print(f"> {tool_name} 실행 중...")
        
        if self.verbose:
            print(f"  도구 상세 정보: {tool_name}, 서버: {server_name}, 매개변수: {kwargs}")
        
        try:
            # 시작 시간 기록
            start_time = time.time()
            
            # 도구 실행
            result = await session.call_tool(tool_name, kwargs)
            
            # 종료 시간 및 실행 시간 계산
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 도구 실행 완료 메시지 표시
            print(f"> {tool_name} 완료 ({execution_time:.2f}초)")
            
            return result.content
        except Exception as e:
            # 도구 실행 실패 메시지 표시
            print(f"> {tool_name} 실패: {str(e)}")
            raise

async def main():
    import sys
    
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    client = MCPClient(verbose=verbose)
    
    try:
        # 서버 연결 로직 확인
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            if sys.argv[1].startswith("--server="):
                server_name = sys.argv[1].split("=")[1]
                await client.connect_to_server(server_name=server_name)
            else:
                await client.connect_to_server(server_script_path=sys.argv[1])
        else:
            # 설정 파일에서 모든 서버에 연결
            success = await client.connect_to_all_servers()
            if not success:
                print("사용법: python client.py <서버_스크립트_경로>")
                print("     또는 python client.py --server=<서버_이름>")
                print("     또는 python client.py  # 모든 설정된 서버에 연결")
                sys.exit(1)
        
        # 확장 모듈 적용
        if "sequential-thinking" in client.connected_servers:
            # Sequential Thinking 확장 적용
            st_extension = SequentialThinkingExtension(client)
            await st_extension.patch_client()
            
        # Perplexity Ask 확장 적용
        if "perplexity-ask" in client.connected_servers:
            px_extension = PerplexityExtension(client)
            await px_extension.patch_client()
                
        await client.chat_loop()
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다...")
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램이 중단되었습니다.")

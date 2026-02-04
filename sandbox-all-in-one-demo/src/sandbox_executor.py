"""
Sandbox 执行器

在 All-In-One Sandbox 中执行代码、安装依赖、读取文件
支持本地模式和远程模式
"""

import httpx
import json
import logging
import asyncio
import uuid
import os
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

# 确保日志能输出到控制台
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


class SandboxExecutor:
    """All-In-One Sandbox 代码执行器"""

    def __init__(self, sandbox_base_url: str, sandbox=None, log_callback=None):
        """
        初始化执行器

        Args:
            sandbox_base_url: Sandbox 的 HTTP 基础 URL
                例如: https://xxx.agentrun-data.cn-hangzhou.aliyuncs.com/sandboxes/xxx
            sandbox: Sandbox 实例（用于 context.execute_async）
            log_callback: 日志回调函数，用于实时推送日志到 VNC Viewer
        """
        self.base_url = sandbox_base_url.rstrip("/")
        self.sandbox = sandbox
        self.client = httpx.Client(timeout=300.0)
        self.log_callback = log_callback
        
        # 读取环境变量决定是否使用本地模式
        self.local_mode = os.environ.get("LOCAL_MODE", "false").lower() == "true"
        self.local_base_url = "http://localhost:5000"
        
        if self.local_mode:
            logger.info(f"[本地] 本地模式已启用")
            logger.info(f"[位置] 本地 API 地址: {self.local_base_url}")
        else:
            logger.info(f"[远程]  远程模式（默认）")
        
        logger.info(f"[配置] 初始化 Sandbox 执行器")
        logger.debug(f"Sandbox URL: {self.base_url}")
        if log_callback:
            self._log(f"[配置] Sandbox 执行器已初始化", "INFO")
    
    def set_log_callback(self, callback):
        """
        动态设置日志回调函数
        
        Args:
            callback: 日志回调函数
        """
        self.log_callback = callback
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """
        发送日志到回调函数（如果有）并始终打印到控制台
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        # 始终打印到控制台
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.log(log_level, message)
        
        # 如果有回调，也发送到回调
        if self.log_callback:
            try:
                self.log_callback(message, level)
            except Exception as e:
                logger.debug(f"日志回调失败: {e}")

    def read_file(self, file_path: str) -> str:
        """
        读取 Sandbox 中的文件
        
        Args:
            file_path: 文件路径（可以是相对路径或绝对路径）
                       - 相对路径（如 "result.json"）会自动转换为 /home/user/result.json
                       - 绝对路径（如 "/tmp/data.txt"）会直接使用
        
        Returns:
            文件内容（字符串）
        
        Raises:
            Exception: 文件不存在或读取失败
        
        Examples:
            >>> executor.read_file("result.json")           # 读取 /home/user/result.json
            >>> executor.read_file("/home/user/data.txt")   # 读取 /home/user/data.txt
            >>> executor.read_file("/tmp/temp.log")         # 读取 /tmp/temp.log
        """
        # 记录读取开始
        logger.info("=" * 70)
        logger.info(f"[打开] 读取文件: {file_path}")
        
        #  自动处理路径：如果不是绝对路径，添加 /home/user 前缀
        if not file_path.startswith('/'):
            original_path = file_path
            file_path = f"/home/user/{file_path}"
            logger.info(f"[刷新] 相对路径转换: {original_path} → {file_path}")
            self._log(f"[刷新] 转换为绝对路径: {file_path}", "DEBUG")
        
        self._log(f"[打开] 正在读取文件: {file_path}", "INFO")
        
        url = f"{self.base_url}/files"
        params = {"path": file_path}

        try:
            logger.debug(f"[发送] 发送请求到: {url}")
            logger.debug(f"📦 参数: {params}")
            
            response = self.client.get(url, params=params)
            response.raise_for_status()

            result = response.json()
            # API 返回格式: {"entry": {...}, "content": str, "encoding": "utf-8"}
            content = result.get("content", "")
            
            #  记录读取结果
            content_lines = content.split('\n')
            content_size = len(content)
            
            logger.info(f"[OK] 文件读取成功")
            logger.info(f"[统计] 文件大小: {content_size} 字节")
            logger.info(f"[统计] 行数: {len(content_lines)} 行")
            
            # 显示文件内容预览
            if content_size > 0:
                logger.info("[文件] 文件内容预览（前 10 行）:")
                for line in content_lines[:10]:
                    logger.info(f"  {line}")
                if len(content_lines) > 10:
                    logger.info(f"  ... (共 {len(content_lines)} 行)")
            else:
                logger.info("[文件] 文件内容: (空)")
            
            #  发送到 VNC Viewer
            self._log(f"[OK] 文件读取成功: {file_path} ({content_size} 字节)", "ACTION")
            
            logger.info("=" * 70)
            return content
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[ERROR] 读取文件失败: HTTP {e.response.status_code}")
            logger.error(f"响应内容: {e.response.text[:500]}")
            
            self._log(f"[ERROR] 读取文件失败: {file_path}", "ERROR")
            
            raise Exception(
                f"读取文件失败: HTTP {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            logger.error(f"[ERROR] 读取文件失败: {str(e)}")
            logger.exception(e)
            
            self._log(f"[ERROR] 读取文件失败: {str(e)}", "ERROR")
            
            raise Exception(f"读取文件失败: {str(e)}")

    def close(self):
        """关闭 HTTP 客户端"""
        self.client.close()
    
    async def _execute_code_local(
        self,
        code: str,
        language: str,
        on_output: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """
        本地模式：直接调用 localhost:5000/contexts/execute
        
        Args:
            code: 代码字符串
            language: 语言类型 ('javascript' 或 'python')
            on_output: 异步输出回调函数
        
        Returns:
            与 SDK 相同格式的结果字典
        """
        url = f"{self.local_base_url}/contexts/execute"
        logger.info(f"[本地] 本地执行 API: {url}")
        logger.info(f"[记录] 语言: {language}")
        
        payload = {
            "code": code,
            "language": language,
            "timeout": 300000  # 5 分钟（毫秒）
        }
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"[OK] 本地执行响应状态: {response.status_code}")
                logger.info(f"[统计] 响应数据: {result}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP 错误: {e.response.status_code} - {e.response.text}"
            logger.error(f"[ERROR] {error_msg}")
            return {
                "code": "HTTP_ERROR",
                "message": error_msg,
                "results": []
            }
        except Exception as e:
            error_msg = f"本地执行失败: {str(e)}"
            logger.error(f"[ERROR] {error_msg}")
            return {
                "code": "EXECUTION_ERROR",
                "message": error_msg,
                "results": []
            }

    def execute_python_code(
        self, code: str, context_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        在 Sandbox 中执行 Python 代码（使用 /contexts/execute API）

        Args:
            code: Python 代码字符串
            context_id: 执行上下文 ID（可选，用于跨步骤保持变量）

        Returns:
            {
                "executionId": str,  # 返回的 contextId
                "status": "completed" | "failed",
                "result": {
                    "exitCode": int,
                    "stdout": str,
                    "stderr": str
                }
            }
        """
        logger.info("=" * 70)
        logger.info("[启动] 开始执行 Python 代码")
        logger.info("-" * 70)
        
        # 记录代码内容（截断显示）
        code_lines = code.split('\n')
        code_preview = '\n'.join(code_lines[:10])
        if len(code_lines) > 10:
            code_preview += f"\n... (共 {len(code_lines)} 行，仅显示前 10 行)"
        
        logger.info("[记录] 代码内容:")
        for line in code_preview.split('\n'):
            logger.info(f"  {line}")
        
        if context_id:
            logger.info(f"🔑 上下文 ID: {context_id}")
        
        self._log("[启动] 开始执行 Python 代码...", "THINKING")
        
        url = f"{self.base_url}/contexts/execute"

        # contextId 和 language 互斥，只能传一个
        payload = {
            "code": code,
            "timeout": 300000,  # 5 分钟超时（毫秒）
        }

        if context_id:
            payload["contextId"] = context_id  # 有 contextId 时不传 language
        else:
            payload["language"] = "python"  # 没有 contextId 时传 language

        try:
            logger.debug(f"[发送] 发送请求到: {url}")
            logger.debug(f"📦 请求体: {json.dumps(payload, ensure_ascii=False)}")
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # 记录原始响应（用于调试）
            logger.debug("=" * 70)
            logger.debug("[接收] 原始响应:")
            logger.debug(json.dumps(result, ensure_ascii=False, indent=2))
            logger.debug("=" * 70)
            
            # 解析 API 响应格式
            # 格式：{"contextId": "...", "results": [{"type": "stdout/stderr/error", "text/value": "..."}]}
            returned_context_id = result.get('contextId', 'N/A')
            results = result.get('results', [])
            
            # 从 results 中提取 stdout 和 stderr
            stdout_parts = []
            stderr_parts = []
            error_parts = []
            has_error = False
            
            for item in results:
                item_type = item.get('type', '')
                if item_type == 'stdout':
                    stdout_parts.append(item.get('text', ''))
                elif item_type == 'stderr':
                    stderr_parts.append(item.get('text', ''))
                elif item_type == 'error':
                    has_error = True
                    error_parts.append(item.get('value', ''))
            
            stdout = '\n'.join(stdout_parts)
            stderr = '\n'.join(stderr_parts)
            error_msg = '\n'.join(error_parts)
            
            # 判断执行状态
            if has_error:
                status = 'failed'
                exit_code = 1
            else:
                status = 'completed'
                exit_code = 0
            
            # 记录执行结果
            logger.info("-" * 70)
            logger.info("[OK] 代码执行完成")
            logger.info(f"[统计] 状态: {status}")
            logger.info(f"🆔 上下文 ID: {returned_context_id}")
            logger.info(f"🔢 退出码: {exit_code}")
            
            if stdout:
                logger.info("[发送] 标准输出:")
                stdout_lines = stdout.strip().split('\n')
                for line in stdout_lines[:20]:  # 最多显示 20 行
                    logger.info(f"  {line}")
                if len(stdout_lines) > 20:
                    logger.info(f"  ... (输出共 {len(stdout_lines)} 行，仅显示前 20 行)")
            else:
                logger.info("[发送] 标准输出: (无)")
            
            if stderr or error_msg:
                logger.warning("[WARNING]  错误信息:")
                error_text = stderr + error_msg
                error_lines = error_text.strip().split('\n')
                for line in error_lines[:20]:  # 最多显示 20 行
                    logger.warning(f"  {line}")
                if len(error_lines) > 20:
                    logger.warning(f"  ... (错误共 {len(error_lines)} 行，仅显示前 20 行)")
            
            # 发送到日志回调
            if exit_code == 0:
                self._log(f"[OK] 代码执行成功", "ACTION")
            else:
                self._log(f"[ERROR] 代码执行失败", "ERROR")
                if error_text:
                    error_preview = '\n'.join(error_text.strip().split('\n')[:5])
                    self._log(f"[WARNING]  错误: {error_preview}", "ERROR")
            
            logger.info("=" * 70)
            
            # 返回统一格式
            return {
                "executionId": returned_context_id,
                "status": status,
                "result": {
                    "exitCode": exit_code,
                    "stdout": stdout,
                    "stderr": stderr + error_msg,
                }
            }
            
        except httpx.HTTPStatusError as e:
            logger.error("[ERROR] HTTP 请求失败")
            logger.error(f"状态码: {e.response.status_code}")
            logger.error(f"响应内容: {e.response.text[:500]}")
            
            self._log(f"[ERROR] HTTP 请求失败: {e.response.status_code}", "ERROR")
            
            return {
                "executionId": None,
                "status": "failed",
                "result": {
                    "exitCode": -1,
                    "stdout": "",
                    "stderr": f"HTTP Error: {e.response.status_code} - {e.response.text}",
                },
            }
        except Exception as e:
            logger.error(f"[ERROR] 执行失败: {str(e)}")
            logger.exception(e)
            
            self._log(f"[ERROR] 执行失败: {str(e)}", "ERROR")
            
            return {
                "executionId": None,
                "status": "failed",
                "result": {
                    "exitCode": -1,
                    "stdout": "",
                    "stderr": f"Error: {str(e)}",
                },
            }

    def execute_shell_command(self, command: str) -> Dict[str, Any]:
        """
        执行 Shell 命令（使用 /processes/cmd API）
        
        Args:
            command: Shell 命令字符串
        
        Returns:
            {
                "status": "completed" | "failed",
                "result": {
                    "exitCode": int,
                    "stdout": str,
                    "stderr": str
                }
            }
        """
        logger.info("=" * 70)
        logger.info("[配置] 开始执行 Shell 命令")
        logger.info(f"[记录] 命令: {command}")
        
        self._log(f"[配置] 执行命令: {command[:100]}...", "THINKING")
        
        #  本地模式：使用 localhost:5000/processes/cmd
        if self.local_mode:
            url = f"{self.local_base_url}/processes/cmd"
            logger.info(f"[本地] 本地模式 Shell API: {url}")
        else:
            url = f"{self.base_url}/processes/cmd"
            logger.info(f"[远程]  远程模式 Shell API: {url}")
        
        payload = {"command": command}
        
        try:
            logger.debug(f"[发送] 发送请求到: {url}")
            logger.debug(f"📦 请求体: {payload}")
            
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            
            logger.info("-" * 70)
            logger.info("[OK] 命令执行完成")
            
            if 'result' in result:
                cmd_result = result['result']
                exit_code = cmd_result.get('exitCode', -1)
                stdout = cmd_result.get('stdout', '')
                stderr = cmd_result.get('stderr', '')
                
                logger.info(f"🔢 退出码: {exit_code}")
                
                if stdout:
                    logger.info("[发送] 输出:")
                    stdout_lines = stdout.strip().split('\n')
                    for line in stdout_lines[-20:]:  # 显示最后 20 行
                        logger.info(f"  {line}")
                
                if stderr:
                    logger.warning("[WARNING]  错误:")
                    stderr_lines = stderr.strip().split('\n')
                    for line in stderr_lines[-10:]:  # 显示最后 10 行
                        logger.warning(f"  {line}")
                
                # 发送到日志回调
                if exit_code == 0:
                    self._log(f"[OK] 命令执行成功", "ACTION")
                else:
                    self._log(f"[ERROR] 命令执行失败（退出码: {exit_code}）", "ERROR")
            
            logger.info("=" * 70)
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error("[ERROR] HTTP 请求失败")
            logger.error(f"状态码: {e.response.status_code}")
            logger.error(f"响应内容: {e.response.text[:500]}")
            
            self._log(f"[ERROR] 命令失败: HTTP {e.response.status_code}", "ERROR")
            
            return {
                "status": "failed",
                "result": {
                    "exitCode": -1,
                    "stdout": "",
                    "stderr": f"HTTP Error: {e.response.status_code} - {e.response.text}",
                },
            }
        except Exception as e:
            logger.error(f"[ERROR] 命令失败: {str(e)}")
            logger.exception(e)
            
            self._log(f"[ERROR] 命令失败: {str(e)}", "ERROR")
            
            return {
                "status": "failed",
                "result": {"exitCode": -1, "stdout": "", "stderr": f"Error: {str(e)}"},
            }

    async def execute_python_code_streaming(
        self, 
        code: str, 
        context_id: Optional[str] = None,
        on_output: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """
        使用 SDK 的 context.execute_async 方法执行 Python 代码
        
        注意：每次执行都是独立的，不保存变量状态（除非使用同一个 context_id）
        
        Args:
            code: Python 代码字符串
            context_id: 执行上下文ID（可选，如果不提供会创建新的 context）
            on_output: 异步输出回调函数 async (line, stream_type) -> None
                      stream_type 可以是 'stdout'、'stderr'、'info' 或 'error'
        
        Returns:
            {
                "executionId": str,
                "status": "completed" | "failed",
                "result": {
                    "exitCode": int,
                    "stdout": str,
                    "stderr": str
                }
            }
        """
        logger.info("=" * 70)
        logger.info("[启动] 使用 SDK 执行 Python 代码")
        logger.info("-" * 70)
        
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        try:
            if on_output:
                await on_output("[启动] 开始执行代码...\n", "info")
            
            logger.info(f"[发送] 执行代码（context_id: {context_id or 'new'}）")
            logger.info(f"📏 代码大小: {len(code)} 字节")
            
            #  本地模式：直接调用 localhost:5000/contexts/execute
            if self.local_mode:
                logger.info("[本地] 使用本地模式执行")
                result = await self._execute_code_local(code, "python", on_output)
            else:
                # [远程] 远程模式：使用 SDK 的 context.execute_async 方法
                logger.info("[远程]  使用远程 SDK 执行")
                logger.info("⏳ 调用 SDK context.execute_async...")
                
                if context_id:
                    # 如果有 context_id，使用它（不传 language）
                    result = await self.sandbox.context.execute_async(
                        code=code,
                        context_id=context_id,
                        timeout=300
                    )
                else:
                    # 如果没有 context_id，只传 language
                    result = await self.sandbox.context.execute_async(
                        code=code,
                        language="python",
                        timeout=300
                    )
            
            logger.info("[OK] SDK 执行完成")
            logger.info(f"执行结果类型: {type(result)}")
            logger.info(f"执行结果键: {result.keys() if isinstance(result, dict) else 'N/A'}")
            logger.info(f"执行结果: {result}")
            
            # 解析结果
            # AgentRun API 返回格式：{"contextId": "...", "results": [...]}
            # results 是一个数组，包含 {"type": "stdout/stderr/result", "text": "..."}
            stdout = ""
            stderr = ""
            exit_code = 0
            
            if isinstance(result, dict):
                results = result.get("results", [])
                logger.info(f"[统计] results 数组长度: {len(results)}")
                
                # 遍历 results 提取输出
                for item in results:
                    item_type = item.get("type", "")
                    if item_type == "stdout":
                        text = item.get("text", "")
                        stdout += text
                        logger.info(f"  - stdout: {len(text)} 字节")
                    elif item_type == "stderr":
                        text = item.get("text", "")
                        stderr += text
                        logger.info(f"  - stderr: {len(text)} 字节")
                    elif item_type == "result":
                        # 有 result 说明执行成功
                        exit_code = 0
                        logger.info(f"  - result: 执行成功")
                
                # 如果没有 results 或 results 为空，检查是否有错误
                if not results:
                    # 检查是否是错误响应
                    if result.get("code") == "INVALID_REQUEST" or result.get("code") == "NOT_FOUND":
                        exit_code = 1
                        stderr = result.get("message", "Unknown error")
                        logger.warning(f"[WARNING]  API 返回错误: {stderr}")
            else:
                logger.error(f"[ERROR] 返回值不是 dict: {result}")
                exit_code = 1
                stderr = f"Invalid response type: {type(result)}"
            
            logger.info(f"[统计] 解析结果 - stdout 长度: {len(stdout)}, stderr 长度: {len(stderr)}, exit_code: {exit_code}")
            
            # 推送标准输出（逐行推送，保留所有内容包括空行）
            if stdout:
                logger.info(f"[发送] 推送 stdout: {len(stdout)} 字节")
                if on_output:
                    # 一次性推送所有输出
                    await on_output(stdout, "stdout")
                    logger.info("[OK] stdout 已推送到回调")
                else:
                    logger.warning("[WARNING]  on_output 回调为 None，无法推送 stdout")
            else:
                logger.info("ℹ️  stdout 为空，跳过推送")
            
            # 推送标准错误
            if stderr:
                logger.info(f"[WARNING]  推送 stderr: {len(stderr)} 字节")
                if on_output:
                    await on_output(stderr, "stderr")
                    logger.info("[OK] stderr 已推送到回调")
            else:
                logger.info("ℹ️  stderr 为空，跳过推送")
            
            # 判断执行状态
            status = "completed" if exit_code == 0 else "failed"
            
            logger.info("-" * 70)
            logger.info(f"[OK] 代码执行完成，退出码: {exit_code}")
            logger.info("=" * 70)
            
            return {
                "executionId": execution_id,
                "status": status,
                "result": {
                    "exitCode": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "executionTimeMs": 0
                }
            }
            
        except Exception as e:
            error_msg = f"执行失败: {str(e)}"
            logger.error(f"[ERROR] {error_msg}")
            logger.exception(e)
            
            if on_output:
                await on_output(f"[ERROR] {error_msg}\n", "error")
            
            logger.info("=" * 70)
            
    async def execute_nodejs_code_streaming(
        self, 
        code: str, 
        on_output: Optional[Callable[[str, str], None]] = None
    ) -> Dict[str, Any]:
        """
        使用 SDK 的 context.execute_async 方法执行 Node.js 代码
        
        注意：SDK 的 language 参数只接受 "python" 或 "javascript"，
             执行 Node.js 代码时使用 "javascript"
        
        Args:
            code: Node.js 代码字符串
            on_output: 异步输出回调函数 async (line, stream_type) -> None
                      stream_type 可以是 'stdout'、'stderr'、'info' 或 'error'
        
        Returns:
            {
                "executionId": str,
                "status": "completed" | "failed",
                "result": {
                    "exitCode": int,
                    "stdout": str,
                    "stderr": str
                }
            }
        """
        logger.info("=" * 70)
        logger.info("[启动] 使用 SDK 执行 Node.js 代码")
        logger.info("-" * 70)
        
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        try:
            if on_output:
                await on_output("[启动] 开始执行 Node.js 代码...\n", "info")
            
            logger.info(f"[发送] 执行 Node.js 代码")
            logger.info(f"📏 代码大小: {len(code)} 字节")
            
            #  本地模式：直接调用 localhost:5000/contexts/execute
            if self.local_mode:
                logger.info("[本地] 使用本地模式执行")
                result = await self._execute_code_local(code, "javascript", on_output)
            else:
                # [远程] 远程模式：使用 SDK 的 context.execute_async 方法
                logger.info("[远程]  使用远程 SDK 执行")
                logger.info("⏳ 调用 SDK context.execute_async (language=javascript)...")
                
                result = await self.sandbox.context.execute_async(
                    code=code,
                    language="javascript",  # SDK 只接受 javascript，不接受 nodejs
                    timeout=300
                )
            
            logger.info("[OK] SDK 执行完成")
            logger.info(f"执行结果类型: {type(result)}")
            logger.info(f"执行结果键: {result.keys() if isinstance(result, dict) else 'N/A'}")
            logger.info(f"执行结果: {result}")
            
            # 解析结果（与 Python 相同）
            stdout = ""
            stderr = ""
            exit_code = 0
            
            if isinstance(result, dict):
                results = result.get("results", [])
                logger.info(f"[统计] results 数组长度: {len(results)}")
                
                # 遍历 results 提取输出
                for item in results:
                    item_type = item.get("type", "")
                    if item_type == "stdout":
                        text = item.get("text", "")
                        stdout += text
                        logger.info(f"  - stdout: {len(text)} 字节")
                    elif item_type == "stderr":
                        text = item.get("text", "")
                        stderr += text
                        logger.info(f"  - stderr: {len(text)} 字节")
                    elif item_type == "result":
                        # 有 result 说明执行成功
                        exit_code = 0
                        logger.info(f"  - result: 执行成功")
                
                # 如果没有 results 或 results 为空，检查是否有错误
                if not results:
                    # 检查是否是错误响应
                    if result.get("code") == "INVALID_REQUEST" or result.get("code") == "NOT_FOUND":
                        exit_code = 1
                        stderr = result.get("message", "Unknown error")
                        logger.warning(f"[WARNING]  API 返回错误: {stderr}")
            else:
                logger.error(f"[ERROR] 返回值不是 dict: {result}")
                exit_code = 1
                stderr = f"Invalid response type: {type(result)}"
            
            logger.info(f"[统计] 解析结果 - stdout 长度: {len(stdout)}, stderr 长度: {len(stderr)}, exit_code: {exit_code}")
            
            # 推送标准输出
            if stdout:
                logger.info(f"[发送] 推送 stdout: {len(stdout)} 字节")
                if on_output:
                    await on_output(stdout, "stdout")
                    logger.info("[OK] stdout 已推送到回调")
                else:
                    logger.warning("[WARNING]  on_output 回调为 None，无法推送 stdout")
            else:
                logger.info("ℹ️  stdout 为空，跳过推送")
            
            # 推送标准错误
            if stderr:
                logger.info(f"[WARNING]  推送 stderr: {len(stderr)} 字节")
                if on_output:
                    await on_output(stderr, "stderr")
                    logger.info("[OK] stderr 已推送到回调")
            else:
                logger.info("ℹ️  stderr 为空，跳过推送")
            
            # 判断执行状态
            status = "completed" if exit_code == 0 else "failed"
            
            logger.info("-" * 70)
            logger.info(f"[OK] Node.js 代码执行完成，退出码: {exit_code}")
            logger.info("=" * 70)
            
            return {
                "executionId": execution_id,
                "status": status,
                "result": {
                    "exitCode": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                    "executionTimeMs": 0
                }
            }
            
        except Exception as e:
            error_msg = f"执行失败: {str(e)}"
            logger.error(f"[ERROR] {error_msg}")
            logger.exception(e)
            
            if on_output:
                await on_output(f"[ERROR] {error_msg}\n", "error")
            
            logger.info("=" * 70)
            
            return {
                "executionId": execution_id,
                "status": "failed",
                "result": {
                    "exitCode": 1,
                    "stdout": "",
                    "stderr": error_msg,
                    "executionTimeMs": 0
                }
            }


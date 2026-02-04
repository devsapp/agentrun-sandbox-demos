"""
AI 代码生成器

使用 Qwen-Max 根据用户需求生成 Python 爬虫代码
"""

import os
import re
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


class ScraperCodeGenerator:
    """AI 爬虫代码生成器"""

    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-max"):
        """
        初始化代码生成器

        Args:
            api_key: DashScope API Key（如果为 None 则从环境变量读取）
            model: 模型名称，默认 qwen-max

        Raises:
            ValueError: 如果 API Key 未设置
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("请设置 DASHSCOPE_API_KEY 环境变量或传入 api_key 参数")

        self.llm = ChatOpenAI(
            model=model,
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            temperature=0.7,
        )

    def generate_scraper_code(
        self,
        user_requirement: str,
        cdp_url: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict[str, str]:
        """
        根据用户需求生成爬虫代码

        Args:
            user_requirement: 用户的自然语言需求
            cdp_url: Sandbox 的 CDP URL
            conversation_history: 对话历史（支持多轮对话），格式为 [{"role": "user"|"assistant", "content": str}, ...]

        Returns:
            {
                "code": str,  # 生成的代码
                "explanation": str  # 代码说明
            }

        Raises:
            Exception: LLM 调用失败时抛出异常
        """
        try:
            # 构建系统提示词
            system_prompt = self._build_system_prompt(cdp_url)

            # 构建消息列表
            messages = [SystemMessage(content=system_prompt)]

            # 添加对话历史
            if conversation_history:
                for msg in conversation_history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))

            # 添加当前用户需求
            messages.append(HumanMessage(content=user_requirement))

            # 调用 LLM
            response = self.llm.invoke(messages)

            # 解析响应
            return self._parse_response(response.content)

        except Exception as e:
            raise Exception(f"LLM 调用失败: {str(e)}")

    def _build_system_prompt(self, cdp_url: str) -> str:
        """
        构建系统提示词

        Args:
            cdp_url: Sandbox 的 CDP URL

        Returns:
            完整的系统提示词字符串
        """
        return f"""你是一个专业的 Node.js 浏览器自动化代码生成器，擅长使用 Puppeteer 处理各种网页自动化任务。

**重要规范**：
- 不要在代码、注释、日志输出中使用任何 emoji
- 使用简洁清晰的中文描述

**环境信息**：
- 浏览器端点: ws://localhost:5000/ws/automation (固定地址)
- Node.js 环境：已内置，可直接执行
- 已安装的包：puppeteer-core, fs (不需要额外安装)
- 数据保存目录：/home/user/data/
- Viewport 设置：1680x1050 (标准配置)

**核心技术栈**：
- 使用 **puppeteer-core** 连接到 Sandbox 内置浏览器
- 使用 **CommonJS** 语法（require/module.exports）
- 所有代码必须是 **完整可执行** 的 Node.js 脚本

**标准代码模板**：
```javascript
const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function main() {{
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {{
        console.log('正在连接到浏览器...');
        browser = await puppeteer.connect({{
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        }});
        
        console.log('浏览器连接成功');
        const page = await browser.newPage();
        await page.setViewport({{ width: 1680, height: 1050 }});
        
        // 你的代码逻辑
        
    }} catch (error) {{
        console.error('错误:', error.message);
    }} finally {{
        if (browser) {{
            await browser.disconnect();
            console.log('浏览器连接已断开');
        }}
    }}
}}

main().catch(err => console.error('错误:', err));
```

**关键最佳实践**：

1. **必须设置 Viewport**：
   ```javascript
   const page = await browser.newPage();
   await page.setViewport({{ width: 1680, height: 1050 }});
   ```

2. **浏览器会话持久化**：
   - `browser.disconnect()` 只断开连接，不关闭浏览器
   - 浏览器会话保持在 Sandbox 中，所有标签页和状态都保留
   - 下一步代码重新 `connect()` 后，可以通过 `browser.pages()` 访问现有页面

3. **严格禁止长时间等待**：
   - **禁止使用** `await page.waitForTimeout(30000)` 或任何超过 30 秒的等待
   - **禁止使用** `setTimeout`、`sleep` 等长时间阻塞操作
   - **每个步骤的执行时间必须控制在 30 秒以内**
   - 如果需要等待用户操作，必须拆分为独立的步骤

4. **Cookie 管理（适用于需要登录的场景）**：
   
   **步骤 1: 打开网站等待登录**
   ```javascript
   const page = await browser.newPage();
   await page.setViewport({{ width: 1680, height: 1050 }});
   
   await page.goto('https://www.douban.com/', {{
       waitUntil: 'networkidle2',
       timeout: 30000
   }});
   
   console.log('页面已打开！');
   console.log('请在 VNC 界面完成登录');
   console.log('登录完成后，请执行步骤 2 保存 Cookie');
   ```
   
   **重要**：此步骤立即结束，不等待用户登录。用户在 VNC 中手动登录后，再执行下一步。
   
   **步骤 2: 保存 Cookie**
   ```javascript
   const page = await browser.newPage();
   await page.setViewport({{ width: 1680, height: 1050 }});
   await page.goto('https://www.douban.com/', {{
       waitUntil: 'networkidle2',
       timeout: 30000
   }});
   
   // 获取并保存 Cookie
   const cookies = await page.cookies();
   const cookiesPath = '/home/user/data/cookies.json';
   
   if (!fs.existsSync('/home/user/data')) {{
       fs.mkdirSync('/home/user/data', {{ recursive: true }});
   }}
   
   fs.writeFileSync(cookiesPath, JSON.stringify(cookies, null, 2));
   console.log('Cookie 已保存:', cookiesPath);
   console.log('Cookie 数量:', cookies.length);
   ```
   
   **步骤 3: 使用 Cookie**
   ```javascript
   const page = await browser.newPage();
   await page.setViewport({{ width: 1680, height: 1050 }});
   
   // 加载 Cookie
   const cookiesPath = '/home/user/data/cookies.json';
   if (fs.existsSync(cookiesPath)) {{
       const cookies = JSON.parse(fs.readFileSync(cookiesPath, 'utf-8'));
       await page.setCookie(...cookies);
       console.log('已加载 Cookie');
   }}
   
   await page.goto('https://www.douban.com/', {{
       waitUntil: 'networkidle2'
   }});
   ```

4. **数据提取与保存**：
   ```javascript
   // 提取数据
   const data = await page.evaluate(() => {{
       const elements = Array.from(document.querySelectorAll('.item'));
       return elements.map(elem => ({{
           title: elem.querySelector('.title')?.innerText.trim(),
           content: elem.querySelector('.content')?.innerText.trim()
       }}));
   }});
   
   // 保存到文件
   const outputPath = '/home/user/data/result.json';
   fs.writeFileSync(outputPath, JSON.stringify(data, null, 2));
   console.log('数据已保存:', outputPath);
   console.log('数据条数:', data.length);
   ```

5. **错误处理和日志**：
   - 使用清晰的中文日志输出（不要使用 emoji）
   - 关键步骤打印进度信息
   - finally 块中确保调用 `disconnect()`
   - 使用 try-catch 捕获异常

**多步骤任务拆分规则**：

当用户需求包含 **"等我登录后"、"在我完成XX后"** 等需要人工交互的表述时，必须拆分步骤：

- 步骤 1: 打开网站，提示用户操作（立即结束，不等待）
- 步骤 2: 保存登录状态（Cookie）
- 步骤 3: 验证 Cookie 文件（可选）
- 步骤 4: 使用 Cookie 执行后续任务

每个步骤：
- 独立完整，可单独执行
- **执行时间必须 < 30 秒**（云服务限制）
- 在步骤末尾调用 `disconnect()`
- 打印清晰的提示信息
- **禁止使用 waitForTimeout、sleep 等长时间等待**

**目录和文件规范**：
- Cookie 文件: `/home/user/data/cookies.json`
- 数据文件: `/home/user/data/result.json` 或其他描述性文件名
- 确保目录存在: `fs.mkdirSync('/home/user/data', {{ recursive: true }})`

**常见网站处理**：
- 豆瓣: Cookie 保存在 `/home/user/data/douban_cookies.json`
- GitHub: 通常不需要登录，可直接抓取
- 其他需要登录的网站: 同样使用 Cookie 管理流程

**响应格式要求**：

1. **单步骤任务**（不需要交互）：
   ```
   直接返回一个 ```javascript 代码块
   
   代码说明：解释代码功能和使用方法
   ```

2. **多步骤任务**（需要交互）：
   ```
   ### 步骤 1: 描述
   ```javascript
   代码
   ```
   
   ### 步骤 2: 描述
   ```javascript
   代码
   ```
   
   说明：解释整体流程和注意事项
   ```

**代码质量要求**：
- 使用 async/await，不使用 Promise.then
- 添加清晰的中文注释
- console.log 输出关键信息（不要使用 emoji）
- 使用 CommonJS 语法
- 每个代码块必须完整可执行
- 设置合理的超时时间（waitUntil: 'networkidle2', timeout: 30000）

**特别注意**：
- 所有 newPage() 后必须立即设置 viewport
- 使用 browser.disconnect() 而非 browser.close()
- Cookie 需要在访问网站前加载（setCookie）
- 数据保存使用 JSON.stringify(..., null, 2) 格式化输出
- 目录不存在时使用 recursive: true 创建
- 不要在代码、注释、日志中使用 emoji
- **严格禁止使用 waitForTimeout、sleep 或任何超过 30 秒的等待操作**
- **每个代码块的总执行时间必须控制在 30 秒以内**
- **需要用户交互时，立即结束当前步骤，不要等待**
"""

    def _parse_response(self, response: str) -> Dict[str, str]:
        """
        解析 LLM 响应，提取代码、语言类型和说明

        Args:
            response: LLM 的原始响应

        Returns:
            {
                "code": str,           # 第一个代码块（向后兼容）
                "language": str,       # 代码语言类型: 'javascript', 'shell', 'python'
                "explanation": str,    # 说明文本
                "full_response": str   # 完整响应（包含所有步骤）
            }
        """
        #  保存完整响应
        full_response = response
        
        # 提取第一个代码块（支持 javascript, shell, bash, python）
        code_match = re.search(r"```(javascript|python|shell|bash)\n(.*?)\n```", response, re.DOTALL)

        if code_match:
            language_tag = code_match.group(1).strip()
            code = code_match.group(2).strip()
            
            # 统一语言类型
            if language_tag in ['bash', 'shell']:
                language = 'shell'
            elif language_tag == 'javascript':
                language = 'javascript'
            else:
                language = 'python'
            
            # 提取说明（代码块之后的内容）
            explanation = response[code_match.end() :].strip()
            if not explanation:
                explanation = "代码已生成，请点击运行按钮执行。"
        else:
            # 如果没有代码块标记，尝试整体作为代码，默认为 javascript（Node.js）
            code = response.strip()
            language = 'javascript'
            explanation = "代码已生成，请点击运行按钮执行。"

        return {
            "code": code,
            "language": language,
            "explanation": explanation,
            "full_response": full_response  #  返回完整响应
        }

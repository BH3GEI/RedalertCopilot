"""
简化的LLM客户端 - 只支持OpenAI，无模拟模式
"""
import json
from openai import OpenAI
from typing import Dict, Any

class LLMClient:
    def __init__(self, api_key: str):
        """初始化OpenAI客户端"""
        self.client = OpenAI(api_key=api_key)
        
        # 模型配置
        self.models = {
            "strategic": "gpt-4o",           # 战略AI用大模型
            "tactical": "gpt-4o-mini",       # 战术AI用快模型
            "reactive": "gpt-4o-mini",       # 快速响应用快模型
            "cache": "gpt-4o-mini"           # 缓存维护用快模型
        }
    
    def chat_completion(self, prompt: str, agent_type: str = "tactical") -> Dict[str, Any]:
        """调用OpenAI API"""
        model = self.models.get(agent_type, "gpt-4o-mini")
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000 if agent_type == "strategic" else 500
            )
            
            content = response.choices[0].message.content
            
            # 尝试解析JSON响应
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # 如果不是JSON，提取JSON部分
                import re
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                else:
                    raise ValueError(f"LLM返回非JSON格式: {content}")
            
        except Exception as e:
            raise Exception(f"OpenAI API调用失败: {e}")
"""
战略AI Agent - 大模型，10秒周期，负责长期规划
"""
import time
import json
import sys
import os
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.state_manager import GlobalStateManager
from shared.logger import ai_logger

class StrategicAgent:
    def __init__(self, state_manager: GlobalStateManager, llm_client):
        self.state_manager = state_manager
        self.llm_client = llm_client
        self.last_update = 0
        self.update_interval = 10  # 10秒更新一次
    
    def should_update(self) -> bool:
        """判断是否需要更新"""
        return time.time() - self.last_update >= self.update_interval
    
    def run_cycle(self):
        """运行一个战略决策周期"""
        if not self.should_update():
            return
        
        ai_logger.log_strategic("开始战略分析...")
        
        # 读取完整状态
        full_state = self.state_manager.read_full_state()
        
        # 构建战略AI prompt
        strategic_prompt = self._build_strategic_prompt(full_state)
        
        # 调用大模型
        response = self._call_llm(strategic_prompt)
        
        # 解析响应并更新状态
        if response:
            self._process_strategic_decision(response)
            self.last_update = time.time()
            ai_logger.log_decision("strategic", response)
            print("[状态] [战略AI] 战略规划已更新")  # 只有这条显示到控制台
    
    def _build_strategic_prompt(self, state: Dict[str, Any]) -> str:
        """构建战略AI的prompt"""
        prompt = f"""你是OpenRA游戏的最高战略指挥官。

### 输入数据:
完整游戏状态: {json.dumps(state, ensure_ascii=False, indent=2)}

### 任务:
基于完整战场信息和用户目标，制定长期战略规划。

### 输出格式 (必须是有效JSON):
```json
{{
  "strategic_update": {{
    "current_phase": "early_rush|mid_game|late_game",
    "build_priority": ["兵营", "步兵", "火箭兵"],
    "resource_allocation": {{"military": 70, "economy": 20, "defense": 10}},
    "next_milestone": "完成双兵营建设", 
    "estimated_timeline": "3分钟内",
    "enemy_analysis": "敌人行为分析",
    "strategy_adjustment": "战略调整说明"
  }},
  "long_term_actions": [
    {{"action": "expand_to_north_resources", "priority": 3, "timeline": "5分钟后"}},
    {{"action": "tech_rush_advanced_units", "priority": 4, "timeline": "8分钟后"}}
  ]
}}
```

只输出JSON，不要其他文字。"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """调用大模型"""
        try:
            if self.llm_client:
                return self.llm_client.chat_completion(prompt, "strategic")
            else:
                raise Exception("LLM客户端未初始化")
            
        except Exception as e:
            ai_logger.log_strategic(f"LLM调用失败: {e}", "error")
            return None
    
    def _process_strategic_decision(self, response: Dict[str, Any]):
        """处理战略决策并更新状态"""
        try:
            # 更新战略计划
            strategic_update = response.get("strategic_update", {})
            self.state_manager.update_strategic(strategic_update)
            
            # 记录长期行动到历史
            long_term_actions = response.get("long_term_actions", [])
            full_state = self.state_manager.read_full_state()
            action_history = full_state.get("action_history", [])
            
            for action in long_term_actions:
                action_history.append({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "agent": "strategic",
                    "action": action["action"],
                    "priority": action["priority"],
                    "timeline": action["timeline"]
                })
            
            # 更新历史记录 - 直接覆盖而不是update
            full_state = self.state_manager.read_full_state()
            full_state["action_history"] = action_history
            self.state_manager._write_state(full_state)
            
        except Exception as e:
            ai_logger.log_strategic(f"处理决策失败: {e}", "error")

if __name__ == "__main__":
    # 测试代码
    state_manager = GlobalStateManager("/tmp/game_state.json")
    strategic_agent = StrategicAgent(state_manager, None)
    
    # 模拟运行
    strategic_agent.run_cycle()
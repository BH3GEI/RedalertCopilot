"""
战术AI Agent - 中模型，2-3秒周期，负责具体战术执行
"""
import time
import json
import sys
import os
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.state_manager import GlobalStateManager
from shared.logger import ai_logger

class TacticalAgent:
    def __init__(self, state_manager: GlobalStateManager, llm_client):
        self.state_manager = state_manager
        self.llm_client = llm_client
        self.last_update = 0
        self.update_interval = 2.5  # 2.5秒更新一次
    
    def should_update(self) -> bool:
        """判断是否需要更新"""
        return time.time() - self.last_update >= self.update_interval
    
    def run_cycle(self):
        """运行一个战术决策周期"""
        if not self.should_update():
            return
        
        ai_logger.log_tactical("开始战术规划...")
        
        # 读取完整状态
        full_state = self.state_manager.read_full_state()
        
        # 构建战术AI prompt
        tactical_prompt = self._build_tactical_prompt(full_state)
        
        # 调用中等模型
        response = self._call_llm(tactical_prompt)
        
        # 解析响应并更新状态
        if response:
            self._process_tactical_decision(response)
            self.last_update = time.time()
            ai_logger.log_decision("tactical", response)
            print("[战术] [战术AI] 战术部署已更新")  # 控制台只显示这条
    
    def _build_tactical_prompt(self, state: Dict[str, Any]) -> str:
        """构建战术AI的prompt"""
        
        # 提取战略约束
        strategic_plan = state.get("strategic_plan", {})
        battlefield = state.get("battlefield_state", {})
        
        prompt = f"""你是OpenRA游戏的战术指挥官，负责具体战术执行。

### 战略约束:
当前阶段: {strategic_plan.get("current_phase", "未知")}
建造优先级: {strategic_plan.get("build_priority", [])}
资源分配: {strategic_plan.get("resource_allocation", {})}
战略目标: {strategic_plan.get("next_milestone", "")}

### 当前战场状态:
{json.dumps(battlefield, ensure_ascii=False, indent=2)}

### 生产队列:
{json.dumps(state.get("production_queues", {}), ensure_ascii=False, indent=2)}

### 任务:
基于战略规划，制定具体的战术行动序列。所有行动必须符合战略约束。

### 输出格式 (必须是有效JSON):
```json
{{
  "tactical_actions": [
    {{"action": "select_unit", "params": {{"type": "步兵", "faction": "己方"}}, "priority": 2}},
    {{"action": "move_actor", "params": {{"direction": "北", "distance": 5}}, "priority": 2}},
    {{"action": "start_production", "params": {{"units": [{{"unit_type": "火箭兵", "quantity": 2}}]}}, "priority": 3}}
  ],
  "formation_updates": {{
    "group_1": {{"role": "attack_north", "target_area": [20,10]}},
    "group_2": {{"role": "defend_base", "target_area": [15,20]}}
  }},
  "production_adjustments": {{
    "prioritize_queues": ["Infantry"],
    "pause_queues": ["Aircraft"]
  }}
}}
```

只输出JSON，不要其他文字。"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """调用中等模型"""
        try:
            if self.llm_client:
                return self.llm_client.chat_completion(prompt, "tactical")
            else:
                raise Exception("LLM客户端未初始化")
            
        except Exception as e:
            ai_logger.log_tactical(f"LLM调用失败: {e}", "error")
            return None
    
    def _process_tactical_decision(self, response: Dict[str, Any]):
        """处理战术决策并更新状态"""
        try:
            # 更新战术状态
            tactical_update = {
                "current_focus": self._extract_tactical_focus(response),
                "active_formations": response.get("formation_updates", {}),
                "immediate_tasks": response.get("tactical_actions", []),
                "production_plan": response.get("production_adjustments", {})
            }
            
            self.state_manager.update_tactical(tactical_update)
            
            # 将战术行动加入历史记录
            self._log_tactical_actions(response.get("tactical_actions", []))
            
        except Exception as e:
            ai_logger.log_tactical(f"处理决策失败: {e}", "error")
    
    def _extract_tactical_focus(self, response: Dict[str, Any]) -> str:
        """从响应中提取当前战术重点"""
        actions = response.get("tactical_actions", [])
        if not actions:
            return "待命"
        
        # 分析主要行动类型
        action_types = [action.get("action", "") for action in actions]
        
        if "move_actor" in action_types:
            return "部队调动"
        elif "attack" in action_types:
            return "进攻作战"
        elif "start_production" in action_types:
            return "扩充生产"
        else:
            return "综合部署"
    
    def _log_tactical_actions(self, actions: List[Dict[str, Any]]):
        """记录战术行动到历史"""
        full_state = self.state_manager.read_full_state()
        action_history = full_state.get("action_history", [])
        
        for action in actions:
            action_history.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agent": "tactical",
                "action": action.get("action", ""),
                "priority": action.get("priority", 2),
                "params": action.get("params", {})
            })
        
        # 保留最近50条记录
        if len(action_history) > 50:
            action_history = action_history[-50:]
        
        self.state_manager._update_section("action_history", action_history, "tactical")

if __name__ == "__main__":
    # 测试代码
    state_manager = GlobalStateManager("/tmp/game_state.json")
    tactical_agent = TacticalAgent(state_manager, None)
    
    # 模拟运行
    tactical_agent.run_cycle()
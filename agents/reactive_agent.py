"""
快速响应AI Agent - 小模型，0.5-1秒响应，处理紧急威胁
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

class ReactiveAgent:
    def __init__(self, state_manager: GlobalStateManager, llm_client):
        self.state_manager = state_manager
        self.llm_client = llm_client
        self.last_update = 0
        self.update_interval = 0.8  # 0.8秒检查一次
    
    def should_update(self) -> bool:
        """判断是否需要更新"""
        return time.time() - self.last_update >= self.update_interval
    
    def run_cycle(self):
        """运行一个快速响应周期"""
        if not self.should_update():
            return
        
        ai_logger.log_reactive("扫描威胁...")
        
        # 只读取威胁相关信息
        threat_data = self.state_manager.read_threats_only()
        
        # 检查是否有紧急威胁
        if not self._has_urgent_threats(threat_data):
            self.last_update = time.time()
            return
        
        ai_logger.log_reactive("发现威胁，启动应急响应...")
        
        # 构建快速响应prompt
        reactive_prompt = self._build_reactive_prompt(threat_data)
        
        # 调用小模型
        response = self._call_llm(reactive_prompt)
        
        # 处理紧急响应
        if response:
            self._process_reactive_decision(response)
            self.last_update = time.time()
            ai_logger.log_decision("reactive", response)
            print("[快速] [快速响应AI] 紧急指令已发出")  # 控制台显示
    
    def _has_urgent_threats(self, threat_data: Dict[str, Any]) -> bool:
        """检查是否存在紧急威胁"""
        threats = threat_data.get("immediate_threats", [])
        return len(threats) > 0
    
    def _build_reactive_prompt(self, threat_data: Dict[str, Any]) -> str:
        """构建快速响应AI的prompt - 精简版"""
        prompt = f"""你是应急响应指挥官，只处理紧急威胁。

### 当前威胁:
{json.dumps(threat_data.get("immediate_threats", []), ensure_ascii=False)}

### 脆弱单位:
{json.dumps(threat_data.get("vulnerable_assets", []), ensure_ascii=False)}

### 战略背景:
目标: {threat_data.get("current_objective", "")}
当前阶段: {threat_data.get("strategic_context", "")}

### 任务:
立即输出紧急行动，优先级必须为1。

### 可用行动:
- move_actor: 移动单位
- attack: 攻击目标  
- select_unit: 选择单位
- stop: 停止行动

### 输出格式 (必须是有效JSON):
```json
{{
  "emergency_actions": [
    {{"action": "move_actor", "params": {{"targets": {{"type": "步兵"}}, "direction": "西", "distance": 5}}, "priority": 1, "reason": "躲避坦克攻击"}}
  ]
}}
```

只输出JSON，不要其他文字。"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """调用小模型 - 追求速度"""
        try:
            if self.llm_client:
                return self.llm_client.chat_completion(prompt, "reactive")
            else:
                raise Exception("LLM客户端未初始化")
            
        except Exception as e:
            ai_logger.log_reactive(f"LLM调用失败: {e}", "error")
            return None
    
    def _process_reactive_decision(self, response: Dict[str, Any]):
        """处理紧急响应并更新状态"""
        try:
            emergency_actions = response.get("emergency_actions", [])
            
            if emergency_actions:
                # 更新紧急状态
                reactive_update = {
                    "last_threat_response": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "emergency_actions": emergency_actions,
                    "threat_level": "active"
                }
                
                self.state_manager.update_reactive(reactive_update)
                
                # 记录紧急行动
                self._log_emergency_actions(emergency_actions)
                
                ai_logger.log_reactive(f"执行了 {len(emergency_actions)} 个紧急行动")
            
        except Exception as e:
            ai_logger.log_reactive(f"处理决策失败: {e}", "error")
    
    def _log_emergency_actions(self, actions: List[Dict[str, Any]]):
        """记录紧急行动到历史"""
        full_state = self.state_manager.read_full_state()
        action_history = full_state.get("action_history", [])
        
        for action in actions:
            action_history.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "agent": "reactive",
                "action": action.get("action", ""),
                "priority": action.get("priority", 1),
                "reason": action.get("reason", "紧急响应"),
                "params": action.get("params", {})
            })
        
        self.state_manager._update_section("action_history", action_history, "reactive")
    
    def force_check_threats(self):
        """强制检查威胁 - 给其他agent调用"""
        threat_data = self.state_manager.read_threats_only()
        if self._has_urgent_threats(threat_data):
            print("[警告] [快速响应AI] 强制威胁检查 - 发现威胁!")
            self.run_cycle()

if __name__ == "__main__":
    # 测试代码
    state_manager = GlobalStateManager("/tmp/game_state.json")
    reactive_agent = ReactiveAgent(state_manager, None)
    
    # 模拟运行
    reactive_agent.run_cycle()
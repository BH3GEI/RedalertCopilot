"""
缓存维护AI Agent - 根据战场情况维护战略缓存，学习优化决策模式
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

class CacheMaintenanceAgent:
    def __init__(self, state_manager: GlobalStateManager, llm_client):
        self.state_manager = state_manager
        self.llm_client = llm_client
        self.last_update = 0
        self.update_interval = 15  # 15秒分析一次，或战斗结束后触发
    
    def should_update(self) -> bool:
        """判断是否需要更新缓存"""
        return time.time() - self.last_update >= self.update_interval
    
    def run_cycle(self):
        """运行缓存维护周期"""
        if not self.should_update():
            return
        
        ai_logger.log_cache("开始分析决策效果...")
        
        # 读取缓存相关数据
        cache_data = self.state_manager.read_cache_data()
        
        # 构建缓存维护prompt
        cache_prompt = self._build_cache_prompt(cache_data)
        
        # 调用AI分析
        response = self._call_llm(cache_prompt)
        
        # 更新缓存
        if response:
            self._process_cache_update(response)
            self.last_update = time.time()
            ai_logger.log_decision("cache", response)
            print("[AI] [缓存AI] 决策缓存已优化")  # 控制台显示
    
    def trigger_battle_analysis(self):
        """战斗结束后触发缓存分析"""
        print("[缓存] [缓存AI] 战斗结束，开始分析...")
        self.run_cycle()
    
    def _build_cache_prompt(self, cache_data: Dict[str, Any]) -> str:
        """构建缓存维护AI的prompt"""
        
        current_situation = cache_data.get("current_situation", {})
        recent_actions = cache_data.get("recent_actions", [])
        existing_cache = cache_data.get("existing_cache", {})
        
        prompt = f"""你是决策缓存维护系统，负责学习和优化决策模式。

### 当前战况模式:
{json.dumps(current_situation, ensure_ascii=False, indent=2)}

### 近期行动效果:
{json.dumps(recent_actions[-10:], ensure_ascii=False, indent=2)}

### 现有决策缓存:
{json.dumps(existing_cache, ensure_ascii=False, indent=2)}

### 任务:
基于实战效果分析，更新和优化决策缓存。识别成功/失败的决策模式。

### 输出格式 (必须是有效JSON):
```json
{{
  "cache_updates": {{
    "new_patterns": {{
      "enemy_tank_rush_early": {{
        "triggers": ["敌坦克数量>2", "游戏时间<5分钟"],
        "recommended_response": "mass_infantry_retreat_and_rocket_production",
        "confidence": 0.85,
        "success_rate": 0.9
      }}
    }},
    "pattern_adjustments": {{
      "infantry_vs_tank": {{
        "old_confidence": 0.7,
        "new_confidence": 0.9,
        "adjustment_reason": "连续3次成功应对坦克威胁"
      }}
    }},
    "deprecated_patterns": [
      "outdated_pattern_name"
    ]
  }},
  "performance_analysis": {{
    "successful_strategies": [
      {{"pattern": "early_infantry_rush", "success_rate": 0.8, "sample_size": 5}}
    ],
    "failed_strategies": [
      {{"pattern": "late_game_air_rush", "success_rate": 0.2, "issues": "资源不足"}}
    ]
  }}
}}
```

只输出JSON，不要其他文字。"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """调用AI进行缓存分析"""
        try:
            if self.llm_client:
                return self.llm_client.chat_completion(prompt, "cache")
            else:
                raise Exception("LLM客户端未初始化")
            
        except Exception as e:
            ai_logger.log_cache(f"LLM调用失败: {e}", "error")
            return None
    
    def _process_cache_update(self, response: Dict[str, Any]):
        """处理缓存更新"""
        try:
            cache_updates = response.get("cache_updates", {})
            
            # 读取现有缓存
            full_state = self.state_manager.read_full_state()
            current_cache = full_state.get("decision_cache", {})
            
            # 添加新模式
            new_patterns = cache_updates.get("new_patterns", {})
            if "strategic_patterns" not in current_cache:
                current_cache["strategic_patterns"] = {}
            current_cache["strategic_patterns"].update(new_patterns)
            
            # 调整现有模式
            adjustments = cache_updates.get("pattern_adjustments", {})
            for pattern_name, adjustment in adjustments.items():
                if pattern_name in current_cache["strategic_patterns"]:
                    current_cache["strategic_patterns"][pattern_name]["confidence"] = adjustment["new_confidence"]
            
            # 删除废弃模式
            deprecated = cache_updates.get("deprecated_patterns", [])
            for pattern_name in deprecated:
                current_cache["strategic_patterns"].pop(pattern_name, None)
            
            # 添加性能分析
            current_cache["performance_analysis"] = response.get("performance_analysis", {})
            current_cache["last_analysis"] = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 更新缓存
            self.state_manager.update_cache(current_cache)
            
        except Exception as e:
            print(f"[缓存维护AI] 处理更新失败: {e}")
    
    def get_cached_response(self, situation_pattern: str) -> Dict[str, Any]:
        """根据情况模式获取缓存的响应"""
        full_state = self.state_manager.read_full_state()
        cache = full_state.get("decision_cache", {})
        patterns = cache.get("strategic_patterns", {})
        
        if situation_pattern in patterns:
            pattern_data = patterns[situation_pattern]
            if pattern_data.get("confidence", 0) > 0.7:  # 置信度阈值
                return {
                    "cached_response": pattern_data.get("recommended_response"),
                    "confidence": pattern_data.get("confidence"),
                    "hit": True
                }
        
        return {"hit": False}
    
    def analyze_current_pattern(self, battlefield_state: Dict[str, Any]) -> str:
        """分析当前战场模式"""
        # 简化的模式识别逻辑
        my_units = battlefield_state.get("my_forces", {}).get("units", {})
        enemy_units = battlefield_state.get("enemy_intel", {}).get("units", {})
        
        infantry_count = my_units.get("步兵", {}).get("count", 0)
        enemy_tank_count = enemy_units.get("坦克", {}).get("count", 0)
        
        if enemy_tank_count >= 2 and infantry_count > 3:
            return "enemy_tank_vs_my_infantry"
        elif infantry_count >= 5:
            return "infantry_mass"
        else:
            return "mixed_forces"

if __name__ == "__main__":
    # 测试代码
    state_manager = GlobalStateManager("/tmp/game_state.json")
    cache_agent = CacheMaintenanceAgent(state_manager, None)
    
    # 模拟运行
    cache_agent.run_cycle()
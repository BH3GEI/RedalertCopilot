"""
全局状态管理器 - 处理JSON读写和并发控制
"""
import json
import threading
import time
from typing import Dict, Any
from pathlib import Path

class GlobalStateManager:
    def __init__(self, state_file_path: str):
        self.state_file = Path(state_file_path)
        self.lock = threading.RLock()
        self._init_state_file()
    
    def _init_state_file(self):
        """初始化状态文件"""
        if not self.state_file.exists():
            initial_state = {
                "meta": {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "game_time": 0,
                    "last_strategic_update": None,
                    "last_tactical_update": None,
                    "last_reactive_update": None,
                    "last_cache_update": None
                },
                "user_config": {},
                "battlefield_state": {},
                "strategic_plan": {},
                "tactical_status": {},
                "reactive_alerts": {},
                "decision_cache": {},
                "production_queues": {},
                "action_history": []
            }
            self._write_state(initial_state)
    
    def read_full_state(self) -> Dict[str, Any]:
        """读取完整状态 - 给大模型用"""
        with self.lock:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def read_threats_only(self) -> Dict[str, Any]:
        """只读取威胁信息 - 给快速响应AI用"""
        full_state = self.read_full_state()
        return {
            "immediate_threats": full_state.get("reactive_alerts", {}).get("immediate_threats", []),
            "vulnerable_assets": self._extract_vulnerable_units(full_state),
            "current_objective": full_state.get("user_config", {}).get("main_goal", ""),
            "strategic_context": full_state.get("strategic_plan", {}).get("current_phase", "")
        }
    
    def read_cache_data(self) -> Dict[str, Any]:
        """读取缓存相关数据 - 给缓存维护AI用"""
        full_state = self.read_full_state()
        return {
            "current_situation": self._analyze_current_pattern(full_state),
            "recent_actions": full_state.get("action_history", [])[-10:],  # 最近10个行动
            "existing_cache": full_state.get("decision_cache", {})
        }
    
    def update_strategic(self, strategic_data: Dict[str, Any]):
        """战略AI更新战略层"""
        self._update_section("strategic_plan", strategic_data, "strategic")
    
    def update_tactical(self, tactical_data: Dict[str, Any]):
        """战术AI更新战术层"""
        self._update_section("tactical_status", tactical_data, "tactical")
    
    def update_reactive(self, reactive_data: Dict[str, Any]):
        """快速响应AI更新应急层"""
        self._update_section("reactive_alerts", reactive_data, "reactive")
    
    def update_cache(self, cache_data: Dict[str, Any]):
        """缓存维护AI更新缓存层"""
        self._update_section("decision_cache", cache_data, "cache")
    
    def update_battlefield(self, battlefield_data: Dict[str, Any]):
        """战场信息层更新战场状态"""
        self._update_section("battlefield_state", battlefield_data, "battlefield")
    
    def _update_section(self, section: str, data: Dict[str, Any], agent_type: str):
        """线程安全的分区更新"""
        with self.lock:
            full_state = self.read_full_state()
            full_state[section].update(data)
            
            # 更新时间戳
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            full_state["meta"]["timestamp"] = timestamp
            full_state["meta"][f"last_{agent_type}_update"] = timestamp
            
            self._write_state(full_state)
    
    def _write_state(self, state: Dict[str, Any]):
        """写入状态文件"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def _extract_vulnerable_units(self, state: Dict[str, Any]) -> list:
        """提取脆弱单位信息"""
        vulnerable = []
        my_units = state.get("battlefield_state", {}).get("my_forces", {}).get("units", {})
        
        for unit_type, data in my_units.items():
            if data.get("avg_hp", 100) < 50:  # 血量低于50%
                vulnerable.append({
                    "type": unit_type,
                    "count": data.get("count", 0),
                    "positions": data.get("positions", []),
                    "hp": data.get("avg_hp", 0)
                })
        return vulnerable
    
    def _analyze_current_pattern(self, state: Dict[str, Any]) -> Dict[str, str]:
        """分析当前战场模式"""
        battlefield = state.get("battlefield_state", {})
        my_forces = battlefield.get("my_forces", {})
        enemy_intel = battlefield.get("enemy_intel", {})
        
        return {
            "battlefield_pattern": self._get_force_comparison(my_forces, enemy_intel),
            "resource_state": self._get_resource_level(battlefield.get("resources", {})),
            "map_control": self._get_control_status(battlefield.get("map_control", {})),
            "game_phase": state.get("strategic_plan", {}).get("current_phase", "unknown")
        }
    
    def _get_force_comparison(self, my_forces: dict, enemy_intel: dict) -> str:
        """分析兵力对比模式"""
        # 简化的模式识别
        my_tank_count = my_forces.get("units", {}).get("坦克", {}).get("count", 0)
        enemy_tank_count = enemy_intel.get("units", {}).get("坦克", {}).get("count", 0)
        
        if enemy_tank_count > my_tank_count:
            return "enemy_tank_advantage"
        elif my_tank_count > enemy_tank_count:
            return "my_tank_advantage"
        else:
            return "equal_forces"
    
    def _get_resource_level(self, resources: dict) -> str:
        """分析资源状况"""
        cash = resources.get("cash", 0)
        if cash > 3000:
            return "abundant"
        elif cash > 1500:
            return "moderate"
        else:
            return "scarce"
    
    def _get_control_status(self, map_control: dict) -> str:
        """分析地图控制"""
        controlled = len(map_control.get("controlled_areas", []))
        enemy_areas = len(map_control.get("enemy_areas", []))
        
        if controlled > enemy_areas:
            return "advantage"
        elif controlled < enemy_areas:
            return "disadvantage"
        else:
            return "equal"
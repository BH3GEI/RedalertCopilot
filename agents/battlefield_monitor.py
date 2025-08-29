"""
战场信息层 - 自动读取API并压缩更新状态
"""
import time
import json
import threading
import sys
import os
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.state_manager import GlobalStateManager
from shared.api_queue import OpenRAAPIQueue

class BattlefieldMonitor:
    def __init__(self, state_manager: GlobalStateManager, api_queue: OpenRAAPIQueue):
        self.state_manager = state_manager
        self.api_queue = api_queue
        self.running = False
        self.update_interval = 2  # 每2秒更新战场信息
        self.last_update = 0
        
        # 信息压缩配置
        self.max_unit_history = 5  # 最多保存5个历史位置
        self.max_enemy_intel = 10  # 最多保存10个敌方单位信息
    
    def start(self):
        """启动战场监控"""
        self.running = True
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        print("[监控] [战场监控] 已启动")
    
    def stop(self):
        """停止战场监控"""
        self.running = False
        print("[停止] [战场监控] 已停止")
    
    def _monitor_loop(self):
        """监控主循环"""
        while self.running:
            try:
                if time.time() - self.last_update >= self.update_interval:
                    self._update_battlefield_state()
                    self.last_update = time.time()
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"[战场监控] 监控循环异常: {e}")
                time.sleep(2)
    
    def _update_battlefield_state(self):
        """更新战场状态"""
        print("[扫描] [战场监控] 收集战场信息...")
        
        # 收集各种战场信息
        self._query_base_resources()
        self._query_screen_units()
        self._query_production_status()
        self._analyze_threats()
    
    def _query_base_resources(self):
        """查询基地资源信息"""
        def handle_base_info(response):
            if response and response.get("status") == 1:
                data = response.get("data", {})
                
                resource_update = {
                    "cash": data.get("Cash", 0),
                    "resources": data.get("Resources", 0), 
                    "power": data.get("Power", 0),
                    "power_consumed": data.get("PowerDrained", 0),
                    "power_total": data.get("PowerProvided", 0),
                    "last_resource_update": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 更新资源状态
                full_state = self.state_manager.read_full_state()
                battlefield = full_state.get("battlefield_state", {})
                battlefield["resources"] = resource_update
                
                self.state_manager.update_battlefield({"resources": resource_update})
                print(f"[资源] [资源更新] 金钱: {data.get('Cash', 0)}, 电力: {data.get('Power', 0)}")
        
        # 通过API队列查询
        self.api_queue.add_command("player_baseinfo_query", {}, priority=3, callback=handle_base_info)
    
    def _query_screen_units(self):
        """查询屏幕内单位"""
        def handle_screen_units(response):
            if response and response.get("status") == 1:
                # 模拟查询我方单位
                my_units_query = {
                    "targets": {"faction": "己方", "range": "screen"}
                }
                
                def handle_my_units(unit_response):
                    if unit_response and unit_response.get("status") == 1:
                        actors = unit_response.get("data", {}).get("actors", [])
                        self._process_unit_data(actors, "my_forces")
                
                self.api_queue.add_command("query_actor", my_units_query, priority=3, callback=handle_my_units)
                
                # 模拟查询敌方单位  
                enemy_units_query = {
                    "targets": {"faction": "敌方", "range": "screen"}
                }
                
                def handle_enemy_units(enemy_response):
                    if enemy_response and enemy_response.get("status") == 1:
                        actors = enemy_response.get("data", {}).get("actors", [])
                        self._process_unit_data(actors, "enemy_intel")
                
                self.api_queue.add_command("query_actor", enemy_units_query, priority=3, callback=handle_enemy_units)
        
        # 先查询屏幕信息
        self.api_queue.add_command("screen_info_query", {}, priority=3, callback=handle_screen_units)
    
    def _process_unit_data(self, actors: List[Dict], faction_type: str):
        """处理单位数据并压缩存储"""
        if not actors:
            return
        
        # 按单位类型分组统计
        unit_summary = {}
        for actor in actors:
            unit_type = actor.get("type", "unknown")
            if unit_type not in unit_summary:
                unit_summary[unit_type] = {
                    "count": 0,
                    "positions": [],
                    "total_hp": 0,
                    "max_hp": 0
                }
            
            summary = unit_summary[unit_type]
            summary["count"] += 1
            summary["positions"].append([actor.get("position", {}).get("x", 0), 
                                       actor.get("position", {}).get("y", 0)])
            summary["total_hp"] += actor.get("hp", 0)
            summary["max_hp"] += actor.get("maxHp", 0)
        
        # 计算平均血量，压缩位置信息
        for unit_type, data in unit_summary.items():
            if data["count"] > 0:
                data["avg_hp"] = int(data["total_hp"] / data["count"])
                data["hp_percentage"] = int((data["total_hp"] / data["max_hp"]) * 100) if data["max_hp"] > 0 else 100
                
                # 位置信息压缩：只保存代表性位置
                positions = data["positions"]
                if len(positions) > self.max_unit_history:
                    # 保存最前、最后和中间位置
                    compressed_pos = [
                        positions[0],  # 第一个
                        positions[len(positions)//2],  # 中间
                        positions[-1]  # 最后一个
                    ]
                    data["positions"] = compressed_pos
                
                # 清理临时计算字段
                data.pop("total_hp", None)
                data.pop("max_hp", None)
        
        # 更新到全局状态
        battlefield_update = {}
        if faction_type == "my_forces":
            battlefield_update = {"my_forces": {"units": unit_summary}}
        elif faction_type == "enemy_intel":
            battlefield_update = {"enemy_intel": {"units": unit_summary}}
        
        self.state_manager.update_battlefield(battlefield_update)
        print(f"[更新] [单位更新] {faction_type}: {len(unit_summary)} 种单位类型")
    
    def _query_production_status(self):
        """查询生产状态"""
        queue_types = ["Building", "Infantry", "Vehicle", "Defense", "Aircraft"]
        
        def handle_production_query(queue_type):
            def callback(response):
                if response and response.get("status") == 1:
                    queue_data = response.get("data", {})
                    
                    # 压缩生产队列信息
                    compressed_queue = {
                        "queue_type": queue_data.get("queue_type"),
                        "total_items": len(queue_data.get("queue_items", [])),
                        "has_ready": queue_data.get("has_ready_item", False),
                        "active_items": []
                    }
                    
                    # 只保存重要的生产项目
                    for item in queue_data.get("queue_items", []):
                        if item.get("status") in ["in_progress", "completed"]:
                            compressed_queue["active_items"].append({
                                "name": item.get("chineseName", ""),
                                "progress": item.get("progress_percent", 0),
                                "remaining_time": item.get("remaining_time", 0),
                                "status": item.get("status")
                            })
                    
                    # 更新生产队列状态
                    full_state = self.state_manager.read_full_state()
                    production_queues = full_state.get("production_queues", {})
                    production_queues[queue_type] = compressed_queue
                    
                    self.state_manager._update_section("production_queues", production_queues, "battlefield")
            
            return callback
        
        # 查询各个生产队列
        for queue_type in queue_types:
            params = {"queueType": queue_type}
            self.api_queue.add_command("query_production_queue", params, priority=3, 
                                     callback=handle_production_query(queue_type))
    
    def _analyze_threats(self):
        """分析当前威胁"""
        # 从当前状态分析威胁
        full_state = self.state_manager.read_full_state()
        enemy_units = full_state.get("battlefield_state", {}).get("enemy_intel", {}).get("units", {})
        my_units = full_state.get("battlefield_state", {}).get("my_forces", {}).get("units", {})
        
        threats = []
        opportunities = []
        
        # 威胁分析
        for enemy_type, enemy_data in enemy_units.items():
            enemy_count = enemy_data.get("count", 0)
            if enemy_count == 0:
                continue
                
            threat_level = self._calculate_threat_level(enemy_type, enemy_count, my_units)
            if threat_level == "high":
                for pos in enemy_data.get("positions", []):
                    threats.append({
                        "type": f"敌方{enemy_type}",
                        "location": pos,
                        "count": enemy_count,
                        "severity": threat_level,
                        "detected_time": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        # 机会分析
        my_total_units = sum(data.get("count", 0) for data in my_units.values())
        enemy_total_units = sum(data.get("count", 0) for data in enemy_units.values())
        
        if my_total_units > enemy_total_units * 1.5:
            opportunities.append({
                "type": "兵力优势",
                "description": f"我方{my_total_units}vs敌方{enemy_total_units}",
                "window": 60  # 机会窗口60秒
            })
        
        # 更新威胁状态
        reactive_update = {
            "immediate_threats": threats,
            "opportunities": opportunities,
            "last_threat_scan": time.strftime("%Y-%m-%d %H:%M:%S"),
            "threat_level": "high" if threats else "safe"
        }
        
        self.state_manager.update_reactive(reactive_update)
        
        if threats:
            print(f"[警告] [威胁检测] 发现 {len(threats)} 个威胁")
        if opportunities:
            print(f"[快速] [机会检测] 发现 {len(opportunities)} 个机会")
    
    def _calculate_threat_level(self, enemy_type: str, enemy_count: int, my_units: Dict) -> str:
        """计算威胁级别"""
        # 简化的威胁评估
        if enemy_type == "坦克" and enemy_count >= 2:
            my_rockets = my_units.get("火箭兵", {}).get("count", 0) 
            my_tanks = my_units.get("坦克", {}).get("count", 0)
            if my_rockets + my_tanks < enemy_count:
                return "high"
        
        elif enemy_type == "步兵" and enemy_count >= 5:
            my_infantry = my_units.get("步兵", {}).get("count", 0)
            if my_infantry < enemy_count * 0.8:
                return "medium"
        
        return "low"
    
    def force_update(self):
        """强制立即更新战场信息"""
        print("[更新] [战场监控] 强制更新...")
        self._update_battlefield_state()

if __name__ == "__main__":
    # 测试代码
    state_manager = GlobalStateManager("/tmp/game_state.json")
    api_queue = OpenRAAPIQueue()
    
    monitor = BattlefieldMonitor(state_manager, api_queue)
    monitor.start()
    
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        monitor.stop()
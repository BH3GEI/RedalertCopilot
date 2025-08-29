"""
API队列管理 - 统一调度OpenRA Socket API调用，避免并发冲突
"""
import asyncio
import json
import socket
import threading
import time
import sys
import os
from typing import Dict, Any, List, Optional
from queue import Queue, PriorityQueue

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.logger import ai_logger

class OpenRAAPIQueue:
    def __init__(self, host: str = "localhost", port: int = 7445):
        self.host = host
        self.port = port
        self.socket = None
        self.command_queue = PriorityQueue()  # 优先级队列
        self.running = False
        self.worker_thread = None
        self.response_callbacks = {}  # 存储响应回调
        
    def start(self):
        """启动API队列处理"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        ai_logger.log_api("已启动")
    
    def stop(self):
        """停止API队列处理"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
        self._close_connection()
        ai_logger.log_api("已停止")
    
    def _connect_to_openra(self) -> bool:
        """连接到OpenRA"""
        try:
            if self.socket:
                self.socket.close()
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.socket.settimeout(5.0)  # 5秒超时
            ai_logger.log_api(f"已连接到OpenRA {self.host}:{self.port}")
            return True
            
        except Exception as e:
            ai_logger.log_api(f"连接失败: {e}", "error")
            self.socket = None
            return False
    
    def _close_connection(self):
        """关闭连接"""
        if self.socket:
            self.socket.close()
            self.socket = None
    
    def add_command(self, command: str, params: Dict[str, Any], priority: int = 2, 
                   callback=None, request_id: str = None):
        """添加命令到队列"""
        if request_id is None:
            request_id = f"{command}_{int(time.time() * 1000)}"
        
        api_request = {
            "apiVersion": "1.0",
            "requestId": request_id,
            "command": command,
            "params": params,
            "language": "zh"
        }
        
        # 优先级越小越优先执行 (1=紧急, 2=普通, 3=低优先级)
        queue_item = (priority, time.time(), api_request, callback)
        self.command_queue.put(queue_item)
        
        if callback:
            self.response_callbacks[request_id] = callback
        
        ai_logger.log_api(f"命令已入队: {command} (优先级: {priority})")
        return request_id
    
    def _process_queue(self):
        """处理命令队列 - 在独立线程中运行"""
        while self.running:
            try:
                # 获取队列中的命令 (阻塞等待)
                if self.command_queue.empty():
                    time.sleep(0.1)
                    continue
                
                priority, timestamp, api_request, callback = self.command_queue.get(timeout=1)
                
                # 执行API调用
                response = self._execute_api_call(api_request)
                
                # 处理响应
                if callback and response:
                    try:
                        callback(response)
                    except Exception as e:
                        ai_logger.log_api(f"回调执行失败: {e}", "error")
                
                # 清理回调
                request_id = api_request.get("requestId")
                self.response_callbacks.pop(request_id, None)
                
                # 避免API调用过于频繁
                time.sleep(0.1)
                
            except Exception as e:
                ai_logger.log_api(f"处理队列失败: {e}", "error")
                time.sleep(1)
    
    def _execute_api_call(self, api_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """执行单个API调用 - 目前只打印日志，不实际调用"""
        try:
            command = api_request.get("command", "unknown")
            params = api_request.get("params", {})
            request_id = api_request.get("requestId", "")
            
            # 只打印日志，不实际连接OpenRA
            ai_logger.log_api(f"模拟执行: {command}")
            ai_logger.log_api(f"参数: {json.dumps(params, ensure_ascii=False)}")
            ai_logger.log_api(f"请求ID: {request_id}")
            
            # 模拟成功响应
            mock_response = {
                "status": 1,
                "requestId": request_id,
                "response": f"模拟执行{command}成功",
                "data": self._generate_mock_data(command, params)
            }
            
            ai_logger.log_api(f"模拟响应: 成功")
            return mock_response
            
        except Exception as e:
            ai_logger.log_api(f"模拟调用异常: {e}", "error")
            return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "queue_size": self.command_queue.qsize(),
            "connected": self.socket is not None,
            "running": self.running,
            "pending_callbacks": len(self.response_callbacks)
        }
    
    # 便捷方法 - 各个agent可以直接调用
    def move_units(self, targets: Dict, direction: str = None, location: Dict = None, 
                  is_attack_move: bool = False, priority: int = 2):
        """移动单位"""
        params = {"targets": targets}
        if direction:
            params["direction"] = direction
            params["distance"] = 5  # 默认距离
        if location:
            params["location"] = location
        if is_attack_move:
            params["isAttackMove"] = 1
        
        return self.add_command("move_actor", params, priority)
    
    def attack_targets(self, attackers: Dict, targets: Dict, priority: int = 2):
        """攻击目标"""
        params = {"attackers": attackers, "targets": targets}
        return self.add_command("attack", params, priority)
    
    def start_production(self, units: List[Dict], auto_place: bool = False, priority: int = 2):
        """开始生产"""
        params = {"units": units, "autoPlaceBuilding": auto_place}
        return self.add_command("start_production", params, priority)
    
    def query_battlefield_info(self, callback=None):
        """查询战场信息"""
        # 批量查询多个信息
        self.add_command("player_baseinfo_query", {}, 3, callback)
        self.add_command("screen_info_query", {}, 3, callback)
        self.add_command("map_query", {}, 3, callback)
    
    def _generate_mock_data(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """生成模拟响应数据"""
        if command == "player_baseinfo_query":
            return {
                "Cash": 3000,
                "Resources": 120, 
                "Power": 25,
                "PowerDrained": 15,
                "PowerProvided": 40
            }
        elif command == "query_actor":
            return {
                "actors": [
                    {
                        "id": 101,
                        "type": "步兵",
                        "faction": params.get("targets", {}).get("faction", "己方"),
                        "hp": 100,
                        "maxHp": 100,
                        "position": {"x": 20, "y": 25}
                    }
                ]
            }
        elif command == "query_production_queue":
            return {
                "queue_type": params.get("queueType", "Infantry"),
                "queue_items": [],
                "has_ready_item": False
            }
        else:
            return {}

if __name__ == "__main__":
    # 测试代码
    api_queue = OpenRAAPIQueue()
    api_queue.start()
    
    # 模拟添加命令
    api_queue.move_units(
        targets={"type": "步兵", "faction": "己方"},
        direction="东",
        priority=1
    )
    
    time.sleep(2)
    api_queue.stop()
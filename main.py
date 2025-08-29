"""
分层AI系统主程序 - 协调四个AI agent运行
"""
import time
import threading
import signal
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from shared.state_manager import GlobalStateManager
from shared.api_queue import OpenRAAPIQueue
from shared.logger import ai_logger
from agents.strategic_agent import StrategicAgent
from agents.tactical_agent import TacticalAgent
from agents.reactive_agent import ReactiveAgent
from agents.cache_agent import CacheMaintenanceAgent
from agents.user_input_agent import UserInputAgent
from agents.battlefield_monitor import BattlefieldMonitor
from shared.llm_client import LLMClient

class LayeredAISystem:
    def __init__(self, state_file_path: str = "./config/game_state.json", openai_api_key: str = None):
        # 初始化状态管理和API队列
        self.state_manager = GlobalStateManager(state_file_path)
        self.api_queue = OpenRAAPIQueue()
        
        # 初始化LLM客户端
        if not openai_api_key:
            raise ValueError("必须提供OpenAI API key")
        
        self.llm_client = LLMClient(openai_api_key)
        
        # 初始化AI agents
        self.strategic_agent = StrategicAgent(self.state_manager, self.llm_client)
        self.tactical_agent = TacticalAgent(self.state_manager, self.llm_client) 
        self.reactive_agent = ReactiveAgent(self.state_manager, self.llm_client)
        self.cache_agent = CacheMaintenanceAgent(self.state_manager, self.llm_client)
        self.user_input_agent = UserInputAgent(self.state_manager, self.llm_client)
        self.battlefield_monitor = BattlefieldMonitor(self.state_manager, self.api_queue)
        
        # 运行状态
        self.running = False
        self.threads = []
    
    def start(self):
        """启动分层AI系统"""
        print("[启动] OpenRA 分层AI系统")
        print("[AI] AI提供商: OpenAI")
        print("[提示] 输入指令控制AI，输入 'help' 查看命令")  
        print("[日志] 详细日志保存在 ./logs/ 目录")
        print("=" * 50)
        
        self.running = True
        self.api_queue.start()
        
        # 启动各个AI agent线程  
        agents = [
            ("战略AI", self.strategic_agent),
            ("战术AI", self.tactical_agent), 
            ("快速响应AI", self.reactive_agent),
            ("缓存维护AI", self.cache_agent)
        ]
        
        for name, agent in agents:
            thread = threading.Thread(target=self._run_agent, args=(name, agent), daemon=True)
            thread.start()
            self.threads.append(thread)
        
        # 启动战场信息监控
        self.battlefield_monitor.start()
        
        print("[完成] 所有AI系统已启动并运行")
        
        # 启动用户交互
        self.user_input_agent.start_chat_loop()
    
    def _run_agent(self, name: str, agent):
        """运行单个agent的循环"""
        while self.running:
            try:
                agent.run_cycle()
                time.sleep(0.2)  # 避免CPU占用过高
            except Exception as e:
                ai_logger.log_api(f"{name} 运行异常: {e}", "error")
                time.sleep(2)
    
    def stop(self):
        """停止系统"""
        print("\n[停止] 正在停止分层AI系统...")
        self.running = False
        
        # 等待线程结束
        for thread in self.threads:
            thread.join(timeout=2)
        
        self.api_queue.stop()
        print("[完成] 分层AI系统已停止")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统运行状态"""
        return {
            "running": self.running,
            "api_queue": self.api_queue.get_queue_status(),
            "agents_active": len([t for t in self.threads if t.is_alive()]),
            "state_file": str(self.state_manager.state_file),
            "last_updates": self.state_manager.read_full_state().get("meta", {})
        }

def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    print('\n收到停止信号...')
    if hasattr(signal_handler, 'system'):
        signal_handler.system.stop()
    sys.exit(0)

def main():
    """主函数"""
    # OpenAI API Key - 从环境变量读取
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("[错误] 请设置OPENAI_API_KEY环境变量")
        print("[提示] 运行: export OPENAI_API_KEY=your_api_key")
        return
    
    # 创建AI系统
    try:
        ai_system = LayeredAISystem("./config/game_state.json", openai_key)
    except ValueError as e:
        print(f"[错误] 系统初始化失败: {e}")
        return
    
    signal_handler.system = ai_system
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # 启动系统
        ai_system.start()
        
        # 主循环 - 监控系统状态
        while True:
            time.sleep(10)
            status = ai_system.get_system_status()
            print(f"[系统监控] 运行状态: {status}")
            
    except KeyboardInterrupt:
        ai_system.stop()
    except Exception as e:
        print(f"系统运行异常: {e}")
        ai_system.stop()

if __name__ == "__main__":
    main()
"""
用户输入层 - 陪聊Node，处理用户交互并更新全局目标
"""
import time
import json
import threading
import sys
import os
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.state_manager import GlobalStateManager

class UserInputAgent:
    def __init__(self, state_manager: GlobalStateManager, llm_client):
        self.state_manager = state_manager
        self.llm_client = llm_client
        self.chat_history = []
        self.running = False
        
    def start_chat_loop(self):
        """启动聊天循环"""
        self.running = True
        print("\n[聊天] 用户交互模式:")
        print("   [日志] 输入游戏指令 (如: '我要rush敌人')")
        print("   [状态] 输入 'status' 查看状态")
        print("   [命令] 输入 'help' 查看命令")  
        print("   [错误] 输入 'quit' 退出")
        print("\n")
        
        chat_thread = threading.Thread(target=self._chat_input_loop, daemon=True)
        chat_thread.start()
    
    def _chat_input_loop(self):
        """聊天输入循环"""
        while self.running:
            try:
                user_input = input("\n[用户] 你: ").strip()
                
                if user_input.lower() == 'quit':
                    self.running = False
                    break
                elif user_input.lower() == 'status':
                    self._show_current_status()
                elif user_input.lower() == 'help':
                    self._show_help()
                elif user_input.lower() == 'logs':
                    self._show_log_summary()
                elif user_input:
                    self._process_user_input(user_input)
                    
            except EOFError:
                break
            except Exception as e:
                print(f"[用户交互] 输入处理异常: {e}")
    
    def _process_user_input(self, user_input: str):
        """处理用户输入"""
        print(f"[AI] [AI陪聊] 收到指令: {user_input}")
        
        # 添加到聊天历史
        self.chat_history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "role": "user",
            "content": user_input
        })
        
        # 分析用户意图
        intent_analysis = self._analyze_user_intent(user_input)
        
        # 如果是游戏指令，更新全局目标
        if intent_analysis.get("is_game_command", False):
            self._update_game_goal(intent_analysis)
            
        # AI回应
        ai_response = self._generate_ai_response(user_input, intent_analysis)
        print(f"[AI] [AI陪聊]: {ai_response}")
        
        # 记录AI回应
        self.chat_history.append({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "role": "assistant", 
            "content": ai_response
        })
    
    def _analyze_user_intent(self, user_input: str) -> Dict[str, Any]:
        """分析用户意图"""
        # 简化的意图识别
        game_keywords = ["rush", "攻击", "防御", "造", "建", "进攻", "撤退", "生产", "坦克", "步兵"]
        goal_keywords = ["目标", "想要", "希望", "计划", "策略"]
        
        is_game_command = any(keyword in user_input for keyword in game_keywords)
        is_goal_setting = any(keyword in user_input for keyword in goal_keywords)
        
        # 提取具体指令
        extracted_goal = None
        if "rush" in user_input or "快攻" in user_input:
            extracted_goal = "aggressive_rush"
        elif "防御" in user_input or "守" in user_input:
            extracted_goal = "defensive_strategy"
        elif "坦克" in user_input and ("造" in user_input or "出" in user_input):
            extracted_goal = "tank_production_focus"
        elif "步兵" in user_input and ("造" in user_input or "出" in user_input):
            extracted_goal = "infantry_production_focus"
        
        return {
            "is_game_command": is_game_command,
            "is_goal_setting": is_goal_setting,
            "extracted_goal": extracted_goal,
            "urgency": "high" if "立即" in user_input or "马上" in user_input else "normal"
        }
    
    def _update_game_goal(self, intent_analysis: Dict[str, Any]):
        """更新游戏目标"""
        extracted_goal = intent_analysis.get("extracted_goal")
        if not extracted_goal:
            return
            
        print(f"[目标] [目标更新] 检测到新目标: {extracted_goal}")
        
        # 根据目标类型更新用户配置
        goal_mappings = {
            "aggressive_rush": {
                "main_goal": "快速aggressive rush敌人",
                "preferred_style": "aggressive_infantry_rush",
                "custom_instructions": "优先快速出兵，忽略防御"
            },
            "defensive_strategy": {
                "main_goal": "稳健发展，重点防御",
                "preferred_style": "defensive_buildup", 
                "custom_instructions": "优先建造防御设施，稳步发展经济"
            },
            "tank_production_focus": {
                "main_goal": "重点发展坦克部队",
                "preferred_style": "tank_heavy_strategy",
                "custom_instructions": "优先建造战车工厂，大量生产坦克"
            },
            "infantry_production_focus": {
                "main_goal": "步兵海战术",
                "preferred_style": "infantry_mass",
                "custom_instructions": "多建兵营，大量生产步兵单位"
            }
        }
        
        new_config = goal_mappings.get(extracted_goal, {})
        if new_config:
            # 更新用户配置
            full_state = self.state_manager.read_full_state()
            user_config = full_state.get("user_config", {})
            user_config.update(new_config)
            
            self.state_manager._update_section("user_config", user_config, "user")
            print(f"[完成] [目标更新] 已更新为: {new_config['main_goal']}")
    
    def _generate_ai_response(self, user_input: str, intent_analysis: Dict[str, Any]) -> str:
        """生成AI回应"""
        if intent_analysis.get("is_game_command"):
            if intent_analysis.get("extracted_goal"):
                return f"明白！我已经更新目标为 {intent_analysis['extracted_goal']}，AI正在调整战略..."
            else:
                return "收到指令！AI正在分析并执行..."
        else:
            # 普通聊天
            responses = [
                "正在专心指挥作战中...",
                "嗯嗯，我在看战场情况",
                "AI们正在协调作战计划",
                "现在情况如何？需要调整策略吗？"
            ]
            return responses[len(self.chat_history) % len(responses)]
    
    def _show_current_status(self):
        """显示当前游戏状态"""
        try:
            full_state = self.state_manager.read_full_state()
            
            print("\n[状态] 当前游戏状态:")
            print(f"[目标] 目标: {full_state.get('user_config', {}).get('main_goal', '未设置')}")
            
            strategic = full_state.get("strategic_plan", {})
            print(f"[地图]  战略阶段: {strategic.get('current_phase', '未知')}")
            print(f"[建造]  建造重点: {strategic.get('build_priority', [])}")
            
            resources = full_state.get("battlefield_state", {}).get("resources", {})
            print(f"[资源] 资源: 金钱={resources.get('cash', 0)}, 电力={resources.get('power', 0)}")
            
            threats = full_state.get("reactive_alerts", {}).get("immediate_threats", [])
            print(f"[警告]  威胁: {len(threats)} 个紧急威胁")
            
            meta = full_state.get("meta", {})
            print(f"[时间] 最后更新: {meta.get('timestamp', '未知')}")
            
        except Exception as e:
            print(f"状态查询失败: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        print("\n[命令] 可用命令:")
        print("   [目标] 游戏指令示例:")
        print("      - '我要rush敌人' / '快速进攻'")
        print("      - '采用防御策略' / '稳扎稳打'") 
        print("      - '重点造坦克' / '大量出步兵'")
        print("   [状态] 系统命令:")
        print("      - 'status' : 查看当前游戏状态")
        print("      - 'logs'   : 查看AI运行日志统计")
        print("      - 'help'   : 显示此帮助信息")  
        print("      - 'quit'   : 退出系统")
    
    def _show_log_summary(self):
        """显示日志统计"""
        try:
            from shared.logger import ai_logger
            log_summary = ai_logger.get_log_summary()
            
            print("\n[日志] AI日志统计:")
            for component, line_count in log_summary.items():
                print(f"   {component}: {line_count} 条日志")
            
            print(f"\n[存储] 日志文件位置: ./logs/")
            
        except Exception as e:
            print(f"日志统计失败: {e}")
    
    def inject_test_goal(self, goal_type: str):
        """注入测试目标 - 用于调试"""
        test_inputs = {
            "rush": "我想要快速rush敌人！",
            "defense": "采用防御策略，稳扎稳打",
            "tank": "重点造坦克，用重装部队碾压",
            "infantry": "步兵海战术，人多力量大"
        }
        
        if goal_type in test_inputs:
            print(f"\n[测试] [测试] 注入目标: {goal_type}")
            self._process_user_input(test_inputs[goal_type])

if __name__ == "__main__":
    # 测试代码
    state_manager = GlobalStateManager("/tmp/game_state.json") 
    user_agent = UserInputAgent(state_manager, None)
    
    # 测试目标注入
    user_agent.inject_test_goal("rush")
    user_agent.inject_test_goal("tank")
    
    # 启动聊天
    user_agent.start_chat_loop()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        user_agent.running = False
"""
日志系统 - 将AI运行日志写入文件，保持控制台清洁
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any

class AILogger:
    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建各个组件的日志器
        self.loggers = {}
        self._setup_loggers()
    
    def _setup_loggers(self):
        """设置各组件日志器"""
        components = [
            "strategic_ai",
            "tactical_ai", 
            "reactive_ai",
            "cache_ai",
            "battlefield_monitor",
            "api_queue",
            "state_manager"
        ]
        
        for component in components:
            logger = logging.getLogger(component)
            logger.setLevel(logging.INFO)
            
            # 文件处理器
            log_file = os.path.join(self.log_dir, f"{component}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            
            # 日志格式
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            self.loggers[component] = logger
    
    def log_strategic(self, message: str, level: str = "info"):
        """战略AI日志"""
        self._log("strategic_ai", message, level)
    
    def log_tactical(self, message: str, level: str = "info"):
        """战术AI日志"""
        self._log("tactical_ai", message, level)
    
    def log_reactive(self, message: str, level: str = "info"):
        """快速响应AI日志"""
        self._log("reactive_ai", message, level)
    
    def log_cache(self, message: str, level: str = "info"):
        """缓存维护AI日志"""
        self._log("cache_ai", message, level)
    
    def log_battlefield(self, message: str, level: str = "info"):
        """战场监控日志"""
        self._log("battlefield_monitor", message, level)
    
    def log_api(self, message: str, level: str = "info"):
        """API队列日志"""
        self._log("api_queue", message, level)
    
    def log_state(self, message: str, level: str = "info"):
        """状态管理器日志"""
        self._log("state_manager", message, level)
    
    def _log(self, component: str, message: str, level: str = "info"):
        """统一日志记录"""
        logger = self.loggers.get(component)
        if logger:
            if level == "error":
                logger.error(message)
            elif level == "warning":
                logger.warning(message)
            else:
                logger.info(message)
    
    def log_decision(self, agent_type: str, decision_data: Dict[str, Any]):
        """记录AI决策 - 特殊格式"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if agent_type == "strategic":
            phase = decision_data.get("strategic_update", {}).get("current_phase", "unknown")
            milestone = decision_data.get("strategic_update", {}).get("next_milestone", "")
            self.log_strategic(f"战略更新 - 阶段: {phase}, 目标: {milestone}")
            
        elif agent_type == "tactical":
            actions = decision_data.get("tactical_actions", [])
            focus = decision_data.get("current_focus", "")
            self.log_tactical(f"战术部署 - 重点: {focus}, 行动数: {len(actions)}")
            
        elif agent_type == "reactive":
            emergency_actions = decision_data.get("emergency_actions", [])
            if emergency_actions:
                action_types = [a.get("action", "") for a in emergency_actions]
                self.log_reactive(f"紧急响应 - 行动: {', '.join(action_types)}")
            
        elif agent_type == "cache":
            new_patterns = len(decision_data.get("cache_updates", {}).get("new_patterns", {}))
            adjustments = len(decision_data.get("cache_updates", {}).get("pattern_adjustments", {}))
            self.log_cache(f"缓存更新 - 新模式: {new_patterns}, 调整: {adjustments}")
    
    def get_log_summary(self) -> Dict[str, int]:
        """获取日志统计"""
        summary = {}
        for component in self.loggers.keys():
            log_file = os.path.join(self.log_dir, f"{component}.log")
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                summary[component] = len(lines)
            else:
                summary[component] = 0
        return summary

# 全局日志实例
ai_logger = AILogger()
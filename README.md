# 分层AI系统 - OpenRA自动游戏架构

## 🎯 系统架构

本系统实现了无需人类干预的OpenRA自动游戏AI，采用分层决策架构解决大模型推理延迟问题。

### 四个AI Agent:

1. **战略AI** (`strategic_agent.py`) 
   - 大模型，10秒周期
   - 负责长期战略规划
   - 修改 `strategic_plan` 部分

2. **战术AI** (`tactical_agent.py`)
   - 中模型，2-3秒周期  
   - 负责具体战术执行
   - 修改 `tactical_status` 部分

3. **快速响应AI** (`reactive_agent.py`)
   - 小模型，0.5-1秒响应
   - 处理紧急威胁
   - 修改 `reactive_alerts` 部分

4. **缓存维护AI** (`cache_agent.py`)
   - 分析战斗效果，优化决策模式
   - 修改 `decision_cache` 部分

### 核心组件:

- **状态管理器** (`state_manager.py`): 线程安全的JSON读写
- **API队列** (`api_queue.py`): 统一调度OpenRA socket连接
- **全局状态**: 所有AI共享的游戏状态JSON

## 🚀 快速开始

### 1. 启动系统
```bash
cd /Users/liyao/Code/mofa/Hackathon2025/examples/mofa/layered-ai-system
python main.py
```

### 2. 配置LLM客户端
在各个agent文件中替换 `llm_client = None` 为实际的LLM客户端。

### 3. 启动OpenRA游戏
确保OpenRA在端口7445监听socket连接。

## 🎮 工作流程

1. **初始化**: 加载 `initial_state.json` 作为起始状态
2. **并行运行**: 四个AI按各自周期独立运行
3. **状态同步**: 通过全局JSON文件协调信息
4. **API调度**: 所有游戏操作通过队列统一执行
5. **学习优化**: 缓存AI持续优化决策模式

## 🔧 关键特性

- **分层决策**: 解决大模型推理延迟问题
- **线程安全**: 多个AI并发访问状态文件
- **优先级队列**: 紧急指令优先执行  
- **决策缓存**: 常见情况快速响应
- **自我学习**: 根据战斗效果优化策略

## 📝 配置文件

- `config/initial_state.json`: 初始游戏状态
- `game_state.json`: 运行时状态文件 (自动生成)

## 🛠 开发说明

每个AI agent都可以:
- 读取完整/部分状态信息
- 修改自己负责的状态区域  
- 通过API队列执行游戏操作
- 记录行动历史用于学习

## ⚠️ 注意事项

1. 需要配置实际的LLM客户端
2. 确保OpenRA游戏正在运行并监听7445端口
3. 各个AI的prompt可能需要根据实际模型调优
4. 建议先在测试环境验证再用于实际对战
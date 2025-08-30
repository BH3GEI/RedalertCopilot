import ray
import time
import json
import traceback
import inspect
from typing import Dict, List, Any, Callable, Optional
from ray.util.queue import Queue
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === 任务执行器 ===
class TaskExecutor:
    def __init__(self):
        self.functions = {}

    def register_function(self, name: str, func: Callable):
        """注册可执行的函数"""
        self.functions[name] = func
        logger.info(f"注册函数: {name}")

    def register_functions_from_module(self, module):
        """从模块批量注册函数"""
        if hasattr(module, 'get_all_tool_functions'):
            functions = module.get_all_tool_functions()
            for name, func in functions.items():
                self.register_function(name, func)
        else:
            # 手动获取模块中的函数
            for name, obj in inspect.getmembers(module):
                if (inspect.isfunction(obj) and
                        not name.startswith('_')):
                    self.register_function(name, obj)

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        try:
            func_name = task.get('func_name')
            args = task.get('args', [])
            kwargs = task.get('kwargs', {})
            task_id = task.get('task_id', 'unknown')

            if func_name not in self.functions:
                raise ValueError(f"未知函数: {func_name}")

            func = self.functions[func_name]

            # 执行函数
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            return {
                'task_id': task_id,
                'func_name': func_name,
                'status': 'success',
                'result': result,
                'execution_time': execution_time,
                'timestamp': time.time()
            }

        except Exception as e:
            return {
                'task_id': task.get('task_id', 'unknown'),
                'func_name': task.get('func_name', 'unknown'),
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': time.time()
            }


# === 生产者Actor ===
@ray.remote
class Producer:
    def __init__(self, producer_id: str, task_queue: Queue):
        self.producer_id = producer_id
        self.task_queue = task_queue
        self.task_counter = 0
        logger.info(f"生产者 {producer_id} 初始化完成")

    def submit_task(self, func_name: str, args: List = None, kwargs: Dict = None) -> str:
        """提交单个任务"""
        self.task_counter += 1
        task_id = f"{self.producer_id}_task_{self.task_counter}"

        task = {
            'task_id': task_id,
            'func_name': func_name,
            'args': args or [],
            'kwargs': kwargs or {},
            'producer_id': self.producer_id,
            'created_at': time.time()
        }

        self.task_queue.put(task)
        logger.info(f"生产者 {self.producer_id} 提交任务: {task_id} ({func_name})")
        return task_id

    def submit_batch_tasks(self, tasks: List[Dict]) -> List[str]:
        """批量提交任务"""
        task_ids = []
        for task_info in tasks:
            task_id = self.submit_task(
                func_name=task_info['func_name'],
                args=task_info.get('args', []),
                kwargs=task_info.get('kwargs', {})
            )
            task_ids.append(task_id)

        logger.info(f"生产者 {self.producer_id} 批量提交 {len(task_ids)} 个任务")
        return task_ids


# === 消费者Actor ===
@ray.remote
class Consumer:
    def __init__(self, consumer_id: str, task_queue: Queue, result_queue: Queue):
        self.consumer_id = consumer_id
        self.task_queue = task_queue
        self.result_queue = result_queue  # 确保result_queue不为None
        self.executor = TaskExecutor()
        self.processed_count = 0
        self.is_running = False
        logger.info(f"消费者 {consumer_id} 初始化完成")

    def register_functions_from_module(self, module):
        """从模块注册函数"""
        self.executor.register_functions_from_module(module)

    def start_consuming(self, timeout: float = 1.0):
        """开始消费任务"""
        self.is_running = True
        logger.info(f"消费者 {self.consumer_id} 开始工作")

        while self.is_running:
            try:
                # 从队列获取任务
                task = self.task_queue.get(timeout=timeout)

                # 执行任务
                result = self.executor.execute_task(task)
                self.processed_count += 1

                # 记录结果
                if result['status'] == 'success':
                    logger.info(f"✅ 消费者 {self.consumer_id} 完成任务 {result['task_id']}: {result['func_name']}")
                else:
                    logger.error(f"❌ 消费者 {self.consumer_id} 任务失败 {result['task_id']}: {result['error']}")

                # 将结果放入结果队列
                try:
                    result['consumer_id'] = self.consumer_id
                    self.result_queue.put(result, timeout=5.0)  # 增加超时时间
                    logger.info(f"📤 消费者 {self.consumer_id} 结果已放入队列: {result['task_id']}")
                except Exception as e:
                    logger.error(f"❌ 消费者 {self.consumer_id} 放入结果失败: {e}")

            except Exception as e:
                if "timeout" not in str(e).lower() and "empty" not in str(e).lower():
                    logger.error(f"消费者 {self.consumer_id} 处理任务时出错: {e}")
                # 超时是正常的，继续循环
                continue

    def stop_consuming(self):
        """停止消费"""
        self.is_running = False
        logger.info(f"消费者 {self.consumer_id} 停止工作，共处理 {self.processed_count} 个任务")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'consumer_id': self.consumer_id,
            'processed_count': self.processed_count,
            'is_running': self.is_running
        }


# === 任务队列管理器 ===
@ray.remote
class GameTaskQueueManager:
    def __init__(self, max_queue_size: int = 1000):
        # 创建任务队列和结果队列
        self.task_queue = Queue(maxsize=max_queue_size)
        self.result_queue = Queue(maxsize=max_queue_size)

        self.producers = {}
        self.consumers = {}
        self.consumer_futures = {}

        logger.info(f"游戏任务队列管理器初始化完成，队列大小: {max_queue_size}")

    def create_producers(self, count: int) -> List[str]:
        """创建生产者"""
        producer_ids = []
        for i in range(count):
            producer_id = f"producer_{i + 1}"
            producer = Producer.remote(producer_id, self.task_queue)
            self.producers[producer_id] = producer
            producer_ids.append(producer_id)

        logger.info(f"创建了 {count} 个生产者")
        return producer_ids

    def create_consumers(self, count: int, game_functions_module=None) -> List[str]:
        """创建消费者并注册游戏函数"""
        consumer_ids = []
        for i in range(count):
            consumer_id = f"consumer_{i + 1}"
            # 确保result_queue被正确传递
            consumer = Consumer.remote(consumer_id, self.task_queue, self.result_queue)

            # 注册游戏函数
            if game_functions_module:
                ray.get(consumer.register_functions_from_module.remote(game_functions_module))

            self.consumers[consumer_id] = consumer
            consumer_ids.append(consumer_id)

        logger.info(f"创建了 {count} 个消费者")
        return consumer_ids

    def start_consumers(self):
        """启动所有消费者"""
        for consumer_id, consumer in self.consumers.items():
            # 非阻塞启动消费者
            future = consumer.start_consuming.remote()
            self.consumer_futures[consumer_id] = future

        logger.info(f"启动了 {len(self.consumers)} 个消费者")

    def stop_consumers(self):
        """停止所有消费者"""
        for consumer in self.consumers.values():
            ray.get(consumer.stop_consuming.remote())

        logger.info("所有消费者已停止")

    def get_producer(self, producer_id: str):
        """获取生产者"""
        return self.producers.get(producer_id)

    def get_queue_stats(self) -> Dict:
        """获取队列统计"""
        return {
            'task_queue_size': self.task_queue.qsize(),
            'result_queue_size': self.result_queue.qsize(),
            'producers_count': len(self.producers),
            'consumers_count': len(self.consumers)
        }

    def get_results(self, count: int = 10, timeout: float = 0.5) -> List[Dict]:
        """获取处理结果"""
        results = []
        for i in range(count):
            try:
                result = self.result_queue.get(timeout=timeout)
                results.append(result)
            except Exception as e:
                if "timeout" in str(e).lower() or "empty" in str(e).lower():
                    break  # 队列空了，停止获取
                else:
                    logger.error(f"获取结果时出错: {e}")
                    break

        return results

    def wait_for_results(self, expected_count: int, max_wait_time: float = 10.0) -> List[Dict]:
        """等待指定数量的结果"""
        results = []
        start_time = time.time()

        while len(results) < expected_count and (time.time() - start_time) < max_wait_time:
            try:
                result = self.result_queue.get(timeout=1.0)
                results.append(result)
                logger.info(f"📥 收到结果: {result['task_id']} ({len(results)}/{expected_count})")
            except Exception as e:
                if "timeout" not in str(e).lower() and "empty" not in str(e).lower():
                    logger.error(f"等待结果时出错: {e}")

        return results

import ray
import time
from ray_task_queue import GameTaskQueueManager
import tools


def game_build_test():
    """游戏建造和生产测试"""
    print("🎮 游戏建造和生产测试")

    # 初始化
    ray.init(ignore_reinit_error=True)
    manager = GameTaskQueueManager.remote()

    # 创建1个生产者，3个消费者（可以并行处理一些任务）
    ray.get(manager.create_producers.remote(1))
    ray.get(manager.create_consumers.remote(3, tools))
    ray.get(manager.start_consumers.remote())

    producer = ray.get(manager.get_producer.remote("producer_1"))

    # === 第一阶段：基础建设 ===
    print("\n=== 第一阶段：展开基地车并检查游戏状态 ===")
    phase1_tasks = [
        {'func_name': 'get_game_state'},
        {'func_name': 'deploy_mcv_and_wait', 'kwargs': {'wait_time': 3.0}},
        {'func_name': 'player_base_info_query'},
    ]

    task_ids = ray.get(producer.submit_batch_tasks.remote(phase1_tasks))
    print(f"提交了 {len(task_ids)} 个基础任务")

    # 等待第一阶段完成
    results = ray.get(manager.wait_for_results.remote(len(phase1_tasks), max_wait_time=15.0))
    print(f"第一阶段完成，获取到 {len(results)} 个结果:")
    for result in results:
        if result['status'] == 'success':
            if result['func_name'] == 'get_game_state' or result['func_name'] == 'player_base_info_query':
                # 显示游戏状态信息
                result_str = str(result['result'])
                if len(result_str) > 150:
                    result_str = result_str[:150] + "..."
                print(f"✅ {result['func_name']}: {result_str}")
            else:
                print(f"✅ {result['func_name']}: {result['result']}")
        else:
            print(f"❌ {result['func_name']}: {result['error']}")

    time.sleep(2)  # 等待基地车展开完成

    # === 第二阶段：建造基础设施 ===
    print("\n=== 第二阶段：建造基础设施 ===")
    phase2_tasks = [
        {'func_name': 'ensure_can_build_wait', 'args': ['发电厂']},
        {'func_name': 'ensure_can_build_wait', 'args': ['兵营']},
        {'func_name': 'ensure_can_build_wait', 'args': ['矿石精炼厂']},
    ]

    task_ids = ray.get(producer.submit_batch_tasks.remote(phase2_tasks))
    print(f"提交了 {len(task_ids)} 个建造任务")

    results = ray.get(manager.wait_for_results.remote(len(phase2_tasks), max_wait_time=30.0))
    print(f"第二阶段完成，获取到 {len(results)} 个结果:")
    for result in results:
        if result['status'] == 'success':
            print(f"✅ {result['func_name']} ({result.get('args', [''])[0]}): 建造成功")
        else:
            print(f"❌ {result['func_name']} ({result.get('args', [''])[0]}): {result['error']}")

    time.sleep(3)  # 等待建筑建造

    # === 第三阶段：建造更多设施和生产单位 ===
    print("\n=== 第三阶段：建造高级设施和生产单位 ===")
    phase3_tasks = [
        {'func_name': 'ensure_can_build_wait', 'args': ['发电厂']},  # 再建一个电厂
        {'func_name': 'ensure_can_build_wait', 'args': ['战车工厂']},  # 坦克厂
        {'func_name': 'ensure_can_produce_unit', 'args': ['矿车']},  # 确保可以生产矿车
        {'func_name': 'produce', 'args': ['矿车', 2]},  # 生产2个矿车
    ]

    task_ids = ray.get(producer.submit_batch_tasks.remote(phase3_tasks))
    print(f"提交了 {len(task_ids)} 个高级任务")

    results = ray.get(manager.wait_for_results.remote(len(phase3_tasks), max_wait_time=40.0))
    print(f"第三阶段完成，获取到 {len(results)} 个结果:")
    for result in results:
        if result['status'] == 'success':
            if result['func_name'] == 'produce':
                print(f"✅ {result['func_name']}: 生产任务ID {result['result']}")
            else:
                args_str = result.get('args', [''])[0] if result.get('args') else ''
                print(f"✅ {result['func_name']} ({args_str}): 成功")
        else:
            args_str = result.get('args', [''])[0] if result.get('args') else ''
            print(f"❌ {result['func_name']} ({args_str}): {result['error']}")

    # === 第四阶段：检查最终状态 ===
    print("\n=== 第四阶段：检查最终游戏状态 ===")
    phase4_tasks = [
        {'func_name': 'player_base_info_query'},
        {'func_name': 'query_production_queue', 'args': ['Vehicle']},  # 查看载具生产队列
        {'func_name': 'visible_units', 'args': [['矿车'], '友军', 'all', []]},  # 查看矿车
    ]

    task_ids = ray.get(producer.submit_batch_tasks.remote(phase4_tasks))
    print(f"提交了 {len(task_ids)} 个状态检查任务")

    results = ray.get(manager.wait_for_results.remote(len(phase4_tasks), max_wait_time=20.0))
    print(f"最终状态检查完成，获取到 {len(results)} 个结果:")
    for result in results:
        if result['status'] == 'success':
            if result['func_name'] == 'visible_units':
                units = result['result']
                print(f"✅ 发现 {len(units)} 个矿车单位")
                for unit in units:
                    print(f"   - 矿车ID: {unit['actor_id']}, 位置: ({unit['position']['x']}, {unit['position']['y']})")
            else:
                result_str = str(result['result'])
                if len(result_str) > 200:
                    result_str = result_str[:200] + "..."
                print(f"✅ {result['func_name']}: {result_str}")
        else:
            print(f"❌ {result['func_name']}: {result['error']}")

    # 获取最终队列状态
    stats = ray.get(manager.get_queue_stats.remote())
    print(f"\n=== 测试总结 ===")
    print(f"队列状态: 任务队列={stats['task_queue_size']}, 结果队列={stats['result_queue_size']}")

    # 计算总体成功率
    total_tasks = len(phase1_tasks) + len(phase2_tasks) + len(phase3_tasks) + len(phase4_tasks)
    print(f"总任务数: {total_tasks}")
    print("✅ 游戏建造和生产测试完成")

    # 清理
    ray.get(manager.stop_consumers.remote())
    ray.shutdown()


def comprehensive_base_test():
    """全面的基地建设测试（可选的扩展测试）"""
    print("🏗️ 全面基地建设测试")

    ray.init(ignore_reinit_error=True)
    manager = GameTaskQueueManager.remote()

    ray.get(manager.create_producers.remote(2))  # 2个生产者
    ray.get(manager.create_consumers.remote(4, tools))  # 4个消费者
    ray.get(manager.start_consumers.remote())

    producer1 = ray.get(manager.get_producer.remote("producer_1"))
    producer2 = ray.get(manager.get_producer.remote("producer_2"))

    # 并行执行建造和生产任务
    build_tasks = [
        {'func_name': 'deploy_mcv_and_wait', 'kwargs': {'wait_time': 2.0}},
        {'func_name': 'ensure_can_build_wait', 'args': ['发电厂']},
        {'func_name': 'ensure_can_build_wait', 'args': ['兵营']},
        {'func_name': 'ensure_can_build_wait', 'args': ['矿石精炼厂']},
        {'func_name': 'ensure_can_build_wait', 'args': ['战车工厂']},
    ]

    production_tasks = [
        {'func_name': 'ensure_can_produce_unit', 'args': ['矿车']},
        {'func_name': 'produce', 'args': ['矿车', 2]},
        {'func_name': 'ensure_can_produce_unit', 'args': ['步兵']},
        {'func_name': 'produce', 'args': ['步兵', 3]},
    ]

    # 并行提交任务
    ray.get(producer1.submit_batch_tasks.remote(build_tasks))
    ray.get(producer2.submit_batch_tasks.remote(production_tasks))

    print(f"并行提交了 {len(build_tasks)} 个建造任务和 {len(production_tasks)} 个生产任务")

    # 等待所有任务完成
    total_tasks = len(build_tasks) + len(production_tasks)
    results = ray.get(manager.wait_for_results.remote(total_tasks, max_wait_time=60.0))

    print(f"\n获取到 {len(results)} 个结果:")
    build_success = 0
    production_success = 0

    for result in results:
        if result['status'] == 'success':
            if 'build' in result['func_name'] or 'ensure' in result['func_name'] or 'deploy' in result['func_name']:
                build_success += 1
                print(f"🏗️ {result['func_name']}: 建造成功")
            else:
                production_success += 1
                print(f"🏭 {result['func_name']}: 生产成功 - {result['result']}")
        else:
            print(f"❌ {result['func_name']}: {result['error']}")

    print(f"\n=== 测试统计 ===")
    print(f"建造任务成功: {build_success}/{len(build_tasks)}")
    print(f"生产任务成功: {production_success}/{len(production_tasks)}")
    print(f"总体成功率: {(build_success + production_success) / total_tasks * 100:.1f}%")

    ray.get(manager.stop_consumers.remote())
    ray.shutdown()


if __name__ == "__main__":
    # 运行基础测试
    game_build_test()

    # 可选：运行扩展测试
    # print("\n" + "="*60)
    # comprehensive_base_test()

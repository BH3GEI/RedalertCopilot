import time
import random
import json
from typing import List, Dict, Any, Optional


def add_num(a: int, b: int) -> int:
    """简单的加法函数"""
    return a + b


def multiply_num(a: int, b: int) -> int:
    """乘法函数"""
    time.sleep(0.1)  # 模拟处理时间
    return a * b


def calculate_power(base: int, exponent: int) -> int:
    """计算幂次方"""
    time.sleep(0.2)
    return base ** exponent


def process_string(text: str, operation: str = "upper") -> str:
    """字符串处理函数"""
    time.sleep(0.1)
    if operation == "upper":
        return text.upper()
    elif operation == "lower":
        return text.lower()
    elif operation == "reverse":
        return text[::-1]
    elif operation == "length":
        return f"长度: {len(text)}"
    else:
        return text


def sum_list(numbers: List[int]) -> Dict[str, Any]:
    """计算列表的统计信息"""
    time.sleep(0.2)
    if not numbers:
        return {"sum": 0, "avg": 0, "count": 0, "max": None, "min": None}

    return {
        "sum": sum(numbers),
        "avg": sum(numbers) / len(numbers),
        "count": len(numbers),
        "max": max(numbers),
        "min": min(numbers)
    }


def generate_random_data(size: int, min_val: int = 1, max_val: int = 100) -> List[int]:
    """生成随机数据"""
    time.sleep(0.3)
    return [random.randint(min_val, max_val) for _ in range(size)]


def simulate_api_call(url: str, method: str = "GET", delay: float = 0.5) -> Dict[str, Any]:
    """模拟API调用"""
    time.sleep(delay)
    return {
        "url": url,
        "method": method,
        "status_code": random.choice([200, 201, 400, 404, 500]),
        "response_time": delay,
        "timestamp": time.time()
    }


def complex_calculation(data: Dict[str, Any]) -> Dict[str, Any]:
    """复杂计算函数"""
    time.sleep(0.4)

    numbers = data.get("numbers", [])
    factor = data.get("factor", 1.0)
    operation = data.get("operation", "sum")

    if not numbers:
        return {"error": "没有提供数据"}

    if operation == "sum":
        result = sum(numbers) * factor
    elif operation == "product":
        result = 1
        for num in numbers:
            result *= num
        result *= factor
    elif operation == "average":
        result = (sum(numbers) / len(numbers)) * factor
    else:
        result = 0

    return {
        "operation": operation,
        "factor": factor,
        "input_count": len(numbers),
        "result": result,
        "processing_time": 0.4
    }


def validate_email(email: str) -> Dict[str, Any]:
    """验证邮箱格式"""
    time.sleep(0.1)
    import re

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(pattern, email))

    return {
        "email": email,
        "is_valid": is_valid,
        "domain": email.split('@')[-1] if '@' in email else None,
        "username": email.split('@')[0] if '@' in email else None
    }


def fibonacci_sequence(n: int) -> List[int]:
    """生成斐波那契数列"""
    time.sleep(0.2)
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    sequence = [0, 1]
    for i in range(2, n):
        sequence.append(sequence[i - 1] + sequence[i - 2])

    return sequence


def sort_and_filter(numbers: List[int], min_value: int = 0, reverse: bool = False) -> Dict[str, Any]:
    """排序和过滤数据"""
    time.sleep(0.15)

    filtered = [num for num in numbers if num >= min_value]
    sorted_numbers = sorted(filtered, reverse=reverse)

    return {
        "original_count": len(numbers),
        "filtered_count": len(filtered),
        "sorted_data": sorted_numbers,
        "removed_count": len(numbers) - len(filtered)
    }


def simulate_database_query(table: str, conditions: Dict[str, Any] = None) -> Dict[str, Any]:
    """模拟数据库查询"""
    time.sleep(random.uniform(0.1, 0.8))  # 模拟数据库延迟

    # 模拟查询结果
    mock_results = {
        "users": [
            {"id": 1, "name": "张三", "age": 25},
            {"id": 2, "name": "李四", "age": 30},
            {"id": 3, "name": "王五", "age": 28}
        ],
        "products": [
            {"id": 1, "name": "笔记本电脑", "price": 5999},
            {"id": 2, "name": "手机", "price": 2999},
            {"id": 3, "name": "平板", "price": 1999}
        ],
        "orders": [
            {"id": 1, "user_id": 1, "product_id": 1, "quantity": 1},
            {"id": 2, "user_id": 2, "product_id": 2, "quantity": 2}
        ]
    }

    results = mock_results.get(table, [])

    # 应用简单的条件过滤
    if conditions:
        for key, value in conditions.items():
            results = [r for r in results if r.get(key) == value]

    return {
        "table": table,
        "conditions": conditions or {},
        "results": results,
        "count": len(results),
        "query_time": random.uniform(0.1, 0.8)
    }


def error_prone_function(success_rate: float = 0.8) -> str:
    """可能出错的函数，用于测试错误处理"""
    time.sleep(0.1)

    if random.random() > success_rate:
        raise Exception(f"随机错误！成功率设置为 {success_rate}")

    return f"函数成功执行！成功率: {success_rate}"


def get_all_tool_functions():
    """返回所有可用的工具函数"""
    import inspect
    import sys
    current_module = sys.modules[__name__]

    functions = {}
    for name, obj in inspect.getmembers(current_module):
        if (inspect.isfunction(obj) and
                not name.startswith('_') and
                name != 'get_all_tool_functions'):
            functions[name] = obj

    return functions


# mcp_server/tools.py
# 这个脚本不依赖于 mcp 框架，只包含可调用的函数
# 适配Ray分布式执行，每个函数独立创建API客户端
import os
import sys
import inspect


from OpenRA_Copilot_Library import GameAPI
from OpenRA_Copilot_Library.models import Location, TargetsQueryParam, Actor, MapQueryResult
from typing import List, Dict, Any, Optional


def get_api_client():
    """为每个进程/函数调用创建独立的API客户端，避免Ray序列化问题"""
    return GameAPI(host="localhost", port=7445, language="zh")


# === 游戏状态查询函数 ===

def get_game_state() -> Dict[str, Any]:
    """返回玩家资源、电力和可见单位列表"""
    api = get_api_client()
    info = api.player_base_info_query()
    units = api.query_actor(
        TargetsQueryParam(
            type=[], faction=["任意"], range="screen", restrain=[{"visible": True}]
        )
    )
    visible = [
        {
            "actor_id": u.actor_id,
            "type": u.type,
            "faction": u.faction,
            "position": {"x": u.position.x, "y": u.position.y},
        }
        for u in units if u.faction != "中立"
    ]

    return {
        "cash": info.Cash,
        "resources": info.Resources,
        "power": info.Power,
        "visible_units": visible
    }


def player_base_info_query() -> Dict[str, Any]:
    """查询玩家基地的资源、电力等基础信息"""
    api = get_api_client()
    info = api.player_base_info_query()
    return {
        "cash": info.Cash,
        "resources": info.Resources,
        "power": info.Power,
        "powerDrained": info.PowerDrained,
        "powerProvided": info.PowerProvided
    }


def screen_info_query() -> Dict[str, Any]:
    """查询当前屏幕信息"""
    api = get_api_client()
    info = api.screen_info_query()
    return {
        "screenMin": {"x": info.ScreenMin.x, "y": info.ScreenMin.y},
        "screenMax": {"x": info.ScreenMax.x, "y": info.ScreenMax.y},
        "isMouseOnScreen": info.IsMouseOnScreen,
        "mousePosition": {"x": info.MousePosition.x, "y": info.MousePosition.y}
    }


def map_query() -> Dict[str, Any]:
    """查询地图信息并返回序列化数据"""
    api = get_api_client()
    result = api.map_query()
    return {
        "width": result.MapWidth,
        "height": result.MapHeight,
        "heightMap": result.Height,
        "visible": result.IsVisible,
        "explored": result.IsExplored,
        "terrain": result.Terrain,
        "resourcesType": result.ResourcesType,
        "resources": result.Resources
    }


# === 单位查询函数 ===

def visible_units(type: List[str], faction: str, range: str, restrain: List[dict]) -> List[Dict[str, Any]]:
    """根据条件查询可见单位"""
    api = get_api_client()
    if isinstance(type, str):
        type = [type]
    if isinstance(restrain, dict):
        restrain = [restrain]
    elif isinstance(restrain, bool):
        restrain = []

    params = TargetsQueryParam(type=type, faction=faction, range=range, restrain=restrain)
    units = api.query_actor(params)
    return [
        {
            "actor_id": u.actor_id,
            "type": u.type,
            "faction": u.faction,
            "position": {"x": u.position.x, "y": u.position.y},
            "hpPercent": getattr(u, "hp_percent", None)
        }
        for u in units
    ]


def query_actor(type: List[str], faction: str, range: str, restrain: List[dict]) -> List[Dict[str, Any]]:
    """查询单位列表"""
    api = get_api_client()
    params = TargetsQueryParam(type=type, faction=faction, range=range, restrain=restrain)
    actors = api.query_actor(params)
    return [
        {
            "actor_id": u.actor_id,
            "type": u.type,
            "faction": u.faction,
            "position": {"x": u.position.x, "y": u.position.y},
            "hpPercent": getattr(u, "hp_percent", None)
        }
        for u in actors
    ]


def get_actor_by_id(actor_id: int) -> Optional[Dict[str, Any]]:
    """根据 Actor ID 获取单个单位的信息，如果不存在则返回 None"""
    api = get_api_client()
    actor = api.get_actor_by_id(actor_id)
    if actor is None:
        return None
    return {
        "actor_id": actor.actor_id,
        "type": actor.type,
        "faction": actor.faction,
        "position": {"x": actor.position.x, "y": actor.position.y},
        "hpPercent": getattr(actor, "hp_percent", None)
    }


def update_actor(actor_id: int) -> Optional[Dict[str, Any]]:
    """根据 actor_id 更新该单位的信息，并返回其最新状态"""
    api = get_api_client()
    actor = Actor(actor_id)
    success = api.update_actor(actor)
    if not success:
        return None
    return {
        "actor_id": actor.actor_id,
        "type": actor.type,
        "faction": actor.faction,
        "position": {"x": actor.position.x, "y": actor.position.y},
        "hpPercent": getattr(actor, "hp_percent", None)
    }


def unit_attribute_query(actor_ids: List[int]) -> Dict[str, Any]:
    """查询指定单位的属性及其攻击范围内的目标"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    return api.unit_attribute_query(actors)


# === 生产函数 ===

def produce(unit_type: str, quantity: int) -> int:
    """生产指定类型和数量的单位，返回生产任务 ID"""
    api = get_api_client()
    wait_id = api.produce(unit_type, quantity, auto_place_building=True)
    return wait_id or -1


def can_produce(unit_type: str) -> bool:
    """检查是否可生产某类型单位"""
    api = get_api_client()
    return api.can_produce(unit_type)


def ensure_can_build_wait(building_name: str) -> bool:
    """确保指定建筑已存在，若不存在则递归建造其所有依赖并等待完成"""
    api = get_api_client()
    return api.ensure_can_build_wait(building_name)


def ensure_can_produce_unit(unit_name: str) -> bool:
    """确保能生产指定单位（会自动补齐依赖建筑并等待完成）"""
    api = get_api_client()
    return api.ensure_can_produce_unit(unit_name)


def query_production_queue(queue_type: str) -> Dict[str, Any]:
    """查询指定类型的生产队列"""
    api = get_api_client()
    return api.query_production_queue(queue_type)


def manage_production(queue_type: str, action: str) -> str:
    """管理生产队列中的项目（暂停、取消或继续）"""
    api = get_api_client()
    api.manage_production(queue_type, action)
    return "ok"


def deploy_mcv_and_wait(wait_time: float = 1.0) -> str:
    """展开自己的基地车并等待指定时间"""
    api = get_api_client()
    api.deploy_mcv_and_wait(wait_time)
    return "ok"


# === 单位控制函数 ===

def move_units(actor_ids: List[int], x: int, y: int, attack_move: bool = False) -> str:
    """移动一批单位到指定坐标"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    loc = Location(x, y)
    api.move_units_by_location(actors, loc, attack_move=attack_move)
    return "ok"


def move_units_by_location(actor_ids: List[int], x: int, y: int, attack_move: bool = False) -> str:
    """把一批单位移动到指定坐标"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    api.move_units_by_location(actors, Location(x, y), attack_move)
    return "ok"


def move_units_by_direction(actor_ids: List[int], direction: str, distance: int) -> str:
    """按方向移动一批单位"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    api.move_units_by_direction(actors, direction, distance)
    return "ok"


def move_units_by_path(actor_ids: List[int], path: List[Dict[str, int]]) -> str:
    """沿指定路径移动一批单位"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    locs = [Location(p["x"], p["y"]) for p in path]
    api.move_units_by_path(actors, locs)
    return "ok"


def move_units_and_wait(
        actor_ids: List[int],
        x: int,
        y: int,
        max_wait_time: float = 10.0,
        tolerance_dis: int = 1
) -> bool:
    """移动一批单位到指定位置并等待到达或超时"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    return api.move_units_by_location_and_wait(actors, Location(x, y), max_wait_time, tolerance_dis)


def stop_units(actor_ids: List[int]) -> str:
    """停止一批单位当前行动"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    api.stop(actors)
    return "ok"


def deploy_units(actor_ids: List[int]) -> str:
    """展开或部署指定单位列表"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    api.deploy_units(actors)
    return "ok"


def repair_units(actor_ids: List[int]) -> str:
    """修复一批单位"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    api.repair_units(actors)
    return "ok"


# === 单位选择和编组 ===

def select_units(type: List[str], faction: str, range: str, restrain: List[dict]) -> str:
    """选中符合条件的单位"""
    api = get_api_client()
    api.select_units(TargetsQueryParam(type=type, faction=faction, range=range, restrain=restrain))
    return "ok"


def form_group(actor_ids: List[int], group_id: int) -> str:
    """为一批单位编组"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    api.form_group(actors, group_id)
    return "ok"


# === 战斗函数 ===

def attack(attacker_id: int, target_id: int) -> bool:
    """发起一次攻击"""
    api = get_api_client()
    atk = Actor(attacker_id)
    tgt = Actor(target_id)
    return api.attack_target(atk, tgt)


def attack_target(attacker_id: int, target_id: int) -> bool:
    """由指定单位发起对目标单位的攻击"""
    api = get_api_client()
    attacker = Actor(attacker_id)
    target = Actor(target_id)
    return api.attack_target(attacker, target)


def can_attack_target(attacker_id: int, target_id: int) -> bool:
    """检查指定单位是否可以攻击目标单位"""
    api = get_api_client()
    attacker = Actor(attacker_id)
    target = Actor(target_id)
    return api.can_attack_target(attacker, target)


# === 占领函数 ===

def occupy(occupiers: List[int], targets: List[int]) -> str:
    """占领目标"""
    api = get_api_client()
    occ = [Actor(i) for i in occupiers]
    tgt = [Actor(i) for i in targets]
    api.occupy_units(occ, tgt)
    return "ok"


def occupy_units(occupier_ids: List[int], target_ids: List[int]) -> str:
    """占领指定目标单位"""
    api = get_api_client()
    occupiers = [Actor(i) for i in occupier_ids]
    targets = [Actor(i) for i in target_ids]
    api.occupy_units(occupiers, targets)
    return "ok"


# === 路径和导航 ===

def find_path(actor_ids: List[int], dest_x: int, dest_y: int, method: str) -> List[Dict[str, int]]:
    """为单位寻找路径"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    path = api.find_path(actors, Location(dest_x, dest_y), method)
    return [{"x": p.x, "y": p.y} for p in path]


def get_unexplored_nearby_positions(
        map_result: Dict[str, Any],
        current_x: int,
        current_y: int,
        max_distance: int
) -> List[Dict[str, int]]:
    """获取当前位置附近尚未探索的坐标列表"""
    api = get_api_client()
    mq = MapQueryResult(
        MapWidth=map_result["width"],
        MapHeight=map_result["height"],
        Height=map_result["heightMap"],
        IsVisible=map_result["visible"],
        IsExplored=map_result["explored"],
        Terrain=map_result["terrain"],
        ResourcesType=map_result["resourcesType"],
        Resources=map_result["resources"]
    )
    locs = api.get_unexplored_nearby_positions(
        mq,
        Location(current_x, current_y),
        max_distance
    )
    return [{"x": loc.x, "y": loc.y} for loc in locs]


# === 视野和探索 ===

def visible_query(x: int, y: int) -> bool:
    """查询指定坐标是否在视野中"""
    api = get_api_client()
    return api.visible_query(Location(x, y))


def explorer_query(x: int, y: int) -> bool:
    """查询指定坐标是否已探索"""
    api = get_api_client()
    return api.explorer_query(Location(x, y))


# === 摄像头控制 ===

def camera_move_to(x: int, y: int) -> str:
    """将镜头移动到指定坐标"""
    api = get_api_client()
    api.move_camera_by_location(Location(x, y))
    return "ok"


def camera_move_dir(direction: str, distance: int) -> str:
    """按方向移动镜头"""
    api = get_api_client()
    api.move_camera_by_direction(direction, distance)
    return "ok"


def move_camera_to(actor_id: int) -> str:
    """将镜头移动到指定 Actor 的位置"""
    api = get_api_client()
    api.move_camera_to(Actor(actor_id))
    return "ok"


# === 建筑控制 ===

def set_rally_point(actor_ids: List[int], x: int, y: int) -> str:
    """为指定建筑设置集结点"""
    api = get_api_client()
    actors = [Actor(i) for i in actor_ids]
    api.set_rally_point(actors, Location(x, y))
    return "ok"


# === Ray集成函数 ===

def get_all_tool_functions():
    """返回所有可用的工具函数，用于Ray动态注册"""
    current_module = sys.modules[__name__]

    functions = {}
    for name, obj in inspect.getmembers(current_module):
        if (inspect.isfunction(obj) and
                not name.startswith('_') and
                name not in ['get_api_client', 'get_all_tool_functions']):
            functions[name] = obj

    return functions


# === 函数参数定义（用于OpenAI Function Calling格式） ===
# === 使用示例和测试 ===

if __name__ == "__main__":
    # 测试函数注册
    functions = get_all_tool_functions()
    print("=== 可用的游戏工具函数 ===")
    for name, func in functions.items():
        print(f"- {name}: {func.__doc__ or '无描述'}")

    print(f"\n总共注册了 {len(functions)} 个函数")

    # 测试API连接（需要游戏运行）
    try:
        test_api = get_api_client()
        print("\n✅ GameAPI连接测试成功")
    except Exception as e:
        print(f"\n❌ GameAPI连接测试失败: {e}")


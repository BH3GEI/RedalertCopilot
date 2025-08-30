import duckdb
import json
import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager


class BattleDataManager:
    def __init__(self, db_path: str = 'battle_system.duckdb'):
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """初始化数据库和表结构"""
        with duckdb.connect(self.db_path) as conn:
            # 创建战场信息表
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS battle_info
                         (
                             id
                             VARCHAR
                             PRIMARY
                             KEY,
                             updated_at
                             TIMESTAMP
                             NOT
                             NULL,
                             content
                             VARCHAR
                             NOT
                             NULL
                         )
                         """)

            # 创建默认prompt表
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS default_prompt
                         (
                             id
                             VARCHAR
                             PRIMARY
                             KEY,
                             updated_at
                             TIMESTAMP
                             NOT
                             NULL,
                             content
                             VARCHAR
                             NOT
                             NULL
                         )
                         """)

            # 创建索引提高查询性能
            conn.execute("CREATE INDEX IF NOT EXISTS idx_battle_updated ON battle_info(updated_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt_updated ON default_prompt(updated_at DESC)")

            print("数据库表初始化完成")

    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = duckdb.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _prepare_content(self, content: Any) -> str:
        """准备内容数据，确保是有效的JSON"""
        if isinstance(content, dict) or isinstance(content, list):
            return json.dumps(content, ensure_ascii=False, indent=2)
        elif isinstance(content, str):
            # 验证是否为有效JSON
            try:
                json.loads(content)
                return content
            except json.JSONDecodeError:
                raise ValueError(f"提供的字符串不是有效的JSON格式: {content}")
        else:
            raise ValueError(f"content必须是dict、list或JSON字符串，当前类型: {type(content)}")

    # === 战场信息操作 ===
    def upsert_battle_info(self, battle_id: str, content: Dict[str, Any]) -> bool:
        """插入或更新战场信息"""
        try:
            json_content = self._prepare_content(content)
            current_time = datetime.datetime.now()

            with self._get_connection() as conn:
                # 先尝试更新
                result = conn.execute("""
                                      UPDATE battle_info
                                      SET updated_at = ?,
                                          content    = ?
                                      WHERE id = ?
                                      """, [current_time, json_content, battle_id])

                # 如果没有更新任何行，则插入新记录
                if result.rowcount == 0:
                    conn.execute("""
                                 INSERT INTO battle_info (id, updated_at, content)
                                 VALUES (?, ?, ?)
                                 """, [battle_id, current_time, json_content])

                print(f"战场信息 {battle_id} 更新成功")
                return True
        except Exception as e:
            print(f"更新战场信息失败: {e}")
            return False

    def get_battle_info(self, battle_id: str) -> Optional[Dict]:
        """获取指定战场信息"""
        try:
            with self._get_connection() as conn:
                result = conn.execute("""
                                      SELECT id, updated_at, content
                                      FROM battle_info
                                      WHERE id = ?
                                      """, [battle_id]).fetchone()

                if result:
                    return {
                        'id': result[0],
                        'updated_at': result[1],
                        'content': json.loads(result[2])
                    }
                return None
        except Exception as e:
            print(f"获取战场信息失败: {e}")
            return None

    def get_all_battle_info(self) -> List[Dict]:
        """获取所有战场信息，按更新时间倒序"""
        try:
            with self._get_connection() as conn:
                results = conn.execute("""
                                       SELECT id, updated_at, content
                                       FROM battle_info
                                       ORDER BY updated_at DESC
                                       """).fetchall()

                return [
                    {
                        'id': row[0],
                        'updated_at': row[1],
                        'content': json.loads(row[2])
                    }
                    for row in results
                ]
        except Exception as e:
            print(f"获取战场信息列表失败: {e}")
            return []

    # === 默认Prompt操作 ===
    def upsert_default_prompt(self, prompt_id: str, content: Dict[str, Any]) -> bool:
        """插入或更新默认prompt"""
        try:
            json_content = self._prepare_content(content)
            current_time = datetime.datetime.now()

            with self._get_connection() as conn:
                # 先尝试更新
                result = conn.execute("""
                                      UPDATE default_prompt
                                      SET updated_at = ?,
                                          content    = ?
                                      WHERE id = ?
                                      """, [current_time, json_content, prompt_id])

                # 如果没有更新任何行，则插入新记录
                if result.rowcount == 0:
                    conn.execute("""
                                 INSERT INTO default_prompt (id, updated_at, content)
                                 VALUES (?, ?, ?)
                                 """, [prompt_id, current_time, json_content])

                print(f"默认prompt {prompt_id} 更新成功")
                return True
        except Exception as e:
            print(f"更新默认prompt失败: {e}")
            return False

    def get_default_prompt(self, prompt_id: str) -> Optional[Dict]:
        """获取指定默认prompt"""
        try:
            with self._get_connection() as conn:
                result = conn.execute("""
                                      SELECT id, updated_at, content
                                      FROM default_prompt
                                      WHERE id = ?
                                      """, [prompt_id]).fetchone()

                if result:
                    return {
                        'id': result[0],
                        'updated_at': result[1],
                        'content': json.loads(result[2])
                    }
                return None
        except Exception as e:
            print(f"获取默认prompt失败: {e}")
            return None

    def get_all_default_prompts(self) -> List[Dict]:
        """获取所有默认prompts，按更新时间倒序"""
        try:
            with self._get_connection() as conn:
                results = conn.execute("""
                                       SELECT id, updated_at, content
                                       FROM default_prompt
                                       ORDER BY updated_at DESC
                                       """).fetchall()

                return [
                    {
                        'id': row[0],
                        'updated_at': row[1],
                        'content': json.loads(row[2])
                    }
                    for row in results
                ]
        except Exception as e:
            print(f"获取默认prompt列表失败: {e}")
            return []

    # === 高级查询功能 ===
    def search_battle_by_status(self, status: str) -> List[Dict]:
        """根据战场状态搜索"""
        try:
            with self._get_connection() as conn:
                results = conn.execute("""
                                       SELECT id, updated_at, content
                                       FROM battle_info
                                       WHERE content LIKE ?
                                       ORDER BY updated_at DESC
                                       """, [f'%"status": "{status}"%']).fetchall()

                return [
                    {
                        'id': row[0],
                        'updated_at': row[1],
                        'content': json.loads(row[2])
                    }
                    for row in results
                ]
        except Exception as e:
            print(f"搜索战场失败: {e}")
            return []

    def get_recent_updates(self, hours: int = 24) -> Dict[str, List]:
        """获取最近更新的数据"""
        try:
            with self._get_connection() as conn:
                cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)

                # 获取最近更新的战场信息
                battle_results = conn.execute("""
                                              SELECT id, updated_at, content
                                              FROM battle_info
                                              WHERE updated_at >= ?
                                              ORDER BY updated_at DESC
                                              """, [cutoff_time]).fetchall()

                # 获取最近更新的prompts
                prompt_results = conn.execute("""
                                              SELECT id, updated_at, content
                                              FROM default_prompt
                                              WHERE updated_at >= ?
                                              ORDER BY updated_at DESC
                                              """, [cutoff_time]).fetchall()

                return {
                    'battles': [
                        {
                            'id': row[0],
                            'updated_at': row[1],
                            'content': json.loads(row[2])
                        }
                        for row in battle_results
                    ],
                    'prompts': [
                        {
                            'id': row[0],
                            'updated_at': row[1],
                            'content': json.loads(row[2])
                        }
                        for row in prompt_results
                    ]
                }
        except Exception as e:
            print(f"获取最近更新失败: {e}")
            return {'battles': [], 'prompts': []}

    # === 删除操作 ===
    def delete_battle_info(self, battle_id: str) -> bool:
        """删除战场信息"""
        try:
            with self._get_connection() as conn:
                result = conn.execute("DELETE FROM battle_info WHERE id = ?", [battle_id])
                if result.rowcount > 0:
                    print(f"战场信息 {battle_id} 删除成功")
                    return True
                else:
                    print(f"战场信息 {battle_id} 不存在")
                    return False
        except Exception as e:
            print(f"删除战场信息失败: {e}")
            return False

    def delete_default_prompt(self, prompt_id: str) -> bool:
        """删除默认prompt"""
        try:
            with self._get_connection() as conn:
                result = conn.execute("DELETE FROM default_prompt WHERE id = ?", [prompt_id])
                if result.rowcount > 0:
                    print(f"默认prompt {prompt_id} 删除成功")
                    return True
                else:
                    print(f"默认prompt {prompt_id} 不存在")
                    return False
        except Exception as e:
            print(f"删除默认prompt失败: {e}")
            return False


# === 使用示例 ===
if __name__ == "__main__":
    # 初始化数据管理器
    db_manager = BattleDataManager('battle_system.duckdb')

    print("=== 插入战场信息 ===")
    battle_data = {
        "name": "龙谷大战",
        "status": "ongoing",
        "round": 3,
        "participants": ["玩家A", "玩家B"],
        "start_time": "2025-08-30T15:30:00",
        "settings": {
            "max_rounds": 10,
            "time_limit": 300
        }
    }
    db_manager.upsert_battle_info("battle_001", battle_data)

    print("\n=== 插入默认Prompt ===")
    prompt_data = {
        "type": "battle_start",
        "template": "欢迎来到{battle_name}！当前是第{round}轮。",
        "variables": ["battle_name", "round"],
        "category": "system_message"
    }
    db_manager.upsert_default_prompt("prompt_battle_start", prompt_data)

    print("\n=== 查询数据 ===")
    # 查询特定战场
    battle = db_manager.get_battle_info("battle_001")
    print(f"战场信息: {battle}")

    # 查询特定prompt
    prompt = db_manager.get_default_prompt("prompt_battle_start")
    print(f"Prompt信息: {prompt}")

    print("\n=== 更新数据 ===")
    # 更新战场状态
    updated_battle = battle_data.copy()
    updated_battle["round"] = 4
    updated_battle["status"] = "intense"
    db_manager.upsert_battle_info("battle_001", updated_battle)

    print("\n=== 高级查询 ===")
    # 按状态搜索
    ongoing_battles = db_manager.search_battle_by_status("intense")
    print(f"激烈战场: {len(ongoing_battles)} 个")

    # 获取最近更新
    recent = db_manager.get_recent_updates(hours=1)
    print(f"最近1小时更新: 战场{len(recent['battles'])}个, Prompt{len(recent['prompts'])}个")

    print("\n=== 查看所有数据 ===")
    all_battles = db_manager.get_all_battle_info()
    all_prompts = db_manager.get_all_default_prompts()
    print(f"总共有 {len(all_battles)} 个战场, {len(all_prompts)} 个prompt")

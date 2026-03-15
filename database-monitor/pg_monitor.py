#!/usr/bin/env python3
"""
PostgreSQL 数据库监控模块
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class PostgreSQLMonitor:
    """PostgreSQL 监控器"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    async def connect(self) -> bool:
        """连接数据库"""
        try:
            self.connection = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            logger.info("PostgreSQL 连接成功")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL 连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.connection:
            self.connection.close()
            logger.info("PostgreSQL 连接已断开")
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集数据库指标"""
        if not self.connection:
            await self.connect()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'database_info': await self._get_database_info(),
            'connection_stats': await self._get_connection_stats(),
            'table_stats': await self._get_table_stats(),
            'query_stats': await self._get_query_stats(),
            'lock_stats': await self._get_lock_stats(),
        }
        
        return metrics
    
    async def _get_database_info(self) -> Dict[str, Any]:
        """获取数据库基本信息"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        version() as version,
                        current_database() as database_name,
                        pg_database_size(current_database()) as database_size,
                        (SELECT count(*) FROM pg_stat_activity) as active_connections
                """)
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            logger.error(f"获取数据库信息失败: {e}")
            return {}
    
    async def _get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        state,
                        count(*) as count
                    FROM pg_stat_activity 
                    WHERE pid != pg_backend_pid()
                    GROUP BY state
                """)
                results = cursor.fetchall()
                return {row['state']: row['count'] for row in results}
        except Exception as e:
            logger.error(f"获取连接统计失败: {e}")
            return {}
    
    async def _get_table_stats(self) -> List[Dict[str, Any]]:
        """获取表统计信息"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables 
                    ORDER BY n_live_tup DESC 
                    LIMIT 10
                """)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"获取表统计失败: {e}")
            return []
    
    async def _get_query_stats(self) -> List[Dict[str, Any]]:
        """获取查询统计"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements 
                    ORDER BY total_time DESC 
                    LIMIT 5
                """)
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.warning("pg_stat_statements 扩展未启用或查询失败")
            return []
    
    async def _get_lock_stats(self) -> Dict[str, Any]:
        """获取锁统计"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        mode,
                        count(*) as count
                    FROM pg_locks 
                    GROUP BY mode
                """)
                results = cursor.fetchall()
                return {row['mode']: row['count'] for row in results}
        except Exception as e:
            logger.error(f"获取锁统计失败: {e}")
            return {}


async def main():
    """主函数示例"""
    # 示例连接字符串
    connection_string = "postgresql://username:password@localhost:5432/database"
    
    monitor = PostgreSQLMonitor(connection_string)
    
    try:
        if await monitor.connect():
            metrics = await monitor.collect_metrics()
            print(json.dumps(metrics, indent=2, default=str))
    finally:
        await monitor.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
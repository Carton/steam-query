"""Steam Store API 客户端 - 查询任意游戏

不需要登录，可以直接查询Steam商店中的任何游戏
"""

import asyncio
import logging
import re
import json
from typing import Any, Optional
from datetime import datetime

import aiohttp
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)


class SteamStoreClient:
    """Steam Store API 客户端

    用于查询Steam商店中的任意游戏，无需用户登录
    """

    def __init__(self, requests_per_second: float = 1.0):
        """初始化客户端

        Args:
            requests_per_second: 请求速率限制（默认1 req/sec）
        """
        self.requests_per_second = requests_per_second
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self._session:
            await self._session.close()

    @sleep_and_retry
    @limits(calls=1, period=1)  # 1 req/sec
    async def _get(
        self, url: str, params: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """HTTP GET请求（带流控）"""
        if not self._session:
            raise RuntimeError("客户端未初始化，请使用 async with")

        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP错误: {e}")
            raise
        except Exception as e:
            logger.error(f"未知错误: {e}")
            raise

    async def search_games_by_name(
        self, query: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """通过游戏名称搜索

        使用Steam商店的搜索功能

        Args:
            query: 搜索关键词
            limit: 返回结果数量

        Returns:
            游戏列表，包含app_id和名称
        """
        logger.info(f"搜索游戏: {query}")

        # Steam商店搜索API（非官方但稳定）
        url = "https://store.steampowered.com/api/storesearch/"
        params = {
            "term": query,
            "l": "english",
            "cc": "US",
            "category1": "998",  # Games
        }

        try:
            data = await self._get(url, params)

            if data.get("total", 0) > 0:
                items = data.get("items", [])[:limit]
                results = []

                for item in items:
                    results.append({
                        "app_id": item.get("id"),
                        "name": item.get("name"),
                        "short_desc": item.get("short_description"),
                        "price": item.get("price"),
                        "platforms": item.get("platforms", []),
                        "metacritic": item.get("metacritic"),
                        "review_score": item.get("review_score"),
                    })

                logger.info(f"找到 {len(results)} 个结果")
                return results
            else:
                logger.warning(f"未找到匹配的游戏: {query}")
                return []

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def get_app_details(self, app_id: int) -> Optional[dict[str, Any]]:
        """获取游戏详细信息

        Args:
            app_id: Steam App ID

        Returns:
            游戏详细信息字典
        """
        logger.debug(f"获取游戏详情: {app_id}")

        # Steam Store API (无需API key)
        url = "https://store.steampowered.com/api/appdetails"
        params = {"appids": app_id, "l": "english"}

        try:
            data = await self._get(url, params)

            if str(app_id) in data and data[str(app_id)].get("success"):
                app_data = data[str(app_id)]["data"]
                return self._parse_app_details(app_data)

            logger.warning(f"游戏 {app_id} 未找到")
            return None

        except Exception as e:
            logger.error(f"获取详情失败 (app_id={app_id}): {e}")
            return None

    def _parse_app_details(self, app_data: dict[str, Any]) -> dict[str, Any]:
        """解析游戏详细信息

        Args:
            app_data: 原始API数据

        Returns:
            解析后的游戏信息
        """
        # 提取发行日期
        release_date_info = app_data.get("release_date", {})
        release_date = None
        if not release_date_info.get("coming_soon", False):
            date_str = release_date_info.get("date")
            if date_str:
                release_date = self._parse_date(date_str)

        # 提取开发商/发行商
        developers = [
            dev.get("name", "")
            for dev in app_data.get("developers", [])
            if isinstance(dev, dict)
        ]
        publishers = [
            pub.get("name", "")
            for pub in app_data.get("publishers", [])
            if isinstance(pub, dict)
        ]

        # 提取类型
        genres = [
            genre.get("description", "")
            for genre in app_data.get("genres", [])
            if isinstance(genre, dict)
        ]

        # 提取标签
        tags = [
            tag.get("tag", "")
            for tag in app_data.get("tags", [])
            if isinstance(tag, dict)
        ]

        # Metacritic评分
        metacritic = app_data.get("metacritic", {})
        metacritic_score = metacritic.get("score") if isinstance(metacritic, dict) else None

        # 价格信息
        price_overview = app_data.get("price_overview", {})
        price = None
        if isinstance(price_overview, dict) and price_overview.get("initial") is not None:
            price = {
                "initial": price_overview.get("initial") / 100,  # 转换为美元
                "final": price_overview.get("final") / 100,
                "discount_percent": price_overview.get("discount_percent", 0),
                "currency": price_overview.get("currency", "USD"),
            }

        # 支持的平台
        platforms = app_data.get("platforms", False)
        supported_platforms = []
        if isinstance(platforms, dict):
            if platforms.get("windows", False):
                supported_platforms.append("Windows")
            if platforms.get("mac", False):
                supported_platforms.append("Mac")
            if platforms.get("linux", False):
                supported_platforms.append("Linux")

        return {
            "app_id": app_data.get("steam_appid"),
            "name": app_data.get("name"),
            "short_desc": app_data.get("short_description"),
            "long_desc": app_data.get("detailed_description", "")[:500],  # 截取前500字符
            "release_date": release_date,
            "developers": developers,
            "publishers": publishers,
            "genres": genres,
            "tags": tags,
            "metacritic_score": metacritic_score,
            "price": price,
            "platforms": supported_platforms,
            "is_free": app_data.get("is_free", False),
            "header_image": app_data.get("header_image"),
            "screenshots": [
                s.get("path_thumbnail", s.get("path", ""))
                for s in app_data.get("screenshots", [])[:5]  # 最多5张截图
                if isinstance(s, dict)
            ],
            "website": app_data.get("website"),
            "requirements": self._extract_requirements(app_data),
        }

    def _parse_date(self, date_str: str) -> Optional[str]:
        """解析日期字符串

        Args:
            date_str: 日期字符串

        Returns:
            ISO格式的日期字符串
        """
        if not date_str:
            return None

        # 尝试常见格式
        formats = ["%d %b, %Y", "%b %d, %Y", "%Y-%m-%d", "%d %b %Y", "%b %d %Y"]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue

        # 如果都失败，返回原始字符串
        return date_str

    def _extract_requirements(self, app_data: dict[str, Any]) -> dict[str, dict[str, str]]:
        """提取系统要求

        Args:
            app_data: 游戏数据

        Returns:
            系统要求字典
        """
        pc_requirements = app_data.get("pc_requirements", {})
        requirements = {}

        if isinstance(pc_requirements, dict):
            for platform in ["minimum", "recommended"]:
                req_data = pc_requirements.get(platform, {})
                if isinstance(req_data, dict):
                    requirements[platform] = {
                        "english": req_data.get("english", ""),
                        "parsed": self._parse_requirements(req_data.get("english", "")),
                    }

        return requirements

    def _parse_requirements(self, req_text: str) -> dict[str, str]:
        """解析系统要求文本

        Args:
            req_text: 系统要求文本

        Returns:
            结构化的要求字典
        """
        requirements = {
            "os": "",
            "processor": "",
            "memory": "",
            "graphics": "",
            "directx": "",
            "storage": "",
        }

        lines = req_text.split("\n")
        current_key = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是新的要求类型
            matched = False
            for key in requirements.keys():
                if line.lower().startswith(f"{key}:"):
                    current_key = key
                    requirements[key] = line.split(":", 1)[1].strip()
                    matched = True
                    break

            # 如果没有匹配到新的key，且当前有key，则继续上一个要求
            if not matched and current_key:
                requirements[current_key] += " " + line

        return requirements

    async def get_games_details_batch(
        self, app_ids: list[int]
    ) -> dict[int, dict[str, Any]]:
        """批量获取游戏详情

        Args:
            app_ids: Steam App ID列表

        Returns:
            App ID到游戏详情的映射
        """
        results = {}

        for app_id in app_ids:
            details = await self.get_app_details(app_id)
            if details:
                results[app_id] = details

        return results

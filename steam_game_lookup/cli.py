"""Steam Game Lookup CLI 命令行工具

查询Steam商店中任意游戏的详细信息
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import colorlog

from .steam_client import SteamStoreClient

# 设置日志
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """设置彩色日志"""
    log_level = logging.DEBUG if verbose else logging.INFO

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    logging.root.setLevel(log_level)
    logging.root.addHandler(handler)


def format_game_info(game: dict) -> str:
    """格式化游戏信息用于显示

    Args:
        game: 游戏信息字典

    Returns:
        格式化的字符串
    """
    lines = [
        "",
        "🎮 " + "=" * 60,
        f"  {game.get('name', 'Unknown')}",
        "🎮 " + "=" * 60,
    ]

    # 基本信息
    lines.append(f"\n📋 基本信息:")
    lines.append(f"   App ID:      {game.get('app_id', 'N/A')}")
    lines.append(f"   发行日期:    {game.get('release_date', 'N/A')}")
    lines.append(f"   免费:        {'是' if game.get('is_free') else '否'}")

    if game.get("developers"):
        lines.append(f"   开发商:      {', '.join(game['developers'])}")
    if game.get("publishers"):
        lines.append(f"   发行商:      {', '.join(game['publishers'])}")

    if game.get("genres"):
        lines.append(f"   类型:        {', '.join(game['genres'])}")

    if game.get("metacritic_score"):
        score = game["metacritic_score"]
        emoji = "🟢" if score >= 75 else "🟡" if score >= 50 else "🔴"
        lines.append(f"   Metascore:  {emoji} {score}/100")

    # 平台
    if game.get("platforms"):
        lines.append(f"\n💻 支持平台:")
        for platform in game["platforms"]:
            lines.append(f"   • {platform}")

    # 价格
    if game.get("price"):
        price = game["price"]
        if price.get("discount_percent", 0) > 0:
            lines.append(
                f"\n💰 价格: ${price['final']:.2f} (原价 ${price['initial']:.2f}, -{price['discount_percent']}%)"
            )
        else:
            lines.append(f"\n💰 价格: ${price['final']:.2f}")
    elif game.get("is_free"):
        lines.append(f"\n💰 价格: 免费")

    # 简短描述
    if game.get("short_desc"):
        desc = game["short_desc"]
        if len(desc) > 100:
            desc = desc[:97] + "..."
        lines.append(f"\n📝 简介:")
        lines.append(f"   {desc}")

    # 链接
    app_id = game.get("app_id")
    if app_id:
        lines.append(f"\n🔗 商店链接: https://store.steampowered.com/app/{app_id}/")

    lines.append("")
    return "\n".join(lines)


def format_game_json(game: dict) -> str:
    """格式化为JSON字符串"""
    # 移除一些冗余字段
    game_copy = game.copy()
    if "long_desc" in game_copy:
        del game_copy["long_desc"]
    if "screenshots" in game_copy:
        del game_copy["screenshots"]

    return json.dumps(game_copy, indent=2, ensure_ascii=False)


async def search_command(args):
    """搜索游戏命令"""
    async with SteamStoreClient() as client:
        results = await client.search_games_by_name(args.query, limit=args.limit)

        if not results:
            print(f"❌ 未找到匹配的游戏: {args.query}")
            return 1

        print(f"\n✅ 找到 {len(results)} 个结果:\n")

        for i, game in enumerate(results, 1):
            print(f"{i}. {game['name']} (App ID: {game['app_id']})")
            if game.get("short_desc"):
                desc = game["short_desc"][:80] + "..." if len(game["short_desc"]) > 80 else game["short_desc"]
                print(f"   {desc}")
            if game.get("price"):
                price = game["price"]
                if price.get("discount_percent", 0) > 0:
                    print(f"   💰 ${price['final']:.2f} (原价 ${price['initial']:.2f}, -{price['discount_percent']}%)")
                elif not price.get("final") == 0:
                    print(f"   💰 ${price['final']:.2f}")
            else:
                print(f"   💰 免费或未定价")
            print()

        # 保存到文件
        if args.output:
            output_data = {
                "query": args.query,
                "timestamp": datetime.now().isoformat(),
                "total": len(results),
                "results": results,
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ 结果已保存到: {args.output}")

        return 0


async def lookup_command(args):
    """查询游戏详情命令"""
    async with SteamStoreClient() as client:
        # 如果是搜索词，先搜索
        if args.query:
            print(f"🔍 搜索: {args.query}")
            search_results = await client.search_games_by_name(args.query, limit=1)

            if not search_results:
                print(f"❌ 未找到游戏: {args.query}")
                return 1

            app_id = search_results[0]["app_id"]
            print(f"✅ 找到: {search_results[0]['name']} (App ID: {app_id})")
        else:
            app_id = args.app_id

        # 获取详细信息
        print(f"⏳ 正在获取详细信息...")
        game = await client.get_app_details(app_id)

        if not game:
            print(f"❌ 无法获取游戏详情 (App ID: {app_id})")
            return 1

        # 显示结果
        if args.json:
            print(format_game_json(game))
        else:
            print(format_game_info(game))

        # 保存到文件
        if args.output:
            output_data = {
                "app_id": app_id,
                "timestamp": datetime.now().isoformat(),
                "game": game,
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ 详情已保存到: {args.output}")

        return 0


async def batch_command(args):
    """批量查询命令"""
    # 读取输入
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            if args.input.endswith(".json"):
                data = json.load(f)
                # 假设是Epic游戏格式
                queries = [
                    g.get("metadata", {}).get("title", "")
                    for g in data
                    if g.get("metadata", {}).get("title")
                ]
            else:
                # 文本文件，每行一个游戏名
                queries = [line.strip() for line in f if line.strip()]
    else:
        queries = args.queries

    if not queries:
        print("❌ 没有要查询的游戏")
        return 1

    print(f"📋 将查询 {len(queries)} 个游戏\n")

    async with SteamStoreClient() as client:
        results = []
        found = 0

        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] 🔍 {query}... ", end="", flush=True)

            # 搜索
            search_results = await client.search_games_by_name(query, limit=1)

            if search_results:
                app_id = search_results[0]["app_id"]
                print(f"✅ (App ID: {app_id})", end="", flush=True)

                # 获取详情
                game = await client.get_app_details(app_id)
                if game:
                    results.append(game)
                    found += 1
                    print(f" ✓")
                else:
                    results.append({"query": query, "error": "无法获取详情"})
                    print(f" ⚠️")
            else:
                results.append({"query": query, "error": "未找到"})
                print(f" ❌")

        # 显示统计
        print(f"\n📊 统计:")
        print(f"   总计: {len(queries)}")
        print(f"   找到: {found}")
        print(f"   未找到: {len(queries) - found}")

        # 保存结果
        if args.output:
            output_data = {
                "timestamp": datetime.now().isoformat(),
                "total": len(queries),
                "found": found,
                "results": results,
            }
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 结果已保存到: {args.output}")

        return 0


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        prog="steam-lookup",
        description="查询Steam商店中任意游戏的详细信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 搜索游戏
  steam-lookup search "Elden Ring"

  # 查询游戏详情（通过App ID）
  steam-lookup lookup 1245620

  # 查询游戏详情（通过名称搜索）
  steam-lookup lookup -q "Hollow Knight"

  # 批量查询
  steam-lookup batch "Elden Ring" "Hollow Knight" "Stardew Valley"

  # 从文件批量查询
  steam-lookup batch -i epic-games.json -o results.json

更多信息: https://github.com/yourusername/steam-game-lookup
        """,
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="显示详细日志"
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 搜索命令
    search_parser = subparsers.add_parser(
        "search", help="搜索游戏（返回匹配的游戏列表）"
    )
    search_parser.add_argument("query", help="搜索关键词")
    search_parser.add_argument(
        "-l", "--limit", type=int, default=10, help="返回结果数量（默认10）"
    )
    search_parser.add_argument("-o", "--output", help="保存结果到JSON文件")

    # 查询命令
    lookup_parser = subparsers.add_parser(
        "lookup", help="查询游戏详细信息"
    )
    lookup_group = lookup_parser.add_mutually_exclusive_group(required=True)
    lookup_group.add_argument("app_id", nargs="?", type=int, help="Steam App ID")
    lookup_group.add_argument("-q", "--query", help="游戏名称（会先搜索）")
    lookup_parser.add_argument(
        "-j", "--json", action="store_true", help="以JSON格式输出"
    )
    lookup_parser.add_argument("-o", "--output", help="保存结果到JSON文件")

    # 批量查询命令
    batch_parser = subparsers.add_parser("batch", help="批量查询多个游戏")
    batch_input = batch_parser.add_mutually_exclusive_group(required=True)
    batch_input.add_argument(
        "queries", nargs="*", help="游戏名称列表"
    )
    batch_input.add_argument(
        "-i", "--input", help="输入文件（JSON或文本，每行一个游戏名）"
    )
    batch_parser.add_argument("-o", "--output", required=True, help="输出JSON文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # 设置日志
    setup_logging(args.verbose)

    # 执行命令
    try:
        if args.command == "search":
            return await search_command(args)
        elif args.command == "lookup":
            return await lookup_command(args)
        elif args.command == "batch":
            return await batch_command(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        return 130
    except Exception as e:
        logger.exception(f"错误: {e}")
        return 1


def cli_main():
    """CLI入口点"""
    exit(asyncio.run(main()))


if __name__ == "__main__":
    cli_main()

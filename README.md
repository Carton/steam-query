# 🎮 Steam Game Lookup

查询Steam商店中**任意游戏**的详细信息 - 无需登录，无需API Key！

## ✨ 特性

- 🔍 **搜索游戏** - 通过游戏名称搜索Steam商店
- 📋 **详细信息** - 获取发行日期、开发商、类型、评分等
- 💰 **价格信息** - 显示当前价格和折扣信息
- 💻 **平台支持** - 显示Windows/Mac/Linux支持
- 📊 **批量查询** - 一次查询多个游戏
- 🎯 **精确匹配** - 支持通过App ID直接查询
- ⏱️ **自动流控** - 内置速率限制，遵守API规则
- 📄 **JSON输出** - 支持导出为JSON格式

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
cd /d/tmp/steam-game-lookup

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -e .
```

### 基础用法

#### 1. 搜索游戏

```bash
# 搜索游戏
steam-lookup search "Elden Ring"

# 限制结果数量
steam-lookup search "Hollow Knight" -l 5

# 保存搜索结果
steam-lookup search "Stardew Valley" -o results.json
```

#### 2. 查询游戏详情

```bash
# 通过App ID查询
steam-lookup lookup 1245620

# 通过游戏名称查询（自动搜索）
steam-lookup lookup -q "Elden Ring"

# JSON格式输出
steam-lookup lookup -q "Hollow Knight" --json

# 保存详情
steam-lookup lookup 1245620 -o elden-ring.json
```

#### 3. 批量查询

```bash
# 查询多个游戏
steam-lookup batch "Elden Ring" "Hollow Knight" "Stardew Valley" -o results.json

# 从Epic游戏JSON批量查询
steam-lookup batch -i ../epic-games.json -o epic-with-steam-info.json

# 从文本文件查询（每行一个游戏名）
steam-lookup batch -i games.txt -o results.json
```

## 📊 输出示例

```
🎮 ============================================================
  Elden Ring
🎮 ============================================================

📋 基本信息:
   App ID:      1245620
   发行日期:    2022-02-25
   免费:        否
   开发商:      FromSoftware Inc.
   发行商:      BANDAI NAMCO Entertainment Inc.
   类型:        Action RPG, Adventure
   Metascore:  🟢 96/100

💻 支持平台:
   • Windows
   • Steam Deck

💰 价格: $59.99

📝 简介:
   A new action RPG developed by FromSoftware Inc. and BANDAI NAMCO...

🔗 商店链接: https://store.steampowered.com/app/1245620/
```

## 🔧 配置

### 环境变量

```bash
# 设置日志级别
export STEAM_LOOKUP_LOG_LEVEL=DEBUG
```

### 速率限制

默认：1 request/second（遵守Steam建议）

可以在代码中修改：
```python
client = SteamStoreClient(requests_per_second=2.0)  # 2 req/sec
```

## 📁 项目结构

```
steam-game-lookup/
├── steam_game_lookup/
│   ├── __init__.py       # 包初始化
│   ├── steam_client.py   # Steam API客户端
│   └── cli.py           # 命令行接口
├── setup.py             # 安装配置
├── requirements.txt     # 依赖列表
└── README.md           # 本文件
```

## 🎯 使用场景

### 场景1：查询Epic游戏的Steam信息

```bash
cd /d/tmp
steam-lookup batch -i epic-games.json -o epic-with-steam.json
```

### 场景2：查找游戏发行日期

```bash
steam-lookup lookup -q "Hollow Knight" --json | jq '.game.release_date'
```

### 场景3：批量查询游戏列表

```bash
# 创建游戏列表
cat > games.txt << EOF
Elden Ring
Hollow Knight
Stardew Valley
Celeste
EOF

# 批量查询
steam-lookup batch -i games.txt -o results.json
```

## ⚠️ 限制

1. **速率限制** - Steam Store API没有公开的速率限制，但建议每秒不超过1次请求
2. **搜索精度** - 使用Steam商店的搜索功能，可能不完全精确
3. **可用性** - 依赖Steam商店API的可用性

## 🔍 类似工具对比

| 工具 | 需要登录 | 需要API Key | 查询任意游戏 |
|------|----------|-------------|--------------|
| **steam-lookup** | ❌ | ❌ | ✅ |
| steam-game-analyzer | ✅ | ✅ | ❌ (仅拥有) |
| steam-cli | ❌ | ✅ | ❌ (仅拥有) |

## 📚 API参考

### SteamStoreClient

```python
from steam_game_lookup import SteamStoreClient

async with SteamStoreClient() as client:
    # 搜索游戏
    results = await client.search_games_by_name("Elden Ring")

    # 获取详情
    game = await client.get_app_details(1245620)

    # 批量获取
    games = await client.get_games_details_batch([1245620, 571860])
```

## 🤝 贡献

欢迎提交问题和拉取请求！

## 📄 许可证

MIT License

## 🔗 相关项目

- [steam-game-analyzer](../steam-game-analyzer) - Steam游戏库分析工具
- [steam-cli](https://github.com/mjrussell/steam-cli) - Steam库管理CLI

## 🙏 致谢

- Steam Store API（非官方但稳定）
- 基于 [steam-game-analyzer](../steam-game-analyzer) 的设计灵感

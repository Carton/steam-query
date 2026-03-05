"""Steam Game Lookup - Setup configuration"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="steam-game-lookup",
    version="1.0.0",
    author="Steam Game Lookup",
    description="查询Steam商店中任意游戏的详细信息 - 无需登录",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/steam-game-lookup",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "aiohttp>=3.9.0",
        "requests>=2.31.0",
        "ratelimit>=2.2.0",
        "colorlog>=6.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "steam-lookup=steam_game_lookup.cli:cli_main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/steam-game-lookup/issues",
        "Source": "https://github.com/yourusername/steam-game-lookup",
    },
)

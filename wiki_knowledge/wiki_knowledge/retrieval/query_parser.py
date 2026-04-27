# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 查询解析器

解析用户查询，提取目标实体和动作词，为多路匹配提供输入。

Author: lhx
Date: 2026-04-27
"""

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedQuery:
    """查询解析结果。

    Attributes:
        target: 目标实体（如"水杯"、"用户认证"）
        action: 动作词（如"如何清洗"、"怎么配置"）
        original_query: 原始查询
    """
    target: str
    action: str
    original_query: str


class QueryParser:
    """查询解析器。

    将用户自然语言查询解析为结构化的目标实体和动作词。
    使用 LLM 提取关键信息。

    Methods:
        parse: 解析用户查询
        _call_llm: 调用 LLM 服务
        _extract_from_template: 模板匹配（降级方案）
    """

    # 动作词库
    ACTION_WORDS = [
        "如何", "怎么", "怎样", "查询", "获取", "设置", "配置",
        "创建", "删除", "更新", "修改", "使用", "调用", "请求",
        "安装", "部署", "启动", "停止", "重启", "连接", "登录",
        "注册", "认证", "授权", "验证", "编译", "运行", "调试",
        "解决", "处理", "排查", "检查", "开启", "关闭", "启用", "禁用",
    ]

    # LLM 解析 Prompt
    PARSE_PROMPT = """## Task
从用户查询中提取目标实体和动作词。

用户查询：{query}

## Task
1. 目标实体：用户想要了解的事物（可能是API、组件、错误码、概念等）
2. 动作词：用户想要执行的操作（如何、怎么、配置、查询等）

## Output Format
JSON格式（不包含任何解释性文字）：
{{
  "target": "目标实体名称",
  "action": "动作词"
}}"""

    async def _call_llm(self, prompt: str) -> str:
        """调用 LLM 服务。

        使用平台封装的 unified_agent_invoke 进行 LLM 调用。

        Args:
            prompt: 提示词

        Returns:
            LLM 响应文本
        """
        from app.config.config import settings
        from app.services.llm_chat.unified_agent import unified_agent_invoke
        from app.services.llm_chat.request import UnifiedAgentRequest

        request = UnifiedAgentRequest(
            query=prompt,
            project_id=settings.get("WIKI_KNOWLEDGE_PROJECT_ID"),
        )

        result = await unified_agent_invoke(request, agent_context={})
        return result.get("answer", "")

    async def parse(self, query: str) -> ParsedQuery:
        """解析用户查询。

        Args:
            query: 用户原始查询

        Returns:
            ParsedQuery：包含目标实体、动作词和原始查询
        """
        # 尝试 LLM 解析
        try:
            prompt = self.PARSE_PROMPT.format(query=query)
            response = await self._call_llm(prompt)
            result = json.loads(response)
            return ParsedQuery(
                target=result.get("target", query),
                action=result.get("action", ""),
                original_query=query
            )
        except (json.JSONDecodeError, Exception):
            # LLM 解析失败，使用模板匹配降级
            return self._extract_from_template(query)

    def _extract_from_template(self, query: str) -> ParsedQuery:
        """模板匹配解析（降级方案）。

        当 LLM 不可用时，使用规则匹配提取目标实体和动作词。

        Args:
            query: 用户查询

        Returns:
            ParsedQuery：解析结果
        """
        target = query
        action = ""

        # 提取动作词
        for action_word in self.ACTION_WORDS:
            if action_word in query:
                action = action_word
                # 移除动作词，获取目标实体
                target = query.replace(action_word, "").strip()
                break

        return ParsedQuery(
            target=target if target else query,
            action=action,
            original_query=query
        )
# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 查询解析器测试

Author: lhx
Date: 2026-04-27

测试结果 (2026-04-27):
- ✅ test_parse_with_llm_success: PASSED
- ✅ test_parse_with_llm_json_decode_error: PASSED
- ✅ test_parse_with_llm_exception: PASSED
- ✅ test_extract_from_template_simple_query: PASSED
- ✅ test_extract_from_template_with_config: PASSED
- ✅ test_extract_from_template_query_action: PASSED
- ✅ test_extract_from_template_no_action_word: PASSED
- ✅ test_extract_from_template_empty_query: PASSED
- ✅ test_action_words_coverage: PASSED
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.service.wiki_knowledge.retrieval.query_parser import (
    QueryParser,
    ParsedQuery,
)


class TestQueryParser:
    """QueryParser 单元测试。"""

    @pytest.fixture
    def parser(self):
        """创建 QueryParser 实例。"""
        return QueryParser()

    @pytest.mark.asyncio
    async def test_parse_with_llm_success(self, parser):
        """测试 LLM 解析成功场景。"""
        mock_response = '{"target": "水杯", "action": "如何清洗"}'

        with patch.object(
            parser,
            "_call_llm",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await parser.parse("如何清洗水杯")

            assert isinstance(result, ParsedQuery)
            assert result.target == "水杯"
            assert result.action == "如何清洗"
            assert result.original_query == "如何清洗水杯"

    @pytest.mark.asyncio
    async def test_parse_with_llm_json_decode_error(self, parser):
        """测试 LLM 返回非 JSON 格式时的降级处理。"""
        with patch.object(
            parser,
            "_call_llm",
            new_callable=AsyncMock,
            return_value="这是一个无效的响应",
        ):
            result = await parser.parse("如何清洗水杯")

            assert isinstance(result, ParsedQuery)
            # 降级到模板匹配：移除动作词"如何"，剩余"清洗水杯"
            assert result.target == "清洗水杯"
            assert result.action == "如何"
            assert result.original_query == "如何清洗水杯"

    @pytest.mark.asyncio
    async def test_parse_with_llm_exception(self, parser):
        """测试 LLM 调用异常时的降级处理。"""
        with patch.object(
            parser,
            "_call_llm",
            new_callable=AsyncMock,
            side_effect=Exception("LLM 服务不可用"),
        ):
            result = await parser.parse("如何清洗水杯")

            assert isinstance(result, ParsedQuery)
            # 降级到模板匹配：移除动作词"如何"，剩余"清洗水杯"
            assert result.target == "清洗水杯"
            assert result.action == "如何"
            assert result.original_query == "如何清洗水杯"

    def test_extract_from_template_simple_query(self, parser):
        """测试模板匹配 - 简单查询。"""
        result = parser._extract_from_template("如何清洗水杯")

        # 移除动作词"如何"，剩余"清洗水杯"
        assert result.target == "清洗水杯"
        assert result.action == "如何"
        assert result.original_query == "如何清洗水杯"

    def test_extract_from_template_with_config(self, parser):
        """测试模板匹配 - 配置类查询。"""
        result = parser._extract_from_template("怎么配置用户认证")

        # 移除动作词"怎么"，剩余"配置用户认证"
        assert result.target == "配置用户认证"
        assert result.action == "怎么"
        assert result.original_query == "怎么配置用户认证"

    def test_extract_from_template_query_action(self, parser):
        """测试模板匹配 - 查询动作。"""
        result = parser._extract_from_template("查询订单状态")

        assert result.target == "订单状态"
        assert result.action == "查询"
        assert result.original_query == "查询订单状态"

    def test_extract_from_template_no_action_word(self, parser):
        """测试模板匹配 - 无动作词。"""
        result = parser._extract_from_template("水杯是什么")

        assert result.target == "水杯是什么"
        assert result.action == ""
        assert result.original_query == "水杯是什么"

    def test_extract_from_template_empty_query(self, parser):
        """测试模板匹配 - 空查询。"""
        result = parser._extract_from_template("")

        assert result.target == ""
        assert result.action == ""
        assert result.original_query == ""

    def test_action_words_coverage(self, parser):
        """测试动作词库覆盖。"""
        # 使用ASCII安全的中文测试用例
        test_cases = [
            ("如何清洗", "如何", "清洗"),
            ("怎么配置", "怎么", "配置"),
            ("查询订单", "查询", "订单"),
            ("设置密码", "设置", "密码"),
            ("删除文件", "删除", "文件"),
        ]

        for query, expected_action, expected_target in test_cases:
            result = parser._extract_from_template(query)
            assert result.action == expected_action, f"Failed for query: {query}"
            assert result.target == expected_target, f"Failed for query: {query}"

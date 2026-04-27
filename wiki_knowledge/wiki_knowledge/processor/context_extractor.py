# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 上下文感知特征提取器

将切片内容、父级标题、同级标题同时输入 LLM，提取实体、概念和同义词。

Author: lhx
Date: 2026-04-27
"""

import json
from dataclasses import dataclass, field
from typing import Optional



@dataclass
class ExtractionResult:
    """特征提取结果。

    Attributes:
        entities: 实体列表（具象名词：API名称、组件名、错误码、参数等）
        concepts: 概念列表（抽象名词：业务逻辑、设计思想、协议原理等）
        synonyms: 同义词字典（标准名 -> 同义词列表）
    """
    entities: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    synonyms: dict[str, list[str]] = field(default_factory=dict)


class ContextAwareExtractor:
    """上下文感知特征提取器。

    利用 LLM 提取切片中的实体、概念，并生成同义词扩展。
    上下文信息（父级标题、同级标题）帮助 LLM 准确理解切片语义。

    Methods:
        extract: 提取切片特征
        _build_context_prompt: 构建包含上下文的 prompt
        _call_llm: 调用 LLM 服务
    """

    # LLM Prompt 模板
    EXTRACTION_PROMPT = """## Context
当前切片：
{content}

父级标题：{parent_title}

同级标题：{sibling_titles}

## Task
从上述切片中提取：
1. 实体 (Entities)：具象名词（API名称、组件名、错误码、特定参数）
2. 概念 (Concepts)：抽象名词（业务逻辑、设计思想、协议原理）
3. 同义词扩展：为每个实体/概念生成3-5个潜在搜索关键词

## Output Format
JSON格式（不包含任何解释性文字）：
{{
  "entities": ["实体1", "实体2"],
  "concepts": ["概念1", "概念2"],
  "synonyms": {{
    "实体1": ["同义词1", "同义词2"],
    "概念1": ["同义词1", "同义词2"]
  }}
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

        # 构建请求
        request = UnifiedAgentRequest(
            query=prompt,
            project_id=settings.get("WIKI_KNOWLEDGE_PROJECT_ID"),
        )

        # 调用统一 Agent
        result = await unified_agent_invoke(request, agent_context={})

        return result.get("answer", "")

    async def extract(self, chunk_result, llm_model: str = "deepseek") -> ExtractionResult:
        """提取切片特征。

        Args:
            chunk_result: WikiChunkProcessor 返回的切片结果
            llm_model: 使用的 LLM 模型（已废弃，改为从配置读取）

        Returns:
            ExtractionResult：包含实体、概念、同义词
        """
        prompt = self._build_context_prompt(chunk_result)

        # 调用 LLM
        response = await self._call_llm(prompt)

        # 解析 JSON 响应
        try:
            result = json.loads(response)
            return ExtractionResult(
                entities=result.get("entities", []),
                concepts=result.get("concepts", []),
                synonyms=result.get("synonyms", {})
            )
        except json.JSONDecodeError:
            # LLM 返回格式异常，返回空结果
            return ExtractionResult()

    def _build_context_prompt(self, chunk_result) -> str:
        """构建包含上下文的 prompt。

        Args:
            chunk_result: 切片结果

        Returns:
            格式化后的 prompt 字符串
        """
        # 限制内容长度，避免超出 LLM 上下文
        content = chunk_result.content[:2000] if chunk_result.content else ""
        parent_title = chunk_result.parent_title or "无"
        sibling_titles = ", ".join(chunk_result.sibling_titles[:5]) if chunk_result.sibling_titles else "无"

        return self.EXTRACTION_PROMPT.format(
            content=content,
            parent_title=parent_title,
            sibling_titles=sibling_titles
        )

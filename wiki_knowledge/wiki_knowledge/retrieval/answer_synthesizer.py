# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 答案生成器

基于 Top 3 切片生成答案并标注溯源。

Author: lhx
Date: 2026-04-27
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.service.wiki_knowledge.retrieval.action_filter import ScoredChunk


@dataclass
class AnswerResult:
    """答案结果。

    Attributes:
        answer: 生成的答案
        sources: 来源切片列表
        generated_at: 生成时间
    """
    answer: str
    sources: list[dict] = field(default_factory=list)
    generated_at: str = ""


class AnswerSynthesizer:
    """答案生成器。

    基于检索到的切片生成答案，并标注来源。
    使用 LLM 整合切片内容生成完整答案。

    Methods:
        synthesize: 基于切片生成答案
        _call_llm: 调用 LLM 服务
        _build_prompt: 构建 prompt
    """

    # 答案生成 Prompt 模板
    SYNTHESIZE_PROMPT = """## Task
基于以下切片生成答案，要求：
1. 整合切片内容，生成完整、准确的答案
2. 每个答案必须标注来源：[来源：标题路径]
3. 如果切片不足以回答问题，说明"暂无相关信息"

## 切片内容
{chunk_context}

## 用户问题
{query}

## Output Format
JSON格式（不包含任何解释性文字）：
{{
  "answer": "生成的答案（包含来源标注）",
  "sources": [
    {{"chunk_id": "xxx", "title_path": "xxx", "score": 0.xx}},
    ...
  ]
}}"""

    # 每个切片的最大字符数（避免 prompt 过长）
    CHUNK_MAX_LENGTH = 500

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

    async def synthesize(
        self,
        query: str,
        chunks: list[ScoredChunk],
        top_k: int = 3,
    ) -> AnswerResult:
        """基于切片生成答案。

        Args:
            query: 用户问题
            chunks: 排序后的切片列表
            top_k: 用于生成答案的切片数量

        Returns:
            AnswerResult：包含答案和来源信息
        """
        if not chunks:
            return AnswerResult(
                answer="抱歉，暂无相关信息。",
                sources=[],
                generated_at=datetime.now().isoformat(),
            )

        # 取 Top K 切片
        top_chunks = chunks[:top_k]

        # 构建上下文
        chunk_context = self._build_chunk_context(top_chunks)

        # 构建 prompt
        prompt = self._build_prompt(query, chunk_context)

        # 调用 LLM
        try:
            response = await self._call_llm(prompt)
            return self._parse_response(response, top_chunks)
        except Exception:
            # LLM 调用失败，返回降级答案
            return self._fallback_answer(query, top_chunks)

    def _build_chunk_context(self, chunks: list[ScoredChunk]) -> str:
        """构建切片上下文。

        Args:
            chunks: 切片列表

        Returns:
            格式化的切片上下文字符串
        """
        contexts = []
        for i, chunk in enumerate(chunks, 1):
            # 截断过长内容
            content = chunk.content[:self.CHUNK_MAX_LENGTH]
            if len(chunk.content) > self.CHUNK_MAX_LENGTH:
                content += "..."

            contexts.append(
                f"[{i}] 标题：{chunk.title_path}\n内容：{content}"
            )

        return "\n\n".join(contexts)

    def _build_prompt(self, query: str, chunk_context: str) -> str:
        """构建 prompt。

        Args:
            query: 用户问题
            chunk_context: 切片上下文

        Returns:
            格式化的 prompt
        """
        return self.SYNTHESIZE_PROMPT.format(
            query=query,
            chunk_context=chunk_context,
        )

    def _parse_response(
        self,
        response: str,
        chunks: list[ScoredChunk],
    ) -> AnswerResult:
        """解析 LLM 响应。

        Args:
            response: LLM 响应文本
            chunks: 原始切片列表（用于 sources）

        Returns:
            AnswerResult
        """
        import json

        try:
            result = json.loads(response)
            return AnswerResult(
                answer=result.get("answer", ""),
                sources=[
                    {
                        "chunk_id": c.chunk_id,
                        "title_path": c.title_path,
                        "score": c.score,
                    }
                    for c in chunks
                ],
                generated_at=datetime.now().isoformat(),
            )
        except json.JSONDecodeError:
            # JSON 解析失败，使用降级答案
            return self._fallback_answer_from_chunks(chunks)

    def _fallback_answer(
        self,
        query: str,
        chunks: list[ScoredChunk],
    ) -> AnswerResult:
        """降级答案生成。

        当 LLM 调用失败时，直接拼接切片内容作为答案。

        Args:
            query: 用户问题
            chunks: 切片列表

        Returns:
            AnswerResult
        """
        if not chunks:
            return AnswerResult(
                answer="抱歉，暂无相关信息。",
                sources=[],
                generated_at=datetime.now().isoformat(),
            )
        return self._fallback_answer_from_chunks(chunks)

    def _fallback_answer_from_chunks(
        self,
        chunks: list[ScoredChunk],
    ) -> AnswerResult:
        """从切片生成降级答案。

        Args:
            chunks: 切片列表

        Returns:
            AnswerResult
        """
        answers = []
        for chunk in chunks:
            answers.append(
                f"[来源：{chunk.title_path}]\n{chunk.content[:300]}..."
            )

        return AnswerResult(
            answer="\n\n".join(answers),
            sources=[
                {
                    "chunk_id": c.chunk_id,
                    "title_path": c.title_path,
                    "score": c.score,
                }
                for c in chunks
            ],
            generated_at=datetime.now().isoformat(),
        )
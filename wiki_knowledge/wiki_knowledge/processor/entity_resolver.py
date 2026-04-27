# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 实体对齐与冲突处理器

处理新实体与现有实体的匹配、裁决和存储。

Author: lhx
Date: 2026-04-27
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ResolutionType(Enum):
    """裁决结果类型。"""
    ALIAS = "alias"           # 自动对齐：置信度 >= 0.85
    SOFT_LINK = "soft_link"   # 软关联待审核：0.6 <= 置信度 < 0.85
    NEW = "new"               # 独立：置信度 < 0.6
    RELATED = "related"       # 关联：建立相关链接（不变）


@dataclass
class ResolutionResult:
    """实体裁决结果。

    Attributes:
        original_name: 原始实体名
        resolution_type: 裁决类型
        kg_id: 关联的知识节点ID（新或已有）
        confidence: 置信度 (0-1)
        pending_review: 是否待审核（仅 SOFT_LINK 时为 True）
    """
    original_name: str
    resolution_type: ResolutionType
    kg_id: str
    confidence: float
    pending_review: bool = False


class EntityResolver:
    """实体对齐与冲突处理器。

    当提取出新实体时，执行候选筛选和 LLM 裁决。

    裁决规则：
    - S >= 0.85：自动对齐，合并到现有实体的同义词库
    - 0.6 <= S < 0.85：软关联，标记待审核
    - S < 0.6：判定为新实体，创建独立的 kg_id

    Methods:
        resolve: 裁决新实体
        _candidate_filter: 候选筛选
        _llm_judge: LLM 裁决
        _call_llm: 调用 LLM 服务
    """

    # LLM 裁决 Prompt
    JUDGE_PROMPT = """## Task
对比两个实体，判断它们是否等价。

实体 A：{entity_a_name}
定义：{entity_a_def}

实体 B：{entity_b_name}
定义：{entity_b_def}

## Evaluation Rules
1. 全等关系（如 Client 和 客户端）-> 置信度 >= 0.9
2. 包含关系（如 支付 和 微信支付）-> 置信度 0.6-0.7
3. 语义相关但对象不同 -> 置信度 < 0.3

## Output Format
JSON格式（不包含任何解释性文字）：
{{
  "confidence": 0.0-1.0,
  "reason": "判断理由"
}}"""

    # 裁决阈值
    THRESHOLD_AUTO_ALIGN = 0.85  # 自动对齐
    THRESHOLD_SOFT_LINK = 0.6    # 软关联（需人工审核）
    MAX_CANDIDATES = 10          # Top N 候选

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

    async def resolve(
        self,
        entity_name: str,
        entity_def: str,
        candidates: list[dict]
    ) -> ResolutionResult:
        """裁决新实体。

        Args:
            entity_name: 待裁决的实体名
            entity_def: 实体定义（来自切片内容）
            candidates: 候选实体列表（从别名索引查询）

        Returns:
            ResolutionResult：裁决结果
        """
        # 如果没有候选实体，直接创建新节点
        if not candidates:
            return ResolutionResult(
                original_name=entity_name,
                resolution_type=ResolutionType.NEW,
                kg_id="",  # 需要调用方创建
                confidence=0.0,
                pending_review=False
            )

        # 获取最佳候选的置信度
        best_candidate = candidates[0]
        confidence, _ = await self._llm_judge(
            entity_a=(entity_name, entity_def),
            entity_b=(best_candidate["name"], best_candidate.get("description", ""))
        )

        # 根据置信度确定裁决类型
        if confidence >= self.THRESHOLD_AUTO_ALIGN:
            return ResolutionResult(
                original_name=entity_name,
                resolution_type=ResolutionType.ALIAS,
                kg_id=best_candidate["kg_id"],
                confidence=confidence,
                pending_review=False
            )
        elif confidence >= self.THRESHOLD_SOFT_LINK:
            return ResolutionResult(
                original_name=entity_name,
                resolution_type=ResolutionType.SOFT_LINK,
                kg_id=best_candidate["kg_id"],
                confidence=confidence,
                pending_review=True
            )
        else:
            return ResolutionResult(
                original_name=entity_name,
                resolution_type=ResolutionType.NEW,
                kg_id="",
                confidence=confidence,
                pending_review=False
            )

    async def _candidate_filter(self, entity_name: str) -> list[dict]:
        """候选筛选。

        在别名索引中检索名称相似或已有同义词覆盖的候选实体。

        Args:
            entity_name: 实体名

        Returns:
            Top N 候选实体列表，每个包含 kg_id, name, description
        """
        # TODO: 实现 MongoDB 查询 Alias_Index
        # 实现逻辑：从 alias_index 表查询名称相似或同义词匹配的候选
        return []

    async def _llm_judge(
        self,
        entity_a: tuple[str, str],
        entity_b: tuple[str, str]
    ) -> tuple[float, str]:
        """LLM 裁决。

        Args:
            entity_a: (名称, 定义)
            entity_b: (名称, 定义)

        Returns:
            (置信度, 判断理由)
        """
        prompt = self.JUDGE_PROMPT.format(
            entity_a_name=entity_a[0],
            entity_a_def=entity_a[1],
            entity_b_name=entity_b[0],
            entity_b_def=entity_b[1]
        )

        response = await self._call_llm(prompt)

        try:
            result = json.loads(response)
            return result.get("confidence", 0.0), result.get("reason", "")
        except json.JSONDecodeError:
            return 0.0, "JSON 解析失败"
# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 动作过滤与排序

根据动作词过滤不相关切片，按权重排序返回。

Author: lhx
Date: 2026-04-27
"""

from dataclasses import dataclass
from typing import Optional

from app.service.wiki_knowledge.retrieval.multi_matcher import RetrievalCandidate


@dataclass
class ScoredChunk:
    """带权重的切片。

    Attributes:
        chunk_id: 切片唯一标识
        title_path: 标题路径
        content: 切片内容
        score: 综合分数（基础分 + 动作词加权）
        match_type: 匹配类型（path_match / entity_navigate）
    """
    chunk_id: str
    title_path: str
    content: str
    score: float
    match_type: str


class ActionFilter:
    """动作粗筛器。

    根据动作词对检索候选切片进行过滤和排序。
    动作词出现在 title_path 中权重高于出现在 content 中。

    Methods:
        filter_and_rank: 根据动作词过滤并排序切片
        _calculate_action_score: 计算动作词匹配分数
    """

    # 动作词列表
    ACTION_WORDS = [
        "如何", "怎么", "怎样", "查询", "获取", "设置", "配置",
        "创建", "删除", "更新", "修改", "使用", "调用", "请求",
        "安装", "部署", "启动", "停止", "重启", "连接", "登录",
        "注册", "认证", "授权", "验证", "编译", "运行", "调试",
        "解决", "处理", "排查", "检查", "开启", "关闭", "启用", "禁用",
    ]

    # 动作词加权因子
    ACTION_TITLE_WEIGHT = 0.3   # 动作词出现在 title_path 中的加权
    ACTION_CONTENT_WEIGHT = 0.1  # 动作词出现在 content 中的加权

    def filter_and_rank(
        self,
        candidates: list[RetrievalCandidate],
        action: str,
        limit: int = 10,
    ) -> list[ScoredChunk]:
        """根据动作词过滤并排序切片。

        Args:
            candidates: 检索候选列表
            action: 动作词
            limit: 返回结果数量限制

        Returns:
            排序后的切片列表
        """
        if not candidates:
            return []

        # 如果没有动作词，直接按分数排序返回
        if not action:
            scored = [
                ScoredChunk(
                    chunk_id=c.chunk_id,
                    title_path=c.title_path,
                    content=c.content,
                    score=c.score,
                    match_type=c.match_type,
                )
                for c in candidates
            ]
            scored.sort(key=lambda x: x.score, reverse=True)
            return scored[:limit]

        # 计算动作词加权分数
        scored_chunks = []
        for candidate in candidates:
            action_score = self._calculate_action_score(candidate, action)
            final_score = candidate.score + action_score

            scored_chunks.append(
                ScoredChunk(
                    chunk_id=candidate.chunk_id,
                    title_path=candidate.title_path,
                    content=candidate.content,
                    score=final_score,
                    match_type=candidate.match_type,
                )
            )

        # 按分数降序排序
        scored_chunks.sort(key=lambda x: x.score, reverse=True)
        return scored_chunks[:limit]

    def _calculate_action_score(
        self,
        candidate: RetrievalCandidate,
        action: str,
    ) -> float:
        """计算动作词匹配分数。

        动作词出现在 title_path 中权重高于出现在 content 中。

        Args:
            candidate: 检索候选
            action: 动作词

        Returns:
            动作词加权分数
        """
        if not action:
            return 0.0

        score = 0.0

        # 检查动作词是否出现在 title_path 中
        if action in candidate.title_path:
            score += self.ACTION_TITLE_WEIGHT

        # 检查动作词是否出现在 content 中
        if action in candidate.content:
            score += self.ACTION_CONTENT_WEIGHT

        return score
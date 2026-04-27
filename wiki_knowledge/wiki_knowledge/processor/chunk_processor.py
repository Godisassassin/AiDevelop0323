# -*- coding: utf-8 -*-
"""
Wiki 知识库 - 知识切片处理器

将 Markdown 文档按标题层级切分为结构化切片，提取上下文信息。

Author: lhx
Date: 2026-04-27
"""

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChunkResult:
    """切片结果。

    Attributes:
        chunk_id: 切片唯一标识
        doc_id: 文档ID
        title_path: 标题路径（如 "第一章 > 第一节 > 小节"）
        content: 切片内容（不含标题）
        summary: 摘要（取内容前100字符）
        parent_title: 父级标题
        sibling_titles: 同级标题列表
    """
    chunk_id: str
    doc_id: int
    title_path: str
    content: str
    summary: str = ""
    parent_title: Optional[str] = None
    sibling_titles: list[str] = field(default_factory=list)


class WikiChunkProcessor:
    """知识切片处理器。

    将 Markdown 文档按 H1-H4 标题切分为结构化切片。
    每个切片包含标题路径、父级标题、同级标题等上下文信息。

    Methods:
        process: 处理 Markdown 文档，返回切片列表
        _split_by_headers: 按标题切分文档
        _extract_title_info: 提取标题路径和上下文
        _generate_chunk_id: 生成切片唯一ID
    """

    # 标题级别正则表达式
    HEADER_PATTERN = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)

    def __init__(self):
        """初始化处理器。"""
        pass

    def process(self, markdown_content: str, doc_id: int) -> list[ChunkResult]:
        """处理 Markdown 文档，返回切片列表。

        Args:
            markdown_content: Markdown 格式的文档内容
            doc_id: 文档唯一标识

        Returns:
            ChunkResult 列表
        """
        if not markdown_content or not markdown_content.strip():
            return []

        # 按标题切分文档
        sections = self._split_by_headers(markdown_content)
        if not sections:
            # 无标题，整个文档作为一个切片
            return [
                ChunkResult(
                    chunk_id=self._generate_chunk_id(),
                    doc_id=doc_id,
                    title_path="",
                    content=markdown_content.strip(),
                    summary=self._generate_summary(markdown_content),
                )
            ]

        # 提取每个切片的上下文信息
        chunks = []
        for i, section in enumerate(sections):
            level = section["level"]
            title = section["title"]
            content = section["content"]

            # 构建标题路径
            title_path = self._build_title_path(sections, i)

            # 提取父级标题
            parent_title = self._get_parent_title(sections, i)

            # 提取同级标题
            sibling_titles = self._get_sibling_titles(sections, i)

            chunks.append(
                ChunkResult(
                    chunk_id=self._generate_chunk_id(),
                    doc_id=doc_id,
                    title_path=title_path,
                    content=content.strip() if content else "",
                    summary=self._generate_summary(content) if content else "",
                    parent_title=parent_title,
                    sibling_titles=sibling_titles,
                )
            )

        return chunks

    def _split_by_headers(self, content: str) -> list[dict]:
        """按标题切分文档。

        Args:
            content: Markdown 文档内容

        Returns:
            包含 level, title, content 的字典列表
        """
        sections = []
        lines = content.split("\n")

        # 找到所有标题的位置
        headers = []
        for i, line in enumerate(lines):
            match = self.HEADER_PATTERN.match(line)
            if match:
                headers.append({"index": i, "level": len(match.group(1)), "title": match.group(2).strip()})

        if not headers:
            return []

        # 提取每个标题下的内容
        for i, header in enumerate(headers):
            start_index = header["index"]
            # 下一个标题的开始位置（或者文档末尾）
            if i + 1 < len(headers):
                end_index = headers[i + 1]["index"]
            else:
                end_index = len(lines)

            # 提取标题下的内容（不含标题行）
            content_lines = lines[start_index + 1:end_index]
            section_content = "\n".join(content_lines).strip()

            sections.append(
                {
                    "level": header["level"],
                    "title": header["title"],
                    "content": section_content,
                }
            )

        return sections

    def _build_title_path(self, sections: list[dict], current_index: int) -> str:
        """构建标题路径。

        Args:
            sections: 所有章节列表
            current_index: 当前章节索引

        Returns:
            标题路径（如 "第一章 > 第一节 > 小节"）
        """
        current = sections[current_index]
        current_level = current["level"]
        path_titles = [current["title"]]

        # 向上查找父级标题
        for i in range(current_index - 1, -1, -1):
            if sections[i]["level"] < current_level:
                path_titles.insert(0, sections[i]["title"])
                current_level = sections[i]["level"]

        return " > ".join(path_titles)

    def _get_parent_title(self, sections: list[dict], current_index: int) -> Optional[str]:
        """获取父级标题（直接所属标题）。

        对于切片所属的标题：
        - H1: 返回 None（无父级）
        - H2+: 返回直接所属的 H(n-1) 标题

        Args:
            sections: 所有章节列表
            current_index: 当前章节索引

        Returns:
            直接所属标题，若无则返回 None
        """
        current = sections[current_index]
        current_level = current["level"]

        # H1 没有父级标题
        if current_level == 1:
            return None

        # 向上查找最近的高级别标题（直接所属的上一级）
        for i in range(current_index - 1, -1, -1):
            if sections[i]["level"] < current_level:
                return sections[i]["title"]

        return None

    def _get_sibling_titles(self, sections: list[dict], current_index: int) -> list[str]:
        """获取同级标题列表。

        Args:
            sections: 所有章节列表
            current_index: 当前章节索引

        Returns:
            同级标题列表（不含当前标题）
        """
        current = sections[current_index]
        current_level = current["level"]

        siblings = []
        for i, section in enumerate(sections):
            if i != current_index and section["level"] == current_level:
                siblings.append(section["title"])

        return siblings

    def _generate_chunk_id(self) -> str:
        """生成切片唯一ID。

        Returns:
            UUID 格式的字符串
        """
        return str(uuid.uuid4())

    def _generate_summary(self, content: str, max_length: int = 100) -> str:
        """生成摘要。

        Args:
            content: 内容
            max_length: 最大长度

        Returns:
            摘要字符串
        """
        if not content:
            return ""
        # 去除多余空白字符
        clean_content = re.sub(r"\s+", " ", content.strip())
        if len(clean_content) <= max_length:
            return clean_content
        return clean_content[:max_length] + "..."

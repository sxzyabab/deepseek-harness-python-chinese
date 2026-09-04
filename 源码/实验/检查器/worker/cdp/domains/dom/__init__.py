"""Cordis 语义 DOM 域导出。"""
#对齐上游 worker/cdp/domains/dom/index.ts

from .模型 import Cordis_Dom后端#DOM模型
from .会话 import Cordis_Dom会话#DOM会话

__all__=['Cordis_Dom后端','Cordis_Dom会话']#仅中文公开名

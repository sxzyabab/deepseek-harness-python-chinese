"""markdown 子包入口。

对齐上游 `ui-primitives/src/markdown/` 本波已迁组件。公开面仅中文名。
"""
from .消息文本 import 消息文本#字面文本
from .代码块 import 代码块#代码面
from .json块 import json块,最大字符,默认截断标签#JSON 块
from .Markdown文本 import Markdown文本,定稿渲染,流式渲染器#助手 Markdown
from .渲染 import (#mdast 渲染器
    建引用目标,收集引用目标,渲染块们,包块子节点,渲染脚注区,
)#渲染
from .解析 import 解析GFM,解析GFM含数学,装载流式解析,装载定稿解析#文法
from .增量 import 增量Markdown解析器,未稳定尾部块数#增量
from .纯文本 import 抽取Markdown纯文本#纯文本
from .katex import 渲染TeX到树,装载TeX渲染#KaTeX

__all__=[#仅中文公开名
    '消息文本','代码块','json块','最大字符','默认截断标签','Markdown文本',
    '定稿渲染','流式渲染器','建引用目标','收集引用目标','渲染块们',
    '包块子节点','渲染脚注区','解析GFM','解析GFM含数学','装载流式解析',
    '装载定稿解析','增量Markdown解析器','未稳定尾部块数','抽取Markdown纯文本',
    '渲染TeX到树','装载TeX渲染',
]#公开面

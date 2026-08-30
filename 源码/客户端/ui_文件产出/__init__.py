"""交付物插件，节点半边。

对齐上游 `@deepseek-ai/dsh-client-ui-deliverables`。公开面仅中文名。登记最终回复格式引导，让浏览器半边能识别最终回复里的文件引用。
"""

__all__=['注入','应用']#仅中文公开名

注入=['systemPrompt']#依赖系统提示词服务
文件引用引导='When you successfully create or modify files, mention the primary outputs in your final response. '+('To make those and any other changed-file references clickable in Web, format them as Markdown inline code using the exact file-tool path, or a basename when unique among the files changed in that turn.')#与浏览器渲染器配对的模型引导（字面量不翻译）

def 应用(上下文):#安装交付物插件
    """为本包发出的文件引用渲染器登记模型引导。"""
    上下文.systemPrompt.section({#登记最终回复文件引用段落
        'name':'ui:deliverable-file-references',#段落名，与浏览器渲染器配对
        'order':190,#插入顺序
        'text':文件引用引导,#稳定的最终回复格式引导
    })#结束 section

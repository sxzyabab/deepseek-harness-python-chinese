"""DeepSeek Anthropic 兼容 Messages API 的提供方私有线路类型。可引用结果项与引用摘录分块到达；提供方按 URL 拼接。这些类型不依赖 ctx.llm。"""

搜索结果项字段=('type','url','title','page_age')#web_search_tool_result 块里的一条 web_search_result：类型标签、URL、可选标题、页面新旧（映射到 publishedAt）
工具结果块字段=('type','content')#web_search_tool_result 内容块：固定 type，可选可引用结果项列表
引用位置字段=('type','url','cited_text')#text 块里的一处引用：可选类型、URL、被引文本
文本块字段=('type','text','citations')#text 内容块：固定 type=text、可选散文、按 URL 的引用列表
内容块类型=('web_search_tool_result','text')#本提供方消费的内容块判别；其余以 type 字段放过
成功信封字段=('content',)#Messages 成功信封：可选内容块列表
错误信封字段=('error','message')#Messages 错误信封：嵌套或字符串 error，或顶层 message（尽力而为；字段会变）

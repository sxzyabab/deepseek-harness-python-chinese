"""Exa 搜索 API（`POST https://api.exa.ai/search`）的线路类型。仅类型——无运行时代码。Exa 返回扁平的 `results[]`；每条带 URL、可选标题、可选 `publishedDate`，以及（请求了高亮时）由显著句子组成的 `highlights[]`。"""
Exa搜索请求字段=('query','type','numResults','contents')#发往 Exa 搜索端点的请求体字段
Exa结果字段=('url','title','publishedDate','highlights')#扁平 results[] 中一条的字段
Exa搜索响应字段=('results',)#Exa 成功信封字段
Exa错误字段=('error','message')#Exa 错误信封字段（尽力而为；字段随失败变化）
检索模式=('auto','keyword','neural')#检索模式：关键词、神经（嵌入）或自动（由 Exa 决定）

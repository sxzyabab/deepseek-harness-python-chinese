"""Perplexity 搜索 API（`POST https://api.perplexity.ai/chat/completions`，OpenAI 兼容聊天形态）的线路类型。结果优先用结构化的 `search_results`，回退到仅 URL 的 `citations`；提供方私有线路形态不依赖 `ctx.llm`。"""
Perplexity请求字段=('model','messages')#发往 Perplexity chat-completions 端点的请求体字段
Perplexity搜索结果字段=('url','title','snippet','date')#一条结构化搜索结果（优先引用形态）字段
Perplexity响应字段=('choices','search_results','citations')#Perplexity 成功信封字段
Perplexity错误字段=('error','message')#Perplexity 错误信封字段（尽力而为；字段会变）
新近窗口=('day','week','month','year')#search_recency_filter 新近窗口值

"""内部桥接为捕获的 fetch 所携带的观测主题名。

对齐上游 `shared/bridge/messages/network.ts`。公开面仅中文名。
"""
__all__=['请求主题们']#仅中文公开名

请求主题们=(#fetch主题列表
    'fetch/start','fetch/request-body-chunk','fetch/request-body-end',#请求侧
    'fetch/response','fetch/response-body-chunk','fetch/end','fetch/error',#响应侧
)#冻结字面量

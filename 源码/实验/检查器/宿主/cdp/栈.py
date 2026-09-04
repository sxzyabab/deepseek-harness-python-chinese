"""Host 栈与 call-frame 数据仍由 Worker 侧 Node inspector session 拥有。

对齐上游 `host/cdp/stack.ts`。公开面仅中文名。
"""
__all__=['宿主cdp桥原因']#仅中文公开名

宿主cdp桥原因='Host Runtime is attached directly from the Inspector Worker'#拒绝原因

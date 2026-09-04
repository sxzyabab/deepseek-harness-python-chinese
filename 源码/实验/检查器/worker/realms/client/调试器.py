"""在有安全暂停的页面代理出现前，显式的 Client 调试器能力。"""
#对齐上游 worker/realms/client/debugger.ts

__all__=['Client调试器能力']#仅中文公开名

def Client调试器能力():#Client调试器能力
    """报告不可用的 Client 调试器后端。"""
    return {'state':'unsupported','reason':'Client native debugging is unavailable'}#不支持

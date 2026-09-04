"""Host 原生脚本身份到规范化源与调试器值的转换。"""
#对齐上游 worker/realms/host/scripts.ts

__all__=['Host脚本键']#仅中文公开名

def Host脚本键(值):#Host脚本键
    """将 Node inspector 脚本 id 转换到 realm 后端身份命名空间。"""
    return 值#包装id（品牌由调用约定保证）

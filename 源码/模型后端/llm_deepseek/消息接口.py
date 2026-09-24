"""共享 DeepSeek Messages API 端点与头策略。"""

__all__=['消息文件测试通道','消息接口根']

消息文件测试通道='files-api-2025-04-14'

def 消息接口根(基址):
    """解析 API 根，不重复显式版本路径。"""
    根=基址.rstrip('/')
    from urllib.parse import urlparse
    路径=urlparse(根).path
    if 路径.endswith('/v1'):
        return 根
    return 根+'/v1'

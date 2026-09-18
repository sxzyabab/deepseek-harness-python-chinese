"""共享 DeepSeek Messages API 端点与请求头政策。"""
from urllib.parse import urlparse as 解析网址#解析路径

__all__=('消息文件测试版头','消息接口根',)#仅中文公开名

#常量
消息文件测试版头='files-api-2025-04-14'#Messages 文件操作与文件引用图请求所需的显式 opt-in

#工具
def 消息接口根(基址):
    """解析 API 根，不重复显式提供方版本路径。"""
    根=基址.rstrip('/')#去尾斜杠
    路径=解析网址(根).path#路径
    if 路径.endswith('/v1'):#已带版本
        return 根#原样
    return f'{根}/v1'#补上 /v1

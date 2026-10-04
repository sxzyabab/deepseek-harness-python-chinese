from ..llm.异常 import 语言模型错误 as 大模型错误#Files 错误基类

__all__=('文件解析失败','深求配置错误','深求文件错误','非法上传索引错误')#仅中文公开名

class 文件解析失败(Exception):
    '上传失败，整请求可回退内联'
    def __init__(自身,原因=None):
        '记下原因'
        super().__init__('DeepSeek Files API could not resolve a request image.')
        自身.name='FileResolutionFailure'
        if 原因 is not None:
            自身.__cause__=原因

class 深求配置错误(Exception):
    'llm-deepseek 配置校验失败'

class 深求文件错误(大模型错误):
    'Files API 操作失败，保留 HTTP 状态供恢复政策'
    def __init__(自身,消息,状态,详情):
        '记下可读失败、状态与分类详情'
        if 状态==401 or 状态==403:
            码='AUTH'
        elif 状态==429:
            码='RATE_LIMIT'
        elif 状态>=500:
            码='SERVER'
        else:
            码='FILES_API'
        super().__init__(消息,码,{'status':状态})
        自身.name='DeepSeekFilesError'
        自身.detail=详情

class 非法上传索引错误(Exception):
    '本地索引损坏'

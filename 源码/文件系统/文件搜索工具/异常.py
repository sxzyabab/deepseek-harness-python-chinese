from ...模型后端.llm.异常 import 装备错误#带类型的Harness错误基类

class 搜索工具错误(Exception):#参数校验失败
    '搜索工具入参非法；详情保持英文线协议原文'
    def __init__(自身,消息):#记下英文消息
        '用原样英文消息构造'
        super().__init__(消息)#英文消息

class 搜索错误(装备错误):#搜索带类型错误
    """带类型的搜索失败。扩展装备错误，因此携带稳定的搜索错误码并链接 cause；工具注册表在 isError 结果上暴露 { name, code }，以便重试/权限/UI 层无需解析消息即可分支。

    稳定错误码：SEARCH_INVALID_PATTERN — ripgrep 拒绝了正则或 glob；SEARCH_FAILED — 搜索无法运行或其输出无法解析；SEARCH_RAW_OUTPUT_OVERFLOW — 原始 rg 输出超出 rawOutputMaxBytes；SEARCH_ABORTED — 协作工具超时或调用方取消
    """
    def __init__(自身,消息,码,选项=None):#记下稳定搜索错误码
        '记下稳定搜索错误码，并把 cause 链到本错误'
        super().__init__(消息,码,选项)#交给装备错误保存消息、错误码与cause
        自身.code=码#再写下本类的错误码字段
        自身.name='SearchError'#固定错误名

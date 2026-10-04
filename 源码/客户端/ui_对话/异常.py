class 对话错误(Exception):
    '审批回执与槽面失败'
    def __init__(自身,消息,原因=None):
        '记下英文消息与可选结构原因'
        super().__init__(消息)#消息原样英文
        自身.reason=原因#结构原因

class 不支持图片媒体类型(Exception):
    '浏览器声明了不支持的图片类型，由 UI 边界本地化'
    def __init__(自身,媒体类型):
        '保存声明值'
        super().__init__('unsupported image media type: '+(媒体类型 or '(empty)'))#消息
        自身.mediaType=媒体类型#声明值

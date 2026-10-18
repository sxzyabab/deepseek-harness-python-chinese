'采集失败。页面上的句子在故障文本里，不从这里取'

__all__=['录制错误']#仅中文公开名


class 录制错误(Exception):
    '采集失败。kind 为 unavailable、permission、empty、cancelled、interrupted、deviceMissing'
    def __init__(自身,kind):
        '记下 kind，name 保持 RecordingError，供调用方辨认'
        super().__init__(kind)#消息就是 kind
        自身.kind=kind#稳定种类
        自身.name='RecordingError'#与上游错误名一致

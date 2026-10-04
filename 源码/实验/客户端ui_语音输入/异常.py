__all__=('录制错误',)#仅中文公开名

class 录制错误(Exception):
    '采集失败，文案键由调用方按 kind 翻译'
    def __init__(自身,kind):
        'kind 为 unavailable / permission / empty / cancelled / interrupted'
        super().__init__(kind)
        自身.kind=kind
        自身.name='RecordingError'

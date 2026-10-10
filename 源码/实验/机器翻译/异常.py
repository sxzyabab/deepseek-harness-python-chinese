'翻译失败诊断，不含提交文本和响应正文'
__all__=['翻译错误']

class 翻译错误(Exception):
    '提供方失败，或请求、响应超出配置上限'
    def __init__(自身,码,消息):
        '码与文案分开；码保持原文，文案给人看'
        super().__init__(消息)
        自身.name='TranslationError'
        自身.code=码

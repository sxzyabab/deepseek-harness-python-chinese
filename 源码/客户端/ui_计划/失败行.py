__all__=['计划失败行']#仅中文公开名

def 计划失败行(翻译,失败):
    """用当前 locale 解释失败的计划读取。"""
    码=失败['code']#错误码
    if 码=='plan/invalid-address':#地址无效
        return 翻译('preview.invalidAddress')#文案
    if 码=='plan/unavailable':#历史不可用
        return 翻译('preview.historyUnavailable')#文案
    if 码=='plan/not-found':#未找到
        return 翻译('preview.notFound')#文案
    return 失败['message']#原样诊断

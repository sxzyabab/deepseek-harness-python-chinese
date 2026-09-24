"""准备插件贡献的请求字段，并在 HTTP 接受后提交投递。"""
import json
from ..llm import 大模型错误

__all__=['准备请求扩展']

def 准备请求扩展(体,选项,准备):
    """合并贡献且不替换 Messages 字段。准备与接纳失败报 REQUEST_EXTENSION。"""
    try:
        请求=dict(选项)
        请求['body']=体
        扩展=准备(请求)
    except Exception as 错误:
        raise 大模型错误('DeepSeek request extension preparation failed','REQUEST_EXTENSION',{'cause':错误})
    for 字段 in 扩展['fields'].keys():
        if 字段 in 体:
            raise 大模型错误('DeepSeek request extension field '+json.dumps(字段,ensure_ascii=False)+' collides with the base request','REQUEST_EXTENSION')
    合并=dict(体)
    合并.update(扩展['fields'])
    def 接纳():
        """HTTP 成功后提交贡献。"""
        try:
            扩展['accept']()
        except Exception as 错误:
            raise 大模型错误('DeepSeek request extension acceptance failed','REQUEST_EXTENSION',{'cause':错误})
    return {'payload':json.dumps(合并,ensure_ascii=False,separators=(',',':'),allow_nan=False),'accept':接纳}

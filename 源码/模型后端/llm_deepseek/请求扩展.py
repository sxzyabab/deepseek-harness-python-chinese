'准备插件贡献的请求字段，并在 HTTP 接受后提交投递'
import json
from ...基础设施.通用工具.序列化编码 import 紧凑json编码
from ..llm.异常 import 语言模型错误 as 大模型错误,错误链#大模型错误与错误链

__all__=['准备请求扩展']

def 准备请求扩展(体,选项,准备,被省略=None,未接纳=None):
    '合并贡献且不替换 Messages 字段。准备失败报 REQUEST_EXTENSION；序列化失败则只发基础请求'
    try:
        请求=dict(选项)
        请求['body']=体
        扩展=准备(请求)
    except Exception as 错误:
        raise 大模型错误('DeepSeek request extension preparation failed: '+错误链(错误),'REQUEST_EXTENSION',{'cause':错误})
    字段列表=list(扩展['fields'].keys())
    for 字段 in 字段列表:
        if 字段 in 体:
            raise 大模型错误('DeepSeek request extension field '+json.dumps(字段,ensure_ascii=False)+' collides with the base request','REQUEST_EXTENSION')
    try:
        合并=dict(体)
        合并.update(扩展['fields'])
        载荷=紧凑json编码(合并)
    except Exception as 错误:
        基础=紧凑json编码(体)
        if 被省略 is not None:
            被省略(字段列表,错误)
        def 空接纳():
            '序列化失败则不提交，贡献方下次再发'
            return None
        return {'payload':基础,'accept':空接纳}
    def 接纳():
        'HTTP 成功后提交贡献；接纳失败只报告，不让请求失败'
        try:
            扩展['accept']()
        except Exception as 错误:
            if 未接纳 is not None:
                未接纳(错误)
    return {'payload':载荷,'accept':接纳}

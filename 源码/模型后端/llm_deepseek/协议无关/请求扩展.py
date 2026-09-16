"""准备插件贡献的请求字段，并在 HTTP 接纳后提交投递。"""
import json#JSON 编码
from ...llm import 大模型错误#LLM 错误

__all__=('准备请求扩展',)#仅中文公开名

def 准备请求扩展(体,选项,准备):#合并扩展字段
    """合并贡献且不替换协议自有字段。准备与接纳失败在各 DeepSeek 协议上共用同一错误类。"""
    try:#准备
        请求=dict(选项)#身份、用途、取消
        请求['body']=体#序列化后的协议请求
        扩展=准备(请求)#贡献注册表
    except Exception as 错误:#准备失败
        raise 大模型错误('DeepSeek request extension preparation failed','REQUEST_EXTENSION',{'cause':错误}) from 错误#准备失败
    for 字段 in 扩展['fields']:#逐字段
        if 字段 in 体:#与基请求冲突
            raise 大模型错误('DeepSeek request extension field '+repr(字段)+' collides with the base request','REQUEST_EXTENSION')#冲突
    合并=dict(体)#基请求
    合并.update(扩展['fields'])#叠贡献
    载荷=json.dumps(合并,ensure_ascii=False,separators=(',',':'),allow_nan=False)#HTTP 载荷
    def 接纳():#HTTP 成功后提交
        """仅在成功 HTTP 响应后调用。"""
        try:#接纳
            扩展['accept']()#提交投递
        except Exception as 错误:#接纳失败
            raise 大模型错误('DeepSeek request extension acceptance failed','REQUEST_EXTENSION',{'cause':错误}) from 错误#接纳失败
    return {'payload':载荷,'accept':接纳}#载荷与提交

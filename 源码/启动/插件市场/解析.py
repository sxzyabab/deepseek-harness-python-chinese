'把取回的索引正文解码、解析并按格式 1 校验'
import json#JSON
from ...工具.插件市场索引 import 解析市场索引,市场索引错误#格式校验

__all__=['解析索引正文']#仅中文公开名

def 解析索引正文(正文,网址):
    '严格 UTF-8 解码后解析 JSON 并校验。失败时 path 为 $ 或违规值的 JSON 路径'
    try:#解码
        文本=正文.decode('utf-8')#严格 UTF-8；非法字节抛 UnicodeDecodeError
    except UnicodeDecodeError:#仅畸形 UTF-8
        return {'ok':False,'path':'$','reason':'must be UTF-8','message':'must be UTF-8'}#比对用原文
    try:#解析
        文档值=json.loads(文本)#JSON
    except json.JSONDecodeError as 错误:#不是 JSON
        理由='must be JSON: '+错误.msg#诊断原样
        return {'ok':False,'path':'$','reason':理由,'message':理由}#失败
    try:#校验
        return {'ok':True,'index':解析市场索引(文档值,网址)}#通过
    except 市场索引错误 as 错误:#格式违规
        return {'ok':False,'path':错误.path,'reason':错误.reason,'message':错误.message}#首条违规

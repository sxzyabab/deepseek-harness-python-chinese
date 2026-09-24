"""ACP 线路内容准入与投影，由 ACP 适配器拥有。"""
import re
from base64 import b64encode as 编码基64,b64decode as 解码基64
from ...附件.附件 import 是否图像准入错误
from ...工具.超时 import 若已中止则抛出
import json

__all__=['ACP内容错误','支持ACP图片提示','接纳ACP提示','助手块转ACP']

图像媒体类型=('image/png','image/jpeg','image/webp','image/gif')
规范基64=re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$')

class ACP内容错误(Exception):
    """稳定 ACP 请求失败分类，不含原始二进制。"""
    def __init__(自身,消息,种类,原因=None):
        """记下无内联二进制的协议细节。"""
        super().__init__(消息)
        自身.name='AcpContentError'
        自身.kind=种类
        if 原因 is not None:
            自身.__cause__=原因

def 图像媒体(值):
    """收窄线路 MIME。"""
    return 值 if 值 in 图像媒体类型 else None

def 解码图像(块):
    """严格解码一张 ACP 内联图。"""
    媒体=图像媒体(块.get('mimeType'))
    if 媒体 is None:
        raise ACP内容错误('image mimeType must be image/png, image/jpeg, image/webp, or image/gif','invalid')
    数据=块.get('data')
    if not isinstance(数据,str) or not 规范基64.match(数据):
        raise ACP内容错误('image data must be canonical base64','invalid')
    字节=解码基64(数据)
    if 编码基64(字节).decode('ascii')!=数据:
        raise ACP内容错误('image data must be canonical base64','invalid')
    return {'data':字节,'mediaType':媒体}

def 断言图像路由(上下文,路由,信号):
    """解析精确当前路由并要求显式图像输入。"""
    提供方=None if 路由 is None else 路由.get('provider')
    模型=None if 路由 is None else 路由.get('model')
    大模型=上下文.获取服务('llm')
    if 提供方 is None or 模型 is None or 大模型 is None:
        raise ACP内容错误('the current model route could not be resolved for image input','invalid')
    try:
        信息=大模型.解析模型信息(提供方,模型,信号)
    except Exception as 错误:
        raise ACP内容错误('the current model route could not be verified for image input','internal') from 错误
    模态=信息.get('inputModalities') if isinstance(信息,dict) else None
    if 模态 is None or 'image' not in 模态:
        raise ACP内容错误('model "'+str(模型)+'" does not declare image input','invalid')

def 支持ACP图片提示(上下文,提供方,模型):
    """初始化是否可如实宣称内联图像提示。"""
    附件=上下文.获取服务('attachments')
    大模型=上下文.获取服务('llm')
    if 附件 is None or 大模型 is None or 提供方 is None or 模型 is None:
        return False
    限额=附件.图像限额
    媒体=限额['mediaTypes'] if isinstance(限额,dict) else getattr(限额,'mediaTypes',())
    if not any(项 in 图像媒体类型 for 项 in 媒体):
        return False
    try:
        信息=大模型.解析模型信息(提供方,模型)
        模态=信息.get('inputModalities') if isinstance(信息,dict) else None
        return 模态 is not None and 'image' in 模态
    except Exception:
        return False

def 资源链接文本(块):
    """基线资源链接变成核心文本词表。"""
    名=json.dumps(块.get('name'),ensure_ascii=False,separators=(',',':'),allow_nan=False)
    址=json.dumps(块.get('uri'),ensure_ascii=False,separators=(',',':'),allow_nan=False)
    return '\n[resource_link name='+名+' uri='+址+']\n'

def 接纳ACP提示(上下文,路由,提示,图像已启用,信号):
    """把 ACP 提示收成有序耐久核心内容。"""
    图像=[]
    for 块 in 提示:
        类型=块.get('type') if isinstance(块,dict) else None
        if 类型=='text' or 类型=='resource_link':
            continue
        if 类型=='image':
            if not 图像已启用:
                raise ACP内容错误('inline image prompts were not advertised by this connection','invalid')
            图像.append(解码图像(块))
            continue
        if 类型=='audio':
            raise ACP内容错误('audio prompt content is not supported','invalid')
        if 类型=='resource':
            raise ACP内容错误('embedded resource prompt content is not supported','invalid')
        raise ACP内容错误('unsupported ACP prompt content','invalid')
    引用表=[]
    if len(图像)>0:
        附件=上下文.获取服务('attachments')
        if 附件 is None:
            raise ACP内容错误('no attachment store is mounted','invalid')
        断言图像路由(上下文,路由,信号)
        若已中止则抛出(信号)
        try:
            引用表=附件.保存图像批次(图像)
        except Exception as 错误:
            if 是否图像准入错误(错误):
                raise ACP内容错误(str(错误),'invalid') from 错误
            raise ACP内容错误('unable to persist the prompt image batch','internal') from 错误
        若已中止则抛出(信号)
    内容=[]
    待文本=''
    图下标=0
    def 冲文本():
        """冲出累计文本。"""
        nonlocal 待文本
        if len(待文本)==0:
            return
        内容.append({'type':'text','text':待文本})
        待文本=''
    for 块 in 提示:
        类型=块.get('type') if isinstance(块,dict) else None
        if 类型=='text':
            待文本+=块.get('text') or ''
        elif 类型=='resource_link':
            待文本+=资源链接文本(块)
        elif 类型=='image':
            冲文本()
            内容.append({'type':'image','attachment':引用表[图下标]})
            图下标+=1
    冲文本()
    if not any(块['type']=='image' or (块['type']=='text' and 块['text'].strip()!='') for 块 in 内容):
        raise ACP内容错误('empty prompt','invalid')
    return 内容

def 助手块转ACP(上下文,块):
    """把已提交助手块译成 ACP 线路内容。"""
    if 块.get('type')=='text':
        return None if len(块.get('text') or '')==0 else {'type':'text','text':块['text']}
    if 块.get('type')!='image':
        return None
    附件=上下文.获取服务('attachments')
    if 附件 is None:
        raise ACP内容错误('cannot deliver assistant image: no attachment store is mounted','internal')
    try:
        已存=附件.读取图像(块['attachment'])
    except Exception as 错误:
        raise ACP内容错误('cannot deliver assistant image: the attachment is unavailable or corrupt','internal') from 错误
    数据=已存['data'] if isinstance(已存,dict) else 已存.data
    引用=已存['ref'] if isinstance(已存,dict) else 已存.ref
    媒体=引用['mediaType'] if isinstance(引用,dict) else 引用.mediaType
    return {'type':'image','data':编码基64(bytes(数据)).decode('ascii'),'mimeType':媒体}

"""确定性 Messages 图片准备：Files 引用与有界内联回退。"""
from ..llm import 大模型错误,内容含图片,卸载图片文案,投影卸载图片,必需图片卸载,图片卸载必需码
from .请求定价 import 深求图片请求定价,解析请求图目标

__all__=['图片定价','准备图片','内联图片','准备文件标识']

图片定价=深求图片请求定价

def 边界(连接,表示):
    """按表示形态取卸载边界。"""
    return {
        'representation':表示,
        'maxBytes':连接['maxRequestFilesBytes'] if 表示=='raw' else 连接['maxInlineRequestImageBytes'],
        'maxImages':连接['maxImagesPerRequest'],
        'byteQuantum':连接['imageOffloadByteQuantum'] if 表示=='raw' else 连接['inlineImageOffloadByteQuantum'],
        'countQuantum':连接['imageOffloadCountQuantum'],
    }

def 图片引用(块列表):
    """产出图片块上的附件引用。"""
    for 块 in 块列表:
        if 块.get('type')=='image':
            yield 块['attachment']

def 准备图片(历史,连接,模型号,附件仓,访问,信号):
    """在转成 Messages 内容前归一保留的图片引用。"""
    版本={}
    def 卸载文案(引用):
        """卸载占位。"""
        return 卸载图片文案(引用,访问(引用) if 访问 is not None else None)
    消息列表=投影卸载图片(历史,卸载文案)
    if not any(内容含图片(消息.get('content') or []) for 消息 in 消息列表):
        return 消息列表,版本
    模型=None
    for 条目 in 连接['models']:
        if 条目['id']==模型号:
            模型=条目
            break
    模态=模型['inputModalities'] if 模型 is not None and 'inputModalities' in 模型 else None
    if 模态 is None or 'image' not in 模态 or 附件仓 is None:
        raise 大模型错误('DeepSeek Messages image input requires a vision model and attachment service','UNSUPPORTED_CONTENT')
    for 消息 in 消息列表:
        角色=消息.get('role')
        if 角色!='user' and 角色!='tool' and 内容含图片(消息.get('content') or []):
            raise 大模型错误('DeepSeek Messages supports images only in user messages and tool results','UNSUPPORTED_CONTENT')
    for 消息 in 消息列表:
        for 引用 in 图片引用(消息.get('content') or []):
            标识=引用['attachmentId']
            if 标识 not in 版本:
                版本[标识]=附件仓.读取图像请求(引用,解析请求图目标(模型,引用),信号)
    断言图片可放(消息列表,版本,连接,'raw')
    return 消息列表,版本

def 内联图片(消息列表,版本,连接):
    """内联预算内要求已记录卸载。"""
    断言图片可放(消息列表,版本,连接,'base64')
    return 消息列表

def 断言图片可放(消息列表,版本,连接,表示):
    """按表示字节再计需卸载张数。"""
    def 字节(块):
        """该出现的表示字节。"""
        return 版本[块['attachment']['attachmentId']]['bytes']
    卸载张=必需图片卸载(消息列表,边界(连接,表示),字节)
    if 卸载张>0:
        raise 大模型错误(
            'DeepSeek Messages '+表示+' request images exceed the route budget; '+str(卸载张)+' more oldest occurrence(s) must be offloaded.',
            图片卸载必需码,
            {'offloadImages':卸载张},
        )

def 准备文件标识(消息列表,版本,文件):
    """把保留图解析成 Files id。"""
    标识表={}
    消息下标=0
    for 消息 in 消息列表:
        图号=0
        for 引用 in 图片引用(消息.get('content') or []):
            图号+=1
            版本项=版本[引用['attachmentId']]
            标识表[引用['attachmentId']]=文件.解析(版本项,{'message':消息下标+1,'image':图号})
        消息下标+=1
    return 标识表

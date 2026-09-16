"""确定性消息协议图准备：Files 引用与有界内联回落。"""
from ....llm import (
    内容含图片,#含图
    大模型错误,#错误
    卸载图片文案,#占位
    投影卸载图片,#投影
    必需图片卸载,#预算
    图片卸载必需码,#卸载码
)#llm 词表
from ...协议无关.请求定价 import 深求图片请求定价,解析请求图目标#定价与目标

__all__=('图片定价','准备图片','内联图片','准备文件标识')#仅中文公开名

图片定价=深求图片请求定价#再导出

def 预算(连接,表示):
    """按表示选出字节与张数界。"""
    return {
        'representation':表示,#表示
        'maxBytes':连接['maxRequestFilesBytes'] if 表示=='raw' else 连接['maxInlineRequestImageBytes'],#字节
        'maxImages':连接['maxImagesPerRequest'],#张数
        'byteQuantum':连接['imageOffloadByteQuantum'] if 表示=='raw' else 连接['inlineImageOffloadByteQuantum'],#量子
        'countQuantum':连接['imageOffloadCountQuantum'],#张数量子
    }#预算

def 图片引用序列(块列表):
    """按出现顺序让出图片引用。"""
    for 块 in 块列表:#逐块
        if 块.get('type')=='image':#图
            yield 块['attachment']#引用
        elif 块.get('type')=='tool-result':#嵌套
            yield from 图片引用序列(块.get('content') or [])#递归

def 断言图可放下(消息列表,版本表,连接,表示):
    """精确表示字节下仍超预算则要求再卸载。"""
    def 版本字节(块):#精确字节
        """取已准备版本字节。"""
        return 版本表[块['attachment']['attachmentId']]['bytes']#字节
    卸载=必需图片卸载(消息列表,预算(连接,表示),版本字节)#还需
    if 卸载>0:#超
        raise 大模型错误(
            'DeepSeek Messages '+表示+' request images exceed the route budget; '+str(卸载)+' more oldest occurrence(s) must be offloaded.',
            图片卸载必需码,
            {'offloadImages':卸载},
        )#卸载必需

def 准备图片(历史,连接,模型号,附件,访问,信号):
    """规范化保留图引用后再转换消息内容。"""
    def 占位(引用):#卸载占位
        """按当前访问生成占位。"""
        return 卸载图片文案(引用,访问(引用) if 访问 is not None else None)#占位
    消息=投影卸载图片(历史,占位)#投影
    版本表={}#id→版本
    if not any(内容含图片(项.get('content') or []) for 项 in 消息):#无图
        return {'messages':消息,'versions':版本表}#原样
    模型=None#目录
    for 条目 in 连接['models']:#逐条
        if 条目['id']==模型号:#命中
            模型=条目#记下
            break#停
    模态=模型.get('inputModalities') if 模型 is not None else None#模态
    if 模态 is None or 'image' not in 模态 or 附件 is None:#非视觉或无仓
        raise 大模型错误('DeepSeek Messages image input requires a vision model and attachment service','UNSUPPORTED_CONTENT')#需要
    for 项 in 消息:#角色
        if 项.get('role')!='user' and 内容含图片(项.get('content') or []):#非用户含图
            raise 大模型错误('DeepSeek Messages supports images only in user messages and tool results','UNSUPPORTED_CONTENT')#角色
    for 项 in 消息:#准备
        for 引用 in 图片引用序列(项.get('content') or []):#引用
            if 引用['attachmentId'] not in 版本表:#未准备
                版本表[引用['attachmentId']]=附件.读取图像请求(引用,解析请求图目标(模型,引用),信号)#准备
    断言图可放下(消息,版本表,连接,'raw')#文件预算
    return {'messages':消息,'versions':版本表}#结果

def 内联图片(消息列表,版本表,连接):
    """内联回落前要求已登录卸载。"""
    断言图可放下(消息列表,版本表,连接,'base64')#内联预算
    return 消息列表#原样

def 准备文件标识(消息列表,版本表,文件):
    """把保留图解析成 Files id，并记下每次出现。"""
    标识表={}#id→文件 id
    for 下标,消息 in enumerate(消息列表):#逐条
        图号=0#出现
        for 引用 in 图片引用序列(消息.get('content') or []):#引用
            图号+=1#序号
            版本=版本表[引用['attachmentId']]#版本
            标识表[引用['attachmentId']]=文件.解析(版本,{'message':下标+1,'image':图号})#解析
    return 标识表#标识

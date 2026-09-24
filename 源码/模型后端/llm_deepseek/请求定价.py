"""DeepSeek 路由的提供方侧请求图定价。"""
from ..llm.内容 import 卸载图片文案,请求图片句柄文案,仅文本图片文案
from ...附件.附件.请求投影 import 长边尺寸,请求图像尺寸
from .图片令牌 import 深求图片令牌,深求请求图尺寸

__all__=[
    '默认最大请求文件字节','默认每请求最大图片数','默认低细节图像素预算',
    '默认请求图最大字节','请求图最大边','解析请求图最大字节','解析请求图目标','深求图片请求定价',
]

默认最大请求文件字节=128*1024*1024
默认每请求最大图片数=600
默认低细节图像素预算=512*512
默认请求图最大字节=2*1024*1024
请求图最大边=4096

def 解析请求图最大字节(模型):
    """一条 DeepSeek 模型路由对每张请求图使用的编码字节目标。"""
    return 模型['imageMaxBytes'] if 'imageMaxBytes' in 模型 and 模型['imageMaxBytes'] is not None else 默认请求图最大字节

def 解析请求图目标(模型,源):
    """一条路由为一张源图选择的确定性请求目标。小图不放大。"""
    预算=默认低细节图像素预算 if 模型.get('imagePixelBudget')=='low' else 模型.get('imagePixelBudget')
    if 预算 is None:
        投影=深求请求图尺寸(源['width'],源['height'])
    else:
        投影=请求图像尺寸(源['width'],源['height'],预算)
    if max(投影['width'],投影['height'])>请求图最大边:
        封顶=长边尺寸(源['width'],源['height'],请求图最大边)
    else:
        封顶=投影
    结果=dict(封顶)
    结果['maxBytes']=解析请求图最大字节(模型)
    return 结果

def 仅文本价(块):
    """纯文本路由用确定性文本替换一张图。"""
    return {'visualTokens':0,'text':仅文本图片文案(块['attachment'])}

def 深求图片请求定价(连接,模型,解析访问=None):
    """从已校验连接快照构建一条 DeepSeek 路由的请求图定价。"""
    目录模型=None
    for 条目 in 连接['models']:
        if 条目['id']==模型:
            目录模型=条目
            break
    模态=目录模型['inputModalities'] if 目录模型 is not None and 'inputModalities' in 目录模型 else None
    if 模态 is None or 'image' not in 模态:
        def 定价纯文本(图列表):
            """每张都按纯文本替换。"""
            return [仅文本价(项) for 项 in 图列表]
        return {'priceImages':定价纯文本}
    def 定价视觉(图列表):
        """保留图按投影尺寸计价，卸载图按占位文本。"""
        结果=[]
        for 项 in 图列表:
            引用=项['attachment']
            if 项.get('offloaded') is True:
                访问=解析访问(引用) if 解析访问 is not None else None
                结果.append({'visualTokens':0,'text':卸载图片文案(引用,访问)})
                continue
            目标=解析请求图目标(目录模型,引用)
            访问=解析访问(引用) if 解析访问 is not None else None
            结果.append({
                'visualTokens':深求图片令牌(目标['width'],目标['height']),
                'text':请求图片句柄文案(引用,目标,访问),
            })
        return 结果
    return {'priceImages':定价视觉}

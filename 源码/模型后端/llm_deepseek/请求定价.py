"""DeepSeek 路由的提供方侧请求图定价。

对齐上游 `llm-deepseek/src/request-pricing.ts`。公开面仅中文名；无英文别名。
"""
from ..llm import (
    仅文本图片文案,#仅文本占位
    卸载图片文案,#卸载占位
    卸载图片前缀张数,#卸载前缀
    请求图片句柄文案,#句柄文案
)#导入图片文本辅助
from ...附件.附件 import 请求图像尺寸#请求图尺寸
from .图片令牌 import 深求图片令牌#图片令牌核算

__all__=(#仅中文公开名
    '默认最大请求文件字节','默认每请求最大图片数','默认请求图像素预算',
    '默认低细节图像素预算','默认请求图最大字节',
    '解析请求图政策','深求图片请求定价',
)#公开面结束

默认最大请求文件字节=128*1024*1024#默认最大请求文件字节
默认每请求最大图片数=600#默认每请求最大图片数
默认请求图像素预算=640000#默认像素预算
默认低细节图像素预算=512*512#低细节像素预算
默认请求图最大字节=1024*1024#默认最大编码字节

def 解析请求图政策(模型):#解析请求图策略
    """解析一条 DeepSeek 模型路由拥有的请求图预算。模型为目录 dict。"""
    if 模型.get('imagePixelBudget')=='low':#低细节
        最大像素=默认低细节图像素预算#低细节预算
    elif 'imagePixelBudget' in 模型 and 模型['imagePixelBudget'] is not None:#显式预算
        最大像素=模型['imagePixelBudget']#条目预算
    else:#默认
        最大像素=默认请求图像素预算#默认预算
    if 'imageMaxBytes' in 模型 and 模型['imageMaxBytes'] is not None:#显式字节
        最大字节=模型['imageMaxBytes']#条目字节
    else:#默认
        最大字节=默认请求图最大字节#默认字节
    return {'maxPixels':最大像素,'maxBytes':最大字节}#完整预算

def 仅文本价(引用):#仅文本价
    """为一仅文本路由用确定性文本替换的一次出现定价。"""
    return {'visualTokens':0,'text':仅文本图片文案(引用)}#零视觉令牌

def 深求图片请求定价(连接,模型,解析访问=None):#图片请求定价
    """从已校验连接快照为一条 DeepSeek 路由构建请求图定价。"""
    目录模型=None#目录条目
    for 条目 in 连接.get('models') or []:#逐条
        if 条目.get('id')==模型:#命中
            目录模型=条目#记下
            break#找到即停
    模态=目录模型.get('inputModalities') if 目录模型 is not None else None#输入模态
    if 模态 is None or 'image' not in 模态:#非视觉路由
        return {'priceImages':lambda 图片列表:[仅文本价(引用) for 引用 in 图片列表]}#仅文本
    政策=解析请求图政策(目录模型)#请求图政策
    def 计价(图片列表):#按出现计价
        """复现最旧优先卸载并按投影尺寸定价。"""
        卸载=卸载图片前缀张数(
            [min(引用['bytes'],政策['maxBytes']) for 引用 in 图片列表],#已表示长度
            {
                'maxBytes':连接.get('maxRequestFilesBytes'),#字节上限
                'maxImages':连接.get('maxImagesPerRequest'),#张数上限
                'byteQuantum':连接.get('imageOffloadByteQuantum'),#字节量子
                'countQuantum':连接.get('imageOffloadCountQuantum'),#张数量子
            },#预算
        )#卸载前缀
        结果=[]#定价表
        for 下标,引用 in enumerate(图片列表):#逐出现
            if 下标<卸载:#被卸载
                访问=解析访问(引用) if 解析访问 is not None else None#可选访问
                结果.append({'visualTokens':0,'text':卸载图片文案(引用,访问)})#占位
                continue#下一项
            尺寸=请求图像尺寸(引用['width'],引用['height'],政策['maxPixels'])#投影尺寸
            访问=解析访问(引用) if 解析访问 is not None else None#可选访问
            结果.append({
                'visualTokens':深求图片令牌(尺寸['width'],尺寸['height']),#视觉令牌
                'text':请求图片句柄文案(引用,尺寸,访问),#句柄
            })#保留图
        return 结果#定价表
    return {'priceImages':计价}#同步定价

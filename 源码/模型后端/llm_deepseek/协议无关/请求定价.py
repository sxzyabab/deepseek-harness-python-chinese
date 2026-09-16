"""DeepSeek 路由的提供方侧请求图定价。"""
from ...llm import (
    仅文本图片文案,#仅文本占位
    卸载图片文案,#卸载占位
    请求图片句柄文案,#句柄文案
)#导入图片文本辅助
from ....附件.附件 import 请求图像尺寸#请求图尺寸
from .图片令牌 import 长边尺寸,深求图片令牌,深求请求图尺寸#令牌与尺寸

__all__=(#仅中文公开名
    '默认最大请求文件字节','默认每请求最大图片数','默认低细节图像素预算',
    '默认请求图最大字节','请求图最大边',
    '解析请求图最大字节','解析请求图目标','深求图片请求定价',
)#公开面结束

默认最大请求文件字节=128*1024*1024#每请求累计文件引用图字节上限
默认每请求最大图片数=600#提供方请求图张数上限
默认低细节图像素预算=512*512#低细节总像素预算
默认请求图最大字节=2*1024*1024#单张确定性请求图编码字节目标
请求图最大边=4096#十五张及以上时每边上限，对每张图都施加以免张数改投影

def 解析请求图最大字节(模型):#解析编码字节目标
    """解析一条 DeepSeek 模型路由对每张请求图施加的编码字节目标。"""
    if 'imageMaxBytes' in 模型 and 模型['imageMaxBytes'] is not None:#显式字节
        return 模型['imageMaxBytes']#条目字节
    return 默认请求图最大字节#默认字节

def 解析请求图目标(模型,源):#解析确定性请求目标
    """先按令牌网格或像素预算投影，再施加每边上限，最后带上编码字节目标；小图不放大。"""
    if 模型.get('imagePixelBudget')=='low':#低细节
        预算=默认低细节图像素预算#低细节预算
    elif 'imagePixelBudget' in 模型:#显式或缺席
        预算=模型['imagePixelBudget']#条目预算，可能是 None
    else:#缺席
        预算=None#走令牌网格
    if 预算 is None:#令牌网格
        投影=深求请求图尺寸(源['width'],源['height'])#令牌网格尺寸
    else:#像素预算
        投影=请求图像尺寸(源['width'],源['height'],预算)#像素预算尺寸
    if max(投影['width'],投影['height'])>请求图最大边:#超每边上限
        封顶=长边尺寸(源['width'],源['height'],请求图最大边)#按长边封顶
    else:#未超
        封顶=投影#投影尺寸
    目标=dict(封顶)#拆离
    目标['maxBytes']=解析请求图最大字节(模型)#编码字节目标
    return 目标#完整请求目标

def 仅文本价(块):#仅文本价
    """为一仅文本路由用确定性文本替换的一次出现定价。"""
    return {'visualTokens':0,'text':仅文本图片文案(块['attachment'])}#零视觉令牌

def 深求图片请求定价(连接,模型,解析访问=None):#图片请求定价
    """从已校验连接快照为一条 DeepSeek 路由构建请求图定价。"""
    目录模型=None#目录条目
    for 条目 in 连接['models']:#逐条
        if 条目['id']==模型:#命中
            目录模型=条目#记下
            break#找到即停
    模态=目录模型.get('inputModalities') if 目录模型 is not None else None#输入模态
    if 模态 is None or 'image' not in 模态:#非视觉路由
        def 仅文本计价(图片列表):#仅文本
            """每出现按仅文本占位计价。"""
            return [仅文本价(块) for 块 in 图片列表]#仅文本
        return {'priceImages':仅文本计价}#仅文本
    def 计价(图片列表):#按出现计价
        """卸载出现按占位文本，保留出现按投影尺寸。"""
        结果=[]#定价表
        for 块 in 图片列表:#逐出现
            引用=块['attachment']#附件引用
            if 块.get('offloaded') is True:#已卸载
                访问=解析访问(引用) if 解析访问 is not None else None#可选访问
                结果.append({'visualTokens':0,'text':卸载图片文案(引用,访问)})#占位
                continue#下一项
            目标=解析请求图目标(目录模型,引用)#投影目标
            访问=解析访问(引用) if 解析访问 is not None else None#可选访问
            结果.append({
                'visualTokens':深求图片令牌(目标['width'],目标['height']),#视觉令牌
                'text':请求图片句柄文案(引用,目标,访问),#句柄
            })#保留图
        return 结果#定价表
    return {'priceImages':计价}#同步定价

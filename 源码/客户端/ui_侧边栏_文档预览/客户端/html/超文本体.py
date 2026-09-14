from .引导 import 创建超文本文档#引导
from .打包 import 打包超文本#打包
from .读取相对 import 创建读取超文本相对#相对读

__all__=['超文本体']#仅中文公开名


def 超文本体(内容,资源地址,关联读取,取标签信息,翻译):
    """产出隔离 HTML 文档结构，或文本交付时无。"""
    if 内容.get('kind')!='bytes':#非字节
        return None#无
    标签=取标签信息()['tab']#标签
    信号=标签['signal'] if 'signal' in 标签 else None#寿命
    相对读=创建读取超文本相对(关联读取,资源地址,信号)#相对读
    try:
        包=打包超文本(内容['data'],相对读,信号)#打包
        文档=创建超文本文档(包)#引导
        return {#结构
            'kind':'html-body',
            'document':文档,
            'title':翻译('frame'),
            'sandbox':'allow-scripts',
        }#结束
    except Exception:#失败
        return {'kind':'html-status','status':'failed','message':翻译('failed')}#状态

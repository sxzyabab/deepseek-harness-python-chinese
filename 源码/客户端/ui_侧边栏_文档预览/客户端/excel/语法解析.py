import threading
from .工作者 import 工作者入口
from .模型 import 不支持特性表
from ..面 import 已中止

__all__=['解析excel']

def 解析excel(字节,格式,上限,信号):
    """在一次性线程里解析，拷贝保留的预览缓冲。"""
    if 已中止(信号):
        raise RuntimeError('已中止')
    if len(字节)>上限['maxBytes']:
        raise RuntimeError('tooLarge')
    盒={'ok':None}
    完成=threading.Event()
    def 跑():
        盒.update(工作者入口(bytes(字节),格式,上限))
        完成.set()
    线=threading.Thread(target=跑,daemon=True)
    线.start()
    if 信号 is not None:
        def 盯():
            if hasattr(信号,'wait'):
                信号.wait()
            完成.set()
        threading.Thread(target=盯,daemon=True).start()
    秒=上限['timeoutMs']/1000
    if not 完成.wait(秒):
        raise RuntimeError('timeout')
    if 已中止(信号):
        raise RuntimeError('已中止')
    if 盒.get('ok') is True and 有效预览(盒.get('value')):
        return 盒['value']
    if 盒.get('ok') is False and 盒.get('code') in ('invalid','tooLarge','timeout','encoding'):
        raise RuntimeError(str(盒['code']))
    raise RuntimeError('invalid')

def 有效预览(值):
    if not isinstance(值,dict) or 'sheets' not in 值 or 'missingResults' not in 值:
        return False
    缺=值['missingResults']
    if type(缺) is bool or type(缺) is not int or 缺<0:
        return False
    特性=值.get('unsupportedFeatures')
    if not isinstance(特性,list):
        return False
    for 项 in 特性:
        if 项 not in 不支持特性表:
            return False
    表=值['sheets']
    if not isinstance(表,list) or len(表)==0:
        return False
    for 页 in 表:
        if not isinstance(页,dict) or not isinstance(页.get('name'),str):
            return False
        if not isinstance(页.get('celldata'),list):
            return False
    return True

"""列表中已改文件的对比缓存；失败可再读。"""
from .改动 import 改动对比网址,是否改动对比#URL 与校验
from .宿主读存储 import 宿主读存储#基类

__all__=['改动对比存储']#仅中文公开名

def _解码对比(应答):#应答→态
    """404 为 missing；其它失败为 error。"""
    if 应答 is None:#无
        return 'error'#错
    状态=应答['status'] if 'status' in 应答 else 0#状态
    if 状态==404:#缺失
        return 'missing'#缺失
    if 'ok' not in 应答 or not 应答['ok']:#失败
        return 'error'#错
    值=应答['json'] if 'json' in 应答 else None#JSON
    return 值 if 是否改动对比(值) else 'error'#校验

def _对比可重试(态):#仅错误可再读
    """error 才替换。"""
    return 态=='error'#是

class 改动对比存储(宿主读存储):#对比存储
    """失败态可被后续请求替换。"""
    def __init__(自身,拉取=None):
        """可选注入拉取。"""
        super().__init__({#策略
            'loading':'loading',#加载
            'failed':'error',#失败
            'retryable':_对比可重试,#仅错误重试
            'decode':_解码对比,#解码
        },拉取)#基类

    def 加载(自身,会话标识,序号,下标):#读一条
        """缓存命中或 missing 保持；error 再读。"""
        return 自身.加载网址(改动对比网址(会话标识,序号,下标))#委托

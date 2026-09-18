"""已宣布 workspace/changes 事件的摘要一次性缓存。"""
from .改动 import 改动摘要网址,是否改动摘要#URL 与校验
from .宿主读存储 import 宿主读存储#基类

__all__=['改动摘要存储']#仅中文公开名

def _解码摘要(应答):#应答→态
    """非 ok 或非法 JSON 为 missing。"""
    if 应答 is None or 'ok' not in 应答 or not 应答['ok']:#失败
        return 'missing'#缺失
    值=应答['json'] if 'json' in 应答 else None#JSON
    return 值 if 是否改动摘要(值) else 'missing'#校验

def _摘要不可重试(_态):#永不重试
    """摘要一旦落地即保持。"""
    return False#否

class 改动摘要存储(宿主读存储):#摘要存储
    """摘要或 missing 保留至连接替换。"""
    def __init__(自身,拉取=None):
        """可选注入拉取。"""
        super().__init__({#策略
            'loading':'loading',#加载
            'failed':'missing',#失败即缺失
            'retryable':_摘要不可重试,#不重试
            'decode':_解码摘要,#解码
        },拉取)#基类

    def 加载(自身,会话标识,序号):#读一条
        """同坐标后续读用缓存。"""
        return 自身.加载网址(改动摘要网址(会话标识,序号))#委托

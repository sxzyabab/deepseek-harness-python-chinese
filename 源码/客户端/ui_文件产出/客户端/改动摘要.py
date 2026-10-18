'已宣告 workspace/changes 的摘要缓存。读到或确认缺失后不再读'
from ...ui_在应用中打开.客户端.控制器 import 等到,读取
from ..改动 import 改动摘要网址,是否改动摘要
from .宿主读存储 import 宿主读存储

__all__=['改动摘要存储']


class 改动摘要存储(宿主读存储):
    '摘要、缺失或正在读'
    def __init__(自身):
        '摘要和缺失都留到连接被换掉'

        def 可重试(状态):
            '站着的状态不再读'
            return False

        def 解码(响应):
            '不成功或对不上摘要记录就是缺失'
            if 读取(响应,'ok') is not True:
                return 'missing'
            值=等到(响应.json())
            if 是否改动摘要(值):
                return 值
            return 'missing'

        super().__init__({
            'loading':'loading',
            'failed':'missing',
            'retryable':可重试,
            'decode':解码,
        })

    def 加载(自身,会话标识,序号):
        '每个坐标读一次'
        自身.加载网址(改动摘要网址(会话标识,序号))

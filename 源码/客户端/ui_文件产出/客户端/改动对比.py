'所列改动文件的对比缓存。失败的下一次会再读'
from ...ui_在应用中打开.客户端.控制器 import 等到,读取
from ..改动 import 改动对比网址,是否改动对比
from .宿主读存储 import 宿主读存储

__all__=['改动对比存储']


class 改动对比存储(宿主读存储):
    '对比、缺失、失败或正在读'
    def __init__(自身):
        '失败可以重读。404 是缺失'

        def 可重试(状态):
            '只有失败态再读'
            return 状态=='error'

        def 解码(响应):
            '404 缺失。正文对不上对比记录则失败'
            if 读取(响应,'status')==404:
                return 'missing'
            if 读取(响应,'ok') is not True:
                return 'error'
            值=等到(响应.json())
            if 是否改动对比(值):
                return 值
            return 'error'

        super().__init__({
            'loading':'loading',
            'failed':'error',
            'retryable':可重试,
            'decode':解码,
        })

    def 加载(自身,会话标识,序号,下标):
        '读一份对比。已有的对比和缺失保持，失败再读'
        自身.加载网址(改动对比网址(会话标识,序号,下标))

'交付卡、改动卡和收口提及共用的原生打开状态'
from ...模块.客户端.通告 import 取握手窗口
from ...存储 import 创建快照存储
from ..改动 import 已改文件网址
from ..已呈现 import 已呈现文件网址

__all__=['成功停留毫秒','成功淡出毫秒','已呈现打开控制器']

成功停留毫秒=5000
成功淡出毫秒=200


class 已呈现打开控制器:
    '一次浏览器插件里的打开请求。插件拆掉就取消'
    def __init__(自身):
        '文件动作地址对应状态。桌面元数据单独一份'
        窗口=取握手窗口()
        自身.状态=创建快照存储({})
        自身.宿主=创建快照存储(None)
        自身._到期={}
        自身._加载中=None
        自身._元数据=窗口.AbortController()
        自身._寿命=窗口.AbortController()
        自身._在飞=set()

    def 打开(自身,会话标识,序号,下标,动作='open',应用=None):
        '打开已声明文件。同一地址正在打开时不再发'
        return 自身._按网址打开(已呈现文件网址(会话标识,序号,下标),动作,应用)

    def 打开改动(自身,会话标识,序号,下标,动作='open',应用=None):
        '打开已记录的改动文件'
        return 自身._按网址打开(已改文件网址(会话标识,序号,下标),动作,应用)

    def _按网址打开(自身,网址,动作,应用):
        '同一地址正在打开或揭示时直接返回'
        阶段=自身.状态.getSnapshot().get(网址)
        if 自身._寿命.signal.aborted or 阶段=='opening' or 阶段=='revealing':
            return None
        自身._清到期(网址)

        def 写进行(状态):
            '进入打开或揭示'
            状态[网址]='opening' if 动作=='open' else 'revealing'

        自身.状态.update(写进行)
        完成=取握手窗口().AbortController()
        自身._在飞.add(完成)
        try:
            return 自身._请求(网址,动作,应用)
        finally:
            完成.abort()
            自身._在飞.discard(完成)

    def 加载宿主(自身):
        '读桌面元数据。已经在读就等这一次。失败可以再读'
        if 自身._寿命.signal.aborted:
            return
        if 自身._加载中 is not None:
            return
        自身.宿主.set(None)
        完成=取握手窗口().AbortController()
        自身._加载中=完成
        自身._在飞.add(完成)
        try:
            窗口=取握手窗口()
            信号=窗口.AbortSignal.any([自身._寿命.signal,自身._元数据.signal])
            自身._读宿主(信号)
        finally:
            if 自身._加载中 is 完成:
                自身._加载中=None
            完成.abort()
            自身._在飞.discard(完成)

    def 重置宿主(自身):
        '连接换了就作废桌面元数据。原来正在读就再读一次'
        正在读=自身._加载中 is not None
        自身._元数据.abort()
        自身._元数据=取握手窗口().AbortController()
        自身._加载中=None
        自身.宿主.set(None)
        if 正在读:
            自身.加载宿主()

    def _读宿主(自身,信号):
        '这个网页引擎不再通过浏览器请求宿主'
        宿主='error'
        if not 信号.aborted:
            自身.宿主.set(宿主)

    def 拆除(自身):
        '取消未完请求，并清掉成功提示的定时器'
        自身._寿命.abort()
        for 网址 in list(自身._到期):
            自身._清到期(网址)
        for 完成 in list(自身._在飞):
            完成.abort()

    def _清到期(自身,网址):
        '取消这一地址的成功淡出'
        标识=自身._到期.pop(网址,None)
        if 标识 is not None:
            取握手窗口().clearTimeout(标识)

    def _请求(自身,网址,动作,应用):
        'POST 打开或揭示。成功过几秒清掉状态'
        阶段='error' if 动作=='open' else 'revealError'
        if not 自身._寿命.signal.aborted:
            if 阶段=='opened' or 阶段=='revealed':
                def 到期(网址=网址):
                    '停留加淡出之后摘掉成功态'
                    自身._到期.pop(网址,None)

                    def 删(状态):
                        '这一地址不再显示成功'
                        if 网址 in 状态:
                            del 状态[网址]

                    自身.状态.update(删)

                自身._到期[网址]=取握手窗口().setTimeout(到期,成功停留毫秒+成功淡出毫秒)
            def 写阶段(状态,阶段=阶段):
                '发布这一次的阶段'
                状态[网址]=阶段
            自身.状态.update(写阶段)
        if 阶段=='opened' or 阶段=='revealed':
            return None
        if 动作=='reveal':
            return 'revealError'
        return 'openError'

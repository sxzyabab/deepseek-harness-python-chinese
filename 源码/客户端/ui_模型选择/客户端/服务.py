'ctx.modelDirectories：两条入口共用的每会话模型目录'

from ....依赖.cordis.服务 import 服务
from ....基础设施.通用工具 import 获取内部数据
from ....工具.值 import 带值弱映射
from .代际目录 import 代际目录
from .目录 import 模型目录

__all__=['模型目录解析器']

依赖=['sessions','remote','remote.session']

class 模型目录解析器(服务):
    '按会话绑定找出那一份目录。未知会话直接失败'
    def __init__(自身,上下文,配置=None):
        '挂到 modelDirectories，预拉共享目录，并听连接和 Host 变更'
        super().__init__(上下文,'modelDirectories')
        自身.目录表=带值弱映射()
        自身.目录账本=代际目录(上下文)
        try:
            自身.目录账本.load()
        except Exception as 加载错误:
            pass
        def 重连(*位置参数):
            '重连后清掉上一代目录，并作废各会话在飞的选定'
            自身.目录账本.resetGeneration()
            for 目录 in 自身.目录表.values:
                目录.resetConnected()
        上下文.监听('connection/reset',重连)
        def 刷新(*位置参数):
            '适配器、设置或凭据变了就重载共享目录'
            自身.目录账本.refresh()
        订阅=getattr(上下文.remote,'$on')
        订阅('llm/adapters-updated',刷新)
        订阅('settings/document-updated',刷新)
        订阅('credentials/record-updated',刷新)
        订阅('credentials/reference-updated',刷新)

    def directoryFor(自身,会话标识):
        '惰性造出这份会话的目录。作用域拆除时拆掉它'
        会话面=自身.ctx.sessions
        作用域=会话面.scope(会话标识)
        if 作用域 is None:
            raise Exception('ui-model-selection: session "'+str(会话标识)+'" resolved no scope')
        绑定=会话面.binding(会话标识)
        if 绑定 is None:
            raise Exception('ui-model-selection: session "'+str(会话标识)+'" resolved no binding')
        键=绑定['ctx'] if isinstance(绑定,dict) else 绑定
        已有=自身.目录表.get(键)
        if 已有 is not None:
            return 已有
        def 可用():
            '子智能体地址还在时，这场会话不能选模型'
            return 会话面.subagentAddress(会话标识) is None
        def 是空白():
            '这场会话还没有第一条消息'
            快照=绑定['session'].getSnapshot()
            if isinstance(快照,dict):
                return 快照.get('blank')
            return 快照.blank
        def 记录(名称,属性):
            '桌面埋点。没有采集服务就跳过'
            分析=自身.ctx.获取服务('productAnalytics',False)
            if 分析 is not None:
                分析.track(名称,属性)
        投影=绑定['session'].projections.面('modelSelection')
        目录=模型目录(
            自身.ctx.remote.session,
            会话标识,
            可用,
            自身.目录账本,
            投影,
            是空白,
            记录,
        )
        自身.目录表.set(键,目录)
        def 拆除目录():
            '会话作用域结束时拆掉这份目录'
            def 清():
                '拆除并从弱表删除'
                目录.dispose()
                自身.目录表.delete(键)
            return 清
        作用域.副作用(拆除目录,'ui-model-selection: session directory')
        return 目录

模型目录解析器.inject=依赖

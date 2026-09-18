from ...依赖 import cordis#外部依赖胶水
from ...工具.值 import 带值弱映射#按座位绑定弱缓存目录
from .代际目录 import 代际目录#共享 Host 代际目录
from .目录 import 模型目录,模型选择错误#每会话目录与异常
服务=cordis.服务#Cordis 服务基类

__all__=['模型目录解析器']#仅中文公开名

class 模型目录解析器(服务):#ctx.modelDirectories
    """双入口共享同一份每会话目录；按座位绑定弱映射。"""
    def __init__(自身,上下文,配置):#挂到 modelDirectories
        """记下阻断文案工厂、代际目录与目录弱表。"""
        super().__init__(上下文,'modelDirectories')#登记
        自身.阻断原因=配置['blockReason']#阻断工厂
        自身.目录账本=代际目录(上下文)#共享 Host 代际目录
        自身.目录表=带值弱映射()#按座位绑定弱缓存
        try:#预拉目录
            自身.目录账本.load()#加载
        except BaseException:#错误由选择器暴露
            pass#吞掉
        def 重连重置():#连接重置
            """清代际并重置各目录。"""
            自身.目录账本.resetGeneration()#清 Host 代际目录
            for 目录 in 自身.目录表.values:#逐个
                目录.resetConnected()#重置
        上下文.监听('connection/reset',重连重置)#监听重置
        def 刷新():#适配器/设置/凭据变更
            """使代际目录失效并重载。"""
            自身.目录账本.refresh()#刷新
        上下文.remote.$on('llm/adapters-updated',刷新)#适配器
        上下文.remote.$on('settings/document-updated',刷新)#设置
        上下文.remote.$on('credentials/reference-updated',刷新)#凭据

    def directoryFor(自身,会话标识):#按会话取共享目录
        """惰性；绑定作用域拆除器会移除并拆除。"""
        会话面=自身.所属上下文.获取服务('sessions')#会话运行时
        作用域=会话面.scope(会话标识)#会话作用域
        if 作用域 is None:#未知
            raise 模型选择错误('ui-model-selection: session "'+str(会话标识)+'" resolved no scope')#失败
        绑定=会话面.binding(会话标识)#座位绑定
        if 绑定 is None:#无绑定
            raise 模型选择错误('ui-model-selection: session "'+str(会话标识)+'" resolved no binding')#失败
        键=绑定.ctx#弱键用绑定上下文
        已有=自身.目录表.get(键)#已有
        if 已有 is not None:#复用
            return 已有#常驻
        def 本会话可用():#非子智能体
            """本会话是否可走模型 RPC。"""
            return 会话面.subagentAddress(会话标识) is None#可用
        投影=绑定.session.projections.faceOf('modelSelection')#持久选定投影
        目录=模型目录(#本会话目录
            自身.所属上下文.remote.session,#会话 RPC 面
            会话标识,#身份
            本会话可用,#非子智能体
            自身.目录账本,#共享代际目录
            投影,#投影源
        )#构造结束
        自身.目录表.set(键,目录)#记入弱表
        对话面=自身.所属上下文.获取服务('conversation')#会话面
        if 对话面 is not None:#有 conversation
            def 发布():#按 routable 写阻断
                """仅明确 false 才阻断。"""
                快照=目录.存储.getSnapshot()#快照
                if 'routable' in 快照 and 快照['routable'] is False:#明确不可路由
                    对话面.blocks.set(会话标识,{'reason':自身.阻断原因()})#阻断
                else:#可或未知
                    对话面.blocks.set(会话标识,None)#清
            发布()#立即推一次
            def 订阻断():#订阅目录
                """快照变更再推。"""
                停=目录.存储.subscribe(发布)#订阅
                def 拆除订阅():#拆除
                    """取消订阅并清阻断。"""
                    停()#取消
                    对话面.blocks.set(会话标识,None)#清
                return 拆除订阅#拆除器
            作用域.副作用(订阻断,'ui-model-selection: composer block')#阻断副作用
        def 拆除目录():#会话拆除
            """拆目录并从表删除。"""
            def 清():#清目录
                """dispose 并删表。"""
                目录.dispose()#拆除
                自身.目录表.delete(键)#删
            return 清#拆除器
        作用域.副作用(拆除目录,'ui-model-selection: session directory')#目录副作用
        return 目录#新常驻

模型目录解析器.inject=['sessions','remote','remote.session']#框架槽

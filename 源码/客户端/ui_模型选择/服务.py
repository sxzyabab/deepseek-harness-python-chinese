"""ModelDirectoryResolver（ctx.modelDirectories）：每会话模型目录根所有者。

对齐上游 `ui-model-selection/src/client/service.ts`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
from .目录 import 模型目录,模型选择错误#每会话目录与异常
服务=cordis.服务#Cordis 服务基类

__all__=['模型目录解析器']#仅中文公开名

class 模型目录解析器(服务):#ctx.modelDirectories
    """双入口共享同一份每会话目录。"""
    def __init__(自身,上下文,配置):#挂到 modelDirectories
        """记下阻断文案工厂与目录表。"""
        super().__init__(上下文,'modelDirectories')#登记
        自身.阻断原因=配置['blockReason']#阻断工厂
        自身.目录表={}#按会话索引
        def 重连重置():#连接重置
            """每个目录硬重置。"""
            for 目录 in list(自身.目录表.values()):#逐个
                目录.resetConnected()#重置
        上下文.监听('connection/reset',重连重置)#监听重置
        def 刷新():#重拉每个已活目录
            """适配器/设置变更时刷新。"""
            for 目录 in list(自身.目录表.values()):#逐个
                try:#重载
                    目录.load()#加载
                except 模型选择错误:#吞掉
                    pass#下次打开重试
        上下文.remote.$on('llm/adapters-updated',刷新)#适配器
        上下文.remote.$on('settings/document-updated',刷新)#设置

    def directoryFor(自身,会话标识):#按会话取共享目录
        """惰性；作用域拆除器会移除并拆除。"""
        已有=自身.目录表[会话标识] if 会话标识 in 自身.目录表 else None#已有
        if 已有 is not None:#复用
            return 已有#常驻
        会话面=自身.所属上下文.获取服务('sessions')#会话运行时
        作用域=会话面.scope(会话标识)#会话作用域
        if 作用域 is None:#未知
            raise 模型选择错误('ui-model-selection: session "'+str(会话标识)+'" resolved no scope')#失败
        连接=自身.所属上下文.获取服务('connection')#连接
        def 本会话可用():#非子智能体
            """本会话是否可走模型 RPC。"""
            return 会话面.subagentAddress(会话标识) is None#可用
        目录=模型目录(#本会话目录
            连接.api.sessions,#会话 RPC
            会话标识,#身份
            本会话可用,#非子智能体
        )#构造结束
        自身.目录表[会话标识]=目录#记入
        会话面=自身.所属上下文.获取服务('conversation')#会话面
        if 会话面 is not None:#有 conversation
            def 发布():#按 routable 写阻断
                """仅明确 false 才阻断。"""
                快照=目录.存储.getSnapshot()#快照
                if 'routable' in 快照 and 快照['routable'] is False:#明确不可路由
                    会话面.blocks.set(会话标识,{'reason':自身.阻断原因()})#阻断
                else:#可或未知
                    会话面.blocks.set(会话标识,None)#清
            发布()#立即推一次
            def 订阻断():#订阅目录
                """快照变更再推。"""
                停=目录.存储.subscribe(发布)#订阅
                def 拆除订阅():#拆除
                    """取消订阅并清阻断。"""
                    停()#取消
                    会话面.blocks.set(会话标识,None)#清
                return 拆除订阅#拆除器
            作用域.副作用(订阻断,'ui-model-selection: composer block')#阻断副作用
        def 拆除目录():#会话拆除
            """拆目录并从表删除。"""
            def 清():#清目录
                """dispose 并删表。"""
                目录.dispose()#拆除
                自身.目录表.pop(会话标识,None)#删
            return 清#拆除器
        作用域.副作用(拆除目录,'ui-model-selection: session directory')#目录副作用
        return 目录#新常驻

模型目录解析器.inject=['connection','sessions','remote']#框架槽

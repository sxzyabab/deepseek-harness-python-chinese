"""耐久会话持久化 Service Definition（`ctx.sessionPersistence`）。后端把会话事件存成事件源日志，并把不可回放的会话头元数据单独携带；调用方通过 `创建`/`打开` 取得的会话句柄寻址一个已存会话。"""
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#导入Cordis服务基类
from ...内核.会话 import 会话头字段#导入会话头（本包只再导出，不拥有）
from .修订 import 会话持久化修订#修订品牌
from .句柄 import (#句柄面
    会话访问,#访问模式
    会话句柄,#会话句柄
    会话句柄读结果字段,#读取结果字段
    会话句柄追加选项字段,#追加选项
    会话句柄刷盘选项字段,#刷盘选项
    会话句柄读选项字段,#读取选项
    会话持久化未找到错误,#未找到
    会话已存在错误,#已存在
    会话已有写主错误,#已有写主
    会话只读错误,#只读
    会话所有权丢失错误,#所有权丢失
    会话句柄已关闭错误,#已关闭
)#从句柄再导出
from .协调器 import (#写路径编排再导出
    默认预备会话缓存大小,#默认预备缓存大小
    默认写批最大延迟毫秒,#默认写批延迟
    写批延迟上限毫秒,#写批延迟上限
    持久化协调器,#持久化协调器
    会话格式不支持错误,#格式不支持错误
    会话持久化损坏错误,#损坏错误
    会话格式版本拒绝文案,#格式版本拒绝文案
    持久化后端字段,#后端约定字段表
    持久化协调器选项字段,#协调器选项字段表
    已存前缀字段,#已存前缀字段表
    已存后缀字段,#已存后缀字段表
)#从协调器再导出
from .预备 import 持久化错误,若已中止则抛出#包异常与中止
from .存储契约 import (#存储契约再导出
    断言已存标识 as 契约断言已存标识,#已存 id
    断言版本 as 契约断言版本,#版本
    校验已存事件,#已存事件
    物化创建头,#创建头
    物化追加批,#追加批
    断言连续,#连续 seq
)#存储契约

#把元数据词汇再导出，使消费方从 Service Definition 导入。
会话持久化修订=会话持久化修订#再导出品牌函数

#对齐上游：export type { SessionHeader } from '@deepseek-ai/dsh-session'
会话头字段=会话头字段#再导出会话头字段键表（权威在 dsh-session / 内核.session）

会话持久化快照字段=('header','revision','eventCount','sizeBytes')#不加载完整日志即可返回的轻量不可变源身份

会话存储元数据字段=('meta','inheritedEventCount')#逻辑会话头与精确继承切口

会话检查字段=('meta','inheritedEventCount','events')#从持久化预备出的不可变逻辑会话

会话原样子产物字段=('meta','filename','content')#后端自己的、一个会话的原始产物文本，原样

会话位置字段=('kind','path')#后端解析出的、每会话本地产物位置（绝对路径提示，绝不当授权令牌）

持久化后端字段=持久化后端字段#再导出后端约定
持久化协调器选项字段=持久化协调器选项字段#再导出协调器选项
已存前缀字段=已存前缀字段#再导出已存前缀
已存后缀字段=已存后缀字段#再导出已存后缀

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '会话持久化修订','会话头字段','会话持久化快照字段','会话存储元数据字段','会话检查字段',
    '会话原样子产物字段','会话位置字段','持久化后端字段','持久化协调器选项字段',
    '已存前缀字段','已存后缀字段','默认预备会话缓存大小','默认写批最大延迟毫秒',
    '写批延迟上限毫秒','持久化协调器','会话格式不支持错误','会话持久化损坏错误',
    '会话格式版本拒绝文案','会话持久化','持久化错误',
    '会话访问','会话句柄','会话句柄读结果字段','会话句柄追加选项字段','会话句柄刷盘选项字段','会话句柄读选项字段',
    '会话持久化未找到错误','会话已存在错误','会话已有写主错误','会话只读错误',
    '会话所有权丢失错误','会话句柄已关闭错误',
    '校验已存事件','物化创建头','物化追加批','断言连续',
    '契约断言已存标识','契约断言版本',
]#公开面结束

class 会话持久化(服务):#会话持久化服务
    """经每会话句柄寻址的耐久仅追加会话存储。"""
    def __init__(自身,上下文):#登记为ctx.sessionPersistence
        """登记为 ctx.sessionPersistence。"""
        if type(自身) is 会话持久化:#直接实例化抽象类
            raise 持久化错误('@deepseek-ai/dsh-session-persistence is the abstract persistence seam; load a backend implementation instead')#必须加载实现
        super().__init__(上下文,'sessionPersistence')#服务名

    def 创建(自身,头,选项=None):#创建并取写句柄
        """创建新的已存会话并取得其写所有权。"""
        raise NotImplementedError('SessionPersistence.create')#子类必须实现

    def 打开(自身,标识,访问,选项=None):#打开句柄
        """打开已有已存会话；`write` 原子声明单写者所有权。"""
        raise NotImplementedError('SessionPersistence.open')#子类必须实现

    def 刷盘全部(自身):#服务范围刷盘
        """在一次耐久屏障中刷本服务实例拥有的每个活写句柄。"""
        raise NotImplementedError('SessionPersistence.flush')#子类必须实现

    def 观察(自身,标识,选项=None):#轻量观察
        """在不读事件日志、不取所有权的情况下观察一个已存会话。"""
        raise NotImplementedError('SessionPersistence.stat')#子类必须实现

    def 列出(自身,选项=None):#列举快照
        """列举本进程可见的每个已存会话，无承诺顺序。"""
        raise NotImplementedError('SessionPersistence.list')#子类必须实现

    # —— 以下为旧协调器面的降级兼容；新恢复路径走 打开/读，不再经 seedSource 预备 —— #

    def 定位(自身,头):#定位产物
        """解析此后端为一个会话的独立本地产物。"""
        raise NotImplementedError('SessionPersistence.locate')#子类必须实现

    @property#是否支持原样子产物
    def 支持原样子产物(自身):#是否支持原样子产物
        """此后端是否每会话暴露一份原样子产物。"""
        raise NotImplementedError('SessionPersistence.supportsRawArtifacts')#子类必须实现

    def 读原始(自身,标识,信号=None):#默认拒绝原样子产物
        """原样读取一个会话的后端拥有产物文本。"""
        若已中止则抛出(信号)#已取消则失败
        raise 持久化错误('this session persistence backend does not expose raw artifacts')#不支持原样子产物

    def 追加(自身,标识,事件列表):#耐久追加（旧面）
        """耐久持久化一批事件（旧协调器面；优先经写句柄追加）。"""
        raise NotImplementedError('SessionPersistence.append')#子类必须实现

    def 预备(自身,标识,信号=None):#降级：旧预备契约
        """降级保留：旧调用方仍可预备未发布 Session；内部改为 eventState 移交，不再使用 seedSource。"""
        raise NotImplementedError('SessionPersistence.prepare')#子类必须实现

    def 加载(自身,标识):#加载并提交恢复
        """加载不可变的已平衡逻辑视图，并提交任何所需的冷恢复。"""
        raise NotImplementedError('SessionPersistence.load')#子类必须实现

    def 检查(自身,标识,信号=None):#检查不提交恢复
        """检查不可变逻辑会话，不提交恢复也不发布它。"""
        raise NotImplementedError('SessionPersistence.inspect')#子类必须实现

    def 从序号读(自身,标识,起始序号,信号=None):#按seq读后缀
        """读取从起始序号起的已存储事件。"""
        raise NotImplementedError('SessionPersistence.readFrom')#子类必须实现

    def 列出快照(自身,信号=None):#列出带头修订的快照
        """列出已物化会话及其廉价的每日志变更令牌。"""
        raise NotImplementedError('SessionPersistence.listSnapshots')#子类必须实现

default=会话持久化#Cordis 默认导出槽

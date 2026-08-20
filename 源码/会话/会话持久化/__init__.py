"""耐久会话持久化 Service Definition（`ctx.sessionPersistence`）。后端把会话事件存成事件源日志，并把不可回放的会话头元数据单独携带。"""
from cordis import 服务#导入Cordis服务基类
from cordis.工具 import 是否thenable#可等待判定
from session import 会话准备,会话头字段#导入会话预备与会话头（本包只再导出，不拥有）
from llm import 结构化克隆#深拷贝
from .修订 import 会话持久化修订#修订品牌
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

#把元数据词汇再导出，使消费方从 Service Definition 导入。
会话持久化修订=会话持久化修订#再导出品牌函数

#对齐上游：export type { SessionHeader } from '@deepseek-ai/dsh-session'
会话头字段=会话头字段#再导出会话头字段键表（权威在 dsh-session / 内核.session）

会话持久化快照字段=('header','revision')#不加载完整日志即可返回的轻量不可变源身份

会话检查字段=('meta','events')#从持久化或活拥有方预备出的不可变逻辑会话

会话原样子产物字段=('meta','filename','content')#后端自己的、一个会话的原始产物文本，原样

会话位置字段=('kind','path')#后端解析出的、每会话本地产物位置（绝对路径提示，绝不当授权令牌）

持久化后端字段=持久化后端字段#再导出后端约定
持久化协调器选项字段=持久化协调器选项字段#再导出协调器选项
已存前缀字段=已存前缀字段#再导出已存前缀
已存后缀字段=已存后缀字段#再导出已存后缀

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步值

def 若已中止则抛出(信号):#取消优先抛出
    """已取消则抛出。"""
    if 信号 is None:#无信号
        return#放过
    方法=getattr(信号,'throwIfAborted',None)#Node风格
    if callable(方法):#有方法
        方法()#抛出
        return#已检查
    if getattr(信号,'aborted',False) is True:#已中止
        raise Exception('aborted')#取消
    if getattr(信号,'已中止',False) is True:#中文旗标
        raise Exception('aborted')#取消

class 会话持久化(服务):#会话持久化服务
    """耐久仅追加会话存储。实现保留连续、可无损 JSON 序列化的事件；追加仅在耐久后决议，加载平衡完整中断尾巴且不改写已提交事件。"""
    def __init__(自身,上下文):#登记为ctx.sessionPersistence
        """登记为 ctx.sessionPersistence。"""
        if type(自身) is 会话持久化:#直接实例化抽象类
            raise Exception('@deepseek-ai/dsh-session-persistence is the abstract persistence seam; load a backend implementation instead')#必须加载实现
        super().__init__(上下文,'sessionPersistence')#服务名

    def 定位(自身,头):#定位产物
        """解析此后端为一个会话的独立本地产物，不读、不创建、不flush、也不以其他方式物化它。像 SQLite 这种不每会话拥有一份产物的后端返回 None。"""
        raise NotImplementedError('SessionPersistence.locate')#子类必须实现

    @property#是否支持原样子产物
    def 支持原样子产物(自身):#是否支持原样子产物
        """此后端是否每会话暴露一份原样子产物。声明 True 的后端必须覆盖 读原始。"""
        raise NotImplementedError('SessionPersistence.supportsRawArtifacts')#子类必须实现

    def 读原始(自身,标识,信号=None):#默认拒绝原样子产物
        """原样读取一个会话的后端拥有产物文本。调用方先测支持原样子产物；之后的 None 只表示请求的会话没有已物化产物。"""
        if 信号 is not None and (getattr(信号,'aborted',False) is True or getattr(信号,'已中止',False) is True):#已取消
            原因=getattr(信号,'reason',None)#取消原因
            if isinstance(原因,BaseException):#有原因
                raise 原因#拒绝取消
            raise Exception('aborted')#拒绝取消
        raise Exception('this session persistence backend does not expose raw artifacts')#不支持原样子产物

    def 创建(自身,头):#注册元数据
        """注册新会话的元数据。后端可以把物理写入推迟到首次追加（惰性物化）。"""
        raise NotImplementedError('SessionPersistence.create')#子类必须实现

    def 追加(自身,标识,事件们):#耐久追加
        """耐久持久化一批事件。遵守仅追加与连续 seq 约定。"""
        raise NotImplementedError('SessionPersistence.append')#子类必须实现

    def 预备(自身,标识,信号=None):#预备未发布会话
        """预备 resume 所用的精确未发布 Session。"""
        若已中止则抛出(信号)#已取消则失败
        已加载=解开(自身.加载(标识))#加载平衡视图
        若已中止则抛出(信号)#加载后再检查
        会话们=自身.ctx.get('sessions')#取会话存储
        if 会话们 is None:#没有会话存储
            raise Exception('cannot prepare a session: SessionStore is not configured')#无法预备
        事件种子=[]#深拷贝事件种子
        for 事件 in 已加载['events']:#逐条
            事件种子.append(结构化克隆(事件))#深拷贝
        return 会话准备.创建(会话们.prepare(标识,{#构造预备
            'seed':事件种子,#深拷贝事件种子
            'meta':结构化克隆(已加载['meta']),#深拷贝头
            'seedSource':'persistence',#种子来自持久化
        }))#create结束

    def 加载(自身,标识):#加载并提交恢复
        """加载不可变的已平衡逻辑视图，并提交任何所需的冷恢复。"""
        raise NotImplementedError('SessionPersistence.load')#子类必须实现

    def 检查(自身,标识,信号=None):#检查不提交恢复
        """检查不可变逻辑会话，不提交恢复也不发布它。"""
        raise NotImplementedError('SessionPersistence.inspect')#子类必须实现

    def 从序号读(自身,标识,起始序号,信号=None):#按seq读后缀
        """读取从起始序号起的已存储事件。"""
        raise NotImplementedError('SessionPersistence.readFrom')#子类必须实现

    def 列出(自身,信号=None):#列出头
        """从元数据做轻量列表，不做整日志解析。"""
        raise NotImplementedError('SessionPersistence.list')#子类必须实现

    def 列出快照(自身,信号=None):#列出带头修订的快照
        """列出已物化会话及其廉价的每日志变更令牌。"""
        raise NotImplementedError('SessionPersistence.listSnapshots')#子类必须实现

default=会话持久化#默认导出
默认=会话持久化#中文默认导出

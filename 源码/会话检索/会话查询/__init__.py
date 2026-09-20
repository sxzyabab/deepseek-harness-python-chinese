from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#框架服务基类
from ...内核.会话 import 会话,快照会话事件#会话回放与事件快照
from ...模型后端.llm import 结构化克隆#拆离克隆
from .配置 import (
    会话查询错误,#检索错误
    会话查询读取窗口上限,#默认读取窗口
    会话查询默认持久检查并发,#默认持久检查并发
    会话查询默认准备会话缓存大小,#准备缓存
    若已中止则抛出,#中止抛出
)#配置常量
from .游标 import 会话搜索游标#游标品牌
from .语料库 import 会话语料库#活优先语料库
from .文档 import 构建会话事件搜索文档,构建会话事件记录#事件文档与记录
from .过滤 import (
    过滤会话事件文档,#过滤事件文档
    过滤会话结果,#过滤会话结果
    物化会话事件结果过滤器,#物化事件过滤器
    物化会话结果过滤器,#物化会话过滤器
    编译会话文本过滤器,#编译文本过滤器
)#过滤器
from .来源 import 校验会话头兼容#头兼容断言
from .抽取 import 抽取会话事件文本#文本抽取
from .追踪 import (
    事件记录 as 追踪事件记录,#事件记录
    当前面事件,#当前面事件
    追踪事件,#事件追踪
    追踪会话,#谱系追踪
)#追踪
from .标题折叠 import 折叠会话标题#标题折叠
from .观测 import 会话观测,会话观测读取器#点观察
from .冷读 import 读冷会话日志#句柄冷读

__all__=[
    '包名','名称','依赖','默认','会话查询引擎',
    '会话查询错误','会话查询读取窗口上限','会话查询默认持久检查并发',
    '会话查询默认准备会话缓存大小',
    '会话搜索游标','校验会话头兼容','抽取会话事件文本',
    '构建会话事件记录','构建会话事件搜索文档',
    '过滤会话结果','过滤会话事件文档',
    '物化会话结果过滤器','物化会话事件结果过滤器','编译会话文本过滤器',
    '会话观测','会话观测读取器','读冷会话日志',
]

class 会话查询引擎(服务):
    """以 sessionQuery 名安装的会话检索服务；活会话优先。"""
    def __init__(自身,上下文,配置=None):
        """以 sessionQuery 名安装服务。"""
        if 配置 is None:#缺省空配置
            配置={}#空配置
        super().__init__(上下文,'sessionQuery')#注册服务名
        窗口上限=配置['readWindowMax'] if 'readWindowMax' in 配置 else 会话查询读取窗口上限#解析窗口上限
        if isinstance(窗口上限,bool) or (not isinstance(窗口上限,int)) or 窗口上限<0:#窗口必须是非负整数
            raise 会话查询错误('session-query: readWindowMax 必须是非负整数','SESSION_QUERY_INVALID_CONFIG')#配置非法
        持久并发=配置['persistedInspectConcurrency'] if 'persistedInspectConcurrency' in 配置 else 会话查询默认持久检查并发#解析持久检查并发
        if isinstance(持久并发,bool) or (not isinstance(持久并发,int)) or 持久并发<1:#并发必须是正整数
            raise 会话查询错误('session-query: persistedInspectConcurrency 必须是正安全整数','SESSION_QUERY_INVALID_CONFIG')#配置非法
        缓存大小=配置['preparedSessionCacheSize'] if 'preparedSessionCacheSize' in 配置 else 会话查询默认准备会话缓存大小#准备缓存
        if isinstance(缓存大小,bool) or (not isinstance(缓存大小,int)) or 缓存大小<1:#缓存必须正整数
            raise 会话查询错误('session-query: preparedSessionCacheSize 必须是正安全整数','SESSION_QUERY_INVALID_CONFIG')#配置非法
        自身._读取窗口上限=窗口上限#读取窗口上限
        自身._语料库=会话语料库(上下文,持久并发)#按并发构造语料库
        自身._观测=会话观测读取器(上下文,自身._语料库,缓存大小)#点观察

    def observeSession(自身,会话标识,选项=None):
        """活优先点观察；方法名 observeSession 为线协议调用面原样保留。"""
        return 自身._观测.读(会话标识,选项)

    def 搜索会话(自身,请求,执行上下文=None):
        """在优先活会话的逻辑语料上检索，并按会话分组。子类实现。"""
        raise NotImplementedError('SessionQueryEngine.searchSessions')#抽象

    def 搜索事件(自身,请求,执行上下文=None):
        """在一条优先活会话的逻辑会话内检索事件。子类实现。"""
        raise NotImplementedError('SessionQueryEngine.searchEvents')#抽象

    def 列出会话(自身,信号=None):
        """用优先活会话的记录列出完整逻辑语料。"""
        return 自身._语料库.列出会话(信号)#委托语料库

    def 读取会话(自身,会话号):
        """读取并回放校验一条完整逻辑会话日志，且不把它变成活会话。"""
        已加载=自身._语料库.加载(会话号)#从语料加载
        继承=已加载['inheritedEventCount'] if 'inheritedEventCount' in 已加载 else 0#继承切口
        会话.创建(会话号,已加载['events'],已加载['header'],继承)#回放校验
        return {'session':结构化克隆(已加载['header']),'inheritedEventCount':继承,'events':[快照会话事件(事件) for 事件 in 已加载['events']]}#日志快照

    def 过滤会话(自身,过滤器列表,信号=None):
        """用与提供方无关的谓词过滤完整逻辑语料。"""
        已物化=物化会话结果过滤器(过滤器列表)#物化过滤器所有权
        return 自身._内部过滤会话(已物化,信号)#走内部过滤

    def 读取标题(自身,会话号,信号=None):
        """折叠最新标题；日志没有标题事件时为 None。"""
        观察=自身.读取标题快照(会话号,信号)#单条观察
        return 观察['title'] if 'title' in 观察 else None#只要标题字段

    def 读取标题快照(自身,会话号,信号=None):
        """折叠最新标题，并返回同一次语料观察的源头。"""
        结果=自身.批量读取标题快照([会话号],信号)[0]#单条批量观察
        if 结果['status']=='rejected':
            raise 结果['reason']#抛出原因
        return 结果['value']#成功观察

    def 批量读取标题快照(自身,会话号列表,信号=None):
        """在一次可取消的语料观察里为去重后的会话折叠标题。"""
        def 投影(源):
            """从事件折叠标题并组装观察。"""
            标题=折叠会话标题(源['events'])#折叠标题
            观察={'session':结构化克隆(源['header']),'inheritedEventCount':源['inheritedEventCount'] if 'inheritedEventCount' in 源 else 0}#克隆源头
            if 标题 is not None:#有标题才带上
                观察['title']=标题#写入标题
            return 观察#单条观察
        return 自身._语料库.批量投影(会话号列表,投影,信号)#投影结束

    def 列出事件(自身,会话号):
        """列出一条逻辑会话的轻量原始日志事件记录。"""
        已加载=自身._语料库.加载(会话号)#加载会话
        return 追踪事件记录(会话号,已加载['events'])#编成事件记录

    def 过滤事件(自身,会话号,过滤器列表):
        """用与提供方无关的过滤器扫描第一方语义事件文档。"""
        已物化=物化会话事件结果过滤器(过滤器列表)#物化过滤器所有权
        return 自身._内部过滤事件(会话号,已物化)#走内部过滤

    def _内部过滤会话(自身,过滤器列表,信号=None):
        """列出后再按过滤器筛。"""
        return 过滤会话结果(自身._语料库.列出会话(信号),过滤器列表)#列出后再过滤

    def _内部过滤事件(自身,会话号,过滤器列表):
        """建成检索文档后再按过滤器筛。"""
        已加载=自身._语料库.加载(会话号)#加载会话
        文档列表=构建会话事件搜索文档(会话号,已加载['events'])#建成检索文档
        return 过滤会话事件文档(文档列表,过滤器列表)#再按过滤器筛

    def 读取面(自身,会话号):
        """从一次语料观察读取一条会话当前完整的模型可见面。"""
        已加载=自身._语料库.加载(会话号)#加载会话
        事件列表=已加载['events']#原始事件
        return {
            'session':结构化克隆(已加载['header']),#克隆会话头
            'inheritedEventCount':已加载['inheritedEventCount'] if 'inheritedEventCount' in 已加载 else 0,#继承切口
            'capturedThroughSeq':事件列表[-1]['seq'] if len(事件列表)>0 else None,#最后seq
            'events':当前面事件(会话号,事件列表),#当前面事件
        }#面快照

    def 追踪会话谱系(自身,会话号,信号=None):
        """从一次语料观察追踪已知祖先与后代。"""
        记录列表=自身._语料库.列出会话(信号)#列出全部记录
        若已中止则抛出(信号)#列出后检查取消
        return 追踪会话(记录列表,会话号)#按记录追踪谱系

    def 追踪事件关系(自身,请求,信号=None):
        """追踪一条事件的直接位置替换与被引用源事件。"""
        已加载=自身._语料库.加载(请求['sessionId'],信号)#加载目标会话
        若已中止则抛出(信号)#加载后检查取消
        return {'session':已加载['header'],'inheritedEventCount':已加载['inheritedEventCount'] if 'inheritedEventCount' in 已加载 else 0,**追踪事件(请求['sessionId'],已加载['events'],请求['seq'])}#组装观察

    def 读取事件(自身,请求,信号=None):
        """读取一条完整事件，外加有界的原始日志上下文窗口。"""
        前窗口=自身._读取窗口('before',请求['before'] if 'before' in 请求 else None)#校验前窗口
        后窗口=自身._读取窗口('after',请求['after'] if 'after' in 请求 else None)#校验后窗口
        会话号=请求['sessionId']#目标会话
        序号=请求['seq']#目标序号
        return 自身._内部读取事件(会话号,序号,前窗口,后窗口,信号)#走内部读取

    def _内部读取事件(自身,会话号,序号,前窗口,后窗口,信号=None):
        """读取目标事件与相邻窗口。"""
        已加载=自身._语料库.加载(会话号,信号)#加载会话
        若已中止则抛出(信号)#加载后检查取消
        事件列表=已加载['events']#原始日志
        目标=事件列表[序号] if 序号<len(事件列表) else None#按序号取目标
        if 目标 is None or 目标['seq']!=序号:#缺席或序号对不上
            raise 会话查询错误('会话 "'+str(会话号)+'" 没有 seq '+str(序号)+' 的事件','SESSION_QUERY_EVENT_NOT_FOUND')#未找到
        起点=max(0,序号-前窗口)#窗口起点
        终点=min(len(事件列表)-1,序号+后窗口)#窗口终点
        目标快照=快照会话事件(目标)#目标事件快照
        窗口事件=[]#窗口事件
        for 事件 in 事件列表[起点:终点+1]:#切出窗口
            窗口事件.append(目标快照 if 事件 is 目标 else 快照会话事件(事件))#目标复用快照
        return {
            'session':结构化克隆(已加载['header']),#克隆会话头
            'inheritedEventCount':已加载['inheritedEventCount'] if 'inheritedEventCount' in 已加载 else 0,#继承切口
            'target':目标快照,#目标快照
            'events':窗口事件,#窗口事件
            'startSeq':起点,#起点序号
            'endSeq':终点,#终点序号
        }#返回窗口

    def _读取窗口(自身,名,值):
        """校验 before/after 窗口参数。"""
        if 值 is None:#缺省为0
            return 0#默认0
        if isinstance(值,bool) or (not isinstance(值,int)) or 值<0 or 值>自身._读取窗口上限:#必须落在上限内
            raise 会话查询错误(名+' 必须是 0 到 '+str(自身._读取窗口上限)+' 之间的整数','SESSION_QUERY_INVALID_WINDOW')#窗口非法
        return 值#返回合法窗口

包名='@deepseek-ai/dsh-session-query'
名称='session-query'
依赖=['sessions']
默认=会话查询引擎
name=名称#框架槽
inject=依赖#框架槽
default=默认#框架槽
会话查询引擎.inject=依赖#框架槽

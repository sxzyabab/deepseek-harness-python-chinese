"""轨迹快照构建器：把会话视图贡献压成舞台向的 TrajectorySnapshot。

对齐上游 `ui-trajectory/src/client/trajectory-snapshot-builder.ts`。公开面仅中文名。
"""
from .约定 import 空轨迹快照#空快照
from .轨迹记录 import 取字段#读字段

__all__=['空轨迹快照','轨迹快照构建器','轨迹视图定义','登记轨迹会话视图']#仅中文公开名

def 步键(回合,步号):#回合与步合成键
    """NUL 分隔回合与步。"""
    return f'{回合}\u0000{步号}'#合成键

def 请求头步键(请求头):#请求头对应的步键
    """仅步位置可合成键。"""
    位置=取字段(请求头,'location')#取出位置
    if 取字段(位置,'kind')!='step':#非步位置
        return None#无键
    return 步键(取字段(取字段(位置,'turn'),'turn'),取字段(取字段(位置,'step'),'step'))#用回合号与步号

def 查找请求头(请求,按步请求头,上一条):#按请求查找适用的请求头
    """精确步键优先，否则用早于本请求的上一条。"""
    命中=按步请求头.get(步键(取字段(请求,'turn'),取字段(请求,'step')))#精确步键
    if 命中 is not None:#命中
        return 命中#用之
    if 上一条 is not None and 取字段(上一条,'seq')<取字段(请求,'startSeq'):#早于本请求
        return 上一条#回退
    return None#无

def 叠请求头(请求,请求头,带变更):#把请求头叠到助手请求上
    """叠 prompt、config，按需叠 change。"""
    if 请求头 is None:#无头则不改
        return 请求#原样
    结果=dict(请求) if isinstance(请求,dict) else {'purpose':取字段(请求,'purpose'),'startSeq':取字段(请求,'startSeq'),'turn':取字段(请求,'turn'),'step':取字段(请求,'step'),'startedAt':取字段(请求,'startedAt'),'completedAt':取字段(请求,'completedAt'),'status':取字段(请求,'status')}#拷贝
    结果['prompt']=取字段(请求头,'prompt')#用头上的提示快照
    结果['requestConfig']=取字段(取字段(请求头,'prompt'),'config')#同步请求配置
    if 带变更 and 取字段(请求头,'change') is not None:#首次消费才带变更
        结果['promptChange']=取字段(请求头,'change')#变更
    return 结果#叠过头

def 写请求配置(节点,提示):#把提示配置写到助手消息节点
    """有提示才写 requestConfig。"""
    if 提示 is None:#无提示
        return 节点#原样
    结果=dict(节点) if isinstance(节点,dict) else dict((键,取字段(节点,键)) for 键 in ('kind','seq','time','turn','step','blocks','usage','messageId','provenance','timing','interrupted'))#拷贝
    结果['requestConfig']=取字段(提示,'config')#写 requestConfig
    return 结果#写过 config

def 索引工具(工具们):#按名字索引工具模式
    """按工具名索引模式。"""
    return {取字段(工具,'name'):工具 for 工具 in 工具们}#按名索引

def 采集模式(块,按名工具,输出):#把工具调用树的模式写入输出表
    """递归子调用。"""
    if isinstance(块,dict) and 'kind' in 块:#已结算取 call.name
        调用=取字段(块,'call')#调用元数据
        名称=取字段(调用,'name') if 调用 is not None else None#call.name
    else:#进行中取 name
        名称=取字段(块,'name')#name
    模式=按名工具.get(名称) if 名称 is not None else None#按名查模式
    if 模式 is not None:#有模式则记下
        输出[取字段(块,'callId')]=模式#记下
    for 子 in 取字段(块,'subCalls') or []:#递归子调用
        采集模式(子,按名工具,输出)#递归

def 打断压缩(请求们,边界们):#会话结束边界打断仍在跑的压缩请求
    """就地改写请求列表。"""
    下一请求=0#尚未扫过的请求下标
    进行中=[]#仍 running 的压缩请求下标栈
    for 边界 in 边界们:#按每条会话结束边界
        while 下一请求<len(请求们):#扫到边界序号之前的请求
            请求=请求们[下一请求]#当前请求
            if 取字段(请求,'startSeq')>=取字段(边界,'seq'):#已到边界后
                break#停
            if 取字段(请求,'purpose')=='compaction' and 取字段(请求,'status')=='running':#进行中的压缩
                进行中.append(下一请求)#入栈
            下一请求+=1#继续
        下标=进行中.pop() if 进行中 else None#弹出最近一条压缩
        while 下标 is not None and 取字段(请求们[下标],'status')!='running':#已不 running 则再弹
            下标=进行中.pop() if 进行中 else None#跳过已结算的
        if 下标 is None:#本边界没有可打断的压缩
            continue#下一条边界
        请求=请求们[下标]#取出该压缩请求
        if 取字段(请求,'purpose')!='compaction':#防御
            continue#跳过
        新请求=dict(请求) if isinstance(请求,dict) else dict(请求.__dict__) if hasattr(请求,'__dict__') else {}#拷贝
        新请求['completedAt']=取字段(边界,'time')#完成时间取边界时间
        新请求['status']='error'#标出错
        新请求['error']='Compaction was interrupted before completion.'#压缩未完成即被打断
        请求们[下标]=新请求#就地替换

def 落回合错误(请求们,结束们):#把回合结束错误落到该回合最后一条助手请求
    """就地改写请求列表。"""
    最后助手={}#回合 → 最后一条助手请求下标
    for 序号,请求 in enumerate(请求们):#扫全部请求
        if 取字段(请求,'purpose')=='assistant':#助手
            最后助手[取字段(请求,'turn')]=序号#后写覆盖
    for 结束 in 结束们:#每条回合结束
        if 取字段(结束,'error') is None:#无错误
            continue#不落
        序号=最后助手.get(取字段(结束,'turn'))#该回合最后助手请求
        if 序号 is None:#该回合没有助手请求
            continue#跳过
        请求=请求们[序号]#取出该请求
        if 取字段(请求,'purpose')!='assistant':#防御
            continue#跳过
        新请求=dict(请求) if isinstance(请求,dict) else {}#拷贝
        新请求['completedAt']=取字段(请求,'completedAt') if 取字段(请求,'completedAt') is not None else 取字段(结束,'time')#已有完成时间优先
        新请求['status']='error'#标出错
        新请求['error']=取字段(结束,'error')#写入回合错误文案
        请求们[序号]=新请求#就地替换

class 轨迹快照构建器:#轨迹快照构建器
    """带键适配器：保留旧的轨迹快照与舞台布局。"""
    def __init__(自身):#空构建器
        """初始化节点表与贡献列表。"""
        自身.节点={}#按 key 收节点
        自身.位置={}#key → contributions 下标
        自身.贡献=[]#按锚点序的贡献列表
        自身.empty=空轨迹快照#空快照，构建器缺省值

    def replace(自身,输入):#全量替换节点并重算快照
        """返回新快照。"""
        自身.节点.clear()#丢掉旧节点
        for 节点 in 取字段(输入,'nodes') or []:#新的全量节点
            自身.节点[取字段(节点,'key')]=节点#按 key 写入
        自身.重建贡献()#按锚点重排贡献
        return 自身.快照()#投影快照

    def apply(自身,输入):#增量 upsert 节点并重算快照
        """返回新快照。"""
        结构变化=False#是否需要整表重排
        for 节点 in 取字段(输入,'upserts') or []:#逐条 upsert
            键=取字段(节点,'key')#节点键
            先前=自身.节点.get(键)#旧节点
            自身.节点[键]=节点#覆盖写入
            if 先前 is None or 取字段(先前,'anchorSeq')!=取字段(节点,'anchorSeq'):#新增或锚点变了
                结构变化=True#必须重排
                continue#跳过就地替换
            下标=自身.位置.get(键)#已有下标
            if 下标 is None:#索引丢了也重排
                结构变化=True#重排
            else:#锚点未变则就地换节点
                自身.贡献[下标]=节点#就地替换
        if 结构变化:#结构变了才重排
            自身.重建贡献()#重排
        return 自身.快照()#投影快照

    def 快照(自身):#把贡献列表压成轨迹快照
        """按锚点序折叠贡献。"""
        按步请求头={}#步键 → 请求头
        for 贡献 in 自身.贡献:#先扫一遍请求头
            数据=取字段(贡献,'data')#载荷
            if 取字段(数据,'kind')!='request-header':#非请求头
                continue#跳过
            键=请求头步键(取字段(数据,'header'))#合成步键
            if 键 is not None:#有键则记下
                按步请求头[键]=取字段(数据,'header')#记下
        已结算=[]#已结算的会话节点
        事件位置={}#序号 → 位置
        请求们=[]#助手与压缩请求
        边界们=[]#会话结束边界
        回合结束=[]#回合结束
        调用模式={}#callId → 工具模式
        已消费变更=set()#已消费的 promptChange 序号
        上一条请求头=None#最近一条请求头
        上一工具=索引工具([])#最近请求头的工具索引
        流式=None#流式部分助手
        进行中=[]#进行中的工具调用
        for 贡献 in 自身.贡献:#按锚点序折叠贡献
            数据=取字段(贡献,'data')#取出载荷
            种类=取字段(数据,'kind')#贡献种类
            if 种类=='request-header':#请求头：只更新回退上下文
                上一条请求头=取字段(数据,'header')#记下当前头
                上一工具=索引工具(取字段(取字段(上一条请求头,'prompt'),'tools') or [])#重建工具索引
                continue#请求头本身不进快照集合
            if 种类=='node':#普通会话节点
                节点=取字段(数据,'node')#会话节点
                已结算.append(节点)#进事件节点
                事件位置[取字段(节点,'seq')]=取字段(贡献,'location')#记下位置
                continue#下一条
            if 种类=='assistant':#助手贡献
                请求=取字段(数据,'request')#助手请求
                请求头=None if 请求 is None else 查找请求头(请求,按步请求头,上一条请求头)#按步或回退找头
                节点=取字段(数据,'node')#助手节点
                if 节点 is not None:#有节点则写 config 后入列
                    已结算.append(写请求配置(节点,取字段(请求头,'prompt') if 请求头 is not None else None))#入列
                if 取字段(数据,'partial') is not None:#有部分助手则覆盖
                    流式=取字段(数据,'partial')#覆盖
                if 请求 is not None:#有请求则叠头后入列
                    带变更=请求头 is not None and 取字段(请求头,'change') is not None and 取字段(请求头,'seq') not in 已消费变更#首次消费
                    请求们.append(叠请求头(请求,请求头,带变更))#叠头后推入
                    if 带变更:#标记已消费
                        已消费变更.add(取字段(请求头,'seq'))#标记
                continue#下一条
            if 种类=='tool':#工具调用树
                根=取字段(数据,'root')#工具调用根块
                if isinstance(根,dict) and 'kind' in 根:#已结算则进事件节点
                    已结算.append(根)#入列
                else:#进行中则进 runningCalls
                    进行中.append(根)#进行中
                if 上一条请求头 is not None and 取字段(上一条请求头,'seq')<取字段(贡献,'anchorSeq'):#头早于本贡献才采模式
                    采集模式(根,上一工具,调用模式)#按 callId 记下模式
                continue#下一条
            if 种类=='compaction':#压缩请求
                请求们.append(取字段(数据,'request'))#直接入请求列
                continue#下一条
            if 种类=='session-end':#会话结束
                边界们.append({'seq':取字段(数据,'seq'),'time':取字段(数据,'time')})#记下边界
                continue#下一条
            结束={'turn':取字段(数据,'turn'),'time':取字段(数据,'time')}#其余视为回合结束
            if 取字段(数据,'error') is not None:#有错误才展开
                结束['error']=取字段(数据,'error')#错误
            回合结束.append(结束)#记下
        请求们.sort(key=lambda 项:取字段(项,'startSeq'))#请求按起步序号排
        打断压缩(请求们,边界们)#边界打断未完成的压缩
        落回合错误(请求们,回合结束)#回合错误落到最后助手请求
        已结算.sort(key=lambda 项:取字段(项,'seq'))#事件节点按序号排
        return {'eventNodes':已结算,'eventLocations':事件位置,'requests':请求们,'callSchemas':调用模式,'partial':流式,'runningCalls':进行中}#组装快照

    def 重建贡献(自身):#按锚点序号重排贡献并重建下标
        """锚点优先，同锚点按 key。"""
        自身.贡献=sorted(自身.节点.values(),key=lambda 项:(取字段(项,'anchorSeq'),取字段(项,'key') or ''))#取出全部节点并排序
        自身.位置.clear()#丢掉旧下标
        for 序号,贡献 in enumerate(自身.贡献):#重建 key → 下标
            自身.位置[取字段(贡献,'key')]=序号#记下位置

轨迹视图定义={#轨迹视图定义
    'target':'trajectory',#投递到轨迹槽
    'create':lambda:轨迹快照构建器(),#每次创建新构建器
}#定义结束

def 登记轨迹会话视图(上下文):#向会话视图登记轨迹目标
    """登记舞台向的轨迹目标构建器。"""
    上下文.conversationViews.register(轨迹视图定义)#登记定义

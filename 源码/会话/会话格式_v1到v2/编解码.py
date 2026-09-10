"""已发布 v2 的冻结物理 JSON 编解码器。"""
from ...内核.会话.序号范围 import 编码序号范围,解码序号范围#序号范围编解码
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    会话格式计数,#格式计数
    快照会话格式产物,#快照产物
    快照会话格式json,#快照JSON
)#从会话格式导入
from .校验 import 断言已发布v2头,断言已发布v2物理产物#从校验导入

头必填=('type','version','id','createdAt','isSeeded','delegationDepth')#头必填
头可选=('cwd','parentSession','origin','agentPreset')#头可选

def 解码物理头(值):#解码物理头
    """解码已发布 v2 物理头为逻辑头。"""
    快照=快照会话格式json(值,'released v2 physical header')#快照
    记录=json记录(快照,'released v2 physical header')#记录
    精确键(记录,头必填,头可选,'released v2 physical header')#精确键
    if 记录['type']!='session' or 记录['version']!=2:#类型或版本不符
        raise 会话格式错误('expected released v2 physical Session header')#错误
    if not isinstance(记录['id'],str):#id非法
        raise 会话格式错误('released v2 header id must be a string')#id
    创建时间=会话格式计数(记录['createdAt'],'released v2 header createdAt')#创建时间
    委托深度=会话格式计数(记录['delegationDepth'],'released v2 header delegationDepth')#委托深度
    if not isinstance(记录['isSeeded'],bool):#种子非法
        raise 会话格式错误('released v2 header isSeeded must be boolean')#种子
    for 键 in ('cwd','parentSession','agentPreset'):#可选字符串字段
        if 键 in 记录 and not isinstance(记录[键],str):#类型不符
            raise 会话格式错误(f'released v2 header {键} must be a string')#错误
    if 'origin' in 记录 and 记录['origin']!='subagent':#origin非法
        raise 会话格式错误('released v2 header origin must be "subagent"')#错误
    逻辑头={'version':2,'id':记录['id'],'createdAt':创建时间,'isSeeded':记录['isSeeded'],'delegationDepth':委托深度}#逻辑头基
    if 'cwd' in 记录:#有cwd
        逻辑头['cwd']=记录['cwd']#cwd
    if 'parentSession' in 记录:#有父会话
        逻辑头['parentSession']=记录['parentSession']#父会话
    if 'origin' in 记录:#有来源
        逻辑头['origin']=记录['origin']#来源
    if 'agentPreset' in 记录:#有预设
        逻辑头['agentPreset']=记录['agentPreset']#预设
    头=快照会话格式json(逻辑头,'released v2 logical header')#快照逻辑头
    断言已发布v2头(头)#断言头
    return 头#返回头

def 解码产物实现(头值,行值列表,可恢复):#解码产物
    """解码物理头与行；可恢复时跳过畸形前缀直至 turn/end。"""
    头=解码物理头(头值)#解码头
    事件列表=[]#事件
    问题=None#问题
    for 行下标,值 in enumerate(行值列表):#遍历行
        try:#尝试解码
            事件=解码事件(值,行下标)#解码事件
        except BaseException as 错误:#捕获
            当前=错误 if isinstance(错误,会话格式错误) else 会话格式错误(f'released v2 row {行下标} is malformed',错误)#包装
            if not 可恢复:#不可恢复则抛
                raise 当前#抛出
            if 问题 is None:#记录首错
                问题=当前#记下
            continue#跳过
        if 问题 is not None:#已有问题
            if 事件['type']=='turn/end':#遇turn/end抛出
                raise 问题#抛出
            continue#否则跳过
        if 事件['seq']!=len(事件列表):#seq间隙
            间隙=会话格式错误(#间隙错误
                f'released v2 row {行下标} has seq gap (expected {len(事件列表)}, got {事件["seq"]})',#消息
            )#Error结束
            if not 可恢复:#不可恢复则抛
                raise 间隙#抛出
            问题=间隙#记录间隙
            if 事件['type']=='turn/end':#遇turn/end抛出
                raise 问题#抛出
            continue#跳过
        事件列表.append(事件)#推入事件
    继承事件数=推导继承事件数(头,事件列表)#推导继承数
    产物=快照会话格式产物({'header':头,'inheritedEventCount':继承事件数,'events':事件列表},'released v2 artifact')#快照
    断言已发布v2物理产物(产物)#断言物理产物
    return 产物#返回

class _v2解码器:#v2流式解码器
    """以显式失败策略逐行解码已发布 v2。"""
    def __init__(自身,头值,恢复):#构造
        """解码头并初始化行状态。"""
        自身.header=解码物理头(头值)#头
        自身._恢复=恢复#恢复策略
        自身._行下标=0#行号
        自身._事件数=0#事件数
        自身._继承事件数=None#继承数
        自身._问题=None#问题

    def decodeRow(自身,值,上下文):#解码行
        """解码一行并同步发出事件。"""
        当前行=自身._行下标#当前行
        自身._行下标+=1#递增
        try:#尝试解码
            事件=解码事件(值,当前行)#解码事件
        except BaseException as 错误:#捕获
            当前=错误 if isinstance(错误,会话格式错误) else 会话格式错误(f'released v2 row {当前行} is malformed',错误)#包装
            if 自身._恢复=='strict':#严格则抛
                raise 当前#抛出
            if 自身._问题 is None:#记录首错
                自身._问题=当前#记下
            return#返回
        if 自身._问题 is not None:#已有问题
            if 事件['type']=='turn/end':#遇回合结束抛出
                raise 自身._问题#抛出
            return#丢弃
        if 事件['seq']!=自身._事件数:#序号缺口
            间隙=会话格式错误(#缺口错误
                f'released v2 row {当前行} has seq gap (expected {自身._事件数}, got {事件["seq"]})',#消息
            )#构造结束
            if 自身._恢复=='strict':#严格则抛
                raise 间隙#抛出
            自身._问题=间隙#记录
            if 事件['type']=='turn/end':#遇回合结束抛出
                raise 自身._问题#抛出
            return#返回
        自身._事件数+=1#递增事件数
        if 事件['type']=='session/end-seed':#结束种子
            数据=json记录(事件['data'],f"session/end-seed {事件['seq']} data")#data
            if 数据.get('inherited') is True:#继承切口
                自身._继承事件数=事件['seq']#记下
        上下文.emitEvent(事件)#发出事件

    def finish(自身,_上下文):#完成
        """完成行校验并返回精确继承切口。"""
        if 自身.header['isSeeded'] and 自身._继承事件数 is None:#种子缺标记
            raise 会话格式错误('released v2 seeded Session lacks an inherited end-seed marker')#错误
        if (not 自身.header['isSeeded']) and 自身._继承事件数 is not None:#非种子却有标记
            raise 会话格式错误('released v2 unseeded Session contains an inherited end-seed marker')#错误
        return 0 if 自身._继承事件数 is None else 自身._继承事件数#返回继承数

def 编码头实现(头,继承事件数):#编码头
    """编码已发布 v2 物理头记录。"""
    断言已发布v2头(头)#断言头
    切割=会话格式计数(继承事件数,'format v2 inherited event count')#校验切口
    if not 头['isSeeded'] and 切割!=0:#非种子却有继承
        raise 会话格式错误('unseeded format v2 Session has inherited events')#错误
    物理头={'type':'session','version':2,'id':头['id'],'createdAt':头['createdAt'],'isSeeded':头['isSeeded'],'delegationDepth':头['delegationDepth']}#物理头基
    if 'cwd' in 头:#有cwd
        物理头['cwd']=头['cwd']#cwd
    if 'parentSession' in 头:#有父会话
        物理头['parentSession']=头['parentSession']#父会话
    if 'origin' in 头:#有来源
        物理头['origin']=头['origin']#来源
    if 'agentPreset' in 头:#有预设
        物理头['agentPreset']=头['agentPreset']#预设
    return 物理头#返回

def 解码事件(值,行下标):#解码事件
    """解码一行物理事件，压缩出处时展开。"""
    快照=快照会话格式json(值,f'released v2 row {行下标}')#快照
    记录=json记录(快照,f'released v2 row {行下标}')#记录
    if 'sourceEventSeqs' not in 记录:#无出处
        return 记录#无出处
    序号=会话格式计数(记录['seq'],f'released v2 row {行下标} seq')#序号
    带出处=dict(记录)#展开
    try:#内核解码
        带出处['sourceEventSeqs']=解码序号范围(记录['sourceEventSeqs'],序号)#解码范围
    except TypeError as 错误:#转为格式错误
        raise 会话格式错误(错误.args[0] if 错误.args else str(错误)) from 错误#包装
    return 快照会话格式json(带出处,f'released v2 row {行下标} provenance')#断言事件

def 推导继承事件数(头,事件列表):#推导继承数
    """从 inherited end-seed 标记推导继承切割。"""
    切割=None#切割点
    for 事件 in 事件列表:#遍历
        if 事件['type']!='session/end-seed':#非end-seed跳过
            continue#跳过
        数据=json记录(事件['data'],f"session/end-seed {事件['seq']} data")#data
        if 数据.get('inherited') is True:#继承标记
            切割=事件['seq']#记下
    if 头['isSeeded'] and 切割 is None:#种子缺标记
        raise 会话格式错误('released v2 seeded Session lacks an inherited end-seed marker')#错误
    if not 头['isSeeded'] and 切割 is not None:#非种子却有标记
        raise 会话格式错误('released v2 unseeded Session contains an inherited end-seed marker')#错误
    return 0 if 切割 is None else 切割#返回切割

def 编码产物实现(产物):#编码产物
    """编码已发布 v2 逻辑产物为物理头与行。"""
    断言已发布v2物理产物(产物)#断言物理
    头=产物['header']#头
    物理头基={'type':'session','version':2,'id':头['id'],'createdAt':头['createdAt'],'isSeeded':头['isSeeded'],'delegationDepth':头['delegationDepth']}#物理头基
    if 'cwd' in 头:#有cwd
        物理头基['cwd']=头['cwd']#cwd
    if 'parentSession' in 头:#有父会话
        物理头基['parentSession']=头['parentSession']#父会话
    if 'origin' in 头:#有来源
        物理头基['origin']=头['origin']#来源
    if 'agentPreset' in 头:#有预设
        物理头基['agentPreset']=头['agentPreset']#预设
    物理头=快照会话格式json(物理头基,'released v2 encoded header')#断言对象
    行列表=tuple(编码出处(事件) for 事件 in 产物['events'])#编码行
    return {'header':物理头,'rows':行列表}#返回

def 编码出处(事件):#编码出处
    """把 sourceEventSeqs 压缩为范围表示。"""
    if 'sourceEventSeqs' not in 事件:#无出处
        return 事件#无出处
    带压缩=dict(事件)#展开
    带压缩['sourceEventSeqs']=编码序号范围(事件['sourceEventSeqs'])#编码范围
    return 快照会话格式json(带压缩,f"released v2 event {事件['seq']} provenance")#断言对象

def json记录(值,标签):#JSON记录
    """要求值为非 null 非数组对象。"""
    if not isinstance(值,dict):#非对象
        raise 会话格式错误(f'{标签} must be an object')#错误
    return 值#断言

def 精确键(记录,必填,可选,标签):#精确键
    """要求恰好含必填键，且无意外键。"""
    允许=set(必填)|set(可选)#允许集
    for 键 in 必填:#缺键
        if 键 not in 记录:#缺键
            raise 会话格式错误(f'{标签} lacks {键}')#缺键错误
    for 键 in 记录.keys():#意外键
        if 键 not in 允许:#意外
            raise 会话格式错误(f'{标签} has unexpected field {键}')#意外错误

class 已发布v2会话格式编解码器类型:#v2编解码器
    """已发布 v2 的冻结物理 JSON 编解码器。"""
    version=2#版本

    def decodeHeader(自身,值):#解码头
        """把物理头解码为逻辑元数据。"""
        return 解码物理头(值)#解码物理头

    def createDecoder(自身,头值,恢复):#创建解码器
        """以显式失败策略创建逐行解码器。"""
        return _v2解码器(头值,恢复)#创建

    def encodeHeader(自身,头,继承事件数):#编码头
        """编码当代物理头记录。"""
        return 编码头实现(头,继承事件数)#编码头

    def encodeEvent(自身,事件):#编码事件
        """把一条逻辑事件编码为物理记录。"""
        return 编码出处(事件)#编码出处

    def decodeArtifact(自身,头值,行值列表):#解码产物
        """严格解码完整物理产物。"""
        return 解码产物实现(头值,行值列表,False)#严格解码

    def decodeRecoverableArtifact(自身,头值,行值列表):#可恢复解码
        """解码行原子可恢复前缀。"""
        return 解码产物实现(头值,行值列表,True)#可恢复

    def 编码产物(自身,产物):#编码产物
        """编码逻辑产物为物理头与行。"""
        return 编码产物实现(产物)#编码

    def encodeArtifact(自身,产物):#编码产物（上游键名）
        """编码逻辑产物为物理头与行。"""
        return 编码产物实现(产物)#编码

已发布v2会话格式编解码器=已发布v2会话格式编解码器类型()#v2编解码器单例

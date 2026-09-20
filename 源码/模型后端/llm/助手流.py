"""一次模型流尝试的无损紧凑表示。

公开面仅中文名；记录 type、块 type 与字段键为线协议原样保留。
无英文别名。
"""
import math,re#负零与非空白检测
from ...工具.值 import 快照json值#无损 JSON 脱离
from .永不 import 断言永不#穷尽检查
from .组装器 import 块组装器#块组装器
from .调用配置 import 深冻结#深冻结

__all__=(#仅中文公开名
    '助手流累积器',
    '展开助手流',
    '是否令牌增量',
    '是否可见块',
    '块是否含可见文本',
    '游程首令牌时间',
    '游程首可见时间',
    '助手流首令牌时间',
    '助手流是否有可见内容',
    '助手流是否有可见文本',
    '末条助手流块',
    '助手流块列表',
    '拼接助手流文本',
    '组装助手流',
)#公开面结束

安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER
非空白=re.compile(r'\S')#非空白检测

def _是否安全整数(值):#安全整数
    """值是否为 Number.isSafeInteger 意义上的安全整数。"""
    if isinstance(值,bool):#布尔不是整数
        return False#拒绝
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#范围
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return abs(值)<=安全整数上限#范围
    return False#其它

def _是否负零(值):#负零
    """是否为 IEEE 负零。"""
    return isinstance(值,float) and 值==0.0 and math.copysign(1.0,值)<0#负零

def _安全时间(值):#安全时间
    """校验助手流时间戳。"""
    if not _是否安全整数(值):#非法时间
        raise TypeError('Assistant stream time must be a safe integer, got '+str(值))#非法时间
    return int(值)#规范为 int

def _安全下标(值,标签):#安全下标
    """校验非负安全整数下标。"""
    if (not _是否安全整数(值)) or 值<0 or _是否负零(值):#非法下标
        raise TypeError(标签+' index must be a non-negative safe integer')#抛错
    return int(值)#规范为 int

def _快照块(块):#快照块
    """无损快照流块。"""
    快照=快照json值(块)#无损快照
    if 快照 is None:#不可序列化
        raise TypeError('Assistant stream chunk must be losslessly JSON-serializable')#不可序列化
    return 快照#返回快照

def _安全间隙(前,后):#安全间隙
    """可逆时间差；不可表示则 None。"""
    间隙=后-前#时间差
    if (not _是否安全整数(间隙)) or 前+间隙!=后:#不可逆
        return None#不可并
    return int(间隙)#可逆间隙

class 助手流累积器:#助手流累积器
    """增量压缩一次尝试，不另保留一份原始块列表。"""
    def __init__(自身):#构造
        """初始化空记录。"""
        自身._记录列表=[]#可变记录

    def 推入(自身,值):#推入带时块
        """向紧凑尝试流添加一块带时块。

        @param 值: 含 time 与 chunk 的带时块。
        @returns 供组装与实时发布用的拆离不可变副本。
        """
        时间=_安全时间(值['time'])#校验时间
        块=_快照块(值['chunk'])#快照块
        带时=深冻结({'time':时间,'chunk':块})#冻结带时副本
        前=自身._记录列表[-1] if 自身._记录列表 else None#末条记录
        类型=块['type']#块类型
        if 类型=='text-delta' or 类型=='reasoning-delta':#文本或推理增量
            _安全下标(块['index'],类型)#校验下标
            if not isinstance(块.get('text'),str):#文本须串
                raise TypeError(类型+' text must be a string')#文本须串
            记录类型='text-chunks' if 类型=='text-delta' else 'reasoning-chunks'#记录类型
            间隙=_安全间隙(前['lastTime'],时间) if 前 is not None and 前['type']==记录类型 else None#可并间隙
            if (前 is not None and 前['type']==记录类型 and 前['index']==块['index'] and 间隙 is not None):#可合并
                前['dt'].append(间隙)#追加时间差
                前['texts'].append(块['text'])#追加文本
                前['lastTime']=时间#更新末时
            else:#新开游程
                自身._记录列表.append({#推入
                    'type':记录类型,#类型
                    'time0':时间,#首时
                    'index':块['index'],#下标
                    'dt':[],#空时间差
                    'texts':[块['text']],#首文本
                    'lastTime':时间,#末时
                })#push 结束
            return 带时#返回副本
        if 类型=='tool-call-delta':#工具调用增量
            _安全下标(块['index'],类型)#校验下标
            if not isinstance(块.get('id'),str):#id 须串
                raise TypeError('tool-call-delta id must be a string')#抛错
            if 'name' in 块 and not isinstance(块['name'],str):#name 类型错
                raise TypeError('tool-call-delta name must be a string')#抛错
            if not isinstance(块.get('argumentsDelta'),str):#参数增量类型错
                raise TypeError('tool-call-delta argumentsDelta must be a string')#抛错
            if len(块['id'])==0 or 块.get('name')=='':#空 id 或空名
                自身._记录列表.append({'type':'chunk','time':时间,'chunk':块})#退回原始块
                return 带时#返回副本
            间隙=_安全间隙(前['lastTime'],时间) if 前 is not None and 前['type']=='tool-call-chunks' else None#可并间隙
            同名=(前 is not None and 前['type']=='tool-call-chunks'
                and (('name' in 前)==('name' in 块))
                and 前.get('name')==块.get('name'))#同名
            if (前 is not None and 前['type']=='tool-call-chunks'
                and 前['index']==块['index'] and 前['id']==块['id']
                and 同名 and 间隙 is not None):#可合并
                前['dt'].append(间隙)#追加时间差
                前['args'].append(块['argumentsDelta'])#追加参数
                前['lastTime']=时间#更新末时
            else:#新开游程
                记录={#工具调用游程
                    'type':'tool-call-chunks',#类型
                    'time0':时间,#首时
                    'index':块['index'],#下标
                    'dt':[],#空时间差
                    'id':块['id'],#调用 id
                    'args':[块['argumentsDelta']],#首参数片段
                    'lastTime':时间,#末时
                }#记录结束
                if 'name' in 块:#可选名
                    记录['name']=块['name']#记下
                自身._记录列表.append(记录)#推入
            return 带时#返回副本
        if 类型 in ('block-start','block-end','usage','finish'):#原始块
            自身._记录列表.append({'type':'chunk','time':时间,'chunk':块})#按原始块存
            return 带时#返回副本
        return 断言永不(块,'AssistantStreamAccumulator.push')#不可达

    def 快照(自身):#快照
        """返回当前紧凑尝试流。"""
        输出=[]#结果
        for 记录 in 自身._记录列表:#映射耐久记录
            if 记录['type']=='chunk':#原始块
                输出.append(dict(记录))#浅拷
                continue#下一条
            耐久={键:值 for 键,值 in 记录.items() if 键!='lastTime'}#去掉运行时末时
            if 耐久['type']=='tool-call-chunks':#工具调用
                输出.append({**耐久,'dt':list(耐久['dt']),'args':list(耐久['args'])})#拷贝数组
            else:#文本/推理
                输出.append({**耐久,'dt':list(耐久['dt']),'texts':list(耐久['texts'])})#拷贝
        return 深冻结(输出)#深冻结返回

def 展开助手流(流):#展开助手流
    """把紧凑记录展开为精确带时块序列。

    @param 流: 一次持久助手结算的紧凑记录。
    @returns 保留每个原始增量边界的拆离带时块。
    @raises TypeError: 当记录或重建时间戳非法时。
    """
    块列表=[]#结果
    for 候选 in 流:#逐记录
        记录=_校验记录(候选)#校验
        if 记录['type']=='chunk':#原始块
            块列表.append({'time':记录['time'],'chunk':记录['chunk']})#直接推入
            continue#下一条
        成员=记录['args'] if 记录['type']=='tool-call-chunks' else 记录['texts']#成员序列
        时间=记录['time0']#起始时间
        for 下标 in range(len(成员)):#逐成员
            if 下标>0:#累加时间差
                时间=时间+记录['dt'][下标-1]#推进
            if 记录['type']=='text-chunks':#文本
                块={'type':'text-delta','index':记录['index'],'text':成员[下标]}#文本增量
            elif 记录['type']=='reasoning-chunks':#推理
                块={'type':'reasoning-delta','index':记录['index'],'text':成员[下标]}#推理增量
            else:#工具调用
                块={#工具调用增量
                    'type':'tool-call-delta',#类型
                    'index':记录['index'],#下标
                    'id':记录['id'],#调用 id
                    'argumentsDelta':成员[下标],#参数片段
                }#chunk 结束
                if 'name' in 记录:#可选名
                    块['name']=记录['name']#带上
            块列表.append({'time':时间,'chunk':块})#推入带时块
    return 块列表#返回序列

def _含非空白(文本):#是否含非空白
    """文本是否含非空白字符。"""
    return 非空白.search(文本) is not None#正则检测

def _块是否读者可见(块):#块是否读者可见
    """完成内容块是否对 transcript 读者可见。"""
    if 块['type']=='tool-call':#工具调用不算内容
        return False#不可见
    if 块['type']=='text' or 块['type']=='reasoning':#文本/推理
        return _含非空白(块['text'])#须非空白
    return True#其余块类型可见

def 是否令牌增量(块):#是否令牌增量
    """一块是否携带模型首枚输出令牌，供延迟测量。"""
    类型=块['type']#块类型
    if 类型=='text-delta' or 类型=='reasoning-delta':#文本或推理增量
        return 块['text']!=''#非空文本
    if 类型=='tool-call-delta':#工具调用增量
        return 块['argumentsDelta']!='' or 'name' in 块#非空参数或带名
    return False#不算令牌

def 是否可见块(块):#是否可见块
    """单块本身是否贡献读者可见的 transcript 内容。"""
    类型=块['type']#块类型
    if 类型=='text-delta' or 类型=='reasoning-delta':#文本或推理增量
        return _含非空白(块['text'])#须非空白
    if 类型=='block-start':#块开始
        return 块['blockType']!='text' and 块['blockType']!='reasoning' and 块['blockType']!='tool-call'#非文本/推理/工具
    if 类型=='block-end':#块结束
        return _块是否读者可见(块['block'])#按完成块判断
    return False#不可见

def 块是否含可见文本(块):#块是否含可见文本
    """一块是否携带非空白文本，作为文本增量或完成的文本块。"""
    if 块['type']=='text-delta':#文本增量
        return _含非空白(块['text'])#文本增量
    return 块['type']=='block-end' and 块['block']['type']=='text' and _含非空白(块['block']['text'])#完成文本块

def _游程首匹配成员时间(游程,谓词):#游程首匹配成员时间
    """扫描打包游程，返回首个谓词为真的成员时间。"""
    片段=游程['args'] if 游程['type']=='tool-call-chunks' else 游程['texts']#成员序列
    时间=游程['time0']#起始时间
    for 下标 in range(len(片段)):#逐成员
        if 下标>0:#累加时间差
            时间=时间+游程['dt'][下标-1]#推进
        if 谓词(片段[下标]):#首匹配
            return 时间#返回
    return None#无匹配

def 游程首令牌时间(游程):#游程首令牌时间
    """一条打包游程中 isTokenDelta 接受的首个成员的时间。"""
    if 游程['type']=='tool-call-chunks' and 'name' in 游程:#带名工具调用游程
        return 游程['time0']#自首成员起算
    return _游程首匹配成员时间(游程,lambda 片段:片段!='')#首个非空片段

def 游程首可见时间(游程):#游程首可见时间
    """一条打包游程中 isVisibleChunk 接受的首个成员的时间。"""
    if 游程['type']=='tool-call-chunks':#工具调用游程没有
        return None#无
    return _游程首匹配成员时间(游程,_含非空白)#文本/推理游程

def 助手流首令牌时间(流):#助手流首令牌时间
    """一条紧凑流中按是否令牌增量计的首枚令牌时间。"""
    for 记录 in 流:#逐记录
        if 记录['type']=='chunk':#原始块
            时间=记录['time'] if 是否令牌增量(记录['chunk']) else None#按 isTokenDelta
        else:#游程
            时间=游程首令牌时间(记录)#游程首令牌
        if 时间 is not None:#首命中
            return 时间#返回
    return None#无令牌

def 助手流是否有可见内容(流):#助手流是否有可见内容
    """一条紧凑流是否按是否可见块携带任何读者可见内容。"""
    for 记录 in 流:#逐记录
        if 记录['type']=='chunk':#原始块
            if 是否可见块(记录['chunk']):#可见
                return True#有
        elif 游程首可见时间(记录) is not None:#游程可见
            return True#有
    return False#无

def 助手流是否有可见文本(流):#助手流是否有可见文本
    """一条紧凑流是否按块是否含可见文本携带非空白文本。"""
    for 记录 in 流:#逐记录
        if 记录['type']=='text-chunks':#文本游程
            for 文本 in 记录['texts']:#任一成员
                if _含非空白(文本):#非空白
                    return True#有
        elif 记录['type']=='chunk' and 块是否含可见文本(记录['chunk']):#原始可见文本块
            return True#有
    return False#无

def 末条助手流块(流,类型):#最后原始块
    """一种从不打包的原始块类型的最后一块，自后向前扫描。"""
    for 下标 in range(len(流)-1,-1,-1):#自后向前
        记录=流[下标]#当前记录
        if 记录['type']=='chunk' and 记录['chunk']['type']==类型:#命中
            return 记录['chunk']#返回
    return None#无此类型

def 助手流块列表(流,类型):#全部原始块
    """一种从不打包的原始块类型的全部块，按流顺序。"""
    块列表=[]#结果
    for 记录 in 流:#逐记录
        if 记录['type']=='chunk' and 记录['chunk']['type']==类型:#收集
            块列表.append(记录['chunk'])#记下
    return 块列表#返回

def 拼接助手流文本(流):#拼接助手流文本
    """按流顺序拼接的全部 text-delta 片段；排除推理与工具调用片段。"""
    片段=[]#片段
    for 记录 in 流:#逐记录
        if 记录['type']=='text-chunks':#文本游程
            片段.append(''.join(记录['texts']))#拼接游程
        elif 记录['type']=='chunk' and 记录['chunk']['type']=='text-delta':#原始文本增量
            片段.append(记录['chunk']['text'])#追加
    return ''.join(片段)#拼接返回

def 组装助手流(流,组装器=None):#组装助手流
    """把一条紧凑流喂入块组装器而不物化成员。

    每条游程贡献一个携带其拼接片段的增量；原始块按记录推入。记录被信任、不校验：
    在耐久边界读到的流请先用展开助手流校验。
    """
    if 组装器 is None:#默认新建
        组装器=块组装器()#新建
    for 记录 in 流:#逐记录
        类型=记录['type']#记录类型
        if 类型=='chunk':#原始块
            组装器.推入(记录['chunk'])#直接推入
        elif 类型=='text-chunks':#文本游程
            组装器.推入({'type':'text-delta','index':记录['index'],'text':''.join(记录['texts'])})#合并文本增量
        elif 类型=='reasoning-chunks':#推理游程
            组装器.推入({'type':'reasoning-delta','index':记录['index'],'text':''.join(记录['texts'])})#合并推理增量
        elif 类型=='tool-call-chunks':#工具调用游程
            块={#合并工具调用增量
                'type':'tool-call-delta',#类型
                'index':记录['index'],#下标
                'id':记录['id'],#调用 id
                'argumentsDelta':''.join(记录['args']),#拼接参数
            }#块结束
            if 'name' in 记录 and 记录['name'] is not None:#可选名
                块['name']=记录['name']#带上
            组装器.推入(块)#推入
        else:#穷尽
            断言永不(记录,'assembleAssistantStream')#不可达
    return 组装器#返回组装器

def _精确键(记录,键列表,标签):#精确键
    """记录键集必须恰好等于给定键列表。"""
    if len(记录)!=len(键列表) or any(键 not in 记录 for 键 in 键列表):#键集不符
        raise TypeError(标签+' Assistant stream record must contain exactly '+', '.join(键列表))#抛错

def _字符串数组(值,标签):#字符串数组
    """校验字符串数组。"""
    if not isinstance(值,list) or any(not isinstance(成员,str) for 成员 in 值):#非串数组
        raise TypeError(标签+' must be a string array')#抛错
    return 值#返回

def _校验游程(记录,成员数,标签):#校验游程
    """校验打包游程的时间与下标。"""
    _安全时间(记录['time0'])#校验首时
    _安全下标(记录['index'],标签)#校验下标
    时间差=记录['dt']#dt
    if not isinstance(时间差,list) or any(not _是否安全整数(值) for 值 in 时间差):#dt 非法
        raise TypeError(标签+' dt must contain safe integers')#抛错
    if len(时间差)!=成员数-1:#长度不符
        raise TypeError(标签+' dt length must be one less than its members')#抛错
    时间=记录['time0']#重建时间
    for 间隙 in 时间差:#累加间隙
        时间=时间+间隙#推进
        if not _是否安全整数(时间):#溢出
            raise TypeError(标签+' member times must stay safe integers')#溢出

def _校验记录(值):#校验记录
    """校验一条助手流记录。"""
    if not isinstance(值,dict):#非对象
        raise TypeError('Assistant stream record must be an object')#抛错
    类型=值.get('type')#类型
    if 类型=='text-chunks' or 类型=='reasoning-chunks':#文本/推理游程
        _精确键(值,['type','time0','index','dt','texts'],类型)#键精确
        文本=_字符串数组(值['texts'],类型+' texts')#文本数组
        if len(文本)==0:#非空
            raise TypeError(类型+' texts must be non-empty')#非空
        _校验游程(值,len(文本),类型)#校验游程
        return 值#返回
    if 类型=='tool-call-chunks':#工具调用游程
        if 'name' in 值:#是否有 name
            键列表=['type','time0','index','dt','id','name','args']#含 name 键集
        else:#无 name
            键列表=['type','time0','index','dt','id','args']#无 name 键集
        _精确键(值,键列表,类型)#键精确
        参数=_字符串数组(值['args'],'tool-call-chunks args')#参数数组
        if len(参数)==0:#非空
            raise TypeError('tool-call-chunks args must be non-empty')#非空
        if not isinstance(值.get('id'),str) or len(值['id'])==0:#id 非法
            raise TypeError('tool-call-chunks id must be a non-empty string')#抛错
        if 'name' in 值 and (not isinstance(值['name'],str) or len(值['name'])==0):#name 非法
            raise TypeError('tool-call-chunks name must be a non-empty string')#抛错
        _校验游程(值,len(参数),类型)#校验游程
        return 值#返回
    if 类型=='chunk':#原始块
        _精确键(值,['type','time','chunk'],'chunk')#键精确
        时间=_安全时间(值['time'])#校验时间
        块值=值['chunk']#块
        if not isinstance(块值,dict):#块非对象
            raise TypeError('Assistant stream raw chunk must be a lossless JSON object')#抛错
        try:#尝试快照
            块=_快照块(块值)#快照
        except TypeError as 错误:#失败
            raise TypeError('Assistant stream raw chunk must be a lossless JSON object') from 错误#包装抛错
        return 深冻结({'type':'chunk','time':时间,'chunk':块})#冻结返回
    raise TypeError('Unsupported Assistant stream record '+repr(类型))#未知类型

# 与并行落地约定的公开别名（迁移／回放／统计优先用这些）
助手流累加器=助手流累积器#约定名
末次助手流块=末条助手流块#约定名
块含可见文本=块是否含可见文本#简名
助手流有可见内容=助手流是否有可见内容#简名
助手流有可见文本=助手流是否有可见文本#简名
__all__=(*__all__,'助手流累加器','末次助手流块','块含可见文本','助手流有可见内容','助手流有可见文本')#补别名

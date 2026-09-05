"""已发布 v0/v1 布局的冻结物理 JSON 编解码器。"""
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    是否会话格式json对象,#是否JSON对象
    会话格式计数,#格式计数
    会话格式安全整数,#安全整数
    快照会话格式产物,#快照产物
    快照会话格式json,#快照JSON
)#从会话格式导入
from ..会话格式.json import 是否安全整数#安全整数判定
from .校验 import (#从校验导入
    断言已发布会话格式头,#断言会话头
    断言已发布v0源产物,#断言v0源产物
    断言已发布v1物理产物,#断言v1物理产物
)#从校验导入
from .校验辅助 import 断言已发布v0键,已发布v0记录#从辅助导入

物理头必填=('type','version','id','createdAt','delegationDepth')#物理头必填
物理头可选=('cwd','parentSession','seedLength','origin','agentPreset')#物理头可选
打包标签=frozenset(['text-chunks','reasoning-chunks','tool-call-chunks'])#打包标签

def 创建已发布编解码器(版本):#创建已发布编解码器
    """为版本 0 或 1 冻结一份物理 JSON 编解码器。"""
    return _已发布编解码器(版本)#编解码器实例

class _已发布编解码器:#已发布编解码器
    """已发布 v0/v1 物理 JSON 编解码器。"""
    def __init__(自身,版本):#记下版本
        """记下物理版本。"""
        自身.version=版本#版本

    def decodeHeader(自身,值):#解码头
        """把物理头解码为逻辑头。"""
        return 解码物理头(值,自身.version)['header']#取逻辑头

    def decodeArtifact(自身,头值,行值们):#解码产物
        """严格解码完整物理产物。"""
        物理=解码物理头(头值,自身.version)#解码物理头
        产物=快照会话格式产物({#快照产物
            'header':物理['header'],#头
            'inheritedEventCount':物理['inheritedEventCount'],#继承数
            'events':扫描行(行值们,False)['events'],#事件
        },f'released v{自身.version} artifact')#标签
        if 自身.version==0:#v0
            断言已发布v0源产物(产物)#断言v0
        else:#v1
            断言已发布v1物理产物(产物)#断言v1
        return 产物#返回

    def decodeRecoverableArtifact(自身,头值,行值们):#可恢复解码
        """解码行原子可恢复前缀。"""
        物理=解码物理头(头值,自身.version)#解码物理头
        恢复=扫描行(行值们,True)#可恢复扫描
        产物=快照会话格式产物({#快照产物
            'header':物理['header'],#头
            'inheritedEventCount':物理['inheritedEventCount'],#继承数
            'events':恢复['events'],#事件
        },f'released v{自身.version} recoverable artifact')#标签
        if 自身.version==0:#v0
            断言已发布v0源产物(产物)#断言v0
        else:#v1
            断言已发布v1物理产物(产物)#断言v1
        return 产物#返回

    def encodeArtifact(自身,产物,选项):#编码产物
        """编码逻辑产物为物理头与行。"""
        if 自身.version==0:#v0
            断言已发布v0源产物(产物)#断言v0
        else:#v1
            断言已发布v1物理产物(产物)#断言v1
        return 编码产物(产物,选项,自身.version)#编码

    def 编码产物(自身,产物,选项):#编码产物（中文名）
        """编码逻辑产物为物理头与行。"""
        return 自身.encodeArtifact(产物,选项)#委托

已发布v0会话格式编解码器=创建已发布编解码器(0)#v0编解码器
已发布v1会话格式编解码器=创建已发布编解码器(1)#v1编解码器

def 解码物理头(值,版本):#解码物理头
    """解码物理头为逻辑头与继承事件数。"""
    源=快照会话格式json(值,f'released v{版本} physical header')#快照源
    记录=已发布v0记录(源,f'released v{版本} physical header')#转记录
    断言已发布v0键(#断言键
        记录,#记录
        物理头必填,#必填
        物理头可选,#可选
        f'released v{版本} physical header',#标签
    )#断言结束
    if 记录['type']!='session' or 记录['version']!=版本:#类型或版本不符
        raise 会话格式错误(f'expected released v{版本} physical Session header')#错误
    if not isinstance(记录['id'],str):#id非法
        raise 会话格式错误(f'released v{版本} header id must be a string')#id非法
    创建时间=会话格式计数(记录['createdAt'],f'released v{版本} header createdAt')#创建时间
    委托深度=会话格式计数(记录['delegationDepth'],f'released v{版本} header delegationDepth')#委托深度
    种子长度=0 if 'seedLength' not in 记录 else 会话格式计数(记录['seedLength'],f'released v{版本} header seedLength')#种子长度
    for 键 in ('cwd','parentSession','agentPreset'):#可选字符串
        if 键 in 记录 and not isinstance(记录[键],str):#类型不符
            raise 会话格式错误(f'released v{版本} header {键} must be a string')#错误
    if 'origin' in 记录 and 记录['origin']!='subagent':#origin非法
        raise 会话格式错误(f'released v{版本} header origin must be "subagent"')#错误
    逻辑头基={'version':版本,'id':记录['id'],'createdAt':创建时间,'isSeeded':'seedLength' in 记录,'delegationDepth':委托深度}#逻辑头基
    if 'cwd' in 记录:#有cwd
        逻辑头基['cwd']=记录['cwd']#cwd
    if 'parentSession' in 记录:#有父会话
        逻辑头基['parentSession']=记录['parentSession']#父会话
    if 'origin' in 记录:#有来源
        逻辑头基['origin']=记录['origin']#来源
    if 'agentPreset' in 记录:#有预设
        逻辑头基['agentPreset']=记录['agentPreset']#预设
    头=快照会话格式json(逻辑头基,f'released v{版本} logical header')#断言头
    断言已发布会话格式头(头,版本)#断言头
    return {'header':头,'inheritedEventCount':种子长度}#返回

def 编码产物(产物,选项,版本):#编码产物
    """编码逻辑产物为物理头与行。"""
    头=产物['header']#逻辑头
    物理头基={'type':'session','version':版本,'id':头['id'],'createdAt':头['createdAt'],'delegationDepth':头['delegationDepth']}#物理头基
    if 'cwd' in 头:#有cwd
        物理头基['cwd']=头['cwd']#cwd
    if 'parentSession' in 头:#有父会话
        物理头基['parentSession']=头['parentSession']#父会话
    if 头.get('isSeeded'):#种子
        物理头基['seedLength']=产物['inheritedEventCount']#种子长度
    if 'origin' in 头:#有来源
        物理头基['origin']=头['origin']#来源
    if 'agentPreset' in 头:#有预设
        物理头基['agentPreset']=头['agentPreset']#预设
    物理头=快照会话格式json(物理头基,f'released v{版本} encoded header')#断言对象
    打包=选项.get('packChunks') if isinstance(选项,dict) else getattr(选项,'packChunks',False)#是否打包
    记录们=打包块游程(产物['events']) if 打包 else list(产物['events'])#记录
    行们=tuple(编码出处(记录) for 记录 in 记录们)#编码行
    return {'header':物理头,'rows':行们}#返回

def 扫描行(行值们,可恢复):#扫描行
    """扫描物理行；可恢复时跳过畸形前缀直至 turn/end。"""
    事件们=[]#事件
    问题=None#问题
    for 行下标,值 in enumerate(行值们):#遍历行
        try:#尝试解码
            行=快照会话格式json(值,f'released Session row {行下标}')#快照行
            解码=解码行(行,行下标)#解码行
        except BaseException as 错误:#捕获错误
            当前=错误 if isinstance(错误,会话格式错误) else 会话格式错误(f'released Session row {行下标} is malformed',错误)#包装
            if not 可恢复:#不可恢复则抛
                raise 当前#抛出
            if 问题 is None:#记录首错
                问题=当前#记下
            continue#继续
        if 问题 is not None:#已有问题
            if any(事件['type']=='turn/end' for 事件 in 解码):#遇回合结束抛出
                raise 问题#抛出
            continue#丢弃后续
        行起始=len(事件们)#行起始
        for 事件 in 解码:#遍历解码事件
            if 事件['seq']!=len(事件们):#序号缺口
                缺口=会话格式错误(#缺口错误
                    f'released Session row {行下标} has seq gap (expected {len(事件们)}, got {事件["seq"]})',#消息
                )#构造结束
                del 事件们[行起始:]#回滚本行
                if not 可恢复:#不可恢复则抛
                    raise 缺口#抛出
                问题=缺口#记录问题
                break#跳出
            事件们.append(事件)#推入
        if 问题 is not None:#本行后有问题
            if any(事件['type']=='turn/end' for 事件 in 解码):#遇回合结束抛出
                raise 问题#抛出
            continue#继续
    return {'events':tuple(事件们)}#冻结返回

def 解码行(值,行下标):#解码行
    """解码一行；打包行展开为多事件。"""
    记录=已发布v0记录(值,f'released Session row {行下标}')#转记录
    类型=记录['type']#类型
    if isinstance(类型,str) and 类型 in 打包标签:#打包行
        return 展开打包行(记录,类型,行下标)#展开
    if 'sourceEventSeqs' in 记录:#有出处
        序号=会话格式计数(记录['seq'],f'released Session row {行下标} seq')#序号
        带出处=dict(记录)#展开
        带出处['sourceEventSeqs']=解码序号范围(记录['sourceEventSeqs'],序号)#解码出处范围
        return (带出处,)#单事件
    return (记录,)#单事件

def 展开打包行(行,类型,行下标):#展开打包行
    """把 text/reasoning/tool-call chunks 行展开为 assistant/chunk 事件。"""
    标签=f'released {类型} row {行下标}'#标签
    断言已发布v0键(行,['type','seq0','time0','data'],[],标签)#断言键
    起始序号=会话格式计数(行['seq0'],f'{标签} seq0')#起始序号
    时间=会话格式安全整数(行['time0'],f'{标签} time0')#起始时间
    数据=已发布v0记录(行['data'],f'{标签} data')#数据
    是工具=类型=='tool-call-chunks'#是否工具块
    断言已发布v0键(#断言数据键
        数据,#数据
        ['turn','step','index','id','dt','args'] if 是工具 else ['turn','step','index','dt','texts'],#必填
        ['name'] if 是工具 else [],#可选
        f'{标签} data',#标签
    )#断言结束
    载荷=数据['args' if 是工具 else 'texts']#载荷
    if (not isinstance(载荷,list) or len(载荷)==0
            or any(not isinstance(成员,str) for 成员 in 载荷)):#载荷非法
        raise 会话格式错误(f'{标签} payload must be a non-empty string array')#错误
    时差=数据['dt']#时间差
    if not isinstance(时差,list) or len(时差)!=len(载荷)-1:#长度不符
        raise 会话格式错误(f'{标签} dt length must match its payload')#错误
    for 差 in 时差:#校验成员
        会话格式安全整数(差,f'{标签} dt member')#校验成员
    if (not isinstance(数据['turn'],(int,float)) or isinstance(数据['turn'],bool)
            or not isinstance(数据['step'],(int,float)) or isinstance(数据['step'],bool)
            or not isinstance(数据['index'],(int,float)) or isinstance(数据['index'],bool)):#坐标非法
        raise 会话格式错误(f'{标签} turn, step, and index must be numbers')#错误
    if 是工具 and (not isinstance(数据['id'],str)
            or ('name' in 数据 and not isinstance(数据['name'],str))):#工具字段非法
        raise 会话格式错误(f'{标签} id and optional name must be strings')#错误
    输出=[]#输出
    for 下标 in range(len(载荷)):#遍历成员
        if 下标>0:#累加时间
            时间=会话格式安全整数(时间+时差[下标-1],f'{标签} member time')#累加时间
        成员=载荷[下标]#成员文本
        if 类型=='text-chunks':#文本块
            块={'type':'text-delta','index':数据['index'],'text':成员}#文本增量
        elif 类型=='reasoning-chunks':#推理块
            块={'type':'reasoning-delta','index':数据['index'],'text':成员}#推理增量
        else:#工具块
            块={'type':'tool-call-delta','index':数据['index'],'id':数据['id'],'argumentsDelta':成员}#工具增量
            if 'name' in 数据:#有名称
                块['name']=数据['name']#名称
        输出.append(快照会话格式json({#推入事件
            'type':'assistant/chunk',#类型
            'seq':会话格式计数(起始序号+下标,f'{标签} member seq'),#序号
            'time':时间,#时间
            'data':{'turn':数据['turn'],'step':数据['step'],'chunk':块},#数据
        },f'{标签} member'))#断言事件
    return tuple(输出)#冻结返回

def 解码序号范围(值,最大条目):#解码序号范围
    """把单点与 [start,end] 范围展开为序号列表。"""
    if not isinstance(值,list):#须为数组
        raise 会话格式错误('sourceEventSeqs must be an array')#须为数组
    输出=[]#输出
    有范围=False#是否含范围
    for 项 in 值:#遍历项
        if isinstance(项,(int,float)) and not isinstance(项,bool):#单个序号
            if len(输出)>=最大条目:#超限
                raise 会话格式错误('sourceEventSeqs exceeds its event seq')#超限
            输出.append(会话格式计数(项,'sourceEventSeqs member'))#推入
            continue#继续
        if not isinstance(项,list) or len(项)!=2:#非二元组
            raise 会话格式错误('sourceEventSeqs range must be a [start, end] pair')#错误
        起点=会话格式计数(项[0],'sourceEventSeqs range start')#起点
        终点=会话格式计数(项[1],'sourceEventSeqs range end')#终点
        if 终点<起点 or 终点-起点+1>最大条目-len(输出):#范围非法
            raise 会话格式错误('sourceEventSeqs range exceeds its event seq')#错误
        for 序号 in range(起点,终点+1):#展开
            输出.append(序号)#推入
        有范围=True#标记
    if 有范围:#需校验递增
        for 下标 in range(1,len(输出)):#非严格递增
            if 输出[下标]<=输出[下标-1]:#非严格递增
                raise 会话格式错误('sourceEventSeqs ranges must be strictly increasing')#错误
    return tuple(输出)#冻结返回

def 编码出处(记录):#编码出处
    """把 sourceEventSeqs 压缩为范围表示。"""
    if 'sourceEventSeqs' not in 记录:#无出处则原样
        return 记录#原样
    出处列表=记录['sourceEventSeqs']#出处列表
    数值们=[会话格式计数(值,'sourceEventSeqs member') for 值 in 出处列表]#转数字
    带压缩=dict(记录)#展开
    带压缩['sourceEventSeqs']=编码序号范围(数值们)#编码范围
    return 快照会话格式json(带压缩)#快照

def 编码序号范围(值们):#编码序号范围
    """把严格递增序号压缩为单点与长度≥3 的范围。"""
    for 下标 in range(1,len(值们)):#非递增原样
        if 值们[下标]<=值们[下标-1]:#非递增
            return tuple(值们)#原样
    输出=[]#输出
    起点下标=0#起点
    while 起点下标<len(值们):#扫描连续段
        终点下标=起点下标#终点
        while (终点下标+1<len(值们)
                and 值们[终点下标+1]==值们[终点下标]+1):#延伸
            终点下标+=1#延伸
        if 终点下标-起点下标>=2:#压成范围
            输出.append((值们[起点下标],值们[终点下标]))#范围
        else:#散点
            for 下标 in range(起点下标,终点下标+1):#散点
                输出.append(值们[下标])#推入
        起点下标=终点下标+1#下一段
    return tuple(输出)#冻结返回

def 打包块游程(事件们):#打包块游程
    """把连续可打包的 assistant/chunk 压成 chunks 行。"""
    输出=[]#输出
    种类=None#当前种类
    游程=[]#当前游程
    def 刷新():#刷新游程
        """够长则打包，否则展开。"""
        nonlocal 种类,游程#可变
        if 种类 is not None and len(游程)>=3:#够长则打包
            输出.append(构建打包行(种类,游程))#打包
        else:#否则展开
            输出.extend(游程)#展开
        种类=None#清空种类
        游程=[]#清空游程
    for 事件 in 事件们:#遍历事件
        候选=分类块(事件)#分类
        上一=游程[-1] if 游程 else None#上一事件
        if (候选 is not None and 候选==种类 and 上一 is not None
                and 续接块(上一,事件,候选)):#可续接
            游程.append(事件)#续接
            continue#继续
        刷新()#先刷新
        if 候选 is None:#非块则直出
            输出.append(事件)#直出
        else:#新游程
            种类=候选#种类
            游程=[事件]#起始
    刷新()#末尾刷新
    return tuple(输出)#冻结返回

def 分类块(事件):#分类块
    """识别可打包的 text/reasoning/tool-call 增量块。"""
    if 事件.get('type')!='assistant/chunk' or not 精确键集合(事件,['type','seq','time','data']):#非标准块
        return None#非标准块
    数据=事件['data']#数据
    if not 是否会话格式json对象(数据) or not 精确键集合(数据,['turn','step','chunk']):#数据不符
        return None#数据不符
    块=数据['chunk']#块
    if (not 是否会话格式json对象(块)
            or not isinstance(块.get('index'),(int,float)) or isinstance(块.get('index'),bool)
            or not isinstance(块.get('type'),str)):#块信封非法
        return None#块信封非法
    if 块['type'] in ('text-delta','reasoning-delta'):#文本或推理
        if 精确键集合(块,['type','index','text']) and isinstance(块.get('text'),str):#键全
            return 块['type']#种类
        return None#键不全则无
    if 块['type']!='tool-call-delta':#非工具增量
        return None#非工具增量
    精确=(精确键集合(块,['type','index','id','argumentsDelta'])
            or 精确键集合(块,['type','index','id','name','argumentsDelta']))#精确键
    if (精确 and isinstance(块.get('id'),str)
            and isinstance(块.get('argumentsDelta'),str)
            and ('name' not in 块 or isinstance(块.get('name'),str))):#判定
        return 'tool-call-delta'#工具增量
    return None#判定失败

def 续接块(前,后,种类):#是否续接块
    """判断后一事件是否可续接前一事件的块游程。"""
    前数据=前['data']#前数据
    后数据=后['data']#后数据
    前块=前数据['chunk']#前块
    后块=后数据['chunk']#后块
    if not 是否安全整数(后['time']-前['time']):#时间差非法
        return False#时间差非法
    if 后数据['turn']!=前数据['turn'] or 后数据['step']!=前数据['step']:#坐标变了
        return False#坐标变了
    if 后块['index']!=前块['index']:#索引变了
        return False#索引变了
    if 种类!='tool-call-delta':#非工具即可
        return True#非工具即可
    return (后块['id']==前块['id']
            and ('name' in 后块)==('name' in 前块)
            and 后块.get('name')==前块.get('name'))#工具身份一致

def 构建打包行(种类,游程):#构建打包行
    """把长度≥3 的块游程建成物理打包行。"""
    首=游程[0]#首事件
    首数据=首['data']#首数据
    首块=首数据['chunk']#首块
    公共={#公共字段
        'turn':首数据['turn'],#回合
        'step':首数据['step'],#步骤
        'index':首块['index'],#索引
        'dt':[游程[下标+1]['time']-游程[下标]['time'] for 下标 in range(len(游程)-1)],#时间差
    }#公共结束
    if 种类=='tool-call-delta':#工具打包
        数据={**公共,'id':首块['id'],'args':[事件['data']['chunk']['argumentsDelta'] for 事件 in 游程]}#数据
        if 'name' in 首块:#有名称
            数据['name']=首块['name']#名称
        return 快照会话格式json({#快照
            'type':'tool-call-chunks',#类型
            'seq0':首['seq'],#起始序号
            'time0':首['time'],#起始时间
            'data':数据,#数据
        })#断言
    return 快照会话格式json({#文本或推理打包
        'type':'text-chunks' if 种类=='text-delta' else 'reasoning-chunks',#类型
        'seq0':首['seq'],#起始序号
        'time0':首['time'],#起始时间
        'data':{**公共,'texts':[事件['data']['chunk']['text'] for 事件 in 游程]},#数据
    })#断言

def 精确键集合(记录,键们):#精确键集合
    """记录自有键集合恰好等于给定键列表。"""
    return len(记录.keys())==len(键们) and all(键 in 记录 for 键 in 键们)#比较

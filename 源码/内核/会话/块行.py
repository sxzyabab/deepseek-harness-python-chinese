from ...模型后端.llm.标识构造 import 调用标识
from ...模型后端.llm.永不 import 断言永不
from .类型 import 安全整数上限

__all__=['打包块游程','解码存储记录']

最少游程=3#最少打包成员

class 块行错误(Exception):
    """内核会话块行包的异常基类。"""

def 外来安全整数(值):
    """外来 JSON 序号与时间是否落在安全整数范围。"""
    if isinstance(值,bool):
        return False#布尔不是整数
    if isinstance(值,int):
        return abs(值)<=安全整数上限
    if isinstance(值,float) and 值.is_integer():
        return abs(值)<=安全整数上限
    return False

def 是否记录(值):
    """值是否为非空对象记录。"""
    return isinstance(值,dict)

def 恰好这些键(值,键列表):
    """精确键检查：value 有 keys 里的每个键且没有别的。"""
    自有=list(值.keys())
    if len(自有)!=len(键列表):
        return False
    for 键 in 键列表:
        if 键 not in 值:
            return False
    return True

def 分类(事件):
    """为打包分类一条事件：整份形态都在白名单时为其 delta 种类。"""
    if 事件['type']!='assistant/chunk':
        return None
    if not 恰好这些键(事件,('type','seq','time','data')):
        return None
    序号=事件['seq']
    时间=事件['time']
    if not 外来安全整数(序号) or 序号<0 or not 外来安全整数(时间):
        return None
    数据=事件['data']
    if (not 是否记录(数据)) or (not 恰好这些键(数据,('turn','step','chunk'))):
        return None
    轮次=数据['turn']
    步骤=数据['step']
    if not isinstance(轮次,(int,float)) or isinstance(轮次,bool):
        return None
    if not isinstance(步骤,(int,float)) or isinstance(步骤,bool):
        return None
    块=数据['chunk']
    if not 是否记录(块):
        return None
    块下标=块['index'] if 'index' in 块 else None
    if not isinstance(块下标,(int,float)) or isinstance(块下标,bool):
        return None
    块类型=块['type']
    if 块类型=='text-delta' or 块类型=='reasoning-delta':
        文本=块['text'] if 'text' in 块 else None
        if 恰好这些键(块,('type','index','text')) and isinstance(文本,str):
            return 块类型
        return None
    if 块类型=='tool-call-delta':
        带名=恰好这些键(块,('type','index','id','name','argumentsDelta')) and isinstance(块['name'] if 'name' in 块 else None,str)
        无名=恰好这些键(块,('type','index','id','argumentsDelta'))
        形态对=无名 or 带名
        if 形态对 and isinstance(块['id'] if 'id' in 块 else None,str) and isinstance(块['argumentsDelta'] if 'argumentsDelta' in 块 else None,str):
            return 块类型
        return None
    return None

def 工具调用于(事件):
    """白名单 delta 块的工具调用字段。"""
    return 事件['data']['chunk']

def 下标于(事件):
    """白名单 delta 块的块下标。"""
    return 工具调用于(事件)['index']

def 是否延续(前,后,种类):
    """后一条是否延长以前一条结尾的游程。"""
    if 后['seq']!=前['seq']+1:
        return False
    if not 外来安全整数(后['time']-前['time']):
        return False
    前数据=前['data']
    后数据=后['data']
    if 后数据['turn']!=前数据['turn'] or 后数据['step']!=前数据['step']:
        return False
    if 下标于(后)!=下标于(前):
        return False
    if 种类!='tool-call-delta':
        return True
    甲=工具调用于(前)
    乙=工具调用于(后)
    甲名=甲['name'] if 'name' in 甲 else None
    乙名=乙['name'] if 'name' in 乙 else None
    return 甲['id']==乙['id'] and ('name' in 甲)==('name' in 乙) and 甲名==乙名

def 建行(种类,游程):
    """为已完成游程建行。"""
    首=游程[0]
    首数据=首['data']
    间隔=[]
    下标=0
    while 下标<len(游程)-1:
        当前=游程[下标+1]
        前条=游程[下标]
        间隔.append(当前['time']-前条['time'])
        下标+=1
    基={
        'turn':首数据['turn'],
        'step':首数据['step'],
        'index':下标于(首),
        'dt':间隔,
    }
    信封={'seq0':首['seq'],'time0':首['time']}
    if 种类=='tool-call-delta':
        调用=工具调用于(首)
        载荷=dict(基)
        载荷['id']=调用标识(调用['id'])
        if 'name' in 调用:
            载荷['name']=调用['name']
        参数列表=[]
        for 事件 in 游程:
            参数列表.append(工具调用于(事件)['argumentsDelta'])
        载荷['args']=参数列表
        行=dict(信封)
        行['type']='tool-call-chunks'
        行['data']=载荷
        return 行
    文本列表=[]
    for 事件 in 游程:
        文本列表.append(工具调用于(事件)['text'])
    载荷=dict(基)
    载荷['texts']=文本列表
    行=dict(信封)
    行['data']=载荷
    if 种类=='text-delta':
        行['type']='text-chunks'
    else:
        行['type']='reasoning-chunks'
    return 行

def 打包块游程(事件列表):
    """为一批事件打包存储。"""
    输出=[]
    种类=None
    游程=[]
    def 冲掉():
        """冲掉当前游程。"""
        nonlocal 种类,游程
        if 种类 is not None and len(游程)>=最少游程:
            输出.append(建行(种类,游程))
        else:
            for 项 in 游程:
                输出.append(项)
        种类=None
        游程=[]
    for 事件 in 事件列表:
        本类=分类(事件)
        if 本类 is None:
            冲掉()
            输出.append(事件)
            continue
        末=游程[-1] if len(游程)>0 else None
        if 本类==种类 and 末 is not None and 是否延续(末,事件,本类):
            游程.append(事件)
            continue
        冲掉()
        种类=本类
        游程=[事件]
    冲掉()
    return 输出

def 畸形(标签,原因):
    """抛出统一的畸形行诊断。"""
    raise 块行错误('畸形 '+标签+' 存储行: '+原因)

def 校验游程数据(标签,数据,载荷键):
    """校验共享游程数据字段与载荷/dt 元数；返回成员载荷。"""
    轮次=数据['turn'] if 'turn' in 数据 else None
    步骤=数据['step'] if 'step' in 数据 else None
    块下标=数据['index'] if 'index' in 数据 else None
    if (not isinstance(轮次,(int,float)) or isinstance(轮次,bool)
        or not isinstance(步骤,(int,float)) or isinstance(步骤,bool)
        or not isinstance(块下标,(int,float)) or isinstance(块下标,bool)):
        畸形(标签,'turn/step/index 必须是数字')
    载荷=数据[载荷键] if 载荷键 in 数据 else None
    if (not isinstance(载荷,list)) or len(载荷)==0:
        畸形(标签,载荷键+' 必须是非空字符串数组')
    for 项 in 载荷:
        if not isinstance(项,str):
            畸形(标签,载荷键+' 必须是非空字符串数组')
    间隔=数据['dt'] if 'dt' in 数据 else None
    if not isinstance(间隔,list):
        畸形(标签,'dt 必须是安全整数数组')
    for 缝 in 间隔:
        if not 外来安全整数(缝):
            畸形(标签,'dt 必须是安全整数数组')
    if len(间隔)!=len(载荷)-1:
        畸形(标签,'dt 长度 '+str(len(间隔))+' 与 '+str(len(载荷))+' 个成员不匹配')
    return 载荷

def 校验行(值,标签):
    """校验一行标签解析值的信封与数据，任何畸形都抛。"""
    if not 恰好这些键(值,('type','seq0','time0','data')):
        畸形(标签,'信封必须恰好是 {type, seq0, time0, data}')
    序号零=值['seq0'] if 'seq0' in 值 else None
    if not 外来安全整数(序号零) or 序号零<0:
        畸形(标签,'seq0 必须是非负安全整数')
    时间零=值['time0'] if 'time0' in 值 else None
    if not 外来安全整数(时间零):
        畸形(标签,'time0 必须是安全整数')
    数据=值['data'] if 'data' in 值 else None
    if not 是否记录(数据):
        畸形(标签,'data 必须是对象')
    if 标签=='tool-call-chunks':
        带名=恰好这些键(数据,('turn','step','index','id','name','dt','args'))
        if (not 带名) and (not 恰好这些键(数据,('turn','step','index','id','dt','args'))):
            畸形(标签,'data 必须恰好是 {turn, step, index, id, name?, dt, args}')
        if not isinstance(数据['id'] if 'id' in 数据 else None,str) or (带名 and not isinstance(数据['name'] if 'name' in 数据 else None,str)):
            畸形(标签,'id（以及出现时的 name）必须是字符串')
        载荷=校验游程数据(标签,数据,'args')
    else:
        if not 恰好这些键(数据,('turn','step','index','dt','texts')):
            畸形(标签,'data 必须恰好是 {turn, step, index, dt, texts}')
        载荷=校验游程数据(标签,数据,'texts')
    if not 外来安全整数(序号零+len(载荷)-1):
        畸形(标签,'成员 seq 必须保持为安全整数')
    时间=时间零
    for 缝 in 数据['dt']:
        时间=时间+缝
        if not 外来安全整数(时间):
            畸形(标签,'成员时间必须保持为安全整数')
    return 值

def 展开行(行):
    """把已校验行展开回精确原始事件，按顺序。"""
    行类型=行['type']
    数据=行['data']
    if 行类型=='tool-call-chunks':
        成员列表=数据['args']
    else:
        成员列表=数据['texts']
    事件列表=[]
    时间=行['time0']
    下标=0
    while 下标<len(成员列表):
        if 下标>0:
            时间=时间+数据['dt'][下标-1]
        if 行类型=='text-chunks':
            块={'type':'text-delta','index':数据['index'],'text':成员列表[下标]}
        elif 行类型=='reasoning-chunks':
            块={'type':'reasoning-delta','index':数据['index'],'text':成员列表[下标]}
        elif 行类型=='tool-call-chunks':
            块={
                'type':'tool-call-delta',
                'index':数据['index'],
                'id':数据['id'],
                'argumentsDelta':成员列表[下标],
            }
            if 'name' in 数据:
                块['name']=数据['name']
        else:
            return 断言永不(行,'块行 展开行')
        事件列表.append({
            'type':'assistant/chunk',
            'seq':行['seq0']+下标,
            'time':时间,
            'data':{'turn':数据['turn'],'step':数据['step'],'chunk':块},
        })
        下标+=1
    return 事件列表

def 解码存储记录(值):
    """把一条解析后的 JSONL 行值解码成它存储的会话事件。"""
    if not 是否记录(值):
        return [值]
    标签=值['type'] if 'type' in 值 else None
    if 标签!='text-chunks' and 标签!='reasoning-chunks' and 标签!='tool-call-chunks':
        return [值]
    return 展开行(校验行(值,标签))

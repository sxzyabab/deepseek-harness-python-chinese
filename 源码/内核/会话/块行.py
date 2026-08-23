"""assistant/chunk delta 游程的无损存储打包。对齐上游 `session/src/chunk-rows.ts`。公开面仅中文名。"""
from ..llm.品牌 import 调用标识#导入调用 id
from ..llm.永不 import 断言永不#导入穷尽检查
from .类型 import 是否安全整数#导入安全整数判定

__all__=['打包块游程','解码存储记录']#仅中文公开名

最少游程=3#最少打包成员

def 是否记录(值):#是否记录
    """值是否为非空对象记录。"""
    return isinstance(值,dict)#对象且非 null

def 恰好这些键(值,键列表):#精确键检查
    """精确键检查：value 有 keys 里的每个键且没有别的。"""
    自有=list(值.keys())#自有键
    if len(自有)!=len(键列表):#键数不匹配
        return False#键数不匹配
    for 键 in 键列表:#逐个键
        if 键 not in 值:#缺键
            return False#缺键
    return True#键数与集合都匹配

def 取字段(对象,键):#读取字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    if 对象 is None:#无对象
        return None#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键)#映射键
    return getattr(对象,键,None)#对象属性

def 有自有(对象,键):#是否拥有自有键
    """对象是否拥有该自有键。"""
    if isinstance(对象,dict):#字典
        return 键 in 对象#字典键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有字典
    return 键 in 字典#自有

def 分类(事件):#分类事件
    """为打包分类一条事件：整份形态都在白名单时为其 delta 种类。"""
    if 取字段(事件,'type')!='assistant/chunk':#非助手块
        return None#非助手块
    if not 恰好这些键(事件,('type','seq','time','data')):#信封键不对
        return None#信封键不对
    序号=取字段(事件,'seq')#序号
    时间=取字段(事件,'time')#时间
    if not 是否安全整数(序号) or 序号<0 or not 是否安全整数(时间):#序号或时间非法
        return None#序号或时间非法
    数据=取字段(事件,'data')#取出载荷
    if (not 是否记录(数据)) or (not 恰好这些键(数据,('turn','step','chunk'))):#载荷键不对
        return None#载荷键不对
    轮次=取字段(数据,'turn')#轮次
    步骤=取字段(数据,'step')#步骤
    if not isinstance(轮次,(int,float)) or isinstance(轮次,bool):#轮次非数字
        return None#轮次非数字
    if not isinstance(步骤,(int,float)) or isinstance(步骤,bool):#步骤非数字
        return None#步骤非数字
    块=取字段(数据,'chunk')#取出块
    if not 是否记录(块):#块不是记录
        return None#块不是记录
    块下标=试取(块,'index')#块下标
    if not isinstance(块下标,(int,float)) or isinstance(块下标,bool):#块不是带数字下标的记录
        return None#块不是带数字下标的记录
    块类型=取字段(块,'type')#块类型
    if 块类型=='text-delta' or 块类型=='reasoning-delta':#文本或推理 delta
        文本=试取(块,'text')#文本
        if 恰好这些键(块,('type','index','text')) and isinstance(文本,str):#键与文本类型都对
            return 块类型#键与文本类型都对才打包
        return None#形态不对
    if 块类型=='tool-call-delta':#工具调用 delta
        带名=恰好这些键(块,('type','index','id','name','argumentsDelta')) and isinstance(试取(块,'name'),str)#有名形态
        无名=恰好这些键(块,('type','index','id','argumentsDelta'))#无名形态
        形态对=无名 or 带名#有名或无名两种形态
        if 形态对 and isinstance(试取(块,'id'),str) and isinstance(试取(块,'argumentsDelta'),str):#形态与字符串字段都对
            return 块类型#形态与字符串字段都对才打包
        return None#形态不对
    return None#其余块不打包

def 工具调用于(事件):#取调用身份
    """白名单 delta 块的工具调用字段。"""
    数据=取字段(事件,'data')#载荷
    return 取字段(数据,'chunk')#块即调用字段

def 下标于(事件):#取块下标
    """白名单 delta 块的块下标。"""
    块=工具调用于(事件)#块
    return 取字段(块,'index')#读 index

def 是否延续(前,后,种类):#是否延续游程
    """后一条是否延长以前一条结尾的游程。"""
    if 取字段(后,'seq')!=取字段(前,'seq')+1:#序号必须连续
        return False#序号必须连续
    if not 是否安全整数(取字段(后,'time')-取字段(前,'time')):#间隔必须是安全整数
        return False#间隔必须是安全整数
    前数据=取字段(前,'data')#前载荷
    后数据=取字段(后,'data')#后载荷
    if 取字段(后数据,'turn')!=取字段(前数据,'turn') or 取字段(后数据,'step')!=取字段(前数据,'step'):#轮次步骤必须相同
        return False#轮次步骤必须相同
    if 下标于(后)!=下标于(前):#块下标必须相同
        return False#块下标必须相同
    if 种类!='tool-call-delta':#非工具调用
        return True#非工具调用则到此
    甲=工具调用于(前)#前一条调用
    乙=工具调用于(后)#后一条调用
    return 取字段(甲,'id')==取字段(乙,'id') and 有自有(甲,'name')==有自有(乙,'name') and 试取(甲,'name')==试取(乙,'name')#id 与 name 都同

def 建行(种类,游程):#建打包行
    """为已完成游程建行。"""
    首=游程[0]#首成员
    首数据=取字段(首,'data')#首载荷
    间隔=[]#时间间隔
    下标=0#成员下标
    while 下标<len(游程)-1:#逐对间隔
        当前=游程[下标+1]#后成员
        前条=游程[下标]#前成员
        间隔.append(取字段(当前,'time')-取字段(前条,'time'))#间隔
        下标+=1#下一对
    基={#共享基字段
        'turn':取字段(首数据,'turn'),#轮次
        'step':取字段(首数据,'step'),#步骤
        'index':下标于(首),#块下标
        'dt':间隔,#间隔
    }#共享基字段
    信封={'seq0':取字段(首,'seq'),'time0':取字段(首,'time')}#信封锚点
    if 种类=='tool-call-delta':#工具调用游程
        调用=工具调用于(首)#调用身份
        载荷=dict(基)#基字段
        载荷['id']=调用标识(取字段(调用,'id'))#品牌调用 id
        if 有自有(调用,'name'):#有名
            载荷['name']=取字段(调用,'name')#有名则带
        参数们=[]#各参数片段
        for 事件 in 游程:#各成员
            参数们.append(取字段(工具调用于(事件),'argumentsDelta'))#参数片段
        载荷['args']=参数们#各参数片段
        行=dict(信封)#锚点
        行['type']='tool-call-chunks'#行类型
        行['data']=载荷#载荷
        return 行#工具调用行
    文本们=[]#各成员文本
    for 事件 in 游程:#各成员
        文本们.append(取字段(工具调用于(事件),'text'))#文本
    载荷=dict(基)#基字段
    载荷['texts']=文本们#文本载荷
    行=dict(信封)#锚点
    行['data']=载荷#载荷
    if 种类=='text-delta':#文本
        行['type']='text-chunks'#文本块行
    else:#推理
        行['type']='reasoning-chunks'#推理块行
    return 行#按种类选行类型

def 打包块游程(事件们):#打包游程
    """为一批事件打包存储。"""
    输出=[]#输出记录
    种类=None#当前游程种类
    游程=[]#当前游程
    def 冲掉():#冲掉当前游程
        """冲掉当前游程。"""
        nonlocal 种类,游程#修改外层
        if 种类 is not None and len(游程)>=最少游程:#够长则打包
            输出.append(建行(种类,游程))#够长则打包
        else:#否则原样放出
            for 项 in 游程:#原样放出
                输出.append(项)#否则原样放出
        种类=None#清空种类
        游程=[]#清空游程
    for 事件 in 事件们:#扫描事件
        本类=分类(事件)#分类
        if 本类 is None:#不可打包
            冲掉()#先冲掉
            输出.append(事件)#原样放出
            continue#下一事件
        末=游程[-1] if len(游程)>0 else None#当前游程末
        if 本类==种类 and 末 is not None and 是否延续(末,事件,本类):#延续当前游程
            游程.append(事件)#接入
            continue#下一事件
        冲掉()#先冲掉旧游程
        种类=本类#开新种类
        游程=[事件]#新游程
    冲掉()#冲掉尾巴
    return 输出#返回记录

def 畸形(标签,原因):#畸形行
    """抛出统一的畸形行诊断。"""
    raise Exception('malformed '+标签+' storage row: '+原因)#带标签抛错

def 校验游程数据(标签,数据,载荷键):#校验游程数据
    """校验共享游程数据字段与载荷/dt 元数；返回成员载荷。"""
    轮次=试取(数据,'turn')#轮次
    步骤=试取(数据,'step')#步骤
    块下标=试取(数据,'index')#块下标
    if (not isinstance(轮次,(int,float)) or isinstance(轮次,bool)
        or not isinstance(步骤,(int,float)) or isinstance(步骤,bool)
        or not isinstance(块下标,(int,float)) or isinstance(块下标,bool)):#基字段非数字
        畸形(标签,'turn/step/index must be numbers')#必须是数字
    载荷=试取(数据,载荷键)#取出载荷
    if (not isinstance(载荷,list)) or len(载荷)==0:#非非空数组
        畸形(标签,载荷键+' must be a non-empty string array')#必须是非空字符串数组
    for 项 in 载荷:#逐项
        if not isinstance(项,str):#非字符串
            畸形(标签,载荷键+' must be a non-empty string array')#必须是非空字符串数组
    间隔=试取(数据,'dt')#取出间隔
    if not isinstance(间隔,list):#非数组
        畸形(标签,'dt must be an array of safe integers')#必须是安全整数数组
    for 缝 in 间隔:#逐个间隔
        if not 是否安全整数(缝):#非安全整数
            畸形(标签,'dt must be an array of safe integers')#必须是安全整数数组
    if len(间隔)!=len(载荷)-1:#元数不匹配
        畸形(标签,'dt length '+str(len(间隔))+' does not match '+str(len(载荷))+' members')#间隔长度必须少一
    return 载荷#返回载荷

def 校验行(值,标签):#校验行
    """校验一行标签解析值的信封与数据，任何畸形都抛。"""
    if not 恰好这些键(值,('type','seq0','time0','data')):#信封键不对
        畸形(标签,'envelope must be exactly {type, seq0, time0, data}')#必须恰好这些键
    序号零=试取(值,'seq0')#序号锚点
    if not 是否安全整数(序号零) or 序号零<0:#序号非法
        畸形(标签,'seq0 must be a non-negative safe integer')#必须非负安全整数
    时间零=试取(值,'time0')#时间锚点
    if not 是否安全整数(时间零):#时间非法
        畸形(标签,'time0 must be a safe integer')#必须是安全整数
    数据=试取(值,'data')#取出数据
    if not 是否记录(数据):#不是对象
        畸形(标签,'data must be an object')#必须是对象
    if 标签=='tool-call-chunks':#工具调用行
        带名=恰好这些键(数据,('turn','step','index','id','name','dt','args'))#带 name 形态
        if (not 带名) and (not 恰好这些键(数据,('turn','step','index','id','dt','args'))):#两种形态都不对
            畸形(标签,'data must be exactly {turn, step, index, id, name?, dt, args}')#必须恰好这些键
        if not isinstance(试取(数据,'id'),str) or (带名 and not isinstance(试取(数据,'name'),str)):#id/name 类型不对
            畸形(标签,'id (and name when present) must be strings')#必须是字符串
        载荷=校验游程数据(标签,数据,'args')#校验 args
    else:#文本或推理行
        if not 恰好这些键(数据,('turn','step','index','dt','texts')):#键不对
            畸形(标签,'data must be exactly {turn, step, index, dt, texts}')#必须恰好这些键
        载荷=校验游程数据(标签,数据,'texts')#校验 texts
    if not 是否安全整数(序号零+len(载荷)-1):#末成员序号越界
        畸形(标签,'member seqs must stay safe integers')#成员序号必须保持安全整数
    时间=时间零#运行时间
    for 缝 in 取字段(数据,'dt'):#累加间隔
        时间=时间+缝#加上间隔
        if not 是否安全整数(时间):#时间越界
            畸形(标签,'member times must stay safe integers')#时间必须保持安全整数
    return 值#当作已校验行

def 展开行(行):#展开行
    """把已校验行展开回精确原始事件，按顺序。"""
    行类型=取字段(行,'type')#行类型
    数据=取字段(行,'data')#载荷
    if 行类型=='tool-call-chunks':#工具调用行
        成员们=取字段(数据,'args')#成员数组
    else:#文本或推理行
        成员们=取字段(数据,'texts')#成员数组
    事件们=[]#重建事件
    时间=取字段(行,'time0')#运行时间
    下标=0#逐成员
    while 下标<len(成员们):#逐成员
        if 下标>0:#非首成员
            时间=时间+取字段(数据,'dt')[下标-1]#累加间隔
        if 行类型=='text-chunks':#文本
            块={'type':'text-delta','index':取字段(数据,'index'),'text':成员们[下标]}#文本 delta
        elif 行类型=='reasoning-chunks':#推理
            块={'type':'reasoning-delta','index':取字段(数据,'index'),'text':成员们[下标]}#推理 delta
        elif 行类型=='tool-call-chunks':#工具调用
            块={#工具调用 delta
                'type':'tool-call-delta',#类型
                'index':取字段(数据,'index'),#块下标
                'id':取字段(数据,'id'),#调用 id
                'argumentsDelta':成员们[下标],#参数片段
            }#工具调用 delta
            if 有自有(数据,'name'):#有名
                块['name']=取字段(数据,'name')#有名则带
        else:#封闭联合穷尽
            return 断言永不(行,'chunk-rows expandRow')#不可达
        事件们.append({#重建事件
            'type':'assistant/chunk',#助手块
            'seq':取字段(行,'seq0')+下标,#成员序号
            'time':时间,#成员时间
            'data':{'turn':取字段(数据,'turn'),'step':取字段(数据,'step'),'chunk':块},#载荷
        })#重建事件
        下标+=1#下一成员
    return 事件们#返回事件

def 解码存储记录(值):#解码存储记录
    """把一条解析后的 JSONL 行值解码成它存储的会话事件。"""
    if not 是否记录(值):#非记录
        return [值]#非记录当单事件
    标签=试取(值,'type')#取出类型标签
    if 标签!='text-chunks' and 标签!='reasoning-chunks' and 标签!='tool-call-chunks':#不是块行
        return [值]#当单事件
    return 展开行(校验行(值,标签))#校验并展开

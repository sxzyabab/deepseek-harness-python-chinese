"""受强制 JSON Schema 子集：断言、对象根约束与按值校验。对齐上游 `tools/src/json-schema.ts`。公开面仅中文名。"""
import json,math
from ...模型后端.llm import 装备错误 as 框架错误,断言永不#框架错误与穷尽检查
from ..会话 import 是否json值#无损JSON判定
from ..会话.json值 import 是否普通对象,是否普通数组#普通记录与数组

__all__=(
    'json模式错误','断言受支持json模式','断言对象json模式','校验json模式值',
    '是否json模式记录','是否普通json数组','自有','转json',
)#仅中文公开名

约束关键字={'type','oneOf','properties','required','additionalProperties','items','enum','const'}#约束关键字
注解关键字={'description','title','default','examples'}#注解关键字
模式类型=('object','array','string','number','integer','boolean','null')#合法类型表
联合旁禁字=('properties','required','additionalProperties','items','enum','const')#oneOf旁禁字

class json模式错误(框架错误):
    """原始模式落在受强制子集之外时抛出。"""
    def __init__(自身,违规列表):
        """用违规列表拼出不支持模式消息；公开属性仅 违规列表。"""
        super().__init__('unsupported JSON schema: '+'; '.join(违规列表),'UNSUPPORTED_SCHEMA')#拼消息
        自身.name='JsonSchemaError'#错误名槽（跨语言对照字面量）
        自身.违规列表=违规列表#违规诊断列表

def 是否普通json记录(值):
    """跨领域检测普通 JSON 记录，不接受数组或奇异对象。"""
    try:
        return 是否普通对象(值)#字典或其冻结形态
    except Exception:
        return False#探测抛错

def 仅可枚举字符串键(值):
    """记录是否只含自有可枚举字符串键。"""
    try:
        return all(isinstance(键,str) for 键 in 值)#每个都是字符串
    except Exception:
        return False#探测抛错

def 是否json模式记录(值):
    """检测键能在 JSON 投影中存活的普通模式记录。"""
    return 是否普通json记录(值) and 仅可枚举字符串键(值)#普通记录且键可见

def 是否普通json数组(值):
    """检测稠密普通数组，且无 JSON 看不见的装饰。"""
    try:
        if not 是否普通数组(值):
            return False#不是数组
        额外=getattr(值,'__dict__',None)#列表额外自有属性
        if 额外 is not None and len(额外)>0:
            return False#JSON 会丢掉的额外键
        return True#稠密普通数组
    except Exception:
        return False#探测抛错

def 是JSON数字(值):
    """无损有限 JSON 数字，排除负零。"""
    if isinstance(值,bool):
        return False#布尔不是数字
    if isinstance(值,int):
        return True#整数有限
    if isinstance(值,float):
        return math.isfinite(值) and not (值==0 and math.copysign(1,值)<0)#有限且非-0
    return False#其它类型

def 标量匹配(类型名,值):
    """标量是否匹配所声明的模式类型。"""
    if 类型名=='string':
        return isinstance(值,str)#字符串
    if 类型名=='number':
        return 是JSON数字(值)#有限JSON数字
    if 类型名=='integer':
        return 是JSON数字(值) and 值==int(值)#整数
    if 类型名=='boolean':
        return isinstance(值,bool)#布尔
    if 类型名=='null':
        return 值 is None#null
    return 断言永不(类型名,'JsonSchemaType')#穷尽

def 检查对象模式收尾(节点,路径,属性表,违规):
    """属性模式走完后再校验仅对象字段。"""
    有必填='required' in 节点#是否声明required
    必填=节点.get('required') if 有必填 else None#必填表
    if 有必填:
        if not 是否普通json数组(必填) or any(not isinstance(项,str) for 项 in 必填):
            违规.append(路径+'.required must be an array of strings')#形态违规
        else:
            已声明=属性表 if 是否json模式记录(属性表) else {}#已声明属性
            for 键 in 必填:
                if 键 not in 已声明:
                    违规.append(路径+'.required names "'+键+'" which is not in properties')#键不在properties
    if 'additionalProperties' in 节点 and not isinstance(节点.get('additionalProperties'),bool):
        违规.append(路径+'.additionalProperties must be a boolean')#必须布尔

def 检查模式节点(根,根路径,违规,已见):
    """收集一棵原始模式树的全部违规，不使用调用栈。"""
    任务表=[{'种类':'进入','节点':根,'路径':根路径}]#从根进入
    任务=任务表.pop() if 任务表 else None#弹出
    while 任务 is not None:
        if 任务['种类']=='离开':
            已见.discard(id(任务['节点']))#解除循环标记
            任务=任务表.pop() if 任务表 else None#下一任务
            continue#下一任务
        if 任务['种类']=='联合收尾':
            for 键 in 联合旁禁字:
                if 键 in 任务['节点']:
                    违规.append(任务['路径']+'.'+键+' is not supported beside oneOf')#不得与oneOf并存
            任务=任务表.pop() if 任务表 else None#下一任务
            continue#下一任务
        if 任务['种类']=='对象收尾':
            检查对象模式收尾(任务['节点'],任务['路径'],任务['属性表'],违规)#校验required
            任务=任务表.pop() if 任务表 else None#下一任务
            continue#下一任务
        节点=任务['节点']#进入任务
        路径=任务['路径']#诊断路径
        if not 是否json模式记录(节点):
            违规.append(路径+' must be a schema object')#必须是模式对象
            任务=任务表.pop() if 任务表 else None#无法再下钻
            continue#下一任务
        if id(节点) in 已见:
            违规.append(路径+' is circular')#循环引用
            任务=任务表.pop() if 任务表 else None#不再下钻
            continue#下一任务
        已见.add(id(节点))#标记在途
        任务表.append({'种类':'离开','节点':节点})#离开时解除标记
        for 键 in list(节点.keys()):
            if 键 in 约束关键字:
                continue#约束关键字稍后专检
            if 键 in 注解关键字:
                try:
                    if not 是否json值(节点[键]):
                        违规.append(路径+'.'+键+' annotation must be lossless JSON data')#必须无损JSON
                except Exception:
                    违规.append(路径+'.'+键+' annotation must be lossless JSON data')#同样记无损失败
                continue#下一键
            违规.append(路径+'.'+键+' is not a supported keyword (subset: type/oneOf/properties/required/additionalProperties/items/enum/const + annotations)')#未知关键字
        if 'description' in 节点 and not isinstance(节点.get('description'),str):
            违规.append(路径+'.description must be a string')#必须字符串
        if 'title' in 节点 and not isinstance(节点.get('title'),str):
            违规.append(路径+'.title must be a string')#必须字符串
        有类型='type' in 节点#是否有type
        有联合='oneOf' in 节点#是否有oneOf
        if 有类型 and 有联合:
            违规.append(路径+' cannot declare both type and oneOf')#不得并存
            任务=任务表.pop() if 任务表 else None#不再下钻
            continue#下一任务
        if not 有类型 and not 有联合:
            for 键 in 联合旁禁字:
                if 键 in 节点:
                    违规.append(路径+'.'+键+' requires type or oneOf')#缺判别
            任务=任务表.pop() if 任务表 else None#仅注解
            continue#下一任务
        if 有联合:
            联合=节点.get('oneOf')#各支
            任务表.append({'种类':'联合收尾','节点':节点,'路径':路径})#先下钻各支
            if not 是否普通json数组(联合) or len(联合)<2:
                违规.append(路径+'.oneOf must be an array of at least two schemas')#形态违规
            else:
                下标=len(联合)-1#倒序入栈
                while 下标>=0:
                    任务表.append({'种类':'进入','节点':联合[下标],'路径':路径+'.oneOf['+str(下标)+']'})#进入该支
                    下标-=1#前进
            任务=任务表.pop() if 任务表 else None#下一任务
            continue#下一任务
        类型值=节点.get('type')#类型值
        if not isinstance(类型值,str) or 类型值 not in 模式类型:
            if isinstance(类型值,list):
                违规.append(路径+'.type must be a single type string (type arrays are not supported)')#不支持类型数组
            else:
                违规.append(路径+'.type must be one of '+'/'.join(模式类型))#必须是表内单一字符串
            任务=任务表.pop() if 任务表 else None#无法按类型下钻
            continue#下一任务
        允许宿主={
            'properties':['object'],#仅对象
            'required':['object'],#仅对象
            'additionalProperties':['object'],#仅对象
            'items':['array'],#仅数组
            'enum':['string','number','integer','boolean','null'],#仅标量
            'const':['string','number','integer','boolean','null'],#仅标量
        }#关键字允许的宿主类型
        for 键,宿主 in 允许宿主.items():
            if 键 in 节点 and 类型值 not in 宿主:
                违规.append(路径+'.'+键+' is not supported on type "'+类型值+'"')#该type不支持
        if 类型值=='object':
            属性表=节点.get('properties') if 'properties' in 节点 else None#属性表
            任务表.append({'种类':'对象收尾','节点':节点,'路径':路径,'属性表':属性表})#属性走完再收尾
            if 'properties' in 节点:
                if not 是否json模式记录(属性表):
                    违规.append(路径+'.properties must be an object of schemas')#必须是模式对象表
                else:
                    条目=list(属性表.items())#属性条目
                    下标=len(条目)-1#倒序入栈
                    while 下标>=0:
                        项=条目[下标]#一条
                        if 项 is not None:
                            任务表.append({'种类':'进入','节点':项[1],'路径':路径+'.properties.'+项[0]})#进入属性模式
                        下标-=1#前进
        elif 类型值=='array':
            if 'items' in 节点:
                任务表.append({'种类':'进入','节点':节点.get('items'),'路径':路径+'.items'})#进入元素模式
        elif 类型值 in ('string','number','integer','boolean','null'):
            有枚举='enum' in 节点#是否有enum
            允许=节点.get('enum') if 有枚举 else None#枚举表
            枚举合法=是否普通json数组(允许) and len(允许)>0 and all(标量匹配(类型值,项) for 项 in 允许)#元素匹配类型
            if 有枚举 and not 枚举合法:
                违规.append(路径+'.enum must be a non-empty array of '+类型值+' values')#必须是该类型非空数组
            有常量='const' in 节点#是否有const
            声明常量=节点.get('const') if 有常量 else None#常量
            常量合法=标量匹配(类型值,声明常量)#常量匹配类型
            if 有常量:
                if not 常量合法:
                    违规.append(路径+'.const must be a '+类型值+' value')#必须是该类型值
                elif 枚举合法 and 声明常量 not in 允许:
                    违规.append(路径+'.const must be one of '+路径+'.enum when both are declared')#必须是enum之一
        else:
            断言永不(类型值,'JsonSchemaType')#穷尽
        任务=任务表.pop() if 任务表 else None#下一任务

def 断言受支持json模式(模式):
    """断言任意原始模式只用受强制子集。"""
    违规=[]#违规收集
    检查模式节点(模式,'schema',违规,set())#遍历
    if len(违规)>0:
        raise json模式错误(违规)#有违规则抛

def 断言对象json模式(模式):
    """断言受强制子集，外加对象根约束。"""
    违规=[]#违规收集
    检查模式节点(模式,'schema',违规,set())#先走子集
    if len(违规)==0 and (not 是否json模式记录(模式) or 'type' not in 模式 or 模式.get('type')!='object'):
        违规.append('schema.type must be "object" (structured output is object-rooted)')#结构化输出必须对象根
    if len(违规)>0:
        raise json模式错误(违规)#有违规则抛

def 安全是否JSON值(值):
    """在探测可能抛错时安全探测无损 JSON 边界。"""
    try:
        return 是否json值(值)#无损则真
    except Exception:
        return False#当作有损

def 诊断路径(路径):
    """参数校验器空哨兵路径的根感知诊断路径。"""
    return 'arguments' if 路径=='' else 路径#空路径显示为arguments

def 属性路径(路径,键):
    """在隐式根上追加对象属性时不加前导点。"""
    return 键 if 路径=='' else 路径+'.'+键#根上直接用键

def 无损失败(路径):
    """一个合法模式节点自有的泛型异常收容诊断。"""
    return ['"'+诊断路径(路径)+'" must be a lossless JSON value']#必须无损JSON

def 追加违规(目标,来源):
    """追加诊断，避免把可能很宽的子结果展开成调用参数。"""
    for 项 in 来源:
        目标.append(项)#逐条推入

def 建值帧(节点,值,路径):
    """用空聚合状态初始化一帧校验。"""
    return {
        '节点':节点,#模式
        '值':值,#值
        '路径':路径,#路径
        '收住':False,#尚未判定是否收住抛错
        '阶段':'起始',#起始阶段
        '子':[],#无子
        '子下标':0,#从头
        '违规':[],#空违规
        '收尾违规':[],#空收尾
        '命中':0,#零命中
        '种类':None,#容器种类
    }#新帧

def 检查标量值(节点,值,路径):
    """原始类型检查之后校验一个标量节点。"""
    允许=节点.get('enum') if 'enum' in 节点 else None#枚举
    if 允许 is not None and 值 not in 允许:
        return ['"'+诊断路径(路径)+'" must be one of '+转json(允许)]#必须是枚举之一
    if 'const' in 节点 and 值!=节点.get('const'):
        return ['"'+诊断路径(路径)+'" must be '+转json(节点.get('const'))]#必须等于常量
    return []#标量合法

def 检查值(模式,值,路径):
    """用显式帧而非递归调用校验一对可信模式/值。"""
    帧表=[建值帧(模式,值,路径)]#根帧
    根结果=None#根结果
    def 接收(结果):
        """把子结果交给父帧。"""
        nonlocal 根结果#写根
        if len(帧表)==0:
            根结果=结果#记下根结果
            return#完成
        父=帧表[-1]#父帧
        if 父.get('种类')=='oneOf':
            if len(结果)==0:
                父['命中']+=1#该支通过
        else:
            追加违规(父['违规'],结果)#并入父违规
    def 结束(结果):
        """结束当前帧。"""
        帧表.pop()#弹出
        接收(结果)#交给父或根
    while len(帧表)>0:
        帧=帧表[-1]#当前帧
        try:
            if 帧['阶段']=='子':
                if 帧['子下标']<len(帧['子']):
                    子=帧['子'][帧['子下标']]#下一子
                    if 子 is None:
                        raise Exception('missing schema-value child frame')#子缺失
                    帧['子下标']+=1#前进
                    帧表.append(建值帧(子['节点'],子['值'],子['路径']))#压入子帧
                    continue#去跑子
                if 帧.get('种类')=='oneOf':
                    结束([] if 帧['命中']==1 else ['"'+诊断路径(帧['路径'])+'" must match exactly one oneOf branch (matched '+str(帧['命中'])+')'])#必须恰好一支
                    continue#下一帧
                追加违规(帧['违规'],帧['收尾违规'])#并入收尾违规
                if len(帧['违规'])>0:
                    结束(帧['违规'])#带回违规
                elif 帧.get('种类')=='object':
                    结束([] if 安全是否JSON值(帧['值']) else ['"'+诊断路径(帧['路径'])+'" must be a lossless JSON object'])#必须无损对象
                else:
                    结束([] if 安全是否JSON值(帧['值']) else ['"'+诊断路径(帧['路径'])+'" must be a dense lossless JSON array'])#必须稠密无损数组
                continue#下一帧
            节点类型=帧['节点'].get('type') if 'type' in 帧['节点'] else None#声明类型
            帧['收住']=not (节点类型 is not None and 节点类型 not in 模式类型)#合法类型才收住探测抛错
            联合=帧['节点'].get('oneOf') if 'oneOf' in 帧['节点'] else None#联合各支
            if 联合 is not None:
                帧['种类']='oneOf'#联合帧
                帧['子']=[{'节点':支,'值':帧['值'],'路径':帧['路径']} for 支 in 联合]#各支同值同路径
                帧['子下标']=0#从头
                帧['命中']=0#清命中
                帧['阶段']='子'#去跑各支
                continue#下一循环
            if 节点类型 is None:
                结束([] if 安全是否JSON值(帧['值']) else 无损失败(帧['路径']))#必须无损
                continue#下一帧
            if 节点类型=='object':
                if not 是否普通json记录(帧['值']):
                    结束(['"'+诊断路径(帧['路径'])+'" must be an object'])#必须是对象
                    continue#结束本分支
                属性表=帧['节点'].get('properties') or {} if 'properties' in 帧['节点'] else {}#属性模式
                违规=[]#必填违规
                必填=帧['节点'].get('required') or [] if 'required' in 帧['节点'] else []#必填键
                for 键 in 必填:
                    if 键 not in 帧['值']:
                        违规.append('missing required property "'+属性路径(帧['路径'],键)+'"')#缺必填属性
                子表=[]#要下钻的属性
                for 键,子模式 in 属性表.items():
                    if 键 not in 帧['值']:
                        continue#缺席则跳过
                    子表.append({'节点':子模式,'值':帧['值'][键],'路径':属性路径(帧['路径'],键)})#下钻该属性
                收尾违规=[]#未声明键
                if 'additionalProperties' in 帧['节点'] and 帧['节点'].get('additionalProperties') is False:
                    for 键 in 帧['值'].keys():
                        if 键 not in 属性表:
                            收尾违规.append('"'+属性路径(帧['路径'],键)+'" is not a declared property (additionalProperties: false)')#多余键
                帧['种类']='object'#对象帧
                帧['子']=子表#属性子
                帧['子下标']=0#从头
                帧['违规']=违规#必填违规
                帧['收尾违规']=收尾违规#多余键
                帧['阶段']='子'#去跑属性
            elif 节点类型=='array':
                if not isinstance(帧['值'],list):
                    结束(['"'+诊断路径(帧['路径'])+'" must be an array'])#必须是数组
                    continue#结束本分支
                元素=帧['节点'].get('items') if 'items' in 帧['节点'] else None#元素模式
                子表=[] if 元素 is None else [{'节点':元素,'值':项,'路径':帧['路径']+'['+str(下标)+']'} for 下标,项 in enumerate(帧['值'])]#每个元素一子
                帧['种类']='array'#数组帧
                帧['子']=子表#元素子
                帧['子下标']=0#从头
                帧['违规']=[]#元素违规由接收累加
                帧['阶段']='子'#去跑元素
            elif 节点类型=='string':
                结束(检查标量值(帧['节点'],帧['值'],帧['路径']) if isinstance(帧['值'],str) else ['"'+诊断路径(帧['路径'])+'" must be a string'])#字符串
            elif 节点类型=='number':
                if not isinstance(帧['值'],(int,float)) or isinstance(帧['值'],bool):
                    结束(['"'+诊断路径(帧['路径'])+'" must be a number'])#必须是数字
                elif not 是JSON数字(帧['值']):
                    结束(['"'+诊断路径(帧['路径'])+'" must be a finite JSON number'])#必须是有限JSON数字
                else:
                    结束(检查标量值(帧['节点'],帧['值'],帧['路径']))#再查enum/const
            elif 节点类型=='integer':
                if not 是JSON数字(帧['值']) or 帧['值']!=int(帧['值']):
                    结束(['"'+诊断路径(帧['路径'])+'" must be an integer'])#必须是整数
                else:
                    结束(检查标量值(帧['节点'],帧['值'],帧['路径']))#再查enum/const
            elif 节点类型=='boolean':
                结束(检查标量值(帧['节点'],帧['值'],帧['路径']) if isinstance(帧['值'],bool) else ['"'+诊断路径(帧['路径'])+'" must be a boolean'])#布尔
            elif 节点类型=='null':
                结束(检查标量值(帧['节点'],帧['值'],帧['路径']) if 帧['值'] is None else ['"'+诊断路径(帧['路径'])+'" must be null'])#null
            else:
                结束(断言永不(节点类型,'JsonSchemaType'))#穷尽
        except Exception as 错误:
            失败=帧表.pop() if 帧表 else None#弹出失败帧
            while 失败 is not None and not 失败.get('收住'):
                失败=帧表.pop() if 帧表 else None#找到能收住的帧
            if 失败 is None:
                raise 错误#无人收住则上抛
            接收(无损失败(失败['路径']))#收成无损失败
    return 根结果 if 根结果 is not None else 无损失败(路径)#根结果或回落无损失败

def 校验json模式值(模式,值,路径='value'):
    """按已断言的原始模式校验候选值。"""
    return 检查值(模式,值,路径)#走显式帧

def 自有(对象,键):
    """对齐 Object.hasOwn。"""
    if isinstance(对象,dict):
        return 键 in 对象#映射自有键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:
        return hasattr(对象,键)#无字典则属性
    return 键 in 字典#自有数据

def 转json(值):
    """对齐 JSON.stringify 的紧凑文本。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'))#紧凑 JSON


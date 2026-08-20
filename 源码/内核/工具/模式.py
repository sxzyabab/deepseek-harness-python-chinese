"""统一 JSON 值模式 DSL、类型推断、编译，以及带类型的工具定义辅助。对齐上游 `tools/src/schema.ts`。公开面仅中文名。"""
import math
from llm import 装备错误 as 框架错误#导入框架错误基类
from .json模式 import (
    断言受支持json模式,#统一子集断言
    是否json模式记录,#模式记录检测
    是否普通json数组,#普通数组检测
    json模式错误,#模式错误
    校验json模式值,#值校验
    自有,#自有键
)#导入统一 JSON Schema 校验

__all__=(
    '定义工具','值模式规格转json模式','参数模式规格转json模式',
    '校验参数','工具参数错误',
)#仅中文公开名

注解键表=('description','title','default','examples')#注解键表

def 作者错误(消息):
    """把一条作者模式违规经共享模式错误类型抛出。"""
    raise json模式错误([消息])#包成 json模式错误

def 拷贝注解(源,目标):
    """拷贝自有注解字段，交给原始模式边界校验。"""
    if 自有(源,'description'):
        目标['description']=源['description']#描述
    if 自有(源,'title'):
        目标['title']=源['title']#标题
    if 自有(源,'default'):
        目标['default']=源['default']#默认
    if 自有(源,'examples'):
        目标['examples']=源['examples']#示例

def 核对作者键(源,路径,允许):
    """拒绝节点声明词表之外的作者专用键。"""
    for 键 in list(源.keys()):
        if 键 not in 允许:
            作者错误(路径+'.'+键+' is not supported by the value schema DSL')#越界键

def 安装编译节点(去向,节点):
    """安装已编译节点，避免 __proto__ 赋值语义。"""
    种类=去向['kind']#按去向
    if 种类=='root':
        去向['holder']['value']=节点#写入托盘
    elif 种类=='property':
        去向['target'][去向['key']]=节点#自有可枚举属性
    elif 种类=='item':
        去向['target']['items']=节点#写入 items
    elif 种类=='one-of':
        去向['target'][去向['index']]=节点#写入该支

def 安装编译属性表(去向,已编译):
    """把已编译属性表装到根或所属对象节点上。"""
    if 去向['kind']=='root':
        去向['holder']['value']=已编译#写入托盘
    else:
        去向['target']['properties']=已编译['properties']#写入 properties

def 跑模式编译器(起始):
    """不递归下降地执行作者模式编译任务图。"""
    在途=set()#当前路径上已见节点
    任务列表=[起始]#任务栈
    任务=任务列表.pop() if 任务列表 else None#弹出任务
    while 任务 is not None:
        if 任务['kind']=='leave':
            在途.discard(id(任务['input']))#解除循环标记
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        if 任务['kind']=='property-map-tail':
            if len(任务['required'])>0:
                任务['compiled']['required']=任务['required']#写入编译表
                if 任务['destination']['kind']=='object':
                    任务['destination']['target']['required']=任务['required']#同步到对象节点
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        if 任务['kind']=='property':
            if not 是否json模式记录(任务['property']):
                作者错误(任务['path']+' must be a value schema object')#必须是模式对象
            if 自有(任务['property'],'required') and 任务['property'].get('required') is not True:
                作者错误(任务['path']+'.required must be true when present')#只允许 true
            if 自有(任务['property'],'required') and 任务['property'].get('required') is True:
                任务['required'].append(任务['key'])#收集必填键
            任务列表.append({
                'kind':'value',#值任务
                'input':任务['property'],#属性规格
                'path':任务['path'],#路径
                'allowRequired':True,#允许 required 键
                'destination':{'kind':'property','target':任务['properties'],'key':任务['key']},#写入属性槽
            })#调度值编译
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        if 任务['kind']=='property-map':
            if not 是否json模式记录(任务['input']):
                作者错误(任务['path']+' must be an object of value schemas')#必须是模式对象表
            输入身份=id(任务['input'])#环检测
            if 输入身份 in 在途:
                作者错误(任务['path']+' is circular')#环
            在途.add(输入身份)#标记在途
            已编译={'properties':{}}#空编译表
            必填=[]#必填收集
            安装编译属性表(任务['destination'],已编译)#先装空表
            任务列表.append({'kind':'leave','input':任务['input']})#离开时解除标记
            任务列表.append({'kind':'property-map-tail','compiled':已编译,'required':必填,'destination':任务['destination']})#收尾写 required
            条目列表=list(任务['input'].items())#属性条目
            下标=len(条目列表)-1#倒序入栈以正序处理
            while 下标>=0:
                条目=条目列表[下标]#一条
                if 条目 is not None:
                    任务列表.append({
                        'kind':'property',#属性任务
                        'property':条目[1],#属性规格
                        'path':任务['path']+'.'+条目[0],#路径
                        'key':条目[0],#键
                        'properties':已编译['properties'],#写入目标
                        'required':必填,#必填收集器
                    })#调度属性
                下标-=1#前进
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        输入=任务['input']#值任务的输入
        路径=任务['path']#路径
        if not 是否json模式记录(输入):
            作者错误(路径+' must be a value schema object')#必须是模式对象
        输入身份=id(输入)#环检测
        if 输入身份 in 在途:
            作者错误(路径+' is circular')#环
        在途.add(输入身份)#标记在途
        作者键=list(注解键表)+(['required'] if 任务.get('allowRequired') else [])#允许的作者键
        节点={}#空节点
        安装编译节点(任务['destination'],节点)#先装空节点
        任务列表.append({'kind':'leave','input':输入})#离开时解除标记
        if 自有(输入,'oneOf'):
            核对作者键(输入,路径,作者键+['oneOf','type'])#词表
            if 自有(输入,'type'):
                作者错误(路径+' cannot declare both type and oneOf')#不得并存
            if not 是否普通json数组(输入.get('oneOf')):
                作者错误(路径+'.oneOf must be an array of at least two value schemas')#至少两支数组
            各支=[None]*len(输入['oneOf'])#各支槽
            节点['oneOf']=各支#挂上
            拷贝注解(输入,节点)#拷贝注解
            下标=len(输入['oneOf'])-1#倒序入栈
            while 下标>=0:
                任务列表.append({
                    'kind':'value',#值任务
                    'input':输入['oneOf'][下标],#该支
                    'path':路径+'.oneOf['+str(下标)+']',#路径
                    'allowRequired':False,#联合支不许 required
                    'destination':{'kind':'one-of','target':各支,'index':下标},#写入该槽
                })#调度各支
                下标-=1#前进
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        输入类型=输入.get('type') if 自有(输入,'type') else None#声明类型
        if 输入类型=='json':
            核对作者键(输入,路径,作者键+['type'])#词表
            拷贝注解(输入,节点)#仅注解，无 type
        elif 输入类型=='object':
            核对作者键(输入,路径,作者键+['type','properties','additionalProperties'])#词表
            if (not 自有(输入,'additionalProperties')) or (not isinstance(输入.get('additionalProperties'),bool)):
                作者错误(路径+'.additionalProperties must be explicitly true or false')#必须显式布尔
            节点['type']='object'#对象类型
            拷贝注解(输入,节点)#注解
            节点['additionalProperties']=输入['additionalProperties']#开放性
            if 自有(输入,'properties'):
                任务列表.append({
                    'kind':'property-map',#属性表任务
                    'input':输入.get('properties'),#属性表
                    'path':路径+'.properties',#路径
                    'destination':{'kind':'object','target':节点},#写入本对象
                })#调度属性表
        elif 输入类型=='array':
            核对作者键(输入,路径,作者键+['type','items'])#词表
            节点['type']='array'#数组类型
            拷贝注解(输入,节点)#注解
            if 自有(输入,'items'):
                任务列表.append({
                    'kind':'value',#值任务
                    'input':输入.get('items'),#元素规格
                    'path':路径+'.items',#路径
                    'allowRequired':False,#元素不许 required
                    'destination':{'kind':'item','target':节点},#写入 items
                })#调度元素
        elif 输入类型 in ('string','number','integer','boolean','null'):
            核对作者键(输入,路径,作者键+['type','enum','const'])#词表
            节点['type']=输入类型#标量类型
            拷贝注解(输入,节点)#注解
            if 自有(输入,'enum'):
                if not 是否普通json数组(输入.get('enum')):
                    作者错误(路径+'.enum must be a non-empty array of scalar values')#必须是稠密数组
                节点['enum']=list(输入['enum'])#拷贝枚举
            if 自有(输入,'const'):
                节点['const']=输入.get('const')#单一允许值
        else:
            作者错误(路径+'.type must be string/number/integer/boolean/null/array/object/json, or use oneOf')#必须声明类型或 oneOf
        任务=任务列表.pop() if 任务列表 else None#下一任务

def 编译属性表(输入,路径):
    """编译一张隐式属性表，并收集各属性的必填性。"""
    托盘={}#根托盘
    跑模式编译器({'kind':'property-map','input':输入,'path':路径,'destination':{'kind':'root','holder':托盘}})#从属性表任务起步
    if 托盘.get('value') is None:
        作者错误(路径+' did not compile')#根必须已写入
    return 托盘['value']#已编译表

def 编译值模式(输入,路径):
    """编译一个作者节点，不施加任何消费方根约束。"""
    托盘={}#根托盘
    跑模式编译器({'kind':'value','input':输入,'path':路径,'allowRequired':False,'destination':{'kind':'root','holder':托盘}})#从值任务起步
    if 托盘.get('value') is None:
        作者错误(路径+' did not compile')#根必须已写入
    return 托盘['value']#已编译节点

def 值模式规格转json模式(规格):
    """把一条作者侧值模式编译成受强制的原始 JSON Schema 子集。"""
    模式节点=编译值模式(规格,'schema')#编译
    断言受支持json模式(模式节点)#再过统一子集
    return 模式节点#返回原始模式

def 参数模式规格转json模式(规格):
    """把隐式开放参数对象编译成原始 JSON Schema。"""
    已编译=编译属性表(规格,'parameters')#编译属性表
    模式节点={'type':'object','properties':已编译['properties']}#拼对象根
    if 已编译.get('required') is not None:
        模式节点['required']=已编译['required']#有必填才带 required
    断言受支持json模式(模式节点)#再过统一子集
    return 模式节点#返回参数模式

class 工具参数错误(框架错误):
    """带类型工具上模型生成的非法参数。"""
    def __init__(自身,违规列表):
        """用违规列表构造；公开属性仅 违规列表。"""
        super().__init__('invalid arguments: '+'; '.join(违规列表),'INVALID_ARGS')#拼消息
        自身.name='ToolArgsError'#错误名槽
        自身.违规列表=违规列表#违规诊断列表

def 校验参数(规格,参数):
    """按隐式参数模式校验模型生成的参数。"""
    return 校验json模式值(参数模式规格转json模式(规格),参数,'')#空路径在诊断里显示为 arguments

def 是否正有限(值):
    """超时预算必须为正有限数。"""
    if isinstance(值,bool):
        return False#布尔不是数字
    if isinstance(值,int):
        return 值>0#正整数
    if isinstance(值,float):
        return math.isfinite(值) and 值>0#正有限浮点
    return False#其余非法

def 定义工具(选项):
    """定义带推断参数与严格执行校验的第一方工具。"""
    用户执行=选项['execute']#抽出执行体
    用户最终化内容=选项.get('finalizeContent')#抽出最终内容变换
    用户渲染=选项['output']['render']#抽出渲染
    用户呈现元数据=选项['output'].get('presentationMeta')#抽出呈现元数据
    用户呈现调用=选项.get('presentCall')#抽出待处理呈现
    用户呈现结果=选项.get('presentResult')#抽出完成呈现
    用户并发安全=选项.get('isConcurrencySafe')#抽出并发分类器
    超时毫秒=选项.get('timeoutMs')#超时
    if 超时毫秒 is not None and not 是否正有限(超时毫秒):
        raise Exception('defineTool('+选项['name']+'): timeoutMs must be a positive finite number')#必须是正有限数
    参数模式=参数模式规格转json模式(选项['parameters'])#编译参数模式
    输出模式=值模式规格转json模式(选项['output']['schema'])#编译输出模式
    def 校验(参数):
        """参数校验闭包。"""
        return 校验json模式值(参数模式,参数,'')#校验
    工具={
        'name':选项['name'],#工具名
        'description':选项['description'],#描述
        'parameters':参数模式,#模型可见参数模式
        'output':{
            'schema':输出模式,#已编译输出模式
        },#输出约定
    }#注册表定义
    def 渲染包装(参数,值):
        """渲染包装。"""
        return 用户渲染(参数,值)#交给作者渲染
    工具['output']['render']=渲染包装#渲染包装
    if 用户呈现元数据 is not None:
        def 元数据包装(参数,值):
            """呈现元数据包装。"""
            return 用户呈现元数据(参数,值)#交给作者投影
        工具['output']['presentationMeta']=元数据包装#元数据包装
    if 超时毫秒 is not None:
        工具['timeoutMs']=超时毫秒#可选超时
    def 执行包装(参数,执行上下文):
        """执行包装：先校验参数。"""
        违规=校验(参数)#先校验参数
        if len(违规)>0:
            raise 工具参数错误(违规)#非法参数
        return 用户执行(参数,执行上下文)#交给作者执行体
    工具['execute']=执行包装#执行包装
    if 用户最终化内容:
        def 最终化包装(执行,结果):
            """最终内容包装。"""
            return 用户最终化内容(执行,结果)#原样转发
        工具['finalizeContent']=最终化包装#最终内容

    if 用户呈现调用:
        def 呈现调用包装(参数):
            """软校验包装。"""
            if len(校验(参数))>0:
                return None#不匹配则通用卡片
            return 用户呈现调用(参数)#交给作者呈现
        工具['presentCall']=呈现调用包装#待处理呈现
    if 用户呈现结果:
        def 呈现结果包装(参数,结果):
            """软校验包装。"""
            if len(校验(参数))>0:
                return None#不匹配则通用卡片
            return 用户呈现结果(参数,结果)#交给作者呈现
        工具['presentResult']=呈现结果包装#完成呈现
    if 用户并发安全:
        def 并发包装(参数):
            """软校验包装。"""
            if len(校验(参数))>0:
                return False#不匹配则独占
            return 用户并发安全(参数)#交给作者分类
        工具['isConcurrencySafe']=并发包装#并发分类器
    return 工具#返回注册表定义

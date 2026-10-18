'同步的模式内省，以及设置草稿的不可变路径编辑。'
import copy
import json
import re
from ....依赖.cordis.服务 import 服务
from ..异常 import 抛校验失败

def 写下标(容器,键,值):
    '按下标写入。长度不够时补到该下标'
    下标=int(键)#Number 后的下标
    while len(容器)<=下标:#补齐
        容器.append(None)
    容器[下标]=值#写入

def 克隆脊(根,路径):
    '沿路径浅拷到叶的父级，返回新根、父容器和叶键'
    结果=dict(根)#根拷贝
    目标=结果#当前容器
    序号=0#已走的段
    停=len(路径)-1#叶之前
    while 序号<停:#走到叶的父级
        键=路径[序号]#本段
        下一键=路径[序号+1]#用下一段决定缺席容器的形状
        if isinstance(目标,list):#数组
            旧下标=int(键)
            if 旧下标<len(目标):#已有
                旧=目标[旧下标]
            else:#缺席
                旧=None
        else:#对象
            if 键 in 目标:
                旧=目标[键]
            else:
                旧=None
        if isinstance(旧,list):#数组浅拷
            子=list(旧)
        elif isinstance(旧,dict):#对象浅拷
            子=dict(旧)
        elif isinstance(下一键,str) and re.fullmatch(r'\d+',下一键) is not None:#下一键是下标
            子=[]
        else:#缺席的对象
            子={}
        if isinstance(目标,list):#写回数组
            写下标(目标,键,子)
        else:#写回对象
            目标[键]=子
        目标=子#下行
        序号+=1
    return 结果,目标,路径[len(路径)-1]

def 深相等(甲,乙):
    '常量和对象按值比较'
    if 甲 is 乙:#同一引用
        return True
    if isinstance(甲,dict) and isinstance(乙,dict):#两边对象
        if len(甲)!=len(乙):
            return False
        for 键 in 甲:
            if 键 not in 乙 or 深相等(甲[键],乙[键]) is not True:
                return False
        return True
    if isinstance(甲,list) and isinstance(乙,list):#两边数组
        if len(甲)!=len(乙):
            return False
        序号=0
        while 序号<len(甲):
            if 深相等(甲[序号],乙[序号]) is not True:
                return False
            序号+=1
        return True
    if type(甲) is not type(乙):
        return False
    return 甲==乙

def 转写(数据):
    '校验句里按 JavaScript String 的常见结果写出'
    if 数据 is None:
        return 'null'
    if 数据 is True:
        return 'true'
    if 数据 is False:
        return 'false'
    if isinstance(数据,str):
        return 数据
    if isinstance(数据,(int,float)) and isinstance(数据,bool) is False:
        return str(数据)
    if isinstance(数据,list):
        片段=[]
        for 项 in 数据:
            片段.append(转写(项))
        return ','.join(片段)
    if isinstance(数据,dict):
        return '[object Object]'
    return str(数据)

def 接路径(路径,段):
    '复制路径并接上一段，避免改到调用方的列表'
    if 路径 is None:
        return [段]
    下一=list(路径)
    下一.append(段)
    return 下一

def 解析模式(节点,数据,路径):
    '按节点类型校验。失败抛带路径前缀的异常。序列化回调不执行'
    if not isinstance(节点,dict):#没有节点就原样通过
        return 数据
    类型=节点.get('type')
    元=节点.get('meta')
    if not isinstance(元,dict):
        元={}
    if 数据 is None and 类型!='lazy':#空值走必填和默认
        if 元.get('required') is True:
            抛校验失败('missing required value',路径)
        if 'default' not in 元 or 元.get('default') is None:
            return None
        数据=copy.deepcopy(元['default'])
    if 类型=='any':
        return 数据
    if 类型=='never':
        抛校验失败('expected nullable but got '+转写(数据),路径)
    if 类型=='const':
        if 深相等(数据,节点.get('value')) is True:
            return 节点.get('value')
        抛校验失败('expected '+转写(节点.get('value'))+' but got '+转写(数据),路径)
    if 类型=='string':
        if isinstance(数据,str) is False:
            抛校验失败('expected string but got '+转写(数据),路径)
        表达式=元.get('pattern')
        if isinstance(表达式,dict) and isinstance(表达式.get('source'),str):
            标志=0
            标记=表达式.get('flags') or ''
            if 'i' in 标记:
                标志=标志|re.IGNORECASE
            if 'm' in 标记:
                标志=标志|re.MULTILINE
            if 's' in 标记:
                标志=标志|re.DOTALL
            正则=re.compile(表达式['source'],标志)
            if 正则.search(数据) is None:
                抛校验失败('expect string to match regexp '+表达式['source'],路径)
        if isinstance(元.get('max'),(int,float)) and len(数据)>元['max']:
            抛校验失败('expected string length <= '+str(元['max'])+' but got '+str(len(数据)),路径)
        if isinstance(元.get('min'),(int,float)) and len(数据)<元['min']:
            抛校验失败('expected string length >= '+str(元['min'])+' but got '+str(len(数据)),路径)
        return 数据
    if 类型=='number':
        if isinstance(数据,bool) or isinstance(数据,(int,float)) is False:
            抛校验失败('expected number but got '+转写(数据),路径)
        if isinstance(元.get('max'),(int,float)) and 数据>元['max']:
            抛校验失败('expected number <= '+str(元['max'])+' but got '+转写(数据),路径)
        if isinstance(元.get('min'),(int,float)) and 数据<元['min']:
            抛校验失败('expected number >= '+str(元['min'])+' but got '+转写(数据),路径)
        步长=元.get('step')
        if isinstance(步长,(int,float)) and 步长!=0:
            起点=元['min'] if isinstance(元.get('min'),(int,float)) else 0
            商=(数据-起点)/步长
            if abs(商-round(商))>1e-8:
                抛校验失败('expected number multiple of '+str(步长)+' but got '+转写(数据),路径)
        return 数据
    if 类型=='boolean':
        if isinstance(数据,bool) is False:
            抛校验失败('expected boolean but got '+转写(数据),路径)
        return 数据
    if 类型=='array':
        if isinstance(数据,list) is False:
            抛校验失败('expected array but got '+转写(数据),路径)
        if isinstance(元.get('max'),(int,float)) and len(数据)>元['max']:
            抛校验失败('expected array length <= '+str(元['max'])+' but got '+str(len(数据)),路径)
        if isinstance(元.get('min'),(int,float)) and len(数据)<元['min']:
            抛校验失败('expected array length >= '+str(元['min'])+' but got '+str(len(数据)),路径)
        内层=节点.get('inner')
        结果=[]
        序号=0
        while 序号<len(数据):
            结果.append(解析模式(内层,数据[序号],接路径(路径,序号)))
            序号+=1
        return 结果
    if 类型=='dict':
        if isinstance(数据,dict) is False:
            抛校验失败('expected object but got '+转写(数据),路径)
        键模式=节点.get('sKey')
        内层=节点.get('inner')
        结果={}
        for 键,值 in 数据.items():
            if isinstance(键模式,dict):
                出键=解析模式(键模式,键,路径)
            else:
                出键=键
            结果[出键]=解析模式(内层,值,接路径(路径,键))
        return 结果
    if 类型=='tuple':
        if isinstance(数据,list) is False:
            抛校验失败('expected array but got '+转写(数据),路径)
        表=节点.get('list') or []
        结果=[]
        序号=0
        while 序号<len(表):
            if 序号<len(数据):
                项=数据[序号]
            else:
                项=None
            结果.append(解析模式(表[序号],项,接路径(路径,序号)))
            序号+=1
        if len(数据)>len(表):
            结果.extend(数据[len(表):])
        return 结果
    if 类型=='object':
        if isinstance(数据,dict) is False:
            抛校验失败('expected object but got '+转写(数据),路径)
        字段表=节点.get('dict') or {}
        结果={}
        for 键,子 in 字段表.items():
            if 键 in 数据:
                子值=数据[键]
            else:
                子值=None
            值=解析模式(子,子值,接路径(路径,键))
            if 值 is not None or 键 in 数据:
                结果[键]=值
        for 键,值 in 数据.items():
            if 键 not in 结果:
                结果[键]=值
        return 结果
    if 类型=='union':
        表=节点.get('list') or []
        for 子 in 表:
            try:
                return 解析模式(子,数据,路径)
            except Exception as 支失败:
                continue#支失败不是这一支，试下一支
        try:
            原文=json.dumps(数据,ensure_ascii=False)
        except TypeError:
            原文=转写(数据)
        抛校验失败('expected union but got '+原文,路径)
    if 类型=='intersect':
        表=节点.get('list') or []
        if len(表)==0:
            return 数据
        结果=None
        for 子 in 表:
            值=解析模式(子,数据,路径)
            if 值 is None:
                continue
            if 结果 is None:
                结果=值
            elif isinstance(结果,dict) and isinstance(值,dict):
                合并=dict(结果)
                合并.update(值)
                结果=合并
            elif 结果!=值:
                抛校验失败('expected intersect but got '+转写(数据),路径)
        if isinstance(数据,dict) and isinstance(结果,dict):
            合并=dict(结果)
            for 键,值 in 数据.items():
                if 键 not in 合并:
                    合并[键]=值
            结果=合并
        return 结果
    if 类型=='transform':
        内层结果=解析模式(节点.get('inner'),数据,路径)
        回调=节点.get('callback')
        if callable(回调):
            return 回调(内层结果)
        return 内层结果
    if 类型=='lazy':
        内层=节点.get('inner')
        if isinstance(内层,dict):
            return 解析模式(内层,数据,路径)
        抛校验失败('unsupported type "lazy"',路径)
    抛校验失败('unsupported type "'+str(类型)+'"',路径)

class 设置模式服务(服务):
    '设置自有的同步模式与不可变路径操作'
    def __init__(自身,上下文):
        '服务名 settingsSchema'
        super().__init__(上下文,'settingsSchema')

    def 再水合(自身,序列化):
        '把 schema.toJSON() 信封展开成带 type、dict、inner、list 的节点'
        if not isinstance(序列化,dict) or 'refs' not in 序列化:
            return 序列化
        引用=序列化['refs']
        if not isinstance(引用,dict):
            return 序列化
        节点表={}
        for 键,项 in 引用.items():
            if isinstance(项,dict):
                节点表[str(键)]=dict(项)
            else:
                节点表[str(键)]=项

        def 取(标识):
            '引用号还原成节点。已经是节点则原样返回'
            if isinstance(标识,dict):
                return 标识
            if 标识 is None:
                return None
            return 节点表.get(str(标识),标识)

        for 节点 in list(节点表.values()):
            if not isinstance(节点,dict):
                continue
            if 'sKey' in 节点:
                节点['sKey']=取(节点.get('sKey'))
            if 'inner' in 节点:
                节点['inner']=取(节点.get('inner'))
            列表=节点.get('list')
            if isinstance(列表,list):
                节点['list']=[取(项) for 项 in 列表]
            字段=节点.get('dict')
            if isinstance(字段,dict):
                新字段={}
                for 字段键,字段值 in 字段.items():
                    新字段[字段键]=取(字段值)
                节点['dict']=新字段
        根=节点表.get(str(序列化.get('uid')))
        if 根 is None:
            return 序列化
        return 根

    def 校验(自身,模式,草稿):
        '通过返回 None。失败返回消息。非 Error 的抛出收成字符串'
        try:
            if callable(模式) and isinstance(模式,dict) is False:
                模式(草稿)
            else:
                解析模式(模式,草稿,None)
            return None
        except Exception as 错误:
            return str(错误)

    def 路径节点(自身,根,路径):
        '沿 object、dict、array 走到路径。缺席返回 None'
        节点=根
        for 键 in 路径:
            if 节点 is None:
                return None
            if not isinstance(节点,dict):
                return None
            类型名=节点.get('type')
            if 类型名=='object':
                表=节点.get('dict')
                if isinstance(表,dict) and 键 in 表:
                    节点=表[键]
                else:
                    节点=None
            elif 类型名=='dict' or 类型名=='array':
                节点=节点.get('inner')
            else:
                return None
        return 节点

    def 取路径(自身,值,路径):
        '按键或下标取值。缺席返回 None'
        当前=值
        for 键 in 路径:
            if isinstance(当前,list):
                下标=None
                if isinstance(键,bool):
                    下标=None
                elif isinstance(键,int):
                    下标=键
                elif isinstance(键,float):
                    if 键==键:
                        整=int(键)
                        if 整==键:
                            下标=整
                elif isinstance(键,str):
                    try:
                        数=float(键)
                    except ValueError:
                        数=None
                    if 数 is not None and 数==数:
                        整=int(数)
                        if 整==数:
                            下标=整
                if 下标 is None or 下标<0 or 下标>=len(当前):
                    当前=None
                else:
                    当前=当前[下标]
                continue
            if not isinstance(当前,dict):
                return None
            if 键 not in 当前:
                当前=None
            else:
                当前=当前[键]
        return 当前

    def 有路径(自身,值,路径):
        '叶键是否存在，与值无关'
        if len(路径)==0:
            return 值 is not None
        父=自身.取路径(值,路径[:-1])
        键=路径[len(路径)-1]
        if isinstance(父,list):
            try:
                数=float(键)
            except (TypeError,ValueError):
                return False
            return 数<len(父)
        if not isinstance(父,dict):
            return False
        return 键 in 父

    def 设路径(自身,根,路径,值):
        '不可变写入，并补齐缺席的容器。空路径按上游原文抛出'
        if len(路径)==0:
            raise Exception('ui-settings: setPath needs a non-empty path')
        结果,父,叶=克隆脊(根,路径)
        if isinstance(父,list):
            写下标(父,叶,值)
        else:
            父[叶]=值
        return 结果

    def 删路径(自身,根,路径):
        '不可变删除。路径不存在时返回原来的根。空路径按上游原文抛出'
        if len(路径)==0:
            raise Exception('ui-settings: deletePath needs a non-empty path')
        if 自身.有路径(根,路径) is False:
            return 根
        结果,父,叶=克隆脊(根,路径)
        if isinstance(父,list):
            del 父[int(叶)]
        else:
            del 父[叶]
        return 结果

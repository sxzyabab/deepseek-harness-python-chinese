"""Code Mode 代码生成——Python 风味。把已注册工具模式纯投影成模型编程所用的 Python SDK 文本。对齐上游 `tools/src/py-types.ts`。公开面仅中文名。"""
import json,re,unicodedata
from .json模式 import 断言受支持json模式,转json,自有#导入统一 JSON Schema 断言

__all__=('json模式转py','渲染工具sdkpy')#仅中文公开名

保留字={
    'False','None','True','and','as','assert','async','await','break','class',
    'continue','def','del','elif','else','except','finally','for','from','global',
    'if','import','in','is','lambda','nonlocal','not','or','pass','raise',
    'return','try','while','with','yield','__debug__',
}#硬关键字加 __debug__
导入顺序=('Any','Literal','NotRequired','Protocol','TypedDict')#导入顺序
不可打印=re.compile(r'[\u0000-\u0008\u000e-\u001f\u007f-\u009f]')#Cc 控制转义
未配对代理=re.compile(r'[\ud800-\udfff]')#未配对代理
类名基上限=120#基名上限
列表嵌套上限=180#list 嵌套上限
安全整数上限=2**53-1#JS 安全整数上限

def 是否裸标识符(名称):
    """名字能否作为裸 Python 标识符发出。"""
    return 名称.isidentifier() and unicodedata.normalize('NFKC',名称)==名称#文法匹配且 NFKC 稳定

def 缩进前缀(层数):
    """indent 层行前缀（每层四空格）。"""
    return '    '*层数#四空格一层

def 转义不可打印(字符):
    """Cc 控制转成 \\xNN。"""
    return '\\x'+format(ord(字符),'02x')#Cc → \xNN

def 转义代理(字符):
    """未配对代理转成 \\uNNNN。"""
    return '\\u'+format(ord(字符),'04x')#代理 → \uNNNN

def 折叠描述(模式节点):
    """模式节点折叠成单行的 description。"""
    描述=模式节点.get('description') if isinstance(模式节点,dict) else getattr(模式节点,'description',None)#取出描述
    if not isinstance(描述,str):
        return None#非字符串则无
    折叠=re.sub(r'\s+',' ',描述)#空白压成单空格
    折叠=不可打印.sub(转义不可打印,折叠)#Cc → \xNN
    折叠=未配对代理.sub(转义代理,折叠)#代理 → \uNNNN
    折叠=折叠.strip()#去首尾空白
    return None if len(折叠)==0 else 折叠#空则视为无描述

def 文档行(描述,层数):
    """工具 description 的单行文档字符串；没有则无行。"""
    折叠=折叠描述({'description':描述})#经同一折叠
    if 折叠 is None:
        return []#无描述则无行
    转义=折叠.replace('\\','\\\\').replace('"','\\"')#先反斜杠再引号
    return [缩进前缀(层数)+'"""'+转义+'"""']#单行三引号

def 是否续写(字符):
    """字符能否出现在标识符续写位置。"""
    return ('x'+字符).isidentifier()#续写检测

def 驼峰(原始):
    """把名字 CamelCase 成 Python 类型标识符。"""
    段列表=[]#切词
    当前=[]#当前段
    for 字符 in 原始:
        if 字符=='_' or not 是否续写(字符):
            if 当前:
                段列表.append(''.join(当前))#收一段
                当前=[]#清空
            continue
        当前.append(字符)#续写
    if 当前:
        段列表.append(''.join(当前))#收尾段
    拼接=''#切词并首字母大写
    for 段 in 段列表:
        if len(段)==0:
            continue#丢掉空段
        拼接+=段[0].upper()+段[1:]#首字母大写
    拼接=unicodedata.normalize('NFKC',拼接)#先规范化
    if 拼接 and 拼接[0].isidentifier() and not 拼接[0].isdigit():
        结果=拼接#合法头
    else:
        结果='Tool'+拼接#非法头加 Tool
    return unicodedata.normalize('NFKC',结果)#加前缀后再规范

def 截断类名基(基名):
    """把类名基截到上限。"""
    if len(基名)<=类名基上限:
        return 基名#未超上限
    截断=基名[:类名基上限]#按码元切
    if 截断 and 0xD800<=ord(截断[-1])<=0xDBFF:
        return 截断[:-1]#丢掉尾部高代理
    return 截断#已截断

def 分配类名(基名,状态):
    """从基名预约唯一类名，碰撞时加后缀。"""
    截断=截断类名基(基名)#先截断
    名称=截断#候选
    if 名称 in 状态['usedClassNames']:
        序号=状态['nextClassCounter'].get(截断,2)#从记下的下一计数起步
        while (截断+str(序号)) in 状态['usedClassNames']:
            序号+=1#跳过仍占用的
        名称=截断+str(序号)#带后缀
        状态['nextClassCounter'][截断]=序号+1#记下下次
    状态['usedClassNames'].add(名称)#占用
    return 名称#唯一类名

def 子类名基(基名,片段):
    """把子名片段接到父类名基上。"""
    return 截断类名基(unicodedata.normalize('NFKC',基名+片段))#拼接、规范、截断

def python标量(值):
    """把已校验标量渲染成 Python 字面量文本。"""
    if 值 is True:
        return 'True'#布尔真
    if 值 is False:
        return 'False'#布尔假
    if isinstance(值,str):
        return 转json(值)#字符串 JSON 引号
    if isinstance(值,int) and not isinstance(值,bool) and abs(值)>安全整数上限:
        return str(值)#精确十进制数字
    if isinstance(值,float) and 值.is_integer() and abs(值)>安全整数上限:
        return str(int(值))#精确十进制数字
    if 值 is None:
        return 'None'#到不了这里，防御
    return str(值)#安全整数或浮点

def 渲染受约束标量(节点,宽类型,状态):
    """把已校验标量 const/enum 渲染成 Literal，否则回落宽类型。"""
    if 自有(节点,'const'):
        状态['typing'].add('Literal')#需要 Literal
        return 'Literal['+python标量(节点['const'])+']'#Literal 常量
    if 自有(节点,'enum'):
        状态['typing'].add('Literal')#需要 Literal
        return 'Literal['+', '.join(python标量(项) for 项 in 节点['enum'])+']'#Literal 列表
    return 宽类型#宽类型

def 建渲染帧(模式节点,类名,列表深度):
    """建一帧 Python 类型渲染。"""
    return {
        'schema':模式节点,#本节点
        'className':类名,#类名前缀
        'phase':'start',#阶段
        'kind':None,#容器种类
        'node':None,#typeddict 的对象节点
        'listDepth':列表深度,#list 深度
        'children':[],#子帧规格
        'childIndex':0,#下一子
        'childTypes':[],#已完成子类型
        'entries':[],#typeddict 字段
        'allocated':None,#已分配类名
    }#空聚合

def 是否可作typeddict字段(名称):
    """字段名能否作为类语法 TypedDict 字段。"""
    if not 是否裸标识符(名称):
        return False#非法标识符
    if 名称 in 保留字:
        return False#硬关键字
    if 名称.startswith('__') and not 名称.endswith('__'):
        return False#会名字修饰
    return True#可作字段

def 渲染类型(模式节点,类名,状态):
    """把一个 JSON Schema 节点映射成 Python 类型表达式。"""
    try:
        断言受支持json模式(模式节点)#断言子集
        帧列表=[建渲染帧(模式节点,类名,0)]#根帧
        根结果=None#根类型文本
        def 结束(类型文本):
            """结束当前帧。"""
            nonlocal 根结果#写根
            帧列表.pop()#弹出
            if len(帧列表)==0:
                根结果=类型文本#根结果
            else:
                帧列表[-1]['childTypes'].append(类型文本)#交给父
        while len(帧列表)>0:
            帧=帧列表[-1]#当前帧
            if 帧['phase']=='children':
                if 帧['childIndex']<len(帧['children']):
                    子=帧['children'][帧['childIndex']]#下一子
                    if 子 is None:
                        raise Exception('missing python render child')#子缺失
                    帧['childIndex']=帧['childIndex']+1#前进
                    帧列表.append(建渲染帧(子['schema'],子['className'],子['listDepth']))#压入子
                    continue
                if 帧.get('kind')=='oneOf':
                    联合=''#累积联合
                    下标=0#逐支
                    for 子类型 in 帧['childTypes']:
                        联合=子类型 if 下标==0 else 联合+' | '+子类型#惰性拼接
                        下标+=1#前进
                    结束(联合)#联合类型
                    continue
                if 帧.get('kind')=='array':
                    元素=帧['childTypes'][0] if 帧['childTypes'] else 'Any'#元素类型
                    结束('list['+元素+']')#list[元素]
                    continue
                节点=帧['node']#对象节点
                名称=帧['allocated']#已分配名
                if 节点 is None or 名称 is None:
                    raise Exception('missing typeddict frame state')#状态缺失
                必填=set(节点.get('required') or [])#必填键
                行列表=['class '+名称+'(TypedDict):']#类头
                下标=0#逐字段
                while 下标<len(帧['entries']):
                    条目=帧['entries'][下标]#字段条目
                    字段类型=帧['childTypes'][下标] if 下标<len(帧['childTypes']) else None#已渲染类型
                    if 条目 is None or 字段类型 is None:
                        raise Exception('missing typeddict field type')#对齐失败
                    字段,字段模式=条目#名与模式
                    描述=折叠描述(字段模式)#字段描述
                    if 描述 is not None:
                        行列表.append(缩进前缀(1)+'# '+描述)#注释行
                    if 字段 in 必填:
                        行列表.append(缩进前缀(1)+字段+': '+字段类型)#裸注解
                    else:
                        状态['typing'].add('NotRequired')#需要 NotRequired
                        行列表.append(缩进前缀(1)+字段+': NotRequired['+字段类型+']')#可选包装
                    下标+=1#前进
                if 节点.get('additionalProperties') is not False:
                    行列表.append(缩进前缀(1)+'# Additional keys beyond those declared are allowed.')#开放说明
                if len(行列表)==1:
                    行列表.append(缩进前缀(1)+'pass')#空体
                状态['classes'].append('\n'.join(行列表))#收下类声明
                结束(名称)#类型就是类名
                continue
            帧['phase']='children'#转为处理子
            节点=帧['schema']#本节点
            if 节点.get('oneOf') is not None:
                帧['kind']='oneOf'#联合帧
                子列表=[]#各支
                支下标=0#下标从 0
                for 支 in 节点['oneOf']:
                    子列表.append({'schema':支,'className':子类名基(帧['className'],str(支下标+1)),'listDepth':帧['listDepth']})#各支
                    支下标+=1#前进
                帧['children']=子列表#各支
                continue
            if not 自有(节点,'type'):
                状态['typing'].add('Any')#需要 Any
                结束('Any')#任意
                continue
            类型名=节点['type']#按类型
            if 类型名=='string':
                结束(渲染受约束标量(节点,'str',状态))#字符串
            elif 类型名=='number':
                结束(渲染受约束标量(节点,'float',状态))#浮点
            elif 类型名=='integer':
                结束(渲染受约束标量(节点,'int',状态))#整数
            elif 类型名=='boolean':
                结束(渲染受约束标量(节点,'bool',状态))#布尔
            elif 类型名=='null':
                结束('None')#None
            elif 类型名=='array':
                if not 自有(节点,'items'):
                    状态['typing'].add('Any')#需要 Any
                    结束('list[Any]')#任意元素列表
                elif 帧['listDepth']>=列表嵌套上限:
                    状态['typing'].add('Any')#需要 Any
                    结束('Any')#降级
                else:
                    帧['kind']='array'#数组帧
                    帧['children']=[{'schema':节点['items'],'className':帧['className'],'listDepth':帧['listDepth']+1}]#一个子
            elif 类型名=='object':
                条目列表=list((节点.get('properties') or {}).items())#属性条目
                全部可字段=True#能否具名 TypedDict
                for 字段名,子模式 in 条目列表:
                    if not 是否可作typeddict字段(字段名):
                        全部可字段=False#无法具名
                        break
                if 类名=='' or not 全部可字段:
                    状态['typing'].add('Any')#需要 Any
                    结束('dict[str, Any]')#降级字典
                elif len(条目列表)==0 and 节点.get('additionalProperties') is not False:
                    状态['typing'].add('Any')#需要 Any
                    结束('dict[str, Any]')#任意字典
                else:
                    帧['kind']='typeddict'#具名 TypedDict
                    帧['node']=节点#对象节点
                    帧['allocated']=分配类名(帧['className'],状态)#分配类名
                    状态['typing'].add('TypedDict')#需要 TypedDict
                    帧['entries']=条目列表#字段表
                    子列表=[]#字段子
                    for 字段,子模式 in 条目列表:
                        子列表.append({'schema':子模式,'className':子类名基(帧['allocated'] or '',驼峰(字段)),'listDepth':1})#字段子
                    帧['children']=子列表#字段子
            else:
                状态['typing'].add('Any')#需要 Any
                结束('Any')#未知类型
        if 根结果 is None:
            return 'Any'#根类型或回落
        return 根结果#根类型
    except Exception:
        状态['typing'].add('Any')#需要 Any
        return 'Any'#降级

def json模式转py(模式节点):
    """把一个 JSON Schema 节点映射成来自 typing 模块的无上下文 Python 类型表达式。"""
    return 渲染类型(模式节点,'',{'classes':[],'usedClassNames':set(),'nextClassCounter':{},'typing':set()})#空类名标记无上下文

sdk说明='''## Writing code for run_code

`run_code` takes two required arguments: `code` — the body of an async Python function (top-level `await` and `return` both work) — and `description`, a short summary of what the program does. At run time exactly two of the names declared below are bound: `tools` and `ToolCallError`. Everything else is a STATIC STUB describing argument and return types — in particular the `TypedDict` classes do NOT exist at run time, so build arguments as plain `dict`/`list` JSON values: `await tools.name({"field": 1})`, never `FooArgs(field=1)`, which raises `NameError`. Inside the program:

- Call tools as `await tools.name(args)` — subscript access for exotic, reserved, or underscore-leading names: `await tools["my-tool"](args)`. Every call resolves to the tool's typed canonical JSON value (each method's return type below). Tool arguments must be lossless JSON.
- A FAILED tool call raises `ToolCallError`, whose `toolName` identifies the failed tool and whose message is human-readable — wrap in `try/except` to handle and continue.
- Independent read-only calls MAY overlap under `asyncio.gather` (safe calls run concurrently; mutating calls run alone, in submission order). Sequence dependent work with `await`.
- Emit the run's answer with `print(...)` and/or a top-level `return <value>`; the returned value must be lossless JSON. ONLY what you print and the returned value come back — intermediate tool results never enter the conversation, so extract just what you need.

The available tools:'''#模型可见用法说明，保持英文

def 渲染工具sdkpy(模式列表):
    """渲染完整 tools:sdk 提示词段（Python 风味）。"""
    def 按名(项):
        """取出工具名供字典序。"""
        return 项['name']#名
    已排序=sorted(模式列表,key=按名)#字典序
    状态={'classes':[],'usedClassNames':set(),'nextClassCounter':{},'typing':set(['Protocol'])}#收集器；协议必用
    成员=[]#协议成员行
    语句数=0#真正的方法语句数
    for 模式项 in 已排序:
        参数类型=渲染类型(模式项['parameters'],驼峰(模式项['name'])+'Args',状态)#参数类型
        输出类型=渲染类型(模式项['output'],驼峰(模式项['name'])+'Output',状态)#输出类型
        名称=模式项['name']#工具名
        if 是否裸标识符(名称) and 名称 not in 保留字 and not 名称.startswith('_'):
            文档=文档行(模式项.get('description'),2)#方法文档
            if len(文档)>0:
                成员.append(缩进前缀(1)+'async def '+名称+'(self, args: '+参数类型+') -> '+输出类型+':')#有文档则文档即方法体
            else:
                成员.append(缩进前缀(1)+'async def '+名称+'(self, args: '+参数类型+') -> '+输出类型+': ...')#无文档用 ...
            成员.extend(文档)#文档行（若有）
            语句数+=1#计一条方法
        else:
            成员.append(缩进前缀(1)+'# tools['+转json(名称)+'](args: '+参数类型+') -> '+输出类型)#下标注释
            描述=折叠描述(模式项)#工具描述
            if 描述 is not None:
                成员.append(缩进前缀(1)+'#   '+描述)#缩进描述
    if 语句数>0:
        体行=成员#有方法
    else:
        体行=[缩进前缀(1)+'pass']+成员#可能加 pass
    体='\n'.join(体行)#协议体
    导入=[符号 for 符号 in 导入顺序 if 符号 in 状态['typing']]#按确定顺序
    if len(状态['classes'])>0:
        类块='\n\n'.join(状态['classes'])+'\n\n'#TypedDict 块
    else:
        类块=''#无类
    错误声明='class ToolCallError(Exception):\n    toolName: str'#绑定失败类桩
    声明='from typing import '+', '.join(导入)+'\n\n'+错误声明+'\n\n'+类块+'class Tools(Protocol):\n'+体+'\n\ntools: Tools'#完整声明
    return sdk说明+'\n\n```python\n'+声明+'\n```'#说明 + 代码块

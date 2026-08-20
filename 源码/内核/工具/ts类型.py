"""Code Mode 代码生成：把已注册工具模式纯投影成模型编程所用的 TypeScript SDK 文本。对齐上游 `tools/src/ts-types.ts`。公开面仅中文名。"""
import re
from .json模式 import 断言受支持json模式,转json,自有#导入统一 JSON Schema 校验

__all__=('json模式转ts','渲染工具sdk')#仅中文公开名

裸标识符规则=re.compile(r'^[A-Za-z_$][A-Za-z0-9_$]*$')#裸标识符规则

def 渲染键(名称):
    """渲染对象键：合法标识符则裸写，否则加引号。"""
    return 名称 if 裸标识符规则.match(名称) else 转json(名称)#合法则裸，否则 JSON 引号

def 缩进前缀(层数):
    """一层 indent 的行前缀（每层两空格）。"""
    return '  '*层数#两空格一层

def 文档行(描述,层数):
    """模式 description 的单行 JSDoc 块；没有描述则无行。"""
    if not isinstance(描述,str) or len(描述)==0:
        return []#无描述则空
    折叠=' '.join(描述.split())#空白压成单空格并去首尾
    折叠=折叠.replace('*/','*\\/')#转义注释结束符
    return [缩进前缀(层数)+'/** '+折叠+' */']#转义 */ 后包进 JSDoc

def 渲染标量(值):
    """渲染已被统一模式边界校验过的一个标量。"""
    return 转json(值)#JSON 字面量

def 渲染受约束标量(节点,类型名):
    """渲染已校验标量的 const/enum，否则回落到宽类型。"""
    宽类型='number' if 类型名=='integer' else 类型名#integer 在 TS 里是 number
    if 自有(节点,'const'):
        return 渲染标量(节点['const'])#有 const 则字面量
    if 自有(节点,'enum'):
        return ' | '.join(渲染标量(项) for 项 in 节点['enum'])#联合字面量
    return 宽类型#宽类型

def 建类型文档(片段列表):
    """从已捕获片段建一份文档，并保留旧的数组加括号判定。"""
    含联合=False#是否含联合或交叉
    for 片段 in 片段列表:
        if isinstance(片段,str):
            if '|' in 片段 or '&' in 片段:
                含联合=True#字符串含 |/&
        elif 片段.get('containsUnionOrIntersection'):
            含联合=True#子文档已标记
    return {'parts':list(片段列表),'containsUnionOrIntersection':含联合}#文档

def 类型文档(*片段):
    """在各调用点不经中间数组建一份小文档。"""
    return 建类型文档(片段)#转给 from

def 展平类型文档(文档):
    """用显式工作栈展平嵌套文档。"""
    块列表=[]#输出块
    任务列表=[文档]#待处理栈
    任务=任务列表.pop() if 任务列表 else None#弹出直到空
    while 任务 is not None:
        if isinstance(任务,str):
            块列表.append(任务)#直接写入
            任务=任务列表.pop() if 任务列表 else None#下一任务
            continue
        片段列表=任务['parts']#片段
        下标=len(片段列表)-1#倒序压片段以保持正序
        while 下标>=0:
            片段=片段列表[下标]#当前片段
            if 片段 is not None:
                任务列表.append(片段)#压入栈
            下标-=1#前进
        任务=任务列表.pop() if 任务列表 else None#下一任务
    return ''.join(块列表)#拼成文本

def 建渲染帧(节点,层数):
    """用空聚合状态初始化一帧模式渲染。"""
    return {
        'node':节点,#当前节点
        'indent':层数,#缩进层
        'phase':'start',#阶段
        'kind':None,#节点种类
        'children':[],#子节点
        'childIndex':0,#下一个子下标
        'childDocuments':[],#子文档
        'entries':[],#对象属性项
    }#空聚合

def 渲染已校验模式(模式节点,层数):
    """把已断言的模式渲染成可组合文档。"""
    帧列表=[建渲染帧(模式节点,层数)]#根帧
    根文档=None#根文档
    def 结束(文档):
        """完成当前帧。"""
        nonlocal 根文档#写根文档
        帧列表.pop()#弹出
        if len(帧列表)==0:
            根文档=文档#已到根
        else:
            帧列表[-1]['childDocuments'].append(文档)#交给父
    while len(帧列表)>0:
        帧=帧列表[-1]#当前帧
        if 帧['phase']=='children':
            if 帧['childIndex']<len(帧['children']):
                子=帧['children'][帧['childIndex']]#下一个子
                if 子 is None:
                    raise Exception('missing schema render child')#子缺失
                帧['childIndex']=帧['childIndex']+1#前进
                帧列表.append(建渲染帧(子['node'],子['indent']))#压入子帧
                continue
            if 帧.get('kind')=='oneOf':
                片段=[]#联合片段
                下标=0#逐个子
                while 下标<len(帧['childDocuments']):
                    if 下标>0:
                        片段.append(' | ')#臂之间加 |
                    子文档=帧['childDocuments'][下标]#子文档
                    if 子文档 is not None:
                        片段.append(子文档)#接入联合
                    下标+=1#前进
                结束(建类型文档(片段))#完成联合
                continue
            if 帧.get('kind')=='array':
                子=帧['childDocuments'][0] if 帧['childDocuments'] else None#元素类型
                if 子 is None:
                    raise Exception('missing array item type')#缺元素类型
                if 子.get('containsUnionOrIntersection'):
                    结束(类型文档('(',子,')[]'))#联合/交叉要加括号再 []
                else:
                    结束(类型文档(子,'[]'))#直接 []
                continue
            必填=set(帧['node'].get('required') or [])#必填键
            片段=['{']#对象字面量开头
            下标=0#逐属性
            while 下标<len(帧['entries']):
                条目=帧['entries'][下标]#属性项
                子=帧['childDocuments'][下标]#属性类型
                if 条目 is None or 子 is None:
                    raise Exception('missing object property type')#缺属性类型
                名称,属性节点=条目#键与属性节点
                for 行 in 文档行(属性节点.get('description'),帧['indent']+1):
                    片段.append('\n')#换行
                    片段.append(行)#属性 JSDoc
                可选='' if 名称 in 必填 else '?'#可选标记
                片段.append('\n')#换行
                片段.append(缩进前缀(帧['indent']+1)+渲染键(名称)+可选+': ')#属性行前缀
                片段.append(子)#属性类型
                片段.append(';')#分号
                下标+=1#前进
            片段.append('\n')#换行
            片段.append(缩进前缀(帧['indent'])+'}')#对象结束
            已声明=建类型文档(片段)#已声明对象
            if 帧['node'].get('additionalProperties') is False:
                结束(已声明)#封闭对象
            else:
                结束(类型文档(已声明,' & Record<string, JsonValue>'))#开放对象交叉 Record
            continue
        节点=帧['node']#当前节点
        if 节点.get('oneOf') is not None:
            帧['kind']='oneOf'#记种类
            帧['children']=[{'node':子,'indent':帧['indent']} for 子 in 节点['oneOf']]#各臂
            帧['childIndex']=0#从头
            帧['childDocuments']=[]#清空
            帧['phase']='children'#进入收子
            continue
        if not 自有(节点,'type'):
            结束(类型文档('JsonValue'))#任意 JSON 值
            continue
        类型名=节点['type']#JSON 类型
        if 类型名 in ('string','number','integer','boolean','null'):
            结束(类型文档(渲染受约束标量(节点,类型名)))#受约束标量
        elif 类型名=='array':
            if not 自有(节点,'items'):
                结束(类型文档('JsonValue[]'))#任意 JSON 数组
            else:
                帧['kind']='array'#记种类
                帧['children']=[{'node':节点['items'],'indent':帧['indent']}]#一个子
                帧['childIndex']=0#从头
                帧['childDocuments']=[]#清空
                帧['phase']='children'#进入收子
        elif 类型名=='object':
            开放=节点.get('additionalProperties') is not False#是否开放
            条目列表=list((节点.get('properties') or {}).items())#属性项
            if len(条目列表)==0:
                结束(类型文档('Record<string, JsonValue>' if 开放 else 'Record<string, never>'))#开放任意或封闭空
            else:
                帧['kind']='object'#记种类
                帧['entries']=条目列表#记下项
                帧['children']=[{'node':子,'indent':帧['indent']+1} for 键,子 in 条目列表]#各属性加深一层
                帧['childIndex']=0#从头
                帧['childDocuments']=[]#清空
                帧['phase']='children'#进入收子
        else:
            结束(类型文档('unknown'))#未知
    if 根文档 is None:
        return 类型文档('unknown')#缺根则 unknown
    return 根文档#根文档

def json模式转ts(模式节点,层数=0):
    """把一个已强制的 JSON-Schema 节点映射成 TypeScript 类型字面量。"""
    try:
        断言受支持json模式(模式节点)#先统一校验
        return 展平类型文档(渲染已校验模式(模式节点,层数))#展平文档
    except Exception:
        return 'unknown'#降级

sdk说明='''## Writing code for run_code

`run_code` takes two required arguments: `code` — the body of an async TypeScript function (erasable syntax only — no `enum` or namespaces; type annotations are advisory, the code runs type-stripped) — and `description`, a short summary of what the program does. Inside the program:

- Call tools as `await tools.name(args)` — quoted access for exotic names: `tools["my-tool"](args)`. Every call resolves to the tool's typed canonical JSON value. Tool arguments must be lossless JSON.
- A FAILED tool call rejects with `ToolCallError`, whose `toolName` identifies the failed tool and whose `message` is human-readable — `try/catch` it to handle and continue.
- Independent read-only calls MAY overlap under `Promise.all` (safe calls run concurrently; mutating calls run alone, in submission order). Sequence dependent work with `await`.
- Emit results with `return` and/or `console.log(...)`. ONLY what you print or return comes back to you — intermediate tool results never enter the conversation, so extract just what you need.

The available tools:'''#SDK 用法说明（模型可见，不改字面量）

def 渲染工具sdk(模式列表):
    """渲染完整 tools:sdk 提示词段落。"""
    def 按名(项):
        """取出工具名供字典序。"""
        return 项['name']#名
    已排序=sorted(模式列表,key=按名)#按名排序
    参数成员=[]#参数成员行
    输出成员=[]#输出成员行
    for 模式项 in 已排序:
        参数成员.extend(文档行(模式项.get('description'),1))#参数侧 JSDoc
        参数成员.append(缩进前缀(1)+渲染键(模式项['name'])+': '+json模式转ts(模式项['parameters'],1)+';')#参数类型
        输出成员.append(缩进前缀(1)+渲染键(模式项['name'])+': '+json模式转ts(模式项['output'],1)+';')#输出类型
    if len(参数成员)>0:
        参数映射='interface ToolArgsMap {\n'+'\n'.join(参数成员)+'\n}'#参数映射
    else:
        参数映射='interface ToolArgsMap {}'#空参数映射
    if len(输出成员)>0:
        输出映射='interface ToolOutputMap {\n'+'\n'.join(输出成员)+'\n}'#输出映射
    else:
        输出映射='interface ToolOutputMap {}'#空输出映射
    错误类='\n'.join(['declare class ToolCallError extends Error {','  readonly name: "ToolCallError";','  readonly toolName: ToolName;','}'])#错误类
    工具常量='\n'.join(['declare const tools: {','  [K in ToolName]: (args: ToolArgsMap[K]) => Promise<ToolOutputMap[K]>;','}'])#tools 常量
    声明='\n\n'.join([参数映射,输出映射,'type ToolName = keyof ToolOutputMap',错误类,工具常量])#声明拼好
    json值别名='type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue }'#JSON 值别名
    return sdk说明+'\n\n```ts\n'+json值别名+'\n\n'+声明+'\n```'#包进 fenced ts

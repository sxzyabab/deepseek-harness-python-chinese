"""由模型驱动的 Typert 制品发射器。

对齐上游 `typert/generator/src/emitter.ts`。只消费 FaceModel 与 TypeGraph；
TypeScript 编译器节点不进入本边界。公开面仅中文名。
Remote 声明 source map 细粒度映射依赖 `@jridgewell/gen-mapping`，本面产出合法空映射。
"""
import json,re#字面量与标识符
from .渲染器 import 类型图渲染器#类型图渲染器
from .模型 import 取字段#读字段

__all__=[#公开面
    'Typert发射错误','面模型发射器','FaceModelEmitter','TypertEmitError',
    '引号','缩进','安全标识符','参数边界键','结果边界键','上下文边界键','调用边界根们',
    'quote','indent','safeIdentifier','invocationBoundaryRoots',
]#结束

class Typert发射错误(Exception):#发射期失败
    """把已建模构造投影成制品失败。"""
    name='TypertEmitError'#错误名

TypertEmitError=Typert发射错误#上游名

def 引号(值):#单引号 JS 字符串字面量
    """转义反斜杠、引号、换行。"""
    return "'"+str(值).replace('\\','\\\\').replace("'","\\'").replace('\n','\\n').replace('\r','\\r')+"'"#字面量

quote=引号#上游名

def 缩进(文本,空格数):#给多行文本每行加前缀空格
    """逐行加前缀。"""
    前缀=' '*空格数#前缀
    return '\n'.join(前缀+行 for 行 in 文本.split('\n'))#拼回

indent=缩进#上游名

def 安全标识符(名):#任意名 → 合法标识符
    """非法字符换成下划线。"""
    归一=re.sub(r'[^$\w]','_',名)#非法换下划线
    if re.match(r'^[$A-Z_a-z]',归一):#已有合法起首
        return 归一#原样
    return '_'+归一#前缀下划线

safeIdentifier=安全标识符#上游名

def 参数边界键(调用,序号):#参数边界键
    """id 加参数下标。"""
    return 取字段(调用,'id')+':parameter:'+str(序号)#键

def 结果边界键(调用):#结果边界键
    """id 加 result。"""
    return 取字段(调用,'id')+':result'#键

def 上下文边界键(调用):#身份边界键
    """id 加 context。"""
    return 取字段(调用,'id')+':context'#键

def 调用边界根们(调用们):#调用列表上的全部边界根
    """供 SchemaEmitter 只为调用边界发射模式。"""
    结果=[]#收集根
    for 调用 in 调用们 or []:#逐条调用
        约定=取字段(调用,'invocation') or {}#调用约定
        if 取字段(约定,'kind')=='context':#context 调用有身份边界
            边界=取字段(约定,'boundary') or {}#身份边界
            结果.append({'key':上下文边界键(调用),'type':取字段(边界,'codecType')})#身份编解码类型
        for 序号,参数 in enumerate(取字段(调用,'parameters') or []):#每个业务参数
            边界=取字段(参数,'boundary') or {}#参数边界
            结果.append({'key':参数边界键(调用,序号),'type':取字段(边界,'codecType')})#参数编解码
        结果边界=取字段(调用,'result') or {}#结果边界
        结果.append({'key':结果边界键(调用),'type':取字段(结果边界,'codecType')})#结果编解码
    return 结果#全部边界根

invocationBoundaryRoots=调用边界根们#上游名

def 文档字面量(文档):#文档字段的可 JSON 字面量
    """省略未定义的可选字段。"""
    出={}#结果
    if 取字段(文档,'description') is not None:#有描述
        出['description']=取字段(文档,'description')#描述
    if 取字段(文档,'summary') is not None:#有摘要
        出['summary']=取字段(文档,'summary')#摘要
    出['tags']=list(取字段(文档,'tags') or [])#标签始终写入
    if 取字段(文档,'jsDoc') is not None:#有原始 JSDoc
        出['jsDoc']=取字段(文档,'jsDoc')#JSDoc
    return 出#字面量

def 严格编解码字面量(边界,模式名):#严格模式编解码字面量
    """mode/typeSymbol/schema。"""
    return '\n'.join([#逐行
        '{',
        "  mode: 'strict',",
        '  typeSymbol: '+引号(取字段(边界,'typeSymbol'))+',',
        '  schema: '+模式名+',',
        '}',
    ])#拼成多行

def 包导出说明符(包名,子路径):#包名加导出示路径 → 模块说明符
    """`.` 即包根。"""
    return 包名 if 子路径=='.' else 包名+子路径[1:]#拼子路径

def 渲染远程属性名(名):#方法名 → 接口属性名
    """合法标识符裸写，否则加引号。"""
    return 名 if re.match(r'^[$A-Z_a-z][$\w]*$',名) else 引号(名)#属性名

def 去重命名空间(调用们):#调用列表中的去重命名空间
    """去重后排序。"""
    return sorted({取字段(调用,'namespace') for 调用 in 调用们})#集合排序

def 远程命名空间接口(命名空间):#命名空间 → 稳定接口名
    """用 utf8 十六进制避免非法标识符。"""
    return 'TypertRemoteNamespace$'+命名空间.encode('utf-8').hex()#十六进制

def 远程声明源(包模型,调用):#Remote 声明 map 的源路径
    """相对包根；声明在 lib/，源在包内再上一层。"""
    import os#路径
    根=取字段(包模型,'root') or ''#包根
    文件=取字段(取字段(调用,'location'),'file') or ''#源文件
    相对=os.path.relpath(文件,根).replace('\\','/')#相对包根
    if 相对=='' or 相对=='..' or 相对.startswith('../') or os.path.isabs(相对):#逃出包根
        raise Typert发射错误('Remote declaration '+str(取字段(调用,'id'))+' is outside its package root '+根)#越界
    return '../'+相对#声明在 lib/

def 远程导入们(调用们):#调用边界上的公开类型导入
    """按符号去重。"""
    导入表={}#符号 → 导入
    def 并入(边界):#把一条边界的导入并入
        for 项 in 取字段(边界,'imports') or []:#逐条公开导入
            符号=取字段(项,'symbol')#符号
            当前=导入表.get(符号)#同符号已有
            if 当前 is not None and (取字段(当前,'specifier')!=取字段(项,'specifier') or 取字段(当前,'name')!=取字段(项,'name')):#冲突
                raise Typert发射错误('typert Remote emitter: symbol '+str(符号)+' has inconsistent public imports')#冲突
            导入表[符号]=项#记下
    for 调用 in 调用们 or []:#逐条调用
        约定=取字段(调用,'invocation') or {}#约定
        if 取字段(约定,'kind')=='context':#身份
            并入(取字段(约定,'boundary') or {})#身份边界
        for 参数 in 取字段(调用,'parameters') or []:#参数
            并入(取字段(参数,'boundary') or {})#参数边界
        并入(取字段(调用,'result') or {})#结果边界
    return sorted(导入表.values(),key=lambda 项:(取字段(项,'specifier'),取字段(项,'name')))#排序

def 分配远程导入名(导入们):#为 Remote 导入分配不冲突本地名
    """避开协议名与贡献常量。"""
    已用={'TypertRemoteContribution','TYPERT_REMOTE'}#已占用
    名表={}#符号 → 本地名
    for 项 in 导入们:#逐条
        基=安全标识符(取字段(项,'name') or 'T')#基底
        名=基#候选
        后缀=2#冲突从 2
        while 名 in 已用:#冲突
            名=基+'$remote'+str(后缀)#加后缀
            后缀+=1#递增
        已用.add(名)#占用
        名表[取字段(项,'symbol')]=名#记下
    return 名表#映射

class 模式发射器:#Zod 模式发射器
    """把选定声明与调用边界投影成 Zod 源码。"""
    def __init__(自身,渲染器,模式们,边界们):#按模式与边界根收集闭包并分配内部名
        """构造期分配唯一 $schema 名。"""
        自身.渲染器=渲染器#类型图渲染器
        自身.模式们=list(模式们 or [])#显式选定的模式
        自身.边界们=list(边界们 or [])#调用边界根
        自身.名表={}#声明符号 → 内部模式名
        自身.边界名表={}#边界键 → 内部模式名
        声明图={}#闭包去重
        for 模式 in 自身.模式们:#每个显式模式
            for 声明 in 渲染器.declarationClosureForTypes([取字段(模式,'type')]):#其类型闭包
                声明图[取字段(声明,'id')]=声明#按 id 去重
        for 边界 in 自身.边界们:#每条调用边界
            类型=取字段(边界,'type')#编解码类型
            if 类型 is None:#缺类型
                continue#跳过
            for 声明 in 渲染器.declarationClosureForTypes([类型]):#其编解码类型闭包
                声明图[取字段(声明,'id')]=声明#按 id 去重
        自身.声明们=[声明 for 声明 in (取字段(渲染器.graph,'declarations') or []) if 取字段(声明,'id') in 声明图]#保持图序
        标识符们=set()#已占用的内部名
        for 声明 in 自身.声明们:#为每个声明分配模式名
            基=安全标识符(取字段(声明,'name') or 'T')+'$schema'#名加 $schema
            名=基#候选
            后缀=2#冲突从 2
            while 名 in 标识符们:#冲突
                名=基+str(后缀)#加数字
                后缀+=1#递增
            标识符们.add(名)#占用
            自身.名表[取字段(声明,'id')]=名#记下
        for 边界 in 自身.边界们:#为每条边界分配模式名
            基=安全标识符(取字段(边界,'key') or 'b')+'$schema'#键加 $schema
            名=基#候选
            后缀=2#冲突从 2
            while 名 in 标识符们:#冲突
                名=基+str(后缀)#加数字
                后缀+=1#递增
            标识符们.add(名)#占用
            自身.边界名表[取字段(边界,'key')]=名#记下

    def emit(自身):#发射定义行、导出与边界查询
        """组装模式制品。"""
        定义们=[自身.声明定义(声明) for 声明 in 自身.声明们]#声明 → const
        for 边界 in 自身.边界们:#每条边界再补一条 const
            定义们.append('const '+自身.边界名(取字段(边界,'key'))+' = '+自身.类型模式(取字段(边界,'type')))#边界模式
        导出们=[]#导出表
        for 模型 in 自身.模式们:#显式模式
            导出们.append({#一条导出
                'model':模型,#源模型
                'exportName':安全标识符(取字段(取字段(模型,'export'),'name') or 'schema'),#安全导出名
                'internalName':自身.导出模式名(模型),#内部模式名
            })#结束
        return {#组装
            'definitions':定义们,#定义行
            'exports':导出们,#导出表
            'boundary':自身.边界名,#按键取内部名
        }#制品

    def 声明定义(自身,声明):#一条声明的 const 定义
        """非泛型直接值；泛型工厂。"""
        名=自身.模式名(取字段(声明,'id'))#内部名
        类型参数=取字段(声明,'typeParameters') or []#类型参数
        if len(类型参数)==0:#非泛型
            return 'const '+名+' = '+自身.声明模式(声明,{})#直接
        形参们=[]#形参名与 id
        for 序号,参数 in enumerate(类型参数):#逐个
            形参们.append(('type'+str(序号)+'$schema',取字段(参数,'id')))#形参
        替换={标识:形参 for 形参,标识 in 形参们}#id → 形参名
        return 'const '+名+' = ('+', '.join(形参 for 形参,_ in 形参们)+') => '+自身.声明模式(声明,替换)#工厂

    def 声明模式(自身,声明,替换):#声明本身的 Zod 表达式
        """按种类投影。"""
        种类=取字段(声明,'kind')#种类
        if 种类=='enum':#枚举无 JSON 投影
            自身.失败(取字段(声明,'name'),'enum declarations have no Zod projection')#拒绝
        if 种类=='alias':#类型别名
            if 取字段(声明,'type') is None:#缺类型
                自身.失败(取字段(声明,'name'),'alias has no modeled type')#失败
            return 自身.描述(自身.类型模式(取字段(声明,'type'),替换),声明)#投影并挂描述
        自身对象=自身.对象模式(取字段(声明,'members') or [],取字段(声明,'name'),替换)#自身成员
        结果=自身对象#从自身出发
        for 基 in 取字段(声明,'extends') or []:#逐个 extends
            结果='z.intersection('+自身.类型模式(基,替换)+', '+结果+')'#与基相交
        return 自身.描述(结果,声明)#挂 JSDoc

    def 类型模式(自身,标识,替换=None):#类型节点 → Zod 表达式
        """按节点种类投影。"""
        if 替换 is None:#缺省
            替换={}#空
        节点=自身.渲染器.node(标识)#取节点
        种类=取字段(节点,'kind')#种类
        if 种类=='keyword':#关键字
            return 自身.关键字模式(取字段(节点,'name'))#关键字
        if 种类=='literal':#字面量
            return 'z.literal('+取字段(节点,'text')+')'#字面量
        if 种类=='parenthesized':#括号
            return 自身.类型模式(取字段(节点,'type'),替换)#剥一层
        if 种类=='reference':#引用
            return 自身.引用模式(节点,替换)#引用
        if 种类=='union':#联合
            类型们=取字段(节点,'types') or []#成员
            if len(类型们)==0:#空
                return 'z.never()'#永不
            if len(类型们)==1:#单元素
                return 自身.类型模式(类型们[0],替换)#直接
            return 'z.union(['+', '.join(自身.类型模式(项,替换) for 项 in 类型们)+'])'#联合
        if 种类=='intersection':#交叉
            类型们=取字段(节点,'types') or []#成员
            if len(类型们)==0:#空
                return 'z.unknown()'#unknown
            结果=自身.类型模式(类型们[0],替换)#头部
            for 右 in 类型们[1:]:#其余
                结果='z.intersection('+结果+', '+自身.类型模式(右,替换)+')'#相交
            return 结果#交叉
        if 种类=='array':#数组
            return 'z.array('+自身.类型模式(取字段(节点,'element'),替换)+')'#数组
        if 种类=='tuple':#元组
            固定=[元素 for 元素 in (取字段(节点,'elements') or []) if not 取字段(元素,'rest')]#固定段
            rest=next((元素 for 元素 in (取字段(节点,'elements') or []) if 取字段(元素,'rest')),None)#rest
            模式='z.tuple(['+', '.join(自身.可选(自身.类型模式(取字段(元素,'type'),替换),取字段(元素,'optional')) for 元素 in 固定)+'])'#固定
            if rest is not None:#有 rest
                模式+='.rest('+自身.元组rest模式(取字段(rest,'type'),替换)+')'#追加
            return 模式#元组
        if 种类=='object':#匿名对象
            return 自身.对象模式(取字段(节点,'members') or [],标识,替换)#对象
        自身.失败(取字段(节点,'id'),'type node '+str(种类)+' has no Zod projection')#无投影

    def 引用模式(自身,节点,替换):#引用节点 → Zod
        """声明 / 类型参数 / 标准库。"""
        目标=取字段(节点,'target') or {}#目标
        if 取字段(目标,'kind')=='declaration':#指向声明
            名=自身.模式名(取字段(目标,'symbol'))#内部名
            声明=自身.渲染器.declaration(取字段(目标,'symbol'))#声明
            实参=取字段(节点,'arguments') or []#类型实参
            if len(取字段(声明,'typeParameters') or [])==0:#非泛型
                if len(实参)>0:#多余实参
                    自身.失败(取字段(节点,'name'),'non-generic declaration received '+str(len(实参))+' type arguments')#失败
                return 'z.lazy(() => '+名+')'#惰性
            参数模式=自身.声明实参(节点,声明,替换)#解析实参
            return 'z.lazy(() => '+名+'('+', '.join(参数模式)+'))'#调用工厂
        if 取字段(目标,'kind')=='type-parameter':#类型参数
            if len(取字段(节点,'arguments') or [])>0:#不能实例化
                自身.失败(取字段(节点,'name'),'type parameter reference cannot receive type arguments')#失败
            模式=替换.get(取字段(目标,'parameter'))#查找替换
            if 模式 is None:#闭包外
                自身.失败(取字段(节点,'name'),'type parameter has no schema substitution')#失败
            return 模式#形参名
        if 取字段(目标,'kind')=='standard':#标准库
            标准名=取字段(目标,'name')#标准名
            实参=取字段(节点,'arguments') or []#实参
            if 标准名 in ('Array','ReadonlyArray'):#数组
                if len(实参)==0:#缺元素
                    自身.失败(取字段(节点,'name'),'array reference has no element type')#失败
                数组='z.array('+自身.类型模式(实参[0],替换)+')'#元素数组
                return 数组+('.readonly()' if 标准名=='ReadonlyArray' else '')#只读
            if 标准名=='Record':#记录
                if len(实参)<2:#必须两个
                    自身.失败(取字段(节点,'name'),'Record requires key and value types')#失败
                return 'z.record('+自身.类型模式(实参[0],替换)+', '+自身.类型模式(实参[1],替换)+')'#记录
            if 标准名=='Date':#日期
                return 'z.date()'#日期
            自身.失败(取字段(节点,'name'),'standard type '+str(标准名)+' has no Zod projection')#拒绝
        自身.失败(取字段(节点,'name'),str(取字段(目标,'kind'))+' reference has no Zod projection')#其余拒绝

    def 声明实参(自身,节点,声明,替换):#解析泛型声明的类型实参
        """每个形参对应的 Zod 表达式。"""
        实参=取字段(节点,'arguments') or []#实参
        形参=取字段(声明,'typeParameters') or []#形参
        if len(实参)>len(形参):#过多
            自身.失败(取字段(节点,'name'),'generic declaration accepts '+str(len(形参))+' type arguments but received '+str(len(实参)))#失败
        已解析=dict(替换)#后续默认能看见先解析的
        结果=[]#按形参序
        for 序号,参数 in enumerate(形参):#逐个
            if 序号<len(实参):#显式实参
                模式=自身.类型模式(实参[序号],替换)#外层替换
            elif 取字段(参数,'default') is not None:#用默认
                模式=自身.类型模式(取字段(参数,'default'),已解析)#看见已解析
            else:#缺实参且无默认
                自身.失败(取字段(节点,'name'),'missing type argument '+str(取字段(参数,'name')))#失败
            结果.append(模式)#收下
            已解析[取字段(参数,'id')]=模式#供后续默认
        return 结果#列表

    def 元组rest模式(自身,标识,替换):#元组 rest 必须是数组类型
        """T[] 或 Array/ReadonlyArray。"""
        节点=自身.渲染器.node(标识)#取节点
        if 取字段(节点,'kind')=='array':#T[]
            return 自身.类型模式(取字段(节点,'element'),替换)#元素
        if 取字段(节点,'kind')=='reference':#标准数组引用
            目标=取字段(节点,'target') or {}#目标
            if 取字段(目标,'kind')=='standard' and 取字段(目标,'name') in ('Array','ReadonlyArray'):#数组
                实参=取字段(节点,'arguments') or []#实参
                if len(实参)==0:#缺
                    自身.失败(取字段(节点,'name'),'tuple rest array has no element type')#失败
                return 自身.类型模式(实参[0],替换)#元素
        自身.失败(标识,'tuple rest element must retain an array type')#拒绝

    def 对象模式(自身,成员们,主体,替换):#成员列表 → z.object / z.record
        """固定属性与索引签名。"""
        属性们=[]#固定 JSON 属性
        索引们=[]#索引签名
        符号成员=0#唯一符号成员计数
        for 成员 in 成员们:#逐个成员
            if 取字段(成员,'static') or 取字段(成员,'visibility')!='public':#静态或非公开
                continue#跳过
            if 取字段(成员,'computed')=='symbol':#唯一符号键
                符号成员+=1#计入
                continue#无 JSON 名
            if 取字段(成员,'computed')=='dynamic':#动态计算名
                自身.失败(主体,'computed member '+str(取字段(成员,'name'))+' has no fixed JSON property name')#失败
            if 取字段(成员,'kind')=='index':#索引签名
                参数们=取字段(取字段(成员,'signature'),'parameters') or []#键参数
                if len(参数们)!=1:#必须恰好一个
                    自身.失败(主体,'index signature must have exactly one key parameter')#失败
                记录='z.record('+自身.类型模式(取字段(参数们[0],'type'),替换)+', '+自身.类型模式(取字段(取字段(成员,'signature'),'returns'),替换)+')'#键值
                if 取字段(成员,'readonly'):#只读
                    记录+='.readonly()'#readonly
                索引们.append(记录)#记下
                continue#不进 properties
            if 取字段(成员,'kind')!='property':#方法等不可投影
                自身.失败(主体,str(取字段(成员,'kind'))+' member '+str(取字段(成员,'name'))+' is not data-schema projectable')#失败
            属性模式=自身.描述(#属性模式
                自身.可选(自身.只读(自身.类型模式(取字段(成员,'type'),替换),取字段(成员,'readonly')),取字段(成员,'optional')),
                成员,#挂成员文档
            )#结束
            属性名=取字段(成员,'jsonName') if 取字段(成员,'jsonName') is not None else 取字段(成员,'name')#JSON 名优先
            属性们.append(引号(属性名)+': '+属性模式)#属性行
        if len(索引们)>1:#多于一个索引
            自身.失败(主体,'object type has more than one JSON index signature')#拒绝
        if len(属性们)==0 and len(索引们)==0 and 符号成员>0:#纯符号对象
            return 'z.unknown()'#unknown
        对象体='' if len(属性们)==0 else '\n'+'\n'.join('  '+项+',' for 项 in 属性们)+'\n'#属性体
        对象='z.object({'+对象体+'})'#固定属性对象
        if len(索引们)==0:#无索引
            return 对象#只返回对象
        if len(属性们)==0:#无属性
            return 索引们[0]#只返回记录
        return 'z.intersection('+对象+', '+索引们[0]+')'#对象与索引相交

    def 导出模式名(自身,模型):#显式模式导出对应的内部名
        """泛型不能直接当导出值。"""
        名=自身.模式名(取字段(模型,'symbol'))#内部名
        声明=自身.渲染器.declaration(取字段(模型,'symbol'))#声明
        if len(取字段(声明,'typeParameters') or [])>0:#泛型
            自身.失败(取字段(取字段(模型,'export'),'name'),'generic schema exports require a concrete declaration')#失败
        return 名#内部名

    def 关键字模式(自身,名):#关键字类型 → Zod
        """按关键字名。"""
        表={#关键字 → Zod
            'any':'z.any()','unknown':'z.unknown()','never':'z.never()',
            'string':'z.string()','number':'z.number()','bigint':'z.bigint()',
            'boolean':'z.boolean()','symbol':'z.symbol()','undefined':'z.undefined()',
            'void':'z.void()',
            'object':"z.custom((value) => (typeof value === 'object' && value !== null) || typeof value === 'function')",
        }#表
        if 名 not in 表:#其余拒绝
            自身.失败(名,'keyword '+str(名)+' has no Zod projection')#失败
        return 表[名]#Zod

    def 模式名(自身,符号):#声明符号 → 内部模式名
        """闭包外声明则失败。"""
        名=自身.名表.get(符号)#查找
        if 名 is None:#闭包外
            自身.失败(符号,'referenced declaration is outside the selected schema closure')#失败
        return 名#内部名

    def 边界名(自身,键):#边界键 → 内部模式名
        """未收录则失败。"""
        名=自身.边界名表.get(键)#查找
        if 名 is None:#未收录
            自身.失败(键,'invocation boundary is outside the selected schema roots')#失败
        return 名#内部名

    def 描述(自身,模式,文档):#有描述则 .describe()
        """无描述原样返回。"""
        说明=取字段(文档,'description')#描述
        return 模式 if 说明 is None else 模式+'.describe('+引号(说明)+')'#挂描述

    def 可选(自身,模式,是否可选):#可选则 .optional()
        """非可选原样。"""
        return 模式+'.optional()' if 是否可选 else 模式#可选

    def 只读(自身,模式,是否只读):#只读则 .readonly()
        """非只读原样。"""
        return 模式+'.readonly()' if 是否只读 else 模式#只读

    def 失败(自身,主体,消息):#统一抛出发射错误
        """主体加说明。"""
        raise Typert发射错误('typert Zod emitter: '+str(主体)+': '+消息)#抛出

class 面模型发射器:#面模型发射器
    """从一份独立分析过的面发射生成的运行时与类型制品。"""
    def __init__(自身,面):#按一面图构造
        """用该面类型图构造渲染器。"""
        自身.面=面#面模型
        自身.渲染器=类型图渲染器(取字段(面,'graph'))#渲染器

    def emit(自身,包名):#发射一个包的制品
        """可执行 JavaScript 及其精确声明；宿主面且有调用则带 Remote。"""
        包模型=None#命中包
        for 候选 in 取字段(自身.面,'packages') or []:#按名找
            if 取字段(候选,'name')==包名:#命中
                包模型=候选#记下
                break#停止
        if 包模型 is None:#本面没有该包
            raise Typert发射错误('typert emitter('+str(取字段(自身.面,'face'))+'): package '+包名+' is not modeled on this face')#失败
        模式制品=模式发射器(#为本包构造模式发射器
            自身.渲染器,#渲染器
            取字段(包模型,'schemas') or [],#显式模式
            调用边界根们(取字段(包模型,'invocations') or []),#调用边界根
        ).emit()#立刻发射
        运行时=自身.运行时模型(包模型)#抽出运行时快照
        结果={#组装本包发射结果
            'package':包名,#包名
            'face':取字段(自身.面,'face'),#所在面
            'exports':[取字段(取字段(模式,'export'),'name') for 模式 in (取字段(包模型,'schemas') or [])],#模式导出名
            'js':自身.渲染Js(包模型,模式制品,运行时),#可执行 JS
            'dts':自身.渲染Dts(包模型,模式制品),#精确声明
        }#结束
        if 取字段(自身.面,'face')=='host' and len(取字段(包模型,'invocations') or [])>0:#宿主面且有调用
            结果['remote']=自身.发射远程(包模型)#Host-for-Client Remote
        return 结果#发射结果

    def 运行时模型(自身,包模型):#抽出 TYPERT.model 快照
        """服务 / 事件 / 对象。"""
        服务们=[]#服务列表
        for 服务 in 取字段(包模型,'services') or []:#逐条服务
            成员们=[自身.运行时成员(自身.渲染器.member(标识)) for 标识 in (取字段(服务,'members') or [])]#投影成员
            条目=文档字面量(服务)#文档
            条目['key']=取字段(服务,'key')#服务键
            条目['exportName']=取字段(取字段(服务,'export'),'name')#导出名
            条目['members']=成员们#成员
            条目['types']=自身.运行时类型(自身.渲染器.declarationClosureForMembers(取字段(服务,'members') or []),取字段(服务,'symbol'))#附属类型
            服务们.append(条目)#收下
        事件们=[]#事件列表
        for 事件 in 取字段(包模型,'events') or []:#逐条事件
            节点=自身.渲染器.node(取字段(事件,'signature'))#签名节点
            if 取字段(节点,'kind')!='function':#必须是函数
                raise Typert发射错误('typert emitter('+str(取字段(自身.面,'face'))+'): event '+str(取字段(事件,'name'))+' is not a function type')#失败
            条目=文档字面量(事件)#文档
            条目['name']=取字段(事件,'name')#事件名
            if 取字段(事件,'mode') is not None:#有模式
                条目['mode']=取字段(事件,'mode')#模式
            条目['signature']=引号(取字段(事件,'name'))+自身.渲染器.renderSignature(取字段(节点,'signature'))#名加签名
            事件们.append(条目)#收下
        对象们=[]#对象列表
        for 对象 in 取字段(包模型,'objects') or []:#逐条对象
            声明=自身.渲染器.declaration(取字段(对象,'symbol'))#对象声明
            条目=文档字面量(对象)#文档
            条目['name']=取字段(声明,'name')#声明名
            条目['exportName']=取字段(取字段(对象,'export'),'name')#导出名
            条目['members']=[自身.运行时成员(成员) for 成员 in (取字段(声明,'members') or [])]#投影成员
            条目['types']=自身.运行时类型(自身.渲染器.declarationClosureForMembers([取字段(成员,'id') for 成员 in (取字段(声明,'members') or [])]),取字段(声明,'id'))#附属
            对象们.append(条目)#收下
        return {'services':服务们,'events':事件们,'objects':对象们}#包级快照

    def 运行时成员(自身,成员):#投影一条运行时成员
        """成员快照。"""
        条目={#成员
            'kind':取字段(成员,'kind'),#种类
            'name':取字段(成员,'name'),#名
            'signature':自身.渲染器.renderMember(成员,True),#渲染签名
        }#结束
        if 取字段(成员,'summary') is not None:#有摘要
            条目['summary']=取字段(成员,'summary')#摘要
        if 取字段(成员,'jsDoc') is not None:#有 JSDoc
            条目['jsDoc']=取字段(成员,'jsDoc')#JSDoc
        return 条目#快照

    def 运行时类型(自身,声明们,根):#闭包中去掉根后的附属类型
        """名称与声明文本，按名排序。"""
        结果=[]#列表
        for 声明 in 声明们:#从闭包
            if 取字段(声明,'id')==根:#去掉根
                continue#跳过
            结果.append({'name':取字段(声明,'name'),'declaration':自身.渲染器.renderDeclaration(取字段(声明,'id'))})#投影
        结果.sort(key=lambda 项:项['name'])#按名排序
        return 结果#附属类型

    def 渲染Js(自身,包模型,模式制品,运行时):#渲染本包 JS 制品
        """生成文件头 + zod + TYPERT。"""
        行们=['/* Generated by @deepseek-ai/dsh-typert-generator from FaceModel — do not edit. */']#头
        if len(模式制品['definitions'])>0:#有定义
            行们.extend(["import { z } from 'zod'",''])#导入 zod
        行们.extend(模式制品['definitions'])#内部定义
        if len(模式制品['definitions'])>0:#定义后空行
            行们.append('')#空行
        for 导出 in 模式制品['exports']:#再导出各模式
            行们.append('export const '+导出['exportName']+' = '+导出['internalName'])#导出
        if len(模式制品['exports'])>0:#导出后空行
            行们.append('')#空行
        模型文=json.dumps(运行时,ensure_ascii=False,indent=2)#运行时快照 JSON
        行们.append('export const TYPERT = {')#TYPERT 起
        行们.append('  package: '+引号(取字段(包模型,'name'))+',')#包名
        行们.append('  face: '+引号(取字段(自身.面,'face'))+',')#面名
        行们.append('  schemas: [')#模式表起
        for 导出 in 模式制品['exports']:#逐条
            行们.append('    { name: '+引号(导出['exportName'])+', schema: '+导出['exportName']+' },')#名与 Zod
        行们.append('  ],')#schemas 止
        行们.append('  invocations: [')#调用表起
        for 调用 in 取字段(包模型,'invocations') or []:#逐条调用
            行们.append(缩进(自身.调用字面量(调用,模式制品),4)+',')#缩进后的字面量
        行们.append('  ],')#invocations 止
        行们.append('  model: '+缩进(模型文,2).lstrip()+',')#嵌入快照
        行们.append('}')#TYPERT 止
        return '\n'.join(行们)+'\n'#源码

    def 渲染Dts(自身,包模型,模式制品):#渲染本包声明制品
        """ZodType 钉到源类型；TYPERT 对外 unknown。"""
        导入表={}#说明符 → 导入名
        for 导出 in 模式制品['exports']:#逐条
            说明符=包导出说明符(取字段(包模型,'name'),取字段(取字段(导出['model'],'export'),'subpath'))#说明符
            导入表.setdefault(说明符,[]).append(取字段(取字段(导出['model'],'export'),'name')+' as '+导出['exportName']+'$source')#别名
        行们=['/* Generated by @deepseek-ai/dsh-typert-generator from FaceModel — do not edit. */']#头
        if len(模式制品['exports'])>0:#有导出
            行们.insert(1,"import type { z } from 'zod'")#导入 z
        for 说明符 in sorted(导入表):#按说明符排序
            行们.append('import type { '+', '.join(sorted(导入表[说明符]))+' } from '+引号(说明符))#类型导入
        行们.append('')#空行
        for 导出 in 模式制品['exports']:#逐条模式
            行们.append('export declare const '+导出['exportName']+': z.ZodType<'+导出['exportName']+'$source>')#ZodType
        if len(模式制品['exports'])>0:#声明后空行
            行们.append('')#空行
        行们.append('export declare const TYPERT: unknown')#对外 unknown
        return '\n'.join(行们)+'\n'#声明

    def 发射远程(自身,包模型):#发射 Host-for-Client Remote 制品
        """只为调用边界发射模式。"""
        模式制品=模式发射器(自身.渲染器,[],调用边界根们(取字段(包模型,'invocations') or [])).emit()#立刻发射
        行们=['/* Generated by @deepseek-ai/dsh-typert-generator from the Host FaceModel — do not edit. */']#头
        if len(模式制品['definitions'])>0:#有定义
            行们.extend(["import { z } from 'zod'",''])#导入
        行们.extend(模式制品['definitions'])#定义
        if len(模式制品['definitions'])>0:#空行
            行们.append('')#空行
        行们.append('export const TYPERT_REMOTE = {')#起
        行们.append('  package: '+引号(取字段(包模型,'name'))+',')#包名
        行们.append('  descriptors: [')#描述符表
        for 调用 in 取字段(包模型,'invocations') or []:#逐条
            行们.append(缩进(自身.调用字面量(调用,模式制品),4)+',')#字面量
        行们.append('  ],')#止
        行们.append('}')#对象止
        行们.append('')#空行
        行们.append('export default TYPERT_REMOTE')#默认导出
        声明=自身.渲染远程Dts(包模型)#声明与 map
        return {'js':'\n'.join(行们)+'\n',**声明}#Remote 制品

    def 调用字面量(自身,调用,模式制品):#一条调用的 JS 字面量
        """拼对象字面量。"""
        行们=['{','  id: '+引号(取字段(调用,'id'))+',','  service: '+引号(取字段(调用,'service'))+',','  namespace: '+引号(取字段(调用,'namespace'))+',','  method: '+引号(取字段(调用,'method'))+',']#固定字段
        if 取字段(调用,'implementation') is not None:#有实现名
            行们.append('  implementation: '+引号(取字段(调用,'implementation'))+',')#实现
        约定=取字段(调用,'invocation') or {}#调用约定
        if 取字段(约定,'kind')=='direct':#直接调用
            行们.append("  invocation: { kind: 'direct' },")#直接
        else:#从 Context 解析
            行们.append('  invocation: {')#起
            行们.append("    kind: 'context',")#种类
            行们.append('    context: '+引号(取字段(约定,'context'))+',')#Context 键
            行们.append('    wire: '+引号(取字段(约定,'wire'))+',')#身份线路
            行们.append('    codec: '+缩进(严格编解码字面量(取字段(约定,'boundary'),模式制品['boundary'](上下文边界键(调用))),4).lstrip()+',')#身份编解码
            行们.append('  },')#止
        if 取字段(调用,'scope') is not None:#有作用域
            作用域=取字段(调用,'scope')#scope
            行们.append('  scope: {')#起
            行们.append('    context: '+引号(取字段(作用域,'context'))+',')#键
            行们.append('    wire: '+引号(取字段(作用域,'wire'))+',')#线路
            行们.append('  },')#止
        行们.append('  parameters: [')#参数表
        for 序号,参数 in enumerate(取字段(调用,'parameters') or []):#逐个
            行们.append('    {')#起
            行们.append('      name: '+引号(取字段(参数,'name'))+',')#名
            行们.append('      wire: '+引号(取字段(参数,'wire'))+',')#线路
            行们.append('      source: '+引号(取字段(参数,'source'))+',')#json/lookup
            if 取字段(参数,'lookup') is not None:#有 lookup
                行们.append('      lookup: '+引号(取字段(参数,'lookup'))+',')#lookup
            if 取字段(取字段(参数,'boundary'),'acceptsUndefined'):#显式接受 undefined
                行们.append('      acceptsUndefined: true,')#标记
            行们.append('      codec: '+缩进(严格编解码字面量(取字段(参数,'boundary'),模式制品['boundary'](参数边界键(调用,序号))),6).lstrip()+',')#编解码
            行们.append('    },')#止
        行们.append('  ],')#参数止
        if 取字段(调用,'cancellation') is not None:#有取消
            行们.append("  cancellation: { parameter: 'signal' },")#signal
        行们.append('  result: '+缩进(严格编解码字面量(取字段(调用,'result'),模式制品['boundary'](结果边界键(调用))),2).lstrip()+',')#结果
        行们.append('  sourceLocation: '+json.dumps(取字段(调用,'location'),ensure_ascii=False)+',')#源码位置
        行们.append('}')#对象止
        return '\n'.join(行们)#多行字面量

    def 渲染远程Dts(自身,包模型):#渲染 Remote 声明与 map
        """模块扩充 + TYPERT_REMOTE 声明；dtsMap 为合法空映射。"""
        导入们=远程导入们(取字段(包模型,'invocations') or [])#公开业务类型导入
        引用名=分配远程导入名(导入们)#本地名
        分组={}#说明符 → 导入项
        for 项 in 导入们:#按说明符分组
            分组.setdefault(取字段(项,'specifier'),[]).append({'name':取字段(项,'name'),'local':引用名[取字段(项,'symbol')]})#项
        行们=[#声明行
            '/* Generated by @deepseek-ai/dsh-typert-generator from the Host FaceModel — do not edit. */',
            'import type {',
            '  RemoteResult,',
            '  TypertRemoteContribution,',
            "} from '@deepseek-ai/dsh-typert-protocol'",
        ]#协议导入
        for 说明符 in sorted(分组):#按说明符
            项们=sorted(分组[说明符],key=lambda 项:项['local'])#按本地名
            名们=[项['name'] if 项['name']==项['local'] else 项['name']+' as '+项['local'] for 项 in 项们]#渲染
            行们.append('import type { '+', '.join(名们)+' } from '+引号(说明符))#业务导入
        行们.append('')#空行
        行们.append("declare module '@deepseek-ai/dsh-typert-protocol' {")#模块扩充
        直接=[调用 for 调用 in (取字段(包模型,'invocations') or []) if 取字段(取字段(调用,'invocation'),'kind')=='direct']#直接调用
        作用域调用=[调用 for 调用 in (取字段(包模型,'invocations') or []) if 取字段(取字段(调用,'invocation'),'kind')=='context' or 取字段(调用,'scope') is not None]#scoped
        if len(直接)>0:#有直接调用
            for 命名空间 in 去重命名空间(直接):#每个命名空间
                行们.append('  interface '+远程命名空间接口(命名空间)+' {')#接口起
                for 调用 in [项 for 项 in 直接 if 取字段(项,'namespace')==命名空间]:#该命名空间方法
                    键=渲染远程属性名(取字段(调用,'method'))#方法名
                    行们.append('    '+键+': '+自身.远程函数类型(调用,引用名,False))#方法签名
                行们.append('  }')#接口止
            行们.append('  interface TypertRemoteMap {')#扁平映射
            for 调用 in 直接:#逐条
                行们.append('    '+自身.远程签名(调用,引用名,False))#非 scoped
            行们.append('  }')#止
            行们.append('  interface TypertRemoteNamespaceMap {')#命名空间映射
            for 命名空间 in 去重命名空间(直接):#逐个
                行们.append('    '+引号(命名空间)+': '+远程命名空间接口(命名空间))#名到接口
            行们.append('  }')#止
        if len(作用域调用)>0:#有作用域调用
            行们.append('  interface TypertRemoteScopeMap {')#ScopeMap
            for 调用 in 作用域调用:#逐条
                行们.append('    '+自身.远程签名(调用,引用名,True))#scoped 键
            行们.append('  }')#止
        行们.append('}')#模块扩充止
        行们.append('')#空行
        行们.append('export declare const TYPERT_REMOTE: TypertRemoteContribution')#贡献常量
        行们.append('export default TYPERT_REMOTE')#默认导出
        行们.append('//# sourceMappingURL=typert.remote-client.d.ts.map')#指向 map
        return {#声明制品
            'dts':'\n'.join(行们)+'\n',#声明
            'dtsMap':json.dumps({'version':3,'file':'typert.remote-client.d.ts','sources':[],'names':[],'mappings':''},ensure_ascii=False)+'\n',#合法空映射（细粒度需 gen-mapping）
        }#结束

    def 远程签名(自身,调用,引用名,作用域键):#渲染 TypertRemoteMap / ScopeMap 的一条属性
        """键: 函数类型。"""
        约定=取字段(调用,'invocation') or {}#约定
        if 取字段(约定,'kind')=='context':#context 调用
            上下文=取字段(约定,'context')#身份 Context
        else:#否则用 scope
            上下文=取字段(取字段(调用,'scope'),'context')#scope.context
        if 作用域键:#scoped 键
            键=str(上下文)+':'+取字段(调用,'namespace')+'/'+取字段(调用,'method')#context:ns/method
        else:#直接键
            键=取字段(调用,'namespace')+'/'+取字段(调用,'method')#ns/method
        return 引号(键)+': '+自身.远程函数类型(调用,引用名,作用域键)#引号键加函数类型

    def 远程函数类型(自身,调用,引用名,作用域键):#渲染消费方看到的 Remote 函数类型
        """(...) => Promise<RemoteResult<T>>。"""
        参数们=[]#形参文本
        作用域线路=取字段(取字段(调用,'scope'),'wire')#scope 线路
        for 参数 in 取字段(调用,'parameters') or []:#筛参数
            if 作用域键 and 取字段(取字段(调用,'invocation'),'kind')!='context' and 取字段(参数,'wire')==作用域线路:#由键携带
                continue#省略
            可选='?' if 取字段(参数,'optional') is True else ''#可选
            参数们.append(安全标识符(取字段(参数,'wire'))+可选+': '+自身.渲染器.renderType(取字段(取字段(参数,'boundary'),'type'),引用名))#线路名作参数
        if 取字段(调用,'cancellation') is not None:#有取消
            参数们.append('signal?: AbortSignal')#signal
        结果=自身.渲染器.renderType(取字段(取字段(调用,'result'),'type'),引用名)#结果手写类型
        return '('+', '.join(参数们)+') => Promise<RemoteResult<'+结果+'>>'#包装

FaceModelEmitter=面模型发射器#上游名

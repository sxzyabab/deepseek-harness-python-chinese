"""面向 Cordis 目录的投影：叠在与编译器无关的 Typert 模型之上。

对齐上游 `typert/generator/src/cordis-catalog.ts`。公开面仅中文名。
本模块负责 Cordis 校验与文本投影；调用方提供仓库特有的类型分类与继承数据。
`投影Cordis目录` / `收集事件` / `收集服务`（根扫描入口）必须 WorkspaceAnalyzer，
显式 NotImplementedError，不空壳装通过。
"""
import re#词边界与标签
from .模型 import 子类型节点标识们,取字段#子边与读字段
from .渲染器 import 类型图渲染器#类型图渲染器

__all__=[#公开面
    'Cordis目录投影器','CordisCatalogProjector',
    '投影Cordis目录','projectCordisCatalog',
    '收集事件','collectEvents','收集服务','collectServices',
    '解析JsDoc','parseJsDoc','渲染运行时Api','renderRuntimeApi',
    '渲染页区域','renderPageRegion','渲染继承页','renderInheritedPage',
    '区域开','区域闭','REGION_BEGIN','REGION_END',
    '收集签名类型名','signatureTypeNames',
]#结束

分析器硬缺口='WorkspaceAnalyzer（typert/generator analyzer.ts / TS 编译器 API）未迁；根扫描入口不可空壳装通过。'#硬缺口文案

派发模式=frozenset(['emit','bail','waterfall','parallel','serial'])#五种派发模式
围栏='ts cordis-catalog'#签名围栏语言标记
声明截断=1500#声明截断阈值
区域开='<!-- BEGIN GENERATED cordis-surface (gen-cordis-catalog.ts) — do not edit between markers -->'#开标记
区域闭='<!-- END GENERATED cordis-surface -->'#闭标记
REGION_BEGIN=区域开#上游名
REGION_END=区域闭#上游名

def 是否模式(模式):#是否五种派发模式之一
    """收窄。"""
    return 模式 in 派发模式#合法

def 指针(位置):#源位置格式化成 file:line
    """文件:行号。"""
    return str(取字段(位置,'file'))+':'+str(取字段(位置,'line'))#指针

def 引号(值):#单引号转义
    """反斜杠、引号、换行。"""
    return "'"+str(值).replace('\\','\\\\').replace("'","\\'").replace('\n','\\n')+"'"#字面量

def 引号列表(值们):#字符串数组字面量
    """逐项 quote。"""
    return '['+', '.join(引号(项) for 项 in 值们)+']'#数组

def 渲染参数文档(参数表):#参数文档数组
    """{ name, description }。"""
    项们=['{ name: '+引号(名)+', description: '+引号(描述)+' }' for 名,描述 in 参数表.items()]#项
    return '['+', '.join(项们)+']'#数组

def 首句(文档):#取说明的第一句
    """到句号/问号/叹号。"""
    行=(文档.split('\n',1)[0] if 文档 else '')#第一行
    命中=re.match(r'^(.*?[.!?])(?:\s|$)',行)#句子
    return ((命中.group(1) if 命中 else 行) or '').strip()#句子或整行

def 检查类型链接(定位,名字们,策略,违规们):#按名字检查类型是否已分类
    """追加未分类项。"""
    链页=取字段(策略,'linkedTypePages') or {}#文档页
    基础=取字段(策略,'foundationTypeNames') or set()#基础类型
    豁免=取字段(策略,'typeLinkExemptions') or {}#豁免
    for 名 in 名字们:#逐个
        if 名 in 链页 or 名 in 基础 or 名 in 豁免:#已分类
            continue#跳过
        违规们.append(#追加诊断
            定位+" references unclassified type '"+名+"'. Add it to linkedTypePages with its documentation page, "
            +"to foundationTypeNames if TypeScript or the framework owns it, or to typeLinkExemptions with "
            +"the non-catalog documentation owner."
        )#结束

def 报告类型链接违规(门禁,违规们):#有违规则抛聚合错误
    """聚合全部类型链接违规。"""
    if len(违规们)==0:#无
        return#静默
    raise Exception(门禁+': '+str(len(违规们))+' signature type-link coverage violation(s):\n'+'\n'.join('  '+项 for 项 in 违规们))#抛

def 报告违规(门禁,违规们):#JSDoc 完整性门禁
    """聚合全部 JSDoc 违规。"""
    if len(违规们)==0:#无
        return#静默
    raise Exception(门禁+': '+str(len(违规们))+' JSDoc completeness violation(s) (see AGENTS.md):\n'+'\n'.join('  '+项 for 项 in 违规们))#抛

def 解析JsDoc(原文):#把原始 JSDoc 拆成散文与标签
    """doc / params / returns / throws / deprecated。"""
    行们=[]#去围栏后按行
    去头=re.sub(r'^/\*\*', '', 原文 or '')#去掉开头 /**
    去尾=re.sub(r'\*/$', '', 去头)#去掉结尾 */
    for 行 in 去尾.split('\n'):#按行
        行们.append(re.sub(r'^\s*\*?\s?', '', 行).rstrip())#去引导 * 与行尾空白
    块们=[]#散文块
    段落=[]#当前段落
    列表=[]#当前列表
    项=[]#当前列表项
    进标签=False#是否已进入块标签区

    def 接合(部分):#空白压成单空格
        return re.sub(r'\s+', ' ', ' '.join(部分)).strip()#接合

    def 冲刷项():#冲刷当前列表项
        nonlocal 项,列表#缓冲
        if len(项)>0:#有内容
            列表.append(接合(项))#并入列表
        项=[]#清空

    def 冲刷列表():#冲刷当前列表
        nonlocal 列表#缓冲
        冲刷项()#先冲刷项
        if len(列表)>0:#有列表
            块们.append('\n'.join(列表))#列表作一块
        列表=[]#清空

    def 冲刷段落():#冲刷段落（含其前列表）
        nonlocal 段落#缓冲
        冲刷列表()#先冲刷列表
        if len(段落)>0:#有段落
            块们.append(接合(段落))#段落作一块
        段落=[]#清空

    for 行 in 行们:#第一遍：抽散文
        标签行=行.lstrip()#去行首空白看标签
        if 标签行.startswith('@'):#块标签行
            冲刷段落()#散文到此结束
            进标签=True#进入标签区
            continue#标签正文第二遍
        if 进标签:#标签区续行留给第二遍
            continue#跳过
        if 行.strip()=='':#空行分段
            冲刷段落()#冲刷
            continue#下一行
        if re.match(r'^-\s+',行):#列表项
            冲刷项()#冲刷上一项
            if len(段落)>0:#列表打断了段落
                块们.append(接合(段落))#先落下段落
                段落=[]#清空
            项.append(行)#开始新项
            continue#下一行
        if len(项)>0:#列表续行
            项.append(行)#续行
        else:#段落续行
            段落.append(行)#续行
    冲刷段落()#收尾

    参数表={}#@param
    返回=None#@returns
    抛错们=[]#@throws
    弃用=False#@deprecated
    槽=None#当前标签续行接收器

    for 行 in 行们:#第二遍：抽块标签
        if re.match(r'^@deprecated(?:\s|$)',行):#弃用
            弃用=True#记弃用
            槽=None#无续行
            continue#下一行
        参=re.match(r'^@param\s+(\[?[\w$]+\]?)\s*(?:[-—–]\s*)?(.*)$',行)#@param
        if 参:#命中
            名=re.sub(r'^\[|\]$', '', 参.group(1) or '')#去掉可选方括号
            值=参.group(2) or ''#首行描述
            参数表[名]=值#写入
            def 续参(文本,名=名):#续行接到该 @param
                参数表[名]=(参数表[名]+' '+文本).strip() if 参数表[名] else 文本#追加
            槽=续参#接收器
            continue#下一行
        返=re.match(r'^@returns?(?:\s+[-—–]?\s*(.*))?$',行)#@return(s)
        if 返:#命中
            值=返.group(1) or ''#首行
            返回=值#记下
            def 续返(文本):#续行
                nonlocal 返回#写回
                返回=(返回+' '+文本).strip() if 返回 else 文本#追加
            槽=续返#接收器
            continue#下一行
        抛=re.match(r'^@throws?(?:\s+[-—–]?\s*(.*))?$',行)#@throw(s)
        if 抛:#命中
            值=抛.group(1) or ''#首行
            抛错们.append(值)#新的一条
            下标=len(抛错们)-1#该条下标
            def 续抛(文本,下标=下标):#续行
                抛错们[下标]=(抛错们[下标]+' '+文本).strip() if 抛错们[下标] else 文本#追加
            槽=续抛#接收器
            continue#下一行
        if 行.startswith('@') or 行.strip()=='':#其他标签或空行
            槽=None#结束续行
        elif 槽 is not None:#续行
            槽(行.strip())#接到当前标签

    散文='\n\n'.join(块们)#散文
    散文=re.sub(r'\{@link\s+([^}]+)\}', r'\1', 散文).strip()#展开 {@link}
    return {'doc':散文,'params':参数表,'returns':返回,'throws':抛错们,'deprecated':弃用}#解析结果

parseJsDoc=解析JsDoc#上游名

def 检查参数(定位,api种类,参数们,标签表,是否豁免,违规们):#校验 @param 与形参一一对应
    """绑定模式禁止；豁免不要求。"""
    for 参数 in 参数们:#逐形参
        if 取字段(参数,'binding')!='identifier':#绑定模式
            违规们.append(定位+": parameter '"+str(取字段(参数,'name'))+"' is a binding pattern; the "+api种类+" API needs simple identifier parameters so @param can name them.")#禁止解构
            continue#下一项
        if 是否豁免(参数):#豁免
            continue#不要求
        描述=标签表.get(取字段(参数,'name'))#对应 @param
        if 描述 is None:#缺标签
            违规们.append(定位+' is missing @param '+str(取字段(参数,'name'))+'.')#缺
        elif 描述.strip()=='':#空描述
            违规们.append(定位+': @param '+str(取字段(参数,'name'))+' has an empty description.')#空
    for 标签 in 标签表:#逐 @param
        if not any(取字段(参数,'binding')=='identifier' and 取字段(参数,'name')==标签 for 参数 in 参数们):#对不上
            违规们.append(定位+': @param '+标签+' does not match any parameter (stale tag?).')#陈旧

def 检查返回(定位,签名,返回,渲染器,违规们):#非 void 返回必须有 @returns
    """void / Promise<void> 不要求。"""
    类型=渲染器.renderType(取字段(签名,'returns'))#返回类型文本
    if 类型 in ('void','Promise<void>'):#void
        return#不要求
    if 返回 is None:#缺标签
        违规们.append(定位+' is missing @returns (return type: '+类型+').')#缺
    elif 返回.strip()=='':#空描述
        违规们.append(定位+': @returns has an empty description.')#空

def 收集签名类型名(渲染器,签名):#收集签名引用的类型名
    """去重排序。"""
    名字=set()#去重
    已访=set()#防环

    def 访问签名(当前):#走访一条签名
        for 参数 in 取字段(当前,'typeParameters') or []:#类型参数
            if 取字段(参数,'constraint') is not None:#约束
                访问(取字段(参数,'constraint'))#约束
            if 取字段(参数,'default') is not None:#默认
                访问(取字段(参数,'default'))#默认
        for 参数 in 取字段(当前,'parameters') or []:#形参
            访问(取字段(参数,'type'))#形参类型
        访问(取字段(当前,'returns'))#返回

    def 访问成员(成员):#走访对象成员
        if 取字段(成员,'kind')=='property':#属性
            访问(取字段(成员,'type'))#类型
        else:#方法
            访问签名(取字段(成员,'signature') or {})#签名

    def 访问(标识):#走访一个类型节点
        if 标识 in 已访:#已走访
            return#跳过
        已访.add(标识)#标记
        节点=渲染器.node(标识)#取出
        种类=取字段(节点,'kind')#种类
        if 种类=='reference' and 取字段(取字段(节点,'target'),'kind')!='type-parameter':#非类型参数引用
            名字.add(取字段(节点,'name'))#记下
        if 种类=='type-query':#typeof
            名字.add(取字段(节点,'expression'))#表达式名
        for 子 in 子类型节点标识们(节点):#子节点
            访问(子)#递归
        if 种类=='object':#对象成员
            for 成员 in 取字段(节点,'members') or []:#成员
                访问成员(成员)#成员
        if 种类 in ('function','constructor'):#函数/构造
            访问签名(取字段(节点,'signature') or {})#签名

    访问签名(签名)#从根签名开始
    return sorted(名字)#排序

signatureTypeNames=收集签名类型名#上游名

def 引用类型闭包(种子们,声明表):#从种子签名收集传递引用的类型
    """词边界匹配名字。"""
    已纳={}#名字 → 声明
    前沿=list(种子们)#本轮种子
    while len(前沿)>0:#直到没有新引用
        下一轮=[]#下一轮
        for 名,声明 in 声明表.items():#逐个候选
            if 名 in 已纳:#已纳入
                continue#跳过
            模式=re.compile(r'\b'+re.escape(名)+r'\b')#词边界
            if any(模式.search(文本) for 文本 in 前沿):#本轮引用了它
                已纳[名]=声明#纳入
                下一轮.append(声明)#声明再作种子
        前沿=下一轮#进入下一轮
    return sorted(({'name':名,'declaration':声明} for 名,声明 in 已纳.items()),key=lambda 项:项['name'])#按名排序

class Cordis目录投影器:#Cordis 目录投影器
    """对一个 Typert 面做仓库特有的 Cordis 校验与投影。"""
    def __init__(自身,面,源声明们,策略):#保存面、声明与策略
        """按该面类型图构造渲染器。"""
        自身.面=面#面模型
        自身.源声明们=list(源声明们 or [])#源声明
        自身.策略=策略#策略
        自身.渲染器=类型图渲染器(取字段(面,'graph'))#渲染器

    def project(自身):#校验并投影
        """全部已校验服务与事件。"""
        return {'events':自身.收集事件(),'services':自身.收集服务()}#目录模型

    def renderRuntimeApi(自身,模型):#渲染运行时目录源
        """面向模型的 TypeScript 目录源码。"""
        服务们=list(取字段(模型,'services') or [])+list(取字段(自身.策略,'runtimeServices') or [])#合并
        排除=取字段(自身.策略,'runtimeServiceExclusions') or set()#排除键
        服务们=[项 for 项 in 服务们 if 取字段(项,'key') not in 排除]#过滤
        服务们.sort(key=lambda 项:取字段(项,'key') or '')#按键排序
        return 渲染运行时Api(#交给文本渲染
            服务们,#可见服务
            取字段(模型,'events') or [],#事件
            自身.运行时类型(服务们,取字段(模型,'events') or []),#类型闭包
            取字段(自身.策略,'inheritedServices') or [],#继承 ctx
        )#结束

    def 收集事件(自身):#收集并校验全部事件
        """通过校验的事件。"""
        条目们=[]#通过
        违规们=[]#JSDoc
        类型违规=[]#类型链接
        for 包 in 取字段(自身.面,'packages') or []:#逐包
            for 事件 in 取字段(包,'events') or []:#逐事件
                解析=解析JsDoc(取字段(事件,'jsDoc') or '')#解析 JSDoc
                if 解析['deprecated']:#已弃用
                    continue#跳过
                源=指针(取字段(事件,'location'))#源指针
                定位="event '"+str(取字段(事件,'name'))+"' ("+源+')'#诊断定位
                节点=自身.渲染器.node(取字段(事件,'signature'))#签名节点
                if 取字段(节点,'kind')!='function':#不可调用
                    违规们.append(定位+' is not represented by a callable type.')#违规
                    continue#跳过
                if 取字段(自身.面,'face')=='host':#宿主面才查类型链接
                    检查类型链接(定位,收集签名类型名(自身.渲染器,取字段(节点,'signature')),自身.策略,类型违规)#检查
                模式=取字段(事件,'mode')#@mode
                if not 是否模式(模式):#缺合法 @mode
                    违规们.append(定位+" is missing an @mode tag. Add '@mode emit|bail|waterfall|parallel|serial' to its JSDoc (see AGENTS.md).")#缺
                参数们=取字段(取字段(节点,'signature'),'parameters') or []#形参
                末=参数们[-1] if len(参数们)>0 else None#末形参
                有next=取字段(末,'name')=='next' if 末 is not None else False#末参是否 next
                if 是否模式(模式) and 有next and 模式!='waterfall':#结构是 waterfall 但标签不是
                    违规们.append(定位+" has a trailing 'next' parameter (structurally a waterfall) but is tagged '@mode "+模式+"'. Fix the tag or the signature.")#不符
                if 是否模式(模式) and not 有next and 模式=='waterfall':#标签 waterfall 但无 next
                    违规们.append(定位+" is tagged '@mode waterfall' but has no trailing 'next' parameter. A waterfall delegates via next().")#缺 next
                if 解析['doc']=='':#无说明
                    违规们.append(定位+' has no description prose. Say what happened / what a listener may do, above the block tags.')#缺描述
                检查参数(#校验 @param
                    定位,'event',参数们,解析['params'],
                    lambda 参数,末=末,有next=有next:取字段(参数,'receiver') or (有next and 参数 is 末),
                    违规们,
                )#结束
                if 是否模式(模式):#模式合法才收录
                    名=取字段(事件,'name') or ''#事件名
                    条目们.append({#一条事件
                        'name':名,#作用域名
                        'scope':名.split('/')[0] if '/' in 名 else 名,#首段
                        'signature':取字段(事件,'text'),#签名文本
                        'jsDoc':取字段(事件,'jsDoc') or '',#原始 JSDoc
                        'mode':模式,#派发模式
                        'doc':解析['doc'],#说明散文
                        'source':源,#源指针
                    })#结束
        报告违规('gen-cordis-catalog',违规们)#JSDoc
        报告类型链接违规('gen-cordis-catalog',类型违规)#类型链接
        return 条目们#已校验事件

    def 可渲染服务(自身):#选出可渲染的 ctx 服务
        """类胜出；声明须落在包 src 下。"""
        已选={}#键 → 胜出
        for 包 in 取字段(自身.面,'packages') or []:#逐包
            for 服务 in 取字段(包,'services') or []:#逐服务
                声明=自身.渲染器.declaration(取字段(服务,'symbol'))#声明
                文件=取字段(取字段(服务,'location'),'file') or ''#文件
                主=re.match(r'^(packages/[^/]+/[^/]+/src/)',文件)#包 src 前缀
                if 主 is None:#不在包 src
                    continue#跳过
                所有者=主.group(1)#前缀
                if 取字段(声明,'kind') not in ('class','interface'):#必须类或接口
                    continue#跳过
                if 取字段(自身.面,'face')=='host':#宿主面
                    if not re.match(r'^packages/[^/]+/[^/]+/src/[^/]+\.ts$',文件):#宿主：一层 .ts
                        continue#跳过
                else:#客户端面
                    if not re.match(r'^packages/[^/]+/[^/]+/src/client/.+\.tsx?$',文件):#client 下
                        continue#跳过
                if not (取字段(取字段(声明,'location'),'file') or '').startswith(所有者):#声明须同包
                    continue#跳过
                当前=已选.get(取字段(服务,'key'))#已选同键
                if 当前 is not None and 取字段(自身.渲染器.declaration(取字段(当前,'symbol')),'kind')=='class':#已有类
                    continue#保住
                已选[取字段(服务,'key')]=服务#写入或覆盖
        return list(已选.values())#胜出

    def 收集服务(自身):#收集并校验全部服务
        """按键排序。"""
        条目们=[]#通过
        违规们=[]#JSDoc
        类型违规=[]#类型链接
        for 服务 in 自身.可渲染服务():#逐条
            声明=自身.渲染器.declaration(取字段(服务,'symbol'))#声明
            解析声明=解析JsDoc(取字段(声明,'jsDoc') or '')#类级 JSDoc
            if 解析声明['deprecated']:#已弃用
                continue#跳过
            文档=解析声明['doc']#类级说明
            源=指针(取字段(声明,'location'))#源指针
            if 文档=='':#无 JSDoc
                违规们.append('service ctx.'+str(取字段(服务,'key'))+' ('+源+'): '+str(取字段(声明,'kind'))+' '+str(取字段(声明,'name'))+' has no JSDoc.')#缺
            方法们=[]#公开成员
            for 成员标识 in 取字段(服务,'members') or []:#逐成员
                成员=自身.渲染器.member(成员标识)#成员
                if str(取字段(成员,'name') or '').startswith('['):#索引签名
                    continue#跳过
                解析=解析JsDoc(取字段(成员,'jsDoc') or '')#成员 JSDoc
                if 解析['deprecated']:#已弃用
                    continue#跳过
                if 取字段(成员,'kind')=='property':#属性
                    if 取字段(成员,'jsDoc') is None:#无 JSDoc
                        continue#不收录
                    方法们.append({'kind':'property','signature':取字段(成员,'text'),'jsDoc':取字段(成员,'jsDoc')})#收录
                    continue#属性不跑方法校验
                if 取字段(成员,'kind')!='method':#非方法
                    continue#跳过
                定位='service method ctx.'+str(取字段(服务,'key'))+'.'+str(取字段(成员,'name'))+' ('+指针(取字段(成员,'location'))+')'#定位
                if 取字段(自身.面,'face')=='host':#宿主面
                    检查类型链接(定位,收集签名类型名(自身.渲染器,取字段(成员,'signature')),自身.策略,类型违规)#检查
                方法们.append({'kind':'method','signature':取字段(成员,'text'),'jsDoc':取字段(成员,'jsDoc') or ''})#先收录
                if 取字段(成员,'jsDoc') is None:#缺 JSDoc
                    违规们.append(定位+' has no JSDoc.')#缺
                    continue#不再查
                if 解析['doc']=='':#缺说明
                    违规们.append(定位+' has no description prose above its block tags.')#缺
                检查参数(定位,'service',取字段(取字段(成员,'signature'),'parameters') or [],解析['params'],lambda 参数:取字段(参数,'receiver'),违规们)#@param
                检查返回(定位,取字段(成员,'signature'),解析['returns'],自身.渲染器,违规们)#@returns
            条目们.append({#一条服务
                'key':取字段(服务,'key'),#ctx 键
                'type':取字段(声明,'name'),#类/接口名
                'abstract':取字段(声明,'abstract'),#是否抽象
                'doc':文档,#类级说明
                'methods':方法们,#公开方法
                'source':源,#源指针
            })#结束
        报告违规('gen-cordis-catalog',违规们)#JSDoc
        报告类型链接违规('gen-cordis-catalog',类型违规)#类型链接
        条目们.sort(key=lambda 项:取字段(项,'key') or '')#按键排序
        return 条目们#服务

    def 运行时类型(自身,服务们,事件们):#收集签名引用的类型声明
        """名字与声明文本。"""
        声明表={}#名字 → 声明文本
        歧义=set()#跨文件重名
        for 声明 in 自身.源声明们:#逐条源声明
            if 取字段(声明,'face')!=取字段(自身.面,'face'):#面不符
                continue#跳过
            if 取字段(声明,'kind')=='enum':#枚举
                continue#跳过
            文件=取字段(取字段(声明,'location'),'file') or ''#文件
            if not re.match(r'^packages/[^/]+/[^/]+/src/.+\.tsx?$',文件):#不在包 src
                continue#跳过
            名=取字段(声明,'name')#类型名
            if 名 in 声明表:#同名已出现
                歧义.add(名)#歧义
                continue#不覆盖
            文本=取字段(声明,'text') or ''#声明文本
            if len(文本)>声明截断:#超长
                文本=文本[:声明截断]+' /* …truncated — full shape in source */'#截断桩
            声明表[名]=文本#写入
        for 名 in 歧义:#去掉歧义
            声明表.pop(名,None)#删除
        种子=[]#种子签名
        for 服务 in 服务们:#服务方法
            for 方法 in 取字段(服务,'methods') or []:#方法
                种子.append(取字段(方法,'signature') or '')#签名
        for 事件 in 事件们:#事件
            种子.append(取字段(事件,'signature') or '')#签名
        return 引用类型闭包(种子,声明表)#闭包

CordisCatalogProjector=Cordis目录投影器#上游名

def 投影Cordis目录(扫描根,策略,目标面='host'):#分析一次工作区并投影
    """对齐上游 projectCordisCatalog；必须 WorkspaceAnalyzer。"""
    raise NotImplementedError('投影Cordis目录: '+分析器硬缺口)#硬缺口

projectCordisCatalog=投影Cordis目录#上游名

def 收集事件(扫描根,策略):#收集全部已建模事件
    """对齐上游 collectEvents；委托投影Cordis目录。"""
    raise NotImplementedError('收集事件: '+分析器硬缺口)#硬缺口

collectEvents=收集事件#上游名

def 收集服务(扫描根,策略):#收集全部已建模服务
    """对齐上游 collectServices；委托投影Cordis目录。"""
    raise NotImplementedError('收集服务: '+分析器硬缺口)#硬缺口

collectServices=收集服务#上游名

def 渲染运行时Api(服务们,事件们,类型们,继承服务们):#生成 tool-cordis 消费的目录源
    """对齐上游 renderRuntimeApi：常量表 + 查询辅助（不依赖分析器）。"""
    行们=[#表头（与上游 gen-cordis-api 生成结构对齐）
        '/**',
        ' * Generated by scripts/gen-cordis-api.ts — do not edit by hand; run',
        ' * `pnpm run gen-cordis-api` to regenerate (freshness-gated by',
        ' * `pnpm run verify-cordis-api` in doc-sync).',
        ' *',
        ' * The machine-readable cordis API catalog `cordis_inspect` serves to the',
        ' * model: harness services (summary + structured public method contracts),',
        ' * harness events (mode + structured listener contracts), and the inherited `ctx` API. Produced by',
        ' * the same AST walk as docs/cordis-catalog, so this data and the rendered',
        ' * docs cannot diverge.',
        ' *',
        ' * @module @deepseek-ai/dsh-tool-cordis/api-catalog',
        ' */',
        '',
        '/* jscpd:ignore-start */',
        '/** One named parameter in a Service method or Event listener. */',
        'export interface ApiParameter {',
        '  /** Parameter name from the exact signature. */',
        '  name: string',
        '  /** Source-owned parameter contract. */',
        '  description: string',
        '}',
        '',
        '/** One public service member and its source-owned contract. */',
        'export interface ServiceApiMethod {',
        '  /** Public method signature with its body stripped. */',
        '  signature: string',
        '  /** Method purpose and behavior. */',
        '  description: string',
        '  /** Named parameters in signature order. */',
        '  parameters: readonly ApiParameter[]',
        '  /** Non-void result contract when documented. */',
        '  returns?: string',
        '  /** Documented failure conditions. */',
        '  throws?: readonly string[]',
        '}',
        '',
        '/** One harness `ctx.<key>` service and its public methods. */',
        'export interface ServiceApiEntry {',
        '  /** The `ctx.<key>` name, e.g. `tools`. */',
        '  key: string',
        '  /** First sentence of the service class JSDoc. */',
        '  summary: string',
        '  /** Complete service description. */',
        '  description: string',
        '  /** Public methods, bodies stripped, in source order. */',
        '  methods: readonly ServiceApiMethod[]',
        '}',
        '',
        '/** One harness event: its dispatch mode, exact signature, and listener contract. */',
        'export interface EventApiEntry {',
        '  /** The scoped event name, e.g. `agent/status`. */',
        '  name: string',
        '  /** The dispatch mode from the declaration\'s `@mode` tag. */',
        '  mode: string',
        '  /** The exact listener signature, whitespace-normalized. */',
        '  signature: string',
        '  /** First sentence of the event JSDoc. */',
        '  summary: string',
        '  /** Complete event description. */',
        '  description: string',
        '  /** Named listener parameters in signature order. */',
        '  parameters: readonly ApiParameter[]',
        '}',
        '',
        '/** One inherited (cordis core + loader/hmr/timer) `ctx` member group with its summary. */',
        'export interface InheritedApiEntry {',
        '  /** The `ctx` member name(s), e.g. `ctx.on / ctx.once`. */',
        '  name: string',
        '  /** One-line summary of what the member does. */',
        '  summary: string',
        '}',
        '',
        '/** One named type declaration referenced by a Service or Event signature. */',
        'export interface TypeApiEntry {',
        '  /** The exported type/interface name, e.g. `ShellRunResult`. */',
        '  name: string',
        '  /** The full declaration text, comments stripped. */',
        '  declaration: string',
        '}',
        '',
        '/** Every harness `ctx.<key>` service, sorted by key. */',
        'export const SERVICE_API: readonly ServiceApiEntry[] = [',
    ]#结束表头
    for 服务 in 服务们:#逐服务
        行们.append('  {')#对象起
        行们.append('    key: '+引号(取字段(服务,'key'))+',')#键
        行们.append('    summary: '+引号(首句(取字段(服务,'doc') or ''))+',')#摘要
        行们.append('    description: '+引号(取字段(服务,'doc') or '')+',')#完整描述
        方法们=取字段(服务,'methods') or []#方法
        if len(方法们)==0:#无方法
            行们.append('    methods: [],')#空
        else:#有方法
            行们.append('    methods: [')#起
            for 方法 in 方法们:#逐方法
                约定=解析JsDoc(取字段(方法,'jsDoc') or '')#解析
                行们.append('      {')#起
                行们.append('        signature: '+引号(取字段(方法,'signature') or '')+',')#签名
                行们.append('        description: '+引号(约定['doc'])+',')#描述
                行们.append('        parameters: '+渲染参数文档(约定['params'])+',')#参数
                if 约定['returns'] is not None:#有 @returns
                    行们.append('        returns: '+引号(约定['returns'])+',')#返回
                if len(约定['throws'])>0:#有 @throws
                    行们.append('        throws: '+引号列表(约定['throws'])+',')#抛错
                行们.append('      },')#止
            行们.append('    ],')#方法止
        行们.append('  },')#服务止
    行们.extend([#事件表头
        ']',
        '',
        '/** Every harness event, sorted by name. */',
        'export const EVENT_API: readonly EventApiEntry[] = [',
    ])#结束
    for 事件 in sorted(事件们,key=lambda 项:取字段(项,'name') or ''):#按名
        约定=解析JsDoc(取字段(事件,'jsDoc') or '')#解析
        行们.append('  {')#起
        行们.append('    name: '+引号(取字段(事件,'name'))+',')#名
        行们.append('    mode: '+引号(取字段(事件,'mode'))+',')#模式
        行们.append('    signature: '+引号(取字段(事件,'signature') or '')+',')#签名
        行们.append('    summary: '+引号(首句(取字段(事件,'doc') or ''))+',')#摘要
        行们.append('    description: '+引号(取字段(事件,'doc') or '')+',')#描述
        行们.append('    parameters: '+渲染参数文档(约定['params'])+',')#参数
        行们.append('  },')#止
    行们.extend([#类型表头
        ']',
        '',
        '/** Shapes of every exported type the Service and Event signatures reference (transitively), sorted by name. */',
        'export const TYPE_API: readonly TypeApiEntry[] = [',
    ])#结束
    for 类型 in 类型们:#逐类型
        行们.append('  {')#起
        行们.append('    name: '+引号(取字段(类型,'name'))+',')#名
        行们.append('    declaration: '+引号(取字段(类型,'declaration'))+',')#声明
        行们.append('  },')#止
    行们.extend([#继承表头
        ']',
        '',
        '/** The inherited `ctx` API (cordis core + loader/hmr/timer), in curated order. */',
        'export const INHERITED_CTX_API: readonly InheritedApiEntry[] = [',
    ])#结束
    for 项 in 继承服务们:#逐条
        行们.append('  { name: '+引号(取字段(项,'name'))+', summary: '+引号(取字段(项,'summary'))+' },')#条目
    行们.extend([#查询辅助与导出函数（对齐上游字节结构）
        ']',
        '',
        'function referencedTypeClosure(seeds: readonly string[]): TypeApiEntry[] {',
        '  const included = new Set<string>()',
        '  let frontier = [...seeds]',
        '  while (frontier.length > 0) {',
        '    const next: string[] = []',
        '    for (const entry of TYPE_API) {',
        '      if (included.has(entry.name)) continue',
        '      const pattern = new RegExp(`\\b${entry.name}\\b`)',
        '      if (!frontier.some(text => pattern.test(text))) continue',
        '      included.add(entry.name)',
        '      next.push(entry.declaration)',
        '    }',
        '    frontier = next',
        '  }',
        '  return TYPE_API.filter(entry => included.has(entry.name))',
        '}',
        '',
        'function contextProperty(key: string): string {',
        '  return /^[A-Za-z_$][\\w$]*$/.test(key) ? `ctx.${key}` : `ctx[${JSON.stringify(key)}]`',
        '}',
        '',
        '/**',
        ' * Project the Service Catalog as a compact directory or one exact coding contract.',
        ' * @param key - exact Service key; omit it to list all Services and method signatures.',
        ' * @param services - platform-specific visible Service entries.',
        ' * @returns compact navigation data or one detailed Service with its referenced type closure.',
        ' */',
        'export function queryServiceApi(key?: string, services: readonly ServiceApiEntry[] = SERVICE_API): object {',
        '  if (key === undefined) {',
        '    return {',
        "      mode: 'catalog',",
        '      services: services.map(service => ({',
        '        key: service.key,',
        '        description: service.summary,',
        '        methods: service.methods.map(method => ({ signature: method.signature })),',
        '      })),',
        '    }',
        '  }',
        '  const service = services.find(candidate => candidate.key === key)',
        '  if (service === undefined) throw new Error(`no catalogued Service named "${key}"`)',
        '  return {',
        "    mode: 'service',",
        '    service: {',
        '      key: service.key,',
        '      description: service.description,',
        '      access: {',
        '        optional: { expression: `ctx.get(${JSON.stringify(service.key)})`, requiresUndefinedCheck: true },',
        '        hardDependency: { inject: [service.key], expression: contextProperty(service.key) },',
        '      },',
        '      methods: service.methods,',
        '    },',
        '    referencedTypes: referencedTypeClosure(service.methods.map(method => method.signature)),',
        '  }',
        '}',
        '',
        '/**',
        ' * Project the Event Catalog as a compact directory or one exact listener contract.',
        ' * @param name - exact Event name; omit it to list all Events and listener signatures.',
        ' * @param events - platform-specific visible Event entries.',
        ' * @returns compact navigation data or one detailed Event with its referenced type closure.',
        ' */',
        'export function queryEventApi(name?: string, events: readonly EventApiEntry[] = EVENT_API): object {',
        '  if (name === undefined) {',
        '    return {',
        "      mode: 'catalog',",
        '      events: events.map(event => ({',
        '        name: event.name,',
        '        description: event.summary,',
        '        mode: event.mode,',
        '        signature: event.signature,',
        '      })),',
        '    }',
        '  }',
        '  const event = events.find(candidate => candidate.name === name)',
        '  if (event === undefined) throw new Error(`no catalogued Event named "${name}"`)',
        '  return {',
        "    mode: 'event',",
        '    event: {',
        '      name: event.name,',
        '      description: event.description,',
        '      mode: event.mode,',
        '      signature: event.signature,',
        '      parameters: event.parameters,',
        '    },',
        '    referencedTypes: referencedTypeClosure([event.signature]),',
        '  }',
        '}',
        '/* jscpd:ignore-end */',
        '',
    ])#结束查询函数
    return '\n'.join(行们)#完整源

renderRuntimeApi=渲染运行时Api#上游名


def githubSlug(标题):#GitHub 标题 slug
    """小写；只留字母数字空格连字符；空格变连字符（对齐上游 \\p{L}\\p{N}）。"""
    小写=标题.lower()#小写
    保留=''.join(字符 for 字符 in 小写 if 字符.isalnum() or 字符 in ' -')#字母数字空格连字符
    return 保留.replace(' ','-')#空格变连字符

def 锚行(标题文本):#显式 <a id> 与空行
    """锚 + 空行。"""
    return ['<a id="'+githubSlug(标题文本)+'"></a>', '']#锚

def 类型链接行(签名,本页,链页):#签名类型交叉链接行
    """Types: 行；无则空串。"""
    见到=set()#出现过的类型名
    for 名 in (链页 or {}):#逐个可链接
        if re.search(r'\b'+re.escape(名)+r'\b',签名 or ''):#词边界命中
            见到.add(名)#记下
    链接们=['['+名+']('+链页[名]+')' for 名 in sorted(见到) if 链页.get(名)!=本页]#丢掉当前页
    return '' if len(链接们)==0 else 'Types: '+' · '.join(链接们)#Types 行

def 渲染事件(事件,本页,链页):#渲染一条事件 Markdown
    """锚、标题、围栏、源链。"""
    出=锚行(str(取字段(事件,'name'))+' — '+str(取字段(事件,'mode')))#锚
    出.extend(['#### `'+str(取字段(事件,'name'))+'` — '+str(取字段(事件,'mode')), ''])#标题
    if 取字段(事件,'doc'):#有说明
        出.extend([取字段(事件,'doc'), ''])#说明
    出.extend(['```'+围栏,取字段(事件,'jsDoc') or '',取字段(事件,'signature') or '','```', ''])#围栏
    链接=类型链接行(取字段(事件,'signature') or '',本页,链页)#类型链接
    if 链接:#有
        出.extend([链接, ''])#写入
    源=取字段(事件,'source') or ''#源指针
    出.extend(['Source: [`'+源+'`](../../'+(源.split(':')[0] if ':' in 源 else 源)+')', ''])#源链
    return 出#行

def 渲染服务(服务,本页,链页):#渲染一条服务 Markdown
    """锚、标题、方法围栏、源链。"""
    种=' (abstract seam)' if 取字段(服务,'abstract') else ''#抽象缝
    出=锚行('ctx.'+str(取字段(服务,'key'))+' — '+str(取字段(服务,'type'))+种)#锚
    出.extend(['### `ctx.'+str(取字段(服务,'key'))+'` — `'+str(取字段(服务,'type'))+'`'+种, ''])#标题
    if 取字段(服务,'doc'):#有类级说明
        出.extend([取字段(服务,'doc'), ''])#说明
    方法们=[项 for 项 in (取字段(服务,'methods') or []) if 取字段(项,'kind')!='property']#只留方法
    if len(方法们)>0:#有方法
        声明们=[]#围栏内容
        for 序号,方法 in enumerate(方法们):#逐方法
            if 序号>0:#第二项起
                声明们.append('')#空行
            声明们.append(取字段(方法,'jsDoc') or '')#JSDoc
            声明们.append(取字段(方法,'signature') or '')#签名
        出.extend(['```'+围栏]+声明们+['```', ''])#围栏
        链接=类型链接行('\n'.join(取字段(方法,'signature') or '' for 方法 in 方法们),本页,链页)#类型链接
        if 链接:#有
            出.extend([链接, ''])#写入
    源=取字段(服务,'source') or ''#源指针
    出.extend(['Source: [`'+源+'`](../../'+(源.split(':')[0] if ':' in 源 else 源)+')', ''])#源链
    return 出#行

def 渲染页区域(页,服务们,事件们,策略):#渲染一页生成区
    """标记定界区域文本（对齐上游 renderPageRegion）。"""
    链页=取字段(策略,'linkedTypePages') or {}#类型链接
    行们=[#区域头
        区域开,'','<a id="cordis-surface"></a>','','## Cordis API','',
        'Generated from source by `scripts/gen-cordis-catalog.ts` (verified fresh by `pnpm run verify-cordis-catalog` in doc-sync; regenerate with `pnpm run gen-cordis-catalog`) — this section is byte-identical in both language sides of the page. Signature blocks use a `ts cordis-catalog` fence and keep the original source JSDoc; dispatch modes are defined in the [primer](../cordis-primer.md#dispatch-modes), and the framework-inherited `ctx` API lives in [cordis-api/inherited.md](../cordis-api/inherited.md).',
        '',
    ]#结束
    for 服务 in 服务们:#各服务
        行们.extend(渲染服务(服务,页,链页))#写入
    作用域们=sorted({取字段(事件,'scope') for 事件 in 事件们})#去重排序
    for 作用域 in 作用域们:#逐 scope
        行们.extend(锚行(作用域+'/* events'))#锚
        行们.extend(['### `'+作用域+'/*` events', ''])#标题
        for 事件 in sorted([项 for 项 in 事件们 if 取字段(项,'scope')==作用域],key=lambda 项:取字段(项,'name') or ''):#按名
            行们.extend(渲染事件(事件,页,链页))#写入
    while len(行们)>0 and 行们[-1]=='':#去掉尾部空行
        行们.pop()#弹出
    行们.append(区域闭)#闭标记
    return '\n'.join(行们)#区域文本

renderPageRegion=渲染页区域#上游名

def 渲染继承页(策略):#渲染继承 API 页
    """完整生成的 Markdown（对齐上游 renderInheritedPage）。"""
    门禁='This file is GENERATED from source (`scripts/gen-cordis-catalog.ts`) and verified fresh by `pnpm run verify-cordis-catalog` (part of `doc-sync`) — do not edit it by hand. Signature blocks use a `ts cordis-catalog` fence and include the original source JSDoc immediately before each event or service method. doc-typecheck skips these bare declaration fragments; type names in a signature link to the page that documents them.'#门禁说明
    行们=[#页头
        '<!-- Generated by scripts/gen-cordis-catalog.ts — do not edit by hand.',
        '     Run `pnpm run gen-cordis-catalog` to regenerate. -->',
        '',
        '# Inherited Cordis API',
        '',
        'The framework `ctx` members and events every plugin sees beyond the harness tier — pinned vendor source ([vendoring policy](../../vendor/README.md)), summarized tersely so the harness pages stay focused on repository-owned vocabulary. Detailed Context, Fiber, Registry, and Service APIs are generated in [context.md](context.md), [fiber.md](fiber.md), [registry.md](registry.md), and [service.md](service.md); the event-dispatch methods in [events.md](events.md).',
        '',
        门禁,
        '',
        '## Inherited `ctx` members (cordis core + loader/hmr/timer)',
        '',
    ]#结束
    for 项 in 取字段(策略,'inheritedServices') or []:#逐条
        源=取字段(项,'source') or ''#源
        行们.append('- `'+str(取字段(项,'name'))+'` — '+str(取字段(项,'summary'))+' ([`'+源+'`](../../'+(源.split(':')[0] if ':' in 源 else 源)+'))')#列表项
    行们.extend(['', '## Inherited events (cordis core + loader/hmr/timer)', ''])#事件标题
    for 项 in 取字段(策略,'inheritedEvents') or []:#逐条
        源=取字段(项,'source') or ''#源
        行们.append('- `'+str(取字段(项,'name'))+'` — '+str(取字段(项,'summary'))+' ([`'+源+'`](../../'+(源.split(':')[0] if ':' in 源 else 源)+'))')#列表项
    行们.append('')#文末空行
    return '\n'.join(行们)#完整 Markdown

renderInheritedPage=渲染继承页#上游名

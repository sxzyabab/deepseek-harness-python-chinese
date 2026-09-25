import re#词边界与标签
from .模型 import 子类型节点标识列表#子边
from .渲染器 import 类型图渲染器#类型图渲染器

__all__=[#公开面
    'Cordis目录投影器',
    '投影Cordis目录',
    '收集事件','收集服务',
    '解析JsDoc','渲染运行时Api',
    '渲染页区域','渲染继承页',
    '区域开','区域闭',
    '收集签名类型名',
]#结束

分析器硬缺口='WorkspaceAnalyzer（typert/generator analyzer.ts / TS 编译器 API）未迁；根扫描入口不可空壳装通过。'#硬缺口文案

派发模式=frozenset(['emit','bail','waterfall','parallel','serial'])#五种派发模式
围栏='ts cordis-catalog'#签名围栏语言标记
声明截断=1500#声明截断阈值
区域开='<!-- BEGIN GENERATED cordis-surface (gen-cordis-catalog.ts) — do not edit between markers -->'#开标记
区域闭='<!-- END GENERATED cordis-surface -->'#闭标记

def 属于派发模式(模式):#是否五种派发模式之一
    """收窄。"""
    return 模式 in 派发模式#合法

def 指针(位置):#源位置格式化成 file:line
    """文件:行号。"""
    文件=位置['file'] if 位置 is not None and 'file' in 位置 else None#文件
    行号=位置['line'] if 位置 is not None and 'line' in 位置 else None#行号
    return str(文件)+':'+str(行号)#指针

def 引号(值):#单引号转义
    """反斜杠、引号、换行。"""
    return "'"+str(值).replace('\\','\\\\').replace("'","\\'").replace('\n','\\n')+"'"#字面量

def 引号列表(值列表):#字符串数组字面量
    """逐项 quote。"""
    return '['+', '.join(引号(项) for 项 in 值列表)+']'#数组

def 渲染参数文档(参数表):#参数文档数组
    """{ name, description }。"""
    项列表=['{ name: '+引号(名)+', description: '+引号(描述)+' }' for 名,描述 in 参数表.items()]#项
    return '['+', '.join(项列表)+']'#数组

def 首句(文档):#取说明的第一句
    """到句号/问号/叹号。"""
    行=(文档.split('\n',1)[0] if 文档 else '')#第一行
    命中=re.match(r'^(.*?[.!?])(?:\s|$)',行)#句子
    return ((命中.group(1) if 命中 else 行) or '').strip()#句子或整行

def 检查类型链接(定位,名字列表,策略,违规列表):#按名字检查类型是否已分类
    """追加未分类项。"""
    链页=(策略['linkedTypePages'] if 策略 is not None and 'linkedTypePages' in 策略 else None) or {}#文档页
    基础=(策略['foundationTypeNames'] if 策略 is not None and 'foundationTypeNames' in 策略 else None) or set()#基础类型
    豁免=(策略['typeLinkExemptions'] if 策略 is not None and 'typeLinkExemptions' in 策略 else None) or {}#豁免
    for 名 in 名字列表:#逐个
        if 名 in 链页 or 名 in 基础 or 名 in 豁免:#已分类
            continue#跳过
        违规列表.append(#追加诊断
            定位+" references unclassified type '"+名+"'. Add it to linkedTypePages with its documentation page, "
            +"to foundationTypeNames if TypeScript or the framework owns it, or to typeLinkExemptions with "
            +"the non-catalog documentation owner."
        )#结束

def 报告类型链接违规(门禁,违规列表):#有违规则抛聚合错误
    """聚合全部类型链接违规。"""
    if len(违规列表)==0:#无
        return#静默
    raise Exception(门禁+': '+str(len(违规列表))+' signature type-link coverage violation(s):\n'+'\n'.join('  '+项 for 项 in 违规列表))#抛

def 报告违规(门禁,违规列表):#JSDoc 完整性门禁
    """聚合全部 JSDoc 违规。"""
    if len(违规列表)==0:#无
        return#静默
    raise Exception(门禁+': '+str(len(违规列表))+' JSDoc completeness violation(s) (see AGENTS.md):\n'+'\n'.join('  '+项 for 项 in 违规列表))#抛

def 解析JsDoc(原文):#把原始 JSDoc 拆成散文与标签
    """doc / params / returns / throws / deprecated。"""
    行列表=[]#去围栏后按行
    去头=re.sub(r'^/\*\*', '', 原文 or '')#去掉开头 /**
    去尾=re.sub(r'\*/$', '', 去头)#去掉结尾 */
    for 行 in 去尾.split('\n'):#按行
        行列表.append(re.sub(r'^\s*\*?\s?', '', 行).rstrip())#去引导 * 与行尾空白
    块列表=[]#散文块
    段落=[]#当前段落
    列表=[]#当前列表
    项=[]#当前列表项
    是否进标签=False#是否已进入块标签区

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
            块列表.append('\n'.join(列表))#列表作一块
        列表=[]#清空

    def 冲刷段落():#冲刷段落（含其前列表）
        nonlocal 段落#缓冲
        冲刷列表()#先冲刷列表
        if len(段落)>0:#有段落
            块列表.append(接合(段落))#段落作一块
        段落=[]#清空

    for 行 in 行列表:#第一遍：抽散文
        标签行=行.lstrip()#去行首空白看标签
        if 标签行.startswith('@'):#块标签行
            冲刷段落()#散文到此结束
            是否进标签=True#进入标签区
            continue#标签正文第二遍
        if 是否进标签:#标签区续行留给第二遍
            continue#跳过
        if 行.strip()=='':#空行分段
            冲刷段落()#冲刷
            continue#下一行
        if re.match(r'^-\s+',行):#列表项
            冲刷项()#冲刷上一项
            if len(段落)>0:#列表打断了段落
                块列表.append(接合(段落))#先落下段落
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
    抛错列表=[]#@throws
    已弃用=False#@deprecated
    槽=None#当前标签续行接收器

    for 行 in 行列表:#第二遍：抽块标签
        if re.match(r'^@deprecated(?:\s|$)',行):#弃用
            已弃用=True#记弃用
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
            抛错列表.append(值)#新的一条
            下标=len(抛错列表)-1#该条下标
            def 续抛(文本,下标=下标):#续行
                抛错列表[下标]=(抛错列表[下标]+' '+文本).strip() if 抛错列表[下标] else 文本#追加
            槽=续抛#接收器
            continue#下一行
        if 行.startswith('@') or 行.strip()=='':#其他标签或空行
            槽=None#结束续行
        elif 槽 is not None:#续行
            槽(行.strip())#接到当前标签

    散文='\n\n'.join(块列表)#散文
    散文=re.sub(r'\{@link\s+([^}]+)\}', r'\1', 散文).strip()#展开 {@link}
    return {'doc':散文,'params':参数表,'returns':返回,'throws':抛错列表,'deprecated':已弃用}#解析结果

def 检查参数(定位,api种类,参数列表,标签表,是否豁免,违规列表):#校验 @param 与形参一一对应
    """绑定模式禁止；豁免不要求。"""
    for 参数 in 参数列表:#逐形参
        绑定=参数['binding'] if 参数 is not None and 'binding' in 参数 else None#绑定
        名=参数['name'] if 参数 is not None and 'name' in 参数 else None#形参名
        if 绑定!='identifier':#绑定模式
            违规列表.append(定位+": parameter '"+str(名)+"' is a binding pattern; the "+api种类+" API needs simple identifier parameters so @param can name them.")#禁止解构
            continue#下一项
        if 是否豁免(参数):#豁免
            continue#不要求
        描述=标签表[名] if 名 in 标签表 else None#对应 @param
        if 描述 is None:#缺标签
            违规列表.append(定位+' is missing @param '+str(名)+'.')#缺
        elif 描述.strip()=='':#空描述
            违规列表.append(定位+': @param '+str(名)+' has an empty description.')#空
    for 标签 in 标签表:#逐 @param
        是否对上=False#是否命中形参
        for 参数 in 参数列表:#逐形参
            if (参数['binding'] if 参数 is not None and 'binding' in 参数 else None)=='identifier' and (参数['name'] if 参数 is not None and 'name' in 参数 else None)==标签:#对上
                是否对上=True#命中
                break#停止
        if not 是否对上:#对不上
            违规列表.append(定位+': @param '+标签+' does not match any parameter (stale tag?).')#陈旧

def 检查返回(定位,签名,返回,渲染器,违规列表):#非 void 返回必须有 @returns
    """void / Promise<void> 不要求。"""
    类型=渲染器.renderType(签名['returns'] if 签名 is not None and 'returns' in 签名 else None)#返回类型文本
    if 类型 in ('void','Promise<void>'):#void
        return#不要求
    if 返回 is None:#缺标签
        违规列表.append(定位+' is missing @returns (return type: '+类型+').')#缺
    elif 返回.strip()=='':#空描述
        违规列表.append(定位+': @returns has an empty description.')#空

def 收集签名类型名(渲染器,签名):#收集签名引用的类型名
    """去重排序。"""
    名字=set()#去重
    已访=set()#防环

    def 访问签名(当前):#走访一条签名
        """走访一条签名。"""
        for 参数 in (当前['typeParameters'] if 当前 is not None and 'typeParameters' in 当前 else None) or []:#类型参数
            约束=参数['constraint'] if 参数 is not None and 'constraint' in 参数 else None#约束
            if 约束 is not None:#约束
                访问(约束)#约束
            缺省=参数['default'] if 参数 is not None and 'default' in 参数 else None#默认
            if 缺省 is not None:#默认
                访问(缺省)#默认
        for 参数 in (当前['parameters'] if 当前 is not None and 'parameters' in 当前 else None) or []:#形参
            访问(参数['type'] if 参数 is not None and 'type' in 参数 else None)#形参类型
        访问(当前['returns'] if 当前 is not None and 'returns' in 当前 else None)#返回

    def 访问成员(成员):#走访对象成员
        """走访对象成员。"""
        if (成员['kind'] if 成员 is not None and 'kind' in 成员 else None)=='property':#属性
            访问(成员['type'] if 成员 is not None and 'type' in 成员 else None)#类型
        else:#方法
            访问签名((成员['signature'] if 成员 is not None and 'signature' in 成员 else None) or {})#签名

    def 访问(标识):#走访一个类型节点
        """走访一个类型节点。"""
        if 标识 in 已访:#已走访
            return#跳过
        已访.add(标识)#标记
        节点=渲染器.node(标识)#取出
        种类=节点['kind'] if 节点 is not None and 'kind' in 节点 else None#种类
        目标=节点['target'] if 节点 is not None and 'target' in 节点 else None#目标
        if 种类=='reference' and (目标['kind'] if 目标 is not None and 'kind' in 目标 else None)!='type-parameter':#非类型参数引用
            名字.add(节点['name'] if 节点 is not None and 'name' in 节点 else None)#记下
        if 种类=='type-query':#typeof
            名字.add(节点['expression'] if 节点 is not None and 'expression' in 节点 else None)#表达式名
        for 子 in 子类型节点标识列表(节点):#子节点
            访问(子)#递归
        if 种类=='object':#对象成员
            for 成员 in (节点['members'] if 节点 is not None and 'members' in 节点 else None) or []:#成员
                访问成员(成员)#成员
        if 种类 in ('function','constructor'):#函数/构造
            访问签名((节点['signature'] if 节点 is not None and 'signature' in 节点 else None) or {})#签名

    访问签名(签名)#从根签名开始
    return sorted(名字)#排序

def 引用类型闭包(种子列表,声明表):#从种子签名收集传递引用的类型
    """词边界匹配名字。"""
    已纳={}#名字 → 声明
    前沿=list(种子列表)#本轮种子
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
    def 按名(项):#按 name 字段排序
        """按 name 字段排序。"""
        return 项['name']#名
    return sorted(({'name':名,'declaration':声明} for 名,声明 in 已纳.items()),key=按名)#按名排序

class Cordis目录投影器:#Cordis 目录投影器
    """对一个 Typert 面做仓库特有的 Cordis 校验与投影。"""
    def __init__(自身,面,源声明列表,策略):#保存面、声明与策略
        """按该面类型图构造渲染器。"""
        自身.面=面#面模型
        自身.源声明列表=list(源声明列表 or [])#源声明
        自身.策略=策略#策略
        自身.渲染器=类型图渲染器(面['graph'] if 面 is not None and 'graph' in 面 else None)#渲染器

    def 投影(自身):#校验并投影
        """全部已校验服务与事件。"""
        return {'events':自身.收集事件(),'services':自身.收集服务()}#目录模型

    def 渲染运行时Api(自身,模型):#渲染运行时目录源
        """面向模型的 TypeScript 目录源码。"""
        服务列表=list((模型['services'] if 模型 is not None and 'services' in 模型 else None) or [])+list((自身.策略['runtimeServices'] if 自身.策略 is not None and 'runtimeServices' in 自身.策略 else None) or [])#合并
        排除=(自身.策略['runtimeServiceExclusions'] if 自身.策略 is not None and 'runtimeServiceExclusions' in 自身.策略 else None) or set()#排除键
        可见=[]#过滤后
        for 项 in 服务列表:#过滤
            if (项['key'] if 项 is not None and 'key' in 项 else None) not in 排除:#保留
                可见.append(项)#收下
        def 按键(项):#按服务键排序
            """按服务键排序。"""
            return (项['key'] if 项 is not None and 'key' in 项 else None) or ''#键
        可见.sort(key=按键)#按键排序
        事件列表=(模型['events'] if 模型 is not None and 'events' in 模型 else None) or []#事件
        return 渲染运行时Api(#交给文本渲染
            可见,#可见服务
            事件列表,#事件
            自身.运行时类型(可见,事件列表),#类型闭包
            (自身.策略['inheritedServices'] if 自身.策略 is not None and 'inheritedServices' in 自身.策略 else None) or [],#继承 ctx
        )#结束

    def 收集事件(自身):#收集并校验全部事件
        """通过校验的事件。"""
        条目表=[]#通过
        违规列表=[]#JSDoc
        类型违规=[]#类型链接
        for 包 in (自身.面['packages'] if 自身.面 is not None and 'packages' in 自身.面 else None) or []:#逐包
            for 事件 in (包['events'] if 包 is not None and 'events' in 包 else None) or []:#逐事件
                解析=解析JsDoc((事件['jsDoc'] if 事件 is not None and 'jsDoc' in 事件 else None) or '')#解析 JSDoc
                if 解析['deprecated']:#已弃用
                    continue#跳过
                源=指针(事件['location'] if 事件 is not None and 'location' in 事件 else None)#源指针
                事件名=事件['name'] if 事件 is not None and 'name' in 事件 else None#事件名
                定位="event '"+str(事件名)+"' ("+源+')'#诊断定位
                节点=自身.渲染器.node(事件['signature'] if 事件 is not None and 'signature' in 事件 else None)#签名节点
                if (节点['kind'] if 节点 is not None and 'kind' in 节点 else None)!='function':#不可调用
                    违规列表.append(定位+' is not represented by a callable type.')#违规
                    continue#跳过
                签名=节点['signature'] if 节点 is not None and 'signature' in 节点 else None#签名
                if (自身.面['face'] if 自身.面 is not None and 'face' in 自身.面 else None)=='host':#宿主面才查类型链接
                    检查类型链接(定位,收集签名类型名(自身.渲染器,签名),自身.策略,类型违规)#检查
                模式=事件['mode'] if 事件 is not None and 'mode' in 事件 else None#@mode
                if not 属于派发模式(模式):#缺合法 @mode
                    违规列表.append(定位+" is missing an @mode tag. Add '@mode emit|bail|waterfall|parallel|serial' to its JSDoc (see AGENTS.md).")#缺
                参数列表=(签名['parameters'] if 签名 is not None and 'parameters' in 签名 else None) or []#形参
                末=参数列表[-1] if len(参数列表)>0 else None#末形参
                是否带next=(末['name'] if 末 is not None and 'name' in 末 else None)=='next' if 末 is not None else False#末参是否 next
                if 属于派发模式(模式) and 是否带next and 模式!='waterfall':#结构是 waterfall 但标签不是
                    违规列表.append(定位+" has a trailing 'next' parameter (structurally a waterfall) but is tagged '@mode "+模式+"'. Fix the tag or the signature.")#不符
                if 属于派发模式(模式) and not 是否带next and 模式=='waterfall':#标签 waterfall 但无 next
                    违规列表.append(定位+" is tagged '@mode waterfall' but has no trailing 'next' parameter. A waterfall delegates via next().")#缺 next
                if 解析['doc']=='':#无说明
                    违规列表.append(定位+' has no description prose. Say what happened / what a listener may do, above the block tags.')#缺描述
                def 事件参数豁免(参数,末形参=末,带next=是否带next):#接收者或 waterfall 的 next 不要求 @param
                    """接收者或 waterfall 的 next 不要求 @param。"""
                    接收者=参数['receiver'] if 参数 is not None and 'receiver' in 参数 else None#接收者
                    return 接收者 or (带next and 参数 is 末形参)#豁免
                检查参数(#校验 @param
                    定位,'event',参数列表,解析['params'],
                    事件参数豁免,
                    违规列表,
                )#结束
                if 属于派发模式(模式):#模式合法才收录
                    名=事件名 or ''#事件名
                    条目表.append({#一条事件
                        'name':名,#作用域名
                        'scope':名.split('/')[0] if '/' in 名 else 名,#首段
                        'signature':事件['text'] if 事件 is not None and 'text' in 事件 else None,#签名文本
                        'jsDoc':(事件['jsDoc'] if 事件 is not None and 'jsDoc' in 事件 else None) or '',#原始 JSDoc
                        'mode':模式,#派发模式
                        'doc':解析['doc'],#说明散文
                        'source':源,#源指针
                    })#结束
        报告违规('gen-cordis-catalog',违规列表)#JSDoc
        报告类型链接违规('gen-cordis-catalog',类型违规)#类型链接
        return 条目表#已校验事件

    def 选出可渲染服务(自身):#选出可渲染的 ctx 服务
        """类胜出；声明须落在包 src 下。"""
        已选={}#键 → 胜出
        for 包 in (自身.面['packages'] if 自身.面 is not None and 'packages' in 自身.面 else None) or []:#逐包
            for 服务 in (包['services'] if 包 is not None and 'services' in 包 else None) or []:#逐服务
                声明=自身.渲染器.declaration(服务['symbol'] if 服务 is not None and 'symbol' in 服务 else None)#声明
                位置=服务['location'] if 服务 is not None and 'location' in 服务 else None#位置
                文件=(位置['file'] if 位置 is not None and 'file' in 位置 else None) or ''#文件
                主=re.match(r'^(packages/[^/]+/[^/]+/src/)',文件)#包 src 前缀
                if 主 is None:#不在包 src
                    continue#跳过
                所有者=主.group(1)#前缀
                if (声明['kind'] if 声明 is not None and 'kind' in 声明 else None) not in ('class','interface'):#必须类或接口
                    continue#跳过
                if (自身.面['face'] if 自身.面 is not None and 'face' in 自身.面 else None)=='host':#宿主面
                    if not re.match(r'^packages/[^/]+/[^/]+/src/[^/]+\.ts$',文件):#宿主：一层 .ts
                        continue#跳过
                else:#客户端面
                    if not re.match(r'^packages/[^/]+/[^/]+/src/client/.+\.tsx?$',文件):#client 下
                        continue#跳过
                声明位置=声明['location'] if 声明 is not None and 'location' in 声明 else None#声明位置
                声明文件=(声明位置['file'] if 声明位置 is not None and 'file' in 声明位置 else None) or ''#声明文件
                if not 声明文件.startswith(所有者):#声明须同包
                    continue#跳过
                键=服务['key'] if 服务 is not None and 'key' in 服务 else None#服务键
                当前=已选[键] if 键 in 已选 else None#已选同键
                if 当前 is not None:#已有同键
                    当前声明=自身.渲染器.declaration(当前['symbol'] if 当前 is not None and 'symbol' in 当前 else None)#已有声明
                    if (当前声明['kind'] if 当前声明 is not None and 'kind' in 当前声明 else None)=='class':#已有类
                        continue#保住
                已选[键]=服务#写入或覆盖
        return list(已选.values())#胜出

    def 收集服务(自身):#收集并校验全部服务
        """按键排序。"""
        条目表=[]#通过
        违规列表=[]#JSDoc
        类型违规=[]#类型链接
        for 服务 in 自身.选出可渲染服务():#逐条
            声明=自身.渲染器.declaration(服务['symbol'] if 服务 is not None and 'symbol' in 服务 else None)#声明
            解析声明=解析JsDoc((声明['jsDoc'] if 声明 is not None and 'jsDoc' in 声明 else None) or '')#类级 JSDoc
            if 解析声明['deprecated']:#已弃用
                continue#跳过
            文档=解析声明['doc']#类级说明
            源=指针(声明['location'] if 声明 is not None and 'location' in 声明 else None)#源指针
            服务键=服务['key'] if 服务 is not None and 'key' in 服务 else None#服务键
            if 文档=='':#无 JSDoc
                违规列表.append('service ctx.'+str(服务键)+' ('+源+'): '+str(声明['kind'] if 声明 is not None and 'kind' in 声明 else None)+' '+str(声明['name'] if 声明 is not None and 'name' in 声明 else None)+' has no JSDoc.')#缺
            方法表=[]#公开成员
            for 成员标识 in (服务['members'] if 服务 is not None and 'members' in 服务 else None) or []:#逐成员
                成员=自身.渲染器.member(成员标识)#成员
                成员名=成员['name'] if 成员 is not None and 'name' in 成员 else None#成员名
                if str(成员名 or '').startswith('['):#索引签名
                    continue#跳过
                解析=解析JsDoc((成员['jsDoc'] if 成员 is not None and 'jsDoc' in 成员 else None) or '')#成员 JSDoc
                if 解析['deprecated']:#已弃用
                    continue#跳过
                成员种类=成员['kind'] if 成员 is not None and 'kind' in 成员 else None#种类
                if 成员种类=='property':#属性
                    if (成员['jsDoc'] if 成员 is not None and 'jsDoc' in 成员 else None) is None:#无 JSDoc
                        continue#不收录
                    方法表.append({'kind':'property','signature':成员['text'] if 成员 is not None and 'text' in 成员 else None,'jsDoc':成员['jsDoc'] if 成员 is not None and 'jsDoc' in 成员 else None})#收录
                    continue#属性不跑方法校验
                if 成员种类!='method':#非方法
                    continue#跳过
                定位='service method ctx.'+str(服务键)+'.'+str(成员名)+' ('+指针(成员['location'] if 成员 is not None and 'location' in 成员 else None)+')'#定位
                成员签名=成员['signature'] if 成员 is not None and 'signature' in 成员 else None#签名
                if (自身.面['face'] if 自身.面 is not None and 'face' in 自身.面 else None)=='host':#宿主面
                    检查类型链接(定位,收集签名类型名(自身.渲染器,成员签名),自身.策略,类型违规)#检查
                方法表.append({'kind':'method','signature':成员['text'] if 成员 is not None and 'text' in 成员 else None,'jsDoc':(成员['jsDoc'] if 成员 is not None and 'jsDoc' in 成员 else None) or ''})#先收录
                if (成员['jsDoc'] if 成员 is not None and 'jsDoc' in 成员 else None) is None:#缺 JSDoc
                    违规列表.append(定位+' has no JSDoc.')#缺
                    continue#不再查
                if 解析['doc']=='':#缺说明
                    违规列表.append(定位+' has no description prose above its block tags.')#缺
                def 服务参数豁免(参数):#接收者不要求 @param
                    """接收者不要求 @param。"""
                    return 参数['receiver'] if 参数 is not None and 'receiver' in 参数 else None#接收者
                检查参数(定位,'service',(成员签名['parameters'] if 成员签名 is not None and 'parameters' in 成员签名 else None) or [],解析['params'],服务参数豁免,违规列表)#@param
                检查返回(定位,成员签名,解析['returns'],自身.渲染器,违规列表)#@returns
            条目表.append({#一条服务
                'key':服务键,#ctx 键
                'type':声明['name'] if 声明 is not None and 'name' in 声明 else None,#类/接口名
                'abstract':声明['abstract'] if 声明 is not None and 'abstract' in 声明 else None,#是否抽象
                'doc':文档,#类级说明
                'methods':方法表,#公开方法
                'source':源,#源指针
            })#结束
        报告违规('gen-cordis-catalog',违规列表)#JSDoc
        报告类型链接违规('gen-cordis-catalog',类型违规)#类型链接
        def 按键(项):#按服务键排序
            """按服务键排序。"""
            return (项['key'] if 项 is not None and 'key' in 项 else None) or ''#键
        条目表.sort(key=按键)#按键排序
        return 条目表#服务

    def 运行时类型(自身,服务列表,事件列表):#收集签名引用的类型声明
        """名字与声明文本。"""
        声明表={}#名字 → 声明文本
        歧义=set()#跨文件重名
        面名=自身.面['face'] if 自身.面 is not None and 'face' in 自身.面 else None#本面
        截断=(自身.策略['runtimeDeclarationMaxChars'] if 自身.策略 is not None and 'runtimeDeclarationMaxChars' in 自身.策略 else None)#策略截断
        if 截断 is None:#未配置
            截断=声明截断#默认 1500
        for 声明 in 自身.源声明列表:#逐条源声明
            if (声明['face'] if 声明 is not None and 'face' in 声明 else None)!=面名:#面不符
                continue#跳过
            位置=声明['location'] if 声明 is not None and 'location' in 声明 else None#位置
            文件=(位置['file'] if 位置 is not None and 'file' in 位置 else None) or ''#文件
            种类=声明['kind'] if 声明 is not None and 'kind' in 声明 else None#种类
            在包源=re.match(r'^packages/[^/]+/[^/]+/src/.+\.tsx?$',文件) is not None#包 src
            在厂商枚举=种类=='enum' and re.match(r'^vendor/[^/]+/src/.+\.ts$',文件) is not None#vendor 枚举
            if (not 在包源) and (not 在厂商枚举):#都不收
                continue#跳过
            名=声明['name'] if 声明 is not None and 'name' in 声明 else None#类型名
            if 名 in 声明表:#同名已出现
                歧义.add(名)#歧义
                continue#不覆盖
            文本=(声明['text'] if 声明 is not None and 'text' in 声明 else None) or ''#声明文本
            if len(文本)>截断:#超长
                文本=文本[:截断]+' /* …truncated — full shape in source */'#截断桩
            声明表[名]=文本#写入
        for 名 in 歧义:#去掉歧义
            if 名 in 声明表:#仍在表中
                del 声明表[名]#删除
        种子=[]#种子签名
        for 服务 in 服务列表:#服务方法
            for 方法 in (服务['methods'] if 服务 is not None and 'methods' in 服务 else None) or []:#方法
                种子.append((方法['signature'] if 方法 is not None and 'signature' in 方法 else None) or '')#签名
        for 事件 in 事件列表:#事件
            种子.append((事件['signature'] if 事件 is not None and 'signature' in 事件 else None) or '')#签名
        return 引用类型闭包(种子,声明表)#闭包

def 投影Cordis目录(扫描根,策略,目标面='host'):#分析一次工作区并投影
    """投影 Cordis 目录。必须 WorkspaceAnalyzer。"""
    raise NotImplementedError('投影Cordis目录: '+分析器硬缺口)#硬缺口

def 收集事件(扫描根,策略):#收集全部已建模事件
    """收集全部已建模事件；委托投影Cordis目录。"""
    raise NotImplementedError('收集事件: '+分析器硬缺口)#硬缺口

def 收集服务(扫描根,策略):#收集全部已建模服务
    """收集全部已建模服务；委托投影Cordis目录。"""
    raise NotImplementedError('收集服务: '+分析器硬缺口)#硬缺口

def 渲染运行时Api(服务列表,事件列表,类型列表,继承服务列表):#生成 tool-cordis 消费的目录源
    """生成 tool-cordis 消费的目录源：常量表 + 查询辅助（不依赖分析器）。"""
    行列表=[#表头
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
    for 服务 in 服务列表:#逐服务
        文档=(服务['doc'] if 服务 is not None and 'doc' in 服务 else None) or ''#文档
        行列表.append('  {')#对象起
        行列表.append('    key: '+引号(服务['key'] if 服务 is not None and 'key' in 服务 else None)+',')#键
        行列表.append('    summary: '+引号(首句(文档))+',')#摘要
        行列表.append('    description: '+引号(文档)+',')#完整描述
        方法表=(服务['methods'] if 服务 is not None and 'methods' in 服务 else None) or []#方法
        if len(方法表)==0:#无方法
            行列表.append('    methods: [],')#空
        else:#有方法
            行列表.append('    methods: [')#起
            for 方法 in 方法表:#逐方法
                约定=解析JsDoc((方法['jsDoc'] if 方法 is not None and 'jsDoc' in 方法 else None) or '')#解析
                行列表.append('      {')#起
                行列表.append('        signature: '+引号((方法['signature'] if 方法 is not None and 'signature' in 方法 else None) or '')+',')#签名
                行列表.append('        description: '+引号(约定['doc'])+',')#描述
                行列表.append('        parameters: '+渲染参数文档(约定['params'])+',')#参数
                if 约定['returns'] is not None:#有 @returns
                    行列表.append('        returns: '+引号(约定['returns'])+',')#返回
                if len(约定['throws'])>0:#有 @throws
                    行列表.append('        throws: '+引号列表(约定['throws'])+',')#抛错
                行列表.append('      },')#止
            行列表.append('    ],')#方法止
        行列表.append('  },')#服务止
    行列表.extend([#事件表头
        ']',
        '',
        '/** Every harness event, sorted by name. */',
        'export const EVENT_API: readonly EventApiEntry[] = [',
    ])#结束
    def 按事件名(项):#按事件名排序
        """按事件名排序。"""
        return (项['name'] if 项 is not None and 'name' in 项 else None) or ''#名
    for 事件 in sorted(事件列表,key=按事件名):#按名
        约定=解析JsDoc((事件['jsDoc'] if 事件 is not None and 'jsDoc' in 事件 else None) or '')#解析
        文档=(事件['doc'] if 事件 is not None and 'doc' in 事件 else None) or ''#文档
        行列表.append('  {')#起
        行列表.append('    name: '+引号(事件['name'] if 事件 is not None and 'name' in 事件 else None)+',')#名
        行列表.append('    mode: '+引号(事件['mode'] if 事件 is not None and 'mode' in 事件 else None)+',')#模式
        行列表.append('    signature: '+引号((事件['signature'] if 事件 is not None and 'signature' in 事件 else None) or '')+',')#签名
        行列表.append('    summary: '+引号(首句(文档))+',')#摘要
        行列表.append('    description: '+引号(文档)+',')#描述
        行列表.append('    parameters: '+渲染参数文档(约定['params'])+',')#参数
        行列表.append('  },')#止
    行列表.extend([#类型表头
        ']',
        '',
        '/** Shapes of every exported type the Service and Event signatures reference (transitively), sorted by name. */',
        'export const TYPE_API: readonly TypeApiEntry[] = [',
    ])#结束
    for 类型 in 类型列表:#逐类型
        行列表.append('  {')#起
        行列表.append('    name: '+引号(类型['name'] if 类型 is not None and 'name' in 类型 else None)+',')#名
        行列表.append('    declaration: '+引号(类型['declaration'] if 类型 is not None and 'declaration' in 类型 else None)+',')#声明
        行列表.append('  },')#止
    行列表.extend([#继承表头
        ']',
        '',
        '/** The inherited `ctx` API (cordis core + loader/hmr/timer), in curated order. */',
        'export const INHERITED_CTX_API: readonly InheritedApiEntry[] = [',
    ])#结束
    for 项 in 继承服务列表:#逐条
        行列表.append('  { name: '+引号(项['name'] if 项 is not None and 'name' in 项 else None)+', summary: '+引号(项['summary'] if 项 is not None and 'summary' in 项 else None)+' },')#条目
    行列表.extend([#查询辅助与导出函数
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
    return '\n'.join(行列表)#完整源

def 生成Github锚(标题):#GitHub 标题 slug
    """小写；只留字母数字空格连字符；空格变连字符（Unicode 字母数字）。"""
    小写=标题.lower()#小写
    保留=''.join(字符 for 字符 in 小写 if 字符.isalnum() or 字符 in ' -')#字母数字空格连字符
    return 保留.replace(' ','-')#空格变连字符

def 锚行(标题文本):#显式 <a id> 与空行
    """锚 + 空行。"""
    return ['<a id="'+生成Github锚(标题文本)+'"></a>', '']#锚

def 类型链接行(签名,本页,链页):#签名类型交叉链接行
    """Types: 行；无则空串。"""
    见到=set()#出现过的类型名
    for 名 in (链页 or {}):#逐个可链接
        if re.search(r'\b'+re.escape(名)+r'\b',签名 or ''):#词边界命中
            见到.add(名)#记下
    链接列表=['['+名+']('+链页[名]+')' for 名 in sorted(见到) if (链页[名] if 名 in 链页 else None)!=本页]#丢掉当前页
    return '' if len(链接列表)==0 else 'Types: '+' · '.join(链接列表)#Types 行

def 源链(源):#渲染 file:line 为仅文件链接
    """展示与链接都只用文件路径。"""
    文件=(源.split(':')[0] if 源 else '')#去掉行号
    return '[`'+文件+'`](../../'+文件+')'#文件链

def 渲染事件(事件,本页,链页):#渲染一条事件 Markdown
    """锚、标题、围栏、源链。"""
    名=事件['name'] if 事件 is not None and 'name' in 事件 else None#事件名
    模式=事件['mode'] if 事件 is not None and 'mode' in 事件 else None#模式
    出=锚行(str(名)+' — '+str(模式))#锚
    出.extend(['#### `'+str(名)+'` — '+str(模式), ''])#标题
    文档=事件['doc'] if 事件 is not None and 'doc' in 事件 else None#说明
    if 文档:#有说明
        出.extend([文档, ''])#说明
    出.extend(['```'+围栏,(事件['jsDoc'] if 事件 is not None and 'jsDoc' in 事件 else None) or '',(事件['signature'] if 事件 is not None and 'signature' in 事件 else None) or '','```', ''])#围栏
    链接=类型链接行((事件['signature'] if 事件 is not None and 'signature' in 事件 else None) or '',本页,链页)#类型链接
    if 链接:#有
        出.extend([链接, ''])#写入
    源=(事件['source'] if 事件 is not None and 'source' in 事件 else None) or ''#源指针
    出.extend(['Source: '+源链(源), ''])#源链
    return 出#行

def 渲染服务(服务,本页,链页):#渲染一条服务 Markdown
    """锚、标题、方法围栏、源链。"""
    键=服务['key'] if 服务 is not None and 'key' in 服务 else None#键
    类型=服务['type'] if 服务 is not None and 'type' in 服务 else None#类型
    种=' (abstract seam)' if (服务['abstract'] if 服务 is not None and 'abstract' in 服务 else None) else ''#抽象缝
    出=锚行('ctx.'+str(键)+' — '+str(类型)+种)#锚
    出.extend(['### `ctx.'+str(键)+'` — `'+str(类型)+'`'+种, ''])#标题
    文档=服务['doc'] if 服务 is not None and 'doc' in 服务 else None#类级说明
    if 文档:#有类级说明
        出.extend([文档, ''])#说明
    方法表=[]#只留方法
    for 项 in (服务['methods'] if 服务 is not None and 'methods' in 服务 else None) or []:#逐成员
        if (项['kind'] if 项 is not None and 'kind' in 项 else None)!='property':#方法
            方法表.append(项)#收下
    if len(方法表)>0:#有方法
        声明列表=[]#围栏内容
        for 序号,方法 in enumerate(方法表):#逐方法
            if 序号>0:#第二项起
                声明列表.append('')#空行
            声明列表.append((方法['jsDoc'] if 方法 is not None and 'jsDoc' in 方法 else None) or '')#JSDoc
            声明列表.append((方法['signature'] if 方法 is not None and 'signature' in 方法 else None) or '')#签名
        出.extend(['```'+围栏]+声明列表+['```', ''])#围栏
        签名文本列表=[]#签名
        for 方法 in 方法表:#逐方法
            签名文本列表.append((方法['signature'] if 方法 is not None and 'signature' in 方法 else None) or '')#签名
        链接=类型链接行('\n'.join(签名文本列表),本页,链页)#类型链接
        if 链接:#有
            出.extend([链接, ''])#写入
    源=(服务['source'] if 服务 is not None and 'source' in 服务 else None) or ''#源指针
    出.extend(['Source: '+源链(源), ''])#源链
    return 出#行

def 渲染页区域(页,服务列表,事件列表,策略):#渲染一页生成区
    """标记定界区域文本。"""
    链页=(策略['linkedTypePages'] if 策略 is not None and 'linkedTypePages' in 策略 else None) or {}#类型链接
    行列表=[#区域头
        区域开,'','<a id="cordis-surface"></a>','','## Cordis API','',
        'Generated from source by `scripts/gen-cordis-catalog.ts` (verified fresh by `pnpm run verify-cordis-catalog` in doc-sync; regenerate with `pnpm run gen-cordis-catalog`) — the language sides differ only in locale-specific paired document paths. Signature blocks use a `ts cordis-catalog` fence and keep the original source JSDoc; dispatch modes are defined in the [primer](../cordis-primer.md#dispatch-modes), and the framework-inherited `ctx` API lives in [cordis-api/inherited.md](../cordis-api/inherited.md).',
        '',
    ]#结束
    for 服务 in 服务列表:#各服务
        行列表.extend(渲染服务(服务,页,链页))#写入
    作用域集=set()#去重
    for 事件 in 事件列表:#收集 scope
        作用域集.add(事件['scope'] if 事件 is not None and 'scope' in 事件 else None)#记下
    作用域列表=sorted(作用域集)#排序
    def 按事件名(项):#按事件名排序
        """按事件名排序。"""
        return (项['name'] if 项 is not None and 'name' in 项 else None) or ''#名
    for 作用域 in 作用域列表:#逐 scope
        行列表.extend(锚行(作用域+'/* events'))#锚
        行列表.extend(['### `'+作用域+'/*` events', ''])#标题
        本组=[]#该作用域事件
        for 项 in 事件列表:#筛选
            if (项['scope'] if 项 is not None and 'scope' in 项 else None)==作用域:#命中
                本组.append(项)#收下
        for 事件 in sorted(本组,key=按事件名):#按名
            行列表.extend(渲染事件(事件,页,链页))#写入
    while len(行列表)>0 and 行列表[-1]=='':#去掉尾部空行
        行列表.pop()#弹出
    行列表.append(区域闭)#闭标记
    return '\n'.join(行列表)#区域文本

def 渲染继承页(策略):#渲染继承 API 页
    """完整生成的 Markdown。"""
    门禁='This file is GENERATED from source (`scripts/gen-cordis-catalog.ts`) and verified fresh by `pnpm run verify-cordis-catalog` (part of `doc-sync`) — do not edit it by hand. Signature blocks use a `ts cordis-catalog` fence and include the original source JSDoc immediately before each event or service method. doc-typecheck skips these bare declaration fragments; type names in a signature link to the page that documents them.'#门禁说明
    行列表=[#页头
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
    for 项 in (策略['inheritedServices'] if 策略 is not None and 'inheritedServices' in 策略 else None) or []:#逐条
        源=(项['source'] if 项 is not None and 'source' in 项 else None) or ''#源
        行列表.append('- `'+str(项['name'] if 项 is not None and 'name' in 项 else None)+'` — '+str(项['summary'] if 项 is not None and 'summary' in 项 else None)+' ([`'+源+'`](../../'+(源.split(':')[0] if ':' in 源 else 源)+'))')#列表项
    行列表.extend(['', '## Inherited events (cordis core + loader/hmr/timer)', ''])#事件标题
    for 项 in (策略['inheritedEvents'] if 策略 is not None and 'inheritedEvents' in 策略 else None) or []:#逐条
        源=(项['source'] if 项 is not None and 'source' in 项 else None) or ''#源
        行列表.append('- `'+str(项['name'] if 项 is not None and 'name' in 项 else None)+'` — '+str(项['summary'] if 项 is not None and 'summary' in 项 else None)+' ([`'+源+'`](../../'+(源.split(':')[0] if ':' in 源 else 源)+'))')#列表项
    行列表.append('')#文末空行
    return '\n'.join(行列表)#完整 Markdown

"""`cordis_runtime_inspect` / 文本报告各节渲染。

对齐上游 `拓展/tool-cordis/src/inspect.ts` 中 describe* 全节。公开面仅中文名。
"""
import re#链接语法
from .光纤状态 import 光纤状态,状态标签#状态镜像
from .接口目录 import 服务目录,事件目录,类型目录,继承上下文目录#生成目录
from .巡检 import 现场实现,是否在光纤子树内,已提供服务,缺失服务,取字段#现场查询

__all__=[#公开面
    '描述服务','描述插件','描述工具','描述动态','描述接口','描述事件',
    '现场服务们','缺席服务',
]#结束

def 散文摘要(摘要):#去掉 {@link …}
    """JSDoc 链接改成裸符号名。"""
    return re.sub(r'\{@link\s+([^}]+)\}',r'\1',摘要)#保留链接内名

def 现场服务们(上下文,目录=None):#拼接现场与目录
    """本进程提供的每个服务，与生成目录拼接。"""
    if 目录 is None:#缺省
        目录=服务目录#模块目录
    编目={条目['key']:条目 for 条目 in 目录}#按键索引
    行们=[]#报告行
    for 实现 in 现场实现(上下文):#每条现场
        条目=编目.get(实现['name'])#目录条目
        光纤=实现['fiber']#所属 Fiber
        状态值=取字段(光纤,'state')#数值状态
        行们.append({#组装
            'name':实现['name'],#键
            'owner':取字段(光纤,'name') or '',#Fiber 名
            'state':状态标签.get(状态值,'unknown') if 状态值 is not None else 'unknown',#标签
            'summary':'' if 条目 is None else 散文摘要(条目['summary']),#摘要
            'catalogued':条目 is not None,#是否编目
            'methods':[] if 条目 is None else [方法['signature'] for 方法 in 条目['methods']],#签名
        })#行
    行们.sort(key=lambda 行:行['name'])#按名排序
    return 行们#列表

def 缺席服务(上下文,目录=None):#目录有、现场无
    """已编目但无现场提供方的服务键。"""
    if 目录 is None:#缺省
        目录=服务目录#模块目录
    现场=set(实现['name'] for 实现 in 现场实现(上下文))#现场键
    return sorted([条目['key'] for 条目 in 目录 if 条目['key'] not in 现场])#缺席

def 描述服务(上下文,目录=None):#services 节
    """每个现场 ctx 服务及其所属 Fiber。"""
    if 目录 is None:#缺省
        目录=服务目录#模块目录
    现场=现场服务们(上下文,目录)#拼接
    if len(现场)==0:#无服务
        return ['(no services provided)']#占位
    活跃标签=状态标签[光纤状态['ACTIVE']]#active
    行们=[]#输出
    for 服务 in 现场:#每条
        状态='' if 服务['state']==活跃标签 else ', '+服务['state']#非活跃才写
        摘要='' if 服务['summary']=='' else ' — '+服务['summary']#有摘要才接
        行们.append('- '+服务['name']+' (provided by '+服务['owner']+状态+')'+摘要)#一行
    return 行们#各行

def 描述插件(上下文):#plugins 节
    """注册表知道的每条 Fiber。"""
    光纤们=[]#收集
    注册表=取字段(上下文,'registry')#插件注册表
    if 注册表 is None:#无表
        return []#空
    值们=注册表.values() if hasattr(注册表,'values') else []#运行时们
    for 运行时 in 值们:#每个插件运行时
        for 光纤 in 取字段(运行时,'fibers') or []:#各 Fiber
            光纤们.append(光纤)#收入
    光纤们.sort(key=lambda 光纤:取字段(光纤,'name') or '')#按名
    return ['- '+(取字段(光纤,'name') or '')+' ['+状态标签.get(取字段(光纤,'state'),'unknown')+']' for 光纤 in 光纤们]#行

def 描述工具(上下文,作用域=None):#tools 节
    """调用方可见的工具名。"""
    工具=取字段(上下文,'tools')#工具服务
    if 工具 is None:#无
        return []#空
    模式们=工具.schemas(作用域) if hasattr(工具,'schemas') else []#可见模式
    return ['- '+取字段(模式,'name') for 模式 in 模式们]#名行

def 描述动态(上下文,智能体=None):#temporary 节
    """本会话动态包。"""
    if 智能体 is None:#无 Agent
        行们=[]#空
    else:#有
        运行器=取字段(上下文,'dynamicCordisRunner')#动态运行器
        行们=运行器.快照(智能体) if 运行器 is not None and hasattr(运行器,'快照') else []#快照
    if len(行们)==0:#无定义
        return ["No dynamic Plugins are defined in this session. Definitions live only in this process's memory, so a DSH restart clears them."]#占位
    输出=[]#多行
    for 行 in 行们:#每个插件
        当前=行.get('currentPackageId')#当前
        下一=行.get('nextPackageId')#下一
        活动=行.get('activeRun')#活动
        头='- Plugin '+str(行['pluginId'])+'; current: '+(str(当前) if 当前 is not None else 'none')+'; next: '+(str(下一) if 下一 is not None else 'none')#头
        if 活动 is None:#已停
            头+='; stopped'#停
        else:#活动
            头+='; active: '+str(活动['packageId'])+' as '+str(活动['pluginRunId'])#活动
        输出.append(头)#插件头
        for 包 in 行.get('packages') or []:#每个包
            半们=[]#半边
            if 包.get('hasHostHalf'):#宿主
                半们.append('host')#host
            if 包.get('hasClientHalf'):#客户端
                半们.append('client')#client
            半='+'.join(半们)#拼接
            活动包=活动 if 活动 is not None and 活动.get('packageId')==包.get('packageId') else None#是否在跑
            if 活动包 is None:#未激活
                输出.append('    - '+str(包['packageId'])+': '+包['name']+' ('+半+') — '+包['purpose'])#元数据
                continue#下一包
            光纤=活动包.get('fiber')#Fiber
            if 光纤 is None:#无 Fiber
                状态='running'#写成 running
            elif 取字段(光纤,'state')==光纤状态['ACTIVE']:#已激活
                状态='running'#running
            else:#其它
                状态=状态标签.get(取字段(光纤,'state'),'unknown')#标签
            提供=[] if 光纤 is None else 已提供服务(上下文,光纤)#provides
            等待=[] if 光纤 is None else 缺失服务(上下文,光纤)#waiting
            失败=活动包.get('renderFailure')#渲染失败
            渲染=''#附加
            if 失败 is not None:#有失败
                渲染='; CLIENT RENDER FAILED at '+str(失败.get('slot'))+': '+str(失败.get('message'))#消息
                if 失败.get('abdicated'):#已摘入口
                    渲染+=' (entry removed)'#标注
            宿主方法=活动包.get('handlers') or []#宿主方法
            方法段='' if len(宿主方法)==0 else '; host methods: '+', '.join(宿主方法)#方法
            输出.append(#包行
                '    - '+str(包['packageId'])+': '+包['name']+' ['+状态+', '+str(活动包['pluginRunId'])+'] ('+半+') — '+包['purpose']
                +'; provides: '+(', '.join(提供) if 提供 else 'none')+'; waiting for: '+(', '.join(等待) if 等待 else 'none')
                +方法段+渲染
            )#拼完
    return 输出#各行

def 类型闭包(种子们,类型们=None):#引用类型闭包（按名排序）
    """传递闭包后按类型名排序。"""
    if 类型们 is None:#缺省
        类型们=类型目录#模块
    已收={}#名→条目
    前沿=list(种子们)#本轮
    while len(前沿)>0:#还有
        下一轮=[]#下一轮
        for 条目 in 类型们:#每个类型
            if 条目['name'] in 已收:#已收
                continue#跳过
            模式=re.compile(r'\b'+re.escape(条目['name'])+r'\b')#词边界
            if any(模式.search(文本) for 文本 in 前沿):#命中
                已收[条目['name']]=条目#收入
                下一轮.append(条目['declaration'])#声明
        前沿=下一轮#换轮
    return sorted(已收.values(),key=lambda 条目:条目['name'])#按名

def 服务行们(服务,契约们):#一条服务的报告行
    """标题 + 方法契约 + 签名。"""
    行们=['- '+服务['name']+' — '+服务['summary']]#标题
    for 签名 in 服务['methods']:#每个签名
        契约=None#查找
        for 候选 in 契约们:#精确名时的契约
            if 候选['signature']==签名:#命中
                契约=候选#记下
                break#结束
        if 契约 is not None:#有契约
            行们.append('    '+契约['description'])#说明
            for 参数 in 契约.get('parameters') or []:#参数
                行们.append('    @param '+参数['name']+' — '+参数['description'])#@param
            if 契约.get('returns') is not None:#返回
                行们.append('    @returns '+契约['returns'])#@returns
            for 失败 in 契约.get('throws') or []:#抛错
                行们.append('    @throws '+失败)#@throws
        行们.append('    '+签名)#签名
    return 行们#各行

def 描述接口(上下文,目录=None,名=None,继承=None,类型们=None):#api 节
    """对照现场运行时渲染生成目录。"""
    if 目录 is None:#缺省
        目录=服务目录#服务
    if 继承 is None:#缺省
        继承=继承上下文目录#继承
    if 类型们 is None:#缺省
        类型们=类型目录#类型
    现场=现场服务们(上下文,目录)#现场
    按键={条目['key']:条目 for 条目 in 目录}#索引
    行们=[]#输出
    选中=[服务 for 服务 in 现场 if 服务['catalogued']]#默认已编目
    契约们=[]#精确名契约
    if 名 is not None:#精确查询
        条目=按键.get(名)#目录
        if 条目 is None:#没有
            raise Exception('no catalogued service named "'+名+'"')#失败
        服务=None#现场
        for 候选 in 现场:#查找
            if 候选['name']==名:#命中
                服务=候选#记下
                break#结束
        if 服务 is None:#没跑
            raise Exception('catalogued service "'+名+'" is not running')#失败
        选中=[服务]#只留一条
        契约们=条目['methods']#契约
    for 服务 in 选中:#写出
        行们.extend(服务行们(服务,契约们))#行
    if 名 is None:#压缩目录附加
        for 服务 in 现场:#未编目
            if 服务['catalogued']:#已编目
                continue#跳过
            行们.append(#无签名提示
                '- '+服务['name']+' (provided by '+服务['owner']+') — running, but this catalog has no signature for it;'
                +" inject: ['"+服务['name']+"'] still reaches it"
            )#行
        未跑=缺席服务(上下文,目录)#缺席
        if len(未跑)>0:#有
            行们.append('not running (loadable services with no live provider): '+', '.join(未跑))#列表
    形态=类型闭包([签名 for 服务 in 选中 for 签名 in 服务['methods']],类型们)#引用类型
    if len(形态)>0:#有类型
        行们.append('type shapes (referenced by the signatures above — read these before assuming a field is a string):')#标题
        for 形状 in 形态:#每个
            for 声明行 in 形状['declaration'].split('\n'):#按行
                行们.append('    '+声明行)#缩进
    if 名 is None:#继承 API
        行们.append('inherited ctx API:')#标题
        for 条目 in 继承:#每条
            行们.append('- '+条目['name']+' — '+条目['summary'])#行
    return 行们#整节

def 描述事件(事件们=None,名=None):#events 节
    """每个 harness 事件及其派发模式。"""
    if 事件们 is None:#缺省
        事件们=事件目录#模块
    选中=事件们#默认全部
    if 名 is not None:#精确
        事件=None#查找
        for 候选 in 事件们:#按名
            if 候选['name']==名:#命中
                事件=候选#记下
                break#结束
        if 事件 is None:#没有
            raise Exception('no catalogued event named "'+名+'"')#失败
        选中=[事件]#只留
    行们=[]#输出
    for 事件 in 选中:#每条
        行们.append('- '+事件['name']+' ['+事件['mode']+'] — '+事件['summary'])#头
        if 名 is not None:#精确才展开
            行们.append('    '+事件['description'])#说明
            for 参数 in 事件.get('parameters') or []:#参数
                行们.append('    @param '+参数['name']+' — '+参数['description'])#@param
        行们.append('    '+事件['signature'])#签名
    行们.append('waterfall listeners receive a trailing next() and MUST call it to delegate — returning without next() short-circuits the chain.')#waterfall 警告
    return 行们#整节

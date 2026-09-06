"""动态 Cordis Fiber 的缺失/已提供服务查询与文本报告全节渲染。

对齐上游 `拓展/tool-cordis/src/inspect.ts`。公开面仅中文名。
"""
import re#去 {@link}
from .光纤状态 import 光纤状态,状态标签#状态镜像与标签
from .接口目录 import 服务目录,事件目录,类型目录,继承上下文目录#生成目录

__all__=[#仅中文公开名
    '缺失服务','已提供服务','是否在光纤子树内','巡检错误',
    '描述服务','描述插件','描述工具','描述临时','描述接口','描述事件',
]#公开面结束

class 巡检错误(Exception):
    """Cordis 巡检查询失败。"""
    pass#消息在构造时传入

def 按行名(行):
    """按服务名排序。"""
    return 行['name']#名

def 按光纤名(光纤):
    """按纤程显示名排序。"""
    return 光纤.名称#显示名

def 按条目名(条目):
    """按类型条目名排序。"""
    return 条目['name']#名

def 是否在光纤子树内(光纤,根):
    """Fiber 是否就是 root，或挂在 root 子树的任意位置。"""
    当前=光纤#从自身向上走
    while True:#直到根或自环
        if 当前 is 根:#命中子树根
            return True#在内
        父上下文=当前.父上下文#父上下文
        if 父上下文 is None:#没有父
            return False#不在
        父=父上下文.纤程#父 Fiber
        if 父 is None or 父 is 当前:#到了真正的根仍未命中
            return False#不在
        当前=父#继续向上

def 现场实现(上下文):
    """从 反射.存储 读出的现场服务登记。存储值为 服务实现 对象。"""
    反射=上下文.反射#反射层
    存储=反射.存储#服务实现表
    结果=[]#现场实现
    for 实现 in 存储.values():#每条
        if 实现 is None:#空槽
            continue#跳过
        结果.append({'name':实现.名称,'fiber':实现.纤程})#收入报告行；name 是巡检报告字段
    return 结果#列表

def 已提供服务(上下文,光纤):
    """一次挂载的 Fiber 子树所提供的服务名，按字典序。"""
    return sorted([实现['name'] for 实现 in 现场实现(上下文) if 是否在光纤子树内(实现['fiber'],光纤)])#过滤排序

def 缺失服务(上下文,光纤):
    """Fiber 在 inject 里声明、但尚不存在的服务名，按声明顺序。inject 是框架槽。"""
    注入=光纤.inject#声明
    if 注入 is None:#无声明
        return []#空
    键列表=list(注入.keys())#声明键
    return [名 for 名 in 键列表 if 上下文.获取服务(名) is None]#仍缺

def 白话摘要(摘要):#去掉链接语法
    """{@link Foo.bar} → Foo.bar。"""
    return re.sub(r'\{@link\s+([^}]+)\}',r'\1',摘要)#保留链接里的符号名

def 现场服务(上下文,目录=None):#拼接现场与目录
    """本进程提供的每个服务，与生成目录拼接。"""
    if 目录 is None:#缺省
        目录=服务目录#模块目录
    编目={条目['key']:条目 for 条目 in 目录}#按键索引
    行列表=[]#报告行
    for 实现 in 现场实现(上下文):#现场
        条目=编目[实现['name']] if 实现['name'] in 编目 else None#目录条目
        状态值=实现['fiber'].状态#纤程状态
        行列表.append({#组装
            'name':实现['name'],#服务键
            'owner':实现['fiber'].名称,#所属 Fiber
            'state':状态标签[状态值] if 状态值 in 状态标签 else str(状态值),#状态标签
            'summary':'' if 条目 is None else 白话摘要(条目['summary']),#摘要
            'catalogued':条目 is not None,#是否已编目
            'methods':[] if 条目 is None else [方法['signature'] for 方法 in 条目['methods']],#方法签名
        })#行
    return sorted(行列表,key=按行名)#按服务名排序

def 缺席服务(上下文,目录=None):#目录有、现场无
    """已编目但无现场提供方的服务键。"""
    if 目录 is None:#缺省
        目录=服务目录#模块
    现场=set(实现['name'] for 实现 in 现场实现(上下文))#现场键
    return sorted([条目['key'] for 条目 in 目录 if 条目['key'] not in 现场])#缺席

def 描述服务(上下文,目录=None):#渲染 services 节
    """每个现场 ctx 服务及其所属 Fiber；生成目录覆盖时再加一行摘要。"""
    if 目录 is None:#缺省
        目录=服务目录#模块
    现场=现场服务(上下文,目录)#拼接
    if len(现场)==0:#无服务
        return ['(no services provided)']#占位
    活跃标签=状态标签[光纤状态['ACTIVE']]#活跃标签
    行列表=[]#输出
    for 服务 in 现场:#每条
        状态='' if 服务['state']==活跃标签 else ', '+服务['state']#非活跃才写出
        摘要='' if 服务['summary']=='' else ' — '+服务['summary']#有摘要才接上
        行列表.append('- '+服务['name']+' (provided by '+服务['owner']+状态+')'+摘要)#行
    return 行列表#节

def 描述插件(上下文):#渲染 plugins 节
    """注册表知道的每条 Fiber 扁平列出。"""
    注册表=上下文.注册表#插件注册表
    光纤列表=[]#收集
    for 记录 in 注册表.全部运行记录():#每个运行时
        for 光纤 in 记录.纤程表:#该插件的纤程
            光纤列表.append(光纤)#收入
    光纤列表=sorted(光纤列表,key=按光纤名)#按名排序
    行列表=[]#输出
    for 光纤 in 光纤列表:#每条
        态=光纤.状态#状态
        标签=状态标签[态] if 态 in 状态标签 else str(态)#标签
        行列表.append('- '+光纤.名称+' ['+标签+']')#行
    return 行列表#节

def 描述工具(上下文,作用域=None):#渲染 tools 节
    """调用方 Agent 能看见的面向模型工具名。"""
    return ['- '+模式['name'] for 模式 in 上下文.tools.schemas(作用域)]#可见工具名

def 描述临时(上下文,智能体=None):#渲染 temporary 节
    """本会话定义的每个动态包。"""
    行列表=[] if 智能体 is None else 上下文.dynamicCordisRunner.快照(智能体)#无 Agent 则无定义空间
    if len(行列表)==0:#空
        return ['No dynamic Plugins are defined in this session. Definitions live only in this process\'s memory, so a DSH restart clears them.']#占位
    输出=[]#多行
    for 行 in 行列表:#每个插件
        当前='none' if 'currentPackageId' not in 行 else str(行['currentPackageId'])#当前包；缺席才写 none
        下一='none' if 'nextPackageId' not in 行 else str(行['nextPackageId'])#下一包
        头='- Plugin '+str(行['pluginId'])+'; current: '+当前+'; next: '+下一#头
        if 'activeRun' not in 行:#无活动
            头+='; stopped'#已停
        else:#有活动
            活动=行['activeRun']#活动
            头+='; active: '+str(活动['packageId'])+' as '+str(活动['pluginRunId'])#活动
        输出.append(头)#插件头
        for 包 in 行['packages']:#每个包
            半边='+'.join((['host'] if 包['hasHostHalf'] else [])+(['client'] if 包['hasClientHalf'] else []))#半边
            活动跑=行['activeRun'] if 'activeRun' in 行 else None#活动
            活动=活动跑 if 活动跑 is not None and 活动跑['packageId']==包['packageId'] else None#该包是否在跑
            if 活动 is None:#未激活
                输出.append('    - '+str(包['packageId'])+': '+包['name']+' ('+半边+') — '+包['purpose'])#元数据
                continue#下一包
            光纤=活动['fiber'] if 'fiber' in 活动 else None#活动 Fiber；快照只在有纤维时写入该键
            if 光纤 is None:#无 Fiber
                状态='running'#写成 running
            elif 光纤.状态==光纤状态['ACTIVE']:#已激活
                状态='running'#running
            else:#其它
                态=光纤.状态#状态值
                状态=状态标签[态] if 态 in 状态标签 else str(态)#标签
            提供=[] if 光纤 is None else 已提供服务(上下文,光纤)#提供
            等待=[] if 光纤 is None else 缺失服务(上下文,光纤)#等待
            失败=活动['renderFailure'] if 'renderFailure' in 活动 else None#客户端渲染失败
            if 失败 is None:#无失败
                失败文=''#空
            else:#有失败
                槽=失败['slot'] if 'slot' in 失败 else ''#槽位
                消息=失败['message'] if 'message' in 失败 else ''#消息
                已卸=失败['abdicated'] if 'abdicated' in 失败 else False#是否卸入口
                失败文='; CLIENT RENDER FAILED at '+str(槽)+': '+str(消息)+(' (entry removed)' if 已卸 else '')#失败文
            方法表=活动['handlers'] if 'handlers' in 活动 else []#宿主方法名列表
            方法文='' if len(方法表)==0 else '; host methods: '+', '.join(方法表)#方法
            提供文='none' if len(提供)==0 else ', '.join(提供)#提供列表
            等待文='none' if len(等待)==0 else ', '.join(等待)#等待列表
            输出.append('    - '+str(包['packageId'])+': '+包['name']+' ['+状态+', '+str(活动['pluginRunId'])+'] ('+半边+') — '+包['purpose']+'; provides: '+提供文+'; waiting for: '+等待文+方法文+失败文)#包行
    return 输出#节

def 类型闭包(种子列表,类型列表=None):#引用类型闭包
    """种子文本引用到的已编目类型形态的传递闭包。"""
    if 类型列表 is None:#缺省
        类型列表=类型目录#模块
    已收={}#名 → 条目
    前沿=list(种子列表)#本轮文本
    while len(前沿)>0:#还有
        下一轮=[]#下一轮
        for 条目 in 类型列表:#每个类型
            if 条目['name'] in 已收:#已收
                continue#跳过
            模式=re.compile(r'\b'+re.escape(条目['name'])+r'\b')#词边界
            if any(模式.search(文本) for 文本 in 前沿):#命中
                已收[条目['name']]=条目#收录
                下一轮.append(条目['declaration'])#继续扫
        前沿=下一轮#下一轮
    return sorted(已收.values(),key=按条目名)#按名排序

def 拼服务行列表(服务,契约列表):#拼一条服务的报告行
    """精确名时带结构化契约。"""
    行列表=['- '+服务['name']+' — '+服务['summary']]#标题
    for 签名 in 服务['methods']:#每个方法
        契约=None#契约
        for 候选 in 契约列表:#查找
            if 候选['signature']==签名:#命中
                契约=候选#记下
                break#停止
        if 契约 is not None:#有契约
            行列表.append('    '+契约['description'])#说明
            参数列表=契约['parameters'] if 'parameters' in 契约 else []#参数；缺席当空列表
            for 参数 in 参数列表:#参数
                行列表.append('    @param '+参数['name']+' — '+参数['description'])#参数行
            if 'returns' in 契约 and 契约['returns'] is not None:#返回
                行列表.append('    @returns '+契约['returns'])#返回行
            抛错列表=契约['throws'] if 'throws' in 契约 else []#抛错
            for 失败 in 抛错列表:#抛错
                行列表.append('    @throws '+失败)#抛错行
        行列表.append('    '+签名)#签名本身
    return 行列表#该服务全部行

def 描述接口(上下文,目录=None,名=None,继承=None,类型列表=None):#渲染 api 节
    """对照现场运行时渲染生成目录。"""
    if 目录 is None:#缺省
        目录=服务目录#模块
    if 继承 is None:#缺省
        继承=继承上下文目录#模块
    if 类型列表 is None:#缺省
        类型列表=类型目录#模块
    现场=现场服务(上下文,目录)#拼接
    按键={条目['key']:条目 for 条目 in 目录}#索引
    行列表=[]#输出
    选中=[服务 for 服务 in 现场 if 服务['catalogued']]#默认已编目
    契约列表=[]#精确名契约
    if 名 is not None:#精确查询
        条目=按键[名] if 名 in 按键 else None#目录
        if 条目 is None:#目录没有
            raise 巡检错误('no catalogued service named "'+名+'"')#抛出
        服务=None#现场
        for 候选 in 现场:#找
            if 候选['name']==名:#命中
                服务=候选#记下
                break#停止
        if 服务 is None:#没跑
            raise 巡检错误('catalogued service "'+名+'" is not running')#抛出
        选中=[服务]#只留一条
        契约列表=条目['methods']#契约
    for 服务 in 选中:#写出
        行列表.extend(拼服务行列表(服务,契约列表))#行
    if 名 is None:#压缩目录附加
        for 服务 in 现场:#未编目
            if 服务['catalogued']:#已编目
                continue#跳过
            行列表.append('- '+服务['name']+' (provided by '+服务['owner']+') — running, but this catalog has no signature for it; inject: [\''+服务['name']+'\'] still reaches it')#无签名提示
        未跑=缺席服务(上下文,目录)#缺席
        if len(未跑)>0:#有
            行列表.append('not running (loadable services with no live provider): '+', '.join(未跑))#缺席列表
    形态=类型闭包([签名 for 服务 in 选中 for 签名 in 服务['methods']],类型列表)#引用类型
    if len(形态)>0:#有类型
        行列表.append('type shapes (referenced by the signatures above — read these before assuming a field is a string):')#标题
        for 形 in 形态:#每个类型
            for 声明行 in 形['declaration'].split('\n'):#按行
                行列表.append('    '+声明行)#缩进
    if 名 is None:#继承 API
        行列表.append('inherited ctx API:')#标题
        for 条目 in 继承:#每条
            行列表.append('- '+条目['name']+' — '+条目['summary'])#行
    return 行列表#整节

def 描述事件(事件列表=None,名=None):#渲染 events 节
    """每个 harness 事件及其派发模式、摘要与签名。"""
    if 事件列表 is None:#缺省
        事件列表=事件目录#模块
    选中=事件列表#默认全部
    if 名 is not None:#精确
        事件=None#查找
        for 候选 in 事件列表:#找
            if 候选['name']==名:#命中
                事件=候选#记下
                break#停止
        if 事件 is None:#没有
            raise 巡检错误('no catalogued event named "'+名+'"')#抛出
        选中=[事件]#一条
    行列表=[]#输出
    for 事件 in 选中:#每条
        行列表.append('- '+事件['name']+' ['+事件['mode']+'] — '+事件['summary'])#头
        if 名 is not None:#精确展开
            行列表.append('    '+事件['description'])#说明
            参数列表=事件['parameters'] if 'parameters' in 事件 else []#参数
            for 参数 in 参数列表:#参数
                行列表.append('    @param '+参数['name']+' — '+参数['description'])#参数
        行列表.append('    '+事件['signature'])#签名
    行列表.append('waterfall listeners receive a trailing next() and MUST call it to delegate — returning without next() short-circuits the chain.')#waterfall 警告
    return 行列表#整节

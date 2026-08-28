"""智能体技能提供方注册表。本包拥有技能能力缝的 Service Definition 角色。具体提供方决定技能从何处来；本服务只合并提供方目录、解析某名称的胜出技能，并把胜出摘要与定义暴露给消费方。"""
import json,math,re,threading#正则、缓存键、有限数与后台观察
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 路径上节点,数字字段#配置字段
服务=cordis.服务#Cordis服务基类
是否thenable=cordis.工具.是否thenable#可等待判定
承诺=cordis.工具.承诺#承诺
from ...内核.作用域 import 具名条目,作用域层集,获取作用域,获取作用域链,弱身份表#分层命名条目与作用域链
from ...模型后端.llm import 断言永不#封闭联合收尾断言
from .类型 import (#再导出类型面
    技能调用来源种类,#MessageSource 判别标签
    技能调用形态,#instructions 形态
    技能调用源字段,#来源字段元组
    技能调用来源,#用户显式调用来源
    技能来源已知,#已知来源桶
    技能资源基址种类,#基址三臂
    技能资源基址目录,#目录基址
    技能资源基址网址,#URL 基址
    技能资源基址不透明,#不透明基址
    技能调用策略,#模型/用户调用控制
    技能摘要,#目录摘要
    技能候选,#带排名与定位器的候选
    技能定义,#含正文的完整定义
    技能注册输入,#运行时登记输入
    技能查找选项,#提供方查找上下文
    技能视图选项,#带观察作用域的读取选项
    技能目录快照,#摘要+完整性
    技能提供方观察,#候选+完整性
    技能提供方控制,#注册期 signal/invalidate
    技能配置,#注册表可配置项
    技能提供方字段,#提供方约定字段
    技能提供方,#提供方协议
)#类型面导入结束

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '技能调用来源种类','技能调用形态','技能调用源字段','技能调用来源','技能来源已知',
    '技能资源基址种类','技能资源基址目录','技能资源基址网址','技能资源基址不透明',
    '技能调用策略','技能摘要','技能候选','技能定义','技能注册输入','技能查找选项',
    '技能视图选项','技能目录快照','技能提供方观察','技能提供方控制','技能配置',
    '技能提供方字段','技能提供方','是否技能名','是否模型可调用','是否用户可调用',
    '转义文本','渲染技能内容','捆绑技能排名','技能注册表','默认',
]#公开面结束

技能名模式=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')#公开技能名：kebab-case
默认收集缓存条目=128#收集缓存默认上限
最大收集尝试=2#收集遇修订冲突最多再试次数
运行时提供方名='runtime'#运行时贡献占用的保留提供方名
运行时排名=250#运行时条目在一层内的默认排名
捆绑技能排名=600#打包技能提供方与本地捆绑根的标准优先排名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否整数(值):#对齐JS Number.isInteger
    """对齐 JS Number.isInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return True#整数
    if isinstance(值,float):#浮点
        return 值.is_integer()#整值浮点
    return False#其它类型

def 是否有限数(值):#对齐JS Number.isFinite
    """对齐 JS Number.isFinite，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是有限数
    if isinstance(值,(int,float)):#数值
        return math.isfinite(值)#有限
    return False#其它类型

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 已中止(信号):#信号是否已中止
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#无信号
    if getattr(信号,'aborted',False):#英文旗标
        return True#英文旗标
    if getattr(信号,'已中止',False):#中文旗标
        return True#中文旗标
    return False#未中止

def 中止原因(信号):#取出中止原因
    """取出中止原因。"""
    if 信号 is None:#无信号
        return None#无信号
    原因=getattr(信号,'reason',None)#英文原因
    if 原因 is not None:#有英文原因
        return 原因#英文原因
    return getattr(信号,'原因',None)#中文原因

def 听中止(信号,回调):#登记一次性abort回调
    """登记一次性 abort 回调。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'addEventListener'):#Web API
        信号.addEventListener('abort',回调,{'once':True})#听一次
        return#已登记
    if hasattr(信号,'加入监听'):#中文API
        信号.加入监听('abort',回调,{'once':True})#听一次

def 摘中止(信号,回调):#去掉abort回调
    """去掉 abort 回调。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'removeEventListener'):#Web API
        信号.removeEventListener('abort',回调)#摘掉
        return#已摘
    if hasattr(信号,'移除监听'):#中文API
        信号.移除监听('abort',回调)#摘掉

def 是否技能名(名):#校验技能名语法
    """判断字符串是否为合法 kebab-case 技能名。"""
    return 技能名模式.fullmatch(名) is not None#匹配公开kebab-case文法

def 是否模型可调用(技能):#模型面是否可调用
    """判断技能是否可向模型广告并由模型加载。"""
    return 取字段(取字段(技能,'invocation'),'modelInvocable') is True#读策略字段

def 是否用户可调用(技能):#用户面是否可调用
    """判断技能是否可向面向人的命令广告并由其加载。"""
    return 取字段(取字段(技能,'invocation'),'userInvocable') is True#读策略字段

def 转义属性(值):#转义属性值
    """转义嵌入标签属性内的文本。"""
    return 值.replace('&','&amp;').replace('"','&quot;').replace('<','&lt;')#& " < 依次转义

def 转义文本(值):#转义正文文本
    """转义嵌入技能标记内的面向模型散文，使提供方供给的文本无法打开或关闭框架标签。"""
    return 值.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')#& < > 依次转义

def 渲染资源提示(技能):#按基址种类生成提示
    """按资源基址种类生成面向模型的资源提示行。"""
    基址=取字段(技能,'resourceBase')#可选资源基址
    提供方=取字段(技能,'provider')#提供方名
    if 基址 is None:#没有基址则只点名提供方
        return [#默认提示
            'Resources for this skill are managed by provider "'+转义文本(提供方)+'".',#提供方托管资源
            'Load referenced resources only as needed.',#按需加载
        ]#默认提示结束
    种类=取字段(基址,'kind')#基址种类
    if 种类=='directory':#本地目录
        return [#目录提示
            'Base directory for this skill: '+转义文本(取字段(基址,'path')),#基目录路径
            'Resolve relative paths mentioned by this skill against the base directory before using them. Load referenced resources only as needed.',#相对路径相对基目录解析
        ]#目录提示结束
    if 种类=='url':#URL基址
        return [#URL提示
            'Base URL for this skill: '+转义文本(取字段(基址,'url')),#基URL
            'Resolve relative URLs mentioned by this skill against the base URL before using them. Load referenced resources only as needed.',#相对URL相对基址解析
        ]#URL提示结束
    if 种类=='opaque':#不透明描述
        return [#不透明提示
            'Resources for this skill: '+转义文本(取字段(基址,'description')),#描述文本
            'Load referenced resources only as needed.',#按需加载
        ]#不透明提示结束
    return 断言永不(基址,'SkillResourceBase.kind')#封闭联合收尾

def 渲染技能内容(技能):#渲染规范技能块
    """把一份已加载技能渲染给模型。输出由 skill 工具结果与用户显式调用注入原样共享。"""
    资源提示=渲染资源提示(技能)#按基址种类生成资源提示行
    行们=[#拼成规范XML形态
        '<skill_content name="'+转义属性(取字段(技能,'name'))+'">',#转义后的名称属性
        '<skill_resources>',#资源提示开标签
    ]#开标签结束
    行们.extend(资源提示)#基址提示行
    行们.extend([#指令与闭标签
        '</skill_resources>',#资源提示闭标签
        '',#空行分隔
        '<skill_instructions>',#指令开标签
        取字段(技能,'content'),#技能正文原样嵌入
        '</skill_instructions>',#指令闭标签
        '</skill_content>',#整块闭标签
    ])#闭标签结束
    return '\n'.join(行们)#按行拼接

class 中止控制器:#发出中止的控制器
    """对应 AbortController，供提供方注册生命周期使用。"""
    def __init__(自身):#创建配套信号
        """创建配套信号。"""
        自身.信号=_中止信号()#本控制器的信号

    def 中止(自身,原因=None):#中止配套信号
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

class _中止信号:#一次中止信号
    """对应 AbortSignal。"""
    def __init__(自身):#初始未中止
        """初始未中止。"""
        自身.aborted=False#英文旗标
        自身.已中止=False#中文旗标
        自身.reason=None#英文原因
        自身.原因=None#中文原因
        自身._监听=[]#abort监听

    def 触发(自身,原因=None):#触发一次中止
        """触发一次中止并通知监听。"""
        if 自身.aborted:#已中止
            return#幂等
        自身.aborted=True#英文旗标
        自身.已中止=True#中文旗标
        自身.reason=原因#英文原因
        自身.原因=原因#中文原因
        for 回调 in list(自身._监听):#快照通知
            回调()#调用监听

    def addEventListener(自身,类型,回调,选项=None):#Web API
        """登记 abort 监听。"""
        if 类型!='abort':#只关心abort
            return#忽略
        if 自身.aborted:#已中止则立刻
            回调()#立刻回调
            return#结束
        自身._监听.append(回调)#登记

    def removeEventListener(自身,类型,回调):#Web API
        """去掉 abort 监听。"""
        if 类型!='abort':#只关心abort
            return#忽略
        if 回调 in 自身._监听:#仍在表中
            自身._监听.remove(回调)#摘掉

    def 加入监听(自身,类型,回调,选项=None):#中文API
        """中文登记。"""
        自身.addEventListener(类型,回调,选项)#委托

    def 移除监听(自身,类型,回调):#中文API
        """中文摘掉。"""
        自身.removeEventListener(类型,回调)#委托

class 技能层:#一层的提供方与运行时表
    """一个作用域的完整技能注册表贡献。"""
    def __init__(自身,作用域):#按作用域构造重复名错误
        """按作用域构造重复名错误。"""
        def 重复错误(名):#重复提供方诊断
            """重复提供方诊断。"""
            if 作用域 is None:#全局层
                return Exception('a skill provider named "'+名+'" is already registered')#全局层重复
            return Exception('a skill provider named "'+名+'" is already registered in this scope')#本作用域重复
        自身.提供方=具名条目(重复错误)#命名提供方表
        自身.运行时={}#运行时技能表

    def 是否空(自身):#层是否可回收
        """此聚合层中每一张贡献表是否都为空。"""
        return 自身.提供方.是否空() and len(自身.运行时)==0#提供方与运行时都空

class 技能注册表(服务):#技能注册表服务
    """技能提供方的分层注册表，沿用工具注册表确立的宿主+每作用域形态。一次注册落入调用上下文作用域的那一层：宿主行与仓库插件落入全局层，由智能体预设常驻组合挂载的插件落入该预设的层。读取时把全局层与观察作用域的链合并——最近一层的同名条目直接胜出，排名只在同一层内决定重复项。对外暴露已排序的、与调用面无关的摘要，并按需加载完整技能正文。"""
    配置=路径上节点({#配置模式
        'collectCacheMaxEntries':数字字段(默认值=默认收集缓存条目),#缓存上限，默认128
    })#结束配置模式
    Config=配置#Cordis 配置模式槽

    def __init__(自身,ctx,配置=None):#安装skills服务
        """安装 skills 服务。"""
        super().__init__(ctx,'skills')#以skills名挂到上下文
        if 配置 is None:#缺省空配置
            配置={}#空配置
        上限=取字段(配置,'collectCacheMaxEntries')#配置上限
        if 上限 is None:#未给出
            上限=默认收集缓存条目#默认128
        自身.收集缓存上限=上限#缓存条目上限
        断言正整数('collectCacheMaxEntries',自身.收集缓存上限)#加载时校验为正整数
        def 建层(作用域):#新建一层
            """新建一层。"""
            return 技能层(作用域)#建层
        def 层变():#层结构变化则失效缓存
            """层结构变化则失效缓存。"""
            自身.使缓存失效()#清缓存并通知
        自身.层集=作用域层集(建层,层变)#按作用域持有层
        自身.收集缓存={}#收集结果缓存
        自身.修订=0#目录修订号
        自身.下一提供方次序=0#下一提供方注册次序
        自身.作用域编号表=弱身份表()#作用域→数字id
        自身.下一作用域编号=1#下一作用域数字id

    def 登记提供方(自身,构造):#注册提供方
        """在插件 apply 期间同步注册一个借用的同进程提供方，落入调用上下文的层：带作用域的上下文只为该作用域注册，无作用域的上下文全局注册。同一层内重复名与保留名抛错；远程初始化属于 list()。拆除会注销提供方并使目录缓存失效。"""
        生命周期=中止控制器()#此次注册的生命周期
        登记=None#插入成功后的层与名
        提供方=None#工厂产出的提供方
        def 使失效():#仅当恰好这次注册仍活着才失效
            """仅当恰好这次注册仍活着才失效。"""
            活跃=登记#当前登记
            if 活跃 is None:#尚未插入或已拆
                return#无操作
            现有=活跃['layer'].提供方.获取(活跃['name'])#层内现有
            if 现有 is not None and 取字段(现有,'provider') is 提供方:#仍是同一实例
                自身.使缓存失效()#清缓存并通知
        控制={'signal':生命周期.信号,'invalidate':使失效}#交给工厂的控制面
        try:#工厂失败则中止生命周期
            提供方=构造(控制)#同步构造提供方
            名=取字段(提供方,'name')#提供方自报名称
            if 名==运行时提供方名:#占用保留名
                raise Exception('"'+运行时提供方名+'" is reserved for runtime skill registrations')#runtime名保留
            次序=自身.下一提供方次序#本次次序
            自身.下一提供方次序+=1#单调递增
            def 写入层(层):#插入并在拆除时撤回
                """插入并在拆除时撤回。"""
                nonlocal 登记#修改外层登记
                撤销=层.提供方.插入(名,{'provider':提供方,'order':次序})#插入命名条目
                登记={'layer':层,'name':名}#记下活登记
                def 拆除():#effect拆除
                    """effect 拆除。"""
                    nonlocal 登记#修改外层
                    登记=None#先清登记，避免迟到失效
                    撤销()#从层移除
                    生命周期.中止(Exception('skill provider "'+名+'" disposed'))#中止生命周期
                return 拆除#拆除器
            return 自身.层集.副作用(自身.ctx,写入层,{'标签':'skills.registerProvider()'})#按调用上下文的层插入
        except BaseException as 错误:#工厂或插入失败
            生命周期.中止(错误)#中止控制面信号
            raise#原样抛出

    def 登记(自身,技能):#注册运行时技能
        """把一份借用的只读运行时技能注册进调用上下文的层。同一层内项目条目高于运行时条目，运行时条目高于用户条目。同层同名运行时条目先到先得；重复项记警告并得到空操作拆除器，因而不能移除胜出者。"""
        校验运行时技能(技能)#校验名、描述与调用策略
        作用域=获取作用域(自身.ctx)#调用上下文的作用域
        if 作用域 is None:#全局层
            已有层=自身.层集.全局#已有全局层
        else:#作用域层
            已有层=自身.层集.窥视(作用域)#已有层，不为此创建
        名=取字段(技能,'name')#技能名
        if 已有层 is not None and 名 in 已有层.运行时:#同层已有同名运行时技能
            自身.ctx.logger.warn('runtime skill "'+名+'" ignored because it is already registered')#先到先得，忽略后来者
            def 空操作():#空操作disposer
                """空操作 disposer，不能拆胜出者。"""
                return None#无操作
            return 空操作#不能拆胜出者
        调用=取字段(技能,'invocation')#可选调用策略
        if 调用 is None:#省略则两面都允许
            调用={'modelInvocable':True,'userInvocable':True}#默认两面
        提供方标签=取字段(技能,'provider')#可选提供方名
        if 提供方标签 is None:#省略则runtime提供方
            提供方标签=运行时提供方名#runtime
        if isinstance(技能,dict):#映射则浅拷贝
            定义=dict(技能)#拷贝字段
        else:#对象则按字段拼
            定义={#基础字段
                'name':名,#技能名
                'description':取字段(技能,'description'),#描述
                'source':取字段(技能,'source'),#来源
                'content':取字段(技能,'content'),#正文
            }#基础结束
            for 可选键 in ('whenToUse','resourceBase','path','metadata'):#可选字段
                可选值=取字段(技能,可选键)#读可选
                if 可选值 is not None:#有则写入
                    定义[可选键]=可选值#写入
        定义['invocation']=调用#调用策略
        定义['provider']=提供方标签#提供方
        def 写入层(层):#写入运行时表
            """写入运行时表。"""
            层.运行时[定义['name']]=定义#按名放入
            def 拆除():#拆除时删除
                """拆除时删除。"""
                层.运行时.pop(定义['name'],None)#删除
            return 拆除#拆除器
        return 自身.层集.副作用(自身.ctx,写入层,{'标签':'skills.register()'})#按调用上下文的层写入

    def 列出(自身,选项=None):#列摘要
        """列出某工作区与调用面无关的技能摘要。消费方在自己的操作边界应用模型或用户调用策略。查找选项与提供方候选是发现全程借用的只读同进程值。"""
        if 选项 is None:#缺省空选项
            选项={}#空选项
        return 取字段(自身.快照(选项),'skills')#快照里的技能列表

    def 快照(自身,选项=None):#拍目录快照
        """观察当前与调用面无关的目录，以及发现是否在稳定修订内完成。不完整观察永不缓存，让消费方保留上次完好状态并在下一请求边界重试。"""
        if 选项 is None:#缺省空选项
            选项={}#空选项
        已收集=自身.收集(选项)#收集胜出条目
        摘要们=[]#胜出摘要
        for 条目 in 取字段(已收集,'entries').values():#Map值转数组
            摘要们.append(成摘要(取字段(条目,'candidate')))#剥成摘要
        摘要们=排序摘要(摘要们)#按名码点排序
        return {'skills':摘要们,'complete':取字段(已收集,'cacheable')}#摘要+完整性

    def 获取(自身,名,选项=None):#按名加载正文
        """加载并校验胜出候选，把它不透明的发现定位器回传给提供方。选定后（含缓存命中）再次检查取消，并与加载竞速，以免不配合的提供方挂住调用方。"""
        if 选项 is None:#缺省空选项
            选项={}#空选项
        if not 是否技能名(名):#非法名直接没有
            return None#没有
        已收集=自身.收集(选项)#收集当前胜出表
        抛若中止(取字段(选项,'signal'))#选定前再查取消
        匹配=取字段(已收集,'entries').get(名)#按名胜出
        if 匹配 is None:#没有此名
            return None#没有
        提供方=取字段(匹配,'provider')#所属提供方
        候选=取字段(匹配,'candidate')#胜出候选
        获取函数=取字段(提供方,'get')#加载正文
        定义=与取消竞速(获取函数(候选,选项),取字段(选项,'signal'))#与取消竞速加载
        if 定义 is None:#已不可加载
            return None#没有
        校验定义(定义)#校验加载结果
        if 取字段(定义,'name')!=取字段(候选,'name'):#加载后改名视为陈旧
            自身.使条目失效(匹配)#仅当该注册仍活着才失效
            return None#对调用方如同不存在
        return 定义#完整定义

    def 收集(自身,选项):#带缓存的收集
        """带缓存的跨层收集。"""
        抛若中止(取字段(选项,'signal'))#入口即查取消
        尝试=1#当前尝试次数
        while True:#修订冲突时可再试
            修订=自身.修订#本轮开始时的修订
            键=自身.收集缓存键(取字段(选项,'cwd'),获取作用域链(取字段(选项,'scope')),修订)#cwd+作用域链+修订
            缓存=自身.收集缓存.get(键)#查缓存
            if 缓存 is not None:#命中则完整
                return {'entries':缓存,'cacheable':True}#命中
            结果=自身.现收集(选项)#未命中则现收集
            抛若中止(取字段(选项,'signal'))#收集后再查取消
            if 修订!=自身.修订:#收集期间目录已变
                if 尝试<最大收集尝试:#还有重试额度
                    尝试+=1#再试一轮
                    continue#用新修订重收集
                return {'entries':取字段(结果,'entries'),'cacheable':False}#不缓存这次结果
            if 取字段(结果,'cacheable'):#完整才写入缓存
                自身.收集缓存[键]=取字段(结果,'entries')#按键存入
                if len(自身.收集缓存)>自身.收集缓存上限:#超出上限
                    最旧=next(iter(自身.收集缓存))#Map插入序最旧键
                    del 自身.收集缓存[最旧]#淘汰最旧
            return 结果#返回本轮结果

    def 现收集(自身,选项):#无缓存地跨层收集
        """无缓存地跨层收集。"""
        层们=[自身.层集.全局]+自身.层集.链上层(取字段(选项,'scope'))#全局+观察链
        合并={}#按名后写覆盖
        可缓存=True#任一层不完整则整体不完整
        for 层 in 层们:#由远到近
            本层=自身.收集层(层,选项)#收集一层
            if not 取字段(本层,'cacheable'):#传播不完整
                可缓存=False#不可缓存
            for 条目 in 取字段(本层,'entries'):#本层胜出
                合并[取字段(取字段(条目,'candidate'),'name')]=条目#近层覆盖远层
        return {'entries':合并,'cacheable':可缓存}#合并结果

    def 收集层(自身,层,选项):#收集一层并去重
        """收集一层并按排名去重。"""
        已收集=自身.枚举层候选(层,选项)#本层全部候选
        条目们=list(取字段(已收集,'entries'))#可变列表
        条目们.sort(key=索引候选排序键)#按rank/提供方次序/本地次序
        已见=set()#本层已胜出的名
        结果=[]#本层去重后的胜出
        for 条目 in 条目们:#已按优先级排序
            技能=取字段(条目,'candidate')#候选本体
            名=取字段(技能,'name')#技能名
            if 名 in 已见:#同层已有更高优先
                自身.ctx.logger.warn('skill "'+名+'" from '+str(取字段(技能,'source'))+' ignored because a higher-priority skill already exists')#忽略较低优先
                continue#跳过
            已见.add(名)#记下胜出名
            结果.append(条目)#收入本层结果
        return {'entries':结果,'cacheable':取字段(已收集,'cacheable')}#本层结果

    def 枚举层候选(自身,层,选项):#枚举一层候选
        """枚举一层候选。"""
        抛若中止(取字段(选项,'signal'))#入口查取消
        候选们=[]#本层原始候选
        可缓存=True#提供方失败或不完整则不可缓存
        运行时次序=0#运行时条目的本地次序
        运行时技能=sorted(层.运行时.values(),key=lambda 项:取字段(项,'name'))#运行时按名排序后枚举
        for 技能 in 运行时技能:#运行时定义
            候选们.append({#把运行时定义包成候选
                'candidate':运行时候选(技能),#带RUNTIME_RANK的候选
                'provider':运行时技能提供方,#注册表内置get
                'providerOrder':-1,#运行时先于真实提供方
                'localOrder':运行时次序,#稳定本地次序
                'layer':层,#所属层
            })#结束push
            运行时次序+=1#下一运行时次序
        for 登记 in list(层.提供方.诸值()):#按插入序问每个提供方
            提供方=取字段(登记,'provider')#提供方实例
            次序=取字段(登记,'order')#注册次序
            本地次序=0#该提供方内本地次序
            输出=None#list()原始输出
            try:#提供方list失败不拖垮整层
                列出函数=取字段(提供方,'list')#列候选
                输出=与取消竞速(列出函数(选项),取字段(选项,'signal'))#与取消竞速
            except BaseException as 错误:#list抛错
                if 已中止(取字段(选项,'signal')):#取消则上抛
                    raise 化为错误(中止原因(取字段(选项,'signal')))#规范化原因
                可缓存=False#失败则本层不可缓存
                自身.ctx.logger.warn('skill provider "'+str(取字段(提供方,'name'))+'" skipped: '+错误消息(错误))#跳过该提供方
            if 输出 is None:#失败后无输出
                continue#下一提供方
            观察=规范提供方观察(输出,取字段(提供方,'name'))#数组或显式观察
            if not 取字段(观察,'complete'):#不完整发现不可缓存
                可缓存=False#不可缓存
            for 候选 in 取字段(观察,'candidates'):#逐条校验后收入
                校验候选(候选,取字段(提供方,'name'))#名、描述、提供方一致性等
                候选们.append({'candidate':候选,'provider':提供方,'providerOrder':次序,'localOrder':本地次序,'layer':层})#带次序的索引候选
                本地次序+=1#下一本地次序
        return {'entries':候选们,'cacheable':可缓存}#本层原始候选

    def 使缓存失效(自身):#bump修订并清空缓存
        """bump 修订并清空缓存。"""
        自身.修订+=1#使现有缓存键失效
        自身.收集缓存.clear()#丢掉全部收集结果
        自身.通知变更()#通知观察者

    def 使条目失效(自身,条目):#按条目精确失效
        """陈旧定义加载后失效，仅当产出该条目的恰好这次注册仍活着。"""
        层=取字段(条目,'layer')#所属层
        提供方=取字段(条目,'provider')#提供方实例
        现有=层.提供方.获取(取字段(提供方,'name'))#层内现有
        if 现有 is not None and 取字段(现有,'provider') is 提供方:#仍是同一实例才清缓存
            自身.使缓存失效()#清缓存

    def 作用域编号(自身,键):#作用域键→稳定数字id
        """作用域键→稳定数字 id。"""
        编号=自身.作用域编号表.取(键)#已分配则复用
        if 编号 is None:#首次见到此键
            编号=自身.下一作用域编号#取下一个id
            自身.下一作用域编号+=1#单调递增
            自身.作用域编号表.设(键,编号)#记住身份
        return 编号#稳定数字

    def 收集缓存键(自身,cwd,链,修订):#收集缓存键
        """收集缓存键。"""
        载荷={}#键对象
        if cwd is not None:#有cwd才写入，对齐JSON省略undefined
            载荷['cwd']=cwd#工作区根
        载荷['scopes']=[自身.作用域编号(键) for 键 in 链]#作用域id链
        载荷['revision']=修订#修订号
        return json.dumps(载荷,separators=(',',':'),ensure_ascii=False)#cwd+作用域id链+修订

    def 通知变更(自身):#发出skills/change
        """通知目录观察者，但不让他们的刷新工作成为负载。"""
        参数=['skills/change']#emit派发参数
        for 回调 in list(自身.ctx.events.dispatch('emit',参数)):#取出emit监听器
            try:#监听器失败不得否决变更
                返回=回调()#可能返回thenable
                if 是否thenable(返回):#异步拒绝也收容
                    def 盯住(任务=返回):#收住拒绝
                        """收住异步拒绝。"""
                        try:#等待
                            任务.等待()#等待
                        except BaseException as 错误:#拒绝
                            自身.ctx.logger.warn('skills/change listener rejected: '+错误消息(错误))#记录拒绝
                    线程=threading.Thread(target=盯住)#后台观察
                    线程.daemon=True#不挡住退出
                    线程.start()#启动
            except BaseException as 错误:#同步抛错
                自身.ctx.logger.warn('skills/change listener threw: '+错误消息(错误))#记录抛错

def 排序摘要(摘要们):#摘要按名排序
    """按技能名码点排序摘要列表。"""
    return sorted(摘要们,key=lambda 项:取字段(项,'name'))#码点序

def 索引候选排序键(条目):#层内候选排序键
    """层内候选排序键：较低 rank 先胜，其次提供方注册次序，再本地次序。"""
    return (取字段(取字段(条目,'candidate'),'rank'),取字段(条目,'providerOrder'),取字段(条目,'localOrder'))#三元组

def 规范提供方观察(输出,提供方名):#规范list输出
    """把 list() 的数组简写或显式观察规范成观察对象。"""
    if isinstance(输出,(list,tuple)):#完整数组简写
        return {'candidates':list(输出),'complete':True}#数组即完整
    if 输出 is None or (not isinstance(输出,dict)):#既非数组也非对象
        raise 非法提供方观察(提供方名)#形状非法
    候选=取字段(输出,'candidates')#候选字段
    完整=取字段(输出,'complete')#完整字段
    if not isinstance(候选,(list,tuple)) or not isinstance(完整,bool):#缺字段
        raise 非法提供方观察(提供方名)#形状非法
    return {'candidates':list(候选),'complete':完整}#已是观察

def 非法提供方观察(提供方名):#list返回值非法
    """list 返回值非法。"""
    return TypeError('skill provider "'+提供方名+'" list() must return an array or { candidates, complete } observation')#要求数组或观察

def 运行时获取(候选,选项=None):#定位器就是定义本身
    """运行时提供方 get：定位器就是定义本身。"""
    return 取字段(候选,'locator')#直接交回

def 运行时列出(选项=None):#运行时不经list发现
    """运行时提供方 list：空目录。"""
    任务=承诺()#立刻兑现
    任务.兑现([])#空目录
    return 任务#已兑现

运行时技能提供方={#注册表内置运行时提供方
    'name':运行时提供方名,#保留名runtime
    'list':运行时列出,#运行时不经list发现
    'get':运行时获取,#定位器就是定义本身
}#结束RUNTIME_SKILL_PROVIDER

def 运行时候选(技能):#运行时定义→候选
    """把运行时定义包成带排名与定位器的候选。"""
    候选={#补rank与locator
        'name':取字段(技能,'name'),#技能名
        'description':取字段(技能,'description'),#描述
        'invocation':取字段(技能,'invocation'),#调用策略
        'source':取字段(技能,'source'),#来源桶
        'provider':取字段(技能,'provider'),#提供方标签
        'rank':运行时排名,#运行时排名
        'locator':技能,#定位器即定义
    }#结束候选基础
    何时=取字段(技能,'whenToUse')#可选何时使用
    if 何时 is not None:#有则写入
        候选['whenToUse']=何时#何时使用
    基址=取字段(技能,'resourceBase')#可选资源基址
    if 基址 is not None:#有则写入
        候选['resourceBase']=基址#资源基址
    路径=取字段(技能,'path')#可选路径
    if 路径 is not None:#有则写入
        候选['path']=路径#路径
    元数据=取字段(技能,'metadata')#可选元数据
    if 元数据 is not None:#有则写入
        候选['metadata']=元数据#元数据
    return 候选#候选

def 校验候选(候选,提供方名):#校验提供方候选
    """校验提供方候选。"""
    名=取字段(候选,'name')#技能名
    if not isinstance(名,str):#名必须是字符串
        raise TypeError('skill provider "'+提供方名+'" returned a non-string skill name')#非字符串名
    if 技能名模式.fullmatch(名) is None:#名必须匹配公开文法
        raise Exception('skill provider "'+提供方名+'" returned invalid skill name "'+名+'"')#非法技能名
    描述=取字段(候选,'description')#描述
    if not isinstance(描述,str):#描述必须是字符串
        raise TypeError('skill provider "'+提供方名+'" returned skill "'+名+'" with a non-string description')#非字符串描述
    if len(描述)==0:#描述不可空
        raise Exception('skill provider "'+提供方名+'" returned skill "'+名+'" without a description')#缺描述
    校验调用(取字段(候选,'invocation'),'skill provider "'+提供方名+'" returned skill "'+名+'"')#校验调用策略
    何时=取字段(候选,'whenToUse')#可选何时使用
    if 何时 is not None and not isinstance(何时,str):#若有则必须是字符串
        raise TypeError('skill provider "'+提供方名+'" returned skill "'+名+'" with a non-string whenToUse')#非字符串whenToUse
    来源=取字段(候选,'source')#来源
    if not isinstance(来源,str):#来源必须是字符串
        raise TypeError('skill provider "'+提供方名+'" returned skill "'+名+'" with a non-string source')#非字符串来源
    排名=取字段(候选,'rank')#排名
    if not 是否有限数(排名):#排名必须是有限数
        raise Exception('skill provider "'+提供方名+'" returned skill "'+名+'" with an invalid rank')#非法排名
    提供方字段=取字段(候选,'provider')#提供方字段
    if not isinstance(提供方字段,str):#提供方字段必须是字符串
        raise TypeError('skill provider "'+提供方名+'" returned skill "'+名+'" with a non-string provider')#非字符串提供方
    if 提供方字段!=提供方名:#必须自称本提供方
        raise Exception('skill provider "'+提供方名+'" returned skill "'+名+'" for provider "'+提供方字段+'"')#提供方名不一致
    路径=取字段(候选,'path')#可选路径
    if 路径 is not None and not isinstance(路径,str):#若有路径则必须是字符串
        raise TypeError('skill provider "'+提供方名+'" returned skill "'+名+'" with a non-string path')#非字符串路径

def 校验运行时技能(技能):#校验运行时注册输入
    """校验运行时注册输入。"""
    名=取字段(技能,'name')#技能名
    if 技能名模式.fullmatch(名) is None:#非法名
        raise Exception('invalid skill name "'+str(名)+'"')#非法名
    描述=取字段(技能,'description')#描述
    if 描述 is None or len(描述)==0:#缺描述
        raise Exception('skill "'+名+'" requires a description')#缺描述
    校验调用(取字段(技能,'invocation'),'runtime skill "'+名+'"')#校验可选调用策略

def 校验定义(技能):#校验加载后的定义
    """校验从提供方控制的解析器或远程来源加载的定义。"""
    名=取字段(技能,'name')#技能名
    描述=取字段(技能,'description')#描述
    何时=取字段(技能,'whenToUse')#可选何时使用
    调用=取字段(技能,'invocation')#调用策略
    来源=取字段(技能,'source')#来源桶
    提供方=取字段(技能,'provider')#提供方
    正文=取字段(技能,'content')#正文
    路径=取字段(技能,'path')#可选路径
    if not isinstance(名,str):#名类型
        raise TypeError('loaded skill name must be a string')#名类型
    if 技能名模式.fullmatch(名) is None:#名文法
        raise Exception('loaded skill has invalid name "'+名+'"')#名文法
    if not isinstance(描述,str):#描述类型
        raise TypeError('loaded skill "'+名+'" description must be a string')#描述类型
    if len(描述)==0:#描述非空
        raise Exception('loaded skill "'+名+'" requires a description')#描述非空
    校验调用(调用,'loaded skill "'+名+'"')#调用策略
    if 何时 is not None and not isinstance(何时,str):#whenToUse类型
        raise TypeError('loaded skill "'+名+'" whenToUse must be a string')#whenToUse类型
    if not isinstance(来源,str):#来源类型
        raise TypeError('loaded skill "'+名+'" source must be a string')#来源类型
    if not isinstance(提供方,str):#提供方类型
        raise TypeError('loaded skill "'+名+'" provider must be a string')#提供方类型
    if not isinstance(正文,str):#正文类型
        raise TypeError('loaded skill "'+名+'" content must be a string')#正文类型
    if 路径 is not None and not isinstance(路径,str):#路径类型
        raise TypeError('loaded skill "'+名+'" path must be a string')#路径类型

def 成摘要(技能):#剥成调用面无关摘要
    """剥成调用面无关摘要。"""
    摘要={#省略未定义的可选字段
        'name':取字段(技能,'name'),#技能名
        'description':取字段(技能,'description'),#描述
        'invocation':取字段(技能,'invocation'),#调用策略
        'source':取字段(技能,'source'),#来源
        'provider':取字段(技能,'provider'),#提供方
    }#结束摘要基础
    何时=取字段(技能,'whenToUse')#可选何时使用
    if 何时 is not None:#有则写入
        摘要['whenToUse']=何时#何时使用
    基址=取字段(技能,'resourceBase')#可选资源基址
    if 基址 is not None:#有则写入
        摘要['resourceBase']=基址#资源基址
    return 摘要#摘要

def 校验调用(调用,主题):#校验调用策略对象
    """校验调用策略对象。"""
    if 调用 is None:#运行时注册允许省略
        return#省略
    if not isinstance(调用,dict):#必须是普通对象
        raise TypeError(主题+' with a non-object invocation policy')#非对象策略
    if not isinstance(取字段(调用,'modelInvocable'),bool):#模型面必须是布尔
        raise TypeError(主题+' with a non-boolean invocation.modelInvocable')#非布尔modelInvocable
    if not isinstance(取字段(调用,'userInvocable'),bool):#用户面必须是布尔
        raise TypeError(主题+' with a non-boolean invocation.userInvocable')#非布尔userInvocable

def 断言正整数(名,值,下限=1):#配置正整数断言
    """配置正整数断言。"""
    if (not 是否整数(值)) or 值<下限:#非整数或低于下限
        raise Exception('skill: '+名+' must be an integer greater than or equal to '+str(下限))#加载时大声失败

def 与取消竞速(任务,信号):#与取消竞速
    """与取消信号竞速等待提供方工作。"""
    if 信号 is None:#无信号则原样返回
        return 解开(任务)#解开
    抛若中止(信号)#已取消则立刻抛
    结果=承诺()#包装竞速
    锁=threading.Lock()#只结算一次
    已结算=[False]#可变旗标
    def 清理():#去掉abort监听
        """去掉 abort 监听。"""
        摘中止(信号,当中止)#防止泄漏
    def 当中止(*位置参数):#信号中止
        """信号中止。"""
        with 锁:#临界区
            if 已结算[0]:#已结算
                return#忽略
            已结算[0]=True#标已结算
        清理()#先摘监听
        结果.拒绝(化为错误(中止原因(信号)))#以规范化Error拒绝
    def 盯任务():#提供方结算
        """提供方结算。"""
        try:#等待任务
            值=解开(任务)#解开
            with 锁:#临界区
                if 已结算[0]:#已结算
                    return#忽略
                已结算[0]=True#标已结算
            清理()#摘监听
            结果.兑现(值)#交回值
        except BaseException as 错误:#失败
            with 锁:#临界区
                if 已结算[0]:#已结算
                    return#忽略
                已结算[0]=True#标已结算
            清理()#摘监听
            结果.拒绝(化为错误(错误))#规范化后拒绝
    听中止(信号,当中止)#只听一次
    线程=threading.Thread(target=盯任务)#后台等待
    线程.daemon=True#不挡住退出
    线程.start()#启动
    return 结果.等待()#阻塞取胜者

def 抛若中止(信号):#已取消则抛
    """已中止的查找抛出完备 Error。"""
    if 已中止(信号):#已取消
        raise 化为错误(中止原因(信号))#规范化reason

def 化为错误(错误):#任意值→Error
    """规范化任意中止或提供方失败，不信任强制转换。"""
    try:#isinstance可能被敌对代理打断
        if isinstance(错误,BaseException):#已是异常则原样
            return 错误#原样
    except BaseException:#敌对代理在isinstance时抛错
        pass#落到完备渲染器
    return Exception(错误消息(错误))#用渲染后的消息包一层

def 错误消息(错误):#任意值→消息
    """渲染任意提供方失败，不让强制转换逃出收容。"""
    try:#String()也可能被敌对值打断
        return str(错误)#常规渲染
    except BaseException:#无法渲染
        return '[unrenderable thrown value]'#占位消息

默认=技能注册表#默认导出注册表类

import json,math,re,threading,weakref#正则、缓存键、有限数、中止通道与原因旁表
from ...依赖 import cordis#外部依赖胶水
from ...依赖.工具 import 获取内部数据#读事件总线内部成员
from ...依赖.schemastery import 数字字段#配置字段
服务=cordis.服务#Cordis服务基类
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
    '转义文本','渲染技能内容','捆绑技能排名','技能注册表','技能错误',
]#公开面结束

技能名模式=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$',re.ASCII)#公开技能名：kebab-case
默认收集缓存条目=128#收集缓存默认上限
最大收集尝试=2#收集遇修订冲突最多再试次数
运行时提供方名='runtime'#运行时贡献占用的保留提供方名
运行时排名=250#运行时条目在一层内的默认排名
捆绑技能排名=600#打包技能提供方与本地捆绑根的标准优先排名
中止原因表=weakref.WeakKeyDictionary()#中止原因旁表，不挂在信号对象上

class 技能错误(Exception):
    """本包异常基类。"""

class 中止信号:
    """threading.Event 取消通道。原因用异常对象承载，不对外挂第二字段。"""
    def __init__(自身,已中止标志=False):
        """创建一条取消通道。"""
        自身.事件=threading.Event()#中止标志
        if 已中止标志:#创建时已中止
            自身.事件.set()#置位
            中止原因表[自身]=技能错误('已中止')#默认中止异常

    def 触发(自身,原因=None):
        """标记中止。"""
        if 自身.事件.is_set():#只触发一次
            return#已触发
        if isinstance(原因,BaseException):#原因已是异常
            中止原因表[自身]=原因#旁表承载
        elif 原因 is not None:#非异常原因
            错=技能错误('已中止')#包装
            错.原因=原因#附加在异常上
            中止原因表[自身]=错#记下
        else:#无原因
            中止原因表[自身]=技能错误('已中止')#默认
        自身.事件.set()#置位

class 中止控制器:
    """发出中止的控制器。"""
    def __init__(自身):
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。信号是本包中止信号。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.事件.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出承载原因的异常。"""
    if 信号 is None:#无信号
        return#无信号
    if not 信号.事件.is_set():#仍活着
        return#仍活着
    if 信号 in 中止原因表:#有承载异常
        raise 中止原因表[信号]#抛出
    raise 技能错误('已中止')#默认中止

def 是否技能名(名):
    """判断字符串是否为合法 kebab-case 技能名。"""
    return 技能名模式.fullmatch(名) is not None#匹配公开kebab-case文法

def 是否模型可调用(技能):
    """判断技能是否可向模型广告并由模型加载。技能是 dict。"""
    if 'invocation' not in 技能:#无调用策略
        return False#不可调用
    return 技能['invocation']['modelInvocable'] is True#读策略字段

def 是否用户可调用(技能):
    """判断技能是否可向面向人的命令广告并由其加载。技能是 dict。"""
    if 'invocation' not in 技能:#无调用策略
        return False#不可调用
    return 技能['invocation']['userInvocable'] is True#读策略字段

def 转义属性(值):
    """转义嵌入标签属性内的文本。"""
    return 值.replace('&','&amp;').replace('"','&quot;').replace('<','&lt;')#& " < 依次转义

def 转义文本(值):
    """转义嵌入技能标记内的面向模型散文，使提供方供给的文本无法打开或关闭框架标签。"""
    return 值.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')#& < > 依次转义

def 渲染资源提示(技能):
    """按资源基址种类生成面向模型的资源提示行。技能与基址是 dict。"""
    基址=技能['resourceBase'] if 'resourceBase' in 技能 else None#可选资源基址
    提供方=技能['provider']#提供方名
    if 基址 is None:#没有基址则只点名提供方
        return [#默认提示
            'Resources for this skill are managed by provider "'+转义文本(提供方)+'".',#提供方托管资源
            'Load referenced resources only as needed.',#按需加载
        ]#默认提示结束
    种类=基址['kind']#基址种类
    if 种类=='directory':#本地目录
        return [#目录提示
            'Base directory for this skill: '+转义文本(基址['path']),#基目录路径
            'Resolve relative paths mentioned by this skill against the base directory before using them. Load referenced resources only as needed.',#相对路径相对基目录解析
        ]#目录提示结束
    if 种类=='url':#URL基址
        return [#URL提示
            'Base URL for this skill: '+转义文本(基址['url']),#基URL
            'Resolve relative URLs mentioned by this skill against the base URL before using them. Load referenced resources only as needed.',#相对URL相对基址解析
        ]#URL提示结束
    if 种类=='opaque':#不透明描述
        return [#不透明提示
            'Resources for this skill: '+转义文本(基址['description']),#描述文本
            'Load referenced resources only as needed.',#按需加载
        ]#不透明提示结束
    return 断言永不(基址,'SkillResourceBase.kind')#封闭联合收尾

def 渲染技能内容(技能):
    """把一份已加载技能渲染给模型。输出由 skill 工具结果与用户显式调用注入原样共享。技能是 dict。"""
    资源提示=渲染资源提示(技能)#按基址种类生成资源提示行
    行列表=[#拼成规范XML形态
        '<skill_content name="'+转义属性(技能['name'])+'">',#转义后的名称属性
        '<skill_resources>',#资源提示开标签
    ]#开标签结束
    行列表.extend(资源提示)#基址提示行
    行列表.extend([#指令与闭标签
        '</skill_resources>',#资源提示闭标签
        '',#空行分隔
        '<skill_instructions>',#指令开标签
        技能['content'],#技能正文原样嵌入
        '</skill_instructions>',#指令闭标签
        '</skill_content>',#整块闭标签
    ])#闭标签结束
    return '\n'.join(行列表)#按行拼接

class 技能层:#一层的提供方与运行时表
    """一个作用域的完整技能注册表贡献。"""
    def __init__(自身,作用域):#按作用域构造重复名错误
        """按作用域构造重复名错误。"""
        def 重复错误(名):#重复提供方诊断
            """重复提供方诊断。"""
            if 作用域 is None:#全局层
                return 技能错误('名为 "'+名+'" 的技能提供方已登记')#全局层重复
            return 技能错误('名为 "'+名+'" 的技能提供方已在本作用域登记')#本作用域重复
        自身.提供方=具名条目(重复错误)#命名提供方表
        自身.运行时={}#运行时技能表

    def 是否空(自身):#层是否可回收
        """此聚合层中每一张贡献表是否都为空。"""
        return 自身.提供方.是否空() and len(自身.运行时)==0#提供方与运行时都空

class 技能注册表(服务):#技能注册表服务
    """技能提供方的分层注册表，沿用工具注册表确立的宿主+每作用域形态。一次注册落入调用上下文作用域的那一层：宿主行与仓库插件落入全局层，由智能体预设常驻组合挂载的插件落入该预设的层。读取时把全局层与观察作用域的链合并——最近一层的同名条目直接胜出，排名只在同一层内决定重复项。对外暴露已排序的、与调用面无关的摘要，并按需加载完整技能正文。"""
    配置={#配置模式
        'collectCacheMaxEntries':数字字段(默认值=默认收集缓存条目),#缓存上限，默认128
    }#结束配置模式

    def __init__(自身,ctx,配置=None):#安装skills服务
        """安装 skills 服务。配置是 dict。"""
        super().__init__(ctx,'skills')#以skills名挂到上下文
        if 配置 is None:#缺省空配置
            配置={}#空配置
        上限=配置['collectCacheMaxEntries'] if 'collectCacheMaxEntries' in 配置 else None#配置上限
        if 上限 is None:#未给出
            上限=默认收集缓存条目#默认128
        自身.收集缓存上限=上限#缓存条目上限
        校验正整数('collectCacheMaxEntries',自身.收集缓存上限)#加载时校验为正整数
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
        """在插件 apply 期间同步注册一个借用的同进程提供方，落入调用上下文的层：带作用域的上下文只为该作用域注册，无作用域的上下文全局注册。同一层内重复名与保留名抛错；远程初始化属于 list()。拆除会注销提供方并使目录缓存失效。提供方是 dict，含 name/list/get。"""
        生命周期=中止控制器()#此次注册的生命周期
        登记=None#插入成功后的层与名
        提供方=None#工厂产出的提供方
        def 使失效():#仅当恰好这次注册仍活着才失效
            """仅当恰好这次注册仍活着才失效。"""
            活跃=登记#当前登记
            if 活跃 is None:#尚未插入或已拆
                return#无操作
            现有=活跃['layer'].提供方.获取(活跃['name'])#层内现有
            if 现有 is not None and 现有['provider'] is 提供方:#仍是同一实例
                自身.使缓存失效()#清缓存并通知
        控制={'signal':生命周期.信号,'invalidate':使失效}#交给工厂的控制面
        try:#工厂失败则中止生命周期
            提供方=构造(控制)#同步构造提供方
            名=提供方['name']#提供方自报名称
            if 名==运行时提供方名:#占用保留名
                raise 技能错误('"'+运行时提供方名+'" 保留给运行时技能登记')#runtime名保留
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
                    生命周期.中止(技能错误('技能提供方 "'+名+'" 已拆除'))#中止生命周期
                return 拆除#拆除器
            return 自身.层集.副作用(自身.ctx,写入层,{'标签':'skills.registerProvider()'})#按调用上下文的层插入
        except BaseException as 错误:#工厂或插入失败
            生命周期.中止(错误)#中止控制面信号
            raise#原样抛出

    def 登记(自身,技能):#注册运行时技能
        """把一份借用的只读运行时技能注册进调用上下文的层。同一层内项目条目高于运行时条目，运行时条目高于用户条目。同层同名运行时条目先到先得；重复项记警告并得到空操作拆除器，因而不能移除胜出者。技能是 dict。"""
        校验运行时技能(技能)#校验名、描述与调用策略
        作用域=获取作用域(自身.ctx)#调用上下文的作用域
        if 作用域 is None:#全局层
            已有层=自身.层集.全局#已有全局层
        else:#作用域层
            已有层=自身.层集.窥视(作用域)#已有层，不为此创建
        名=技能['name']#技能名
        if 已有层 is not None and 名 in 已有层.运行时:#同层已有同名运行时技能
            自身.ctx.日志.警告('runtime skill "'+名+'" ignored because it is already registered')#先到先得，忽略后来者
            def 空操作():#空操作disposer
                """空操作 disposer，不能拆胜出者。"""
                return None#无操作
            return 空操作#不能拆胜出者
        调用=技能['invocation'] if 'invocation' in 技能 else None#可选调用策略
        if 调用 is None:#省略则两面都允许
            调用={'modelInvocable':True,'userInvocable':True}#默认两面
        提供方标签=技能['provider'] if 'provider' in 技能 else None#可选提供方名
        if 提供方标签 is None:#省略则runtime提供方
            提供方标签=运行时提供方名#runtime
        定义=dict(技能)#浅拷贝字段
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
        """列出某工作区与调用面无关的技能摘要。消费方在自己的操作边界应用模型或用户调用策略。查找选项与提供方候选是发现全程借用的只读同进程值。选项是 dict。"""
        if 选项 is None:#缺省空选项
            选项={}#空选项
        return 自身.快照(选项)['skills']#快照里的技能列表

    def 快照(自身,选项=None):#拍目录快照
        """观察当前与调用面无关的目录，以及发现是否在稳定修订内完成。不完整观察永不缓存，让消费方保留上次完好状态并在下一请求边界重试。选项与收集结果是 dict。"""
        if 选项 is None:#缺省空选项
            选项={}#空选项
        已收集=自身.收集(选项)#收集胜出条目
        摘要列表=[]#胜出摘要
        for 条目 in 已收集['entries'].values():#Map值转数组
            摘要列表.append(成摘要(条目['candidate']))#剥成摘要
        摘要列表=排序摘要(摘要列表)#按名码点排序
        return {'skills':摘要列表,'complete':已收集['cacheable']}#摘要+完整性

    def 获取(自身,名,选项=None):#按名加载正文
        """加载并校验胜出候选，把它不透明的发现定位器回传给提供方。选定后（含缓存命中）再次检查取消。选项、条目、提供方、候选、定义都是 dict。"""
        if 选项 is None:#缺省空选项
            选项={}#空选项
        if not 是否技能名(名):#非法名直接没有
            return None#没有
        已收集=自身.收集(选项)#收集当前胜出表
        信号=选项['signal'] if 'signal' in 选项 else None#可选取消信号
        若已中止则抛出(信号)#选定前再查取消
        if 名 not in 已收集['entries']:#没有此名
            return None#没有
        匹配=已收集['entries'][名]#按名胜出
        提供方=匹配['provider']#所属提供方
        候选=匹配['candidate']#胜出候选
        定义=提供方['get'](候选,选项)#同步加载正文
        若已中止则抛出(信号)#加载后再查取消
        if 定义 is None:#已不可加载
            return None#没有
        校验定义(定义)#校验加载结果
        if 定义['name']!=候选['name']:#加载后改名视为陈旧
            自身.使条目失效(匹配)#仅当该注册仍活着才失效
            return None#对调用方如同不存在
        return 定义#完整定义

    def 收集(自身,选项):#带缓存的收集
        """带缓存的跨层收集。选项与结果是 dict。"""
        信号=选项['signal'] if 'signal' in 选项 else None#可选取消信号
        若已中止则抛出(信号)#入口即查取消
        尝试=1#当前尝试次数
        while True:#修订冲突时可再试
            修订=自身.修订#本轮开始时的修订
            键=自身.收集缓存键(选项['cwd'] if 'cwd' in 选项 else None,获取作用域链(选项['scope'] if 'scope' in 选项 else None),修订)#cwd+作用域链+修订
            if 键 in 自身.收集缓存:#命中则完整
                return {'entries':自身.收集缓存[键],'cacheable':True}#命中
            结果=自身.现收集(选项)#未命中则现收集
            若已中止则抛出(信号)#收集后再查取消
            if 修订!=自身.修订:#收集期间目录已变
                if 尝试<最大收集尝试:#还有重试额度
                    尝试+=1#再试一轮
                    continue#用新修订重收集
                return {'entries':结果['entries'],'cacheable':False}#不缓存这次结果
            if 结果['cacheable']:#完整才写入缓存
                自身.收集缓存[键]=结果['entries']#按键存入
                if len(自身.收集缓存)>自身.收集缓存上限:#超出上限
                    最旧=next(iter(自身.收集缓存))#Map插入序最旧键
                    del 自身.收集缓存[最旧]#淘汰最旧
            return 结果#返回本轮结果

    def 现收集(自身,选项):#无缓存地跨层收集
        """无缓存地跨层收集。选项与层结果是 dict。"""
        层列表=[自身.层集.全局]+自身.层集.链上层(选项['scope'] if 'scope' in 选项 else None)#全局+观察链
        合并={}#按名后写覆盖
        可缓存=True#任一层不完整则整体不完整
        for 层 in 层列表:#由远到近
            本层=自身.收集层(层,选项)#收集一层
            if 本层['cacheable'] is False:#传播不完整
                可缓存=False#不可缓存
            for 条目 in 本层['entries']:#本层胜出
                合并[条目['candidate']['name']]=条目#近层覆盖远层
        return {'entries':合并,'cacheable':可缓存}#合并结果

    def 收集层(自身,层,选项):#收集一层并去重
        """收集一层并按排名去重。已收集与条目是 dict。"""
        已收集=自身.枚举层候选(层,选项)#本层全部候选
        条目列表=list(已收集['entries'])#可变列表
        条目列表.sort(key=索引候选排序键)#按rank/提供方次序/本地次序
        已见=set()#本层已胜出的名
        结果=[]#本层去重后的胜出
        for 条目 in 条目列表:#已按优先级排序
            技能=条目['candidate']#候选本体
            名=技能['name']#技能名
            if 名 in 已见:#同层已有更高优先
                自身.ctx.日志.警告('skill "'+名+'" from '+str(技能['source'])+' ignored because a higher-priority skill already exists')#忽略较低优先
                continue#跳过
            已见.add(名)#记下胜出名
            结果.append(条目)#收入本层结果
        return {'entries':结果,'cacheable':已收集['cacheable']}#本层结果

    def 枚举层候选(自身,层,选项):#枚举一层候选
        """枚举一层候选。选项、登记、提供方、观察都是 dict。"""
        信号=选项['signal'] if 'signal' in 选项 else None#可选取消信号
        若已中止则抛出(信号)#入口查取消
        候选列表=[]#本层原始候选
        可缓存=True#提供方失败或不完整则不可缓存
        运行时次序=0#运行时条目的本地次序
        运行时技能=sorted(层.运行时.values(),key=按技能名)#运行时按名排序后枚举
        for 技能 in 运行时技能:#运行时定义
            候选列表.append({#把运行时定义包成候选
                'candidate':运行时候选(技能),#带RUNTIME_RANK的候选
                'provider':运行时技能提供方,#注册表内置get
                'providerOrder':-1,#运行时先于真实提供方
                'localOrder':运行时次序,#稳定本地次序
                'layer':层,#所属层
            })#结束push
            运行时次序+=1#下一运行时次序
        for 登记 in list(层.提供方.诸值()):#按插入序问每个提供方
            提供方=登记['provider']#提供方实例
            次序=登记['order']#注册次序
            本地次序=0#该提供方内本地次序
            输出=None#list()原始输出
            try:#提供方list失败不拖垮整层
                输出=提供方['list'](选项)#同步列候选
                若已中止则抛出(信号)#列出后再查取消
            except BaseException as 错误:#list抛错
                if 已中止(信号):#取消则上抛
                    若已中止则抛出(信号)#抛出承载原因
                可缓存=False#失败则本层不可缓存
                自身.ctx.日志.警告('skill provider "'+str(提供方['name'])+'" skipped: '+错误消息(错误))#跳过该提供方
            if 输出 is None:#失败后无输出
                continue#下一提供方
            观察=规范提供方观察(输出,提供方['name'])#数组或显式观察
            if 观察['complete'] is False:#不完整发现不可缓存
                可缓存=False#不可缓存
            for 候选 in 观察['candidates']:#逐条校验后收入
                校验候选(候选,提供方['name'])#名、描述、提供方一致性等
                候选列表.append({'candidate':候选,'provider':提供方,'providerOrder':次序,'localOrder':本地次序,'layer':层})#带次序的索引候选
                本地次序+=1#下一本地次序
        return {'entries':候选列表,'cacheable':可缓存}#本层原始候选

    def 使缓存失效(自身):#bump修订并清空缓存
        """bump 修订并清空缓存。"""
        自身.修订+=1#使现有缓存键失效
        自身.收集缓存.clear()#丢掉全部收集结果
        自身.通知变更()#通知观察者

    def 使条目失效(自身,条目):#按条目精确失效
        """陈旧定义加载后失效，仅当产出该条目的恰好这次注册仍活着。条目与提供方是 dict。"""
        层=条目['layer']#所属层
        提供方=条目['provider']#提供方实例
        现有=层.提供方.获取(提供方['name'])#层内现有
        if 现有 is not None and 现有['provider'] is 提供方:#仍是同一实例才清缓存
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
        return json.dumps(载荷,ensure_ascii=False,separators=(',',':'),allow_nan=False)#cwd+作用域id链+修订

    def 通知变更(自身):#发出skills/change
        """通知目录观察者，但不让他们的刷新工作成为负载。"""
        参数=['skills/change']#emit派发参数
        事件总线=获取内部数据(自身.ctx,'属性链')['事件']#事件总线，不经壳
        for 回调 in list(获取内部数据(事件总线,'解析监听器')(事件总线,'emit',参数)):#取出emit监听器
            try:#监听器失败不得否决变更
                回调()#同步回调
            except Exception as 错误:#监听器契约未钉死，收容以免否决注册表变更
                自身.ctx.日志.警告('skills/change listener threw: '+错误消息(错误))#记录抛错

def 按技能名(项):
    """按技能名取排序键。项是 dict。"""
    return 项['name']#码点序键

def 排序摘要(摘要列表):
    """按技能名码点排序摘要列表。"""
    return sorted(摘要列表,key=按技能名)#码点序

def 索引候选排序键(条目):
    """层内候选排序键：较低 rank 先胜，其次提供方注册次序，再本地次序。条目是 dict。"""
    return (条目['candidate']['rank'],条目['providerOrder'],条目['localOrder'])#三元组

def 规范提供方观察(输出,提供方名):
    """把 list() 的数组简写或显式观察规范成观察对象。"""
    if isinstance(输出,(list,tuple)):#完整数组简写
        return {'candidates':list(输出),'complete':True}#数组即完整
    if 输出 is None or (not isinstance(输出,dict)):#既非数组也非对象
        raise 非法提供方观察(提供方名)#形状非法
    if 'candidates' not in 输出 or 'complete' not in 输出:#缺字段
        raise 非法提供方观察(提供方名)#形状非法
    候选=输出['candidates']#候选字段
    完整=输出['complete']#完整字段
    if not isinstance(候选,(list,tuple)) or not isinstance(完整,bool):#字段形态非法
        raise 非法提供方观察(提供方名)#形状非法
    return {'candidates':list(候选),'complete':完整}#已是观察

def 非法提供方观察(提供方名):
    """list 返回值非法。"""
    return TypeError('技能提供方 "'+提供方名+'" 的列出() 必须返回数组或 { candidates, complete } 观察')#要求数组或观察

def 运行时获取(候选,选项=None):
    """运行时提供方 get：定位器就是定义本身。候选是 dict。"""
    return 候选['locator']#直接交回

def 运行时列出(选项=None):
    """运行时提供方 list：空目录。"""
    return []#空目录

运行时技能提供方={#注册表内置运行时提供方
    'name':运行时提供方名,#保留名runtime
    'list':运行时列出,#运行时不经list发现
    'get':运行时获取,#定位器就是定义本身
}#结束RUNTIME_SKILL_PROVIDER

def 运行时候选(技能):
    """把运行时定义包成带排名与定位器的候选。技能是 dict。"""
    候选={#补rank与locator
        'name':技能['name'],#技能名
        'description':技能['description'],#描述
        'invocation':技能['invocation'],#调用策略
        'source':技能['source'],#来源桶
        'provider':技能['provider'],#提供方标签
        'rank':运行时排名,#运行时排名
        'locator':技能,#定位器即定义
    }#结束候选基础
    if 'whenToUse' in 技能:#可选何时使用
        候选['whenToUse']=技能['whenToUse']#何时使用
    if 'resourceBase' in 技能:#可选资源基址
        候选['resourceBase']=技能['resourceBase']#资源基址
    if 'path' in 技能:#可选路径
        候选['path']=技能['path']#路径
    if 'metadata' in 技能:#可选元数据
        候选['metadata']=技能['metadata']#元数据
    return 候选#候选

def 校验候选(候选,提供方名):
    """校验提供方候选。候选是 dict。"""
    名=候选['name'] if 'name' in 候选 else None#技能名
    if not isinstance(名,str):#名必须是字符串
        raise TypeError('技能提供方 "'+提供方名+'" 返回了非字符串技能名')#非字符串名
    if 技能名模式.fullmatch(名) is None:#名必须匹配公开文法
        raise 技能错误('技能提供方 "'+提供方名+'" 返回了非法技能名 "'+名+'"')#非法技能名
    描述=候选['description'] if 'description' in 候选 else None#描述
    if not isinstance(描述,str):#描述必须是字符串
        raise TypeError('技能提供方 "'+提供方名+'" 返回的技能 "'+名+'" 描述不是字符串')#非字符串描述
    if len(描述)==0:#描述不可空
        raise 技能错误('技能提供方 "'+提供方名+'" 返回的技能 "'+名+'" 缺少描述')#缺描述
    校验调用(候选['invocation'] if 'invocation' in 候选 else None,'skill provider "'+提供方名+'" returned skill "'+名+'"')#校验调用策略
    何时=候选['whenToUse'] if 'whenToUse' in 候选 else None#可选何时使用
    if 何时 is not None and not isinstance(何时,str):#若有则必须是字符串
        raise TypeError('技能提供方 "'+提供方名+'" 返回的技能 "'+名+'" 的 whenToUse 不是字符串')#非字符串whenToUse
    来源=候选['source'] if 'source' in 候选 else None#来源
    if not isinstance(来源,str):#来源必须是字符串
        raise TypeError('技能提供方 "'+提供方名+'" 返回的技能 "'+名+'" 的 source 不是字符串')#非字符串来源
    排名=候选['rank'] if 'rank' in 候选 else None#排名
    if isinstance(排名,bool) or not isinstance(排名,(int,float)) or not math.isfinite(排名):#入口排除布尔，排名必须是有限数
        raise 技能错误('技能提供方 "'+提供方名+'" 返回的技能 "'+名+'" 排名非法')#非法排名
    提供方字段=候选['provider'] if 'provider' in 候选 else None#提供方字段
    if not isinstance(提供方字段,str):#提供方字段必须是字符串
        raise TypeError('技能提供方 "'+提供方名+'" 返回的技能 "'+名+'" 的 provider 不是字符串')#非字符串提供方
    if 提供方字段!=提供方名:#必须自称本提供方
        raise 技能错误('技能提供方 "'+提供方名+'" 返回的技能 "'+名+'" 声称属于提供方 "'+提供方字段+'"')#提供方名不一致
    路径=候选['path'] if 'path' in 候选 else None#可选路径
    if 路径 is not None and not isinstance(路径,str):#若有路径则必须是字符串
        raise TypeError('技能提供方 "'+提供方名+'" 返回的技能 "'+名+'" 的 path 不是字符串')#非字符串路径

def 校验运行时技能(技能):
    """校验运行时注册输入。技能是 dict。"""
    名=技能['name'] if 'name' in 技能 else None#技能名
    if not isinstance(名,str) or 技能名模式.fullmatch(名) is None:#非法名
        raise 技能错误('非法技能名 "'+str(名)+'"')#非法名
    描述=技能['description'] if 'description' in 技能 else None#描述
    if 描述 is None or len(描述)==0:#缺描述
        raise 技能错误('技能 "'+名+'" 需要描述')#缺描述
    校验调用(技能['invocation'] if 'invocation' in 技能 else None,'runtime skill "'+名+'"')#校验可选调用策略

def 校验定义(技能):
    """校验从提供方控制的解析器或远程来源加载的定义。技能是 dict。"""
    名=技能['name'] if 'name' in 技能 else None#技能名
    描述=技能['description'] if 'description' in 技能 else None#描述
    何时=技能['whenToUse'] if 'whenToUse' in 技能 else None#可选何时使用
    调用=技能['invocation'] if 'invocation' in 技能 else None#调用策略
    来源=技能['source'] if 'source' in 技能 else None#来源桶
    提供方=技能['provider'] if 'provider' in 技能 else None#提供方
    正文=技能['content'] if 'content' in 技能 else None#正文
    路径=技能['path'] if 'path' in 技能 else None#可选路径
    if not isinstance(名,str):#名类型
        raise TypeError('已加载技能名必须是字符串')#名类型
    if 技能名模式.fullmatch(名) is None:#名文法
        raise 技能错误('已加载技能名非法 "'+名+'"')#名文法
    if not isinstance(描述,str):#描述类型
        raise TypeError('已加载技能 "'+名+'" 的 description 必须是字符串')#描述类型
    if len(描述)==0:#描述非空
        raise 技能错误('已加载技能 "'+名+'" 需要描述')#描述非空
    校验调用(调用,'loaded skill "'+名+'"')#调用策略
    if 何时 is not None and not isinstance(何时,str):#whenToUse类型
        raise TypeError('已加载技能 "'+名+'" 的 whenToUse 必须是字符串')#whenToUse类型
    if not isinstance(来源,str):#来源类型
        raise TypeError('已加载技能 "'+名+'" 的 source 必须是字符串')#来源类型
    if not isinstance(提供方,str):#提供方类型
        raise TypeError('已加载技能 "'+名+'" 的 provider 必须是字符串')#提供方类型
    if not isinstance(正文,str):#正文类型
        raise TypeError('已加载技能 "'+名+'" 的 content 必须是字符串')#正文类型
    if 路径 is not None and not isinstance(路径,str):#路径类型
        raise TypeError('已加载技能 "'+名+'" 的 path 必须是字符串')#路径类型

def 成摘要(技能):
    """剥成调用面无关摘要。技能是 dict。序列化时省略缺席键。"""
    摘要={#省略未定义的可选字段
        'name':技能['name'],#技能名
        'description':技能['description'],#描述
        'invocation':技能['invocation'],#调用策略
        'source':技能['source'],#来源
        'provider':技能['provider'],#提供方
    }#结束摘要基础
    if 'path' in 技能:#可选绝对路径
        摘要['path']=技能['path']#路径
    if 'whenToUse' in 技能:#可选何时使用
        摘要['whenToUse']=技能['whenToUse']#何时使用
    if 'resourceBase' in 技能:#可选资源基址
        摘要['resourceBase']=技能['resourceBase']#资源基址
    return 摘要#摘要

def 校验调用(调用,主题):
    """校验调用策略对象。调用是 dict 或 None。"""
    if 调用 is None:#运行时注册允许省略
        return#省略
    if not isinstance(调用,dict):#必须是普通对象
        raise TypeError(主题+' 的调用策略不是对象')#非对象策略
    if 'modelInvocable' not in 调用 or not isinstance(调用['modelInvocable'],bool):#模型面必须是布尔
        raise TypeError(主题+' 的 invocation.modelInvocable 不是布尔')#非布尔modelInvocable
    if 'userInvocable' not in 调用 or not isinstance(调用['userInvocable'],bool):#用户面必须是布尔
        raise TypeError(主题+' 的 invocation.userInvocable 不是布尔')#非布尔userInvocable

def 校验正整数(名,值,下限=1):
    """配置入口正整数断言。排除布尔。"""
    if isinstance(值,bool) or not isinstance(值,int) or 值<下限:#非整数或低于下限
        raise 技能错误('skill: '+名+' 必须是大于等于 '+str(下限)+' 的整数')#加载时大声失败

def 错误消息(错误):
    """渲染任意提供方失败，不让强制转换逃出收容。"""
    try:#String()也可能被敌对值打断
        return str(错误)#常规渲染
    except Exception:#无法渲染；敌对值可能在 str 时抛任意错误
        return '[无法渲染的抛出值]'#占位消息

技能注册表.Config=技能注册表.配置#Cordis 配置模式槽
default=技能注册表#Cordis 默认导出

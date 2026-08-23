"""技能引用插件的浏览器半边。

登记「/」技能源——候选来自 skill.list RPC，按每次调用的会话
投影 sessionId 寻址（会话一律由智能体托底；宿主从会话头解析 cwd）。
选定落下字面 `/name ` 文本，提示发出同一字面量（纯文本引用决策）。
确定性在宿主侧——预步骤边界认出前导 `/name` 命名用户可调用技能。
RPC 走登记时捕获的插件根上下文连接。目录拉取按会话缓存：每次按键的
候选重询在本地过滤已落定快照。本浏览器半边还拥有 `skill` 键的 toolview。

对齐上游 `ui-skill/src/client/index.ts`。公开面仅中文名。
SkillRow 像素半硬缺口跳过；逻辑行从父包 `技能行` 接线。
"""
from ....依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#承诺
是否thenable=cordis.工具.是否thenable#可等待判定
from .文案 import 命名空间,中文,英文#词典（同目录厚叶）
from ..技能行 import 技能行#技能工具行（跳过 SkillRow.tsx；用父包厚叶）

__all__=['注入','应用']#仅中文公开名；对齐上游 export inject / apply

注入=['inputTriggers','connection','sessions','slots','locale','remote']#触发源、连接、会话、槽位、文案、远程

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 应用(上下文):#安装技能引用浏览器半边
    """登记「/」源、词表，以及按键的工具行。

    @param 上下文 - 客户端根上下文。
    """
    def 登记词典():#登记中英文案
        """登记本插件词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记中英文案
    上下文.effect(登记词典,'ui-skill: dictionaries')#词典生命周期
    def 登记工具行():#登记 skill toolview
        """等 toolview 槽出现再登记 skill 行。"""
        return 上下文.slots.register({#按 skill 键的 toolview 条目
            'name':'tool.call.toolview','key':'skill','locale':命名空间,#条目选项
        },技能行)#技能工具行组件
    上下文.slots.inject('tool.call.toolview',登记工具行)#等槽出现再登记
    连接=上下文.get('connection')#登记时捕获的根连接
    技能接口=取字段(取字段(连接,'api'),'skills')#根连接上的 skills RPC
    会话服务=上下文.get('sessions')#会话服务，用于子智能体地址
    拉取表={}#会话 → 在飞/已落定目录拉取（插件闭包；fiber effect 为拆除边界）
    词表监听={}#会话 → 词表监听者集合（subscribeLexicon 消费者）

    def 通知词表(会话标识):#通知该会话的词表监听者
        """通知该会话的词表监听者。"""
        for 监听 in list(词表监听.get(会话标识,set())):#快照后逐个通知，避免遍历中改集合
            try:#单个监听者失败不得饿死其余
                监听()#触发词表失效回调
            except Exception as 错误:#监听者自己抛了
                # 收住监听者失败：结算通知来自被忽略的 promise 链
                # （抛出会变成未处理拒绝），且一个坏消费者不得饿死其余。
                print('[ui-skill] lexicon listener failed:',错误)#记日志，不向外抛

    def 拉目录(会话标识):#按会话单飞拉取技能目录
        """按会话单飞拉取技能目录。"""
        if 会话服务.subagentAddress(会话标识) is not None:#子智能体会话没有用户技能目录
            return 已兑现([])#空目录
        已有=拉取表.get(会话标识)#已有在飞或已落定拉取
        if 已有 is not None:#同键复用，不发第二次 RPC
            return 已有['promise']#共享 promise
        中止器={'aborted':False}#自有中止：仅失效/拆除时触发，不跟菜单生命周期
        def 中止拉取():#中止在飞拉取
            """仅失效/拆除时触发。"""
            中止器['aborted']=True#标中止
        def 解包目录(包装):#从 list 响应取出 skills
            """解包 skill.list 业务结果。"""
            结果=取字段(包装,'result')#业务结果
            if not 取字段(结果,'ok'):#业务失败转成抛错
                错误=取字段(结果,'error')#错误
                raise Exception('skill.list failed: '+str(取字段(错误,'code'))+': '+str(取字段(错误,'message')))#转抛
            return 取字段(取字段(结果,'value'),'skills')#目录条目
        def 执行():#对齐上游 (async () => { await skills.list ... })()
            """单飞拉取：skill.list RPC；体内唯一一次 list。"""
            包装=技能接口.list({'sessionId':会话标识},中止器)#整条路径唯一一次 skill.list
            if 是否thenable(包装):#异步
                return 包装.then(解包目录)#链式解包同一次结果
            return 解包目录(包装)#同步：把同一次结果传入解包，禁止再 list
        产出=执行()#立即执行，共享同一 promise
        承诺=产出 if 是否thenable(产出) else 已兑现(产出)#统一为承诺
        条目={'promise':承诺,'abort':中止拉取}#本键的共享条目
        拉取表[会话标识]=条目#写入缓存，后续调用者加入这趟
        def 落定成功(技能们):#成功：写入 settled 并通知
            """写入 settled 并通知。"""
            条目['settled']=技能们#同步词表可读的快照
            通知词表(会话标识)#通知词表监听者
        def 落定失败(_错误=None):#失败：若仍是本条目则摘掉
            """失败拉取不得毒化该键：下一消费者会重试。"""
            if 拉取表.get(会话标识) is 条目:#本条目仍在才删，避免误删新拉取
                del 拉取表[会话标识]#摘掉
        if 是否thenable(承诺):#承诺
            承诺.then(落定成功,落定失败)#挂臂
        else:#已兑现值
            try:#写入
                落定成功(解开(承诺))#快照
            except Exception:#失败
                落定失败()#摘键
        return 承诺#把共享 promise 交给调用方

    def 失效(键):#丢掉一键缓存并中止在飞拉取
        """丢掉一键缓存并中止在飞拉取。"""
        条目=拉取表.get(键)#该键的条目
        if 条目 is None:#没有缓存则无需做
            return#早退
        del 拉取表[键]#摘掉缓存键
        条目['abort']()#中止仍在飞的拉取
        通知词表(键)#词表已空，通知监听者

    def 清空全部():#清空全部会话的目录缓存
        """清空全部会话的目录缓存。"""
        for 键 in list(拉取表.keys()):#快照键后逐个失效
            失效(键)#逐个失效

    翻译=上下文.locale.bind(命名空间)#绑定本插件命名空间的翻译

    def 候选(会话,选项):#按查询过滤本会话技能候选
        """按查询过滤本会话技能候选。"""
        查询=取字段(选项,'query','')#查询串
        信号=取字段(选项,'signal')#中止信号
        技能们=解开(拉目录(取字段(会话,'sessionId')))#共享目录（或加入在飞拉取）
        if 取字段(信号,'aborted'):#被取代的按键：共享拉取仍热着，本调用方让出
            return []#早退
        结果=[]#候选列表
        for 技能 in 技能们:#从落定目录本地过滤
            名=取字段(技能,'name','')#技能名
            if not 名.startswith(查询):#名称前缀匹配查询
                continue#跳过
            描述=取字段(技能,'description','')#描述
            if 取字段(技能,'modelInvocable'):#模型可调则原文
                次要=描述#原文
            else:#仅用户标记骑在 description 上
                次要=翻译('menu.userOnly')+' · '+描述#加「仅用户」前缀
            结果.append({'name':名,'description':次要})#编成菜单候选
        return 结果#候选列表

    def 预热(会话):#作用域诞生时点火即忘预热
        """点火即忘的作用域诞生预热；共享拉取经 candidates 上报。"""
        承诺=拉目录(取字段(会话,'sessionId'))#预热该会话的键
        if 是否thenable(承诺):#承诺
            def 忽略成功(_值=None):#吞掉成功
                """预热失败由 candidates 再报，此处吞掉。"""
                return None#忽略
            def 忽略失败(_错误=None):#吞掉失败
                """预热失败由 candidates 再报，此处吞掉。"""
                return None#忽略
            承诺.then(忽略成功,忽略失败)#吞掉失败

    def 词表(会话):#同步词表：已落定目录的技能名
        """已落定目录的技能名；在飞或失败则缺席。"""
        条目=拉取表.get(取字段(会话,'sessionId'))#缓存
        if 条目 is None:#无
            return None#缺席
        已落定=条目.get('settled')#快照
        if 已落定 is None:#在飞或失败
            return None#缺席
        return [取字段(技能,'name') for 技能 in 已落定]#技能名列表

    def 订阅词表(会话,监听):#登记该会话的词表失效监听者
        """登记该会话的词表失效监听者。"""
        键=取字段(会话,'sessionId')#会话键
        集合=词表监听.get(键)#已有集合
        if 集合 is None:#新建
            集合=set()#空集合
            词表监听[键]=集合#写回映射（新建时必须 set）
        集合.add(监听)#加入本监听者
        def 退订():#退订
            """从该会话集合摘掉。"""
            集合.discard(监听)#从该会话集合摘掉
            if len(集合)==0 and 键 in 词表监听:#空了则摘掉会话键
                del 词表监听[键]#摘掉会话键
        return 退订#拆除器

    def 选定(载荷):#选定：插入字面 /name 加空格
        """纯文本引用决策：选定落下纯文本，提示发出同一字面量。"""
        候选项=取字段(载荷,'candidate')#候选
        return {'text':'/'+取字段(候选项,'name')+' '}#字面 /name 加尾空格

    源={#「/」技能触发源
        'trigger':'/',#触发字符
        'name':'skill',#来源名
        'order':2,#菜单分组顺序
        'candidates':候选,#候选
        'warm':预热,#预热
        'lexicon':词表,#词表
        'subscribeLexicon':订阅词表,#订阅词表
        'onPick':选定,#选定
    }#源结束
    触发服务=上下文.get('inputTriggers')#斜杠触发服务，用来登记本源
    # 预设决定智能体读哪些技能提供方，因此已切换会话的缓存目录属于它不再运行的组合。
    上下文.remote.$on('agent-preset/selected',失效)#预设切换丢掉该会话目录键
    上下文.on('connection/reset',清空全部)#连接重置清空全部（宿主目录可能跨代不同）
    def 挂源():#登记源；拆除时卸源并清缓存
        """把「/」技能源写入花名册。"""
        注销=触发服务.registerSource(源)#登记源
        def 拆除():#fiber 拆除
            """从花名册摘掉本源并清缓存。"""
            注销()#从花名册摘掉本源
            清空全部()#中止在飞拉取并清空缓存
        return 拆除#拆除器
    上下文.effect(挂源,'ui-skill: source')#effect 名

"""技能引用插件的浏览器半边。

登记「/」技能源、词表，以及按键的工具行。候选来自 skill.list RPC，按会话投影 sessionId 寻址。

对齐上游 `ui-skill/src/client/index.ts`。公开面仅中文名。
"""
from cordis.工具 import 已兑现,是否thenable#承诺与可等待判定
from .文案 import 命名空间,中文,英文#词典
from .技能行 import 技能行#技能工具行

__all__=['注入','应用']#仅中文公开名

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
    """登记「/」源、词表，以及按键的工具行。"""
    def 登记词典():#登记中英文案
        """登记本插件词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.effect(登记词典,'ui-skill: dictionaries')#词典生命周期
    def 登记工具行():#登记 skill toolview
        """等 toolview 槽出现再登记 skill 行。"""
        return 上下文.slots.register({#按 skill 键的 toolview 条目
            'name':'tool.call.toolview','key':'skill','locale':命名空间,#条目选项
        },技能行)#技能工具行组件
    上下文.slots.inject('tool.call.toolview',登记工具行)#等槽出现
    连接=上下文.get('connection')#根连接
    技能接口=取字段(取字段(连接,'api'),'skills')#skills RPC
    会话服务=上下文.get('sessions')#会话服务
    拉取表={}#会话 → 在飞/已落定目录拉取
    词表监听={}#会话 → 词表监听者集合

    def 通知词表(会话标识):#通知该会话的词表监听者
        """通知该会话的词表监听者。"""
        for 监听 in list(词表监听.get(会话标识,set())):#快照后逐个通知
            try:#单个监听者失败不得饿死其余
                监听()#触发
            except Exception as 错误:#监听者自己抛了
                print('[ui-skill] lexicon listener failed:',错误)#记日志

    def 拉目录(会话标识):#按会话单飞拉取技能目录
        """按会话单飞拉取技能目录。"""
        if 会话服务.subagentAddress(会话标识) is not None:#子智能体会话
            return 已兑现([])#没有用户技能目录
        已有=拉取表.get(会话标识)#已有拉取
        if 已有 is not None:#同键复用
            return 已有['promise']#共享 promise
        中止器={'aborted':False}#自有中止旗
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
        原始=技能接口.list({'sessionId':会话标识},中止器)#只调一次 skill.list（对齐上游单次 await）
        if 是否thenable(原始):#异步
            承诺=原始.then(解包目录)#链式解包
        else:#同步
            承诺=已兑现(解包目录(原始))#复用同一次结果，禁止二次 list
        条目={'promise':承诺,'abort':中止拉取}#本键共享条目
        拉取表[会话标识]=条目#写入缓存
        def 落定成功(技能们):#成功：写入 settled
            """写入 settled 并通知。"""
            条目['settled']=技能们#同步词表快照
            通知词表(会话标识)#通知
        def 落定失败(_错误=None):#失败：摘键
            """失败拉取不得毒化该键。"""
            if 拉取表.get(会话标识) is 条目:#仍是本条目
                del 拉取表[会话标识]#摘掉
        if 是否thenable(承诺):#承诺
            承诺.then(落定成功,落定失败)#挂臂
        else:#已兑现值
            try:#写入
                落定成功(解开(承诺))#快照
            except Exception:#失败
                落定失败()#摘键
        return 承诺#共享 promise

    def 失效(键):#丢掉一键缓存
        """丢掉一键缓存并中止在飞拉取。"""
        条目=拉取表.get(键)#该键条目
        if 条目 is None:#没有缓存
            return#无需做
        del 拉取表[键]#摘掉
        条目['abort']()#中止
        通知词表(键)#通知

    def 清空全部():#清空全部会话目录缓存
        """清空全部会话的目录缓存。"""
        for 键 in list(拉取表.keys()):#快照键
            失效(键)#逐个失效

    翻译=上下文.locale.bind(命名空间)#绑定翻译

    def 候选(会话,选项):#按查询过滤本会话技能候选
        """按查询过滤本会话技能候选。"""
        查询=取字段(选项,'query','')#查询串
        信号=取字段(选项,'signal')#中止信号
        技能们=解开(拉目录(取字段(会话,'sessionId')))#共享目录
        if 取字段(信号,'aborted'):#菜单已关
            return []#早退
        结果=[]#候选列表
        for 技能 in 技能们:#本地过滤
            名=取字段(技能,'name','')#技能名
            if not 名.startswith(查询):#前缀不匹配
                continue#跳过
            描述=取字段(技能,'description','')#描述
            if 取字段(技能,'modelInvocable'):#模型可调
                次要=描述#原文
            else:#仅用户
                次要=翻译('menu.userOnly')+' · '+描述#加前缀
            结果.append({'name':名,'description':次要})#候选
        return 结果#候选列表

    def 预热(会话):#作用域诞生预热
        """点火即忘的作用域诞生预热。"""
        承诺=拉目录(取字段(会话,'sessionId'))#预热
        if 是否thenable(承诺):#承诺
            def 忽略成功(_值=None):#吞掉成功
                """预热失败由 candidates 再报。"""
                return None#忽略
            def 忽略失败(_错误=None):#吞掉失败
                """预热失败由 candidates 再报。"""
                return None#忽略
            承诺.then(忽略成功,忽略失败)#吞掉失败

    def 词表(会话):#同步词表
        """已落定目录的技能名。"""
        条目=拉取表.get(取字段(会话,'sessionId'))#缓存
        if 条目 is None:#无
            return None#缺席
        已落定=条目.get('settled')#快照
        if 已落定 is None:#在飞或失败
            return None#缺席
        return [取字段(技能,'name') for 技能 in 已落定]#技能名列表

    def 订阅词表(会话,监听):#登记词表失效监听者
        """登记该会话的词表失效监听者。"""
        键=取字段(会话,'sessionId')#会话键
        集合=词表监听.get(键)#已有集合
        if 集合 is None:#新建
            集合=set()#空集合
            词表监听[键]=集合#写回
        集合.add(监听)#加入
        def 退订():#退订
            """从该会话集合摘掉。"""
            集合.discard(监听)#摘掉
            if len(集合)==0 and 键 in 词表监听:#空了
                del 词表监听[键]#摘掉会话键
        return 退订#拆除器

    def 选定(载荷):#选定：插入字面 /name 加空格
        """纯文本引用决策。"""
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
    触发服务=上下文.get('inputTriggers')#斜杠触发服务
    上下文.remote.$on('agent-preset/selected',失效)#预设切换丢掉该会话目录键
    上下文.on('connection/reset',清空全部)#连接重置清空全部
    def 挂源():#登记源；拆除时卸源并清缓存
        """把「/」技能源写入花名册。"""
        注销=触发服务.registerSource(源)#登记源
        def 拆除():#fiber 拆除
            """从花名册摘掉本源并清缓存。"""
            注销()#摘源
            清空全部()#清缓存
        return 拆除#拆除器
    上下文.effect(挂源,'ui-skill: source')#生命周期

"""面向人的 /goal 命令，叠在同会话持久目标域之上。"""
import re#解析 edit 后跟替换陈述
from goal import 目标错误#目标域边界错误

名称='command-goal'#Cordis插件名
注入=['commands','goals']#依赖命令注册表与目标服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
用法='Usage: /goal [<objective>|clear|edit <objective>|pause|resume]'#人类可读用法行
def 取字段(对象,键):#从映射或对象读字段
    """从映射或对象读字段；缺席为 None。"""
    if 对象 is None:#空对象
        return None#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键)#映射键
    return getattr(对象,键,None)#对象属性

def 断言永不可达(值,标签):#封闭联合多出未处理成员时大声失败
    """本地封闭联合多出未处理成员时大声失败。"""
    raise TypeError('unknown '+标签+': '+str(值))#带标签的未知值

def 解析目标命令(原始输入):#把原始输入收成判别联合
    """只解析 /goal 自己拥有的语法；其余任意输入都当作目标陈述。"""
    输入=原始输入.strip()#去掉首尾空白
    if len(输入)==0:#空输入：展示
        return {'kind':'show'}#展示当前目标
    控制=输入.lower()#控制词不区分大小写
    if 控制=='clear':#清除
        return {'kind':'clear'}#清除
    if 控制=='pause':#暂停
        return {'kind':'pause'}#暂停
    if 控制=='resume':#恢复
        return {'kind':'resume'}#恢复
    if 控制=='edit':#只有 edit 没有陈述
        return {'kind':'invalid-edit'}#无效编辑
    if re.match(r'(?iu)^edit(?=\s)',输入):#edit 后跟替换陈述
        return {'kind':'edit','objective':输入[4:].strip()}#替换陈述
    return {'kind':'create','objective':输入}#其余整段当作创建陈述

def 阶段标签(阶段):#阶段 → 展示用英文标签
    """一条持久目标阶段的人类标签。"""
    if 阶段=='active':#活跃
        return 'active'#活跃
    if 阶段=='paused':#已暂停
        return 'paused'#已暂停
    if 阶段=='blocked':#已阻塞
        return 'blocked'#已阻塞
    if 阶段=='complete':#已完成
        return 'complete'#已完成
    return 断言永不可达(阶段,'goal phase')#未处理成员

def 命令提示(目标):#按阶段与武装给出可用命令
    """从某一精确实时状态出发仍有意义的命令提示。"""
    阶段=取字段(目标,'phase')#持久阶段
    if 阶段=='active':#活跃：武装与解除武装提示不同
        if 取字段(目标,'activation')=='armed':#已武装则提示暂停
            return '/goal edit <objective>, /goal pause, /goal clear'#武装中可编辑、暂停、清除
        return '/goal edit <objective>, /goal resume, /goal clear'#未武装可编辑、恢复、清除
    if 阶段=='paused' or 阶段=='blocked':#已暂停或已阻塞
        return '/goal edit <objective>, /goal resume, /goal clear'#可编辑、恢复、清除
    if 阶段=='complete':#已完成
        return '/goal <objective>, /goal clear'#可新建或清除
    return 断言永不可达(阶段,'goal phase')#未处理成员

def 渲染目标(标题,目标):#标题加视图折成成功文本
    """渲染直接 UI 输出，不暴露比较交换内部。"""
    阶段=取字段(目标,'phase')#阶段
    原因=取字段(目标,'blockedReason') if 阶段=='blocked' else None#仅阻塞阶段带原因
    if 阶段=='blocked' and 原因 is None:#缺原因则数据坏了
        raise TypeError('blocked goal is missing its reason')#持久回放应保证阻塞目标带已校验原因
    if 原因 is None:#无阻塞行
        阻塞行=[]#空
    else:#有阻塞行
        阻塞行=['Blocker: '+取字段(原因,'code')+': '+取字段(原因,'message')]#可选阻塞行
    行=[#按行拼给用户
        标题,#操作标题
        'Status: '+阶段标签(阶段),#阶段
        *阻塞行,#阻塞原因，无则空
        'Objective: '+取字段(目标,'objective'),#目标陈述
        'Rounds: '+str(取字段(目标,'roundsStarted'))+'/'+str(取字段(目标,'maxGoalRounds')),#已接纳轮次与上限
        'Activation: '+取字段(目标,'activation'),#进程内武装
        '',#空行分隔
        'Commands: '+命令提示(目标),#下一步可用命令
    ]#行结束
    return {'kind':'success','text':'\n'.join(行)}#成功结果

def 目标引用(目标):#视图 → 比较交换引用
    """当前精确的比较交换引用。"""
    return {'id':取字段(目标,'id'),'revision':取字段(目标,'revision')}#身份加修订

def 缺少目标(动作):#缺当前目标
    """需要当前目标的操作在缺失时的直接错误。"""
    return {#错误结果
        'kind':'error',#命令失败
        'text':'No goal is currently set; /goal '+动作+' requires one. '+用法,#指出需要先有目标
    }#结束错误结果

def 执行目标命令(上下文,调用):#解析并分发
    """把一条已解析的人类命令交给拥有持久化的域执行。"""
    命令=解析目标命令(取字段(调用,'rawInput'))#本命令语法
    try:#域边界可能抛 目标错误
        当前=上下文.goals.get(取字段(调用,'agent'))#该智能体当前目标
        种类=取字段(命令,'kind')#语法判别
        if 种类=='show':#展示
            if 当前 is None:#没有当前目标
                return {'kind':'success','text':'No goal is currently set.\n'+用法}#空状态加用法
            return 渲染目标('Goal',当前)#渲染当前目标
        if 种类=='invalid-edit':#edit 缺陈述
            return {'kind':'error','text':'Goal editing requires a replacement objective.\n'+用法}#要求替换陈述
        if 种类=='create':#创建
            if 当前 is not None and 取字段(当前,'phase')!='complete':#未完成目标还在
                return {#拒绝覆盖
                    'kind':'error',#命令失败
                    'text':'A goal is already '+阶段标签(取字段(当前,'phase'))+'. Use /goal edit <objective> to change it or /goal clear before replacing it.',#须先编辑或清除
                }#结束拒绝覆盖
            return 渲染目标('Goal created',上下文.goals.create(取字段(调用,'agent'),{'objective':取字段(命令,'objective')}))#创建并渲染
        if 种类=='edit':#编辑
            if 当前 is None:#没有可编辑的目标
                return 缺少目标('edit')#缺目标
            if 取字段(当前,'phase')=='complete':#已完成则改为新建
                return 渲染目标('Goal created',上下文.goals.create(取字段(调用,'agent'),{'objective':取字段(命令,'objective')}))#完成后重建
            return 渲染目标(#就地编辑
                'Goal updated',#更新标题
                上下文.goals.edit(取字段(调用,'agent'),目标引用(当前),{'objective':取字段(命令,'objective')}),#比较交换编辑
            )#结束更新渲染
        if 种类=='pause':#暂停
            if 当前 is None:#没有可暂停的目标
                return 缺少目标('pause')#缺目标
            return 渲染目标('Goal paused',上下文.goals.pause(取字段(调用,'agent'),目标引用(当前)))#暂停并渲染
        if 种类=='resume':#恢复
            if 当前 is None:#没有可恢复的目标
                return 缺少目标('resume')#缺目标
            return 渲染目标('Goal resumed',上下文.goals.resume(取字段(调用,'agent'),目标引用(当前)))#恢复并渲染
        if 种类=='clear':#清除
            if 当前 is None:#本来就没有
                return {'kind':'success','text':'No goal to clear.'}#空清除
            上下文.goals.clear(取字段(调用,'agent'),目标引用(当前))#留下墓碑
            return {'kind':'success','text':'Goal cleared.'}#清除成功
        return 断言永不可达(命令,'goal command')#未处理成员
    except 目标错误:#合法的状态拒绝
        return {#把域错误收成命令错误
            'kind':'error',#命令失败
            'text':'The goal command is not valid for the current state. Run /goal to view available commands.',#让用户先看当前状态
        }#结束域拒绝

def 应用(上下文):#注册 /goal
    """为每个已组合的命令适配器注册 Codex 形 /goal 命令。"""
    def 处理(调用):#把调用交给本解析器
        return 执行目标命令(上下文,调用)#解析并分发
    上下文.commands.register({#挂到命令注册表
        'name':'goal',#斜杠命令名
        'description':'set or view the goal for a long-running task',#面向人的简述
        'input':{'hint':'[<objective>|clear|edit <objective>|pause|resume]'},#输入提示
        'handler':处理,#把调用交给本解析器
    })#结束注册

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出

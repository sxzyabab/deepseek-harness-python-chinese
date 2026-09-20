"""本包拥有的持久工作流记录不变量。"""
from ...内核.会话 import 安全整数上限#外来 JSON 安全整数上限
包名='@deepseek-ai/dsh-tool-workflow'#本包在不变量注册表中的名字
名称='tool-workflow-invariant'#配套插件名
依赖=['invariants']#依赖不变量服务

__all__=['包名','名称','依赖','安装','应用']#仅中文公开名

def 是否工作流记录事件(事件):#判断是否为本包记录事件
    """本包是否拥有这条候选 Session 事件。事件是 dict。"""
    return str(事件['type']).startswith('tool-workflow/')#按事件类型前缀识别

def 字符串标识(值,标签,失败):#把未知值校成非空字符串身份
    """要求持久不透明身份是非空字符串。"""
    if not isinstance(值,str) or len(值)==0:#类型或长度不对；判 length
        失败(标签+' must be a non-empty string')#身份不变量失败
    return 值#返回已校验字符串

def 成员序号(值,失败):#把未知值校成从 1 起的序号
    """要求一名工作流成员的从 1 起的序号身份。持久日志是外来 JSON，在此校验安全整数。"""
    if isinstance(值,bool):#布尔不是整数
        合法=False#非法
    elif isinstance(值,int):#整数
        合法=abs(值)<=安全整数上限#安全范围
    elif isinstance(值,float) and 值.is_integer():#整值浮点
        合法=abs(值)<=安全整数上限#安全范围
    else:#其它
        合法=False#非法
    if (not 合法) or 值<1:#不是从 1 起的安全整数
        失败('tool-workflow member seq must be a positive safe integer')#序号不变量失败
    return int(值)#收成 int

def 载荷对象(事件,失败):#把事件 data 校成 JSON 对象
    """读取一个普通载荷字段，不信任还原出的插件数据。事件是 dict。"""
    数据=事件['data'] if 'data' in 事件 else None#取出原始载荷
    if 数据 is None or (not isinstance(数据,dict)):#不是普通对象
        失败(str(事件['type'])+' data must be a JSON object')#载荷形态失败
    return 数据#返回对象形态载荷

def 为事件克隆追踪(来源,事件,失败):#为即将折叠的事件克隆可变运行槽
    """只复制当前候选会改动的那条运行；其余已提交状态保持共享。事件是 dict。"""
    追踪=dict(来源)#浅拷贝运行表
    if 事件['type']=='tool-workflow/run-start':#start 只新增条目
        return 追踪#无需深拷贝已有运行
    数据=载荷对象(事件,失败)#读取载荷
    运行号=字符串标识(数据['runId'] if 'runId' in 数据 else None,str(事件['type'])+' runId',失败)#取出运行标识
    运行=来源[运行号] if 运行号 in 来源 else None#查找已有运行
    if 运行 is not None:#该运行已存在
        追踪[运行号]={'ended':运行['ended'],'members':dict(运行['members'])}#深拷贝该运行的成员表
    return 追踪#返回候选折叠用副本

def 开放运行(追踪,运行号,事件类型,失败):#取出仍开放的运行追踪
    """要求具名运行存在且仍未关闭。追踪是 dict。"""
    运行=追踪[运行号] if 运行号 in 追踪 else None#按 id 查找
    if 运行 is None:#没有对应 start
        失败(事件类型+' has no matching tool-workflow/run-start for run '+运行号)#没有对应 start 则失败
    if 运行['ended'] is True:#已结束后又来事件
        失败(事件类型+' appears after tool-workflow/run-end for run '+运行号)#已结束后又来事件则失败
    return 运行#返回仍开放的运行

def 应用事件(追踪,事件,失败):#按事件类型更新折叠状态
    """用一条相关 Session 事件推进工作流记录折叠。事件是 dict。"""
    数据=载荷对象(事件,失败)#读取载荷对象
    事件类型=事件['type']#事件类型
    运行号=字符串标识(数据['runId'] if 'runId' in 数据 else None,str(事件类型)+' runId',失败)#取出运行标识
    if 事件类型=='tool-workflow/run-start':#打开一条运行记录
        名称=数据['name'] if 'name' in 数据 else None#展示名称
        if not isinstance(名称,str) or len(名称)==0:#名称不是非空字符串；判 length
            失败('tool-workflow/run-start name must be a non-empty string')#名称不变量失败
        if 运行号 in 追踪:#重复运行 id
            失败('tool-workflow/run-start repeats run '+运行号)#重复运行 id 则失败
        追踪[运行号]={'ended':False,'members':{}}#登记新的开放运行
        return#start 处理结束
    if 事件类型=='tool-workflow/agent-start':#记录一名成员开始
        运行=开放运行(追踪,运行号,事件类型,失败)#取出仍开放的运行
        序号=成员序号(数据['seq'] if 'seq' in 数据 else None,失败)#校验成员序号
        标签=数据['label'] if 'label' in 数据 else None#展示标签
        if not isinstance(标签,str):#标签必须是字符串
            失败('tool-workflow/agent-start label must be a string')#标签失败
        if 'phase' in 数据 and 数据['phase'] is not None and (not isinstance(数据['phase'],str)):#出现了非字符串 phase
            失败('tool-workflow/agent-start phase must be a string when present')#阶段字段失败
        字符串标识(数据['childId'] if 'childId' in 数据 else None,'tool-workflow/agent-start childId',失败)#子会话 id 必须非空
        if 序号 in 运行['members']:#重复成员序号
            失败('tool-workflow/agent-start repeats member seq '+str(序号)+' in run '+运行号)#重复成员序号则失败
        运行['members'][序号]=False#记为尚未结束
        return#成员开始处理结束
    if 事件类型=='tool-workflow/agent-end':#记录一名成员结算
        运行=开放运行(追踪,运行号,事件类型,失败)#取出仍开放的运行
        序号=成员序号(数据['seq'] if 'seq' in 数据 else None,失败)#校验成员序号
        结局=数据['outcome'] if 'outcome' in 数据 else None#成员结局
        if 结局!='completed' and 结局!='failed' and 结局!='cancelled':#结局不在封闭联合内
            失败('tool-workflow/agent-end outcome '+str(结局)+' is invalid')#未知结局则失败
        if 序号 not in 运行['members']:#没有配对开始
            失败('tool-workflow/agent-end has no matching member seq '+str(序号)+' in run '+运行号)#没有配对开始则失败
        if 运行['members'][序号] is True:#重复结束
            失败('tool-workflow/agent-end repeats member seq '+str(序号)+' in run '+运行号)#重复结束则失败
        运行['members'][序号]=True#记为已结束
        return#成员结束处理结束
    if 事件类型=='tool-workflow/run-end':#关闭一条运行记录
        运行=开放运行(追踪,运行号,事件类型,失败)#取出仍开放的运行
        停止原因=数据['stopReason'] if 'stopReason' in 数据 else None#停止原因
        if 停止原因!='completed' and 停止原因!='cancelled' and 停止原因!='error':#停止原因不在封闭联合内
            失败('tool-workflow/run-end stopReason '+str(停止原因)+' is invalid')#未知停止原因则失败
        开放成员=[序号 for 序号,已结束 in 运行['members'].items() if 已结束 is False]#尚未结束的成员序号
        if len(开放成员)>0:#仍有未结算成员；判 length
            失败('tool-workflow/run-end leaves member seq '+', '.join(str(序号) for 序号 in 开放成员)+' open in run '+运行号)#带着开放成员关闭则失败
        运行['ended']=True#标记运行已结束
        运行['members'].clear()#清空成员表
        return#运行结束处理结束
    失败('unknown tool-workflow event type '+str(事件类型))#未知类型则失败

def 安装(上下文,失败):#把记录不变量装到上下文上
    """为每个已挂接 Session 安装独立的增量折叠。"""
    追踪表={}#会话身份到折叠状态，键为 id(会话)
    暂存={}#派发阶段暂存的候选折叠（键为 id(事件)）

    def 播种(会话):#用已有事件播种折叠
        """用已有事件播种折叠。会话是对象。"""
        追踪={}#空折叠表
        for 事件 in 会话.events:#回放已有事件
            if 是否工作流记录事件(事件):#本包记录事件
                应用事件(追踪,事件,失败)#折叠
        追踪表[id(会话)]=追踪#保存该会话折叠
        return 追踪#返回播种结果

    def 取追踪(会话):#取出或播种
        """取出或播种。会话是对象。"""
        键=id(会话)#会话身份
        if 键 in 追踪表:#已有
            return 追踪表[键]#已提交折叠
        return 播种(会话)#补种子

    for 会话 in 上下文.sessions.list():#为已有会话播种
        播种(会话)#播种
    def 会话已创建(会话,*其余):#新会话立即播种
        """新会话立即播种。"""
        _=其余#额外参数不用
        播种(会话)#播种
    def 内部派发(模式,事件名,参数,*其余):#在发布前预检会话事件
        """提交前预检会话事件。"""
        _=模式#派发模式不用
        _=其余#额外参数不用
        if 事件名!='session/event':#只关心会话事件
            return#放过
        会话=参数[0]#取出会话
        事件=参数[1]#取出事件
        if not 是否工作流记录事件(事件):#非本包事件跳过
            return#放过
        追踪=为事件克隆追踪(取追踪(会话),事件,失败)#为候选事件克隆可变槽
        应用事件(追踪,事件,失败)#在副本上折叠
        暂存[id(事件)]={'session':会话,'trace':追踪}#暂存以便正式发布提交
    def 会话事件(会话,事件,*其余):#正式发布时提交折叠
        """正式发布时提交折叠。"""
        _=其余#额外参数不用
        if not 是否工作流记录事件(事件):#非本包事件跳过
            return#放过
        候选=暂存[id(事件)] if id(事件) in 暂存 else None#取出派发阶段暂存
        if 候选 is None or 候选['session'] is not 会话:#没有匹配的预检结果
            return 失败('session/event reached publication without matching workflow-record validation')#未经预检就发布则失败
        暂存.pop(id(事件),None)#丢掉暂存
        追踪表[id(会话)]=候选['trace']#提交折叠
    上下文.监听('session/created',会话已创建,{'全局':True})#新会话立即播种
    上下文.监听('internal/dispatch',内部派发,{'全局':True})#全局监听派发
    上下文.监听('session/event',会话事件,{'全局':True})#全局监听会话事件

安装.inject=['sessions']#安装器还依赖 sessions 服务

def 应用(上下文):#把本包不变量登记到上下文
    """注册本包的不变量配套。携带不变量服务的 Cordis 上下文。返回安装成功后该登记的拆除器。"""
    return 上下文.invariants.register(包名,安装)#同步登记

name=名称#Cordis 插件名槽
inject=依赖#Cordis 依赖槽
apply=应用#Cordis 入口槽

"""会话事件日志的包内关系不变量。对齐上游 `session/src/invariant.ts`。公开面仅中文名。"""
from ...依赖 import cordis#外部依赖胶水
from ...模型后端.llm.永不 import 断言永不#导入穷尽检查
from .修复 import 工具未启动#导入工具未启动错误码
from ..作用域 import 弱身份表#导入按身份存取的弱表

包名='@deepseek-ai/dsh-session'#本包名
名称='session-invariant'#配套插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis插件名（协议槽）
inject=注入#Cordis依赖声明（协议槽）

__all__=['包名','名称','注入','安装','应用','空踪迹','校验事件','应用变迁']#仅中文公开名

def 取字段(对象,键):#读取字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    if 对象 is None:#无对象
        return None#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键)#映射键
    return getattr(对象,键,None)#对象属性

def 要求打开步骤(踪迹,种类,轮次,步骤,失败):#要求步骤打开
    """断言步骤作用域事件点名的是当前打开的轮次与步骤。"""
    if 踪迹['openTurn']!=轮次 or 踪迹['openStep']!=步骤:#与打开的轮次/步骤不符
        失败(种类+' names turn '+str(轮次)+'/step '+str(步骤)+' but open is turn '+str(踪迹['openTurn'])+'/step '+str(踪迹['openStep']))#点名与打开不一致

def 校验事件(踪迹,事件,失败):#纯校验并返回变迁
    """校验一条候选事件，不改已提交踪迹。"""
    序号=取字段(事件,'seq')#事件序号
    if 序号<=踪迹['lastSeq']:#序号未严格递增
        失败('seq must strictly increase: saw '+str(序号)+' after '+str(踪迹['lastSeq']))#序号必须递增
    打开轮次=踪迹['openTurn']#下一打开轮次
    打开步骤=踪迹['openStep']#下一打开步骤
    下一轮次=踪迹['nextTurn']#下一轮次号
    下一步骤=踪迹['nextStep']#下一步骤号
    待完成={'kind':'none'}#默认不改调用集
    种类=取字段(事件,'type')#事件类型
    数据=取字段(事件,'data')#载荷
    if 种类=='turn/start':#轮次开始
        轮次=取字段(数据,'turn')#事件轮次
        if 踪迹['openTurn'] is not None:#已有打开轮次
            失败('turn/start '+str(轮次)+' while turn '+str(踪迹['openTurn'])+' is still open')#不得嵌套打开
        if 轮次!=踪迹['nextTurn']:#轮次号不连续
            失败('turn/start expected turn '+str(踪迹['nextTurn'])+', got '+str(轮次))#必须是下一号
        打开轮次=轮次#打开该轮次
        下一步骤=1#步骤从 1 起
    elif 种类=='turn/end':#轮次结束
        轮次=取字段(数据,'turn')#事件轮次
        if 踪迹['openTurn']!=轮次:#结束的不是打开轮次
            失败('turn/end '+str(轮次)+' does not match open turn '+str(踪迹['openTurn']))#必须匹配打开轮次
        if 踪迹['openStep'] is not None:#步骤仍打开
            失败('turn/end '+str(轮次)+' while step '+str(踪迹['openStep'])+' is still open')#结束前必须关步骤
        打开轮次=None#关闭轮次
        下一轮次=下一轮次+1#下一轮次号加一
    elif 种类=='step/start':#步骤开始
        轮次=取字段(数据,'turn')#事件轮次
        步骤=取字段(数据,'step')#事件步骤
        if 踪迹['openTurn']!=轮次:#不在打开轮次里
            失败('step/start in turn '+str(轮次)+' but open turn is '+str(踪迹['openTurn']))#必须在打开轮次
        if 踪迹['openStep'] is not None:#已有打开步骤
            失败('step/start '+str(步骤)+' while step '+str(踪迹['openStep'])+' is still open')#不得嵌套打开
        if 步骤!=踪迹['nextStep']:#步骤号不连续
            失败('step/start expected step '+str(踪迹['nextStep'])+' in turn '+str(轮次)+', got '+str(步骤))#必须是下一号
        打开步骤=步骤#打开该步骤
    elif 种类=='step/end':#步骤结束
        要求打开步骤(踪迹,'step/end',取字段(数据,'turn'),取字段(数据,'step'),失败)#必须点名打开步骤
        待完成={'kind':'clear'}#清空未完成调用
        打开步骤=None#关闭步骤
        下一步骤=下一步骤+1#下一步骤号加一
    elif 种类=='assistant/chunk':#助手块
        要求打开步骤(踪迹,'assistant/chunk',取字段(数据,'turn'),取字段(数据,'step'),失败)#必须在打开步骤
    elif 种类=='assistant/message':#助手消息
        要求打开步骤(踪迹,'assistant/message',取字段(数据,'turn'),取字段(数据,'step'),失败)#必须在打开步骤
    elif 种类=='tool/call':#工具调用
        要求打开步骤(踪迹,'tool/call',取字段(数据,'turn'),取字段(数据,'step'),失败)#必须在打开步骤
        待完成={'kind':'add','callId':取字段(数据,'callId')}#记下未完成调用
    elif 种类=='tool/result':#工具结果
        if 试取(事件,'surfaceOp')!='append':#表面替换而非追加
            if 踪迹['openTurn'] is None:#没有打开轮次
                失败('tool/result surface replacement appended outside any open turn')#替换必须在轮次内
        else:#追加
            要求打开步骤(踪迹,'tool/result',取字段(数据,'turn'),取字段(数据,'step'),失败)#追加必须在打开步骤
            消息=取字段(数据,'message')#结果消息
            来源=取字段(消息,'source')#工具来源
            调用号=取字段(来源,'callId')#结果对应的调用
            内容=取字段(消息,'content')#内容块
            块=内容[0]#第一块
            错误=试取(数据,'error')#可选错误身份
            合成未启动=试取(块,'isError') is True and 试取(错误,'code')==工具未启动#合成的未启动错误
            if (调用号 not in 踪迹['pendingCalls']) and (not 合成未启动):#既无先前调用也不是合成未启动
                失败('tool/result for '+str(调用号)+' with no prior tool/call in this step')#本步必须先有 tool/call
            待完成={'kind':'delete','callId':调用号}#从待完成集删掉
    elif 种类=='user/message':#用户消息
        pass#无额外关系
    elif 种类=='session/end-seed':#种子结束
        pass#无约束
    elif 种类=='todo/write' or 种类=='request/header' or 种类=='request/context':#核心执行事件
        if 踪迹['openTurn'] is None:#没有打开轮次
            失败(种类+' appended outside any open turn (core execution events must be turn-enclosed)')#核心执行事件必须包在轮次内
    else:#可合并扩展的事件
        pass#可合并扩展的事件关系归其拥有插件
    return {#构造变迁
        'scalars':{#标量下一状态
            'lastSeq':序号,#上次序号
            'openTurn':打开轮次,#打开轮次
            'openStep':打开步骤,#打开步骤
            'nextTurn':下一轮次,#下一轮次号
            'nextStep':下一步骤,#下一步骤号
        },#标量下一状态
        'pendingCalls':待完成,#调用集变更
    }#变迁

def 应用变迁(踪迹,变迁):#应用变迁
    """在事件提交后应用一条已校验变迁。"""
    标量=变迁['scalars']#标量字段
    踪迹['lastSeq']=标量['lastSeq']#写入序号
    踪迹['openTurn']=标量['openTurn']#写入打开轮次
    踪迹['openStep']=标量['openStep']#写入打开步骤
    踪迹['nextTurn']=标量['nextTurn']#写入下一轮次
    踪迹['nextStep']=标量['nextStep']#写入下一步骤
    变更=变迁['pendingCalls']#调用集变更
    种=变更['kind']#变更种类
    if 种=='none':#无变更
        pass#无变更
    elif 种=='add':#增加调用
        踪迹['pendingCalls'].add(变更['callId'])#加入待完成
    elif 种=='delete':#删除调用
        踪迹['pendingCalls'].discard(变更['callId'])#移出待完成
    elif 种=='clear':#清空
        踪迹['pendingCalls'].clear()#清掉本步调用
    else:#封闭联合穷尽
        断言永不(变更,'session trace pending-call transition')#不可达

def 空踪迹():#空踪迹
    """每个会话用于关系日志检查的空账本。"""
    return {#空踪迹
        'lastSeq':-1,#尚无序号
        'openTurn':None,#无打开轮次
        'openStep':None,#无打开步骤
        'nextTurn':1,#下一轮从 1
        'nextStep':1,#下一步从 1
        'pendingCalls':set(),#无待完成调用
    }#空踪迹

def 安装(上下文对象,失败):#安装会话不变量
    """把会话贡献安装进其子注册光纤。"""
    踪迹表=弱身份表()#各会话踪迹
    暂存表=弱身份表()#提交前暂存的变迁
    def 播种会话(会话):#从已有日志播种
        """从已有日志播种。"""
        踪迹=空踪迹()#空踪迹
        踪迹表.设(会话,踪迹)#挂上会话
        for 事件 in 会话.events:#回放已有事件
            应用变迁(踪迹,校验事件(踪迹,事件,失败))#校验并提交
        return 踪迹#返回踪迹
    def 取踪迹(会话):#取踪迹
        """取踪迹，缺则播种。"""
        已有=踪迹表.取(会话)#已有踪迹
        if 已有 is None:#缺
            return 播种会话(会话)#缺则播种
        return 已有#已有
    for 会话 in 上下文对象.sessions.列出():#已有会话
        播种会话(会话)#为已有会话播种
    def 新会话(载体,会话,*位置参数):#新会话播种
        """新会话播种。派发 this 是载体。"""
        播种会话(会话)#播种
    上下文对象.on('session/created',新会话,{'global':True})#新会话播种
    def 提交事件(载体,会话,事件,*位置参数):#事件发表后提交变迁
        """事件发表后提交变迁。派发 this 是载体。"""
        暂存=暂存表.取(事件)#取出暂存
        if 暂存 is None or 暂存['session'] is not 会话:#没有匹配的提交前校验
            return 失败('session/event reached publication without matching pre-commit validation')#发表前必须已校验
        暂存表.设(事件,None)#清掉暂存
        应用变迁(暂存['trace'],暂存['transition'])#应用到踪迹
    上下文对象.on('session/event',提交事件,{'global':True})#全局监听
    def 派发钩子(_模式,事件名,参数,*其余):#派发时先纯校验
        """派发时先纯校验。"""
        if 事件名!='session/event':#只看会话事件
            return#只看会话事件
        会话=参数[0]#会话
        事件=参数[1]#事件
        踪迹=取踪迹(会话)#取踪迹
        变迁=校验事件(踪迹,事件,失败)#纯校验
        暂存表.设(事件,{'session':会话,'trace':踪迹,'transition':变迁})#暂存待提交
    上下文对象.on('internal/dispatch',派发钩子,{'global':True})#全局监听

安装.inject=['sessions']#安装时还要 sessions（Cordis 安装器协议槽）

def 应用(上下文对象):#注册会话不变量配套
    """注册会话不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记贡献并返回已兑现拆除器

apply=应用#Cordis插件入口（协议槽）

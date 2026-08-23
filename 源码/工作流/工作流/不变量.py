"""本包拥有的工作流生命周期不变量。"""
import json#元数据快照序列化
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器
from ...内核.会话 import 是否安全整数#对齐 JS Number.isSafeInteger

包名='@deepseek-ai/dsh-workflow'#本包在不变量注册表中的名字
名称='workflow-invariant'#配套插件名
注入=['invariants']#依赖不变量服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 元数据快照(元数据):#把元数据打成可比较的 JSON 快照
    """把运行身份里的 meta 块序列化，供跨事件比对是否漂移。"""
    return json.dumps(元数据,ensure_ascii=False,separators=(',',':'))#紧凑 JSON，键序保持插入序

def 取追踪(追踪表,信息,失败):#按运行身份取出追踪；对不上则失败
    """要求某次运行的每条事件都保留其已校验的身份快照。"""
    运行号=取字段(信息,'id')#事件携带的运行 id
    追踪=追踪表.get(运行号)#按运行 id 查找追踪
    if 追踪 is None:#没有对应 start
        失败('workflow event has no matching workflow/start for run '+json.dumps(运行号,ensure_ascii=False))#没有对应 start 则失败
    if 追踪['meta']!=元数据快照(取字段(信息,'meta')):#元数据与 start 时不一致
        失败('workflow event meta diverges from workflow/start for run '+json.dumps(运行号,ensure_ascii=False))#元数据漂移则失败
    return 追踪#返回匹配的追踪

def 校验智能体结束(开始,结束,失败):#校验 agent-end 与 agent-start 身份一致
    """断言智能体成对事件共享的不可变身份字段。"""
    if 取字段(开始,'label')!=取字段(结束,'label') or 取字段(开始,'phase')!=取字段(结束,'phase') or 取字段(开始,'childId')!=取字段(结束,'childId'):#标签、阶段或子 id 不一致
        失败('workflow/agent-end identity diverges from workflow/agent-start for seq '+str(取字段(结束,'seq')))#身份漂移则失败
    结局=取字段(结束,'outcome')#取出结局字符串
    if 结局!='completed' and 结局!='failed' and 结局!='cancelled':#结局不在封闭联合内
        失败('workflow/agent-end carries unknown outcome '+json.dumps(结局,ensure_ascii=False))#未知结局则失败

def 校验工作流结束(追踪,结果,失败):#校验 workflow/end 与追踪一致
    """用累计运行追踪校验终态结果。"""
    if len(追踪['agents'])>0:#仍有未配对的智能体调用
        失败('workflow/end has '+str(len(追踪['agents']))+' agent call(s) without workflow/agent-end')#未配对则失败
    已开始=取字段(结果,'agentsStarted')#结果里的智能体计数
    if not 是否安全整数(已开始) or 已开始<追踪['starts']:#计数不是安全整数或小于已观察开始次数
        失败('workflow/end agentsStarted must be a safe integer covering every observed agent start')#智能体计数不变量失败
    停止原因=取字段(结果,'stopReason')#停止原因
    缺席=object()#探测 error 是否缺席（对齐 JS undefined）
    if isinstance(结果,dict):#映射载荷
        错误值=结果['error'] if 'error' in 结果 else 缺席#有键才取值，否则缺席
    else:#对象载荷
        错误值=getattr(结果,'error',缺席)#属性缺席用哨兵
    if 停止原因=='completed':#完成不得带 error
        if 错误值 is not 缺席:#显式给出了 error（含 None）
            失败('workflow/end error must be absent exactly for completed runs')#error 字段与停止原因不匹配
    elif not isinstance(错误值,str):#非完成必须是字符串
        失败('workflow/end error must be absent exactly for completed runs')#error 字段与停止原因不匹配

def 安装(上下文对象,失败):#把工作流不变量装到上下文上
    """安装工作流 start/end 与子调用配对检查。"""
    追踪表={}#运行 id 到追踪的表
    暂存开始=set()#dispatch 阶段暂存的 start 身份对象 id()（对齐上游 WeakSet；dict 不可弱引用）
    暂存智能体开始=set()#dispatch 阶段暂存的智能体开始对象 id()
    暂存智能体结束=set()#dispatch 阶段暂存的智能体结束对象 id()
    暂存结束=set()#dispatch 阶段暂存的运行结束对象 id()

    def 内部派发(_模式,事件名,参数,*其余):#在派发前预检工作流事件
        """提交前预检 workflow/* 事件。"""
        if 事件名=='workflow/start':#处理运行开始
            信息=参数[0]#取出运行身份
            元数据=取字段(信息,'meta')#取出元数据
            if len(str(取字段(信息,'id')))==0 or len(str(取字段(元数据,'name')))==0 or len(str(取字段(元数据,'description')))==0:#id、名称或描述为空
                失败('workflow/start id, meta.name, and meta.description must be non-empty')#空身份字段则失败
            if 取字段(信息,'id') in 追踪表:#重复运行 id
                失败('workflow/start repeated run id '+json.dumps(取字段(信息,'id'),ensure_ascii=False))#重复运行 id 则失败
            暂存开始.add(id(信息))#暂存该次 start 以便正式监听提交
            return#start 预检结束
        if not str(事件名).startswith('workflow/'):#非工作流事件直接跳过
            return#放过
        信息=参数[0]#其余工作流事件的运行身份
        追踪=取追踪(追踪表,信息,失败)#必须已有对应 start
        if 事件名=='workflow/agent-start':#处理智能体开始
            智能体=参数[1]#取出智能体调用身份
            序号=取字段(智能体,'seq')#调用序号
            if not 是否安全整数(序号) or 序号<1 or len(str(取字段(智能体,'childId')))==0:#序号非法或子 id 为空
                失败('workflow/agent-start seq must be positive and childId must be non-empty')#智能体开始字段失败
            if 序号 in 追踪['agents']:#重复序号
                失败('workflow/agent-start repeated seq '+str(序号))#重复序号则失败
            暂存智能体开始.add(id(智能体))#暂存以便正式监听提交
            return#智能体开始预检结束
        if 事件名=='workflow/agent-end':#处理智能体结束
            智能体=参数[1]#取出智能体结束信息
            开始=追踪['agents'].get(取字段(智能体,'seq'))#查找对应开始
            if 开始 is None:#没有配对开始
                失败('workflow/agent-end has no matching start for seq '+str(取字段(智能体,'seq')))#没有配对开始则失败
                return#已失败
            校验智能体结束(开始,智能体,失败)#校验身份字段
            暂存智能体结束.add(id(智能体))#暂存以便正式监听提交
            return#智能体结束预检结束
        if 事件名=='workflow/end':#处理运行结束
            结果=参数[1]#取出对外结果摘要
            校验工作流结束(追踪,结果,失败)#校验终态与追踪
            暂存结束.add(id(结果))#暂存以便正式监听提交
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听派发

    def 提交开始(信息,*其余):#提交运行开始追踪
        """正式监听：登记该运行的追踪。"""
        # v8 ignore next -- internal/dispatch stages the same run-info object
        if id(信息) not in 暂存开始:#未经派发预检的对象直接忽略
            return#忽略
        暂存开始.discard(id(信息))#消费暂存
        追踪表[取字段(信息,'id')]={'meta':元数据快照(取字段(信息,'meta')),'agents':{},'starts':0}#登记该运行的追踪
    上下文对象.on('workflow/start',提交开始,{'global':True})#全局监听运行开始

    def 提交智能体开始(信息,智能体,*其余):#提交智能体开始
        """正式监听：记下尚未配对结束的调用。"""
        # v8 ignore next -- internal/dispatch stages the same agent object
        if id(智能体) not in 暂存智能体开始:#未经派发预检的对象直接忽略
            return#忽略
        暂存智能体开始.discard(id(智能体))#消费暂存
        追踪=取追踪(追踪表,信息,失败)#取出该运行追踪
        追踪['agents'][取字段(智能体,'seq')]=智能体#记下尚未配对结束的调用
        追踪['starts']+=1#累计开始次数
    上下文对象.on('workflow/agent-start',提交智能体开始,{'global':True})#全局监听智能体开始

    def 提交智能体结束(信息,智能体,*其余):#提交智能体结束
        """正式监听：配对完成后移除该调用。"""
        # v8 ignore next -- internal/dispatch stages the same agent object
        if id(智能体) not in 暂存智能体结束:#未经派发预检的对象直接忽略
            return#忽略
        暂存智能体结束.discard(id(智能体))#消费暂存
        取追踪(追踪表,信息,失败)['agents'].pop(取字段(智能体,'seq'),None)#配对完成后移除该调用
    上下文对象.on('workflow/agent-end',提交智能体结束,{'global':True})#全局监听智能体结束

    def 提交结束(信息,结果,*其余):#提交运行结束
        """正式监听：运行结束后丢弃追踪。"""
        # v8 ignore next -- internal/dispatch stages the same result object
        if id(结果) not in 暂存结束:#未经派发预检的对象直接忽略
            return#忽略
        暂存结束.discard(id(结果))#消费暂存
        追踪表.pop(取字段(信息,'id'),None)#运行结束后丢弃追踪
    上下文对象.on('workflow/end',提交结束,{'global':True})#全局监听运行结束

def 应用(上下文对象):#把本包不变量登记到上下文
    """注册工作流不变量配套。携带不变量服务的 Cordis 上下文。返回安装成功后该登记的 disposer。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#同步登记并包成 Promise

apply=应用#Cordis 插件入口

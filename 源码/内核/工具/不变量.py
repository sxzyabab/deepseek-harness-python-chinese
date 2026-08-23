"""工具管线的包内不变量。对齐上游 `@deepseek-ai/dsh-tools/invariant`。公开面仅中文名；Cordis 加载槽 `name`/`inject`/`apply` 为协议兼容别名，不入 `__all__`。"""
from ..llm.调用配置 import 是否冻结#导入冻结判定
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#导入立刻兑现的拆除器
from ..作用域 import 弱身份表#导入按身份存取的弱表

包名='@deepseek-ai/dsh-tools'#本包名
名称='tools-invariant'#配套插件名
注入=['invariants']#依赖 invariants 服务
name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖声明槽

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键):
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):
        return 对象[键]#映射键
    return getattr(对象,键)#对象属性

def 试取(对象,键):
    """读取可选字段，缺席为 None。"""
    if isinstance(对象,dict):
        return 对象.get(键)#映射键
    return getattr(对象,键,None)#对象属性

def 校验结果(执行,结果,失败):
    """校验不可变的最终执行/结果快照：执行与结果及内容都必须已冻结，且带非空 name 与 callId。"""
    if not 是否冻结(执行):
        失败('tools/result execution must be frozen before publication')#执行必须冻结
    内容=试取(结果,'content')#结果内容
    if (not 是否冻结(结果)) or (not 是否冻结(内容)):
        失败('tools/result outcome and content must be frozen before publication')#结果与内容必须冻结
    名称值=试取(执行,'name')#工具名
    调用号=试取(执行,'callId')#调用 id
    if (not isinstance(名称值,str)) or len(名称值)==0 or len(str(调用号))==0:
        失败('tools/result execution must carry non-empty name and callId')#名称与调用 id 不得为空

def 安装(上下文对象,失败):
    """安装单调管线、最终快照与代码派发封闭检查。"""
    阶段表=弱身份表()#每次执行的管线阶段
    打开轮次表=弱身份表()#各会话当前打开轮次
    派发根表=弱身份表()#子调用到根调用的映射
    def 校验派发(会话对象,事件):
        """校验代码派发事件的根/父/子封闭关系。"""
        种类=试取(事件,'type')#事件类型
        if 种类!='tool/code-dispatch-start' and 种类!='tool/code-dispatch':
            return#非派发事件放过
        数据=试取(事件,'data')#载荷
        根=str(试取(数据,'rootCallId'))#根调用 id
        父=str(试取(数据,'parentCallId'))#父调用 id
        子=str(试取(数据,'subCallId'))#子调用 id
        if len(根)==0 or len(父)==0 or len(子)==0:
            失败(种类+' must carry non-empty rootCallId, parentCallId, and subCallId')#三个 id 都不得为空
            return#已失败
        根映射=派发根表.取(会话对象)#该会话已见映射
        已知=根映射.get(子) if 根映射 is not None else None#该子调用已知根
        if 已知 is not None and 已知!=根:
            失败(种类+' changed rootCallId for subCallId '+子)#根不得改
        if 父!=根 and (根映射 is None or 根映射.get(父)!=根):
            失败(种类+' parentCallId '+父+' does not belong to rootCallId '+根)#父必须属于根
    def 提交派发(会话对象,事件):
        """提交派发映射：记下子调用到根的归属。"""
        种类=试取(事件,'type')#事件类型
        if 种类!='tool/code-dispatch-start' and 种类!='tool/code-dispatch':
            return#非派发事件放过
        数据=试取(事件,'data')#载荷
        根映射=派发根表.取(会话对象)#该会话映射
        if 根映射 is None:
            根映射={}#新建
            派发根表.设(会话对象,根映射)#挂上
        根映射[str(试取(数据,'subCallId'))]=str(试取(数据,'rootCallId'))#记下子到根
    def 播种(会话对象):
        """从会话日志播种打开轮次与派发根映射。"""
        打开轮次=None#当前打开轮次
        派发根表.设(会话对象,{})#空映射
        for 事件 in 会话对象.events:
            校验派发(会话对象,事件)#先校验派发
            提交派发(会话对象,事件)#再提交映射
            种类=试取(事件,'type')#事件类型
            if 种类=='turn/start':
                打开轮次=试取(试取(事件,'data'),'turn')#打开轮次
            elif 种类=='turn/end':
                打开轮次=None#关闭轮次
            elif (种类=='tool/code-dispatch-start' or 种类=='tool/code-dispatch') and 打开轮次 is None:
                失败(种类+' appended outside any open turn')#必须包在轮次内
        打开轮次表.设(会话对象,打开轮次)#记下打开轮次
        return 打开轮次#返回打开轮次
    def 取打开轮次(会话对象):
        """取打开轮次，缺或已关闭则播种。"""
        已有=打开轮次表.取(会话对象)#已有打开轮次
        if 已有 is None:
            return 播种(会话对象)#缺席或已关闭则播种
        return 已有#已有打开轮次
    for 会话对象 in 上下文对象.sessions.列出():
        播种(会话对象)#为已有会话播种
    def 会话已创建(会话对象,*其余):
        """新会话播种。"""
        播种(会话对象)#播种
    上下文对象.on('session/created',会话已创建,{'global':True})#新会话播种
    def 会话事件(会话对象,事件,*其余):
        """事件提交后更新打开轮次与派发映射。"""
        校验派发(会话对象,事件)#校验派发
        提交派发(会话对象,事件)#提交映射
        种类=试取(事件,'type')#事件类型
        if 种类=='turn/start':
            打开轮次表.设(会话对象,试取(试取(事件,'data'),'turn'))#打开轮次
        elif 种类=='turn/end':
            打开轮次表.设(会话对象,None)#关闭轮次
    上下文对象.on('session/event',会话事件,{'global':True})#全局监听
    def 内部派发(_模式,事件名,参数,*其余):
        """提交前检查管线阶段单调性与派发封闭。"""
        if 事件名=='session/event':
            会话对象=参数[0]#会话
            事件=参数[1]#事件
            校验派发(会话对象,事件)#校验派发
            种类=试取(事件,'type')#事件类型
            if (种类=='tool/code-dispatch-start' or 种类=='tool/code-dispatch') and 取打开轮次(会话对象) is None:
                失败(种类+' appended outside any open turn')#必须包在轮次内
            return#会话事件处理完
        if 事件名=='tools/pre-execute':
            执行=参数[0]#取出执行
            if 阶段表.取(执行) is not None:
                失败('tools/pre-execute repeated for one execution')#不得重复预执行
            阶段表.设(执行,'pre')#记为预执行
            return#预执行处理完
        if 事件名=='tools/execute':
            执行=参数[0]#取出执行
            if 阶段表.取(执行)!='pre':
                失败('tools/execute must follow tools/pre-execute')#必须先预执行
            阶段表.设(执行,'execute')#记为执行
            return#执行处理完
        if 事件名=='tools/post-execute':
            执行=参数[0]#取出执行
            先前=阶段表.取(执行)#上一阶段
            if 先前!='pre' and 先前!='execute':
                失败('tools/post-execute must follow tools/pre-execute or tools/execute')#必须跟在预执行或执行后
            阶段表.设(执行,'post')#记为后执行
            return#后执行处理完
        if 事件名!='tools/result':
            return#其余事件放过
        执行=参数[0]#拆出执行
        结果=参数[1]#拆出结果
        校验结果(执行,结果,失败)#校验最终快照
        阶段表.设(执行,None)#清掉阶段
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听

安装.注入=['sessions']#中文：安装时还要 sessions
安装.inject=安装.注入#invariants 登记约定读 inject 槽

def 应用(上下文对象):
    """注册工具不变量配套，返回已兑现的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记贡献并返回拆除器

apply=应用#Cordis 插件入口槽

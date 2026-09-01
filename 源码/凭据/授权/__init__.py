"""授权能力缝（`ctx.authorization`）服务定义。

对齐上游 `@deepseek-ai/dsh-authorization`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#服务基类
from ...模型后端.llm import 装备错误 as 框架错误#Harness 风格错误
from .类型 import 授权条目字段,授权结算#类型词汇

__all__=[#仅中文公开名
    '授权错误','授权拒绝错误','授权服务','默认',
]#公开面结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
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
        return 值.等待()#等待
    return 值#同步值

def 信号已中止(信号):#对齐 signal.aborted
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if 取字段(信号,'aborted') is True:#英文
        return True#已中止
    if 取字段(信号,'已中止') is True:#中文
        return True#已中止
    return False#未中止

class 授权错误(框架错误):#稳定错误分类
    """授权失败的结构化错误。"""
    def __init__(自身,消息,码,选项=None):#构造
        """记下消息与稳定码。"""
        super().__init__(消息,码,选项)#基类
        自身.name='AuthorizationError'#错误名

class 授权拒绝错误(授权错误):#人类拒绝
    """提示被人类拒绝时使用。"""
    def __init__(自身,消息='the authorization prompt was declined'):#默认文案
        """DECLINED 码。"""
        super().__init__(消息,'DECLINED')#基类
        自身.name='AuthorizationDeclinedError'#错误名

class 授权服务(服务):#授权注册表与单次飞行
    """每个凭证键同时只允许一次授权尝试。"""
    inject=['credentials']#依赖凭据缝
    注入=['credentials']#中文别名

    def __init__(自身,上下文):#构造服务
        """登记为 ctx.authorization。"""
        super().__init__(上下文,'authorization')#服务名
        自身.流程表={}#键→流程
        自身.运行表={}#键→在途控制器

    def 注册流程(自身,流程):#注册一种获取凭证的方式
        """同一键只能有一个流程；返回拆除器。"""
        def 装寿命():#effect 体
            """登记并在拆除时撤回在途尝试。"""
            键=取字段(流程,'key')#凭证键
            if 键 in 自身.流程表:#重复
                raise 授权错误('an authorization flow for "'+str(键)+'" is already registered','DUPLICATE_FLOW')#冲突
            自身.流程表[键]=流程#占住
            def 拆():#拆除
                """流程离开则中止在途尝试。"""
                自身.流程表.pop(键,None)#释放
                在途=自身.运行表.get(键)#在途
                if 在途 is not None:#有在途
                    取字段(在途,'controller').abort()#中止
            return 拆#拆除器
        拆除=自身.ctx.effect(装寿命,'authorization.registerFlow()')#登记 effect
        return lambda:解开(拆除()) if callable(拆除) else None#包装拆除

    def 列举(自身):#列出全部已注册流程
        """按注册顺序返回公开条目。"""
        return [自身._条目(流程) for 流程 in 自身.流程表.values()]#映射

    def 描述(自身,键):#查询单个流程
        """未知键返回 None。"""
        流程=自身.流程表.get(键)#查找
        if 流程 is None:#未注册
            return None#缺席
        return 自身._条目(流程)#公开视图

    def _条目(自身,流程):#流程的公开视图
        """附带 inFlight 标记。"""
        键=取字段(流程,'key')#凭证键
        return {'key':键,'label':取字段(流程,'label'),'methods':取字段(流程,'methods'),'inFlight':键 in 自身.运行表}#条目

    def 取消(自身,键):#撤回在途尝试
        """无在途则为空操作。"""
        在途=自身.运行表.get(键)#查找
        if 在途 is not None:#有在途
            取字段(在途,'controller').abort()#中止

    def 开始(自身,请求):#运行一次授权尝试
        """成功返回 authorized，人类拒绝或撤回返回 cancelled。"""
        键=取字段(请求,'key')#目标键
        流程=自身.流程表.get(键)#查找流程
        if 流程 is None:#无流程
            raise 授权错误('no authorization flow is registered for "'+str(键)+'"','NO_FLOW')#无流程
        方法=取字段(请求,'method')#指定方法
        if 方法 is None:#默认首个
            方法=取字段(取字段(流程,'methods')[0],'id')#首选方法
        if not any(取字段(候选,'id')==方法 for 候选 in 取字段(流程,'methods')):#未知方法
            raise 授权错误('authorization flow for "'+str(键)+'" offers no method "'+str(方法)+'"','UNKNOWN_METHOD')#未知
        if 键 in 自身.运行表:#已在飞
            raise 授权错误('an authorization attempt for "'+str(键)+'" is already running','ALREADY_IN_FLIGHT')#忙
        信号=取字段(请求,'signal')#外部信号
        if 信号已中止(信号):#开始前已撤回
            return {'status':'cancelled'}#取消
        控制器=cordis.中止控制器() if hasattr(cordis,'中止控制器') else type('C',(),{'signal':type('S',(),{'aborted':False,'reason':None})(),'abort':lambda 自身2,原因=None:setattr(自身2.signal,'aborted',True)})()#简易控制器
        自身.运行表[键]={'controller':控制器}#占槽
        结算='failed'#默认失败
        try:#运行流程
            结果=解开(自身._尝试(流程,方法,控制器.signal,取字段(请求,'interaction')))#一次尝试
            结算=取字段(结果,'status')#记录结算
            return 结果#返回结果
        finally:#释放槽并扇出 settled
            自身.运行表.pop(键,None)#释放
            自身._结算(键,结算)#事件扇出

    def _结算(自身,键,结算):#扇出 authorization/settled
        """监听器失败记日志；INVARIANT 失败重抛。"""
        不变量失败=None#收集不变量失败
        监听器们=自身.ctx.events.dispatch('emit',['authorization/settled',键,结算]) if hasattr(自身.ctx.events,'dispatch') else []#取监听器
        for 监听器 in 监听器们 or []:#逐个调用
            try:#同步监听
                返回=监听器(键,结算)#调用
                if 返回 is not None and 是否thenable(返回):#异步监听
                    def 记错(错误):自身.ctx.logger.warn('authorization: an authorization/settled listener for "'+str(键)+'" failed');自身.ctx.logger.warn(错误)#记日志
                    if hasattr(返回,'add_done_callback'):返回.add_done_callback(lambda 未来:记错(未来.exception()) if 未来.exception() else None)#Future
            except Exception as 错误:#同步失败
                if getattr(错误,'code',None)=='INVARIANT':#不变量
                    不变量失败=不变量失败 or 错误#保留首个
                    continue#继续其余
                自身.ctx.logger.warn('authorization: an authorization/settled listener for "'+str(键)+'" failed')#记日志
                自身.ctx.logger.warn(错误)#详情
        if 不变量失败 is not None:#有不变量失败
            raise 不变量失败#重抛

    def _尝试(自身,流程,方法,信号,交互):#运行流程并确认提交
        """流程必须在本尝试内提交凭证记录。"""
        已观察={'declined':False,'committed':False}#观察状态
        def 记录更新(键,*_):#credentials/record-updated
            """记下本键是否在本尝试内提交。"""
            if 键==取字段(流程,'key'):已观察['committed']=True#已提交
        取消监听=自身.ctx.on('credentials/record-updated',记录更新)#挂监听
        try:#运行流程
            if 信号已中止(信号):#已撤回
                return {'status':'cancelled'}#取消
            def 提示包装(提示):#包装交互提示
                """区分人类拒绝与其它失败。"""
                try:return 解开(交互.prompt(提示))#转发
                except 授权拒绝错误:#人类拒绝
                    已观察['declined']=True#记下
                    raise#继续抛
            运行=取字段(流程,'run')({#会话面
                'method':方法,#所选方法
                'signal':信号,#取消信号
                'notify':lambda 通知:交互.notify(通知),#通知
                'prompt':提示包装,#提示
            })#run 调用
            解开(运行)#等待完成
        except Exception as 错误:#流程失败
            if 信号已中止(信号) or 已观察['declined']:#撤回或拒绝
                return {'status':'cancelled'}#取消
            raise 错误#其它失败上抛
        finally:#拆掉监听
            if callable(取消监听):取消监听()#disposer
            elif 取消监听 is not None and hasattr(取消监听,'dispose'):取消监听.dispose()#纤程式
        if not 已观察['committed']:#未提交
            raise 授权错误('authorization flow for "'+str(取字段(流程,'key'))+'" resolved without committing a credential record in this attempt','NOT_COMMITTED')#未提交
        描述=解开(自身.ctx.credentials.describeRecord(取字段(流程,'key')))#读记录
        if not 取字段(描述,'configured'):#提交后又删
            raise 授权错误('authorization flow for "'+str(取字段(流程,'key'))+'" deleted its credential record instead of committing one','NOT_COMMITTED')#未提交
        return {'status':'authorized'}#成功

默认=授权服务#默认导出
default=授权服务#Cordis 默认导出

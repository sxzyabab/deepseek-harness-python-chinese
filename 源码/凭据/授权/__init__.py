"""授权能力缝（`ctx.authorization`）服务定义。

公开面仅中文名。
"""
import threading#中止信号
from ...依赖 import cordis#外部依赖胶水
from ...依赖.工具 import 获取内部数据#读事件总线内部成员
服务=cordis.服务#服务基类
from ...模型后端.llm import 装备错误 as 框架错误#Harness 风格错误

__all__=[#仅中文公开名
    '授权错误','授权拒绝错误','授权服务','默认','信号已中止',
]#公开面结束

def 信号已中止(信号):
    """信号是否已中止。信号为 threading.Event。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#已中止

class 授权错误(框架错误):
    """授权失败的结构化错误。"""
    def __init__(自身,消息,码,选项=None):
        """记下消息与稳定码。"""
        super().__init__(消息,码,选项)#基类
        自身.name='AuthorizationError'#错误名

class 授权拒绝错误(授权错误):
    """提示被人类拒绝时使用。"""
    def __init__(自身,消息='the authorization prompt was declined'):
        """DECLINED 码。"""
        super().__init__(消息,'DECLINED')#基类
        自身.name='AuthorizationDeclinedError'#错误名

class 授权服务(服务):
    """每个凭证键同时只允许一次授权尝试。"""
    inject=['credentials']#框架槽

    def __init__(自身,上下文):
        """登记为 ctx.authorization。"""
        super().__init__(上下文,'authorization')#服务名
        自身.流程表={}#键→流程 dict
        自身.运行表={}#键→在途 Event

    def 注册流程(自身,流程):
        """同一键只能有一个流程；返回拆除器。流程为 dict。"""
        def 装寿命():
            """登记并在拆除时撤回在途尝试。"""
            键=流程['key']#凭证键
            if 键 in 自身.流程表:#重复
                raise 授权错误('an authorization flow for "'+str(键)+'" is already registered','DUPLICATE_FLOW')#冲突
            自身.流程表[键]=流程#占住
            def 拆():
                """流程离开则中止在途尝试。"""
                自身.流程表.pop(键,None)#释放
                在途=自身.运行表[键] if 键 in 自身.运行表 else None#在途
                if 在途 is not None:#有在途
                    在途['信号'].set()#中止
            return 拆#拆除器
        return 自身.ctx.副作用(装寿命,'authorization.registerFlow()')#登记副作用

    def 列举(自身):
        """按注册顺序返回公开条目。"""
        return [自身.条目(流程) for 流程 in 自身.流程表.values()]#映射

    def 描述(自身,键):
        """未知键返回 None。"""
        流程=自身.流程表[键] if 键 in 自身.流程表 else None#查找
        if 流程 is None:#未注册
            return None#缺席
        return 自身.条目(流程)#公开视图

    def 条目(自身,流程):
        """附带 inFlight 标记。流程为 dict。"""
        键=流程['key']#凭证键
        return {'key':键,'label':流程['label'],'methods':流程['methods'],'inFlight':键 in 自身.运行表}#条目

    def 取消(自身,键):
        """无在途则为空操作。"""
        在途=自身.运行表[键] if 键 in 自身.运行表 else None#查找
        if 在途 is not None:#有在途
            在途['信号'].set()#中止

    def 开始(自身,请求):
        """成功返回 authorized，人类拒绝或撤回返回 cancelled。请求为 dict。"""
        键=请求['key']#目标键
        流程=自身.流程表[键] if 键 in 自身.流程表 else None#查找流程
        if 流程 is None:#无流程
            raise 授权错误('no authorization flow is registered for "'+str(键)+'"','NO_FLOW')#无流程
        方法=请求['method'] if 'method' in 请求 else None#指定方法
        if 方法 is None:#默认首个
            方法=流程['methods'][0]['id']#首选方法
        有方法=False#是否提供该方法
        for 候选 in 流程['methods']:#扫描
            if 候选['id']==方法:#命中
                有方法=True#有
                break#停
        if not 有方法:#未知方法
            raise 授权错误('authorization flow for "'+str(键)+'" offers no method "'+str(方法)+'"','UNKNOWN_METHOD')#未知
        if 键 in 自身.运行表:#已在飞
            raise 授权错误('an authorization attempt for "'+str(键)+'" is already running','ALREADY_IN_FLIGHT')#忙
        信号=请求['signal'] if 'signal' in 请求 else None#外部信号
        if 信号已中止(信号):#开始前已撤回
            return {'status':'cancelled'}#取消
        控制器=信号 if 信号 is not None else threading.Event()#本尝试中止旗
        自身.运行表[键]={'信号':控制器}#占槽
        结算='failed'#默认失败
        try:#运行流程
            交互=请求['interaction'] if 'interaction' in 请求 else None#交互面
            结果=自身.尝试(流程,方法,控制器,交互)#一次尝试
            结算=结果['status']#记录结算
            return 结果#返回结果
        finally:#释放槽并扇出 settled
            自身.运行表.pop(键,None)#释放
            自身.结算(键,结算)#事件扇出

    def 结算(自身,键,结算):
        """监听器失败记日志；INVARIANT 失败重抛。"""
        不变量失败=None#收集不变量失败
        事件总线=获取内部数据(自身.ctx,'属性链')['事件']#事件总线，不经壳
        监听器列表=获取内部数据(事件总线,'解析监听器')(事件总线,'emit',['authorization/settled',键,结算])#取监听器
        for 监听器 in 监听器列表:#逐个调用
            try:#同步监听
                监听器(键,结算)#监听器已同步
            except Exception as 错误:#监听器可抛任意类型，扇出契约未钉死，无法再收窄
                码=错误.code if hasattr(错误,'code') else None#稳定码
                if 码=='INVARIANT':#不变量
                    if 不变量失败 is None:#保留首个
                        不变量失败=错误#记下
                    continue#继续其余
                自身.ctx.日志.警告('authorization: an authorization/settled listener for "'+str(键)+'" failed')#记日志
                自身.ctx.日志.警告(错误)#详情
        if 不变量失败 is not None:#有不变量失败
            raise 不变量失败#重抛

    def 尝试(自身,流程,方法,信号,交互):
        """流程必须在本尝试内提交凭证记录。流程为 dict。"""
        已观察={'declined':False,'committed':False}#观察状态
        def 记录更新(键,*其余):
            """记下本键是否在本尝试内提交。"""
            if 键==流程['key']:#本键
                已观察['committed']=True#已提交
        取消监听=自身.ctx.监听('credentials/record-updated',记录更新)#挂监听
        try:#运行流程
            if 信号已中止(信号):#已撤回
                return {'status':'cancelled'}#取消
            def 提示包装(提示):
                """区分人类拒绝与其它失败。"""
                try:#转发
                    return 交互.prompt(提示)#同步提示
                except 授权拒绝错误:#人类拒绝
                    已观察['declined']=True#记下
                    raise#继续抛
            def 通知包装(通知):
                """转发通知。"""
                交互.notify(通知)#通知
            流程['run']({#会话面
                'method':方法,#所选方法
                'signal':信号,#取消信号
                'notify':通知包装,#通知
                'prompt':提示包装,#提示
            })#run 调用已同步
        except Exception as 错误:#流程 run 可抛任意类型，无法再收窄
            if 信号已中止(信号) or 已观察['declined']:#撤回或拒绝
                return {'status':'cancelled'}#取消
            raise 错误#其它失败上抛
        finally:#拆掉监听
            取消监听()#disposer
        if not 已观察['committed']:#未提交
            raise 授权错误('authorization flow for "'+str(流程['key'])+'" resolved without committing a credential record in this attempt','NOT_COMMITTED')#未提交
        键=流程['key']#目标键
        if hasattr(自身.ctx.credentials,'描述记录') and isinstance(键,str) and '/' in 键:#记录键
            描述=自身.ctx.credentials.描述记录(键)#读记录描述
        else:#引用键
            描述=自身.ctx.credentials.描述(键)#读引用描述
        if not 描述['configured']:#提交后又删
            raise 授权错误('authorization flow for "'+str(流程['key'])+'" deleted its credential record instead of committing one','NOT_COMMITTED')#未提交
        return {'status':'authorized'}#成功

默认=授权服务#中文默认导出
default=授权服务#框架槽

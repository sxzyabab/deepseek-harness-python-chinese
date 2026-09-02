"""可配置的包拥有运行时不变量贡献注册表。

工作区每个包从 `./invariant` 配套注册检查；普通包入口点与诊断解耦。
"""
import re#编译包名过滤正则
from ...依赖 import cordis#Cordis
from ...依赖.schemastery import 字典字段,布尔字段,列表字段,字符串字段#配置校验
服务=cordis.服务#Cordis 服务基类
__all__=[#仅中文公开名
    '配置','不变量错误','不变量注册表',
    '名称','注入','配置模式','应用','apply','默认',
    'InvariantRegistry','InvariantError',
]#公开面结束

名称='invariants'#Cordis 插件名
注入=[]#根服务无依赖

class 不变量错误(Exception):#包归因不变量失败
    """包拥有的运行时不变量被违反时抛出。"""
    code='INVARIANT'#稳定机器可读不变量失败码
    def __init__(自身,包名,消息):#构造包归因失败
        super().__init__(f'invariant violated by "{包名}": {消息}')#标准前缀
        自身.包名=包名#完整 npm 包名
        自身.name='InvariantError'#错误名

def _编译模式列表(字段名,值列表):#编译并校验一个包过滤列表
    """编译并校验一个包过滤列表。"""
    已见=set()#去重
    结果=[]#正则列表
    for 值 in 值列表:#逐项
        if len(值)==0 or 值.strip()!=值:#空白或带外围空白
            raise Exception(f'invariants: {字段名} entries must be non-blank and have no surrounding whitespace')#拒绝
        if 值 in 已见:#重复
            raise Exception(f'invariants: {字段名} contains duplicate regex {repr(值)}')#拒绝
        已见.add(值)#记下
        try:#编译正则
            结果.append(re.compile(值))#加入列表
        except re.error as 原因:#非法正则
            raise Exception(f'invariants: {字段名} contains invalid regex {repr(值)}') from 原因#包装
    return 结果#返回编译结果

class 不变量注册表(服务):#包拥有不变量注册表
    """带全局与基于正则选择的包拥有不变量注册表。"""
    def __init__(自身,上下文对象,配置=None):#创建并安装注册表
        super().__init__(上下文对象,'invariants')#登记服务
        if 配置 is None:#无配置
            配置={}#空配置
        自身._启用=配置.get('enabled',True)#全局开关
        自身._所有者上下文=上下文对象#拥有注册的上下文
        自身._包允许列表=_编译模式列表('package_allowlist',配置.get('package_allowlist',[]))#允许列表
        自身._包阻止列表=_编译模式列表('package_blocklist',配置.get('package_blocklist',[]))#阻止列表
        自身._注册=set()#已注册包名

    def _已选中(自身,包名):#一个完整包名是否通过配置的过滤
        if not 自身._启用:#全局关闭
            return False#不选中
        if len(自身._包允许列表)>0 and not any(模式.search(包名) for 模式 in 自身._包允许列表):#不在允许列表
            return False#不选中
        return not any(模式.search(包名) for 模式 in 自身._包阻止列表)#阻止列表后仍通过

    def register(自身,包名,安装器):#注册一个包的不变量安装器
        """注册一个包的不变量安装器。即使过滤禁用其检查，包名也会被预留。启用的安装器在子 fiber 中运行；失败会拆除该 fiber 并释放预留。"""
        if len(包名)==0 or 包名.strip()!=包名 or re.search(r'\s',包名):#包名非法
            raise Exception('invariants: packageName must be non-blank and contain no whitespace')#拒绝
        if 包名 in 自身._注册:#重复注册
            raise Exception(f'invariants: package "{包名}" is already registered')#拒绝
        上下文对象=自身._所有者上下文#显式来源
        注册表=自身._注册#共享注册集
        注册表.add(包名)#预留包名
        def 安装不变量(子上下文):#子 fiber 安装器
            def 失败(消息):#包归因失败报告器
                raise 不变量错误(包名,消息)#抛出不变量错误
            return 安装器(子上下文,失败)#跑包安装器
        if getattr(安装器,'inject',None) is not None:#安装器声明依赖
            安装不变量.inject=安装器.inject#透传 inject
        try:#在 effect 中安装
            注册效果=上下文对象.effect(lambda: 自身._运行注册(上下文对象,包名,安装不变量,注册表),f'invariants.register({repr(包名)})')#登记 effect
            return 注册效果#返回 disposer
        except BaseException as 错误:#登记失败
            注册表.discard(包名)#释放预留
            raise 错误#再抛

    def _运行注册(自身,上下文对象,包名,安装不变量,注册表):#在 effect 内完成注册生命周期
        if not 自身._已选中(包名):#过滤未选中
            def 拆除():#仅释放预留
                注册表.discard(包名)#释放名
            return 拆除#返回拆除器
        子插件=上下文对象.plugin(安装不变量)#安装子插件
        try:#等待子 fiber 就绪
            if hasattr(子插件,'wait'):#可等待
                子插件.wait()#等待就绪
            elif hasattr(子插件,'等待'):#中文等待
                子插件.等待()#等待就绪
        except BaseException as 错误:#启动失败
            if hasattr(子插件,'dispose'):#可拆除
                子插件.dispose()#拆除子 fiber
            注册表.discard(包名)#释放预留
            raise 错误#再抛
        async def 拆除():#异步拆除
            try:#拆除子 fiber
                if hasattr(子插件,'dispose'):#可拆除
                    结果=子插件.dispose()#启动拆除
                    if hasattr(结果,'wait'):#可等待
                        结果.wait()#等拆除完成
                    elif hasattr(结果,'等待'):#中文等待
                        结果.等待()#等拆除完成
            finally:#无论成败释放名
                注册表.discard(包名)#释放预留
        return 拆除#返回拆除器

配置模式=字典字段({#运行时不变量选择配置
    'enabled':布尔字段(默认值=True),#全局开关
    'package_allowlist':列表字段(字符串字段(),默认值=[]),#允许包名正则
    'package_blocklist':列表字段(字符串字段(),默认值=[]),#阻止包名正则
})#配置模式结束

def 应用(上下文对象,配置=None):#安装不变量注册表
    """在宿主组合上挂载不变量注册表服务。"""
    不变量注册表(上下文对象,配置)#构造并登记
    return None#无额外拆除

apply=应用#Cordis 插件入口
默认=不变量注册表#默认导出
InvariantRegistry=不变量注册表#上游类名
InvariantError=不变量错误#上游类名

import re#编译包名过滤正则
from ...依赖.schemastery import 字典字段,布尔字段,列表字段,字符串字段#配置校验
from ...依赖 import cordis#Cordis
服务=cordis.服务#Cordis 服务基类

名称='invariants'#Cordis 插件名
注入=[]#根服务无依赖
空白模式=re.compile(r'[ \t]')#包名不得含空白
配置模式=字典字段({#运行时不变量选择配置
    'enabled':布尔字段(默认值=True),#全局开关
    'package_allowlist':列表字段(字符串字段(),默认值=[]),#允许包名正则
    'package_blocklist':列表字段(字符串字段(),默认值=[]),#阻止包名正则
})#配置模式结束
配置=配置模式#中文配置

class 不变量错误(Exception):#包归因不变量失败
    """包拥有的运行时不变量被违反时抛出。"""
    def __init__(自身,包名,消息):#构造包归因失败
        """记下包名与英文消息。"""
        super().__init__('不变量被 "'+包名+'" 违反: '+消息)#标准前缀
        自身.包名=包名#完整 npm 包名
        自身.code='INVARIANT'#稳定机器可读不变量失败码
        自身.name='InvariantError'#错误名

def 编译模式列表(字段名,值列表):#编译并校验一个包过滤列表
    """编译并校验一个包过滤列表。"""
    已见=set()#去重
    结果=[]#正则列表
    for 值 in 值列表:#逐项
        if len(值)==0 or 值.strip()!=值:#空白或带外围空白
            raise 不变量错误('@deepseek-ai/dsh-invariants',字段名+' 条目必须非空且无外围空白')#拒绝
        if 值 in 已见:#重复
            raise 不变量错误('@deepseek-ai/dsh-invariants',字段名+' 含重复正则 '+repr(值))#拒绝
        已见.add(值)#记下
        try:#编译正则
            结果.append(re.compile(值))#加入列表
        except re.error as 原因:#非法正则
            raise 不变量错误('@deepseek-ai/dsh-invariants',字段名+' 含非法正则 '+repr(值)) from 原因#包装
    return 结果#返回编译结果

class 不变量注册表(服务):#包拥有不变量注册表
    """带全局与基于正则选择的包拥有不变量注册表。"""
    Config=配置模式#Cordis配置模式
    def __init__(自身,上下文对象,配置值=None):#创建并安装注册表
        """创建并安装注册表。配置是 dict。"""
        super().__init__(上下文对象,'invariants')#登记服务
        if 配置值 is None:#无配置
            配置值={}#空配置
        自身._启用=配置值['enabled'] if 'enabled' in 配置值 else True#全局开关
        自身._所有者上下文=上下文对象#拥有注册的上下文
        允许=配置值['package_allowlist'] if 'package_allowlist' in 配置值 else []#允许列表
        阻止=配置值['package_blocklist'] if 'package_blocklist' in 配置值 else []#阻止列表
        自身._包允许列表=编译模式列表('package_allowlist',允许)#允许列表
        自身._包阻止列表=编译模式列表('package_blocklist',阻止)#阻止列表
        自身._注册=set()#已注册包名

    def _已选中(自身,包名):#一个完整包名是否通过配置的过滤
        """一个完整包名是否通过配置的过滤。"""
        if not 自身._启用:#全局关闭
            return False#不选中
        if len(自身._包允许列表)>0:#有允许列表
            命中=False#是否命中
            for 模式 in 自身._包允许列表:#逐模式
                if 模式.search(包名) is not None:#命中
                    命中=True#记下
                    break#停
            if not 命中:#不在允许列表
                return False#不选中
        for 模式 in 自身._包阻止列表:#阻止列表
            if 模式.search(包名) is not None:#命中阻止
                return False#不选中
        return True#通过

    def register(自身,包名,安装器):#注册一个包的不变量安装器
        """注册一个包的不变量安装器。即使过滤禁用其检查，包名也会被预留。启用的安装器在子 fiber 中运行；失败会拆除该 fiber 并释放预留。"""
        if len(包名)==0 or 包名.strip()!=包名 or 空白模式.search(包名) is not None:#包名非法
            raise 不变量错误('@deepseek-ai/dsh-invariants','packageName 必须非空且不含空白')#拒绝
        if 包名 in 自身._注册:#重复注册
            raise 不变量错误('@deepseek-ai/dsh-invariants','包 "'+包名+'" 已登记')#拒绝
        上下文对象=自身._所有者上下文#显式来源
        注册表=自身._注册#共享注册集
        注册表.add(包名)#预留包名
        def 安装不变量(子上下文):#子 fiber 安装器
            """子 fiber 安装器。"""
            def 失败(消息):#包归因失败报告器
                """包归因失败报告器。"""
                raise 不变量错误(包名,消息)#抛出不变量错误
            return 安装器(子上下文,失败)#跑包安装器
        if hasattr(安装器,'inject') and 安装器.inject is not None:#安装器声明依赖
            安装不变量.inject=安装器.inject#透传 inject
        def 执行注册():#在 effect 内完成注册生命周期
            """在 effect 内完成注册生命周期。"""
            return 自身._运行注册(上下文对象,包名,安装不变量,注册表)#执行生命周期
        try:#在 effect 中安装
            注册效果=上下文对象.副作用(执行注册,'invariants.register('+repr(包名)+')')#登记副作用
            return 注册效果#返回 disposer
        except BaseException as 错误:#登记失败
            注册表.discard(包名)#释放预留
            raise 错误#再抛

    def _运行注册(自身,上下文对象,包名,安装不变量,注册表):#在 effect 内完成注册生命周期
        """在 effect 内完成注册生命周期。"""
        if not 自身._已选中(包名):#过滤未选中
            def 拆除未选():#仅释放预留
                """仅释放预留。"""
                注册表.discard(包名)#释放名
            return 拆除未选#返回拆除器
        子插件=上下文对象.启动插件(安装不变量)#安装子插件
        try:#等待子 fiber 就绪
            子插件.等待()#等待就绪
        except BaseException as 错误:#启动失败
            子插件.拆除()#拆除子 fiber
            注册表.discard(包名)#释放预留
            raise 错误#再抛
        def 拆除():#拆除
            """拆除子 fiber 并释放名。"""
            try:#拆除子 fiber
                子插件.拆除()#启动拆除
            finally:#无论成败释放名
                注册表.discard(包名)#释放预留
        return 拆除#返回拆除器

def 应用(上下文对象,配置值=None):#安装不变量注册表
    """在宿主组合上挂载不变量注册表服务。"""
    不变量注册表(上下文对象,配置值)#构造并登记
    return None#无额外拆除

__all__=[#仅中文公开名
    '配置','不变量错误','不变量注册表',
    '名称','注入','配置模式','应用',
]#公开面结束
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
Config=配置模式#Cordis配置模式
apply=应用#Cordis插件入口
default=不变量注册表#Cordis默认导出

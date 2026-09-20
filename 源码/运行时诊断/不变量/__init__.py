import re
from ...依赖.schemastery import 字典字段,布尔字段,列表字段,字符串字段
from ...依赖 import cordis
服务=cordis.服务

名称='invariants'
依赖=[]
空白模式=re.compile(r'[ \t]')#包名不得含空白
配置模式=字典字段(字典结构={
    'enabled':布尔字段(默认值=True),
    'package_allowlist':列表字段(字符串字段(),默认值=[]),
    'package_blocklist':列表字段(字符串字段(),默认值=[]),
})
配置=配置模式

class 不变量错误(Exception):
    """包拥有的运行时不变量被违反时抛出。"""
    def __init__(自身,包名,消息):
        """记下包名与英文消息。"""
        super().__init__('不变量被 "'+包名+'" 违反: '+消息)
        自身.包名=包名
        自身.code='INVARIANT'#稳定机器可读不变量失败码
        自身.name='InvariantError'

def 编译模式列表(字段名,值列表):
    """编译并校验一个包过滤列表。"""
    已见=set()
    结果=[]
    for 值 in 值列表:
        if len(值)==0 or 值.strip()!=值:
            raise 不变量错误('@deepseek-ai/dsh-invariants',字段名+' 条目必须非空且无外围空白')
        if 值 in 已见:
            raise 不变量错误('@deepseek-ai/dsh-invariants',字段名+' 含重复正则 '+repr(值))
        已见.add(值)
        try:
            结果.append(re.compile(值))
        except re.error as 原因:
            raise 不变量错误('@deepseek-ai/dsh-invariants',字段名+' 含非法正则 '+repr(值)) from 原因
    return 结果

class 不变量注册表(服务):
    """带全局与基于正则选择的包拥有不变量注册表。"""
    Config=配置模式
    def __init__(自身,上下文,配置值=None):
        """创建并安装注册表。配置是 dict。"""
        super().__init__(上下文,'invariants')
        if 配置值 is None:
            配置值={}
        自身._启用=配置值['enabled'] if 'enabled' in 配置值 else True
        自身._所有者上下文=上下文
        允许=配置值['package_allowlist'] if 'package_allowlist' in 配置值 else []
        阻止=配置值['package_blocklist'] if 'package_blocklist' in 配置值 else []
        自身._包允许列表=编译模式列表('package_allowlist',允许)
        自身._包阻止列表=编译模式列表('package_blocklist',阻止)
        自身._注册=set()

    def _已选中(自身,包名):
        """一个完整包名是否通过配置的过滤。"""
        if not 自身._启用:
            return False
        if len(自身._包允许列表)>0:
            命中=False
            for 模式 in 自身._包允许列表:
                if 模式.search(包名) is not None:
                    命中=True
                    break
            if not 命中:
                return False
        for 模式 in 自身._包阻止列表:
            if 模式.search(包名) is not None:
                return False
        return True

    def register(自身,包名,安装器):
        """注册一个包的不变量安装器。即使过滤禁用其检查，包名也会被预留。启用的安装器在子 fiber 中运行；失败会拆除该 fiber 并释放预留。"""
        if len(包名)==0 or 包名.strip()!=包名 or 空白模式.search(包名) is not None:
            raise 不变量错误('@deepseek-ai/dsh-invariants','packageName 必须非空且不含空白')
        if 包名 in 自身._注册:
            raise 不变量错误('@deepseek-ai/dsh-invariants','包 "'+包名+'" 已登记')
        上下文=自身._所有者上下文
        注册表=自身._注册
        注册表.add(包名)
        def 安装不变量(子上下文):
            """子 fiber 安装器。"""
            def 失败(消息):
                """包归因失败报告器。"""
                raise 不变量错误(包名,消息)
            return 安装器(子上下文,失败)
        if hasattr(安装器,'inject') and 安装器.inject is not None:
            安装不变量.inject=安装器.inject
        def 执行注册():
            """在 effect 内完成注册生命周期。"""
            return 自身._运行注册(上下文,包名,安装不变量,注册表)
        try:
            注册效果=上下文.副作用(执行注册,'invariants.register('+repr(包名)+')')
            return 注册效果
        except BaseException as 错误:
            注册表.discard(包名)
            raise 错误

    def _运行注册(自身,上下文,包名,安装不变量,注册表):
        """在 effect 内完成注册生命周期。"""
        if not 自身._已选中(包名):
            def 拆除未选():
                """仅释放预留。"""
                注册表.discard(包名)
            return 拆除未选
        子插件=上下文.启动插件(安装不变量)
        try:
            子插件.等待()
        except BaseException as 错误:
            子插件.拆除()
            注册表.discard(包名)
            raise 错误
        def 拆除():
            """拆除子 fiber 并释放名。"""
            try:
                子插件.拆除()
            finally:
                注册表.discard(包名)
        return 拆除

def 应用(上下文,配置值=None):
    """在宿主组合上挂载不变量注册表服务。"""
    不变量注册表(上下文,配置值)
    return None

__all__=[
    '配置','不变量错误','不变量注册表',
    '名称','依赖','配置模式','应用',
]
name=名称#框架槽
inject=依赖#框架槽
Config=配置模式#框架槽
apply=应用#框架槽
default=不变量注册表#框架槽

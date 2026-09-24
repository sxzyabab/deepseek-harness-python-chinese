from ...依赖.工具 import 克隆,聚合错误,获取内部数据
from ...依赖.loader import 插件树
from ...内核.作用域 import 获取作用域,获取作用域父
from .类型 import 预设注册表错误

__all__=[
    '实时预设挂载表','已泄漏服务列表','常驻挂载','获取智能体服务',
    '审计表行列表','挂载预设',
]

挂载表=[]

class 预设树(插件树):
    """只存在于内存的加载器树，不写回配置文件。"""
    def __init__(自身,上下文):
        """建树后把拥有方原先的子树子组还回去。"""
        拥有=上下文.纤程.插件配置
        子树=拥有.子树 if 拥有 is not None else None
        子组=拥有.子组 if 拥有 is not None else None
        插件树.__init__(自身,上下文)
        if 拥有 is not None:
            拥有.子树=子树
            拥有.子组=子组

    def 写入(自身):
        """内存树不持久化。"""
        return

def 实时预设挂载表(范围内=None):
    """当前进程里仍被注册表持留的预设挂载。"""
    全部=list(挂载表)
    if 范围内 is None:
        return 全部
    结果=[]
    for 项 in 全部:
        if 位于纤程内(项['fiber'],范围内):
            结果.append(项)
    return 结果

def 位于纤程内(纤程,根):
    """按对象身份判断纤程是否落在根及其子树里。"""
    当前=纤程
    while True:
        if 当前 is 根:
            return True
        父=当前.父上下文.纤程
        if 父 is 当前:
            return False
        当前=父

def 已泄漏服务列表(上下文,挂载纤程):
    """挂载子树写进根隔离域的服务名，按词典序。"""
    存储=上下文.反射.存储
    根隔离=获取内部数据(上下文.根,'属性链')['隔离']
    泄漏=[]
    for 标签,实现 in list(存储.items()):
        if 实现 is None:
            continue
        if not 位于纤程内(实现.纤程,挂载纤程):
            continue
        if 根隔离.get(实现.名称) is 标签:
            泄漏.append(实现.名称)
    泄漏.sort()
    return 泄漏

def 常驻挂载(智能体上下文):
    """智能体作用域父键对应的常驻挂载。"""
    智能体键=获取作用域(智能体上下文)
    if 智能体键 is None:
        return None
    常驻键=获取作用域父(智能体键)
    if 常驻键 is None:
        return None
    for 候选 in 实时预设挂载表():
        if 候选['key'] is 常驻键:
            return 候选
    return None

def 获取智能体服务(上下文,智能体,名称):
    """读取该智能体所在预设隔离域里的服务实现。"""
    挂载=常驻挂载(智能体.ctx)
    if 挂载 is None:
        return None
    存储=上下文.反射.存储
    for 标签,实现 in list(存储.items()):
        if 实现 is None:
            continue
        if 实现.名称!=名称:
            continue
        if 位于纤程内(实现.纤程,挂载['fiber']):
            return 实现.值
    return None

def 审计表行列表(树):
    """已启用行的导入失败、激活失败与待服务。"""
    失败=[]
    待定=[]
    for 插件配置对象 in 树.列出插件配置():
        if 插件配置对象.已禁用:
            continue
        纤程=插件配置对象.纤程
        选项=插件配置对象.选项
        标注=str(选项['id'] if 'id' in 选项 else None)+' ('+str(选项['name'] if 'name' in 选项 else None)+')'
        if 纤程 is None:
            失败.append(标注+': 从未启动')
            continue
        try:
            纤程.等待()
        except BaseException as 错误:
            失败.append(标注+': '+挂载细节(错误))
            continue
        缺失=[]
        for 服务名 in 纤程.依赖表:
            if 纤程.所属上下文.获取服务(服务名,False) is None:
                缺失.append(服务名)
        if len(缺失)>0:
            待定.append(标注+': 正在等待 '+', '.join(缺失))
    return {'failed':失败,'pending':待定}

def 细节分支(错误):
    """自身消息未覆盖的聚合成员。"""
    if isinstance(错误,聚合错误):
        return 错误.错误列表
    起因=错误.__cause__ if isinstance(错误,BaseException) else None
    if isinstance(起因,聚合错误):
        return 起因.错误列表
    if isinstance(错误,ExceptionGroup):
        return list(错误.exceptions)
    return []

def 挂载细节(错误):
    """一行一条原因的挂载失败文本。"""
    if not isinstance(错误,BaseException):
        return str(错误)
    分支=细节分支(错误)
    if len(分支)==0:
        return str(错误)
    行=[str(错误)]
    for 成员 in 分支:
        行.append('- '+挂载细节(成员).replace('\n','\n  '))
    return '\n'.join(行)

def 挂载预设(上下文,标识,插件列表):
    """在注册表作用域下装一棵修订并审计。"""
    if 获取作用域(上下文) is None:
        raise 预设注册表错误('挂载智能体预设需要作用域')
    上下文.纤程.等待()
    树=预设树(上下文)
    def 停树效果():
        """卸载时停掉根组。"""
        def 停树():
            """停止子插件配置。"""
            树.根组.停止()
        return 停树
    上下文.副作用(停树效果,'agent-preset.tree')
    树.根组.更新(克隆(插件列表))
    审计=审计表行列表(树)
    泄漏=已泄漏服务列表(上下文,上下文.纤程)
    if len(审计['failed'])>0:
        raise 预设注册表错误('\n'.join(审计['failed']))
    if len(泄漏)>0:
        raise 预设注册表错误('预设服务需要隔离域: '+', '.join(泄漏))
    挂载={'presetId':标识,'fiber':上下文.纤程,'tree':树,'key':获取作用域(上下文)}
    挂载表.append(挂载)
    def 摘挂载效果():
        """卸载时从登记表摘掉。"""
        def 摘掉():
            """按身份移除。"""
            下标=0
            while 下标<len(挂载表):
                if 挂载表[下标] is 挂载:
                    挂载表.pop(下标)
                    return
                下标+=1
        return 摘掉
    上下文.副作用(摘挂载效果,'agent-preset.mount')
    return 挂载

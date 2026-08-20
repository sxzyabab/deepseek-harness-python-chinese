"""当前 Cordis Loader 插件条目的只读投影。

对齐上游 `@deepseek-ai/dsh-host-plugin-inventory`。公开面仅中文名。每次 list 直接读 Loader，跳过 group 行。本包默认导出网关服务类。
"""
from typert.protocol import 远程服务,远程#Remote 服务基类与装饰器
from .类型 import (
    插件条目标识,#条目 id
    插件光纤阶段,#光纤阶段
    插件清单条目,#清单行
    插件清单快照,#整份快照
    打品牌条目标识,#品牌化
    光纤状态表,#FiberState 数值
    光纤阶段表,#阶段投影
)#类型面
from .远程 import TYPERT_REMOTE,远程贡献对象#Host-for-Client Remote 贡献

__all__=[#仅中文公开名
    '插件清单网关',
    '插件条目标识',
    '插件光纤阶段',
    '插件清单条目',
    '插件清单快照',
    'TYPERT_REMOTE',
    '远程贡献对象',
]#公开面结束

class 插件清单网关(远程服务):#插件清单网关
    """只远程暴露 Loader 当前非 group 条目状态的服务。"""
    inject=['loader']#依赖 Loader
    注入=['loader']#中文别名

    def __init__(自身,上下文):#按上下文登记 pluginInventory
        """登记为 ctx.pluginInventory。"""
        super().__init__(上下文,'pluginInventory')#服务名

    @远程('list')
    def list(自身):#投影当前非 group 条目
        """每次调用都直接读 Loader。按 Loader 顺序返回。"""
        条目们=[]#按遍历顺序收集
        for 条目 in 自身.ctx.loader.entries():#遍历 Loader 树
            选项=取字段(条目,'options') or {}#条目选项
            if 取字段(选项,'group'):#group 不是清单行
                continue#跳过
            光纤=取字段(条目,'fiber')#可能尚无
            if 光纤 is None:#无活根
                阶段=None#null
            else:#有 fiber
                状态=取字段(光纤,'state')#FiberState 数值
                阶段=光纤阶段表.get(状态)#对外阶段；DISPOSED 映射 null
            条目们.append({#一条对外投影
                'entryId':打品牌条目标识(取字段(条目,'id')),#品牌化 id
                'moduleName':取字段(选项,'name'),#插件模块名
                'enabled':not 取字段(条目,'disabled',False),#未禁用即启用
                'fiberPhase':阶段,#根 Fiber 阶段
            })#行结束
        return {'entries':条目们}#整份快照

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

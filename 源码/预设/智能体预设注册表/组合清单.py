from ...依赖.工具 import 是否表达式节点,取表达式
from .定义 import 条目列表问题

__all__=['定义组合体','已挂载组合体表行列表']

def 禁用贡献(值,求值表达式):
    """一层 disabled 对有效启用态的贡献。"""
    if 是否表达式节点(值):
        try:
            return bool(求值表达式(取表达式(值)))
        except Exception:
            return 'conditional'
    return bool(值)

def 合并禁用(外层,自身层):
    """祖先组与本行禁用态按加载器规则合并。"""
    if 外层 is True or 自身层 is True:
        return True
    if 外层=='conditional' or 自身层=='conditional':
        return 'conditional'
    return False

def 展平行列表(行列表,外层禁用,求值表达式,已找到):
    """组行只提供结构，子行才进入清单。"""
    for 值 in 行列表:
        行=值
        禁用=合并禁用(外层禁用,禁用贡献(行['disabled'] if 'disabled' in 行 else None,求值表达式))
        if ('group' in 行) and 行['group'] is True:
            子=行['config'] if 'config' in 行 else []
            展平行列表(子,禁用,求值表达式,已找到)
            continue
        条目标识=行['id'] if 'id' in 行 and isinstance(行['id'],str) and 行['id']!='' else None
        项={
            'entryId':条目标识,
            'moduleName':行['name'],
            'enabled':False if 禁用 is True else ('conditional' if 禁用=='conditional' else True),
        }
        if 'disabled' in 行 and 是否表达式节点(行['disabled']):
            项['condition']=取表达式(行['disabled'])
        已找到.append(项)

def 定义组合体(行列表,求值表达式):
    """激活前从声明展平插件行。"""
    问题=条目列表问题(行列表)
    if 问题 is not None:
        return {'broken':问题}
    已找到=[]
    展平行列表(行列表,False,求值表达式,已找到)
    return {'rows':已找到}

def 已挂载组合体表行列表(树):
    """已挂载树按加载器顺序给出的插件行。"""
    已找到=[]
    拥有=树.所属上下文.纤程.插件配置
    前缀='' if 拥有 is None else 拥有.编号+':'
    for 插件配置对象 in 树.列出插件配置():
        if 'group' in 插件配置对象.选项 and 插件配置对象.选项['group']:
            continue
        编号=插件配置对象.编号
        相对=编号[len(前缀):] if 编号.startswith(前缀) else 编号
        项={
            'entryId':相对,
            'moduleName':插件配置对象.选项['name'],
            'enabled':not 插件配置对象.已禁用,
        }
        禁用项=插件配置对象.选项['disabled'] if 'disabled' in 插件配置对象.选项 else None
        if 是否表达式节点(禁用项):
            项['condition']=取表达式(禁用项)
        if 插件配置对象.纤程 is not None:
            项['fiberState']=插件配置对象.纤程.状态
        已找到.append(项)
    return 已找到

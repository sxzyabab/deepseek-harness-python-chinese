"""工作区浏览器的查看 store：会话列表分组模式，跨重载持久化。

对齐上游 `ui-workspace/src/client/stores.ts`。公开面仅中文名。
模块级只导出工厂（模块级句柄会在插件重载间钉死 store 身份）。
"""

__all__=['扁平会话顺序键','创建工作区查看存储']#仅中文公开名

扁平会话顺序键='__flat_session_order__'#无层级扁平会话列表的浏览器本地排序账本键

def 初值():#播种初始查看状态
    """默认按工作区分组、按活动提升。"""
    return {#查看状态
        'groupBy':'workspace',#默认按工作区分组
        'orderBy':'updated',#默认按活动提升
        'groupExpansion':{},#分组展开表为空
        'sessionOrderByAccount':{},#各账本会话顺序为空
        'sessionUpdatedAtByAccount':{},#各账本更新时间戳为空
    }#初值结束

def 设分组(草稿,模式):#写入分组模式
    """写入 groupBy。"""
    草稿['groupBy']=模式#写入

def 设排序(草稿,模式):#写入排序模式
    """写入 orderBy。"""
    草稿['orderBy']=模式#写入

def 设分组展开(草稿,键,展开):#写入某分组展开
    """写入 groupExpansion[key]。"""
    草稿['groupExpansion'][键]=展开#写入

def 保留账本键(草稿,工作区键们):#丢掉已不存在的工作区账本键
    """只保留仍存在的账本键。"""
    保留=set(工作区键们)#仍应保留的工作区键集合
    草稿['groupExpansion']={键:值 for 键,值 in 草稿['groupExpansion'].items() if 键 in 保留}#重写分组展开表
    草稿['sessionOrderByAccount']={键:值 for 键,值 in 草稿['sessionOrderByAccount'].items() if 键 in 保留}#重写会话顺序账本
    草稿['sessionUpdatedAtByAccount']={键:值 for 键,值 in 草稿['sessionUpdatedAtByAccount'].items() if 键 in 保留}#重写更新时间账本

def 同步会话顺序账本(草稿,账本键,顺序,更新时间):#同步某账本顺序与时间戳
    """写入该账本会话顺序与更新时间戳。"""
    草稿['sessionOrderByAccount'][账本键]=顺序#写入顺序
    草稿['sessionUpdatedAtByAccount'][账本键]=更新时间#写入时间戳

def 设会话顺序(草稿,账本键,顺序):#只写某账本会话顺序
    """写入该账本会话顺序。"""
    草稿['sessionOrderByAccount'][账本键]=顺序#写入

def 创建工作区查看存储():#创建查看 store 句柄
    """返回 store 规格（init / persist / actions），供 register 收下。"""
    return {#规格进、句柄出（对齐 defineStore 入参）
        'init':初值,#播种
        'persist':'dsh.workspace.view.v5',#持久化键
        'actions':{#动作写集合
            'setGroupBy':设分组,#写入分组模式
            'setOrderBy':设排序,#写入排序模式
            'setGroupExpanded':设分组展开,#写入某分组展开
            'retainAccountKeys':保留账本键,#保留账本键
            'syncSessionOrderAccount':同步会话顺序账本,#同步顺序与时间戳
            'setSessionOrder':设会话顺序,#只写顺序
        },#动作结束
    }#规格结束

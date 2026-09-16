__all__=['扁平会话顺序键','创建工作区查看存储']#仅中文公开名

扁平会话顺序键='__flat_session_order__'#无层级扁平会话列表的浏览器本地排序账本键

def 拷会话顺序(顺序表):#只读投影 → 可变拷贝
    """逐账本浅拷贝顺序。"""
    return {键:list(顺序) for 键,顺序 in 顺序表.items()}#可变拷贝

def 初值():#播种初始查看状态
    """默认按工作区分组、按近因。"""
    return {#查看状态
        'groupBy':'workspace',#默认按工作区分组
        'orderBy':'updated',#默认按近因
        'groupExpansion':{},#分组展开表为空
        'sessionOrderByAccount':{},#各账本会话顺序为空
    }#初值结束

def 设分组(草稿,模式):#写入分组模式
    """写入 groupBy。"""
    草稿['groupBy']=模式#写入

def 设排序(草稿,模式,初始顺序):#写入排序模式
    """切入手动时拷初始序；切近因则清空账本。"""
    if 模式==草稿['orderBy']:#未变
        return#不动
    草稿['sessionOrderByAccount']=拷会话顺序(初始顺序) if 模式=='manual' else {}#切入手动才拷
    草稿['orderBy']=模式#写入

def 设分组展开(草稿,键,展开):#写入某分组展开
    """写入 groupExpansion[key]。"""
    草稿['groupExpansion'][键]=展开#写入

def 保留账本键(草稿,工作区键集合):#丢掉已不存在的工作区账本键
    """只保留仍存在的账本键，并丢掉旧时间戳账本。"""
    保留=set(工作区键集合)#仍应保留的工作区键集合
    草稿['groupExpansion']={键:值 for 键,值 in 草稿['groupExpansion'].items() if 键 in 保留}#重写分组展开表
    草稿['sessionOrderByAccount']={键:值 for 键,值 in 草稿['sessionOrderByAccount'].items() if 键 in 保留}#重写会话顺序账本
    if 'sessionUpdatedAtByAccount' in 草稿:#旧时间戳账本
        del 草稿['sessionUpdatedAtByAccount']#丢掉

def 同步会话顺序(草稿,顺序表):#合并写入各账本顺序
    """近因模式不写手动账本。"""
    if 草稿['orderBy']!='manual':#近因
        return#不写
    草稿['sessionOrderByAccount'].update(拷会话顺序(顺序表))#合并拷贝

def 设会话顺序(草稿,账本键,顺序,初始顺序):#只写某账本会话顺序
    """从近因切入手动时先铺全表。"""
    if 草稿['orderBy']=='updated':#从近因切入
        草稿['sessionOrderByAccount']=拷会话顺序(初始顺序)#铺全表
    草稿['orderBy']='manual'#此后为手动
    草稿['sessionOrderByAccount'][账本键]=list(顺序)#写入该账本

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
            'syncSessionOrders':同步会话顺序,#合并写入各账本
            'setSessionOrder':设会话顺序,#只写顺序
        },#动作结束
    }#规格结束

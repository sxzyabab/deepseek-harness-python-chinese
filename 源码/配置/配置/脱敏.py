"""设置值的结构密钥擦除。`角色=secret` 字段在值越过线路边界之前被移除。"""

缺席=object()

def 是否记录(值):
    """值是否为 walker 可以递归进入的普通数据对象。"""
    return isinstance(值,dict) and type(值) is dict

def 行走(节点,值,路径,密钥列表):
    """按 schemastery 节点走值并擦除密钥。"""
    if 节点 is None:
        return 值
    元=getattr(节点,'meta',None) or {}
    if 元.get('role')=='secret':
        密钥列表.append({'path':list(路径),'set':值 is not 缺席})
        return 缺席
    类型=getattr(节点,'type',None)
    if 类型=='object':
        属性=getattr(节点,'dict',None) or {}
        源=值 if 是否记录(值) else 缺席
        重建={}
        if 源 is not 缺席:
            for 键,条目 in 源.items():
                if 键 in 属性:
                    continue
                重建[键]=条目
        for 键,孩子 in 属性.items():
            子值=缺席 if 源 is 缺席 or 键 not in 源 else 源[键]
            剥掉=行走(孩子,子值,list(路径)+[键],密钥列表)
            if 剥掉 is not 缺席:
                重建[键]=剥掉
        if 源 is 缺席 and len(重建)==0:
            return 值
        return 重建
    if 类型=='dict':
        if not 是否记录(值):
            return 值
        重建={}
        内层=getattr(节点,'inner',None)
        for 键,条目 in 值.items():
            剥掉=行走(内层,条目,list(路径)+[键],密钥列表)
            if 剥掉 is not 缺席:
                重建[键]=剥掉
        return 重建
    if 类型=='array':
        if not isinstance(值,list):
            return 值
        内层=getattr(节点,'inner',None)
        结果=[]
        下标=0
        for 条目 in 值:
            结果.append(行走(内层,条目,list(路径)+[str(下标)],密钥列表))
            下标+=1
        return 结果
    if 类型=='union' or 类型=='intersect':
        当前=值
        for 孩子 in getattr(节点,'list',None) or []:
            当前=行走(孩子,当前,路径,密钥列表)
        return 当前
    if 类型=='transform':
        return 行走(getattr(节点,'inner',None),值,路径,密钥列表)
    return 值

def 脱敏密钥(模式对象,值):
    """从值中移除 schema 声明的每个 secret 字段。"""
    密钥列表=[]
    剥掉=行走(模式对象,值 if 值 is not None else 缺席,[],密钥列表)
    位置={}
    for 密钥 in 密钥列表:
        键=str(密钥['path'])
        先前=位置.get(键)
        位置[键]={'path':密钥['path'],'set':密钥['set'] or (先前 is not None and 先前['set'] is True)}
    return {'value':剥掉,'secrets':list(位置.values())}

已脱敏密钥=dict
已脱敏值=dict

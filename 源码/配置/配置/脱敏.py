"""设置值的结构密钥擦除。`角色=secret` 字段在值越过线路边界之前被移除。"""
from ...依赖.schemastery import 字段

缺席=object()#对齐 JS undefined，与 JSON null（None）区分

def 是否记录(值):
    """值是否为 walker 可以递归进入的普通数据对象。"""
    return isinstance(值,dict) and type(值) is dict

def 行走(根,节点,值,路径,密钥列表):
    """按 JSON Schema 走值并擦除密钥。节点为 schema dict。"""
    引用=节点['$ref'] if isinstance(节点,dict) and '$ref' in 节点 else None
    if isinstance(引用,str) and 引用.startswith('#/'):
        当前=根
        for 片段 in 引用[2:].split('/'):
            if not isinstance(当前,dict):
                break
            if 片段 not in 当前:
                当前=None
                break
            当前=当前[片段]
        if isinstance(当前,dict):
            节点=当前
    if not isinstance(节点,dict):
        return 值
    if '角色' in 节点 and 节点['角色']=='secret':
        密钥列表.append({'path':list(路径),'set':值 is not 缺席})
        return 缺席
    属性=节点['properties'] if 'properties' in 节点 else None
    if isinstance(属性,dict):
        源=值 if 是否记录(值) else 缺席
        重建={}
        if 源 is not 缺席:
            for 键,条目 in 源.items():
                if 键 in 属性:
                    continue#声明属性稍后处理
                重建[键]=条目
        for 键,孩子 in 属性.items():
            if 源 is 缺席 or 键 not in 源:
                子值=缺席
            else:
                子值=源[键]#含 JSON null
            剥掉=行走(根,孩子,子值,list(路径)+[键],密钥列表)
            if 剥掉 is not 缺席:
                重建[键]=剥掉
        if 源 is 缺席 and len(重建)==0:
            return 值
        return 重建
    额外=节点['additionalProperties'] if 'additionalProperties' in 节点 else None
    if isinstance(额外,dict) and 是否记录(值):
        重建={}
        for 键,条目 in 值.items():
            剥掉=行走(根,额外,条目,list(路径)+[键],密钥列表)
            if 剥掉 is not 缺席:
                重建[键]=剥掉
        return 重建
    项=节点['items'] if 'items' in 节点 else None
    if isinstance(项,dict) and isinstance(值,list):
        结果=[]
        下标=0
        for 条目 in 值:
            结果.append(行走(根,项,条目,list(路径)+[str(下标)],密钥列表))
            下标+=1
        return 结果
    return 值

def 脱敏密钥(模式对象,值):
    """从值中移除 schema 声明的每个 secret 字段。"""
    根=模式对象.toJsonSchema() if isinstance(模式对象,字段) else 模式对象
    密钥列表=[]
    剥掉=行走(根,根,值,[],密钥列表)
    return {'value':剥掉,'secrets':密钥列表}#缺席可出现在 value

已脱敏密钥=dict#密钥位置记录形态（path/set）
已脱敏值=dict#擦除结果形态（value/secrets）

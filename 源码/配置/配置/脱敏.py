"""设置值的结构密钥擦除。`role('secret')` 字段在值越过线路边界之前被移除；旁路记录每个 schema 声明的密钥位置以及它当前是否持有值，以便配置界面渲染只写输入，而从不收到密钥本身。"""

缺席=object()#对齐 JS undefined，与 JSON null（None）区分

def 是否记录(值):#收窄为普通对象
    """值是否为 walker 可以递归进入的普通数据对象。"""
    return isinstance(值,dict) and type(值) is dict#非数组纯对象

def 取节点类型(节点):#读模式节点类型标签
    """读活模式节点的类型标签。"""
    return getattr(节点,'类型',None)#中文 schemastery 字段

def 取节点元(节点):#读模式节点元数据
    """读活模式节点的元数据表。"""
    元=getattr(节点,'元',None)#中文 schemastery 字段
    if 元 is None:#缺席
        return {}#空表
    return 元#元数据

def 取节点字典(节点):#读对象属性表
    """读 object 节点的属性表。"""
    return getattr(节点,'字典',None)#中文 schemastery 字段

def 取节点内层(节点):#读容器元素模式
    """读 dict/array 节点的元素模式。"""
    return getattr(节点,'内层',None)#中文 schemastery 字段

def 行走(节点,值,路径,密钥们):#按schema走值并擦除密钥
    """按 schema 走值并擦除密钥字段。"""
    if 节点 is None:#没有schema则原样返回
        return 值#含缺席；对齐上游 node===undefined 时原样交回
    元=取节点元(节点)#元数据
    if 元.get('角色')=='secret':#本节点是密钥
        密钥们.append({'path':list(路径),'set':值 is not 缺席})#记录位置与是否有值
        return 缺席#从结果中移除（对齐 return undefined）
    类型=取节点类型(节点)#容器类型
    if 类型=='object':#对象属性
        属性表=取节点字典(节点) or {}#schema声明的属性
        源=值 if 是否记录(值) else 缺席#值侧普通对象；非记录对齐 undefined
        重建={}#重建后的对象
        if 源 is not 缺席:#值侧有对象则先拷未声明键
            for 键,条目 in 源.items():#遍历值侧键
                if 键 in 属性表:#声明属性稍后处理
                    continue#跳过
                重建[键]=条目#保留未声明键
        for 键,孩子 in 属性表.items():#遍历声明属性
            if 源 is 缺席 or 键 not in 源:#缺席键（键不在≠值为 null）
                子值=缺席#对齐 undefined
            else:#有键
                子值=源[键]#含 JSON null（None）
            剥掉=行走(孩子,子值,list(路径)+[键],密钥们)#递归擦除
            if 剥掉 is not 缺席:#非缺席才写入（None/null 保留）
                重建[键]=剥掉#写入
        if 源 is 缺席 and len(重建)==0:#空重建且无源则保持原值
            return 值#原值（可能仍是缺席）
        return 重建#重建对象
    if 类型=='dict':#字典
        if not 是否记录(值):#非对象则原样返回
            return 值#原样
        重建={}#重建字典
        for 键,条目 in 值.items():#遍历条目
            剥掉=行走(取节点内层(节点),条目,list(路径)+[键],密钥们)#按元素schema擦除
            if 剥掉 is not 缺席:#非缺席才写入（None/null 保留）
                重建[键]=剥掉#写入
        return 重建#返回重建字典
    if 类型=='array':#数组
        if not isinstance(值,list):#非数组则原样返回
            return 值#原样
        结果=[]#重建数组
        下标=0#元素下标
        for 条目 in 值:#遍历元素
            结果.append(行走(取节点内层(节点),条目,list(路径)+[str(下标)],密钥们))#按下标走元素；可含缺席
            下标+=1#前进
        return 结果#重建数组
    # TODO(settings-wire-redaction): 改为失败关闭——只经联合、交叉或变换可达的密钥在此原样返回，没有任何记录表明它被漏掉。
    return 值#其余类型原样返回

def 脱敏密钥(模式对象,值):#擦除schema声明的密钥
    """从值中移除 schema 声明的每个 `role('secret')` 字段。walker 跟随 `object`、`dict` 和 `array` 容器；密钥必须直接声明在经那些容器可达的字段上。从不修改输入。"""
    密钥们=[]#密钥位置累积
    剥掉=行走(模式对象,值,[],密钥们)#从根走一遍
    return {'value':剥掉,'secrets':密钥们}#缺席可出现在 value（对齐 undefined）

已脱敏密钥=dict#密钥位置记录形态（path/set）
已脱敏值=dict#擦除结果形态（value/secrets）

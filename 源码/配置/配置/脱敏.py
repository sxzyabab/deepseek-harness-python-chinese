"""设置值的结构密钥擦除。`角色=secret` 字段在值越过线路边界之前被移除。"""
from ...依赖 import schemastery
字段=schemastery.字段#配置字段

缺席=object()#对齐 JS undefined，与 JSON null（None）区分

def 是否记录(值):
    "值是否为 walker 可以递归进入的普通数据对象"
    return isinstance(值,dict) and type(值) is dict#非数组纯对象

def 行走(根,节点,值,路径,密钥们):
    "按 JSON Schema 走值并擦除密钥"
    if isinstance(节点,dict) and isinstance(节点.get('$ref'),str) and 节点['$ref'].startswith('#/'):#本地 $ref
        当前=根#从根走
        for 片段 in 节点['$ref'][2:].split('/'):#逐段
            if not isinstance(当前,dict):#走不下去
                break#停止
            当前=当前.get(片段)#下一层
        if isinstance(当前,dict):
            节点=当前#解引用
    if not isinstance(节点,dict):
        return 值#没有 schema
    if 节点.get('角色')=='secret':
        密钥们.append({'path':list(路径),'set':值 is not 缺席})#记录位置与是否有值
        return 缺席#从结果中移除
    属性=节点.get('properties')#对象字段
    if isinstance(属性,dict):
        源=值 if 是否记录(值) else 缺席#值侧普通对象
        重建={}#重建后的对象
        if 源 is not 缺席:
            for 键,条目 in 源.items():
                if 键 in 属性:
                    continue#声明属性稍后处理
                重建[键]=条目#保留未声明键
        for 键,孩子 in 属性.items():
            if 源 is 缺席 or 键 not in 源:
                子值=缺席#缺席键
            else:
                子值=源[键]#含 JSON null
            剥掉=行走(根,孩子,子值,list(路径)+[键],密钥们)#递归擦除
            if 剥掉 is not 缺席:
                重建[键]=剥掉#写入
        if 源 is 缺席 and len(重建)==0:
            return 值#原值
        return 重建#重建对象
    额外=节点.get('additionalProperties')#字典值模式
    if isinstance(额外,dict) and 是否记录(值):
        重建={}#重建字典
        for 键,条目 in 值.items():
            剥掉=行走(根,额外,条目,list(路径)+[键],密钥们)#按值模式擦除
            if 剥掉 is not 缺席:
                重建[键]=剥掉#写入
        return 重建#重建字典
    项=节点.get('items')#数组元素
    if isinstance(项,dict) and isinstance(值,list):
        结果=[]#重建数组
        下标=0#元素下标
        for 条目 in 值:
            结果.append(行走(根,项,条目,list(路径)+[str(下标)],密钥们))#按下标走
            下标+=1#前进
        return 结果#重建数组
    return 值#其余类型原样返回

def 脱敏密钥(模式对象,值):
    "从值中移除 schema 声明的每个 secret 字段"
    根=模式对象.toJsonSchema() if isinstance(模式对象,字段) else 模式对象#活字段收成 JSON Schema
    密钥们=[]#密钥位置累积
    剥掉=行走(根,根,值,[],密钥们)#从根走一遍
    return {'value':剥掉,'secrets':密钥们}#缺席可出现在 value

已脱敏密钥=dict#密钥位置记录形态（path/set）
已脱敏值=dict#擦除结果形态（value/secrets）

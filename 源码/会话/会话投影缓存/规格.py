"""session_projcache 域声明。"""
from ...依赖.schemastery import 字典字段,数字字段,字符串字段,任意字段,布尔字段#schema
from ...存储.存储域 import 定义域,域表#域工厂

检查点行=字典字段(字典结构={#单行 schema
    'ver':数字字段(),#状态版本
    'seq':数字字段(),#水位
    'val':任意字段(),#JSON 状态
})#行结束

检查点身份=字典字段(字典结构={#身份 schema
    'formatVersion':数字字段(),#可选格式代
    'createdAt':数字字段(),#创建时刻
    'cwd':字符串字段(),#可选 cwd
    'isSeeded':布尔字段(),#可选播种
    'inheritedEventCount':数字字段(),#可选继承切口
})#身份结束

检查点记录=字典字段(字典结构={#记录 schema
    'identity':检查点身份,#绑定身份
    'rows':字典字段(键值结构=(字符串字段(),检查点行)),#投影行
})#记录结束

投影缓存域规格=定义域({#域 spec
    'name':'session_projcache',#域名
    'version':7,#版本
    'compatibleVersions':[3,4,5,6],#可读前代
    'invalidRecords':'backup-and-skip',#畸形记录旁路
    'layout':'per-record',#布局
    'tables':{'sessions':域表(检查点记录)},#sessions 表
})#spec 结束

__all__=['检查点行','检查点身份','检查点记录','投影缓存域规格']#公开面

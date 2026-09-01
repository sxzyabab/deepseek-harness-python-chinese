"""session_projcache 域声明（对齐 upstream session-projection-cache/spec）。"""
from ...依赖 import schemastery#schema
from ...存储.存储域 import 定义域,声明表#域工厂

检查点行=schemastery.对象字段({#单行 schema
    'ver':schemastery.数字字段(),#状态版本
    'seq':schemastery.数字字段(),#水位
    'val':schemastery.任意字段(),#JSON 状态
})#行结束

检查点身份=schemastery.对象字段({#身份 schema
    'createdAt':schemastery.数字字段(),#创建时刻
    'cwd':schemastery.字符串字段(),#可选 cwd
})#身份结束

检查点记录=schemastery.对象字段({#记录 schema
    'identity':检查点身份,#绑定身份
    'rows':schemastery.字典字段(检查点行),#投影行
})#记录结束

投影缓存域规格=定义域({#域 spec
    'name':'session_projcache',#域名
    'version':4,#版本
    'layout':'per-record',#布局
    'tables':{'sessions':声明表(检查点记录)},#sessions 表
})#spec 结束

__all__=['检查点行','检查点身份','检查点记录','投影缓存域规格']#公开面

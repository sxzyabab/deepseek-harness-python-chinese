"""todo_write 行摘要：纯计划推导。

对齐上游 `ui-tool/src/client/tool/toolviews/plan-summary.ts`。公开面仅中文名。
"""

__all__=['计划摘要']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 计划摘要(待办们):#从整表推导
    """done/total/activeContent/activeExtra。"""
    活跃=[项 for 项 in 待办们 if 取字段(项,'status')=='in_progress']#进行中
    首=取字段(活跃[0],'content') if 活跃 else None#首正文
    命名=isinstance(首,str) and 首.strip()!=''#可用名
    return {#摘要
        'done':len([项 for 项 in 待办们 if 取字段(项,'status')=='completed']),#完成
        'total':len(待办们),#总
        'activeContent':首 if 命名 else None,#活跃正文
        'activeExtra':(len(活跃)-1) if 命名 else 0,#额外
    }#结束

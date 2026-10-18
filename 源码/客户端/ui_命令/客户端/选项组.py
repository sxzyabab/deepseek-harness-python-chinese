__all__=['分组选项']

def 分组选项(选项表):
    '按调用方的 group.name 分组，不排序。没有组的行占第一次出现的那一块'
    组表={}
    for 选项 in 选项表:
        组对象=选项['group'] if 'group' in 选项 else None
        if isinstance(组对象,dict) and 'name' in 组对象:
            名=组对象['name']
        else:
            名=None
        if 名 in 组表:
            组表[名]['rows'].append(选项)
        else:
            组表[名]={'group':组对象,'rows':[选项]}
    return list(组表.values())

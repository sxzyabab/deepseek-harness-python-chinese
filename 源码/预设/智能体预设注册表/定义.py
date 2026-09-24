__all__=['条目列表问题']

def 条目列表问题(行列表,位置=''):
    """校验已解析的插件行列表，含嵌套组。"""
    if not isinstance(行列表,list):
        if 位置=='':
            return '组合体必须是插件行的顶层列表'
        return '组 '+位置+' 必须容纳插件行列表'
    下标=0
    while 下标<len(行列表):
        行=行列表[下标]
        if 位置=='':
            标注='第 '+str(下标+1)+' 行'
        else:
            标注=位置+' 第 '+str(下标+1)+' 行'
        if not isinstance(行,dict) or 行 is None:
            return 标注+' 不是插件行（需要带 name 的映射）'
        名称=行['name'] if 'name' in 行 else None
        if not isinstance(名称,str) or 名称=='':
            return 标注+' 未给出插件名（需要非空 name 字符串）'
        if ('group' in 行) and 行['group'] is True:
            嵌套=条目列表问题(行['config'] if 'config' in 行 else None,标注)
            if 嵌套 is not None:
                return 嵌套
        下标+=1
    return None

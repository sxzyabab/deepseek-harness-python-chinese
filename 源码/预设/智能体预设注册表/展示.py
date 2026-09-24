__all__=['是否内置预设','预设展示文本']

内置预设键={
    'standard':{'name':'presetStandardName','description':'presetStandardDescription'},
    'ptc':{'name':'presetPtcName','description':'presetPtcDescription'},
    'minimal':{'name':'presetMinimalName','description':'presetMinimalDescription'},
    'cordis':{'name':'presetCordisName','description':'presetCordisDescription'},
}

def 是否内置预设(预设):
    """已发布 name 的声明自管文案；无 name 且标识在内置表中才走词典。"""
    if 'name' in 预设:
        return False
    return 预设['id'] in 内置预设键

def 预设展示文本(预设,取文案):
    """内置标识走词典键，用户自写元数据不翻译。"""
    if 是否内置预设(预设):
        键表=内置预设键[预设['id']]
        return {'name':取文案(键表['name']),'description':取文案(键表['description'])}
    名称=预设['name'] if 'name' in 预设 else 预设['id']
    结果={'name':名称}
    if 'description' in 预设:
        结果['description']=预设['description']
    return 结果

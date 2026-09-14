
__all__=['合并回合轨条目','空轨条目']#仅中文公开名

空轨条目=()#稳定空元组

def 大纲条目(值):
    """turn/seq 承重；预览装饰可降级。值为 dict。"""
    if not isinstance(值,dict):#非映射
        return None#丢
    回合=值['turn'] if 'turn' in 值 else None#回合
    序号=值['seq'] if 'seq' in 值 else None#序号
    if isinstance(回合,bool) or not isinstance(回合,int) or 回合<0:#turn 无效
        return None#丢
    if isinstance(序号,bool) or not isinstance(序号,int) or 序号<0:#seq 无效
        return None#丢
    提示=值['prompt'] if 'prompt' in 值 else None#提示
    回复=值['response'] if 'response' in 值 else None#回复
    return {'turn':回合,'seq':序号,'prompt':提示 if isinstance(提示,str) else '','response':回复 if isinstance(回复,str) else ''}#条目

def 列出大纲条目(大纲):
    """投影缺席或畸形时为空。"""
    return 大纲 if isinstance(大纲,list) else []#数组

def 按回合号(项):
    """排序键：回合号。"""
    return 项['turn']#回合

def 合并回合轨条目(已加载,大纲):
    """两侧都有的回合保留已加载锚；结果按回合升序。"""
    按回合={}#索引
    for 原始 in 列出大纲条目(大纲):#先铺大纲
        条目=大纲条目(原始)#收窄
        if 条目 is None:#坏
            continue#跳
        按回合[条目['turn']]={'turn':条目['turn'],'prompt':条目['prompt'],'response':条目['response'],'anchor':{'kind':'unloaded','seq':条目['seq']}}#未加载
    已=已加载 if 已加载 is not None else []#已加载
    for 项 in 已:#已加载覆盖
        回合=项['turn'] if 'turn' in 项 else None#回合
        if 回合 is None:#无
            continue#跳
        预览=按回合[回合] if 回合 in 按回合 else None#大纲预览
        提示=项['prompt'] if 'prompt' in 项 else ''#提示
        回复=项['response'] if 'response' in 项 else ''#回复
        锚键=项['anchorKey'] if 'anchorKey' in 项 else None#锚键
        预提示=预览['prompt'] if 预览 is not None else ''#预提示
        预回复=预览['response'] if 预览 is not None else ''#预回复
        按回合[回合]={'turn':回合,'prompt':提示 if 提示!='' else 预提示,'response':回复 if 回复!='' else 预回复,'anchor':{'kind':'loaded','key':锚键}}#已加载
    if len(按回合)==0:#皆无
        return 空轨条目#空
    return tuple(sorted(按回合.values(),key=按回合号))#升序

__all__=['拆除条目纤程','移除包拥有样式']#仅中文公开名

def 拆除条目纤程(条目):
    """清纤程前释放运行时，好让刷新导入新代码。"""
    纤程=getattr(条目,'fiber',None)#纤程
    if 纤程 is None:#无
        return#停
    运行时=getattr(纤程,'runtime',None)#运行时
    if 运行时 is not None:#有
        条目.ctx.registry.delete(运行时.callback)#摘登记
    while getattr(纤程,'inertia',None) is not None:#等惯性
        纤程.inertia.wait() if hasattr(纤程.inertia,'wait') else None#阻塞
    if hasattr(条目,'fiber'):#有字段
        delattr(条目,'fiber')#清

def 移除包拥有样式(标识):
    """插件 effect 清理后移除样式。"""
    文档=globals().get('document')#DOM
    if 文档 is None:#无
        return#停
    for 元 in 文档.querySelectorAll('style[data-plugin]'):#逐样式
        if 元.getAttribute('data-plugin')==标识:#同包
            元.remove()#拆

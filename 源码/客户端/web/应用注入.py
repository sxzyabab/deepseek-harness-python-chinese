__all__=['应用索引注入']#仅中文公开名

def 应用索引注入(行表,加载脚本):
    """按表顺序执行索引注入行；loadScript 负责 script-src。"""
    文档=globals().get('document')#DOM
    for 行 in 行表:#逐行
        种=行['kind']#种类
        if 种=='global':#全局
            globals()[行['name']]=行['value']#挂
        elif 种=='script':#内联脚本
            if 文档 is None:#无 DOM
                raise RuntimeError('web boot: script injection requires document')#失败
            元=文档.createElement('script')#造
            元.textContent=行['text']#正文
            位=文档.head if 行.get('placement')=='head' else 文档.body#位
            位.append(元)#挂
        elif 种=='script-src':#外链
            加载脚本(行['src'])#加载
        elif 种=='script-preload':#预加载
            pass#由 loadScript 拥有
        elif 种=='style':#样式
            if 文档 is None:#无
                raise RuntimeError('web boot: style injection requires document')#失败
            元=文档.createElement('style')#造
            元.textContent=行['text']#正文
            文档.head.append(元)#挂
        elif 种=='html':#HTML
            if 文档 is None:#无
                raise RuntimeError('web boot: html injection requires document')#失败
            位=文档.head if 行.get('placement')=='head' else 文档.body#位
            位.insertAdjacentHTML('beforeend',行['html'])#插
        else:#未知
            raise RuntimeError('web boot: unknown index injection row '+str(行))#失败

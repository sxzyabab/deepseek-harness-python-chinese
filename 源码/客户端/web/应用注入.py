import builtins#浏览器页面对象挂在 builtins 上

__all__=['应用索引注入']#仅中文公开名

浏览器全局=('window','document','navigator','localStorage','sessionStorage','performance','location','Element','MutationObserver','queueMicrotask','fetch','WebSocket','ResizeObserver','matchMedia','requestAnimationFrame','cancelAnimationFrame','setTimeout','clearTimeout','getComputedStyle','closeTopModal')#页面专属名

def 应用索引注入(行表,加载脚本):
    '按表顺序执行索引注入行；loadScript 负责 script-src'
    try:#已在页面
        文档=document#DOM
    except NameError:#尚未注入
        文档=None#无
    for 行 in 行表:#逐行
        种=行['kind']#种类
        if 种=='global':#全局
            名=行['name']#名
            值=行['value']#值
            if 名 in 浏览器全局 or 名.startswith('__DSH'):#页面或宿主注入
                setattr(builtins,名,值)#塞进 builtins
                if 名=='document':#本轮脚本用
                    文档=值#更新
                if 名=='window':#窗口上的页面名一并挂上
                    for 别名 in 浏览器全局:#逐个
                        if 别名!='window' and hasattr(值,别名):#窗口自带
                            setattr(builtins,别名,getattr(值,别名))#裸名可用
                            if 别名=='document':#本轮脚本用
                                文档=getattr(值,'document')#更新
            else:#其余启动全局
                globals()[名]=值#挂在本模块
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

"""客户端模块系统：浏览器侧约定面与启动清单解析。

对齐上游 `modules/src/client/manifest.ts`。公开面仅中文名；线字段英文字面量保持上游。
"""

__all__=[#仅中文公开名
    '客户端模块错误',
    '网页启动入口',
    '网页启动图',
    '启动模块行',
    '启动插件行',
    '启动清单',
    '解析启动清单',
    '客户端插件交接',
    '客户端窗口',
    '客户端模块记录',
    '客户端模块加载器',
    '客户端模块系统选项',
]#公开面结束

class 客户端模块错误(Exception):
    """本包模块系统失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

class 网页启动入口(dict):#启动图行
    """宿主推来的一条已组合客户端条目。键：id、url、rev；可选 inject、immediately。"""

class 网页启动图(dict):#启动图
    """宿主作为 window.__DSH_BOOT__ 注入的已组合客户端条目图。键：rev、entries。"""

class 启动模块行(dict):#模块表行
    """一条启动行的 npm 包视图。键：id、url、rev。"""

class 启动插件行(dict):#插件行
    """一条启动行的 cordis 插件视图。键：id、inject、immediately。"""

class 启动清单(dict):#启动清单
    """解析后的启动清单：一条线，两种消费方视图。键：rev、modules、plugins。"""

class 客户端插件交接(dict):#插件交接
    """客户端打包交给 window.__ModuleLoader__.load 的形态。键：id、factory。"""

class 客户端窗口(dict):#窗口协议
    """Web 启动协议的 Window API。键：__DSH_BOOT__、__ModuleLoader__、__DSH_MODULES__。"""

class 客户端模块记录(dict):#模块记录
    """已物化模块账本。键：id、exports、styles、edges。"""

class 客户端模块加载器:#客户端模块 loader 约定
    """内嵌 Loader 与客户端 HMR 插件消费的内部约定子集。"""

class 客户端模块系统选项(dict):#模块系统选项
    """ClientModuleSystem 的选项。键：modules、staticModules；可选 loadBundle。"""

def 解析启动清单(线值):#解析启动清单
    """把 window.__DSH_BOOT__ 解析成两种消费方视图；缺失或畸形抛错。"""
    if not isinstance(线值,dict):#必须是对象；数据入口校验
        raise 客户端模块错误('client-modules: window.__DSH_BOOT__ is missing or not an object')#缺失或非对象
    if 'rev' not in 线值 or not isinstance(线值['rev'],str):#rev 必须是字符串
        raise 客户端模块错误('client-modules: boot manifest rev must be a string')#rev 不合格
    if 'entries' not in 线值 or not isinstance(线值['entries'],list):#entries 必须是数组
        raise 客户端模块错误('client-modules: boot manifest entries must be an array')#entries 不合格
    模块列表=[]#模块表行
    插件列表=[]#插件行
    for 值 in 线值['entries']:#逐行
        if not isinstance(值,dict):#每行必须是对象
            raise 客户端模块错误('client-modules: boot manifest entry is not an object')#非对象
        有标识='id' in 值 and isinstance(值['id'],str)#id 形态
        位置='"'+值['id']+'"' if 有标识 else str(值)#诊断位置
        if (not 有标识) or ('url' not in 值) or (not isinstance(值['url'],str)) or ('rev' not in 值) or (not isinstance(值['rev'],str)):#三个字符串字段
            raise 客户端模块错误('client-modules: boot manifest entry '+位置+' must carry string id/url/rev')#缺字段
        注入=值['inject'] if 'inject' in 值 else None#可选依赖
        if 注入 is not None and (not isinstance(注入,list) or any(not isinstance(项,str) for 项 in 注入)):#inject 可选字符串数组
            raise 客户端模块错误('client-modules: boot manifest entry '+位置+' inject must be a string array')#inject 不合格
        立即=值['immediately'] if 'immediately' in 值 else None#可选立即预取
        if 立即 is not None and not isinstance(立即,bool):#immediately 可选布尔
            raise 客户端模块错误('client-modules: boot manifest entry '+位置+' immediately must be a boolean')#immediately 不合格
        模块列表.append({'id':值['id'],'url':值['url'],'rev':值['rev']})#模块表行
        插件列表.append({#插件行
            'id':值['id'],#包名
            'inject':[] if 注入 is None else list(注入),#缺省空依赖
            'immediately':立即 is True,#缺省 false
        })#结束 plugins
    return {'rev':线值['rev'],'modules':模块列表,'plugins':插件列表}#两种视图

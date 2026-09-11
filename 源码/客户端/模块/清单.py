"""客户端模块系统：浏览器侧约定面与启动清单解析。

对齐上游 `modules/src/client/manifest.ts`。公开面仅中文名；线字段英文字面量保持上游。
"""
import json#诊断串化

__all__=[#仅中文公开名
    '客户端模块错误',
    '网页启动入口',
    '网页启动图',
    '启动模块行',
    '启动插件行',
    '启动清单',
    '可选字符串数组',
    '解析客户端声明',
    '精确包说明符',
    '剥客户端后缀',
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
    """宿主推来的一条已组合客户端条目。键：id、url、rev；可选 inject、immediately、external。"""

class 网页启动图(dict):#启动图
    """宿主作为 window.__DSH_BOOT__ 注入的已组合客户端条目图。键：rev、entries、batches。"""

class 启动模块行(dict):#模块表行
    """一条启动行的 npm 包视图。键：id、url、initialUrl、rev、inject、external。"""

class 启动插件行(dict):#插件行
    """一条启动行的 cordis 插件视图。键：id、inject、immediately。"""

class 启动清单(dict):#启动清单
    """解析后的启动清单：一条线，两种消费方视图。键：rev、modules、plugins。"""

class 客户端插件交接(dict):#打包登记
    """经 window.__ModuleLoader__.load 提交的一个客户端打包工厂登记。键：id、factory。"""

class 客户端窗口(dict):#窗口协议
    """Web 启动协议的 Window API。键：__DSH_BOOT__、__ModuleLoader__。"""

class 客户端模块记录(dict):#模块记录
    """已物化模块账本。键：id、exports、styles、edges。"""

class 客户端模块加载器:#客户端模块 loader 约定
    """内嵌 Loader 与客户端 HMR 插件消费的内部约定子集。"""

class 客户端模块系统选项(dict):#模块系统选项
    """ClientModuleSystem 的选项。键：manifest、staticModules、registrationTarget、bootstrapModule；可选 loadBundle。"""

def 可选字符串数组(主语,字段,值):#可选字符串数组
    """校验从 dsh.client 声明或启动线读出的可选字符串数组字段。"""
    if 值 is None:#缺席
        return None#无
    if not isinstance(值,list) or any(not isinstance(项,str) for 项 in 值):#必须是字符串数组
        raise 客户端模块错误('client-modules: '+主语+' '+字段+' must be a string array')#类型错
    return list(值)#已校验

def 解析客户端声明(包名,值):#解析 dsh.client
    """把未知已解析 JSON 收窄为 dsh.client 声明。"""
    if 值 is None:#缺席
        return None#无声明
    if not isinstance(值,dict):#必须是对象
        raise 客户端模块错误('client-modules: '+包名+' has a non-object dsh.client declaration')#非对象
    if 'platform' not in 值 or not isinstance(值['platform'],str):#platform 必须是字符串
        raise 客户端模块错误('client-modules: '+包名+' dsh.client.platform must be a string')#platform 不合格
    注入=可选字符串数组(包名,'dsh.client.inject',值['inject'] if 'inject' in 值 else None)#可选 inject
    外部=可选字符串数组(包名,'dsh.client.external',值['external'] if 'external' in 值 else None)#可选 external
    if 'immediately' in 值 and not isinstance(值['immediately'],bool):#immediately 可选布尔
        raise 客户端模块错误('client-modules: '+包名+' dsh.client.immediately must be a boolean')#immediately 不合格
    声明={'platform':值['platform']}#已校验声明
    if 注入 is not None:#有注入
        声明['inject']=注入#注入边
    if 外部 is not None:#有外部
        声明['external']=外部#外部请求
    if 'immediately' in 值:#有立即标记
        声明['immediately']=值['immediately']#立即预取
    return 声明#声明

def 精确包说明符(说明符):#精确包说明符
    """说明符点名的裸包根；子路径、路径或任何带 scheme 的说明符则为 None。"""
    if 说明符.startswith('@'):#作用域包
        段列表=说明符.split('/')#按斜杠切
        if len(段列表)==2 and all(段列表):#恰好两段且非空
            return 说明符#包名
        return None#不是裸作用域包
    if len(说明符)>0 and ('/' not in 说明符) and (':' not in 说明符):#无斜杠无冒号
        return 说明符#裸名
    return None#子路径或 scheme

def 剥客户端后缀(说明符):#剥 /client 后缀
    """把模块说明符归一到拥有它的图行。"""
    if 说明符.endswith('/client'):#有后缀
        return 说明符[:-len('/client')]#切掉
    return 说明符#原样

def 解析启动清单(线值):#解析启动清单
    """把 window.__DSH_BOOT__ 解析成两种消费方视图；缺失或畸形抛错。"""
    if not isinstance(线值,dict):#必须是对象
        raise 客户端模块错误('client-modules: window.__DSH_BOOT__ is missing or not an object')#缺失或非对象
    if 'rev' not in 线值 or not isinstance(线值['rev'],str):#rev 必须是字符串
        raise 客户端模块错误('client-modules: boot manifest rev must be a string')#rev 不合格
    if 'entries' not in 线值 or not isinstance(线值['entries'],list):#entries 必须是数组
        raise 客户端模块错误('client-modules: boot manifest entries must be an array')#entries 不合格
    if 'batches' not in 线值 or not isinstance(线值['batches'],list):#batches 必须是数组
        raise 客户端模块错误('client-modules: boot manifest batches must be an array')#batches 不合格
    模块字段列表=[]#尚无 initialUrl 的模块字段
    插件列表=[]#插件行
    已见条目标识=set()#已见条目 id
    for 值 in 线值['entries']:#逐行
        if not isinstance(值,dict):#每行必须是对象
            raise 客户端模块错误('client-modules: boot manifest entry is not an object')#非对象
        有标识='id' in 值 and isinstance(值['id'],str)#id 形态
        位置='"'+值['id']+'"' if 有标识 else json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#诊断位置
        if (not 有标识) or ('url' not in 值) or (not isinstance(值['url'],str)) or ('rev' not in 值) or (not isinstance(值['rev'],str)):#三个字符串字段
            raise 客户端模块错误('client-modules: boot manifest entry '+位置+' must carry string id/url/rev')#缺字段
        if 值['id'] in 已见条目标识:#重复 id
            raise 客户端模块错误('client-modules: duplicate graph entry "'+值['id']+'"')#重复
        已见条目标识.add(值['id'])#记下 id
        主语='boot manifest entry '+位置#诊断主语
        注入=可选字符串数组(主语,'inject',值['inject'] if 'inject' in 值 else None)#可选 inject
        外部=可选字符串数组(主语,'external',值['external'] if 'external' in 值 else None)#可选 external
        if 'immediately' in 值 and not isinstance(值['immediately'],bool):#immediately 可选布尔
            raise 客户端模块错误('client-modules: boot manifest entry '+位置+' immediately must be a boolean')#immediately 不合格
        模块字段列表.append({#模块字段
            'id':值['id'],#包名
            'url':值['url'],#HMR URL
            'rev':值['rev'],#修订
            'inject':[] if 注入 is None else list(注入),#缺省空依赖
            'external':[] if 外部 is None else list(外部),#缺省空外部
        })#结束 append
        插件列表.append({#插件行
            'id':值['id'],#包名
            'inject':[] if 注入 is None else list(注入),#缺省空依赖
            'immediately':值['immediately'] is True if 'immediately' in 值 else False,#缺省 false
        })#结束 plugins.append
    条目标识集=set(行['id'] for 行 in 模块字段列表)#图上全部 id
    初始网址表={}#条目 → 初始批 URL
    批网址集=set()#已见批 URL
    for 值 in 线值['batches']:#逐批
        if not isinstance(值,dict):#每批必须是对象
            raise 客户端模块错误('client-modules: boot manifest batch is not an object')#非对象
        阶段=值['phase'] if 'phase' in 值 else None#阶段
        if 阶段!='bootstrap' and 阶段!='application':#必须是已知阶段
            raise 客户端模块错误('client-modules: boot manifest batch phase must be "bootstrap" or "application", received '+json.dumps(阶段,ensure_ascii=False,separators=(',',':'),allow_nan=False))#阶段非法
        if ('url' not in 值) or (not isinstance(值['url'],str)) or ('rev' not in 值) or (not isinstance(值['rev'],str)):#url/rev 必须是字符串
            raise 客户端模块错误('client-modules: boot manifest '+阶段+' batch must carry string url/rev')#缺字段
        if 值['url'] in 批网址集:#批 URL 不得重复
            raise 客户端模块错误('client-modules: boot manifest carries duplicate batch URL '+json.dumps(值['url'],ensure_ascii=False,separators=(',',':'),allow_nan=False))#重复 URL
        批网址集.add(值['url'])#记下 URL
        条目=可选字符串数组('boot manifest '+阶段+' batch','entries',值['entries'] if 'entries' in 值 else None)#批内条目
        if 条目 is None or len(条目)==0:#必须非空
            raise 客户端模块错误('client-modules: boot manifest '+阶段+' batch entries must be a non-empty string array')#空批
        for 标识 in 条目:#逐条目归属
            if 标识 not in 条目标识集:#必须在图上
                raise 客户端模块错误('client-modules: boot manifest '+阶段+' batch names unknown entry "'+标识+'"')#未知条目
            if 标识 in 初始网址表:#不得跨批重复
                raise 客户端模块错误('client-modules: boot manifest entry "'+标识+'" belongs to more than one batch')#重复归属
            初始网址表[标识]=值['url']#记下初始 URL
    模块列表=[]#完整模块行
    for 行 in 模块字段列表:#补上 initialUrl
        if 行['id'] not in 初始网址表:#必须有批
            raise 客户端模块错误('client-modules: boot manifest entry "'+行['id']+'" belongs to no initial-load batch')#无批
        完整=dict(行)#拷字段
        完整['initialUrl']=初始网址表[行['id']]#所属批 URL
        模块列表.append(完整)#完整模块行
    return {'rev':线值['rev'],'modules':模块列表,'plugins':插件列表}#两种视图

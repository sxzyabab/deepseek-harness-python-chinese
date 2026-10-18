from ....基础设施.通用工具 import 紧凑json编码#诊断里的 JSON 文本
from ..异常 import 客户端模块错误#本包异常


__all__=[#仅中文公开名
    '可选字符串数组',
    '解析客户端声明',
    '精确包说明符',
    '剥客户端后缀',
    '解析启动清单',
    '读取发行',
]

缺席=object()#区分字段缺席与 JSON null
畸形发行=object()#发行在场但读不出来


def 可选字符串数组(主语,字段,值=缺席):
    '校验可选字符串数组。缺席返回 None。在场但不是字符串数组则抛错'
    if 值 is 缺席:#字段没有出现
        return None#无
    if not isinstance(值,list) or any(not isinstance(项,str) for 项 in 值):#不是字符串数组
        raise 客户端模块错误('client-modules: '+主语+' '+字段+' must be a string array')#类型错
    return list(值)#拷一份


def 解析客户端声明(包名,值):
    '把在场的 dsh.client 收成声明。缺席由调用方处理。null 或非对象抛错'
    if not isinstance(值,dict):#必须是对象
        raise 客户端模块错误('client-modules: '+包名+' has a non-object dsh.client declaration')#非对象
    if 'platform' not in 值 or not isinstance(值['platform'],str):#platform 必须是字符串
        raise 客户端模块错误('client-modules: '+包名+' dsh.client.platform must be a string')#不合格
    依赖=可选字符串数组(包名,'dsh.client.inject',值['inject'] if 'inject' in 值 else 缺席)#可选 inject
    外部=可选字符串数组(包名,'dsh.client.external',值['external'] if 'external' in 值 else 缺席)#可选 external
    if 'immediately' in 值 and not isinstance(值['immediately'],bool):#在场则必须是布尔
        raise 客户端模块错误('client-modules: '+包名+' dsh.client.immediately must be a boolean')#不合格
    声明={'platform':值['platform']}#已校验
    if 依赖 is not None:#有依赖
        声明['inject']=依赖#依赖边
    if 外部 is not None:#有外部
        声明['external']=外部#外部请求
    if 'immediately' in 值:#有立即标记
        声明['immediately']=值['immediately']#原值
    return 声明#声明


def 精确包说明符(说明符):
    '说明符点名的裸包根。子路径、路径或带 scheme 的说明符返回 None'
    if 说明符.startswith('@'):#作用域包
        段列表=说明符.split('/')#按斜杠切
        if len(段列表)==2 and all(段列表):#恰好两段且非空
            return 说明符#包名
        return None#不是裸作用域包
    if len(说明符)>0 and ('/' not in 说明符) and (':' not in 说明符):#无斜杠无冒号
        return 说明符#裸名
    return None#子路径或 scheme


def 剥客户端后缀(说明符):
    '去掉末尾的 /client。裸包名与 <id>/client 落到同一图行'
    if 说明符.endswith('/client'):#有后缀
        return 说明符[:-len('/client')]#切掉
    return 说明符#原样


def 解码发行(值):
    '读在场的发行身份。null 或畸形返回畸形发行，成功只留 version 与可选 commit'
    if 值 is None:#JSON null
        return 畸形发行#畸形
    发行=值 if isinstance(值,dict) else None#必须是对象
    提交=None if 发行 is None else 发行.get('commit',缺席)#commit 可以缺席
    版本不合格=发行 is None or not isinstance(发行.get('version'),str)#没有字符串 version
    提交不合格=提交 is not 缺席 and not isinstance(提交,str)#在场但不是字符串
    if 版本不合格 or 提交不合格:#读不出来
        return 畸形发行#畸形
    if 提交 is 缺席:#没有 commit
        return {'version':发行['version']}#只有版本
    return {'version':发行['version'],'commit':提交}#版本与提交


def 读取发行(线值):
    '只读宿主图的 release。其余字段不校验。读不出来当没有发行'
    if not isinstance(线值,dict):#不是对象
        return None#无
    if 'release' not in 线值:#字段缺席
        return None#无
    结果=解码发行(线值['release'])#解码
    if 结果 is 畸形发行:#畸形当成没有
        return None#无
    return 结果#发行或 None


def 解析启动清单(线值):
    '把 window.__DSH_BOOT__ 解析成模块行与插件行。缺失或畸形抛错'
    if not isinstance(线值,dict):#必须是对象
        raise 客户端模块错误('client-modules: window.__DSH_BOOT__ is missing or not an object')#缺失或非对象
    if 'rev' not in 线值 or not isinstance(线值['rev'],str):#rev 必须是字符串
        raise 客户端模块错误('client-modules: boot manifest rev must be a string')#不合格
    if 'release' in 线值:#发行在场才解码
        发行=解码发行(线值['release'])#解码
        if 发行 is 畸形发行:#畸形
            raise 客户端模块错误('client-modules: boot manifest release must carry a string version and an optional string commit')#不合格
    else:#缺席
        发行=None#无发行
    if 'entries' not in 线值 or not isinstance(线值['entries'],list):#entries 必须是数组
        raise 客户端模块错误('client-modules: boot manifest entries must be an array')#不合格
    if 'batches' not in 线值 or not isinstance(线值['batches'],list):#batches 必须是数组
        raise 客户端模块错误('client-modules: boot manifest batches must be an array')#不合格
    模块字段列表=[]#尚无 initialUrl
    插件列表=[]#插件行
    已见条目标识=set()#已见 id
    for 值 in 线值['entries']:#逐行
        if not isinstance(值,dict):#每行必须是对象
            raise 客户端模块错误('client-modules: boot manifest entry is not an object')#非对象
        有标识='id' in 值 and isinstance(值['id'],str)#id 形态
        位置='"'+值['id']+'"' if 有标识 else 紧凑json编码(值)#诊断位置
        网址合格='url' in 值 and isinstance(值['url'],str)#url
        修订合格='rev' in 值 and isinstance(值['rev'],str)#rev
        if (not 有标识) or (not 网址合格) or (not 修订合格):#三个字符串字段
            raise 客户端模块错误('client-modules: boot manifest entry '+位置+' must carry string id/url/rev')#缺字段
        if 值['id'] in 已见条目标识:#重复 id
            raise 客户端模块错误('client-modules: duplicate graph entry "'+值['id']+'"')#重复
        已见条目标识.add(值['id'])#记下
        主语='boot manifest entry '+位置#诊断主语
        依赖=可选字符串数组(主语,'inject',值['inject'] if 'inject' in 值 else 缺席)#可选 inject
        外部=可选字符串数组(主语,'external',值['external'] if 'external' in 值 else 缺席)#可选 external
        if 'immediately' in 值 and not isinstance(值['immediately'],bool):#在场则必须是布尔
            raise 客户端模块错误('client-modules: boot manifest entry '+位置+' immediately must be a boolean')#不合格
        模块字段列表.append({#模块字段
            'id':值['id'],#包名
            'url':值['url'],#单资源 URL
            'rev':值['rev'],#修订
            'inject':[] if 依赖 is None else list(依赖),#缺省空
            'external':[] if 外部 is None else list(外部),#缺省空
        })#字段结束
        插件列表.append({#插件行
            'id':值['id'],#包名
            'inject':[] if 依赖 is None else list(依赖),#缺省空
            'immediately':值['immediately'] is True if 'immediately' in 值 else False,#缺省 false
        })#插件行结束
    条目标识集=set(行['id'] for 行 in 模块字段列表)#图上全部 id
    初始网址表={}#条目到初始批 URL
    批网址集=set()#已见批 URL
    for 值 in 线值['batches']:#逐批
        if not isinstance(值,dict):#每批必须是对象
            raise 客户端模块错误('client-modules: boot manifest batch is not an object')#非对象
        阶段=值['phase'] if 'phase' in 值 else None#阶段
        if 阶段!='bootstrap' and 阶段!='application':#必须是已知阶段
            raise 客户端模块错误('client-modules: boot manifest batch phase must be "bootstrap" or "application", received '+紧凑json编码(阶段))#阶段非法
        批网址合格='url' in 值 and isinstance(值['url'],str)#url
        批修订合格='rev' in 值 and isinstance(值['rev'],str)#rev
        if (not 批网址合格) or (not 批修订合格):#两个字符串字段
            raise 客户端模块错误('client-modules: boot manifest '+阶段+' batch must carry string url/rev')#缺字段
        if 值['url'] in 批网址集:#批 URL 不得重复
            raise 客户端模块错误('client-modules: boot manifest carries duplicate batch URL '+紧凑json编码(值['url']))#重复
        批网址集.add(值['url'])#记下
        条目=可选字符串数组('boot manifest '+阶段+' batch','entries',值['entries'] if 'entries' in 值 else 缺席)#批内条目
        if 条目 is None or len(条目)==0:#必须非空
            raise 客户端模块错误('client-modules: boot manifest '+阶段+' batch entries must be a non-empty string array')#空批
        for 标识 in 条目:#逐条目归属
            if 标识 not in 条目标识集:#必须在图上
                raise 客户端模块错误('client-modules: boot manifest '+阶段+' batch names unknown entry "'+标识+'"')#未知
            if 标识 in 初始网址表:#不得跨批重复
                raise 客户端模块错误('client-modules: boot manifest entry "'+标识+'" belongs to more than one batch')#重复归属
            初始网址表[标识]=值['url']#记下初始 URL
    模块列表=[]#完整模块行
    for 行 in 模块字段列表:#补上 initialUrl
        if 行['id'] not in 初始网址表:#必须有批
            raise 客户端模块错误('client-modules: boot manifest entry "'+行['id']+'" belongs to no initial-load batch')#无批
        完整=dict(行)#拷字段
        完整['initialUrl']=初始网址表[行['id']]#所属批 URL
        模块列表.append(完整)#完整行
    清单={'rev':线值['rev'],'modules':模块列表,'plugins':插件列表}#两种视图
    if 发行 is not None:#有发行才写入
        清单['release']=发行#发行
    return 清单#清单

import json#JSON 选择器
import re#chunk 名与 rev 查询
from threading import Event as 事件#飞行到达门闩
from .清单 import 客户端模块错误,剥客户端后缀#本包异常与后缀剥离
from .条目 import 客户端条目表#页面条目调和
from .条目生命周期 import 移除包拥有样式#拆除包拥有样式

__all__=['客户端模块系统','认领样式']#仅中文公开名

#常量
客户端分块名=re.compile(r'^client\.[A-Za-z0-9][A-Za-z0-9._-]*\.js\Z',re.ASCII)#包内 chunk 文件名

#工具
def 认领样式(标识):
    """认领并清点工厂物化期间注入的 style 标签。"""
    if 'document' not in globals():#无 DOM
        return []#空
    文档=globals()['document']#浏览器 document
    for 元素 in 文档.querySelectorAll('style:not([data-plugin])'):#未打标的 style
        元素.setAttribute('data-plugin',标识)#标给本插件
    选择器='style[data-plugin='+json.dumps(标识,ensure_ascii=False,separators=(',',':'),allow_nan=False)+']'#本插件选择器
    拥有=[]#本插件拥有的 css 键
    for 元素 in 文档.querySelectorAll(选择器):#本插件的 style
        属性=元素.getAttribute('data-plugin-css')#css 键
        拥有.append(属性 if 属性 is not None else 标识)#缺属性则回退 id
    return 拥有#归本插件的键

def 默认加载包(网址):
    """同源外部经典脚本；阻塞到 load/error，失败原样抛。"""
    if 'document' not in globals():#无 DOM
        raise 客户端模块错误('client-modules: bundle script '+网址+' failed to load')#无法加载
    文档=globals()['document']#浏览器 document
    元素=文档.createElement('script')#经典脚本元素
    元素.async=True#DOM 属性不译
    元素.src=网址#包 URL
    完成=事件()#脚本结算门
    错误箱=[]#失败箱
    def 成功(_事件=None):
        """卸掉元素并放行。"""
        元素.remove()#卸掉
        完成.set()#放行
    def 失败(_事件=None):
        """卸掉元素、记下错误并放行。"""
        元素.remove()#卸掉
        错误箱.append(客户端模块错误('client-modules: bundle script '+网址+' failed to load'))#失败
        完成.set()#放行
    元素.addEventListener('load',成功,{'once':True})#只听一次
    元素.addEventListener('error',失败,{'once':True})#只听一次
    文档.head.append(元素)#挂到 head
    完成.wait()#阻塞到结算
    if len(错误箱)>0:#失败
        raise 错误箱[0]#原样抛

def 改写修订(网址,修订):
    """替换 rev 查询，同时保留绝对、协议相对或路径相对形态。"""
    if re.search(r'[?&]rev=[^&#]*',网址) is None:#没有 rev 查询
        raise 客户端模块错误('client-modules: bundle URL '+网址+' has no revision')#大声失败
    return re.sub(r'([?&]rev=)[^&#]*',lambda 匹配:匹配.group(1)+修订,网址,count=1)#换上新 rev

def 分块标识(拥有标识,文件名):
    """一个包内 chunk 的模块表键。"""
    return 拥有标识+'/'+文件名#拥有包/文件名

def 分块网址(行,文件名,修订):
    """对照包的单资源 URL 与当前修订解析兄弟 chunk。"""
    网址=改写修订(行['url'],修订)#带修订的组合 URL
    标记='/??'#组合标记
    资源起点=网址.find(标记)#资源起点
    修订起点=网址.find('&rev=',资源起点+len(标记)) if 资源起点>=0 else -1#修订起点
    资源=None if 资源起点<0 or 修订起点<0 else 网址[资源起点+len(标记):修订起点]#资源段
    if 资源!=行['id']+'/client.js':#必须是该包 client.js 组合
        raise 客户端模块错误('client-modules: cannot resolve chunk '+json.dumps(文件名,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' from bundle URL '+网址)
    return 网址[:资源起点]+'/'+行['id']+'/'+文件名+'?'+网址[修订起点+1:]#单文件 URL

#
class 客户端模块系统:
    """状态表加上到达/物化机械，实现客户端模块加载器。"""
    def __init__(自身,选项):
        """在已解析的启动行上建造模块系统。选项是 dict。"""
        清单=选项['manifest']#已解析启动清单
        自身.version='client'#加载器版本标签
        自身.manifest=清单#可被调和更新
        自身.loadCache={}#已物化记录
        种子源=选项['staticModules'] if 'staticModules' in 选项 else None#平台种子
        自身.种子=dict(种子源) if 种子源 is not None else {}#种子表
        自身.工厂表={}#表键 → {factory, rev}
        自身.启动标识集=set()#启动模块 id
        自身.进行中到达={}#URL → 飞行去重条目
        自身.代次表={}#拥有包 → 代次
        自身.重载目标={}#包 id → {url, rev}
        自身.正在物化=set()#正在物化的 id
        自身.图行={}#启动图行
        自身.加载包=选项['loadBundle'] if 'loadBundle' in 选项 and 选项['loadBundle'] is not None else 默认加载包#加载钩；须同步阻塞
        自身.entries=客户端条目表(自身,{#页面条目表
            'update':自身.更新清单,#更新描述符
            'invalidateForReplacement':自身.替换前失效,#替换前失效
            'prune':自身.裁剪,#裁剪未引用
        })#结束条目表
        for 行 in 清单['modules']:#索引启动行
            自身.图行[行['id']]=行#写入图
        启动标识=剥客户端后缀(选项['bootstrapModule']['id'])#规范化启动 id
        自身.启动标识集.add(启动标识)#记下启动 id
        自身.loadCache[启动标识]={#启动模块已物化
            'id':启动标识,#包名
            'exports':选项['bootstrapModule']['exports'],#已物化导出
            'styles':[],#启动无样式记账
            'edges':set(),#无边
        }#结束 loadCache
        目标=选项['registrationTarget']#HTML 登记门面
        if 目标['mode']!='queue':#必须仍在队列模式
            raise 客户端模块错误('client-modules: window.__ModuleLoader__.create called after module-system boot')#双启动
        待处理=目标['pendingQueue']#待处理队列
        积压=list(待处理)#拷出
        待处理.clear()#掏空
        目标['mode']='live'#切到活模式
        def 活登记(交接):
            """活登记汇。"""
            自身.登记(交接)#收下工厂
        目标['load']=活登记#活汇
        for 交接 in 积压:#排空队列
            目标['load'](交接)#登记

    def 替换前失效(自身,标识,修订):
        """条目替换前失效；启动包不可替换。"""
        if 标识 in 自身.启动标识集:#启动包
            raise 客户端模块错误('client-modules: replacing bootstrap module '+标识+' requires a page reload')#不可替换
        自身.invalidate(标识,修订)#失效

    def 登记(自身,交接):
        """登记一个打包工厂；拒绝未失效却执行两次的脚本。"""
        拥有标识=剥客户端后缀(交接['id'])#规范化拥有包
        分块=交接['chunk'] if 'chunk' in 交接 else None#可选 chunk
        if 分块 is not None and 客户端分块名.match(分块) is None:#非法 chunk 名
            raise 客户端模块错误('client-modules: invalid package-local chunk '+json.dumps(分块,ensure_ascii=False,separators=(',',':'),allow_nan=False))
        标识=拥有标识 if 分块 is None else 分块标识(拥有标识,分块)#表键
        if 标识 in 自身.启动标识集 or 标识 in 自身.工厂表:#启动或已登记
            诊断名=交接['id'] if 分块 is None else 标识#诊断名
            raise 客户端模块错误('client-modules: duplicate factory registration for "'+诊断名+'" (bundle executed twice without invalidate?)')
        重载=自身.重载目标[拥有标识] if 拥有标识 in 自身.重载目标 else None#重载目标
        图行=自身.图行[拥有标识] if 拥有标识 in 自身.图行 else None#图行
        修订=None#修订
        if 重载 is not None:#有重载
            修订=重载['rev']#重载修订
        elif 图行 is not None:#有图行
            修订=图行['rev']#图修订
        自身.工厂表[标识]={'factory':交接['factory'],'rev':修订}#收下工厂

    def 等待到达(自身,条目):
        """等同一 URL 的在飞到达；失败原样抛。"""
        条目['完成'].wait()#等门
        if len(条目['错误'])>0:#失败
            raise 条目['错误'][0]#原样抛

    def 到达(自身,行):
        """加载一行图，使其工厂登记上；内部阻塞。"""
        标识=行['id']#行身份
        if 标识 in 自身.loadCache or 标识 in 自身.工厂表:#已物化或已登记
            return#跳过
        重载=自身.重载目标[标识] if 标识 in 自身.重载目标 else None#HMR 重载目标
        网址=重载['url'] if 重载 is not None else 行['initialUrl']#重载优先，否则初始批 URL
        在飞=自身.进行中到达[网址] if 网址 in 自身.进行中到达 else None#同 URL 进行中
        if 在飞 is not None:#共享进行中
            自身.等待到达(在飞)#等同一加载
        else:#尚无进行中
            完成=事件()#本飞门闩
            错误箱=[]#本飞错误
            条目={'完成':完成,'错误':错误箱}#飞行条目
            自身.进行中到达[网址]=条目#记下进行中
            try:#等脚本
                自身.加载包(网址)#同步加载
            except BaseException as 错误:#失败
                错误箱.append(错误)#记下
                raise#原样抛
            finally:#无论成败
                完成.set()#放行等待方
                自身.进行中到达.pop(网址,None)#清进行中
        if 标识 not in 自身.工厂表:#脚本没来登记
            raise 客户端模块错误('client-modules: bundle '+网址+' loaded without registering "'+标识+'" via __ModuleLoader__.load')
        if 重载 is not None and 标识 in 自身.重载目标 and 自身.重载目标[标识] is 重载:#仍是本次重载目标
            del 自身.重载目标[标识]#清掉

    def 按图到达(自身,行,开集=None,已访问=None):
        """在消费方之前登记每个注入包与未解决的动态请求。"""
        if 开集 is None:#默认开集
            开集=[]#空
        if 已访问 is None:#默认已访问
            已访问=set()#空
        try:#环起点
            环起点=开集.index(行['id'])#找环
        except ValueError:#无环
            环起点=-1#无
        if 环起点!=-1:#有环
            raise 客户端模块错误(
                'client-modules: module arrival cycle '+' -> '.join(开集[环起点:]+[行['id']])
                +' (the host must reject this graph before serving it)',
            )
        if 行['id'] in 已访问:#已访问
            return#跳过
        已访问.add(行['id'])#记下访问
        下一=开集+[行['id']]#推进开集
        for 请求 in 行['external']:#动态请求
            标识=剥客户端后缀(请求)#规范化
            if 请求 in 自身.种子 or 标识 in 自身.loadCache:#种子或已物化
                continue#跳过
            if 标识 in 自身.图行:#图上有依赖
                自身.按图到达(自身.图行[标识],下一,已访问)#先到依赖
        for 包名 in 行['inject']:#注入边
            if 包名 in 自身.图行:#图上有依赖
                自身.按图到达(自身.图行[包名],[],已访问)#注入边单独开集
        自身.到达(行)#再到本行

    def 物化(自身,标识,拥有标识=None):
        """物化一个已登记工厂（同步；记在 loadCache）。"""
        if 拥有标识 is None:#默认拥有者即自身
            拥有标识=标识#同键
        if 标识 in 自身.loadCache:#命中缓存
            return 自身.loadCache[标识]#记录
        if 标识 not in 自身.工厂表:#缺工厂
            raise 客户端模块错误('client-modules: no registered factory for "'+标识+'"')#缺工厂
        if 标识 in 自身.正在物化:#重入
            raise 客户端模块错误('client-modules: require cycle through "'+标识+'" (factory-form CJS cannot deliver partial exports)')#环是致命的
        自身.正在物化.add(标识)#标正在物化
        try:#跑工厂
            边=set()#本模块 require 过的 spec
            导出=自身.工厂表[标识]['factory'](自身.造要求(拥有标识,边))#交出 exports
            记录={'id':标识,'exports':导出,'styles':认领样式(拥有标识),'edges':边}#拼记录
            自身.loadCache[标识]=记录#写入缓存
            return 记录#返回记录
        except BaseException:#工厂抛错
            移除包拥有样式(拥有标识)#拆掉已注入样式
            raise#再抛
        finally:#无论成败
            自身.正在物化.discard(标识)#清重入守卫

    def 造要求(自身,拥有标识,边):
        """答给工厂的同步 require，并挂异步 chunk 操作。"""
        def 要求(说明符):
            """种子 → 已物化 → 已登记工厂。"""
            边.add(说明符)#记下边
            if 说明符 in 自身.种子:#平台种子
                return 自身.种子[说明符]#种子
            标识=剥客户端后缀(说明符)#剥 /client
            if 标识 in 自身.loadCache:#命中缓存
                return 自身.loadCache[标识]['exports']#导出
            if 标识 in 自身.工厂表:#现场物化
                return 自身.物化(标识)['exports']#物化导出
            raise 客户端模块错误(
                'client-modules: require("'+说明符+'") missed the module table — not a platform seed word, not a materialized module, '
                +'and no registered package factory (a build-time externals drift, or a dynamic dependency that did not arrive)',
            )
        def 异步要求(说明符):
            """相对 chunk 或普通导入；同步阻塞。"""
            边.add(说明符)#记下边
            if not 说明符.startswith('./'):#非相对
                return 自身.import_(说明符)#走 import
            文件名=说明符[2:]#相对文件名
            if 客户端分块名.match(文件名) is None:#非法相对 chunk
                raise 客户端模块错误('client-modules: invalid relative chunk request '+json.dumps(说明符,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            return 自身.导入分块(拥有标识,文件名)#导入 chunk
        setattr(要求,'async',异步要求)#挂异步操作（TS require.async）
        return 要求#带 async 的 require

    def 导入分块(自身,拥有标识,文件名):
        """加载、登记并物化一个包内动态 chunk；内部阻塞。"""
        标识=分块标识(拥有标识,文件名)#表键
        if 标识 in 自身.loadCache:#已物化
            return 自身.loadCache[标识]['exports']#复用
        if 标识 not in 自身.工厂表:#尚未登记
            代次=自身.代次表[拥有标识] if 拥有标识 in 自身.代次表 else 0#捕获代次
            if 拥有标识 not in 自身.图行:#拥有包不在图上
                raise 客户端模块错误('client-modules: chunk owner "'+拥有标识+'" is not a boot graph entry')
            行=自身.图行[拥有标识]#图行
            修订=None#修订
            if 拥有标识 in 自身.工厂表 and 自身.工厂表[拥有标识]['rev'] is not None:#拥有工厂修订
                修订=自身.工厂表[拥有标识]['rev']#用之
            elif 拥有标识 in 自身.重载目标:#重载修订
                修订=自身.重载目标[拥有标识]['rev']#用之
            else:#图修订
                修订=行['rev']#回退
            网址=分块网址(行,文件名,修订)#chunk URL
            在飞=自身.进行中到达[网址] if 网址 in 自身.进行中到达 else None#进行中
            if 在飞 is not None:#共享
                自身.等待到达(在飞)#等
            else:#新建传输
                完成=事件()#门闩
                错误箱=[]#错误
                条目={'完成':完成,'错误':错误箱}#飞行
                自身.进行中到达[网址]=条目#记下
                try:#加载
                    自身.加载包(网址)#同步
                except BaseException as 错误:#失败
                    错误箱.append(错误)#记下
                    raise#再抛
                finally:#清
                    完成.set()#放行
                    自身.进行中到达.pop(网址,None)#摘
            当前代=自身.代次表[拥有标识] if 拥有标识 in 自身.代次表 else 0#当前代
            if 当前代!=代次:#失效换代
                自身.工厂表.pop(标识,None)#丢掉陈旧工厂
                自身.loadCache.pop(标识,None)#丢掉陈旧记录
                return 自身.导入分块(拥有标识,文件名)#重试
            if 标识 not in 自身.工厂表:#仍未登记
                raise 客户端模块错误('client-modules: bundle '+网址+' loaded without registering "'+标识+'" via __ModuleLoader__.load')
        return 自身.物化(标识,拥有标识)['exports']#物化并返回

    def import_(自身,说明符,父网址=None,属性=None):
        """按文档化分支顺序解析 specifier；内部阻塞后返回导出。"""
        if 说明符 in 自身.种子:#平台种子
            return 自身.种子[说明符]#种子
        标识=剥客户端后缀(说明符)#规范化
        if 标识 in 自身.loadCache:#已物化
            return 自身.loadCache[标识]['exports']#导出
        if 标识 in 自身.图行:#在图上
            自身.按图到达(自身.图行[标识])#先到达
        elif 标识 not in 自身.工厂表:#不在图且无工厂
            raise 客户端模块错误(
                'client-modules: cannot resolve "'+说明符+'" — not a seed word, not a materialized module, '
                +'and not a row in the boot graph (the runtime mirror of the bundle purity gate)',
            )
        return 自身.物化(标识)['exports']#物化并返回

    def prefetch(自身,标识):
        """第一阶段到达：加载条目脚本以登记其工厂；内部阻塞。"""
        规范化=剥客户端后缀(标识)#规范化
        if 规范化 in 自身.loadCache:#已物化
            return#跳过
        if 规范化 not in 自身.图行:#图上没有
            raise 客户端模块错误('client-modules: prefetch("'+标识+'") — not a graph entry')
        自身.按图到达(自身.图行[规范化])#到达整条依赖

    def 更新清单(自身,清单,托管):
        """在任何条目导入其依赖前刷新描述符与无主工厂修订。"""
        for 标识 in 自身.启动标识集:#启动包不得从图消失
            旧有=any(行['id']==标识 for 行 in 自身.manifest['modules'])#旧图有
            新有=any(行['id']==标识 for 行 in 清单['modules'])#新图有
            if 旧有 and not 新有:#被删
                raise 客户端模块错误('client-modules: removing bootstrap module '+标识+' requires a page reload')
        拥有=set(托管)#页面托管的条目
        for 行 in 清单['modules']:#逐行
            刷新=dict(行)#拷行
            刷新['initialUrl']=行['url']#初 URL 用现 URL
            自身.图行[行['id']]=刷新#刷新图行
            缓存修订=None#缓存修订
            if 行['id'] in 自身.工厂表:#有工厂
                缓存修订=自身.工厂表[行['id']]['rev']#工厂修订
            elif 行['id'] in 自身.重载目标:#有重载
                缓存修订=自身.重载目标[行['id']]['rev']#重载修订
            if 行['id'] not in 拥有 and 缓存修订 is not None and 缓存修订!=行['rev']:#无主且修订变
                自身.invalidate(行['id'],行['rev'])#失效
                移除包拥有样式(行['id'])#拆样式
        自身.manifest=清单#写回清单

    def 裁剪(自身,根列表):
        """保留活 Loader 模块及其传递请求，再驱逐未引用图记录。"""
        保留=set(自身.启动标识集)#保留集
        def 访问(说明符):
            """传递访问。"""
            标识=剥客户端后缀(说明符)#规范化
            if 标识 in 保留:#已保留
                return#停
            保留.add(标识)#记下
            行=自身.图行[标识] if 标识 in 自身.图行 else None#图行
            边列表=[]#边
            if 行 is not None:#有行
                边列表.extend(行['external'])#外部
                边列表.extend(行['inject'])#注入
            if 标识 in 自身.loadCache:#有物化边
                边列表.extend(自身.loadCache[标识]['edges'])#require 边
            for 请求 in 边列表:#逐边
                访问(请求)#继续
        for 行 in 自身.manifest['modules']:#清单根
            访问(行['id'])#访问
        for 标识 in 根列表:#Loader 根
            访问(标识)#访问
        for 标识 in list(自身.图行.keys()):#逐图行
            if 标识 in 保留:#仍保留
                continue#跳过
            del 自身.图行[标识]#摘图
            自身.invalidate(标识)#失效
            移除包拥有样式(标识)#拆样式

    def invalidate(自身,标识,修订=None):
        """丢掉条目与 chunk 工厂及物化记录；可选记下重载目标。"""
        规范化=剥客户端后缀(标识)#规范化
        if 规范化 in 自身.启动标识集:#启动模块不失效
            return#停
        自身.代次表[规范化]=(自身.代次表[规范化] if 规范化 in 自身.代次表 else 0)+1#推进代次
        if 规范化 in 自身.图行:#有行
            行=自身.图行[规范化]#图行
            新修订=修订 if 修订 is not None else 行['rev']#新修订
            自身.重载目标[规范化]={'url':改写修订(行['url'],新修订),'rev':新修订}#记下重载
        else:#页内直接登记
            自身.重载目标.pop(规范化,None)#无重载
        for 键 in list(自身.工厂表.keys()):#丢掉工厂
            if 键==规范化 or 键.startswith(规范化+'/client.'):#条目与 chunk
                del 自身.工厂表[键]#删
        for 键 in list(自身.loadCache.keys()):#丢掉物化
            if 键==规范化 or 键.startswith(规范化+'/client.'):#条目与 chunk
                del 自身.loadCache[键]#删

客户端模块系统.import=客户端模块系统.import_#TS 方法名 import；保留字故本体为 import_

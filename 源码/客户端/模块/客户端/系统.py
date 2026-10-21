import re,threading#分块名、修订查询与在飞加载
from pywebbridge import undefined as 未定义#页面上的 undefined
from urllib.parse import quote as 百分号编码#修订进 URL
from ....基础设施.通用工具 import 紧凑json编码#诊断 JSON
from ..异常 import 客户端模块错误#本包异常
from .清单 import 剥客户端后缀#后缀
from .条目 import 客户端条目表#页面条目
from .条目生命周期 import 移除包拥有样式,收成节点#拆样式、节点表收成
from .通告 import 登记握手窗口#传进来的窗口


__all__=['客户端模块系统']#仅中文公开名

客户端分块名=re.compile(r'^client\.[A-Za-z0-9][A-Za-z0-9._-]*\.js\Z')#包内分块文件名


def 默认加载包(网址):
    '这个网页引擎不往浏览器里加载包脚本'
    raise 客户端模块错误('client-modules: 这个网页引擎不往浏览器里加载包脚本 '+网址)#失败


def 改写修订(网址,修订):
    '替换 rev 查询，保留绝对、协议相对或路径相对形态'
    if re.search(r'[?&]rev=[^&#]*',网址) is None:#没有 rev
        raise 客户端模块错误('client-modules: bundle URL '+网址+' has no revision')#大声失败
    def 替换(匹配):
        '换上百分号编码后的修订'
        return 匹配.group(1)+百分号编码(修订,safe='')#新查询
    return re.sub(r'([?&]rev=)[^&#]*',替换,网址,count=1)#只换第一处


def 描述错误(错误):
    '抛出值的消息。Error 取消息，其余转成字符串'
    if isinstance(错误,Exception):#异常
        return str(错误)#消息
    return str(错误)#其它


def 分块标识(拥有标识,文件名):
    '一个包内分块的模块表键'
    return 拥有标识+'/'+文件名#拥有包/文件名


def 未打标样式(文档):
    '工厂运行前已经在页面上、且没有 data-plugin 的 style'
    if 文档 is None or 文档 is 未定义:#没有这次握手的文档
        return []#空
    return 收成节点(文档.querySelectorAll('style:not([data-plugin])'))#未打标


def 认领样式(标识,之前,文档):
    '认领工厂物化期间新注入的 style，并返回 data-plugin-css'
    if 文档 is None or 文档 is 未定义:#没有这次握手的文档
        return []#空
    for 元素 in 未打标样式(文档):#现在的未打标
        已有=False#物化前就有
        for 旧 in 之前:#对照身份
            if 旧 is 元素:#同一个节点
                已有=True#不是新的
                break#不用再看
        if not 已有:#物化期间出现
            元素.setAttribute('data-plugin',标识)#认领
    拥有=[]#css 键
    选择器='style[data-plugin='+紧凑json编码(标识)+']'#本插件
    for 元素 in 收成节点(文档.querySelectorAll(选择器)):#本插件的 style
        属性=元素.getAttribute('data-plugin-css')#css 键
        拥有.append(标识 if 属性 is None else 属性)#缺属性则回退 id
    return 拥有#键列表


class 客户端模块系统:
    '状态表加上到达与物化。version 固定为 client'
    def __init__(自身,选项):
        '在已解析的启动行上建造。选项含 manifest、种子、登记门面、启动模块'
        清单=选项['manifest']#已解析清单
        自身.version='client'#加载器版本
        自身.manifest=清单#可被调和更新
        自身.loadCache={}#已物化记录
        自身.种子=dict(选项['staticModules'])#平台种子
        自身.工厂表={}#表键到工厂与修订
        自身.启动标识集=set()#启动模块
        自身.进行中到达={}#地址到在飞加载
        自身.代次表={}#拥有包到代次
        自身.重载目标={}#包 id 到单资源地址
        自身.正在物化=set()#重入守卫
        自身.图行={}#启动图行
        自身.导入错误表={}#最近一次导入或预取失败
        自身.文档=选项.get('document')#这次握手的文档，样式认领用它
        if 自身.文档 is not None:#有传进来的文档
            登记握手窗口(自身.文档.defaultView)#窗口用这一份，不许再创建
        自身.失败包网址=set()#已经失败、不再重放的批地址
        自身.已执行包网址=set()#脚本已经执行过的地址
        自身.加载包=默认加载包 if 选项.get('loadBundle') is None else 选项['loadBundle']#加载钩，须阻塞
        自身.entries=客户端条目表(自身,{#页面条目
            'update':自身.更新清单,#刷新描述符
            'invalidateForReplacement':自身.替换前失效,#替换前失效
            'prune':自身.裁剪,#裁剪
        })#条目表结束
        for 行 in 清单['modules']:#索引启动行
            自身.图行[行['id']]=行#写入
        启动标识=剥客户端后缀(选项['bootstrapModule']['id'])#启动包
        自身.启动标识集.add(启动标识)#记下
        自身.loadCache[启动标识]={#启动模块已经物化
            'id':启动标识,#包名
            'exports':选项['bootstrapModule']['exports'],#导出
            'styles':[],#启动不记样式
            'edges':set(),#无边
        }#记录结束
        目标=选项['registrationTarget']#HTML 门面
        if 目标.mode!='queue':#必须仍在队列模式
            raise 客户端模块错误('client-modules: window.__ModuleLoader__.create called after module-system boot')#双启动
        队列=目标.pendingQueue#页面上的队列。没有方法时已经是数组
        if isinstance(队列,list):#帧把纯数据数组交成列表
            积压=队列
            目标.pendingQueue=[]#页面上的队列掏空
        else:#仍是页面数组。不能用 for 遍历句柄：越界下标是 undefined，不会停
            取出=队列.splice(0)#掏空并取出
            if isinstance(取出,list):
                积压=取出
            else:
                长度=取出.length#数组长度是数值
                if isinstance(长度,int) is not True:
                    长度=0
                积压=[]
                下标=0
                while 下标<长度:
                    积压.append(取出[下标])
                    下标=下标+1
        目标.mode='live'#先切到活模式
        def 活登记(交接):
            '活登记汇'
            自身.登记(交接)#收下工厂
        目标.load=活登记#活汇
        for 交接 in 积压:#排空队列
            目标.load(交接)#登记

    def 替换前失效(自身,标识,修订):
        '条目替换前失效。启动包不能替换'
        if 标识 in 自身.启动标识集:#启动包
            raise 客户端模块错误('client-modules: replacing bootstrap module '+标识+' requires a page reload')#要刷新页面
        自身.invalidate(标识,修订)#失效

    def 登记(自身,交接):
        '登记一个打包工厂。未失效却执行两次则拒绝'
        拥有标识=剥客户端后缀(交接['id'])#拥有包
        分块=交接['chunk'] if 'chunk' in 交接 else None#可选分块
        if 分块 is not None and 客户端分块名.match(分块) is None:#非法分块名
            raise 客户端模块错误('client-modules: invalid package-local chunk '+紧凑json编码(分块))#非法
        标识=拥有标识 if 分块 is None else 分块标识(拥有标识,分块)#表键
        if 标识 in 自身.启动标识集 or 标识 in 自身.工厂表:#启动或已登记
            诊断名=交接['id'] if 分块 is None else 标识#诊断名
            raise 客户端模块错误('client-modules: duplicate factory registration for "'+诊断名+'" (bundle executed twice without invalidate?)')#重复
        重载=自身.重载目标.get(拥有标识)#重载目标
        图行=自身.图行.get(拥有标识)#图行
        修订=None#修订
        if 重载 is not None:#有重载
            修订=重载['rev']#重载修订
        elif 图行 is not None:#有图行
            修订=图行['rev']#图修订
        自身.工厂表[标识]={'factory':交接['factory'],'rev':修订}#收下

    def 共享加载(自身,网址):
        '同一地址只跑一次在飞加载。失败不记入已执行'
        在飞=自身.进行中到达.get(网址)#进行中
        if 在飞 is not None:#共享
            在飞['完成'].wait()#等
            if len(在飞['错误'])>0:#失败
                raise 在飞['错误'][0]#原样抛
            return#成功
        完成=threading.Event()#本飞门
        错误箱=[]#本飞错误
        自身.进行中到达[网址]={'完成':完成,'错误':错误箱}#记下
        try:#加载
            自身.加载包(网址)#阻塞加载
            自身.已执行包网址.add(网址)#执行过
        except BaseException as 错误:#失败
            错误箱.append(错误)#记下
            raise#再抛
        finally:#放行等待方
            完成.set()#放行
            自身.进行中到达.pop(网址,None)#摘掉

    def 到达(自身,行):
        '加载一行，使它的工厂登记上。批失败后退到单资源地址'
        标识=行['id']#行身份
        if 标识 in 自身.loadCache or 标识 in 自身.工厂表:#已物化或已登记
            return#跳过
        重载=自身.重载目标.get(标识)#热更新目标
        首选=行['initialUrl'] if 重载 is None else 重载['url']#首选地址
        回退=None#单资源回退
        if 重载 is None and 行['url']!=首选:#批地址失败后用单资源
            回退=行['url']#回退
        失败=[]#尝试说明
        def 尝试(网址):
            '跑一次传输。登记上、传输失败、或加载了但没登记'
            try:#传输
                自身.共享加载(网址)#加载
            except BaseException as 错误:#传输失败
                失败.append(网址+': '+描述错误(错误))#记下
                return 'transport-failed'#可再试一次
            if 标识 in 自身.工厂表:#登记上了
                return 'registered'#成功
            失败.append(网址+': loaded without registering "'+标识+'" via __ModuleLoader__.load')#没登记
            return 'not-registered'#不能重放这一个批
        结局='transport-failed'#默认
        if 首选 in 自身.失败包网址:#这一个批已经失败过
            失败.append(首选+': skipped after an earlier failure of this bundle')#跳过
        elif 回退 is not None and 首选 in 自身.已执行包网址:#批已经跑过且这行仍缺
            失败.append(首选+': already executed without registering "'+标识+'"')#不能重放
            结局='not-registered'#直接回退
            自身.失败包网址.add(首选)#记住
        else:#尝试首选
            结局=尝试(首选)#第一次
            if 结局=='transport-failed':#传输失败再试一次
                结局=尝试(首选)#第二次
            if 结局!='registered' and 回退 is not None:#批失败才记住
                自身.失败包网址.add(首选)#记住
        if 结局!='registered' and 回退 is not None:#回退单资源
            结局=尝试(回退)#单资源
        if 结局!='registered':#都没登记
            raise 客户端模块错误('client-modules: could not load "'+标识+'": '+'; '.join(失败))#汇总
        if 重载 is not None and 自身.重载目标.get(标识) is 重载:#仍是这一次重载
            del 自身.重载目标[标识]#清掉

    def 按图到达(自身,行,开集=None,已访问=None):
        '在消费方之前让注入包和动态请求先到'
        if 开集 is None:#默认开集
            开集=[]#空
        if 已访问 is None:#默认已访问
            已访问=set()#空
        try:#环起点
            环起点=开集.index(行['id'])#找
        except ValueError:#没有
            环起点=-1#无
        if 环起点!=-1:#有环
            raise 客户端模块错误(
                'client-modules: module arrival cycle '+' -> '.join(开集[环起点:]+[行['id']])
                +' (the host must reject this graph before serving it)',
            )#环
        if 行['id'] in 已访问:#已经到过
            return#跳过
        已访问.add(行['id'])#记下
        下一=开集+[行['id']]#推进
        for 请求 in 行['external']:#动态请求
            依赖标识=剥客户端后缀(请求)#规范化
            if 请求 in 自身.种子 or 依赖标识 in 自身.loadCache:#种子或已物化
                continue#跳过
            依赖=自身.图行.get(依赖标识)#图上的依赖
            if 依赖 is not None:#有依赖行
                自身.到达依赖(行['id'],依赖,下一,已访问)#先到依赖
        for 包名 in 行['inject']:#注入边
            依赖=自身.图行.get(包名)#图上的依赖
            if 依赖 is not None:#有依赖行
                自身.到达依赖(行['id'],依赖,[],已访问)#注入边单独开集
        自身.到达(行)#再到本行

    def 到达依赖(自身,消费标识,依赖,开集,已访问):
        '依赖失败时带上消费方，读起来是一条链'
        try:#到达依赖
            自身.按图到达(依赖,开集,已访问)#先到
        except BaseException as 错误:#依赖失败
            raise 客户端模块错误(
                'client-modules: "'+消费标识+'" not loaded because dependency "'+依赖['id']+'" failed: '+描述错误(错误),
            ) from 错误#带上原因

    def 物化(自身,标识,拥有标识=None):
        '物化已登记工厂。同步，结果记在 loadCache'
        if 拥有标识 is None:#默认拥有者就是自己
            拥有标识=标识#同键
        已有=自身.loadCache.get(标识)#缓存
        if 已有 is not None:#命中
            return 已有#记录
        已登记=自身.工厂表.get(标识)#工厂
        if 已登记 is None:#没有工厂
            raise 客户端模块错误('client-modules: no registered factory for "'+标识+'"')#缺工厂
        if 标识 in 自身.正在物化:#重入
            raise 客户端模块错误('client-modules: require cycle through "'+标识+'" (factory-form CJS cannot deliver partial exports)')#环是致命的
        自身.正在物化.add(标识)#标上
        之前=未打标样式(自身.文档)#物化前的样式
        try:#跑工厂
            边=set()#require 过的说明符
            导出=已登记['factory'](自身.造要求(拥有标识,边))#导出
            记录={'id':标识,'exports':导出,'styles':认领样式(拥有标识,之前,自身.文档),'edges':边}#记录
            自身.loadCache[标识]=记录#写入
            return 记录#返回
        except BaseException:#工厂抛错
            认领样式(拥有标识,之前,自身.文档)#先认领再拆，避免留下无主样式
            移除包拥有样式(拥有标识,自身.文档)#拆掉
            raise#再抛
        finally:#无论成败
            自身.正在物化.discard(标识)#清守卫

    def 造要求(自身,拥有标识,边):
        '交给工厂的同步 require，并挂上 async 分块操作'
        def 要求(说明符):
            '种子、已物化、已登记工厂'
            边.add(说明符)#记下边
            if 说明符 in 自身.种子:#平台种子
                return 自身.种子[说明符]#种子
            标识=剥客户端后缀(说明符)#剥 /client
            记录=自身.loadCache.get(标识)#缓存
            if 记录 is not None:#已物化
                return 记录['exports']#导出
            if 标识 in 自身.工厂表:#现场物化
                return 自身.物化(标识)['exports']#导出
            raise 客户端模块错误(
                'client-modules: require("'+说明符+'") missed the module table — not a platform seed word, not a materialized module, '
                +'and no registered package factory (a build-time externals drift, or a dynamic dependency that did not arrive)',
            )#没找到
        def 异步要求(说明符):
            '相对分块或普通导入。这里阻塞到完成'
            边.add(说明符)#记下边
            if not 说明符.startswith('./'):#不是相对路径
                return 自身.import_(说明符)#走 import
            文件名=说明符[2:]#相对文件名
            if 客户端分块名.match(文件名) is None:#非法相对分块
                raise 客户端模块错误('client-modules: invalid relative chunk request '+紧凑json编码(说明符))#非法
            return 自身.导入分块(拥有标识,文件名)#导入分块
        setattr(要求,'async',异步要求)#协议名 async
        return 要求#带 async 的 require

    def 导入分块(自身,拥有标识,文件名):
        '加载、登记并物化一个包内动态分块'
        标识=分块标识(拥有标识,文件名)#表键
        已有=自身.loadCache.get(标识)#缓存
        if 已有 is not None:#已物化
            return 已有['exports']#复用
        if 标识 not in 自身.工厂表:#尚未登记
            代次=自身.代次表.get(拥有标识,0)#捕获代次
            行=自身.图行.get(拥有标识)#拥有包的图行
            if 行 is None:#不在图上
                raise 客户端模块错误('client-modules: chunk owner "'+拥有标识+'" is not a boot graph entry')#没有图行
            修订=None#修订
            拥有工厂=自身.工厂表.get(拥有标识)#拥有工厂
            重载=自身.重载目标.get(拥有标识)#重载
            if 拥有工厂 is not None and 拥有工厂['rev'] is not None:#工厂修订
                修订=拥有工厂['rev']#用之
            elif 重载 is not None:#重载修订
                修订=重载['rev']#用之
            else:#图修订
                修订=行['rev']#回退
            网址=改写修订(行['url'],修订)#带修订的组合地址
            标记='/??'#组合标记
            资源起点=网址.find(标记)#资源起点
            修订起点=网址.find('&rev=',资源起点+len(标记)) if 资源起点>=0 else -1#修订起点
            资源=None if 资源起点<0 or 修订起点<0 else 网址[资源起点+len(标记):修订起点]#资源段
            if 资源!=行['id']+'/client.js':#必须是该包的 client.js
                raise 客户端模块错误('client-modules: cannot resolve chunk '+紧凑json编码(文件名)+' from bundle URL '+网址)#解析不了
            分块地址=网址[:资源起点]+'/'+行['id']+'/'+文件名+'?'+网址[修订起点+1:]#单文件地址
            自身.共享加载(分块地址)#加载分块脚本
            if 自身.代次表.get(拥有标识,0)!=代次:#失效换代
                自身.工厂表.pop(标识,None)#丢掉陈旧工厂
                自身.loadCache.pop(标识,None)#丢掉陈旧记录
                return 自身.导入分块(拥有标识,文件名)#重试
            if 标识 not in 自身.工厂表:#仍未登记
                raise 客户端模块错误('client-modules: bundle '+分块地址+' loaded without registering "'+标识+'" via __ModuleLoader__.load')#没登记
        return 自身.物化(标识,拥有标识)['exports']#物化

    def import_(自身,说明符,父网址=None,属性=None):
        '按种子、缓存、图行、工厂的顺序解析。父网址与属性不参与'
        if 说明符 in 自身.种子:#平台种子
            return 自身.种子[说明符]#种子
        标识=剥客户端后缀(说明符)#规范化
        已有=自身.loadCache.get(标识)#缓存
        if 已有 is not None:#已物化
            return 已有['exports']#导出
        行=自身.图行.get(标识)#图行
        if 行 is None:#不在图上
            if 标识 in 自身.工厂表:#有工厂就物化
                return 自身.物化(标识)['exports']#导出
            raise 客户端模块错误(
                'client-modules: cannot resolve "'+说明符+'" — not a seed word, not a materialized module, '
                +'and not a row in the boot graph (the runtime mirror of the bundle purity gate)',
            )#解析不了
        def 操作():
            '先按图到达再物化'
            自身.按图到达(行)#到达
            return 自身.物化(标识)['exports']#导出
        return 自身.记录导入错误(标识,操作)#记下失败

    def prefetch(自身,标识):
        '只登记工厂，不物化。已物化的启动包直接返回'
        规范化=剥客户端后缀(标识)#规范化
        if 规范化 in 自身.loadCache:#已物化
            return#跳过
        行=自身.图行.get(规范化)#图行
        if 行 is None:#不在图上
            raise 客户端模块错误('client-modules: prefetch("'+标识+'") — not a graph entry')#没有图行
        def 操作():
            '按图到达'
            自身.按图到达(行)#到达
        自身.记录导入错误(规范化,操作)#记下失败

    def importError(自身,标识):
        '这一行最近一次 import 或 prefetch 的失败。没有或已经成功则 None'
        return 自身.导入错误表.get(剥客户端后缀(标识))#记录

    def 记录导入错误(自身,标识,操作):
        '跑图行操作。成功清掉记录，失败记下再抛'
        try:#跑
            结果=操作()#结果
            自身.导入错误表.pop(标识,None)#成功则清
            return 结果#返回
        except Exception as 错误:#失败
            自身.导入错误表[标识]=错误#记下
            raise#再抛

    def 更新清单(自身,清单,托管):
        '任何条目导入依赖之前，刷新描述符和无主工厂的修订'
        for 标识 in 自身.启动标识集:#启动包不能从图上消失
            旧有=any(行['id']==标识 for 行 in 自身.manifest['modules'])#旧图有
            新有=any(行['id']==标识 for 行 in 清单['modules'])#新图有
            if 旧有 and not 新有:#被删
                raise 客户端模块错误('client-modules: removing bootstrap module '+标识+' requires a page reload')#要刷新页面
        拥有=set(托管)#页面托管的条目
        for 行 in 清单['modules']:#逐行
            刷新=dict(行)#拷
            刷新['initialUrl']=行['url']#初地址改成当前单资源地址
            自身.图行[行['id']]=刷新#刷新
            缓存修订=None#已缓存修订
            工厂=自身.工厂表.get(行['id'])#工厂
            重载=自身.重载目标.get(行['id'])#重载
            if 工厂 is not None:#有工厂
                缓存修订=工厂['rev']#工厂修订
            elif 重载 is not None:#有重载
                缓存修订=重载['rev']#重载修订
            if 行['id'] not in 拥有 and 缓存修订 is not None and 缓存修订!=行['rev']:#无主且修订变了
                自身.invalidate(行['id'],行['rev'])#失效
                移除包拥有样式(行['id'],自身.文档)#拆样式
        自身.manifest=清单#写回

    def 裁剪(自身,根列表):
        '留下活着的加载器模块和它们传递请求到的记录，再丢掉其余图行'
        保留=set(自身.启动标识集)#保留集
        def 访问(说明符):
            '传递访问'
            标识=剥客户端后缀(说明符)#规范化
            if 标识 in 保留:#已经留下
                return#停
            保留.add(标识)#记下
            行=自身.图行.get(标识)#图行
            边列表=[]#边
            if 行 is not None:#有行
                边列表.extend(行['external'])#外部
                边列表.extend(行['inject'])#注入
            记录=自身.loadCache.get(标识)#物化记录
            if 记录 is not None:#有 require 边
                边列表.extend(记录['edges'])#边
            for 请求 in 边列表:#逐边
                访问(请求)#继续
        for 行 in 自身.manifest['modules']:#清单根
            访问(行['id'])#访问
        for 标识 in 根列表:#加载器根
            访问(标识)#访问
        for 标识 in list(自身.图行.keys()):#逐图行
            if 标识 in 保留:#仍保留
                continue#跳过
            del 自身.图行[标识]#摘图
            自身.invalidate(标识)#失效
            移除包拥有样式(标识,自身.文档)#拆样式

    def invalidate(自身,标识,修订=None):
        '丢掉条目和分块的工厂与物化记录。可选记下重载地址'
        规范化=剥客户端后缀(标识)#规范化
        if 规范化 in 自身.启动标识集:#启动模块不失效
            return#停
        自身.导入错误表.pop(规范化,None)#清失败记录
        自身.代次表[规范化]=自身.代次表.get(规范化,0)+1#换代
        行=自身.图行.get(规范化)#图行
        if 行 is not None:#有行
            新修订=行['rev'] if 修订 is None else 修订#新修订
            自身.重载目标[规范化]={'url':改写修订(行['url'],新修订),'rev':新修订}#重载目标
        else:#没有图行
            自身.重载目标.pop(规范化,None)#清重载
        前缀=规范化+'/client.'#分块前缀
        for 键 in list(自身.工厂表.keys()):#丢掉工厂
            if 键==规范化 or 键.startswith(前缀):#条目与分块
                del 自身.工厂表[键]#删
        for 键 in list(自身.loadCache.keys()):#丢掉物化
            if 键==规范化 or 键.startswith(前缀):#条目与分块
                del 自身.loadCache[键]#删


setattr(客户端模块系统,'import',客户端模块系统.import_)#协议名 import

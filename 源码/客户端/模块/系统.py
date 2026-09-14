import json,threading#JSON 与脚本加载链
from concurrent.futures import Future as 原生结果#单次操作结果
from .清单 import 客户端模块错误#本包异常

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._结果.done():#尚未结算
            自身._结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._结果.set_exception(错误)#原样拒绝
            else:#非异常
                包装=客户端模块错误('task rejected')#包装拒绝
                包装.原因=错误#附加信息做成属性
                自身._结果.set_exception(包装)#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._结果.result(timeout=超时)#取结果或抛错

__all__=['客户端模块系统','剥客户端后缀','认领样式']#仅中文公开名

def 剥客户端后缀(说明符):
    """插件包 client 子路径与裸 id 命名同一份 exports。"""
    if 说明符.endswith('/client'):#有后缀
        return 说明符[:-len('/client')]#切掉
    return 说明符#原样

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
    """同源外部经典脚本；返回操作任务，由到达内部等待。"""
    if 'document' not in globals():#无 DOM
        raise 客户端模块错误('client-modules: bundle script '+网址+' failed to load')#无法加载
    文档=globals()['document']#浏览器 document
    元素=文档.createElement('script')#经典脚本元素
    元素.async=True#DOM 属性不译
    元素.src=网址#包 URL
    任务=操作任务()#脚本加载任务
    def 成功(_事件=None):
        """卸掉元素并兑现。"""
        元素.remove()#卸掉
        任务.兑现(None)#兑现
    def 失败(_事件=None):
        """卸掉元素并拒绝。"""
        元素.remove()#卸掉
        任务.拒绝(客户端模块错误('client-modules: bundle script '+网址+' failed to load'))#失败
    元素.addEventListener('load',成功,{'once':True})#只听一次
    元素.addEventListener('error',失败,{'once':True})#只听一次
    文档.head.append(元素)#挂到 head
    return 任务#返回任务

class 客户端模块系统:
    """状态表加上到达/物化机械，实现客户端模块加载器。"""
    def __init__(自身,选项):
        """在已解析的启动行上建造模块系统。选项是 dict。"""
        自身.version='client'#加载器版本标签
        自身.loadCache={}#已物化记录
        种子源=选项['staticModules'] if 'staticModules' in 选项 else None#平台种子
        自身.种子=dict(种子源) if 种子源 is not None else {}#种子表
        自身.静态表={}#壳自有模块
        自身.工厂表={}#已登记工厂
        自身.进行中到达={}#进行中预取
        自身.正在物化=set()#正在物化的 id
        自身.图行={}#启动图行
        自身.加载包=选项['loadBundle'] if 'loadBundle' in 选项 and 选项['loadBundle'] is not None else 默认加载包#加载钩
        for 行 in 选项['modules']:#索引启动行
            标识=行['id']#包名
            if 标识 in 自身.图行:#重复 id
                raise 客户端模块错误('client-modules: duplicate graph entry "'+标识+'"')#重复
            自身.图行[标识]=行#写入图
        窗口=globals()#窗口面
        if '__ModuleLoader__' in 窗口 and 窗口['__ModuleLoader__'] is not None:#已安装
            raise 客户端模块错误('client-modules: window.__ModuleLoader__ already installed (double boot?)')#禁止双启动
        def 交接加载(交接):
            """按交接 id 键控登记工厂。交接是 dict。"""
            标识=交接['id']#包名
            工厂=交接['factory']#工厂
            if 标识 in 自身.工厂表:#重复登记
                raise 客户端模块错误('client-modules: duplicate factory registration for "'+标识+'" (bundle executed twice without invalidate?)')#重复
            自身.工厂表[标识]=工厂#收下工厂
        窗口['__ModuleLoader__']={'load':交接加载}#安装登记槽

    def 到达(自身,行):
        """加载一行图，使其工厂登记上；内部阻塞，返回 None。"""
        标识=行['id']#行身份
        网址=行['url']#URL
        if 标识 in 自身.进行中到达:#共享进行中
            自身.进行中到达[标识].等待()#等同一加载
            return None#已登记或失败已抛
        if 标识 in 自身.工厂表:#已登记
            return None#跳过
        任务=自身.加载包(网址)#加载脚本；形态是操作任务
        自身.进行中到达[标识]=任务#记下进行中
        try:#等脚本
            任务.等待()#阻塞到加载结束
            if 标识 not in 自身.工厂表:#脚本没来登记
                raise 客户端模块错误('client-modules: bundle '+网址+' loaded without registering "'+标识+'" via __ModuleLoader__.load')#缺登记
        finally:#无论成败
            自身.进行中到达.pop(标识,None)#清进行中
        return None#工厂已登记

    def 物化(自身,标识):
        """物化一个已登记工厂（同步；记在 loadCache）。"""
        if 标识 in 自身.loadCache:#命中缓存
            return 自身.loadCache[标识]#记录
        if 标识 not in 自身.工厂表:#缺工厂
            raise 客户端模块错误('client-modules: no registered factory for "'+标识+'"')#缺工厂
        if 标识 in 自身.正在物化:#重入
            raise 客户端模块错误('client-modules: require cycle through "'+标识+'" (factory-form CJS cannot deliver partial exports)')#环是致命的
        自身.正在物化.add(标识)#标正在物化
        try:#跑工厂
            边=set()#本模块 require 过的 spec
            导出=自身.工厂表[标识](自身.造要求(边))#交出 exports
            记录={'id':标识,'exports':导出,'styles':认领样式(标识),'edges':边}#拼记录
            自身.loadCache[标识]=记录#写入缓存
            return 记录#返回记录
        finally:#无论成败
            自身.正在物化.discard(标识)#清重入守卫

    def 造要求(自身,边):
        """答给工厂的同步 require。"""
        def 要求(说明符):
            """种子 → 静态 → 已物化 → 已登记工厂。"""
            边.add(说明符)#记下边
            if 说明符 in 自身.种子:#平台种子
                return 自身.种子[说明符]#种子
            if 说明符 in 自身.静态表:#壳自有
                return 自身.静态表[说明符]#静态
            标识=剥客户端后缀(说明符)#剥 /client
            if 标识 in 自身.loadCache:#命中缓存
                return 自身.loadCache[标识]['exports']#导出
            if 标识 in 自身.工厂表:#现场物化
                return 自身.物化(标识)['exports']#物化导出
            raise 客户端模块错误(#三种都不是
                'client-modules: require("'+说明符+'") missed the module table — not a platform seed word, not a shell-own module, '
                +'and no registered factory (a build-time externals drift, or a forbidden cross-plugin value import)',
            )#结束错误
        return 要求#同步 require

    def import_(自身,说明符,父网址=None,属性=None):
        """按文档化分支顺序解析 specifier；内部阻塞后返回导出。"""
        if 说明符 in 自身.种子:#平台种子
            return 自身.种子[说明符]#种子
        if 说明符 in 自身.loadCache:#已物化
            return 自身.loadCache[说明符]['exports']#导出
        if 说明符 in 自身.静态表:#壳自有
            导出=自身.静态表[说明符]#取出模块
            自身.loadCache[说明符]={'id':说明符,'exports':导出,'styles':[],'edges':set()}#写入缓存
            return 导出#返回
        if 说明符 not in 自身.工厂表:#工厂尚未到达
            if 说明符 not in 自身.图行:#图上没有
                raise 客户端模块错误(#解析失败
                    'client-modules: cannot resolve "'+说明符+'" — not a seed word, not a shell-own module, '
                    +'and not a row in the boot graph (the runtime mirror of the bundle purity gate)',
                )#结束错误
            自身.到达(自身.图行[说明符])#先拉包，内部阻塞
        return 自身.物化(说明符)['exports']#物化并返回

    def registerStatic(自身,标识,模块):
        """登记一个外壳自有模块。"""
        if 标识 in 自身.静态表:#禁止重复
            raise 客户端模块错误('client-modules: shell-own module "'+标识+'" registered twice')#重复
        自身.静态表[标识]=模块#写入静态表

    def prefetch(自身,标识):
        """第一阶段到达：加载条目脚本以登记其工厂；内部阻塞。"""
        if 标识 in 自身.静态表:#壳自有无需拉
            return None#跳过
        if 标识 not in 自身.图行:#图上没有
            raise 客户端模块错误('client-modules: prefetch("'+标识+'") — not a graph entry')#图上没有
        return 自身.到达(自身.图行[标识])#拉包登记工厂

    def invalidate(自身,标识):
        """丢掉已登记工厂和已物化记录。"""
        自身.工厂表.pop(标识,None)#丢掉工厂
        自身.loadCache.pop(标识,None)#丢掉物化记录

客户端模块系统.import=客户端模块系统.import_#TS 方法名 import；保留字故本体为 import_

"""ClientModuleSystem — 客户端模块加载器约定背后的实现。

对齐上游 `modules/src/client/system.ts`。公开面仅中文名。
"""
import threading#脚本加载与到达链
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
from .清单 import 客户端模块记录#模块记录形状

class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#本库或外来 thenable

def 已兑现(值=None):#立刻兑现的操作任务
    任务=操作任务()#新任务
    任务.兑现(值)#立刻成功
    return 任务#已完成

__all__=['客户端模块系统','剥客户端后缀','认领样式']#仅中文公开名

def 剥客户端后缀(说明符):#剥 /client 后缀
    """插件包 client 子路径与裸 id 命名同一份 exports。"""
    if 说明符.endswith('/client'):#有后缀
        return 说明符[:-len('/client')]#切掉
    return 说明符#原样

def 认领样式(标识):#认领样式标签
    """认领并清点工厂物化期间注入的 style 标签。"""
    文档=globals().get('document')#浏览器 document
    if 文档 is None:#无 DOM
        return []#空
    for 元素 in 文档.querySelectorAll('style:not([data-plugin])'):#未打标的 style
        元素.setAttribute('data-plugin',标识)#标给本插件
    拥有=[]#本插件拥有的 css 键
    for 元素 in 文档.querySelectorAll('style[data-plugin='+__import__('json').dumps(标识)+']'):#本插件的 style
        拥有.append(元素.getAttribute('data-plugin-css') or 标识)#css 键或回退 id
    return 拥有#归本插件的键

def 默认加载包(网址):#默认包加载钩
    """同源外部经典脚本。"""
    文档=globals().get('document')#浏览器 document
    if 文档 is None:#无 DOM
        raise Exception('client-modules: bundle script '+网址+' failed to load')#无法加载
    元素=文档.createElement('script')#经典脚本元素
    元素.async=True#异步加载
    元素.src=网址#包 URL
    任务=操作任务()#脚本加载任务
    def 成功(_事件=None):#加载成功
        """卸掉元素并兑现。"""
        元素.remove()#卸掉
        任务.兑现(None)#兑现
    def 失败(_事件=None):#加载失败
        """卸掉元素并拒绝。"""
        元素.remove()#卸掉
        任务.拒绝(Exception('client-modules: bundle script '+网址+' failed to load'))#失败
    元素.addEventListener('load',成功,{'once':True})#只听一次
    元素.addEventListener('error',失败,{'once':True})#只听一次
    文档.head.append(元素)#挂到 head
    return 任务#返回任务

class 客户端模块系统:#模块系统
    """状态表加上到达/物化机械，实现客户端模块加载器。"""
    def __init__(自身,选项):#播种并安装登记槽
        """在已解析的启动行上建造模块系统。"""
        自身.version='client'#加载器版本标签
        自身.loadCache={}#已物化记录
        自身.种子=dict(选项.get('staticModules') or {})#平台种子
        自身.静态表={}#壳自有模块
        自身.工厂表={}#已登记工厂
        自身.进行中到达={}#进行中预取
        自身.正在物化=set()#正在物化的 id
        自身.图行={}#启动图行
        自身.加载包=选项.get('loadBundle') or 默认加载包#加载钩
        for 行 in 选项['modules']:#索引启动行
            标识=行['id']#包名
            if 标识 in 自身.图行:#重复 id
                raise Exception('client-modules: duplicate graph entry "'+标识+'"')#重复
            自身.图行[标识]=行#写入图
        窗口=globals()#窗口面
        if 窗口.get('__ModuleLoader__') is not None:#已安装
            raise Exception('client-modules: window.__ModuleLoader__ already installed (double boot?)')#禁止双启动
        def 交接加载(交接):#工厂交接
            """按交接 id 键控登记工厂。"""
            标识=交接['id'] if isinstance(交接,dict) else 交接.id#包名
            工厂=交接['factory'] if isinstance(交接,dict) else 交接.factory#工厂
            if 标识 in 自身.工厂表:#重复登记
                raise Exception('client-modules: duplicate factory registration for "'+标识+'" (bundle executed twice without invalidate?)')#重复
            自身.工厂表[标识]=工厂#收下工厂
        窗口['__ModuleLoader__']={'load':交接加载}#安装登记槽

    def 到达(自身,行):#拉取包
        """加载一行图，使其工厂登记上。"""
        标识=行['id']#行身份
        网址=行['url']#URL
        进行中=自身.进行中到达.get(标识)#进行中预取
        if 进行中 is not None:#共享进行中
            return 进行中#共享
        if 标识 in 自身.工厂表:#已登记
            return 已兑现(None)#跳过
        任务=自身.加载包(网址)#加载脚本
        def 检查登记(_值=None):#脚本加载后检查登记
            """脚本必须经 __ModuleLoader__.load 登记。"""
            if 标识 not in 自身.工厂表:#脚本没来登记
                raise Exception('client-modules: bundle '+网址+' loaded without registering "'+标识+'" via __ModuleLoader__.load')#缺登记
        def 清理(_值=None):#结束则清进行中
            """清进行中到达。"""
            自身.进行中到达.pop(标识,None)#删除
        if _是否thenable(任务):#异步
            链=操作任务()#共享到达任务
            def 跑():#加载后检查并清理
                try:#等脚本
                    _等待(任务)#等加载
                    检查登记()#检查登记
                    清理()#清理
                    链.兑现(None)#成功
                except BaseException as 错误:#失败
                    清理()#清理
                    链.拒绝(错误)#上抛
            threading.Thread(target=跑,daemon=True).start()#后台链
            自身.进行中到达[标识]=链#记下进行中
            return 链#共享任务
        检查登记()#同步路径
        清理()#清理
        return 已兑现(None)#兑现

    def 物化(自身,标识):#跑工厂
        """物化一个已登记工厂（同步；记在 loadCache）。"""
        已有=自身.loadCache.get(标识)#已物化
        if 已有 is not None:#命中缓存
            return 已有#记录
        已登记=自身.工厂表.get(标识)#已登记工厂
        if 已登记 is None:#缺工厂
            raise Exception('client-modules: no registered factory for "'+标识+'"')#缺工厂
        if 标识 in 自身.正在物化:#重入
            raise Exception('client-modules: require cycle through "'+标识+'" (factory-form CJS cannot deliver partial exports)')#环是致命的
        自身.正在物化.add(标识)#标正在物化
        try:#跑工厂
            边=set()#本模块 require 过的 spec
            导出=已登记(自身.造要求(边))#交出 exports
            记录={'id':标识,'exports':导出,'styles':认领样式(标识),'edges':边}#拼记录
            自身.loadCache[标识]=记录#写入缓存
            return 记录#返回记录
        finally:#无论成败
            自身.正在物化.discard(标识)#清重入守卫

    def 造要求(自身,边):#造同步 require
        """答给工厂的同步 require。"""
        def 要求(说明符):#解析一个 spec
            """种子 → 静态 → 已物化 → 已登记工厂。"""
            边.add(说明符)#记下边
            if 说明符 in 自身.种子:#平台种子
                return 自身.种子[说明符]#种子
            if 说明符 in 自身.静态表:#壳自有
                return 自身.静态表[说明符]#静态
            标识=剥客户端后缀(说明符)#剥 /client
            记录=自身.loadCache.get(标识)#已物化
            if 记录 is not None:#命中缓存
                return 记录['exports']#导出
            if 标识 in 自身.工厂表:#现场物化
                return 自身.物化(标识)['exports']#物化导出
            raise Exception(#三种都不是
                'client-modules: require("'+说明符+'") missed the module table — not a platform seed word, not a shell-own module, '
                +'and no registered factory (a build-time externals drift, or a forbidden cross-plugin value import)',
            )#结束错误
        return 要求#同步 require

    def import_(自身,说明符,父网址=None,属性=None):#异步导入
        """按文档化分支顺序解析 specifier。"""
        if 说明符 in 自身.种子:#平台种子
            return 已兑现(自身.种子[说明符])#种子
        已有=自身.loadCache.get(说明符)#已物化
        if 已有 is not None:#命中缓存
            return 已兑现(已有['exports'])#导出
        if 说明符 in 自身.静态表:#壳自有
            导出=自身.静态表[说明符]#取出模块
            自身.loadCache[说明符]={'id':说明符,'exports':导出,'styles':[],'edges':set()}#写入缓存
            return 已兑现(导出)#返回
        if 说明符 not in 自身.工厂表:#工厂尚未到达
            行=自身.图行.get(说明符)#启动行
            if 行 is None:#图上没有
                raise Exception(#解析失败
                    'client-modules: cannot resolve "'+说明符+'" — not a seed word, not a shell-own module, '
                    +'and not a row in the boot graph (the runtime mirror of the bundle purity gate)',
                )#结束错误
            到达任务=自身.到达(行)#先拉包
            if _是否thenable(到达任务):#异步到达
                结果=操作任务()#物化链
                def 跑():#到达后物化
                    try:#等到达
                        _等待(到达任务)#等到达
                        结果.兑现(自身.物化(说明符)['exports'])#物化导出
                    except BaseException as 错误:#失败
                        结果.拒绝(错误)#上抛
                threading.Thread(target=跑,daemon=True).start()#后台链
                return 结果#链式
        return 已兑现(自身.物化(说明符)['exports'])#物化并返回

    def registerStatic(自身,标识,模块):#登记壳自有模块
        """登记一个外壳自有模块。"""
        if 标识 in 自身.静态表:#禁止重复
            raise Exception('client-modules: shell-own module "'+标识+'" registered twice')#重复
        自身.静态表[标识]=模块#写入静态表

    def prefetch(自身,标识):#预取一行
        """第一阶段到达：加载条目脚本以登记其工厂。"""
        if 标识 in 自身.静态表:#壳自有无需拉
            return 已兑现(None)#跳过
        行=自身.图行.get(标识)#启动行
        if 行 is None:#图上没有
            raise Exception('client-modules: prefetch("'+标识+'") — not a graph entry')#图上没有
        return 自身.到达(行)#拉包登记工厂

    def invalidate(自身,标识):#作废一模块
        """丢掉已登记工厂和已物化记录。"""
        自身.工厂表.pop(标识,None)#丢掉工厂
        自身.loadCache.pop(标识,None)#丢掉物化记录

客户端模块系统.import=客户端模块系统.import_#对齐上游方法名 import

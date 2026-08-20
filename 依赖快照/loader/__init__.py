"""拥有条目树并导入已配置插件的加载器服务。"""
import json,os,time
import cordis
import cosmokit
from .内部 import 模块加载器,模块阶段#内部加载器
from .配置.条目 import 条目#条目节点
from .配置.组 import 条目组,组#条目组与组插件
from .配置.隔离 import (
    隔离,#隔离钩子
    领域,#隔离域
    本地领域,#本地域
    全局领域,#全局域
)
from .配置.树 import 条目树#条目树
from .配置.工具 import 求值,插值,是否js表达式#表达式辅助

class 加载器(条目树):
    """拥有加载器条目树并导入已配置插件的服务。"""
    def __init__(自身,ctx,config=None):
        """登记 loader 服务并挂上配置插值、更新与自拆除钩子。"""
        if config is None:
            config={}#默认空配置
        条目树.__init__(自身,ctx)#创建根组
        自身.config=config#根配置
        if config.get('baseUrl'):
            自身.ctx.baseUrl=config.get('baseUrl')#解析基准
        共享=os.environ.get('CORDIS_SHARED')#CORDIS_SHARED
        if 共享:
            自身.envData=json.loads(共享)#共享环境
        else:
            自身.envData={'startTime':int(time.time()*1000)}#启动时刻
        自身.name='loader'#服务名
        自身.internal=模块加载器.从内部()#Node 内部加载器
        自身.builtins={}#cordis: 内建表
        cosmokit.定义属性(自身,cordis.服务.追踪器,{'associate':'loader','property':'ctx','noShadow':True})#追踪器
        自身._追踪器={'associate':'loader','property':'ctx','noShadow':True}#字段追踪器
        ctx.reflect.提供('loader',自身,自身._检查)#按光纤生命周期注册
        def 配置插值(_配置,下一步):
            """非组、非条目子插件的配置做 !!js 插值。"""
            配置=下一步()#先取内建配置
            光纤=自身.ctx.events.ctx.fiber#派发 this（插件光纤）
            条目对象=getattr(光纤,'entry',None)#光纤条目
            if not 条目对象 or getattr(光纤.parent.fiber,'entry',None) is 条目对象:
                return 配置#无条目或条目子插件保持字面量
            运行时=光纤.runtime#插件运行时
            回调=None#插件回调
            if 运行时:
                回调=运行时['callback'] if isinstance(运行时,dict) else getattr(运行时,'callback',None)#入口
            if 回调 is not None and getattr(回调,条目组.键,None):
                return 配置#组插件保持字面量
            return 插值(光纤.ctx,配置)#对照光纤上下文插值
        ctx.on('internal/config',配置插值,{'global':True})#全局配置钩子
        def 保存更新(配置,不保存,下一步):
            """把生效配置写回条目并持久化。"""
            光纤=自身.ctx.events.ctx.fiber#插件光纤
            条目对象=getattr(光纤,'entry',None)#光纤条目
            if not 条目对象 or 不保存 or getattr(光纤.parent.fiber,'entry',None) is 条目对象:
                return 下一步()#不写回
            下一步()#先应用
            运行时=光纤.runtime#插件运行时
            配置模式=None#schema
            if 运行时:
                配置模式=运行时['Config'] if isinstance(运行时,dict) else getattr(运行时,'Config',None)#Config
            反解析=None#simplify
            if 配置模式 is not None:
                if isinstance(配置模式,dict):
                    反解析=配置模式.get('simplify')#字典
                else:
                    反解析=getattr(配置模式,'simplify',None)#对象
            条目对象.options['config']=反解析(配置) if 反解析 else 配置#写回
            条目对象.parent.tree.写入()#持久化
        ctx.on('internal/update',保存更新,{'global':True,'prepend':True})#前置写回
        def 重载日志(配置,_,下一步):
            """条目重载时打日志。"""
            光纤=自身.ctx.events.ctx.fiber#插件光纤
            条目对象=getattr(光纤,'entry',None)#光纤条目
            if not 条目对象 or getattr(光纤.parent.fiber,'entry',None) is 条目对象:
                return 下一步()#不打
            自身.显示日志(条目对象,'reload')#reload 日志
            return 下一步()#继续链
        ctx.on('internal/update',重载日志,{'global':True})#重载日志
        def 插件钩子(光纤):
            """绑定 fiber.entry，并处理条目根光纤的自拆除。"""
            父条目=光纤.parent.__dict__.get(条目.键) if hasattr(光纤.parent,'__dict__') else None#父上下文上的条目
            if 父条目 and not getattr(光纤,'entry',None):
                光纤.entry=父条目#1. set fiber.entry
                cordis.注入.解析(光纤.entry.options.get('inject'),光纤.inject)#合并 inject
            if 光纤.uid:
                return#1. 光纤刚创建
            if not getattr(光纤,'entry',None):
                return#2. 不被加载器跟踪
            if getattr(光纤.parent.fiber,'entry',None) is 光纤.entry:
                return#3. 条目下的子插件光纤
            运行时=光纤.runtime#插件运行时
            回调=运行时['callback'] if isinstance(运行时,dict) else 运行时.callback#身份回调
            if not ctx.registry.has(回调):
                return#4. 插件删除导致的拆除
            树拥有者=光纤.entry.parent.tree.ctx.fiber#树拥有方光纤
            if not 树拥有者.uid or 树拥有者.state==cordis.光纤状态.卸载中:
                return#5. 整棵树正在拆除
            if 光纤.entry._拆除中:
                return#6. 加载器正在替换或移除该光纤
            自身.显示日志(光纤.entry,'unload')#unload 日志
            if 光纤.entry.disabled:
                return#7. 加载器行为导致的拆除
            光纤.entry.options['disabled']=True#记为禁用
            光纤.entry.parent.tree.写入()#持久化
        ctx.on('internal/plugin',插件钩子)#自拆除
        ctx.plugin(隔离)#安装隔离钩子

    def 写入(自身):
        """根树在内存中，写入为空操作。"""
        return#no-op

    def _检查(自身):
        """await 拦截开启且仍有任务时保持依赖方挂起。"""
        配置=cordis.服务._解析配置(自身)#合并拦截配置
        if 配置.get('await') and 自身.取任务():
            return False#仍在加载
        return True#可用

    def 显示日志(自身,条目对象,类型):
        """组条目或未开启日志时不输出。"""
        if 条目对象.options.get('group') or not 条目对象.parent.tree.enableLogs:
            return#跳过
        日志=getattr(自身.ctx.root,'logger',None)#根日志服务
        if 日志:
            日志('loader').info('%s plugin %C',类型,条目对象.options.get('name'))#插件日志

    def 定位(自身,光纤=None):
        """返回拥有该光纤的加载器条目编号。"""
        if 光纤 is None:
            光纤=自身.ctx.fiber#默认当前光纤
        while True:
            条目对象=getattr(光纤,'entry',None)#光纤条目
            if 条目对象:
                return 条目对象.id#命中
            下一个=光纤.parent.fiber#父光纤
            if 光纤 is 下一个:
                return None#根光纤
            光纤=下一个#继续上溯

    def 退出(自身):
        """完整重载时由宿主重启进程的钩子。"""
        return#空实现

    def 解开导出(自身,导出):
        """在应用插件前摊平 ESM/CJS/default 导出。"""
        if cosmokit.是否可空(导出):
            return 导出#空值
        def 取字段(对象,键):
            """读取 default / __esModule。"""
            if isinstance(对象,dict):
                return 对象[键] if 键 in 对象 else None#映射
            return getattr(对象,键,None)#对象
        默认=取字段(导出,'default')#default ??
        if 默认 is not None:
            导出=默认#换到 default
        if not 取字段(导出,'__esModule'):
            return 导出#非 esModule
        默认=取字段(导出,'default')#再取一层
        return 默认 if 默认 is not None else 导出#default ?? exports

Loader=加载器#英文别名
加载器.write=加载器.写入#英文别名
加载器.showLog=加载器.显示日志#英文别名
加载器.locate=加载器.定位#英文别名
加载器.exit=加载器.退出#英文别名
加载器.unwrapExports=加载器.解开导出#英文别名
加载器.check=加载器._检查#英文别名

Entry=条目#再导出
EntryGroup=条目组#再导出
Group=组#再导出
EntryTree=条目树#再导出
Realm=领域#再导出
LocalRealm=本地领域#再导出
GlobalRealm=全局领域#再导出
isolate=隔离#再导出
evaluate=求值#再导出
interpolate=插值#再导出
isJsExpr=是否js表达式#再导出
ModuleLoader=模块加载器#再导出
ModulePhase=模块阶段#再导出

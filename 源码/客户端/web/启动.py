from threading import Thread as 线程#预取扇出
from .启动客户端 import 网页错误,启动客户端#组装与本包异常
from .启动页 import 启动页#启动页
from .挂载 import 挂载客户端#应用挂载
from .种子 import 静态模块表#静态模块表

__all__=['网页应用入口','上下文构造']#仅中文公开名

上下文构造=None#Cordis Context 类；启动前由宿主写入

def 全部并发(调用表):
    """扇出：每路一线程，join 后按原序抬错。"""
    if len(调用表)==0:#空
        return#无事
    错误表=[None]*len(调用表)#按原序错误
    def 跑一路(下标,调用):
        """执行一路并记下错误。"""
        try:#跑
            调用()#无参调用
        except BaseException as 错误:#失败
            错误表[下标]=错误#记下
    线程表=[]#工作线程
    for 下标,调用 in enumerate(调用表):#每路一线程
        工作=线程(target=跑一路,args=(下标,调用),daemon=True)#工作线程
        工作.start()#启动
        线程表.append(工作)#登记
    for 工作 in 线程表:#扇出 join
        工作.join()#等到结束
    for 错误 in 错误表:#按原序检查
        if 错误 is not None:#有失败
            raise 错误#原样抛

class 网页应用入口:#apps/web 消费的浏览器启动入口
    """绘制启动页；run 启动加载器。"""
    def __init__(自身,容器,接缝=None,窗口=None):
        """记下挂载点与可选传输替换。窗口为带 DSH 门面的 dict。"""
        自身.容器=容器#应用挂载点
        自身.接缝=接缝#可选 seams
        自身.窗口=窗口#DshWindow
        自身.页=启动页(容器)#启动页
        自身.上下文=None#客户端插件树上下文
        自身.模块系统=None#模块系统
        自身.清单=None#启动清单

    def run(自身,失败回调=None):
        """加载并激活每个客户端入口，再把挂载点交给 UI 渲染器。失败回调可选。"""
        try:#跑启动
            窗口=自身.窗口#门面
            if 窗口 is None:#缺窗口
                raise 网页错误('网页启动：缺少 window.__ModuleLoader__ 引导门面')#失败
            if '__DSH_BOOT_READY__' in 窗口:#有就绪门
                窗口['__DSH_BOOT_READY__'].等待()#等引导就绪；生产者不在本范围
            if '__ModuleLoader__' not in 窗口:#缺门面
                raise 网页错误('网页启动：缺少 window.__ModuleLoader__ 引导门面')#失败
            模块加载器=窗口['__ModuleLoader__']#模块加载器门面
            创建选项={'boot':窗口['__DSH_BOOT__'] if '__DSH_BOOT__' in 窗口 else None,'staticModules':静态模块表()}#基础选项
            if '__DSH_TRANSPORT__' in 窗口:#预注入传输
                传输=窗口['__DSH_TRANSPORT__']#钩子
                if 'loadBundle' in 传输:#有 loadBundle
                    创建选项['loadBundle']=传输['loadBundle']#默认传输
            if 自身.接缝 is not None and 'loadBundle' in 自身.接缝:#测试 seams 覆盖
                创建选项['loadBundle']=自身.接缝['loadBundle']#覆盖
            自身.模块系统=模块加载器.create(创建选项)#创建模块系统
            自身.清单=自身.模块系统.manifest#记下清单
            自身.预取立即层()#预取立即层
            if 上下文构造 is None:#未绑定 Context
                raise 网页错误('网页启动：未绑定 Context 类')#失败
            上下文=上下文构造()#新 Cordis 树
            自身.上下文=上下文#记下
            自身.页.setTotal(len(自身.清单['plugins']))#设进度总数
            def 投影状态(名,状态):
                """投影到启动页；载体呈现失败时跳过 failed。"""
                if 失败回调 is None or 状态!='failed':#可写页
                    自身.页.setState(名,状态)#写下
            启动客户端({#组装插件树
                'ctx':上下文,#根上下文
                'modules':自身.模块系统,#模块系统
                'manifest':自身.清单,#清单
                'onEntryState':投影状态,#投影
            })#启动客户端结束
            挂载客户端(上下文,自身.容器)#挂应用
        except Exception as 原因:#启动失败
            if 失败回调 is not None:#载体呈现
                失败回调(原因)#回调
            elif isinstance(原因,网页错误):#本包错误
                自身.页.fail(原因.args[0] if len(原因.args)>0 else str(原因))#启动页失败报告
            else:#其它
                自身.页.fail(str(原因))#启动页失败报告

    def dispose(自身):
        """拆除客户端插件树以及当前拥有挂载点的页面。"""
        上下文=自身.上下文#当前
        自身.上下文=None#清空引用
        if 上下文 is not None:#有树
            上下文.fiber.dispose().等待()#拆除插件树并等落定；cordis 纤程须显式等待
        自身.页.dispose()#拆除启动页

    def 预取立即层(自身):
        """在并发插件导入前预取一阶段包及其动态请求。预取失败不阻断启动。"""
        调用表=[]#预取调用
        for 行 in 自身.清单['plugins']:#逐行
            if 行['immediately'] is not True:#非立即
                continue#下
            def 造预取(标识):
                """预取一个包。"""
                def 预取一条():
                    """只提前开传输；失败由 Loader 导入再报。"""
                    try:#预取
                        自身.模块系统.prefetch(标识)#预取；模块系统内同步阻塞
                    except 网页错误:#仅吞本包预取失败
                        return#忽略
                return 预取一条#调用
            调用表.append(造预取(行['id']))#收下
        全部并发(调用表)#并发预取

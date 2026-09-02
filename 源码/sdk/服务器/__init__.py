"""面向 SDK 的标准输入输出 JSON-RPC 插件。

对齐上游 `@deepseek-ai/dsh-sdk-jsonrpc-server`。公开面仅中文名。是否加载由外部 cordis.yml 决定；标准输出留给协议帧。保持具名插件导出且无默认导出，以便 Loader 保留 name、inject、Config 和 apply。
"""
import sys,threading#生产 stdio、退出与异步退出拍
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 布尔字段#配置字段
from ..协议 import 换行JSONRPC传输#换行 JSON-RPC 传输
from .服务端 import 装备SDKJSONRPC服务端#SDK 运行时服务器

__all__=['名称','注入','配置','应用','装备SDKJSONRPC服务端']#仅中文公开名

名称='sdk-jsonrpc-server'#Cordis插件名（字面量）
注入=['agents']#只需智能体工厂；initialize 用 ctx.get() 读取可选 LLM seam

配置={#可校验的插件配置模式
    'maxTokensAsSuccess':布尔字段(默认值=False),#默认不把 max-tokens 当成功
}#Config 模式结束

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 应用(上下文,配置值):#安装 JSON-RPC 服务插件
    """在已配置流上服务 SDK 请求。effect 拆除会关闭 SDK 创建的智能体并关闭传输。"""
    解析配置=配置值#Cordis 在调用插件前已套用模式默认值
    根光纤=上下文.root.fiber#抓住根 fiber 以便 shutdown 后拆除
    输入=取字段(配置值,'input')#可选测试输入
    if 输入 is None:#生产用标准输入
        输入=sys.stdin#stdin
    输出=取字段(配置值,'output')#可选测试输出
    if 输出 is None:#生产用标准输出
        输出=sys.stdout#stdout
    退出函数=取字段(配置值,'exit')#可选测试退出
    if 退出函数 is None:#生产用进程退出
        def 退出函数(码):#生产退出
            """以给定码退出进程。"""
            sys.exit(码)#退出
    传输=换行JSONRPC传输(输入,输出)#在选定流上建传输
    服务端=装备SDKJSONRPC服务端(上下文,传输,{#建 SDK 服务器
        'maxTokensAsSuccess':取字段(解析配置,'maxTokensAsSuccess'),#部署级状态映射
    })#服务器选项结束
    退出任务=None#进行中的退出任务，避免重入
    def 拆除并退出():#刷传输、拆根、以 0 退出
        """共用一个退出任务。"""
        nonlocal 退出任务#改外层
        if 退出任务 is not None:#已在退出
            return 解开(退出任务)#复用
        def 跑退出():#实际退出序列
            """先刷出 shutdown 响应，再拆除根运行时，最后以 0 退出。"""
            try:#刷出
                解开(传输.刷出())#先刷出 shutdown 响应
            except BaseException:#刷失败不阻断
                pass#继续拆除
            try:#拆根
                解开(根光纤.dispose())#再拆除根运行时
            except BaseException:#拆失败不阻断退出
                pass#仍退出
            退出函数(0)#以 0 退出进程
        退出任务=已兑现(True)#占位标记已启动
        跑退出()#跑退出会 exit，通常不返回
        return None#占位
    def 请求处理(方法,参数):#安装请求处理器
        """分发到类型化处理函数；shutdown 之后安排进程退出。"""
        结果=解开(服务端.处理请求(方法,参数))#分发
        if 方法=='shutdown':#shutdown 之后安排进程退出
            threading.Thread(target=拆除并退出,daemon=True).start()#异步退出以免卡住响应写出
        return 结果#返回给传输写成响应
    传输.当请求(请求处理)#挂上请求处理
    def 服务生命周期():#注册传输生命周期 effect
        """开始读帧；拆除时关服务端与传输。"""
        传输.启动()#开始读帧
        def 拆除():#effect 拆除
            """关闭 SDK 拥有的智能体与订阅，再关传输。"""
            解开(服务端.关闭())#关闭 SDK 拥有的智能体与订阅
            传输.关闭()#摘监听并拒绝挂起请求
        return 拆除#拆除函数
    上下文.effect(服务生命周期,'jsonrpc.serve')#effect 名

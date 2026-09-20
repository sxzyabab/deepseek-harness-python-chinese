import builtins,threading#页面全局与启动回合锁
from ....依赖 import cordis#外部依赖胶水
from ....客户端.模块.条目生命周期 import 拆除条目纤程#条目纤程拆除
from ....客户端.连接.客户端 import 安装连接#连接安装
from ....客户端.web.启动客户端 import 启动客户端#生产客户端启动
from ....客户端.web.挂载 import 挂载客户端#生产客户端挂载
from .名册 import 断言计划,名册转启动图,组装计划,客户端测试运行时错误#计划校验与启动图
from .进程内模块 import 装入插件模块,创建进程内模块#进程内模块
from .远程代理 import 远程接口包名,收集远程命名空间,远程代理插件#远程代理

__all__=['测试客户端']#仅中文公开名

上下文类=cordis.上下文#Cordis 上下文
连接包名='@deepseek-ai/dsh-client-connection'#连接包名
默认连接超时毫秒=5000#默认连接超时毫秒

class 事件源桩:#事件源桩
    """jsdom 缺少的 EventSource 惰性替身。"""

    def addEventListener(自身,*位置参数):#空监听
        """空监听。"""
        return#无操作

    def close(自身):#空关闭
        """空关闭。"""
        return#无操作

class 尺寸观察桩:#尺寸观察桩
    """jsdom 缺少的 ResizeObserver 惰性替身。"""

    def observe(自身,*位置参数):#空观察
        """空观察。"""
        return#无操作

    def disconnect(自身):#空断开
        """空断开。"""
        return#无操作

文档对象模型补桩={'EventSource':事件源桩,'ResizeObserver':尺寸观察桩}#jsdom 垫片

class 共享文档对象模型垫片:#共享 jsdom 垫片
    """本进程每个活客户端共享的垫片；首持有者安装，末释放者拆除。"""

    def __init__(自身):#构造
        """空持有。"""
        自身._持有=0#持有计数
        自身._拆垫片=None#垫片拆除

    def 获取(自身):#获取持有
        """持有垫片，返回本持有者的释放器。"""
        if 自身._持有==0:#第一个持有者
            自身._拆垫片=安装文档对象模型垫片()#装垫片
        自身._持有+=1#计数
        def 释放():#释放
            """最后一个持有者拆垫片。"""
            自身._持有-=1#减计数
            if 自身._持有>0:#仍有持有者
                return
            if 自身._拆垫片 is not None:#有垫片
                自身._拆垫片()#拆垫片
                自身._拆垫片=None#清空
        return 释放#释放器

共享垫片单例=共享文档对象模型垫片()#进程内共享垫片

def 安装文档对象模型垫片():#安装 jsdom 垫片
    """为每个缺席全局安装垫片；拆除器只删除那些装上的。"""
    已装=[名 for 名 in 文档对象模型补桩 if getattr(builtins,名,None) is None]#缺席者
    for 名 in 已装:#安装
        setattr(builtins,名,文档对象模型补桩[名])#安装
    def 拆除():#只拆装上的
        """删除本次装上的全局。"""
        for 名 in 已装:#逐个
            if hasattr(builtins,名):#仍在
                delattr(builtins,名)#删除
    return 拆除#拆除器

def 收成错误(错误):#收成 Error
    """抛出值所代表的异常：自身，或其字符串形式包一层。"""
    if isinstance(错误,Exception):#已是
        return 错误#原样
    return 客户端测试运行时错误(str(错误))#包一层

def 取消息(错误):#取消息
    """异常消息。"""
    return str(收成错误(错误))#消息

def 取连接(上下文):#取连接
    """名册的 Connection 服务；未提供则抛。"""
    连接=上下文.获取服务('connection')#取服务
    if 连接 is None:#无连接
        raise 客户端测试运行时错误('client-test-runtime: the roster provides no `connection` service')#英文诊断
    return 连接#返回

def 解析挂载点(挂载):#解析挂载点
    """解析挂载选项。"""
    if 挂载 is None or 挂载 is False:#不挂载
        return {'element':None,'owned':False}#空
    文档=getattr(builtins,'document',None)#页面文档
    if 文档 is None:#无 DOM
        raise 客户端测试运行时错误('client-test-runtime: mount requires a DOM; add `// @vitest-environment jsdom` to the spec')#英文诊断
    if 挂载 is True:#自建节点
        元素=文档.createElement('div')#新建
        文档.body.appendChild(元素)#挂到 body
        return {'element':元素,'owned':True}#自有
    return {'element':挂载,'owned':False}#调用方节点

def 安定(函数):#安定
    """有 DOM 时本应包 React act；Python 无 act，直接跑。"""
    函数()#直接跑

def 等到已连接(上下文,模拟,超时毫秒):#等到已连接
    """等待 connection.state 为 connected。"""
    状态=取连接(上下文).state#连接状态
    if 状态.getSnapshot()=='connected':#已连接
        return
    完成=threading.Event()#完成事件
    def 订阅回调():#订阅
        """已连接则放行。"""
        if 状态.getSnapshot()!='connected':#未到
            return
        完成.set()#放行
    退订=状态.subscribe(订阅回调)#订阅
    if not 完成.wait(超时毫秒/1000):#超时
        退订()#退订
        漏配=[str(行.模式)+' '+str(行.端点) for 行 in 模拟.日志.漏配列表()]#漏配
        流列表=[str(行.端点)+' ('+str(行.状态)+')' for 行 in 模拟.日志.流列表()]#流列表
        raise 客户端测试运行时错误('client-test-runtime: connection state is '+str(状态.getSnapshot())+' after '+str(超时毫秒)+'ms; unmatched: ['+', '.join(漏配)+']; streams: ['+', '.join(流列表)+']')#英文诊断
    退订()#退订

class 测试客户端:#测试客户端
    """测试下已启动的客户端。"""

    @staticmethod
    def 启动(计划,模拟,选项=None):#启动
        """装入名册模块，绑定本客户端模拟到 Connection 行，持有垫片并走生产启动。"""
        if 选项 is None:#缺省
            选项={}#空
        断言计划(计划)#校验计划
        提供表=计划.提供#行替换
        if 提供表 is not None and 远程接口包名 in 提供表:#禁止提供远程包
            raise 客户端测试运行时错误('client-test-runtime: '+远程接口包名+' cannot be provided; its remote.<ns> services are the tier\'s proxies')#英文诊断
        名册含远程=any(行.包名==远程接口包名 for 行 in 计划.名册.行表)#名册是否含远程包
        名册=计划.名册.去掉([远程接口包名]) if 名册含远程 else 计划.名册#丢掉远程包
        上下文=上下文类()#新建上下文
        页面定位=None#页面主机名
        定位=getattr(builtins,'location',None)#页面 location
        if 定位 is not None:#有 location
            页面定位={'hostname':定位.hostname}#主机名
        挂载点={'element':None,'owned':False}#挂载点
        释放=None#垫片释放
        def 还原():#还原
            """移除自有节点并释放垫片。"""
            if 挂载点['owned'] and 挂载点['element'] is not None:#自有
                挂载点['element'].remove()#移除
            if 释放 is not None:#有释放器
                释放()#释放垫片
        try:#启动
            裁剪计划=组装计划(名册,计划.提供)#名册已裁远程包
            模块表=dict(装入插件模块(裁剪计划))#装入模块
            连接模块=模块表.get(连接包名)#连接行
            if 连接模块 is not None and (提供表 is None or 连接包名 not in 提供表):#替换连接 apply
                def 应用连接(连接上下文):#安装模拟载体
                    """经 installConnection 挂上本客户端模拟。"""
                    选项表={'transport':{'rpc':模拟.rpc}}#传输
                    if 页面定位 is not None:#有主机名
                        选项表['location']=页面定位#带上
                    安装连接(连接上下文,选项表)#安装
                替换=dict(连接模块) if isinstance(连接模块,dict) else {
                    'inject':getattr(连接模块,'inject',None),
                    'apply':应用连接,
                    'name':getattr(连接模块,'name',None),
                    'Config':getattr(连接模块,'Config',None),
                    'default':getattr(连接模块,'default',None),
                }
                if isinstance(连接模块,dict):#字典形
                    替换['apply']=应用连接#覆盖
                else:#对象形改成字典
                    替换['apply']=应用连接#覆盖
                模块表[连接包名]=替换#写回
            挂载点=解析挂载点(选项['挂载'] if '挂载' in 选项 else None)#解析挂载点
            释放=共享垫片单例.获取()#持有垫片
            系统=创建进程内模块(名册转启动图(名册.行表),模块表)#进程内模块系统
            上下文.启动插件(远程代理插件(收集远程命名空间(模块表.values(),模拟),模拟))#先挂远程代理
            启动客户端({'ctx':上下文,'modules':系统,'manifest':系统.manifest})#生产启动
            if 挂载点['element'] is not None:#需要挂载
                if 上下文.获取服务('uiRenderer') is None:#无名册渲染器
                    raise 客户端测试运行时错误('client-test-runtime: mount requested, but the roster provides no `uiRenderer`')#英文诊断
                挂载客户端(上下文,挂载点['element'])#挂载
            if ('是否等待已连接' not in 选项) or 选项['是否等待已连接'] is not False:#等待已连接
                超时=选项['连接超时毫秒'] if '连接超时毫秒' in 选项 and 选项['连接超时毫秒'] is not None else 默认连接超时毫秒#超时
                等到已连接(上下文,模拟,超时)#等到连接
        except Exception:#失败
            try:#尽力拆除
                def 拆树():#拆树
                    """安定内拆除根纤程。"""
                    上下文.纤程.拆除()#拆树
                安定(拆树)#安定
            except Exception:#拆除失败
                pass#启动失败才是要报告的
            还原()#还原垫片与挂载
            raise#重抛原错误
        return 测试客户端(上下文,模拟,挂载点['element'],还原)#返回

    def __init__(自身,上下文,模拟,容器,还原):#私有构造经 启动
        """记下上下文、模拟、容器与还原器。"""
        自身.ctx=上下文#根上下文
        自身.模拟=模拟#模拟
        自身.容器=容器#容器
        自身._还原=还原#还原
        自身._拆除中=None#进行中的拆除
        自身._拆除锁=threading.Lock()#拆除锁

    @property
    def 连接(自身):#连接
        """名册的 Connection 服务；未提供则抛。"""
        return 取连接(自身.ctx)#取连接

    def 冲刷(自身):#冲刷
        """冲刷挂起工作。"""
        def 空趟():#空安定趟
            """空安定趟。"""
            return#无操作
        安定(空趟)#空安定趟

    def 重载(自身,名称):#重载
        """重建一个 Loader 条目。"""
        条目=自身._按名取条目(名称)#按名取条目
        拆除条目纤程(条目)#拆旧纤程
        条目.刷新()#刷新
        自身.ctx.loader.等待()#等加载器静止

    def 卸下行(自身,名称):#卸下行
        """移除一个 Loader 条目并等待其插件清理。"""
        条目=自身._按名取条目(名称)#按名取条目
        纤程=getattr(条目,'fiber',None)#条目纤程
        拆除=纤程.拆除 if 纤程 is not None and hasattr(纤程,'拆除') else None#拆除器
        自身.ctx.loader.移除(条目.编号)#按编号移除
        if 拆除 is not None:#有拆除
            拆除()#等待清理

    def 拆除(自身):#拆除
        """拆除插件树，还原垫片，最后检查漏配；并发调用等待同一次拆除。"""
        with 自身._拆除锁:#串行领取
            if 自身._拆除中 is not None:#已有拆除
                进行中=自身._拆除中#同一次
            else:#首次
                完成=threading.Event()#完成事件
                自身._拆除中=完成#登记
                进行中=None#本线程执行
        if 进行中 is not None:#等待他人
            进行中.wait()#等到完成
            return
        try:#执行拆除
            自身._拆除实现()#拆除
        finally:#放行等待者
            完成.set()#完成

    def _拆除实现(自身):#拆除实现
        """拆树、还原、检查漏配。"""
        失败=None#树拆除失败
        try:#拆树
            def 拆树():#拆树
                """安定内拆除根纤程。"""
                自身.ctx.纤程.拆除()#拆除
            安定(拆树)#安定
        except Exception as 错误:#拆树失败
            失败=收成错误(错误)#收成
        自身._还原()#还原垫片与挂载
        if 失败 is None:#树拆成功
            自身.模拟.断言无漏配()#检查漏配
            return
        try:#仍检查漏配
            自身.模拟.断言无漏配()#检查
        except Exception as 漏配:#漏配也失败
            树消息=失败.args[0] if len(失败.args)>0 else str(失败)#树失败消息
            raise 客户端测试运行时错误(取消息(漏配)+'\nclient-test-runtime: the plugin tree also failed to dispose: '+str(树消息),失败)#两条消息
        raise 失败#只报树失败

    def _按名取条目(自身,名称):#按名取条目
        """按包名找 Loader 条目。"""
        条目列表=list(自身.ctx.loader.列出插件配置())#全部条目
        条目=None#命中
        for 候选 in 条目列表:#逐个
            选项=候选.选项#配置文件选项
            if 'name' in 选项 and 选项['name']==名称:#名字匹配
                条目=候选#命中
                break#找到
        if 条目 is None:#未找到
            已有=', '.join(候选.选项['name'] if 'name' in 候选.选项 else '' for 候选 in 条目列表)#已有名
            raise 客户端测试运行时错误('client-test-runtime: no Loader entry named '+名称+'; entries: '+已有)#英文诊断
        return 条目#返回

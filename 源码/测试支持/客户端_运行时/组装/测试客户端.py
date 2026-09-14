import builtins,threading#页面全局与启动回合锁
from ....依赖 import cordis#外部依赖胶水
from ....客户端.热更新.客户端 import 拆除条目光纤#条目光纤拆除
from ....客户端.web.启动客户端 import 启动客户端#生产客户端启动
from ....客户端.web.挂载 import 挂载客户端#生产客户端挂载
from .名册 import 断言计划,名册转启动图,组装计划,客户端测试运行时错误#计划校验与启动图
from .进程内模块 import 装入插件模块,创建进程内模块#进程内模块
from .远程代理 import 远程接口包名,收集远程命名空间,远程代理插件#远程代理

__all__=['测试客户端']#仅中文公开名

上下文类=cordis.上下文#Cordis 上下文
启动回合锁=threading.Lock()#启动回合锁
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

class 共享全局:#共享全局
    """本进程每个活客户端共享的传输全局与垫片。"""

    def __init__(自身):#构造
        """空持有。"""
        自身._持有=0#持有计数
        自身._原先传输=None#原先传输
        自身._拆垫片=None#垫片拆除

    def 安装(自身,传输):#安装传输
        """把传输全局指到即将运行的启动或重建所用的传输。"""
        builtins.__DSH_TRANSPORT__=传输#写入全局

    def 获取(自身,传输):#获取持有
        """持有全局并装上传输，返回本持有者的释放器。"""
        if 自身._持有==0:#第一个持有者
            自身._原先传输=getattr(builtins,'__DSH_TRANSPORT__',None)#记住原先
            自身._拆垫片=安装文档对象模型垫片()#装垫片
        自身._持有+=1#计数
        自身.安装(传输)#装传输
        def 释放():#释放
            """最后一个持有者拆垫片并恢复传输。"""
            自身._持有-=1#减计数
            if 自身._持有>0:#仍有持有者
                return#结束
            if 自身._拆垫片 is not None:#有垫片
                自身._拆垫片()#拆垫片
                自身._拆垫片=None#清空
            if 自身._原先传输 is None:#无原先
                if hasattr(builtins,'__DSH_TRANSPORT__'):#有键
                    delattr(builtins,'__DSH_TRANSPORT__')#删键
            else:#有原先
                builtins.__DSH_TRANSPORT__=自身._原先传输#恢复
            自身._原先传输=None#清空
        return 释放#释放器

共享全局单例=共享全局()#进程内共享全局

def 领取回合(工作):#领取回合
    """把工作作为下一启动回合跑；失败不传给下一回合。"""
    with 启动回合锁:#串行
        工作()#跑

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
        return#结束
    完成=threading.Event()#完成事件
    def 订阅回调():#订阅
        """已连接则放行。"""
        if 状态.getSnapshot()!='connected':#未到
            return#结束
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
        """装入名册模块，占着启动回合走生产启动，可选挂载并等待连接。"""
        if 选项 is None:#缺省
            选项={}#空
        断言计划(计划)#校验计划
        提供表=计划.提供#行替换
        if 提供表 is not None and 远程接口包名 in 提供表:#禁止提供远程包
            raise 客户端测试运行时错误('client-test-runtime: '+远程接口包名+' cannot be provided; its remote.<ns> services are the tier\'s proxies')#英文诊断
        名册含远程=any(行.包名==远程接口包名 for 行 in 计划.名册.行表)#名册是否含远程包
        名册=计划.名册.去掉([远程接口包名]) if 名册含远程 else 计划.名册#丢掉远程包
        上下文=上下文类()#新建上下文
        传输={'rpc':模拟.rpc}#传输钩子
        挂载点={'element':None,'owned':False}#挂载点
        释放=None#全局释放
        def 还原():#还原
            """移除自有节点并释放全局。"""
            if 挂载点['owned'] and 挂载点['element'] is not None:#自有
                挂载点['element'].remove()#移除
            if 释放 is not None:#有释放器
                释放()#释放全局
        try:#启动
            裁剪计划=组装计划(名册,计划.提供)#名册已裁远程包
            模块表=装入插件模块(裁剪计划)#装入模块
            挂载点=解析挂载点(选项['挂载'] if '挂载' in 选项 else None)#解析挂载点
            def 启动回合():#启动回合
                """持有全局、建造进程内模块并启动。"""
                nonlocal 释放#写入外层
                释放=共享全局单例.获取(传输)#持有全局
                系统=创建进程内模块(名册转启动图(名册.行表),模块表)#进程内模块系统
                上下文.启动插件(远程代理插件(收集远程命名空间(模块表.values(),模拟),模拟))#先挂远程代理
                启动客户端({'ctx':上下文,'modules':系统,'manifest':系统.manifest})#生产启动
            领取回合(启动回合)#启动回合
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
            还原()#还原全局与挂载
            raise#重抛原错误
        return 测试客户端(上下文,模拟,挂载点['element'],还原)#返回

    def __init__(自身,上下文,模拟,容器,还原):#私有构造经 启动
        """记下上下文、模拟、容器与还原器。"""
        自身.ctx=上下文#根上下文
        自身.模拟=模拟#模拟
        自身.容器=容器#容器
        自身._还原=还原#还原
        自身._已拆过=False#是否已拆
        自身._拆除锁=threading.Lock()#拆除锁

    def _传输(自身):#传输
        """本客户端的 connection 行 apply 时读取的载体。"""
        return {'rpc':自身.模拟.rpc}#rpc 面

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
        def 重建回合():#启动回合
            """装本客户端传输、拆旧光纤并刷新。"""
            共享全局单例.安装(自身._传输())#装本客户端传输
            拆除条目光纤(条目)#拆旧光纤
            条目.刷新()#刷新
            自身.ctx.loader.等待()#等加载器静止
        领取回合(重建回合)#启动回合

    def 卸下行(自身,名称):#卸下行
        """移除一个 Loader 条目。"""
        自身.ctx.loader.移除(自身._按名取条目(名称).编号)#按编号移除

    def 拆除(自身):#拆除
        """拆除插件树，还原全局，最后检查漏配。"""
        with 自身._拆除锁:#串行
            if 自身._已拆过:#已拆
                return#结束
            自身._已拆过=True#标记
            自身._拆除实现()#拆除

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
        自身._还原()#还原全局与挂载
        if 失败 is None:#树拆成功
            自身.模拟.断言无漏配()#检查漏配
            return#结束
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

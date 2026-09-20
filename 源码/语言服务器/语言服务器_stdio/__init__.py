import threading#提供方队列与生命周期
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,列表字段,字典字段,任意字段,数字字段
聚合错误=cordis.聚合错误#聚合错误
from ...语言服务器.语言服务器 import 语言服务器错误,语言服务器提供方标识#LSP错误与提供方id工厂
from ...工具.超时 import 定时器延迟上限毫秒,中止控制器,合成信号,已中止#定时器上限与取消
from .取消 import 可中止等待,中止错误,操作任务#取消与操作任务
from .宿主 import 规范化工作区,读宿主源#宿主I/O
from .实例 import 语言服务器实例#语言服务器实例

包名='@deepseek-ai/dsh-lsp-stdio'
名称='lsp-stdio'
依赖=['fs','lsp','subprocess']

__all__=[
    '包名','名称','依赖','应用','默认','配置模式','本地语言服务器提供方',
]

默认最大消息字节=16000000#默认单条成帧消息上限（字节）
默认最大标准误字节=1000000#默认stderr尾上限（字节）
默认最大文档字节=4000000#默认源文件上限（字节）
默认关闭超时毫秒=5000#默认优雅关闭预算（毫秒）
默认杀进程宽限毫秒=2000#默认SIGTERM到SIGKILL宽限（毫秒）

本地服务器配置模式={#单条服务器配置模式
    'command':字符串字段(可空=False),#可执行文件必填
    'args':列表字段(字符串字段(),默认值=[]),#参数默认空数组
    'env':字典字段(键值结构=(字符串字段(),字符串字段()),默认值={}),#环境默认空对象
    'extensionToLanguage':字典字段(键值结构=(字符串字段(),字符串字段()),可空=False),#扩展映射必填
    'initializationOptions':任意字段(默认值=None),#初始化选项默认null
    'configuration':任意字段(默认值=None),#配置回答默认null
    'maxMessageBytes':数字字段(默认值=默认最大消息字节),#消息上限默认值
    'maxStderrBytes':数字字段(默认值=默认最大标准误字节),#stderr尾默认值
    'maxDocumentBytes':数字字段(默认值=默认最大文档字节),#源文件上限默认值
    'shutdownTimeoutMs':数字字段(最大=定时器延迟上限毫秒,默认值=默认关闭超时毫秒),#关闭预算默认值
    'killGraceMs':数字字段(最大=定时器延迟上限毫秒,默认值=默认杀进程宽限毫秒),#杀进程宽限默认值
}#结束本地服务器配置模式

配置模式={#插件配置模式
    'servers':字典字段(字典结构=本地服务器配置模式,可空=False),#服务器表必填
}#结束 Config schema

本地服务器配置字段=('command','extensionToLanguage','args','env','initializationOptions','configuration','maxMessageBytes','maxStderrBytes','maxDocumentBytes','shutdownTimeoutMs','killGraceMs')#一项已配置的本地语言服务器及其宿主上限
插件配置字段=('servers',)#插件配置：提供方 id → 本地语言服务器配置

def 抛出拆除失败(失败列表,消息):#拆除失败延后抛出
    """等每一项兄弟都结算之后，才把拆除失败抛出去。失败列表是异常列表。"""
    if len(失败列表)==1:#单次失败原样抛出
        raise 失败列表[0]#原样
    if len(失败列表)>1:#多次失败聚合成聚合错误
        raise 聚合错误(失败列表,消息)#AggregateError

def 全部结算(任务列表):#对齐Promise.allSettled
    """等全部落定，收集 fulfilled/rejected。任务是操作任务或已有同步值。"""
    结果列表=[]#结算表
    for 任务 in 任务列表:#逐路
        try:#等待
            if isinstance(任务,操作任务):#任务
                任务.等待()#等待
            结果列表.append({'status':'fulfilled','value':None})#成功
        except BaseException as 错误:
            结果列表.append({'status':'rejected','reason':错误})#拒绝
    return 结果列表#全部结算

def 断言定时器(提供方标识,名称,值):#校验定时器预算
    """拒绝会被 Node 钳位、而不是按配置调度的定时器值。排除布尔。"""
    if isinstance(值,bool) or isinstance(值,int) is False or 值<1 or 值>定时器延迟上限毫秒:#超出可调度范围
        raise 语言服务器错误('lsp-stdio: servers.'+str(提供方标识)+'.'+名称+' 必须是不超过 '+str(定时器延迟上限毫秒)+' 的正整数','LSP_INVALID_PROVIDER')#加载时失败

def 断言正整数(提供方标识,名称,值):#校验正整数配置
    """加载时拒绝非正或非整数配置值，让错误配置大声失败。排除布尔。"""
    if isinstance(值,bool) or isinstance(值,int) is False or 值<1:#非正整数
        raise 语言服务器错误('lsp-stdio: servers.'+str(提供方标识)+'.'+名称+' 必须是正整数','LSP_INVALID_PROVIDER')#加载时失败

def 校验服务器配置(提供方标识,已解析):#加载时校验一条服务器配置
    """在表中任何一个提供方注册之前，校验一条已解析的服务器配置。已解析是 dict。"""
    断言定时器(提供方标识,'shutdownTimeoutMs',已解析['shutdownTimeoutMs'])#校验优雅关闭预算
    断言定时器(提供方标识,'killGraceMs',已解析['killGraceMs'])#校验杀进程宽限
    断言正整数(提供方标识,'maxStderrBytes',已解析['maxStderrBytes'])#校验stderr尾上限
    断言正整数(提供方标识,'maxMessageBytes',已解析['maxMessageBytes'])#校验消息上限
    断言正整数(提供方标识,'maxDocumentBytes',已解析['maxDocumentBytes'])#校验源文件上限

class 本地语言服务器提供方:#按工作区池化的stdio提供方
    """池化的通用提供方：每个规范工作区一个服务器进程，按需创建。配置是 dict。"""
    def __init__(自身,提供方标识,文件系统,配置,可执行,拉起器):
        """记下身份、扩展映射、文件系统与拉起器。"""
        自身.id=语言服务器提供方标识(提供方标识)#打成品牌id
        自身.extensionToLanguage=配置['extensionToLanguage']#记下扩展映射
        自身.文件系统=文件系统#共享文件系统
        自身.配置=配置#已填默认的服务器配置
        自身.可执行=可执行#已解析绝对可执行路径
        自身.拉起器=拉起器#子进程拉起器
        自身.实例表={}#工作区到实例
        自身.队列表={}#工作区查询队列尾
        自身.工作区解析集=set()#飞行中的工作区解析
        自身.生命周期=中止控制器()#提供方生命周期取消
        自身.已拆除=False#是否已拆除
        自身.锁=threading.Lock()#表互斥

    def 是否已拆除(自身):
        """读取拆除标志。"""
        return 自身.已拆除#当前是否已拆除

    def 断言活动(自身,信号=None):#已拆除或已取消则拒绝
        """拒绝无法发布或使用提供方拥有实例的工作。"""
        if 自身.是否已拆除():#拆除后拒绝
            raise 语言服务器错误('lsp-stdio 提供方已拆除','LSP_DISPOSED')#LSP_DISPOSED
        if 信号 is not None and 已中止(信号):#已取消
            raise 中止错误(信号)#抛分类中止错误

    def 查询信号(自身,信号=None):#融合调用方取消与提供方拆除
        """为每一次文件系统与协议等待，把调用方取消与提供方拆除融合在一起。"""
        if 信号 is None:#无调用方信号则只用生命周期
            return 自身.生命周期.信号#提供方拆除信号
        return 合成信号(信号,自身.生命周期.信号)#任一触发即中止

    def 查询(自身,请求,信号=None):#执行一次提供方查询
        """在提供方 I/O 之前先尊重已经中止的信号，使已取消的请求永远不会启动服务器。"""
        自身.断言活动(信号)#进入前检查拆除与取消
        查询信号=自身.查询信号(信号)#融合后的查询信号
        工作区任务=操作任务()#规范化工作区
        飞行=操作任务()#飞行解析的结算尾
        with 自身.锁:#纳入拆除等待集
            自身.工作区解析集.add(飞行)#飞行集
        def 执行规范化():#后台规范化
            """规范化工作区。"""
            try:#规范化
                工作区=规范化工作区(自身.文件系统,请求['workspaceRoot'],查询信号)#得到规范工作区
                工作区任务.兑现(工作区)#成功
            except BaseException as 错误:
                工作区任务.拒绝(错误)#拒绝
            finally:#无论成败都移出飞行集
                try:#结算飞行尾
                    飞行.兑现(None)#结算
                except BaseException:#已结算
                    pass#忽略
                with 自身.锁:#移出
                    自身.工作区解析集.discard(飞行)#不再被拆除等待
        threading.Thread(target=执行规范化,daemon=True).start()#规范化
        try:#等待规范化
            工作区=工作区任务.等待()#得到规范工作区
        except BaseException:#失败也要等飞行尾
            try:#等飞行
                飞行.等待()#结算
            except BaseException:#忽略
                pass#忽略
            raise#抛出
        自身.断言活动(查询信号)#解析后再检查拆除与取消
        工作区键=工作区['target']['targetKey']#稳定工作区键
        def 执行生命周期():#在该工作区队列上执行完整生命周期
            """读源→打开→查询→关闭。"""
            自身.断言活动(查询信号)#轮到时再检查
            # 在工作区队列内、拉起之前读取：排队查询在轮到时看到当前字节。
            源=读宿主源(自身.文件系统,请求['filePath'],工作区,自身.配置['maxDocumentBytes'],查询信号)#读取并约束源
            自身.断言活动(查询信号)#读源后再检查
            实例=自身.取实例(工作区键,工作区)#取出或创建该工作区实例
            try:#经选中实例查询
                return 实例.查询(请求,源,查询信号)#串行查询
            except BaseException as 错误:#实例失败
                if 实例.是传输失败(错误) is False:#非传输失败则原样抛出
                    raise 错误#原样
                实例.拆除()#拆除已失败实例
                自身.若当前则驱逐(工作区键,实例)#若槽仍是它则丢掉
                自身.断言活动(查询信号)#替换前再检查
                实例=自身.取实例(工作区键,工作区)#换一个新实例
                return 实例.查询(请求,源,查询信号)#透明重试一次
            finally:#查询结束后处理死槽
                if 实例.已死:#实例已死
                    实例.拆除()#有界拆除
                    自身.若当前则驱逐(工作区键,实例)#若槽仍是它则丢掉
        return 自身.入队(工作区键,查询信号,执行生命周期)#排队

    def 入队(自身,工作区键,信号,运行):#按工作区串行排队
        """为一个规范工作区串行化一次完整查询生命周期。"""
        with 自身.锁:#取先前尾
            先前=自身.队列表[工作区键] if 工作区键 in 自身.队列表 else None#缺席则无先前工作
        结果任务=操作任务()#本查询结果
        def 执行排队工作():#可中止地等待先前工作再执行本查询
            """串行执行。"""
            try:#等待先前
                if 先前 is not None:#有先前尾才等
                    可中止等待(先前,信号)#可中止等待
                结果任务.兑现(运行())#执行本查询
            except BaseException as 错误:
                结果任务.拒绝(错误)#拒绝
        # 即便本调用方放弃等待，尾仍跟随实际的先前工作。它永不拒绝。
        尾=操作任务()#实际工作的结算尾
        def 跟尾():#尾跟随
            """等先前与本查询结算。"""
            if 先前 is not None:#有先前尾才等
                try:#等先前
                    先前.等待()#先前
                except BaseException:#不继承
                    pass#忽略
            try:#执行
                执行排队工作()#本查询
            finally:#结算尾
                尾.兑现(None)#永不拒绝
                with 自身.锁:#清槽
                    if 工作区键 in 自身.队列表 and 自身.队列表[工作区键] is 尾:#仍是本尾才删除
                        del 自身.队列表[工作区键]#删除
        with 自身.锁:#记下新尾
            自身.队列表[工作区键]=尾#新尾
        threading.Thread(target=跟尾,daemon=True).start()
        return 结果任务.等待()#交给调用方

    def 取实例(自身,工作区键,工作区):#取出或创建实例
        """返回或同步发布某个规范工作区的那一个实例。"""
        自身.断言活动()#创建前必须仍活着
        with 自身.锁:#互斥
            已有=自身.实例表[工作区键] if 工作区键 in 自身.实例表 else None#已有实例
            if 已有 is not None:#复用
                return 已有#复用活实例
            创建=自身.创建实例(工作区)#同步创建
            自身.实例表[工作区键]=创建#写入槽
            return 创建#交给调用方

    def 若当前则驱逐(自身,工作区键,实例):#条件驱逐
        """仅当槽里仍是这个实例时才丢掉。"""
        with 自身.锁:#互斥
            if 工作区键 in 自身.实例表 and 自身.实例表[工作区键] is 实例:#仍是本实例才删除
                del 自身.实例表[工作区键]#删除

    def 创建实例(自身,工作区):#按工作区组装并创建实例
        """组装实例规格并创建（握手惰性开始）。"""
        规格={#组装实例规格
            'command':自身.可执行,#已解析可执行路径
            'args':自身.配置['args'] if 'args' in 自身.配置 else [],#启动参数
            'cwd':工作区['canonicalPath'],#规范工作区路径
            'workspaceUri':工作区['fileUrl'],#规范工作区file URI
            'env':自身.配置['env'] if 'env' in 自身.配置 else {},#显式环境覆盖
            'configuration':自身.配置['configuration'] if 'configuration' in 自身.配置 else None,#静态配置回答
            'initializationOptions':自身.配置['initializationOptions'] if 'initializationOptions' in 自身.配置 else None,#initialize选项
            'maxMessageBytes':自身.配置['maxMessageBytes'],#单条消息上限
            'maxStderrBytes':自身.配置['maxStderrBytes'],#stderr尾上限
            'shutdownTimeoutMs':自身.配置['shutdownTimeoutMs'],#优雅关闭预算
            'killGraceMs':自身.配置['killGraceMs'],#杀进程宽限
        }#结束 spec
        return 语言服务器实例(规格,自身.拉起器)#创建实例

    def 拆除全部(自身):#拆除本提供方全部实例
        """拆除每一个活实例并挡住后续查询。"""
        自身.已拆除=True#挡住新查询
        自身.生命周期.中止(语言服务器错误('lsp-stdio 提供方已拆除','LSP_DISPOSED'))#中止飞行中的等待
        with 自身.锁:#快照
            活着=list(自身.实例表.values())#快照活实例
            排空=list(自身.队列表.values())#快照队列尾
            解析中=list(自身.工作区解析集)#快照飞行中的工作区解析
            自身.实例表.clear()#清空实例表
        失败列表=[]#拆除失败
        for 实例 in 活着:#拆除每个实例
            try:#拆除是同步等待
                实例.拆除()#拆除并等待
            except BaseException as 错误:#拆除失败
                失败列表.append(错误)#记下
        for 尾 in 排空:#等到队列尾结算
            try:#尾是操作任务
                尾.等待()#等待
            except BaseException as 错误:#排空失败
                失败列表.append(错误)#记下
        for 飞行 in 解析中:#等到工作区解析结算
            try:#飞行是操作任务
                飞行.等待()#等待
            except BaseException as 错误:#解析失败
                失败列表.append(错误)#记下
        with 自身.锁:#清空
            自身.队列表.clear()#清空队列表
            自身.工作区解析集.clear()#清空飞行解析集
        抛出拆除失败(失败列表,'lsp-stdio 实例拆除失败')#有失败则在全部结算后抛

def 应用(上下文,配置):
    """注册已配置的 stdio LSP 提供方。加载时（凭证擦洗之后）解析每一个可执行文件，再发布任何提供方；每个进程在首次匹配查询时惰性拉起。配置是 dict。"""
    服务器表=配置['servers'] if 'servers' in 配置 else {}#展开服务器表
    条目表=list(服务器表.items()) if isinstance(服务器表,dict) else []#条目
    if len(条目表)==0:#空表则加载失败
        raise 语言服务器错误('lsp-stdio: servers 至少要有一台服务器','LSP_INVALID_PROVIDER')
    搭建中止=中止控制器()#加载期取消控制器
    def 插件事件(纤维):
        """插件回调必须在 Cordis 能跑 effect 清理之前看见自己的拆除。纤维是 cordis 对象。"""
        if 纤维 is 上下文.纤程 and 纤维.编号 is None:#本插件纤程已拆除
            搭建中止.中止(语言服务器错误('lsp-stdio 搭建已拆除','LSP_DISPOSED'))#中止仍在进行的可执行解析
    停止监听=上下文.监听('internal/plugin',插件事件)#结束 拆除监听
    提供方列表=[]#先解析全部可执行文件再构造提供方
    查找列表=[]#并行解析条目
    try:#注册前先解析每一项服务器本地设置
        for 提供方标识,原始配置 in 条目表:#逐项（并行用线程）
            if str(提供方标识).strip()=='':#拒绝空id
                raise 语言服务器错误('lsp-stdio: 服务器 id 必须是非空字符串','LSP_INVALID_PROVIDER')
            已解析=原始配置#schema已填默认值
            校验服务器配置(提供方标识,已解析)#加载时校验预算与字节上限
            查找任务=操作任务()#解析任务
            查找列表.append(查找任务)#记下
            def 执行解析(标识=提供方标识,配置值=已解析,结果=查找任务):
                """解析可执行并构造提供方。"""
                try:#解析
                    if 已中止(搭建中止.信号):#已拆除
                        raise 中止错误(搭建中止.信号)#中止
                    可执行=上下文.subprocess.解析可执行文件(配置值['command'],配置值['env'] if 'env' in 配置值 else None,搭建中止.信号)#解析可执行路径
                    if 已中止(搭建中止.信号):#解析后若已拆除则抛错
                        raise 中止错误(搭建中止.信号)#中止
                    def 拉起(规格):
                        """子进程拉起器。"""
                        return 上下文.subprocess.启动(规格)
                    结果.兑现(本地语言服务器提供方(标识,上下文.fs,配置值,可执行,拉起))#构造隔离提供方
                except BaseException as 错误:
                    结果.拒绝(错误)#拒绝
            threading.Thread(target=执行解析,daemon=True).start()#并行解析
        try:#等待全部解析
            for 查找 in 查找列表:#逐项等待
                提供方列表.append(查找.等待())#全部成功才收下
        except BaseException as 错误:#任一项失败
            搭建中止.中止(错误)#取消其余仍在飞的解析
            全部结算(查找列表)#等到其余结算，避免未处理拒绝
            raise 错误#把原失败抛给加载器
    finally:#无论成败都卸监听
        停止监听()#停止拆除监听
    def 挂注册():
        """逐个注册，失败则回滚已发布的。"""
        拆除器列表=[]#已成功注册的拆除器
        try:#逐个注册
            for 提供方 in 提供方列表:#发布提供方
                拆除器列表.append(上下文.lsp.注册提供方(提供方))#注册
        except BaseException as 错误:#中途冲突或无效
            for 拆除 in reversed(拆除器列表):#逆序回滚已发布
                拆除()#回滚
            raise 错误#加载失败
        def 拆除全部():
            """先拆掉全部路由再拆进程，避免新查询打进正在排空的提供方。"""
            for 拆除 in reversed(拆除器列表):#逆序注销路由
                拆除()#注销
            失败列表=[]#提供方拆除失败
            for 提供方 in 提供方列表:#顺序拆除
                try:#拆除全部是同步等待
                    提供方.拆除全部()#拆除本提供方
                except BaseException as 错误:
                    失败列表.append(错误)#记下
            抛出拆除失败(失败列表,'lsp-stdio 提供方拆除失败')#有失败则抛
        return 拆除全部#拆除器
    上下文.副作用(挂注册,'lsp-stdio.registerProviders')#结束 注册副作用

默认=应用
name=名称#框架槽
inject=依赖#框架槽
Config=配置模式#框架槽
apply=应用#框架槽
default=默认#框架槽

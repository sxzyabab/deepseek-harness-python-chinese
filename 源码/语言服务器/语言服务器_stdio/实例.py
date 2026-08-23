"""一条语言服务器实例：一条连接，加上 initialize 握手、可中止的串行查询队列、瞬时 didOpen→请求→didClose 生命周期，以及有界拆除。一个实例拥有一个 (提供方 id, 规范工作区) 进程。查询经单一队列串行，以便一次未能拦住服务器的取消可以终止该实例而不杀掉无关工作；不同实例并行运行。"""
import threading#队列与拆除互斥
from ...依赖 import cordis#外部依赖胶水
承诺=cordis.工具.承诺#承诺
是否thenable=cordis.工具.是否thenable#可等待判定
已兑现=cordis.工具.已兑现#立刻兑现
from ..lsp import 语言服务器错误#带稳定code的语言服务器错误
from ..超时 import 截止,取已中止#有界截止期与已中止判定
from .取消 import 可中止等待,中止错误#可中止等待与中止错误
from .连接 import 语言服务器连接#JSON-RPC连接
from .翻译 import (
    协商位置编码,#协商位置编码
    归一悬停,#归一悬停
    归一位置列表,#归一位置列表
    请求方法,#操作到方法名
    支持操作,#操作是否被宣称
    支持瞬时打开,#是否支持瞬时打开
)#协议翻译

实例规格字段=('command','args','cwd','env','maxMessageBytes','maxStderrBytes','killGraceMs','configuration','workspaceUri','initializationOptions','shutdownTimeoutMs')#连接规格之外实例还需要的参数

生命周期空操作方法=set([#本宿主用空结果确认的服务器→客户端请求方法（无动态注册）
    'window/workDoneProgress/create',#工作进度创建
    'client/registerCapability',#动态注册能力
    'client/unregisterCapability',#动态注销能力
])#结束

客户端能力={#initialize时宣称的客户端能力
    'general':{'positionEncodings':['utf-16']},#只宣称utf-16位置编码
    'workspace':{'workspaceFolders':True,'configuration':True},#工作区文件夹与配置
    'textDocument':{#文本文档能力
        'synchronization':{'dynamicRegistration':False},#不同步动态注册
        'hover':{'contentFormat':['markdown','plaintext']},#悬停支持markdown与纯文本
        'definition':{'linkSupport':True},#定义支持LocationLink
        'implementation':{'linkSupport':True},#实现支持LocationLink
        'references':{},#引用查询（无额外选项）
    },#结束 textDocument
}#结束客户端能力

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 标记已结算():#宽限竞态的已结算哨兵
    """在取消宽限竞态中标记已结算的请求（任一结果都表示请求已结束）。"""
    return True#请求已结束

class 语言服务器实例:#一条已初始化的语言服务器实例
    """一个已初始化的服务器进程。不作为提供方导出——提供方对这些实例做单飞与池化。query() 串行；dispose() 拒绝排队工作并拆掉进程。"""
    def __init__(自身,规格,拉起器,写入器=None):#构造实例并启动握手
        """记下拉起、initialize 与拆除参数，并开始握手。"""
        自身.规格=规格#实例规格
        自身.连接=语言服务器连接(规格,拉起器,自身.回答服务器请求,写入器)#拉起连接并回答服务器请求
        自身.能力=None#握手后的服务器能力
        自身.队列=已兑现(None)#查询串行尾
        自身.已拆除=False#是否已拆除
        自身.拆除承诺=None#进行中的拆除
        自身.进程已关=False#进程是否已关闭
        自身.就绪=承诺()#握手完成边界
        自身.锁=threading.Lock()#队列与拆除互斥
        def 跑握手():#后台initialize
            """开始initialize握手。"""
            try:#握手
                自身.初始化()#initialize
                自身.就绪.兑现(None)#成功
            except BaseException as 错误:#握手失败
                自身.就绪.拒绝(错误)#拒绝每一条查询
        threading.Thread(target=跑握手,daemon=True).start()#开始握手
        def 盯关闭():#进程关闭后同步置位dead
            """等待连接关闭承诺。"""
            try:#等待
                解开(自身.连接.关闭承诺)#进程关闭
            except BaseException:#关闭路径失败
                pass#仍置位
            自身.进程已关=True#同步置位
        threading.Thread(target=盯关闭,daemon=True).start()#盯关闭

    @property#只读属性
    def 已死(自身):#同步存活检查
        """同步存活检查：进程已关闭或实例已拆除时为 true。"""
        return 自身.进程已关 or 自身.已拆除 or 自身.连接.已失败#进程已关、已拆除或传输已失败

    def 是传输失败(自身,错误):#是否为本实例的致命传输原因
        """测试捕获到的查询错误是否来自本实例的传输。"""
        return 自身.连接.失败于(错误)#按引用比较连接上的失败

    def 查询(自身,请求,源,信号=None):#经串行队列跑一次查询
        """经串行队列跑一次查询。"""
        结果承诺=承诺()#本查询结果
        with 自身.锁:#互斥排队
            先前=自身.队列#先前的队列尾
            def 跑():#可中止地等待队列尾再跑
                """轮到后跑瞬时打开生命周期。"""
                try:#等待先前并执行
                    可中止等待(先前,信号)#可中止地等待队列尾
                    值=自身.跑查询(请求,源,信号)#跑瞬时打开生命周期
                    结果承诺.兑现(值)#成功
                except BaseException as 错误:#查询失败
                    if 自身.是传输失败(错误):#传输失败则拆除实例
                        try:#拆除
                            自身.启动拆除()#拆除
                        except BaseException:#拆除失败
                            pass#仍抛原错
                    结果承诺.拒绝(错误)#把原错误交给调用方
            # 无论本查询结果如何都让尾活着，好让下一个调用方仍串行。尾跟随实际的先前工作，而不是可中止视图。
            尾=承诺()#实际工作的结算尾
            def 跟尾():#尾跟随实际工作
                """等先前与本查询都结算。"""
                try:#等先前
                    解开(先前)#先前
                except BaseException:#先前失败
                    pass#不继承
                try:#等本查询线程跑完
                    跑()#跑本查询（内含可中止等待）
                finally:#结算尾
                    尾.兑现(None)#尾永不拒绝
            threading.Thread(target=跟尾,daemon=True).start()#串行
            自身.队列=尾#记下新尾
        return 结果承诺.等待()#交给调用方

    def 初始化(自身):#与服务器做initialize握手
        """发送 initialize / initialized。"""
        初始化结果=自身.连接.请求('initialize',{#发送initialize请求
            # 子进程提供方可能跑在另一个 PID 命名空间或机器上；宿主 PID 会让服务器监视一个无关进程。
            'processId':None,#不把宿主pid交给服务器
            'rootUri':取字段(自身.规格,'workspaceUri'),#规范工作区URI
            'workspaceFolders':[{'uri':取字段(自身.规格,'workspaceUri'),'name':'workspace'}],#单个工作区文件夹
            'capabilities':客户端能力,#本宿主宣称的客户端能力
            'initializationOptions':取字段(自身.规格,'initializationOptions'),#静态初始化选项
        })#断言为initialize结果
        能力=取字段(初始化结果,'capabilities')#取出服务器能力
        # 省略的编码默认 utf-16；任何其他值都是协议错误，在此拒绝。
        协商位置编码(取字段(能力,'positionEncoding'))#锁定utf-16
        自身.能力=能力#记下能力供后续查询
        解开(自身.连接.通知('initialized',{}))#发送initialized通知

    def 跑查询(自身,请求,源,信号=None):#跑瞬时打开→请求→关闭
        """跑瞬时打开生命周期。"""
        if 自身.已拆除:#已拆除则拒绝
            raise 语言服务器错误('LSP instance was disposed','LSP_DISPOSED')#拒绝
        if 信号 is not None and 取已中止(信号):#进入前若已取消则抛错
            raise 中止错误(信号)#取消
        try:#等待握手，允许查询信号放弃
            可中止等待(自身.就绪,信号)#可中止地等待initialize
        except BaseException as 错误:#握手失败或等待被取消
            if not 自身.已死:#实例尚未死
                自身.启动拆除()#拆掉中毒实例
            raise 错误#把原失败交给调用方
        能力=自身.能力#握手后的能力
        if 能力 is None:#能力缺失则未初始化
            raise Exception('LSP instance is not initialized')#未初始化
        操作=取字段(请求,'operation')#语义操作
        if not 支持操作(能力,操作):#服务器未宣称该操作
            raise 语言服务器错误('server does not support '+str(操作),'LSP_UNSUPPORTED_OPERATION')#拒绝不支持的操作
        if not 支持瞬时打开(取字段(能力,'textDocumentSync')):#不支持瞬时打开关闭
            raise 语言服务器错误('server does not support the transient textDocument/didOpen this host requires','LSP_UNSUPPORTED_OPERATION')#拒绝缺少openClose
        网址=取字段(源,'fileUrl')#源文件URI
        已打开=False#是否已成功didOpen
        try:#打开文档、发请求、归一结果
            if 信号 is not None and 取已中止(信号):#didOpen前再检查取消
                raise 中止错误(信号)#取消
            try:#发送didOpen
                可中止等待(自身.连接.通知('textDocument/didOpen',{#瞬时打开文档
                    'textDocument':{#完整源文本
                        'uri':网址,#URI
                        'languageId':取字段(请求,'languageId'),#语言id
                        'version':1,#版本1
                        'text':取字段(源,'text'),#全文
                    },#textDocument结束
                }),信号)#可中止地等待写入
            except BaseException as 错误:#didOpen写入失败或被取消
                自身.启动拆除()#拆除不可用实例
                raise 错误#把原失败交给调用方
            已打开=True#已打开，finally需didClose
            载荷=自身.发送请求(操作,网址,取字段(请求,'position'),信号)#发送语义请求
            return 自身.归一(操作,载荷)#归一成seam结果
        finally:#无论成败都尝试关闭文档
            if 已打开 and not 自身.已死:#仍活着且已打开
                try:#发送didClose
                    解开(自身.连接.通知('textDocument/didClose',{'textDocument':{'uri':网址}}))#关闭瞬时文档
                except BaseException:#关闭写入失败
                    try:#拆除不可信实例
                        自身.启动拆除()#有界拆除
                    except BaseException:#拆除本身拒绝
                        pass#保留已结算的查询结果/错误

    def 发送请求(自身,操作,网址,位置,信号=None):#发送一条语义请求
        """发送语义请求并可选与取消竞态。"""
        参数={#请求参数
            'textDocument':{'uri':网址},#已打开文档
            'position':{'line':取字段(位置,'line'),'character':取字段(位置,'character')},#零基位置
        }#params骨架
        if 操作=='findReferences':#引用查询强制包含声明
            参数['context']={'includeDeclaration':True}#始终包含声明
        请求标识=自身.连接.窥视下一标识()#预先看见即将分配的id
        发送=承诺()#请求承诺包装
        def 跑发送():#后台发请求
            """发出带id请求。"""
            try:#请求
                发送.兑现(自身.连接.请求(请求方法(操作),参数))#响应
            except BaseException as 错误:#失败
                发送.拒绝(错误)#拒绝
        threading.Thread(target=跑发送,daemon=True).start()#发出
        if 信号 is None:#无取消则直接等待响应
            return 发送.等待()#等待
        return 自身.竞态中止(发送,请求标识,信号)#与取消竞态

    def 竞态中止(自身,发送,请求标识,信号):#请求与取消竞态
        """让未决请求与中止竞态。中止时发送 $/cancelRequest，并给服务器一段有界宽限去确认；若它未及时结算，则作废并拆除实例。"""
        try:#先等请求，允许信号放弃等待
            return 可中止等待(发送,信号)#可中止地等待响应
        except BaseException as 错误:#等待被拒绝
            if not 取已中止(信号):#不是取消则原样抛出
                raise 错误#原样
            自身.连接.取消(请求标识)#尽力发送$/cancelRequest
            宽限=截止(None,取字段(自身.规格,'killGraceMs'),'LSP_CANCEL_GRACE')#取消宽限截止期
            try:#宽限内看请求是否已结算
                已结算=False#默认未结算
                try:#请求结算与宽限竞态
                    可中止等待(发送.then(lambda _=None:标记已结算(),lambda _=None:标记已结算()),宽限.signal)#竞态
                    已结算=True#宽限耗尽前已结算
                except BaseException:#宽限到期或其它
                    已结算=False#未结算
                if not 已结算:#宽限内未结算则拆除
                    自身.启动拆除()#拆除
            finally:#无论是否拆除都释放截止期
                宽限.释放()#释放deadline
            raise 错误#把取消错误交给调用方

    def 归一(自身,操作,载荷):#把线协议结果收成seam联合
        """归一封闭结果联合。"""
        if 操作=='hover':#悬停
            return {'kind':'hover','hover':归一悬停(载荷)}#归一悬停
        # 文件系统提供方拥有执行平台的 URI 语法，可能与 harness 宿主不同。把该坐标保留到渲染。
        return {'kind':'locations','locations':归一位置列表(载荷),'resolvedWorkspaceUri':取字段(自身.规格,'workspaceUri')}#导航结果带规范工作区URI

    def 回答服务器请求(自身,方法,参数):#回答一条服务器→客户端请求
        """按方法分派服务器请求。"""
        if 方法=='workspace/configuration':#配置请求
            条目=取字段(参数,'items') if 参数 is not None else None#取出items
            项们=条目 if isinstance(条目,list) else []#缺席则空数组
            return [取字段(自身.规格,'configuration') for _ in 项们]#每项都回同一静态值
        if 方法 in 生命周期空操作方法:#生命周期记账请求
            return None#空成功
        if 方法=='workspace/applyEdit':#应用编辑
            raise Exception('workspace/applyEdit is not permitted by this host')#拒绝applyEdit
        raise Exception('unsupported server request: '+str(方法))#其余方法一律拒绝

    def 拆除(自身):#拆除本实例
        """拒绝排队工作，尝试优雅 shutdown/exit，再升级 SIGTERM→SIGKILL，并等待进程关闭。"""
        自身.启动拆除()#启动或加入那一次拆除事务

    def 启动拆除(自身):#单飞拆除事务
        """只发布一次拆除，并让每一个调用方等待同一条静止边界。"""
        with 自身.锁:#互斥
            自身.已拆除=True#挡住新查询
            if 自身.拆除承诺 is None:#只启动一次拆除
                自身.拆除承诺=承诺()#拆除承诺
                def 跑拆除():#后台拆除
                    """执行 tearDown。"""
                    try:#拆除
                        自身.执行拆除()#有界拆除
                        自身.拆除承诺.兑现(None)#成功
                    except BaseException as 错误:#拆除失败
                        自身.拆除承诺.拒绝(错误)#拒绝
                threading.Thread(target=跑拆除,daemon=True).start()#启动
            承诺对象=自身.拆除承诺#共用
        return 解开(承诺对象)#共用同一条静止边界

    def 执行拆除(自身):#优雅关闭失败则强制终止
        """尝试 shutdown/exit，再强制终止。"""
        关闭截止=截止(None,取字段(自身.规格,'shutdownTimeoutMs'),'LSP_SHUTDOWN')#优雅关闭截止期
        try:#尝试shutdown/exit
            自身.优雅关闭(关闭截止.signal)#有界优雅关闭
        except BaseException:#优雅关闭失败或超时
            pass#下面的进程树清理仍是权威的
        finally:#无论成败都释放截止期
            关闭截止.释放()#释放deadline
        自身.强制终止()#升级终止并等待退出

    def 优雅关闭(自身,信号):#有界优雅关闭
        """尽力而为的 LSP shutdown/exit，含进程关闭，由 signal 封顶。"""
        关闭发送=承诺()#shutdown请求承诺
        def 跑关闭():#后台shutdown
            """发送shutdown。"""
            try:#请求
                关闭发送.兑现(自身.连接.请求('shutdown',None))#有界等待shutdown响应
            except BaseException as 错误:#失败
                关闭发送.拒绝(错误)#拒绝
        threading.Thread(target=跑关闭,daemon=True).start()#发出
        可中止等待(关闭发送,信号)#与关闭截止竞态
        解开(自身.连接.通知('exit',None))#发送exit通知
        可中止等待(自身.连接.关闭承诺,信号)#有界等待进程关闭

    def 强制终止(自身):#强制终止并等待退出
        """终止进程树，然后等待领导者与辅助进程退出。这些等待有意无界。"""
        自身.连接.终止()#seam升级SIGTERM→宽限→SIGKILL
        解开(自身.连接.关闭承诺)#协议连接关闭
        自身.连接.等待进程树退出()#整棵进程树退出

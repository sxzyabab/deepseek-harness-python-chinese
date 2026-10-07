import threading#队列与拆除互斥
from ...工具.超时 import 截止,等待中止#有界截止期
from ...基础设施.js特性 import PromiseEX as 期约#就绪、查询、拆除等返回的期约
from ..语言服务器.异常 import 语言服务器错误#带稳定code的语言服务器错误
from .取消 import 可中止等待,中止错误#取消入口
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

class 语言服务器实例:#一条已初始化的语言服务器实例
    '一个已初始化的服务器进程。不作为提供方导出——提供方对这些实例做单飞与池化。查询() 串行；拆除() 拒绝排队工作并拆掉进程'
    def __init__(自身,规格,拉起器,写入器=None):#构造实例并启动握手
        '记下拉起、initialize 与拆除参数，并开始握手'
        自身.规格=规格#实例规格
        自身.连接=语言服务器连接(规格,拉起器,自身.回答服务器请求,写入器)#拉起连接并回答服务器请求
        自身.能力=None#握手后的服务器能力
        自身.队列=期约()#查询串行尾，从不拒绝；起点是已解决的期约
        自身.队列.解决(None)#尚无先前工作
        自身.已拆除=False#是否已拆除
        自身.拆除任务=None#进行中的拆除期约，之后共用
        自身.进程已关=False#进程是否已关闭
        自身.锁=threading.Lock()#队列与拆除互斥
        自身.就绪=自身.初始化()#握手完成边界，握手失败时拒绝每一条查询
        def 标记进程已关(关闭值=None):
            '进程关闭后同步置位dead'
            自身.进程已关=True#同步置位
        自身.连接.关闭任务.然后(标记进程已关,标记进程已关)#进程关闭

    @property#只读属性
    def 已死(自身):#同步存活检查
        '同步存活检查：进程已关闭或实例已拆除时为 true'
        return 自身.进程已关 or 自身.已拆除 or 自身.连接.已失败#进程已关、已拆除或传输已失败

    def 是传输失败(自身,错误):#是否为本实例的致命传输原因
        '测试捕获到的查询错误是否来自本实例的传输'
        return 自身.连接.失败于(错误)#按引用比较连接上的失败

    def 查询(自身,请求,源,信号=None):#经串行队列跑一次查询
        '经串行队列跑一次查询，返回期约，兑现归一后的结果。排队等待期间也观察中止：先前查询挂住时，后来的查询仍能放弃等待'
        结果=期约()#本查询结果
        with 自身.锁:#互斥排队
            先前=自身.队列#先前的队列尾
            尾=期约()#本查询的结算尾，永不拒绝
            自身.队列=尾#记下新尾
        def 查询失败(错误):
            '查询失败：传输失败则先尝试拆除实例，再把原错误交给调用方'
            if 自身.是传输失败(错误):#传输失败则拆除实例
                def 拆除之后(落定值=None):
                    '拆除尝试结束后拒绝'
                    结果.拒绝(错误)#把原错误交给调用方
                自身.等待拆除尝试().然后(拆除之后,拆除之后)#拆除
                return#已挂接
            结果.拒绝(错误)#把原错误交给调用方
        def 轮到本查询(队列值):
            '先前工作结算后，执行瞬时打开生命周期'
            自身.执行查询(请求,源,信号).然后(结果.解决,查询失败)#执行
        可中止等待(先前,信号).然后(轮到本查询,查询失败)#可中止地等待队列尾
        # 无论本查询结果如何都让尾活着，好让下一个调用方仍串行。尾跟随实际的先前工作，而不是可中止视图。
        def 尾落定(落定值=None):
            '尾永不拒绝：先前与本查询都结算后才解决'
            尾.解决(None)#解决
        def 等本查询(先前值=None):
            '先前结算后等本查询结算'
            结果.然后(尾落定,尾落定)#本查询
        先前.然后(等本查询,等本查询)#实际的先前工作
        return 结果#交给调用方

    def 初始化(自身):#与服务器做initialize握手
        '发送 initialize / initialized，返回期约，兑现于握手完成'
        结果=期约()#握手结果
        def 握手回应(初始化结果):
            'initialize 兑现后协商位置编码并发送 initialized'
            try:#协商
                能力=初始化结果['capabilities'] if 'capabilities' in 初始化结果 else None#取出服务器能力
                # 省略的编码默认 utf-16；任何其他值都是协议错误，在此拒绝。
                协商位置编码(能力['positionEncoding'] if 能力 is not None and 'positionEncoding' in 能力 else None)#锁定utf-16
            except Exception as 错误:#协议错误
                结果.拒绝(错误)#拒绝每一条查询
                return#已落定
            自身.能力=能力#记下能力供后续查询
            自身.连接.通知('initialized',{}).然后(结果.解决,结果.拒绝)#发送initialized通知
        自身.连接.请求('initialize',{#发送initialize请求
            # 子进程提供方可能跑在另一个 PID 命名空间或机器上；宿主 PID 会让服务器监视一个无关进程。
            'processId':None,#不把宿主pid交给服务器
            'rootUri':自身.规格['workspaceUri'],#规范工作区URI
            'workspaceFolders':[{'uri':自身.规格['workspaceUri'],'name':'workspace'}],#单个工作区文件夹
            'capabilities':客户端能力,#本宿主宣称的客户端能力
            'initializationOptions':自身.规格['initializationOptions'] if 'initializationOptions' in 自身.规格 else None,#静态初始化选项
        }).然后(握手回应,结果.拒绝)#断言为initialize结果
        return 结果#期约

    def 执行查询(自身,请求,源,信号=None):#执行瞬时打开→请求→关闭
        '执行瞬时打开生命周期，返回期约，兑现归一结果'
        结果=期约()#查询结果
        if 自身.已拆除:#已拆除则拒绝
            结果.拒绝(语言服务器错误('语言服务器实例已拆除','LSP_DISPOSED'))#拒绝
            return 结果#已落定
        if 信号 is not None and 已中止(信号):#进入前若已取消则拒绝
            结果.拒绝(中止错误(信号))#取消
            return 结果#已落定
        def 握手失败(错误):
            '握手失败或等待被取消：实例未死就拆掉中毒实例，再把原失败交给调用方'
            def 拆除之后(落定值=None):
                '拆除尝试结束后拒绝'
                结果.拒绝(错误)#把原失败交给调用方
            if not 自身.已死:#实例尚未死
                自身.等待拆除尝试().然后(拆除之后,拆除之后)#拆掉中毒实例
                return#已挂接
            拆除之后()#实例已死，直接拒绝
        def 握手完成(就绪值):
            '握手完成后检查能力，再瞬时打开文档、发请求、关闭文档'
            能力=自身.能力#握手后的能力
            if 能力 is None:#能力缺失则未初始化
                结果.拒绝(语言服务器错误('语言服务器实例尚未初始化','LSP_INTERNAL'))#未初始化
                return#已落定
            操作=请求['operation']#语义操作
            if 支持操作(能力,操作) is False:#服务器未宣称该操作
                结果.拒绝(语言服务器错误('服务器不支持 '+str(操作),'LSP_UNSUPPORTED_OPERATION'))#拒绝不支持的操作
                return#已落定
            if 支持瞬时打开(能力['textDocumentSync'] if 'textDocumentSync' in 能力 else None) is False:#不支持瞬时打开关闭
                结果.拒绝(语言服务器错误('服务器不支持本宿主所需的瞬时 textDocument/didOpen','LSP_UNSUPPORTED_OPERATION'))#拒绝缺少openClose
                return#已落定
            网址=源['fileUrl']#源文件URI
            已打开=False#是否已成功didOpen
            def 收尾(终结):
                '无论成败都尝试关闭文档：仍活着且已打开才发 didClose，关闭写入失败则拆除不可信实例，再执行终结'
                if 已打开 and not 自身.已死:#仍活着且已打开
                    def 关闭写入失败(关闭错误):
                        '关闭写入失败不改变已结算的结果，但实例已不可信，拆除它'
                        自身.等待拆除尝试().然后(终结,终结)#拆除后终结
                    自身.连接.通知('textDocument/didClose',{'textDocument':{'uri':网址}}).然后(终结,关闭写入失败)#关闭瞬时文档
                    return#已挂接
                终结()#无需关闭
            def 查询成功(载荷):
                '语义请求兑现：归一后先收尾再交出结果'
                try:#归一成seam结果
                    值=自身.归一(操作,载荷)#归一
                except Exception as 错误:#归一失败
                    查询失败(错误)#按失败收尾
                    return#已处理
                def 交出结果(落定值=None):
                    '收尾结束后交出结果'
                    结果.解决(值)#成功
                收尾(交出结果)#先收尾
            def 查询失败(错误):
                '语义请求失败：先收尾再交出原错误'
                def 交出错误(落定值=None):
                    '收尾结束后交出原错误'
                    结果.拒绝(错误)#原样
                收尾(交出错误)#先收尾
            def 打开失败(错误):
                'didOpen 写入失败或被取消：协议流已不可用，拆除实例让池驱逐，再交出原失败'
                def 拆除之后(落定值=None):
                    '拆除尝试结束后拒绝'
                    结果.拒绝(错误)#把原失败交给调用方
                自身.等待拆除尝试().然后(拆除之后,拆除之后)#拆除不可用实例
            def 已打开回调(打开值):
                'didOpen 写入完成：已打开，发送语义请求'
                nonlocal 已打开#改外层
                已打开=True#已打开，收尾需didClose
                自身.发送请求(操作,网址,请求['position'],信号).然后(查询成功,查询失败)#发送语义请求
            if 信号 is not None and 已中止(信号):#didOpen前再检查取消
                查询失败(中止错误(信号))#取消
                return#已处理
            可中止等待(自身.连接.通知('textDocument/didOpen',{#瞬时打开文档
                'textDocument':{#完整源文本
                    'uri':网址,#URI
                    'languageId':请求['languageId'],#语言id
                    'version':1,#版本1
                    'text':源['text'],#全文
                },#textDocument结束
            }),信号).然后(已打开回调,打开失败)#可中止地等待写入
        可中止等待(自身.就绪,信号).然后(握手完成,握手失败)#可中止地等待initialize
        return 结果#期约

    def 发送请求(自身,操作,网址,位置,信号=None):#发送一条语义请求
        '发送语义请求并可选与取消竞态，返回期约，兑现线协议载荷'
        参数={#请求参数
            'textDocument':{'uri':网址},#已打开文档
            'position':{'line':位置['line'],'character':位置['character']},#零基位置
        }#params骨架
        if 操作=='findReferences':#引用查询强制包含声明
            参数['context']={'includeDeclaration':True}#始终包含声明
        请求标识=自身.连接.窥视下一标识()#预先看见即将分配的id
        发送=自身.连接.请求(请求方法(操作),参数)#带id请求，期约
        if 信号 is None:#无取消则直接等待响应
            return 发送#响应期约
        return 自身.竞态中止(发送,请求标识,信号)#与取消竞态

    def 竞态中止(自身,发送,请求标识,信号):#请求与取消竞态
        '让未决请求与中止竞态，返回期约。中止时发送 $/cancelRequest，并给服务器一段有界宽限去确认；若它未及时结算，则作废并拆除实例'
        结果=期约()#竞态结果
        def 等待被拒(错误):
            '等待被拒绝：不是取消则原样拒绝；是取消则发 $/cancelRequest 并在宽限内看请求是否结算'
            if not 已中止(信号):#不是取消则原样拒绝
                结果.拒绝(错误)#原样
                return#已落定
            自身.连接.取消(请求标识)#尽力发送$/cancelRequest
            宽限=截止(None,自身.规格['killGraceMs'],'LSP_CANCEL_GRACE')#取消宽限截止期
            def 宽限耗尽执行器(解决,拒绝):
                '宽限截止期到达时以 False 解决，作为竞态的另一边'
                def 等宽限():
                    '阻塞到宽限截止期中止'
                    等待中止(宽限.signal)#等待
                    解决(False)#宽限耗尽
                threading.Thread(target=等宽限,daemon=True).start()#等待宽限
            def 标记已结算(落定值=None):
                '请求不论成败结算都算已结算'
                return True#请求已结束
            已结算哨=发送.然后(标记已结算,标记已结算)#发送落定哨，兑现 True
            def 收尾(落定值=None):
                '释放截止期后把取消错误交给调用方'
                宽限.释放()#释放deadline
                结果.拒绝(错误)#把取消错误交给调用方
            def 宽限结果(已结算):
                '宽限内未结算则拆除实例，再收尾'
                if not 已结算:#宽限内未结算则拆除
                    自身.等待拆除尝试().然后(收尾,收尾)#拆除
                    return#已挂接
                收尾()#已结算
            期约.竞速([已结算哨,期约(宽限耗尽执行器)]).然后(宽限结果,收尾)#请求结算与宽限竞态
        可中止等待(发送,信号).然后(结果.解决,等待被拒)#先等请求，允许信号放弃等待
        return 结果#期约

    def 归一(自身,操作,载荷):#把线协议结果收成seam联合
        '归一封闭结果联合'
        if 操作=='hover':#悬停
            return {'kind':'hover','hover':归一悬停(载荷)}#归一悬停
        # 文件系统提供方拥有执行平台的 URI 语法，可能与 harness 宿主不同。把该坐标保留到渲染。
        return {'kind':'locations','locations':归一位置列表(载荷),'resolvedWorkspaceUri':自身.规格['workspaceUri']}#导航结果带规范工作区URI

    def 回答服务器请求(自身,方法,参数):#回答一条服务器→客户端请求
        '按方法分派服务器请求；这些回答不需要等待，直接返回结果或抛出'
        if 方法=='workspace/configuration':#配置请求
            条目=参数['items'] if 参数 is not None and 'items' in 参数 else None#取出items
            项列表=条目 if isinstance(条目,list) else []#缺席则空数组
            return [自身.规格['configuration'] if 'configuration' in 自身.规格 else None for 项 in 项列表]#每项都回同一静态值
        if 方法 in 生命周期空操作方法:#生命周期记账请求
            return None#空成功
        if 方法=='workspace/applyEdit':#应用编辑
            raise 语言服务器错误('本宿主不允许 workspace/applyEdit','LSP_UNSUPPORTED_OPERATION')#拒绝applyEdit
        raise 语言服务器错误('不支持的服务器请求: '+str(方法),'LSP_UNSUPPORTED_OPERATION')#其余方法一律拒绝

    def 拆除(自身):#拆除本实例
        '拒绝排队工作，尝试优雅 shutdown/exit，再升级 SIGTERM→SIGKILL，并等待进程关闭。返回期约'
        return 自身.启动拆除()#启动或加入那一次拆除事务

    def 启动拆除(自身):#单飞拆除事务
        '只发布一次拆除，并让每一个调用方等待同一条静止边界，返回期约'
        需要启动=False#本调用是否负责启动拆除
        with 自身.锁:#互斥
            自身.已拆除=True#挡住新查询
            if 自身.拆除任务 is None:#只启动一次拆除
                自身.拆除任务=期约()#拆除期约
                需要启动=True#本调用启动
            任务对象=自身.拆除任务#共用
        if 需要启动:#锁外启动，免得同步回调重入时死锁
            自身.执行拆除().然后(任务对象.解决,任务对象.拒绝)#拆除结果交给共用期约
        return 任务对象#共用同一条静止边界

    def 等待拆除尝试(自身):#拆除失败只留给提供方汇总
        '等拆除结束，拆除失败保留在记忆的拆除期约里，由提供方再等一次并与查询结果一起汇报，所以这里不论成败都兑现。返回期约'
        尝试结果=期约()#尝试结果
        def 尝试结束(落定值=None):
            '拆除不论成败都结束了'
            尝试结果.解决(None)#解决
        自身.启动拆除().然后(尝试结束,尝试结束)#等拆除
        return 尝试结果#期约

    def 执行拆除(自身):#优雅关闭失败则强制终止
        '尝试 shutdown/exit，再强制终止，返回期约'
        结果=期约()#拆除结果
        关闭截止=截止(None,自身.规格['shutdownTimeoutMs'],'LSP_SHUTDOWN')#优雅关闭截止期
        def 强制收尾(落定值=None):
            '优雅关闭不论成败都结束了：释放截止期，升级终止并等待静止；托管范围清理才是权威'
            关闭截止.释放()#释放deadline
            自身.强制终止().然后(结果.解决,结果.拒绝)#升级终止并等待退出
        自身.优雅关闭(关闭截止.signal).然后(强制收尾,强制收尾)#有界优雅关闭
        return 结果#期约

    def 优雅关闭(自身,信号):#有界优雅关闭
        '尽力而为的 LSP shutdown/exit，含进程关闭，由 signal 封顶。返回期约'
        结果=期约()#优雅关闭结果
        def 已回应(关闭值):
            'shutdown 响应后发送 exit 通知'
            自身.连接.通知('exit',None).然后(已通知,结果.拒绝)#发送exit通知
        def 已通知(通知值):
            'exit 写入后有界等待进程关闭'
            可中止等待(自身.连接.关闭任务,信号).然后(结果.解决,结果.拒绝)#有界等待进程关闭
        可中止等待(自身.连接.请求('shutdown',None),信号).然后(已回应,结果.拒绝)#与关闭截止竞态
        return 结果#期约

    def 强制终止(自身):#强制终止并等待退出
        '终止提供方托管范围，然后等待直接服务器结果与整段范围静止，返回期约。这些等待有意无界，因为静止——而不是再一个定时器——才是拆除欠调用方的后置条件'
        自身.连接.终止()#seam升级SIGTERM→宽限→SIGKILL
        return 期约.全部([自身.连接.关闭任务,自身.连接.等待进程树退出()])#协议连接关闭与托管范围退出

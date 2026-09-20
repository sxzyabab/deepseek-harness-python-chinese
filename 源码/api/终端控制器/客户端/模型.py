import threading#写入链、流消费与渲染确认
from ....内核.作用域 import 操作任务#创建与关闭
from ....工具.加密 import 随机uuid#附着身份
from ....工具.超时 import 中止控制器,已中止,等待中止,若已中止则抛出#寿命
from ...网关.流载体 import 远程流载体错误#载体失败
from ..类型 import 远程错误#视图失败
from .外壳偏好 import 首选外壳,记住外壳#偏好

__all__=['终端视图错误','终端视图','快照存储']#仅中文公开名

视图问题表=('missingTerminal','inputFull','attachmentEnded','invalidOutput','terminalLimit')#产品键

class 快照存储:#getSnapshot / subscribe / set
    """可观察快照；一次替换。"""
    def __init__(自身,初值):#记下
        """初值。"""
        自身._状态=初值#状态
        自身._监听=set()#订阅者
    def getSnapshot(自身):#读
        """当前快照。"""
        return 自身._状态#状态
    def subscribe(自身,监听):#订
        """返回取消。"""
        自身._监听.add(监听)#登记
        return lambda:自身._监听.discard(监听)#取消
    def set(自身,下一):#写
        """替换并通知。"""
        自身._状态=下一#写
        for 回调 in list(自身._监听):#派发
            try:#单回调
                回调()#通知
            except Exception as 错误:
                print('[terminal-controller] subscriber failed:',错误)#日志

class 终端视图错误(远程错误):#本视图失败
    """code=terminal/view，details.issue 为产品键。"""
    def __init__(自身,问题,消息=None):#记下
        """缺省消息即问题键。"""
        super().__init__('terminal/view',问题 if 消息 is None else 消息,{'issue':问题})#构造

def 取值(结果):#解开 Remote 信封
    """失败则抛出 error。"""
    if not 结果['ok']:
        失败=结果['error']#载荷
        详情=失败['details'] if 'details' in 失败 else {}#详情
        raise 远程错误(失败['code'],失败['message'],详情)#包装
    return 结果['value']#值

def 取码(错误):#结构识别
    """看 code 字段。"""
    if isinstance(错误,dict):#信封
        return 错误['code'] if 'code' in 错误 else None#码
    return getattr(错误,'code',None)#对象

def 取详情(错误):#详情
    """details。"""
    if isinstance(错误,dict):#信封
        return 错误['details'] if 'details' in 错误 else None#详情
    return getattr(错误,'details',None)#对象

class 终端视图:#侧栏出现；进程只在显式关闭时结束
    """DOM 卸挂不杀进程。"""
    def __init__(自身,会话标识,远程,网关,标识,缺失则创建=True,壳路径=None,保持=None):#构造
        """网关提供 $stream；保持为窗口确认回调。"""
        自身._会话标识=会话标识#会话
        自身._远程=远程#terminal 面
        自身._网关=网关#Gateway
        自身.id=标识#Host 身份
        自身._缺失则创建=缺失则创建#新标签才分配
        自身._壳路径=壳路径#引导所选
        自身._保持=保持#窗口保持就绪
        自身.状态=快照存储({'phase':'idle','writable':False})#可观察
        自身._寿命=中止控制器()#寿命
        自身._流=None#当前输出流
        自身._已挂=False#DOM 已挂
        自身._附着标识=None#可写附着
        自身._待渲染=None#等确认
        自身._修订=0#渲染修订
        自身._创建中=None#分配任务
        自身._加载=None#刷新任务
        自身._关闭中=None#关闭任务
        自身._写入=操作任务()#输入链
        自身._写入.兑现(None)#空链
        自身._排队输入=0#未完成输入字节
        自身._拆除中=set()#已拆流

    def 挂载(自身):#DOM 寿命
        """返回卸挂；卸挂不结束进程。"""
        自身._已挂=True#挂
        快照=自身.状态.getSnapshot()#状态
        if 'info' not in 快照 or 快照['info'] is None:#尚无进程
            threading.Thread(target=自身.刷新,daemon=True).start()#刷新
        else:#已有
            自身.连接()#接
        def 卸挂():#DOM 卸
            """放流。"""
            自身._已挂=False#卸
            自身.拆除()#拆流
        return 卸挂#回调

    def 刷新(自身):#启动或恢复，去重
        """已列终端缺失时不得静默换壳。"""
        if 自身._创建中 is not None:#分配中
            自身._创建中.等待()#等
            return
        if 自身._加载 is not None:#刷新中
            自身._加载.等待()#等
            return
        if 自身._关闭中 is not None or 已中止(自身._寿命.信号):#停
            return#空
        自身._补丁({'phase':'loading','error':None,'issue':None})#加载
        任务=操作任务()#本轮
        自身._加载=任务#记下
        def 在线程执行():#线程
            """查环境与列表，创建或收养。"""
            try:#加载
                环境盒={}#环境
                列表盒={}#列表
                失败盒={}#错误
                def 取环境():#并行
                    """environment。"""
                    try:#调
                        环境盒['值']=取值(自身._远程.environment(自身._会话标识,自身._寿命.信号))#环境
                    except BaseException as 错误:
                        失败盒['错误']=错误#记下
                def 取列表():#并行
                    """list。"""
                    try:#调
                        列表盒['值']=取值(自身._远程.list(自身._会话标识))#列表
                    except BaseException as 错误:
                        失败盒['错误']=错误#记下
                线1=threading.Thread(target=取环境)#环境
                线2=threading.Thread(target=取列表)#列表
                线1.start()#启
                线2.start()#启
                线1.join()#等
                线2.join()#等
                if '错误' in 失败盒:#有
                    raise 失败盒['错误']#抛
                环境=环境盒['值']#环境
                可用=列表盒['值']#列表
                if 自身._已停():#停
                    任务.兑现(None)#完
                    return
                自身._补丁({'environment':环境})#环境
                信息=None#命中
                for 项 in 可用:
                    if 项['id']==自身.id:#命中
                        信息=项#记下
                        break#停
                if 信息 is not None:#已有
                    自身._收养(信息)#收养
                elif 自身._缺失则创建:#新标签
                    路径=自身._壳路径#显式
                    if 路径 is None:#用偏好
                        壳列=取值(自身._远程.shells(自身._会话标识,自身._寿命.信号))#探测
                        上次=首选外壳()#偏好
                        路径=None#未选
                        for 壳 in 壳列:#找偏好
                            if 壳['path']==上次:#可用
                                路径=壳['path']#用
                                break#停
                        if 路径 is None and len(壳列)>0:#回落默认
                            路径=壳列[0]['path']#第一
                    if 自身._已停():#停
                        任务.兑现(None)#完
                        return
                    if 路径 is not None:#有壳
                        记住外壳(路径)#记下
                    自身._创建(环境,路径)#分配
                else:#恢复失败
                    raise 终端视图错误('missingTerminal')#缺失
                任务.兑现(None)#完
            except BaseException as 错误:
                自身._失败(错误)#发布
                任务.兑现(None)#吞
            finally:#清
                自身._加载=None#放
        threading.Thread(target=在线线程执行).start()#跑
        任务.等待()#等

    def _已停(自身):#关闭或寿命尽
        """不再推进分配。"""
        return 已中止(自身._寿命.信号) or 自身._关闭中 is not None#停

    def _创建(自身,环境,壳路径=None):#分配壳
        """用环境限额夹住初始尺寸。"""
        自身._补丁({'phase':'creating','error':None,'issue':None})#创建中
        任务=操作任务()#本轮
        自身._创建中=任务#记下
        def 在线程执行():#线程
            """create 后收养。"""
            try:#创建
                请求={'id':自身.id,'cols':min(80,环境['maxCols']),'rows':min(24,环境['maxRows'])}#请求
                if 壳路径 is not None:#指定壳
                    请求['shellPath']=壳路径#路径
                信息=取值(自身._远程.create(自身._会话标识,请求,自身._寿命.信号))#创建
                if not 已中止(自身._寿命.信号):#未取消
                    自身._收养(信息)#收养
                任务.兑现(None)#完
            except BaseException as 错误:
                自身._失败(错误)#发布
                任务.兑现(None)#吞
            finally:#清
                自身._创建中=None#放
        threading.Thread(target=在线线程执行).start()#跑
        任务.等待()#等

    def _收养(自身,信息):#已有 Host 终端
        """保持确认后再连接。"""
        自身._补丁({'info':信息,'title':信息['title']})#元数据
        if 自身._保持 is None:#无保持
            if 自身._已挂 and 自身._关闭中 is None:#可接
                自身.连接()#接
            return
        def 后台():
            """等保持。"""
            try:
                自身._保持(自身._寿命.信号)#就绪
                if 自身._已挂 and 自身._关闭中 is None and not 自身._已停():#可接
                    自身.连接()#接
            except BaseException as 错误:
                if not 自身._已停():#仍活
                    自身._失败(错误)
        threading.Thread(target=后台,daemon=True).start()#后台

    def 连接(自身):#新屏幕并夺回输入
        """已挂且未关闭才开流。"""
        快照=自身.状态.getSnapshot()#状态
        信息=快照['info'] if 'info' in 快照 else None#信息
        if 信息 is None or not 自身._已挂 or 自身._关闭中 is not None or 已中止(自身._寿命.信号):#不可
            return#跳
        自身.拆除()#放旧流
        盒={'流':None}#闭包
        def 打开(信号):#开口
            """保持后再新附着身份。"""
            if 自身._保持 is not None:#有保持
                自身._保持(信号)#就绪
            若已中止则抛出(信号)#中止
            附着标识=随机uuid()#身份
            自身._附着标识=附着标识#记下
            return 自身._远程.follow(自身._会话标识,信息['id'],附着标识,信号)#跟随
        def 结束(已接受):#正常结束
            """附着结束。"""
            return 终端视图错误('attachmentEnded')
        def 载体失败(错误):#丢包
            """标断开。"""
            if 自身._流 is 盒['流']:#仍是本流
                自身._补丁({'phase':'disconnected','writable':False})#断开
        流选项={
            'name':'Browser terminal output',#名
            'open':打开,#开口
            'ended':结束,
            'carrierFailed':载体失败,#载体
        }#选项
        流工厂=getattr(自身._网关,'$stream')#工厂
        流=流工厂(流选项)#开
        盒['流']=流#记下
        自身._流=流#记下
        自身._补丁({'phase':'connecting','writable':False,'error':None,'issue':None,'render':None})#连接中
        threading.Thread(target=自身._消费,args=(流,),daemon=True).start()#消费

    def 确认(自身,修订):#xterm 已解析
        """只确认当前待渲染修订。"""
        待=自身._待渲染#待
        if 待 is None or 待['revision']!=修订:#过期
            return#跳
        待['resolve']()#放行
        自身._待渲染=None#清

    def 写入(自身,数据):#原始输入串行
        """并发 RPC 不得打乱按键序。"""
        状态=自身.状态.getSnapshot()#状态
        附着标识=自身._附着标识#附着
        信息=状态['info'] if 'info' in 状态 else None#信息
        可写=状态['writable'] if 'writable' in 状态 else False#可写
        if not 可写 or 信息 is None or 附着标识 is None:#不可
            return#跳
        字节=len(数据.encode('utf-8'))#UTF-8
        环境=状态['environment'] if 'environment' in 状态 else None#环境
        上限=环境['maxInputBytes'] if 环境 is not None else 0#上限
        if 自身._排队输入+字节>上限:#满
            自身._失败(终端视图错误('inputFull'))#满
            return#跳
        自身._排队输入+=字节#记账
        标识=信息['id']#终端
        上一=自身._写入#前
        当前=操作任务()#本
        自身._写入=当前#链
        def 在线程执行():#线程
            """等前一个再写。"""
            try:#前
                上一.等待()#等
            except BaseException:#忽略
                pass#继续
            try:#写
                现=自身.状态.getSnapshot()#现态
                现写=现['writable'] if 'writable' in 现 else False#可写
                if 自身._附着标识!=附着标识 or not 现写:#过期
                    当前.兑现(None)#完
                    return#跳
                取值(自身._远程.write(自身._会话标识,标识,附着标识,数据))#写
                当前.兑现(None)#完
            except BaseException as 错误:
                if 自身._附着标识==附着标识:#仍本附着
                    自身._失败(错误)#发布
                当前.拒绝(错误)#拒绝
            finally:#还账
                自身._排队输入-=字节#还
        threading.Thread(target=在线线程执行).start()#跑

    def 调整尺寸(自身,列,行):#仅可写视图
        """夹到环境限额。"""
        状态=自身.状态.getSnapshot()#状态
        附着标识=自身._附着标识#附着
        信息=状态['info'] if 'info' in 状态 else None#信息
        可写=状态['writable'] if 'writable' in 状态 else False#可写
        if not 可写 or 信息 is None or 附着标识 is None:#不可
            return#跳
        if 信息['cols']==列 and 信息['rows']==行:#未变
            return#跳
        标识=信息['id']#终端
        环境=状态['environment'] if 'environment' in 状态 else None#环境
        if 环境 is not None:#有限额
            列=min(列,环境['maxCols'])#列
            行=min(行,环境['maxRows'])#行
        上一=自身._写入#前
        当前=操作任务()#本
        自身._写入=当前#链
        def 在线程执行():#线程
            """等前一个再调。"""
            try:#前
                上一.等待()#等
            except BaseException:#忽略
                pass#继续
            try:#调
                现=自身.状态.getSnapshot()#现态
                现写=现['writable'] if 'writable' in 现 else False#可写
                if 自身._附着标识!=附着标识 or not 现写:#过期
                    当前.兑现(None)#完
                    return#跳
                取值(自身._远程.resize(自身._会话标识,标识,附着标识,列,行))#调
                当前.兑现(None)#完
            except BaseException as 错误:
                if 自身._附着标识==附着标识:#仍本附着
                    自身._失败(错误)#发布
                当前.拒绝(错误)#拒绝
        threading.Thread(target=在线线程执行).start()#跑

    def 重命名(自身,标题):#显示名
        """成功后立刻反映到视图。"""
        快照=自身.状态.getSnapshot()#状态
        现标=快照['title'] if 'title' in 快照 else None#现
        if 标题.strip()==现标 or 已中止(自身._寿命.信号):#未变
            return#跳
        try:#改
            取值(自身._远程.rename(自身._会话标识,自身.id,标题))#远程
            去空白=标题.strip()#去空白
            当前=自身.状态.getSnapshot()#现
            信息=当前['info'] if 'info' in 当前 else None#信息
            补丁={'title':去空白}#补丁
            if 信息 is not None:#有信息
                拷=dict(信息)#拷
                拷['title']=去空白#标题
                补丁['info']=拷#写回
            自身._补丁(补丁)#发布
        except BaseException as 错误:
            自身._失败(错误)#发布

    def 关闭(自身):#显式杀进程范围
        """失败可重试。"""
        if 自身._关闭中 is not None:#已开始
            自身._关闭中.等待()#等
            return
        自身._补丁({'phase':'closing','writable':False,'error':None,'issue':None})#关闭中
        自身.拆除()#放流
        任务=操作任务()#本轮
        自身._关闭中=任务#记下
        def 在线程执行():#线程
            """等未完成创建再 close。"""
            try:#关
                if 自身._创建中 is not None:#创建未完
                    自身._创建中.等待()#等
                取值(自身._远程.close(自身._会话标识,自身.id))#关
                自身.拆除()#再拆
                自身._补丁({'phase':'closed','writable':False})#已关
                任务.兑现(None)#完
            except BaseException as 错误:
                自身._关闭中=None#可重试
                自身._失败(错误)#发布
                任务.拒绝(错误)#拒绝
        threading.Thread(target=在线线程执行).start()#跑
        任务.等待()#等

    def 释放(自身):#插件卸载，不关 Host
        """等到已拆流结束。"""
        自身._已挂=False#卸
        自身._寿命.中止()#中止
        自身.拆除()#拆当前
        for 任务 in list(自身._拆除中):#先前
            任务.等待()#等

    def 拆除(自身):#放当前流
        """确认待渲染并拆流。"""
        上一=自身._流#旧
        自身._流=None#清
        自身._附着标识=None#放权
        if 自身._待渲染 is not None:#有待
            自身._待渲染['resolve']()#放行
            自身._待渲染=None#清
        if 上一 is None:#无
            return#跳
        任务=操作任务()#拆除任务
        自身._拆除中.add(任务)#登记
        def 在线程执行():#线程
            """拆底层流。"""
            try:#拆
                上一.拆除()#拆
                任务.兑现(None)#完
            except BaseException as 错误:
                任务.拒绝(错误)#拒绝
            自身._拆除中.discard(任务)#摘
        threading.Thread(target=在线线程执行).start()#跑

    def _消费(自身,流):#跟输出
        """代际必须先有 snapshot。"""
        代际=0#已接受代
        序号=0#输出序号
        try:#读
            for 项 in 流:#逐项
                if 自身._流 is not 流:#已换
                    return#停
                帧=项.value#帧
                if 代际!=项.generation:#新代
                    if 帧['type']!='snapshot':#缺屏
                        raise 终端视图错误('invalidOutput','Terminal output generation is missing its screen snapshot')#缺
                    代际=项.generation#记下
                    序号=帧['sequence']#序号
                    项.接受()#开口
                elif 帧['type']=='output':#增量
                    if 帧['sequence']!=序号+1:#缺口
                        raise 终端视图错误('invalidOutput','Terminal output sequence has a gap')#缺口
                    序号=帧['sequence']#推进
                elif 帧['type']=='snapshot':#意外
                    raise 终端视图错误('invalidOutput','Unexpected terminal screen snapshot')#意外
                if 帧['type']!='output':#状态或快照
                    信息=帧['info']#信息
                    控制=信息['controllerId'] if 'controllerId' in 信息 else None#控制者
                    可写=信息['state']=='running' and 控制==自身._附着标识#控制权
                    自身._补丁({'info':信息,'title':信息['title'],'phase':'connected','writable':可写})#连接
                if 帧['type']!='state':#需渲染
                    自身._修订+=1#修订
                    修订=自身._修订#捕获
                    完成=threading.Event()#确认
                    def 解决():#放行
                        """确认或中止。"""
                        完成.set()#放
                    自身._待渲染={'revision':修订,'resolve':解决}#记下
                    def 中止时():#流取消
                        """当确认。"""
                        自身.确认(修订)#确认
                    def 监视():#等中止
                        """代际信号。"""
                        等待中止(项.signal)#等
                        中止时()#确认
                    threading.Thread(target=监视,daemon=True).start()#监视
                    自身._补丁({'render':{'revision':修订,'frame':帧}})#渲染
                    if 已中止(项.signal):#已取消
                        中止时()#立刻
                    完成.wait()#等 DOM
        except BaseException as 错误:
            if 自身._流 is 流:#仍本流
                快照=自身.状态.getSnapshot()#状态
                信息=快照['info'] if 'info' in 快照 else None#信息
                状态名=信息['state'] if 信息 is not None else None#态
                if 状态名=='exited':#已退出
                    自身._补丁({'phase':'closed','writable':False})#关
                else:
                    自身._失败(错误)#发布

    def _补丁(自身,补丁):#合并快照
        """寿命尽则忽略。"""
        if 已中止(自身._寿命.信号):#已拆
            return#跳
        当前=自身.状态.getSnapshot()#现
        下一=dict(当前)#拷
        下一.update(补丁)#叠
        自身.状态.set(下一)#写

    def _失败(自身,错误):#发布失败
        """只读拒绝不清屏；载体失败标断开。"""
        码=取码(错误)#码
        if 码=='terminal/control-unavailable':#只读或未运行
            自身._补丁({'writable':False,'error':None,'issue':None})#禁输入
            return
        问题=None#产品键
        if 码=='terminal/view':#本视图
            详情=取详情(错误)#详情
            if isinstance(详情,dict) and 'issue' in 详情:#有
                问题=详情['issue']#键
        elif 码=='terminal/limit-reached':#限额
            问题='terminalLimit'#键
        阶段='disconnected' if isinstance(错误,远程流载体错误) else 'failed'#阶段
        if isinstance(错误,BaseException) and len(错误.args)>0:#消息
            消息=str(错误.args[0])#第一参
        else:#其它
            消息=str(错误)#串
        自身._补丁({'phase':阶段,'writable':False,'issue':问题,'error':消息})#发布

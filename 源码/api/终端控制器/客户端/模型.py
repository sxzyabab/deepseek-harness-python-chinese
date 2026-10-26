'不依赖 React 的浏览器终端状态，以及可重连的远程流'
from threading import Event as 事件#画面确认与刷新汇合
from threading import RLock as 可重入锁#输入记账
from threading import current_thread as 当前线程#重入与拆除
from collections import deque#尚未发出的输入
from ....客户端.存储 import 创建快照存储#可观察状态
from ....基础设施.通用工具 import (
    启动守护线程,#后台刷新
    获取内部数据,#逻辑流工厂
    紧凑json编码,#帧字节
    utf8字节数,#输入字节
)
from ....类型化远程调用.协议 import 远程错误,取远程错误#失败码
from ...网关.异常 import 远程流载体错误#传输断开
from ...网关.流协议 import 已中止,若中止则抛 as 若已中止则抛出#取消
from ....客户端.连接.rpc import 中止信号,中止控制器#取消
from ..异常 import 终端视图错误#视图失败
from .命令解释器偏好 import 首选命令解释器,记住命令解释器#壳偏好

__all__=['终端视图','取出值']#视图与信封


def 取出值(结果):
    '远程信封失败则抛出。没有 ok 字段时当作已经解开的值'
    if not isinstance(结果,dict) or 'ok' not in 结果:#不是信封
        return 结果#原样
    if 结果['ok']:#成功
        return 结果['value'] if 'value' in 结果 else None#业务值
    错误=结果['error']#失败载荷
    if isinstance(错误,BaseException):#已经是异常
        raise 错误#原样
    if isinstance(错误,dict):#线路上的 code/message/details
        码=错误['code'] if 'code' in 错误 else 'gateway/internal'#码
        消息=错误['message'] if 'message' in 错误 else ''#说明
        详情=错误['details'] if 'details' in 错误 else {}#细节
        raise 远程错误(码,消息,详情)#还原远程错误
    raise RuntimeError(str(错误))#其余失败


def 新建盒():
    '一次可等待的结算。失败写在盒子上'
    盒=事件()#落定
    盒.错误=None#失败
    return 盒#盒子


class 终端视图:
    '视图活过 DOM 卸挂。只有明确关闭才结束进程'
    def __init__(自身,会话标识,远程,网关,标识,缺失则创建=True,壳路径=None,保持=None):
        '记下会话、远程、身份，以及新标签才允许分配'
        自身._会话标识=会话标识#所属会话
        自身._远程=远程#terminal 命名空间
        自身._网关=网关#带逻辑流的远程服务
        自身.id=标识#宿主终端身份
        自身._缺失则创建=缺失则创建#已列出的终端不能悄悄换掉
        自身._壳路径=壳路径#引导时选定的壳
        自身._保持=保持#输出附着前要等的窗口确认
        自身.状态=创建快照存储({'phase':'idle','writable':False})#可观察状态
        自身._寿命=中止控制器()#视图寿命
        自身._流=None#当前输出流
        自身._已挂=False#DOM 还在
        自身._附着=None#当前输入附着
        自身._待渲染=None#等仿真确认的修订
        自身._修订=0#本地渲染修订
        自身._创建中=None#分配进行中
        自身._加载中=None#刷新进行中
        自身._关闭中=None#关闭进行中
        自身._跑线程=None#正在跑刷新的线程
        自身._消费线程=None#正在读输出的线程
        自身._锁=可重入锁()#输入与标志

    def 挂载(自身):
        '接上 DOM 寿命。返回的卸挂不结束进程'
        自身._已挂=True#已挂
        if 自身.状态.getSnapshot().get('info') is None:#还没有进程信息
            启动守护线程(自身.刷新)#不挡住挂载
        else:#已经有进程
            自身.连接()#重新附着

        def 卸挂():
            '卸挂只拆流'
            自身._已挂=False#已卸
            自身._拆除附着()#进程继续

        return 卸挂#交给调用方

    def 刷新(自身):
        '启动或恢复这个标签。同一次刷新不重复跑。重入直接返回'
        with 自身._锁:#看是否已有同一次
            if 自身._跑线程 is 当前线程():#补丁回调里又进来了
                return#外层还在跑
            if 自身._创建中 is not None:#分配进行中
                等待=自身._创建中#等它
                要跑=False#不另起
            elif 自身._加载中 is not None:#刷新进行中
                等待=自身._加载中#等它
                要跑=False#不另起
            elif 自身._关闭中 is not None or 已中止(自身._寿命.信号):#已关或已拆
                return#不再分配
            else:#开始这一次
                等待=None#不用等
                要跑=True#跑
                自身._加载中=新建盒()#占住
                自身._跑线程=当前线程()#记下
        if not 要跑:#已有同一次
            if 等待 is not None:#等别的线程跑完
                等待.wait()#汇合
            return#结束
        自身._补丁({'phase':'loading','error':None,'issue':None})#进入读取
        try:#环境、列表，然后创建或收养
            环境结果=自身._远程.environment(自身._会话标识,自身._寿命.信号)#限额
            列表结果=自身._远程.list(自身._会话标识)#已保留
            环境=取出值(环境结果)#解开
            可用=取出值(列表结果)#解开
            if 自身._已停():#中途停了
                return#不再推进
            自身._补丁({'environment':环境})#记下限额
            信息=None#命中的终端
            for 项 in 可用:#按身份找
                if 项['id']==自身.id:#命中
                    信息=项#记下
                    break#停
            if 信息 is not None:#已有进程
                自身._收养(信息)#恢复
            elif 自身._缺失则创建:#新标签才分配
                路径=自身._壳路径#引导选定
                if 路径 is None:#没指定就用记住的或第一个
                    壳列=取出值(自身._远程.shells(自身._会话标识,自身._寿命.信号))#已安装
                    上次=首选命令解释器()#偏好
                    for 壳 in 壳列:#找还能用的偏好
                        if 壳['path']==上次:#可用
                            路径=壳['path']#用它
                            break#停
                    if 路径 is None and len(壳列)>0:#没有偏好
                        路径=壳列[0]['path']#第一个
                if 自身._已停():#查壳期间停了
                    return#不再分配
                if 路径 is not None:#有壳就记住
                    记住命令解释器(路径)#下次还能用
                自身._创建(环境,路径)#分配
            else:#列出的终端不见了
                raise 终端视图错误('missingTerminal')#不能悄悄换一个
        except BaseException as 错误:#失败写进状态，不向外抛
            自身._失败(错误)#发布
        finally:#放开同一次刷新
            with 自身._锁:#清标志
                盒=自身._加载中#这一次
                自身._加载中=None#允许下一次
                自身._跑线程=None#重入结束
            if 盒 is not None:#有盒子
                盒.set()#放开等待者

    def _已停(自身):
        '寿命尽或正在关闭时不再推进分配'
        return 已中止(自身._寿命.信号) or 自身._关闭中 is not None#停

    def _创建(自身,环境,壳路径=None):
        '用环境限额夹住初始尺寸。失败写进状态'
        自身._补丁({'phase':'creating','error':None,'issue':None})#正在启动
        盒=新建盒()#这一次分配
        with 自身._锁:#发布进行中
            自身._创建中=盒#关闭会等它
        try:#向宿主要终端
            请求={'id':自身.id,'cols':min(80,环境['maxCols']),'rows':min(24,环境['maxRows'])}#初始尺寸
            if 壳路径 is not None:#指定了壳
                请求['shellPath']=壳路径#带上
            信息=取出值(自身._远程.create(自身._会话标识,请求,自身._寿命.信号))#分配
            if not 已中止(自身._寿命.信号):#还活着
                自身._收养(信息)#进入连接
        except BaseException as 错误:#失败可重试
            自身._失败(错误)#发布
        finally:#分配盒子结束
            with 自身._锁:#清掉
                自身._创建中=None#允许下一次
            盒.set()#放开关闭等待

    def _收养(自身,信息):
        '记下进程。有窗口保持时先等确认再连接'
        自身._补丁({'info':信息,'title':信息['title']})#元数据
        if 自身._保持 is None:#不需要保持
            if 自身._已挂 and 自身._关闭中 is None:#已经挂上
                自身.连接()#附着
            return#结束
        def 确认后连接():
            '保持确认后再附着。失败且还没停就发布'
            try:#等确认
                自身._保持(自身._寿命.信号)#窗口确认
                if 自身._已挂 and 自身._关闭中 is None:#仍然挂着
                    自身.连接()#附着
            except BaseException as 错误:#确认失败
                if not 自身._已停():#还要给用户看
                    自身._失败(错误)#发布
        启动守护线程(确认后连接)#不挡住收养

    def 连接(自身):
        '用新的屏幕重新附着，并重新拿到输入控制'
        快照=自身.状态.getSnapshot()#当前
        信息=快照.get('info')#进程
        if 信息 is None or not 自身._已挂 or 自身._关闭中 is not None or 已中止(自身._寿命.信号):#不能连
            return#跳过
        自身._拆除附着()#拆掉上一条
        流盒={'流':None}#回调里要对上这一条

        def 打开(信号):
            '先等窗口保持，再把宿主附着里的帧交出来'
            if 自身._保持 is not None:#需要确认
                自身._保持(信号)#等确认
            若已中止则抛出(信号)#确认期间取消
            句柄=自身._远程.attach(自身._会话标识,信息['id'],信号)#宿主附着
            附着={#这一代输入
                'handle':句柄,#可 send 的流
                'signal':信号,#代际取消
                'sequence':0,#下一条序号从 1 起
                'acknowledged':0,#已确认
                'pending':{},#序号到字节
                'queued':deque(),#还没发出
                'window':None,#载体窗口
                'bytes':0,#未确认的原始输入
                'bufferedBytes':0,#未确认的帧字节
                'inFlightBytes':0,#已发出未确认
            }#附着
            自身._附着=附着#当前
            try:#逐帧交给逻辑流
                for 帧 in 句柄:#宿主帧
                    if isinstance(帧,dict) and 帧.get('type')=='snapshot':#基线带窗口
                        附着['window']=帧.get('inputWindow')#可能没有
                    yield 帧#交给监督流
            finally:#这一代结束
                if 自身._附着 is 附着:#还是这一代
                    自身._附着=None#摘掉

        def 结束(已接受=None):
            '附着正常结束'
            return 终端视图错误('attachmentEnded')#产品键

        def 载体失败(错误=None):
            '物理流失败时标成断开'
            if 自身._流 is 流盒['流']:#还是这一条
                自身._补丁({'phase':'disconnected','writable':False})#断开

        流=获取内部数据(自身._网关,'stream')({#可重连输出
            'name':'Browser terminal output',#名字
            'open':打开,#打开一代
            'ended':结束,#结束原因
            'carrierFailed':载体失败,#传输失败
        })#流
        流盒['流']=流#给回调对上
        自身._流=流#当前
        自身._补丁({'phase':'connecting','writable':False,'error':None,'issue':None,'render':None})#正在连接
        自身._消费线程=启动守护线程(自身._消费,流)#后台读

    def 确认(自身,修订):
        '仿真解析完这一帧之后放开下一条'
        待=自身._待渲染#当前等待
        if 待 is None or 待['revision']!=修订:#不是这一帧
            return#忽略
        待['完成'].set()#放开
        自身._待渲染=None#清掉

    def 写入(自身,数据):
        '在原始 UTF-8 和编码帧预算内排队。断线后不重放'
        if len(数据)==0:#空输入
            return#跳过
        自身._送出('write',{'data':数据},utf8字节数(数据))#排队

    def 调整尺寸(自身,列,行):
        '只有当前可写的视图才改尺寸，并且和键盘输入排在一起'
        自身._送出('resize',{'cols':列,'rows':行},0)#排队

    def _送出(自身,种类,字段,字节):
        '在锁里检查预算并尽量发出。输入失败在锁外拆流'
        错误=None#锁外再处理
        with 自身._锁:#记账
            状态=自身.状态.getSnapshot()#当前
            附着=自身._附着#当前附着
            if not 状态.get('writable') or 状态.get('info') is None or 附着 is None or 已中止(附着['signal']):#不能写
                return#跳过
            if 种类=='write':#原始输入预算
                环境=状态.get('environment') if isinstance(状态.get('environment'),dict) else {}#限额
                上限=环境['maxInputBytes'] if 'maxInputBytes' in 环境 else 0#没有环境则当 0
                if 附着['bytes']+字节>上限:#超了
                    错误=终端视图错误('inputFull')#满了
            else:#改尺寸
                信息=状态['info']#当前尺寸
                列=字段['cols']#请求列
                行=字段['rows']#请求行
                if 信息['cols']==列 and 信息['rows']==行:#没变
                    return#跳过
                环境=状态.get('environment') if isinstance(状态.get('environment'),dict) else {}#限额
                if 'maxCols' in 环境:#有列上限
                    列=min(列,环境['maxCols'])#夹住
                if 'maxRows' in 环境:#有行上限
                    行=min(行,环境['maxRows'])#夹住
                字段={'cols':列,'rows':行}#夹过的尺寸
            if 错误 is None:#预算通过
                命令={'type':种类,'sequence':附着['sequence']+1}#下一条
                命令.update(字段)#写或尺寸
                帧字节=utf8字节数(紧凑json编码(命令))#命令本身
                窗口=附着['window']#载体窗口
                if isinstance(窗口,dict):#有开销
                    帧字节+=窗口['frameOverheadBytes'] if 'frameOverheadBytes' in 窗口 else 0#加上封套
                环境=状态.get('environment') if isinstance(状态.get('environment'),dict) else {}#缓冲上限
                缓冲上限=环境['maxBufferedBytes'] if 'maxBufferedBytes' in 环境 else 0#没有则当 0
                单帧过大=isinstance(窗口,dict) and 'maxBytes' in 窗口 and 帧字节>窗口['maxBytes']#一帧就超了
                if 附着['bufferedBytes']+帧字节>缓冲上限 or 单帧过大:#帧预算不够
                    错误=终端视图错误('inputFull')#满了
                else:#收下
                    附着['queued'].append({'command':命令,'inputBytes':字节,'frameBytes':帧字节})#排队
                    附着['sequence']=命令['sequence']#推进
                    附着['bytes']+=字节#原始字节
                    附着['bufferedBytes']+=帧字节#帧字节
                    错误=自身._刷出已锁(附着)#能发就发
        if isinstance(错误,BaseException):#锁外拆流
            自身._输入失败(错误)#失败并拆除

    def _刷出已锁(自身,附着):
        '锁已持有。发出队首，直到窗口满、不可写或发送失败'
        while 自身._附着 is 附着 and not 已中止(附着['signal']) and 自身.状态.getSnapshot().get('writable'):#还能发
            下一条=附着['queued'].popleft() if 附着['queued'] else None#队首
            if 下一条 is None:#空了
                return None#完成
            窗口=附着['window']#载体窗口
            if isinstance(窗口,dict) and 'maxBytes' in 窗口 and 附着['inFlightBytes']+下一条['frameBytes']>窗口['maxBytes']:#在途已满
                附着['queued'].appendleft(下一条)#放回去
                return None#等确认
            try:#发给载体
                附着['handle'].send(下一条['command'])#发送
            except BaseException as 错误:#发送失败
                附着['queued'].appendleft(下一条)#放回去
                return 错误#交给锁外
            附着['pending'][下一条['command']['sequence']]={'inputBytes':下一条['inputBytes'],'frameBytes':下一条['frameBytes']}#等确认
            附着['inFlightBytes']+=下一条['frameBytes']#在途
        return None#这一轮停了

    def _输入失败(自身,错误):
        '输入失败后拆掉附着，进程还在'
        自身._失败(错误)#发布
        自身._拆除附着()#拆流

    def 重命名(自身,标题):
        '改宿主显示名。成功后立刻反映到视图'
        if 标题.strip()==自身.状态.getSnapshot().get('title') or 已中止(自身._寿命.信号):#没变或已拆
            return#跳过
        try:#等宿主
            取出值(自身._远程.rename(自身._会话标识,自身.id,标题))#改名
            当前=自身.状态.getSnapshot().get('info')#现有信息
            补丁={'title':标题.strip()}#显示名
            if 当前 is not None:#有信息
                补丁['info']={**当前,'title':标题.strip()}#一起改
            自身._补丁(补丁)#发布
        except BaseException as 错误:#失败留在视图
            自身._失败(错误)#发布

    def 关闭(自身):
        '明确终止这个视图的进程。失败可以再试'
        with 自身._锁:#看是否已在关
            已有=自身._关闭中#进行中的那一次
        if 已有 is not None:#加入
            已有.wait()#等
            if 已有.错误 is not None:#失败
                raise 已有.错误#同一失败
            return#成功
        自身._补丁({'phase':'closing','writable':False,'error':None,'issue':None})#正在关闭
        自身._拆除附着()#先拆流
        盒=新建盒()#这一次
        with 自身._锁:#发布进行中
            if 自身._关闭中 is not None:#刚才有人开始了
                已有=自身._关闭中#改等它
            else:#占住
                已有=None#自己关
                自身._关闭中=盒#记下
        if 已有 is not None:#加入后到的那一次
            已有.wait()#等
            if 已有.错误 is not None:#失败
                raise 已有.错误#同一失败
            return#成功
        try:#即使创建被拒绝，也可能留下要关的分配
            创建=自身._创建中#进行中的分配
            if 创建 is not None:#等它落定
                创建.wait()#成败都等
            取出值(自身._远程.close(自身._会话标识,自身.id))#关宿主
            自身._拆除附着()#再拆一次
            自身._补丁({'phase':'closed','writable':False})#已关闭
        except BaseException as 错误:#失败可重试
            with 自身._锁:#清掉以便再关
                自身._关闭中=None#允许再试
            自身._失败(错误)#发布
            盒.错误=错误#加入者看见
            盒.set()#放开
            raise#原样
        盒.set()#成功

    def 释放(自身):
        '插件卸下时停掉客户端工作，不关宿主终端'
        自身._已挂=False#卸挂
        自身._寿命.中止配套信号()#停掉刷新和保持
        自身._拆除附着()#拆流

    def _拆除附着(自身):
        '停掉当前流。正在读这条流的线程不自己等自己'
        先前=自身._流#上一条
        线程=自身._消费线程#读者
        自身._流=None#先摘掉
        自身._附着=None#输入作废
        自身._消费线程=None#摘掉线程
        if 自身._待渲染 is not None:#还在等画面
            自身._待渲染['完成'].set()#放开读者
            自身._待渲染=None#清掉
        if 先前 is not None:#有流
            先前.dispose()#停掉
        if 线程 is not None and 线程 is not 当前线程():#别的线程在读
            线程.join()#等它退出

    def _消费(自身,流):
        '一代必须先有快照。输出序号要连续。画面要等仿真确认'
        代际=0#当前代
        序号=0#输出序号
        try:#读到流结束或失败
            for 项 in 流:#每一项
                if 自身._流 is not 流:#已经换了
                    return#停
                帧=项.value#业务帧
                if 代际!=项.generation:#新的一代
                    if 帧['type']!='snapshot':#缺屏幕
                        raise 终端视图错误('invalidOutput','Terminal output generation is missing its screen snapshot')#拒绝
                    代际=项.generation#记下
                    序号=帧['sequence']#基线序号
                    项.accept()#开口已接受
                elif 帧['type']=='output':#后续输出
                    if 帧['sequence']!=序号+1:#有缺口
                        raise 终端视图错误('invalidOutput','Terminal output sequence has a gap')#拒绝
                    序号=帧['sequence']#推进
                elif 帧['type']=='snapshot':#一代里不能再来屏幕
                    raise 终端视图错误('invalidOutput','Unexpected terminal screen snapshot')#拒绝
                if 帧['type']=='ack':#输入确认
                    自身._确认输入(帧)#减预算
                    continue#不画
                if 帧['type']!='output':#快照或状态
                    可写=帧['info']['state']=='running' and 帧['writable']#运行且这一路可写
                    自身._补丁({'info':帧['info'],'title':帧['info']['title'],'phase':'connected','writable':可写})#已连接
                if 帧['type']!='state':#快照和输出要等仿真
                    自身._等待画面(项,帧)#等确认
                    if 自身._流 is not 流:#等待期间被拆
                        return#停
        except BaseException as 错误:#这一条流失败
            if 自身._流 is 流:#还是这一条
                信息=自身.状态.getSnapshot().get('info')#进程
                if isinstance(信息,dict) and 信息.get('state')=='exited':#已经退出
                    自身._补丁({'phase':'closed','writable':False})#当成关闭
                else:#其余失败
                    自身._失败(错误)#发布

    def _确认输入(自身,帧):
        '按顺序减掉已确认的输入，再继续发'
        错误=None#锁外处理
        with 自身._锁:#改记账
            附着=自身._附着#当前
            if 附着 is None:#没有附着
                错误=终端视图错误('invalidOutput','Terminal acknowledgement has no attachment')#拒绝
            else:#核对序号
                待定=附着['pending'].get(帧['sequence'])#这一条的字节
                if 帧['sequence']!=附着['acknowledged']+1 or 待定 is None:#乱序
                    错误=终端视图错误('invalidOutput','Terminal input acknowledgement is out of order')#拒绝
                else:#按顺序确认
                    附着['acknowledged']=帧['sequence']#推进
                    附着['bytes']-=待定['inputBytes']#减原始
                    附着['bufferedBytes']-=待定['frameBytes']#减帧
                    附着['inFlightBytes']-=待定['frameBytes']#减在途
                    附着['pending'].pop(帧['sequence'],None)#摘掉
                    if 'refusal' in 帧 and 帧['refusal'] is not None:#控制被拒绝
                        自身._补丁({'writable':False})#变成只读
                    错误=自身._刷出已锁(附着)#窗口有空了
        if isinstance(错误,BaseException):#确认本身非法或发送失败
            if isinstance(错误,终端视图错误) and 错误.details.get('issue')=='invalidOutput':#协议失败
                raise 错误#交给消费循环
            自身._输入失败(错误)#输入失败拆流

    def _等待画面(自身,项,帧):
        '把这一帧交给仿真，等它确认或这一代被取消'
        自身._修订+=1#新修订
        修订=自身._修订#记下
        完成=事件()#仿真或取消
        自身._待渲染={'revision':修订,'完成':完成}#当前帧
        停止=中止控制器()#等完就停监听
        融合=中止信号.任一([项.signal,停止.信号])#代际取消或等完

        def 听取消():
            '这一代取消则当成已确认'
            融合._事件.wait()#阻塞
            if 已中止(项.signal):#代际没了
                自身.确认(修订)#放开

        启动守护线程(听取消)#后台听
        自身._补丁({'render':{'revision':修订,'frame':帧}})#交给仿真
        if 已中止(项.signal):#补丁时已经取消
            自身.确认(修订)#放开
        完成.wait()#等仿真或取消
        停止.中止配套信号()#停监听

    def _补丁(自身,补丁):
        '寿命尽则忽略。一次替换整个快照'
        if 已中止(自身._寿命.信号):#已拆
            return#忽略
        当前=dict(自身.状态.getSnapshot())#拷贝
        当前.update(补丁)#盖上
        自身.状态.set(当前)#通知

    def _失败(自身,错误):
        '载体失败标成断开。视图、限额和不可用收成产品键'
        远程=取远程错误(错误)#按 code
        问题=None#产品键
        if 远程 is not None and 远程.code=='terminal/view':#视图失败
            问题=远程.details.get('issue')#原键
        elif 远程 is not None and 远程.code=='terminal/limit-reached':#名额
            问题='terminalLimit'#产品键
        elif 远程 is not None and 远程.code=='terminal/unavailable':#没有了
            问题='missingTerminal'#产品键
        if isinstance(错误,远程流载体错误):#传输
            阶段='disconnected'#断开
        else:#业务失败
            阶段='failed'#失败
        说明=str(错误)#给人看的说明
        自身._补丁({'phase':阶段,'writable':False,'issue':问题,'error':说明})#发布

'一路 PTY、有界终端仿真和可拆开的浏览器跟随者'
import codecs#流式 UTF-8
from threading import Event as 事件#排空与屏幕写完
from threading import Condition as 条件变量#输出块
from threading import RLock as 可重入锁#屏幕与输入串行
from collections import deque#输出块
from ...工具.惰性导入 import 创建惰性导入#无头终端
from ...基础设施.通用工具 import 启动守护线程,utf8字节数#消费输出与输入字节
from ...基础设施.通用工具.数值判定 import 最大安全整数#序号与尺寸
from ...类型化远程调用.协议 import 远程错误,取远程错误#控制拒绝
from ..网关.流协议 import 已中止,若中止则抛 as 若已中止则抛出#附着取消
from .输出跟随 import 终端跟随#一路输出
from .保持 import 终端保持,等到结果#无人值守与期约

__all__=['浏览器终端']#仅这一类

加载无头=创建惰性导入('@xterm/headless',__file__)#无头终端
加载序列化=创建惰性导入('@xterm/addon-serialize',__file__)#屏幕序列化


def 是安全整数(值):
    '排除布尔后的安全整数'
    if isinstance(值,bool) or not isinstance(值,int):#布尔是 int 的子类
        return False#不是
    if 值>最大安全整数 or 值<-最大安全整数:#超出双精度整数
        return False#不是
    return True#是


class 浏览器终端:
    '进程寿命独立于跟随者和组件寿命'
    def __init__(自身,句柄,信息,回滚行,最大缓冲字节):
        '装上无头屏幕并开始排空进程输出'
        自身.句柄=句柄#已分配的终端进程
        自身.info=信息#当前元数据
        自身._最大缓冲字节=最大缓冲字节#每路跟随者的上限
        无头=加载无头()#无头模块
        序列化模块=加载序列化()#序列化模块
        终端类=无头.Terminal#仿真类
        序列化类=序列化模块.SerializeAddon#序列化类
        自身.屏幕=终端类({'cols':信息['cols'],'rows':信息['rows'],'scrollback':回滚行,'allowProposedApi':True})#有界屏幕
        自身.序列化=序列化类()#序列化插件
        自身.屏幕.loadAddon(自身.序列化)#装上
        自身.跟随者=set()#还在收输出的附着
        自身.序号=0#输出序号
        自身._操作锁=可重入锁()#屏幕、输入和快照串行
        自身._已退出=False#提供方完成先于排空
        自身._关闭任务=None#进行中的进程清理
        自身._保持器=None#提交后才有
        自身._控制=None#当前独占输入的跟随者
        自身._排空=事件()#输出消费结束
        启动守护线程(自身._消费输出)#排空进程输出

    def 监视(自身,策略,关闭中,已关,失败时):
        '分配提交给会话所有者之后才开始监视'
        def 终止():
            '先关上身份，再等进程静止，然后摘掉所有者记录'
            关闭中()#关闭 id
            自身._关闭进程()#终止并排空
            已关()#摘掉记录

        自身._保持器=终端保持(策略,自身.句柄.检查活动,终止,失败时)#无人值守

    def 保持进程(自身,信号):
        '独立于输出附着保持已提交的进程'
        if 自身._保持器 is None:#还没提交
            raise RuntimeError('Terminal has not been committed')#拒绝
        yield from 自身._保持器.保持(信号)#确认和寿命

    def 附着(自身,输入,限额,信号,输入窗口=None):
        '独占输入。更早的附着继续收输出。先给屏幕，再给输出、状态和确认'
        若已中止则抛出(信号)#进来时已取消
        跟随者=终端跟随(自身._最大缓冲字节)#这一路队列

        def 建立基线():
            '在操作锁里登记控制者并做出屏幕快照'
            若已中止则抛出(信号)#排队期间被取消
            自身._控制=跟随者#这一路独占输入
            自身._广播状态()#其余附着变成只读
            快照={'type':'snapshot','sequence':自身.序号,'screen':自身.序列化.serialize(),'info':自身.info,'writable':自身._可写(跟随者)}#基线
            if 输入窗口 is not None:#载体有入站帧上限
                快照['inputWindow']=输入窗口#交给客户端
            自身.跟随者.add(跟随者)#此后接收广播
            return 快照#第一帧

        基线=自身._排入(建立基线)#串行拿到快照
        输入迭代=iter(输入)#网关解码后的命令
        命令线程=启动守护线程(自身._消费输入,输入迭代,跟随者,限额,信号)#边输出边读命令
        try:#先交基线，再跟跟随者队列
            yield 基线#屏幕
            yield from 跟随者.读取(信号)#输出、状态和确认
        finally:#拆开这一路，进程继续活着
            自身.跟随者.discard(跟随者)#不再广播给它
            跟随者.关闭()#停读
            if 自身._控制 is 跟随者:#它还握着输入
                自身._控制=None#放开
                自身._广播状态()#其余附着看见只读
            关闭迭代=getattr(输入迭代,'close',None)#同步迭代器的 return
            if 关闭迭代 is not None:#有关闭
                关闭迭代()#打断还堵在 next 上的读取
            命令线程.join()#等输入泵结束

    def 重命名(自身,标题):
        '把显示名发给每一个已附着的视图'
        自身.info={**自身.info,'title':标题}#换标题
        自身._广播状态()#推状态帧

    def 关闭(自身):
        '终止提供方拥有的整个进程范围，再放开屏幕。失败可以再试'
        if 自身._保持器 is not None:#已经在监视
            自身._保持器.关闭()#由保持去终止
            return#保持那一次负责结果
        自身._关闭进程()#没有监视时直接关进程

    def 释放(自身):
        '停止无人值守调度并等最后一次进程清理'
        if 自身._保持器 is not None:#有监视
            自身._保持器.释放()#停表并清理
            return#里面会关进程
        自身._关闭进程()#没有监视时直接关进程

    def _消费输入(自身,输入迭代,跟随者,限额,信号):
        '按序号吃命令。序列缺口让这一路失败，控制拒绝只确认不重放'
        序号=0#从 1 开始核对
        try:#失败交给跟随者，不杀掉终端
            while True:#直到命令结束、取消或附着失效
                try:#迭代器结束
                    命令=next(输入迭代)#下一条
                except StopIteration:#没有更多命令
                    return#正常结束
                if 已中止(信号) or not 跟随者.仍活动:#不再接受
                    return#留下进程
                序号+=1#先推进再核对
                if not 是安全整数(命令['sequence']) or 命令['sequence']!=序号:#有缺口
                    raise RuntimeError('Terminal input sequence has a gap')#不补洞

                def 执行(命令=命令):
                    '在屏幕锁里写或改尺寸'
                    若已中止则抛出(信号)#执行前再看取消
                    自身._要求控制(跟随者)#只读或已退出则拒绝
                    if 命令['type']=='write':#键盘输入
                        if utf8字节数(命令['data'])>限额['maxInputBytes']:#超过单次上限
                            raise RuntimeError('Terminal input exceeds the configured limit')#拒绝
                        if 自身._保持器 is not None:#有无人值守
                            自身._保持器.作废()#输入打断空闲
                        等到结果(自身.句柄.写入(命令['data']))#交给提供方
                    elif 命令['type']=='resize':#改尺寸
                        列=命令['cols']#列
                        行=命令['rows']#行
                        if (not 是安全整数(列) or 列<2 or 列>限额['maxCols']
                                or not 是安全整数(行) or 行<1 or 行>限额['maxRows']):#超出限额
                            raise RuntimeError('Terminal dimensions exceed the configured limits')#拒绝
                        等到结果(自身.句柄.调整尺寸(列,行))#提供方
                        自身.屏幕.resize(列,行)#仿真
                        自身.info={**自身.info,'cols':列,'rows':行}#记下
                        自身._广播状态()#尺寸变化
                    else:#网关编解码本应排除
                        raise RuntimeError('Terminal input command is not a known type')#闭合失败

                try:#控制拒绝变成带 refusal 的确认
                    自身._排入(执行)#串行
                    跟随者.推入({'type':'ack','sequence':序号})#提供方已接受
                except BaseException as 错误:#看是控制拒绝、已退出，还是要失败
                    远程=取远程错误(错误)#按 code 认
                    if 远程 is not None and 远程.code=='terminal/control-unavailable':#只读或未运行
                        跟随者.推入({'type':'ack','sequence':序号,'refusal':远程.details['reason']})#不重放
                    elif 自身._已退出:#进程已经结束
                        跟随者.推入({'type':'ack','sequence':序号,'refusal':'not-running'})#不重放
                    else:#其余失败拆掉这一路
                        raise#交给下面的失败
        except BaseException as 错误:#输入或输出失败只影响这一路
            if isinstance(错误,Exception):#普通异常
                跟随者.失败(错误)#报告给读者
            else:#BaseException 但不是 Exception
                跟随者.失败(RuntimeError(str(错误)))#收成 Error

    def _可写(自身,跟随者):
        '只有当前控制者、进程仍在跑、且还没开始关闭时可写'
        未退出=not 自身._已退出#提供方还没完成
        未关=自身._关闭任务 is None#还没开始清理
        在跑=自身.info['state']=='running'#元数据仍是运行
        是控制=自身._控制 is 跟随者#这一路握着输入
        return 未退出 and 未关 and 在跑 and 是控制#四项都要

    def _广播状态(自身):
        '给每一路推一条状态帧'
        for 跟随者 in list(自身.跟随者):#拷贝，推入时可能关掉某一路
            跟随者.推入({'type':'state','info':自身.info,'writable':自身._可写(跟随者)})#状态

    def _要求控制(自身,跟随者):
        '未运行或输入在另一路时拒绝，不拆掉输出附着'
        if 自身._已退出 or 自身._关闭任务 is not None or 自身.info['state']!='running':#进程不在跑
            raise 远程错误('terminal/control-unavailable','Terminal is not running',{'reason':'not-running'})#拒绝
        if 自身._控制 is not 跟随者 or not 跟随者.仍活动:#输入在别处
            raise 远程错误('terminal/control-unavailable','Terminal input is controlled by another attachment',{'reason':'read-only'})#拒绝

    def _广播(自身,帧):
        '把一帧推进每一路跟随者'
        for 跟随者 in list(自身.跟随者):#拷贝
            跟随者.推入(帧)#排队

    def _排入(自身,操作):
        '串行执行。这一次的失败由调用方收下，后面的清理仍能跑'
        with 自身._操作锁:#一次一项
            return 操作()#执行

    def _关闭进程(自身):
        '终止进程并排空输出。失败则清掉任务，允许再试'
        已有=自身._关闭任务#进行中或已成功
        if 已有 is not None:#已经开始
            已有.wait()#加入
            if 已有.错误 is not None:#那一次失败了
                raise 已有.错误#交给调用方
            return#成功
        完成=事件()#这一次
        完成.错误=None#失败写在这一次上
        自身._关闭任务=完成#可写立刻变成假
        try:#终止、排空、完结跟随者、放开屏幕
            等到结果(自身.句柄.终止())#进程范围
            自身._排空.wait()#等输出消费结束
            for 跟随者 in list(自身.跟随者):#每一路
                跟随者.完结()#把已排队的帧交完
            自身.跟随者.clear()#不再广播
            自身.屏幕.dispose()#放开仿真
        except BaseException as 错误:#可以再试
            完成.错误=错误#加入者看见
            自身._关闭任务=None#允许再关
            完成.set()#放开
            raise#原样
        完成.set()#成功

    def _消费输出(自身):
        '按投递顺序解码。进程结束后再发布退出或失败'
        解码器=codecs.getincrementaldecoder('utf-8-sig')('replace')#忽略 BOM，坏字节替换
        队列=deque()#尚未解码的块
        条件=条件变量()#数据或结束
        结束了={'值':False}#输出流结束
        结局={'完成':事件(),'值':None,'错误':None,'好':False}#done 的结果

        def 成功(值=None):
            '提供方完成。退出标志先于排空和发布'
            自身._已退出=True#先记下
            结局['值']=值#退出事实
            结局['好']=True#兑现
            结局['完成'].set()#放开

        def 失败结局(错误=None):
            'done 拒绝。先排空再走失败'
            结局['错误']=错误#原因
            结局['完成'].set()#放开

        自身.句柄.done.然后(成功,失败结局)#不等排空就订阅

        def 在数据(块):
            '收下一块输出'
            if isinstance(块,str):#文本
                块=块.encode('utf-8')#按字节解码
            with 条件:#入队
                队列.append(块)#顺序
                条件.notify()#唤醒

        def 在结束(*位置参数):
            '用户可见输出结束'
            with 条件:#标记
                结束了['值']=True#结束
                条件.notify()#唤醒

        自身.句柄.输出.监听('data',在数据)#按投递
        自身.句柄.输出.一次('end',在结束)#排空已排队输出后结束
        try:#解码、收尾、等退出事实
            while True:#直到输出结束
                with 条件:#取一块
                    while len(队列)==0 and not 结束了['值']:#还没有
                        条件.wait()#等数据或结束
                    if len(队列)==0 and 结束了['值']:#已结束
                        break#去刷尾
                    块=队列.popleft()#一块
                自身._写出屏幕(解码器.decode(块))#流式解码
            自身._写出屏幕(解码器.decode(b'',True))#刷出尾部
            结局['完成'].wait()#等 done
            if not 结局['好']:#done 拒绝
                if isinstance(结局['错误'],BaseException):#异常
                    raise 结局['错误']#进入失败发布
                raise RuntimeError(str(结局['错误']))#收成异常
            自身.info={**自身.info,'state':'exited','exitCode':结局['值']['exitCode']}#发布退出
        except BaseException as 错误:#输出或退出失败
            自身.info={**自身.info,'state':'failed','error':str(错误)}#发布失败
        自身._广播状态()#最后一条状态
        自身._排空.set()#关闭进程可以继续

    def _写出屏幕(自身,数据):
        '空串跳过。等仿真解析完再广播这一段输出'
        if len(数据)==0:#没有新文本
            return#跳过

        def 写入():
            '等 write 的回调，再广播'
            写完=事件()#仿真解析完

            def 回调():
                '解析完成'
                写完.set()#放开

            自身.屏幕.write(数据,回调)#写入仿真
            写完.wait()#等解析
            自身.序号+=1#输出序号
            自身._广播({'type':'output','sequence':自身.序号,'data':数据})#有序输出

        自身._排入(写入)#与输入串行

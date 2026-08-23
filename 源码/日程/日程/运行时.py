"""一个精确根智能体的可拆除在线计时器投影。"""
import threading,time#计时器与墙钟
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定
from ..llm import 创建用户消息#用户消息构造
from .领域 import (
    折叠日程事件,#折叠事件流
    渲染固定频率提醒批次成帧,#渲染固定频率批次
    渲染提醒成帧,#渲染一次性提醒框
    解析固定频率出现,#解析固定频率出现
    日程日志错误,#日志错误
    解析纪元毫秒,#纪元解析
    纪元转规范UTC,#UTC 格式化
)#domain 导入
from .持久化 import 冲洗日程持久#导入持久屏障
from .事务 import 跑日程事务#导入串行事务

计时器延迟上限毫秒=2147483647#Node 计时器在不钳位下能表示的最大延迟
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 到期决定(折叠,现在):#选出一条到期一次性、一批完整固定频率，或下一次唤醒
    """选出一条到期一次性、一批完整固定频率，或下一次唤醒。"""
    带序=[]#带创建顺序索引
    下标=0#索引
    for 记录 in 折叠['active']:#逐条
        带序.append({'record':记录,'index':下标})#带序
        下标+=1#前进
    一次性们=[]#一次性候选
    for 项 in 带序:#筛选
        记录=项['record']#记录
        if 记录['kind']!='every' and 解析纪元毫秒(记录['scheduledAt'])<=现在:#非 every 且已到期
            一次性们.append(项)#收入
    一次性们.sort(key=lambda 项:(解析纪元毫秒(项['record']['scheduledAt']),项['index']))#排序
    if len(一次性们)>0:#有到期一次性
        return {'kind':'one-shot','record':一次性们[0]['record']}#优先一次性
    固定们=[]#固定频率候选
    for 项 in 带序:#筛选
        记录=项['record']#记录
        if 记录['kind']=='every' and 解析纪元毫秒(记录['scheduledAt'])<=现在:#every 且已到期
            固定们.append(项)#收入
    固定们.sort(key=lambda 项:(解析纪元毫秒(项['record']['scheduledAt']),项['index']))#按目标再创建序
    if len(固定们)>0:#有到期固定频率
        提醒们=[]#一批最新出现
        for 项 in 固定们:#逐条
            记录=项['record']#活动记录
            提醒们.append({'record':记录,'occurrenceAt':解析固定频率出现(记录,现在)['occurrenceAt']})#最新到期出现
        return {'kind':'every','acceptedAt':纪元转规范UTC(现在),'reminders':提醒们}#批次
    目标=None#最早未来目标
    for 记录 in 折叠['active']:#找最早未来
        候选=解析纪元毫秒(记录['scheduledAt'])#该记录目标
        if 候选>现在 and (目标 is None or 候选<目标):#更早的未来
            目标=候选#更新
    决定={'kind':'wait'}#等待
    if 目标 is not None:#有目标
        决定['target']=目标#带目标
    return 决定#等待或空闲

def 渲染抛出(值):#仅为进程内诊断渲染未知抛出值
    """仅为进程内诊断渲染未知抛出值。"""
    if isinstance(值,Exception):#异常
        return str(值)#消息
    return str(值)#其它

class 日程运行时:#日程运行时
    """一个精确智能体持久日程的进程局部、可拆除投影。"""
    def __init__(自身,上下文,智能体):#构造未激活运行时
        """构造未激活运行时；启动 开始第一次预检。"""
        自身.上下文=上下文#全局上下文
        自身.智能体=智能体#所属根智能体
        自身.停止事件=threading.Event()#拆除时解开
        自身.计时器=None#当前武装的计时器
        自身.空闲等待=None#等待空闲的线程
        自身.运行=None#当前驱动循环线程
        自身.已请求=False#是否有合并中的驱动请求
        自身.停止中=False#是否正在拆除
        自身.已故障=False#是否已永久故障
        自身.拆除中=None#拆除锁去重
        自身.拆除锁=threading.Lock()#拆除互斥

    def 启动(自身):#开始最初的耐久预检与计时器派生
        """开始最初的耐久预检与计时器派生。"""
        自身.请求驱动()#请求第一次驱动

    def 请求驱动(自身):#在已提交变更或空闲转移后重算在线投影
        """在已提交变更或空闲转移后重算在线投影。"""
        if 自身.停止中 or 自身.已故障:#拆除或故障则忽略
            return#停
        自身.清计时器()#取消当前计时器
        自身.已请求=True#记下合并请求
        if 自身.运行 is not None:#已有循环则只合并
            return#合并
        def 循环体():#新循环
            """跑合并循环。"""
            try:#在无发起方作用域启动
                def 跑():#循环入口
                    """跑合并请求。"""
                    自身.跑合并请求()#串行排空
                结果=自身.上下文.agents.withoutInitiator(跑)#无发起方
                解开(结果)#若可等待则等
            except Exception as 错误:#循环失败
                if 自身.仍权威():#仍是权威所有者
                    自身.上下文.logger.warn('schedule: runtime failed for agent "'+str(取字段(自身.智能体,'id'))+'": '+渲染抛出(错误))#记警告
                自身.已故障=True#永久故障
            finally:#退休该循环
                自身.退休(线程)#退休
        try:#启动线程
            线程=threading.Thread(target=循环体,daemon=True)#后台循环
            自身.运行=线程#记下当前循环
            线程.start()#启动
        except Exception as 错误:#同步启动失败
            if 自身.仍权威():#仍是权威所有者
                自身.上下文.logger.warn('schedule: could not start runtime for agent "'+str(取字段(自身.智能体,'id'))+'": '+渲染抛出(错误))#记警告
            自身.运行=None#清空

    def 拆除(自身):#停止未来工作、取消计时器，并等待每一个未完成的运行时承诺
        """停止未来工作、取消计时器，并等待每一个未完成的运行时承诺。"""
        with 自身.拆除锁:#去重拆除
            if 自身.拆除中:#已在拆
                return#停
            自身.拆除中=True#标记
        自身.停止中=True#标记停止
        自身.已请求=False#丢掉合并请求
        自身.清计时器()#取消计时器
        自身.停止事件.set()#解开空闲等待
        待等=[]#在途线程
        if 自身.运行 is not None:#有循环
            待等.append(自身.运行)#收入
        if 自身.空闲等待 is not None:#有空闲等待
            待等.append(自身.空闲等待)#收入
        for 线程 in 待等:#等全部停稳
            线程.join(timeout=30)#有界等待

    def 跑合并请求(自身):#串行排空合并触发
        """串行排空合并触发。"""
        while 自身.已请求 and (not 自身.停止中) and (not 自身.已故障):#还有请求且可跑
            自身.已请求=False#吃掉当前请求
            跑日程事务(自身.智能体,自身.驱动一轮)#独占跑一轮

    def 退休(自身,线程):#退休一次精确运行，并兑现其最后微任务里落到的触发
        """退休一次精确运行，并兑现其最后空隙里落到的触发。"""
        if 自身.运行 is not 线程:#不是当前循环则忽略
            return#停
        自身.运行=None#清空循环槽
        if 自身.已请求 and (not 自身.停止中) and (not 自身.已故障):#结算空隙里的请求
            自身.请求驱动()#再驱

    def 仍权威(自身):#此精确根生命周期是否仍权威
        """此精确根生命周期是否仍权威。"""
        标识=取字段(自身.智能体,'id')#智能体 id
        return 自身.上下文.agents.get(标识) is 自身.智能体 and 自身.智能体 in 自身.上下文.agents.roots()#仍指向且仍是根

    def 可跑(自身):#此运行时是否可以开始或继续日程工作
        """此运行时是否可以开始或继续日程工作。"""
        return (not 自身.停止中) and 自身.仍权威()#未拆除且仍权威

    def 清计时器(自身):#取消当前已武装的计时器（若有）
        """取消当前已武装的计时器（若有）。"""
        if 自身.计时器 is None:#没有计时器
            return#停
        自身.计时器.cancel()#取消
        自身.计时器=None#清空槽

    def 武装(自身,目标,现在):#武装一段有界计时器；每次唤醒都重查墙钟
        """武装一段有界计时器；每次唤醒都重查墙钟。"""
        延迟=min(目标-现在,计时器延迟上限毫秒)/1000#钳位延迟（秒）
        def 到期():#到期回调
            """到期后重算投影。"""
            自身.计时器=None#清空槽
            自身.请求驱动()#重算投影
        自身.计时器=threading.Timer(max(0,延迟),到期)#武装
        自身.计时器.daemon=True#守护
        自身.计时器.start()#启动

    def 等待空闲(自身):#等待一个公开空闲边界，不占准入也不创建重试计时器
        """等待一个公开空闲边界，不占准入也不创建重试计时器。"""
        if 自身.空闲等待 is not None:#已在等
            return#停
        def 干活():#空闲或拆除
            """等待空闲后再驱。"""
            try:#空闲或拆除
                while not 自身.停止事件.is_set():#未拆除
                    try:#尝试空闲
                        解开(自身.智能体.whenIdle())#等空闲
                        break#已空闲
                    except Exception as 错误:#等待失败
                        if 自身.仍权威():#仍权威
                            自身.上下文.logger.warn('schedule: idle wait failed for agent "'+str(取字段(自身.智能体,'id'))+'": '+渲染抛出(错误))#记警告
                        break#停等
            finally:#清空槽
                自身.空闲等待=None#清空
                自身.请求驱动()#再驱
        线程=threading.Thread(target=干活,daemon=True)#后台等待
        自身.空闲等待=线程#记下
        线程.start()#启动

    def 读折叠(自身):#折叠当前精确运行时后缀，并把损坏的持久流关在里面
        """折叠当前精确运行时后缀，并把损坏的持久流关在里面。"""
        try:#折叠当前日志
            会话=取字段(自身.智能体,'session')#会话
            头=取字段(会话,'header')#头
            种子=取字段(头,'seedLength',0) or 0#fork 后缀起点
            return 折叠日程事件(取字段(会话,'events'),种子)#折叠
        except Exception as 错误:#折叠失败
            自身.已故障=True#永久故障
            细节=str(错误) if isinstance(错误,日程日志错误) else 渲染抛出(错误)#诊断细节
            自身.上下文.logger.warn('schedule: corrupt schedule log for agent "'+str(取字段(自身.智能体,'id'))+'": '+细节)#记警告
            return None#无法继续

    def 安全决定(自身,折叠,现在):#把非法墙钟决定关在里面，不永久故障此运行时
        """把非法墙钟决定关在里面，不永久故障此运行时。"""
        try:#派生决定
            return 到期决定(折叠,现在)#按折叠态决定
        except Exception as 错误:#决定失败
            自身.上下文.logger.warn('schedule: fixed-rate decision failed for agent "'+str(取字段(自身.智能体,'id'))+'": '+渲染抛出(错误))#记警告
            return None#本轮放弃

    def 驱动一轮(自身):#预检、折叠、武装，或派发下一条一次性或固定频率批次
        """预检、折叠、武装，或派发下一条一次性或固定频率批次。"""
        自身.清计时器()#先清计时器
        if not 自身.可跑():#不可跑则停
            return#停
        try:#预检持久屏障
            冲洗日程持久(自身.上下文,取字段(自身.智能体,'session'))#flush 当前前缀
        except Exception as 错误:#预检失败
            if 自身.仍权威():#仍权威
                自身.上下文.logger.warn('schedule: preflight failed for agent "'+str(取字段(自身.智能体,'id'))+'": '+渲染抛出(错误))#记警告
            return#本轮放弃
        if not 自身.可跑():#flush 期间可能拆除
            return#停
        折叠=自身.读折叠()#折叠当前流
        if 折叠 is None:#损坏则停
            return#停
        唤醒现在=int(time.time()*1000)#唤醒墙钟
        唤醒决定=自身.安全决定(折叠,唤醒现在)#决定下一步
        if 唤醒决定 is None:#决定失败
            return#停
        if 唤醒决定['kind']=='wait':#无需派发
            if 唤醒决定.get('target') is not None:#有目标
                自身.武装(唤醒决定['target'],唤醒现在)#武装下次
            return#等待
        def 维护体():#维护体内派发
            """在空闲相位认领维护。"""
            if not 自身.可跑():#已不可跑
                return False#未派发
            认领=自身.读折叠()#认领后再折叠
            if 认领 is None:#损坏
                return False#未派发
            决定现在=int(time.time()*1000)#决定墙钟
            决定=自身.安全决定(认领,决定现在)#再决定
            if 决定 is None:#决定失败
                return False#未派发
            if 决定['kind']=='wait':#已不再到期
                if 决定.get('target') is not None:#有目标
                    自身.武装(决定['target'],决定现在)#改武装
                return False#未派发
            try:#组装并投递提醒
                if 决定['kind']=='one-shot':#一次性
                    文本=渲染提醒成帧(决定['record'])#一次性框
                else:#批次
                    文本=渲染固定频率提醒批次成帧(决定['reminders'])#批次框
                消息=创建用户消息({#插件来源消息
                    'content':[{'type':'text','text':文本}],#提醒正文
                    'source':{'kind':'plugin','plugin':'schedule'},#日程插件源
                })#结束
                解开(自身.智能体.followup(消息))#投递 followup
            except Exception as 错误:#成帧或投递失败
                if 自身.仍权威():#仍权威
                    自身.上下文.logger.warn('schedule: framing or followup failed for agent "'+str(取字段(自身.智能体,'id'))+'": '+渲染抛出(错误))#记警告
                return False#未派发
            try:#追加派发变更
                会话=取字段(自身.智能体,'session')#会话
                if 决定['kind']=='one-shot':#一次性
                    解开(会话.append('schedule/change',{'version':1,'operation':'dispatch','id':决定['record']['id']}))#追加派发
                else:#固定频率批次
                    for 提醒 in 决定['reminders']:#逐条追加
                        解开(会话.append('schedule/change',{'version':1,'operation':'dispatch','id':提醒['record']['id'],'acceptedAt':决定['acceptedAt']}))#追加派发
            except Exception as 错误:#追加失败
                自身.已故障=True#永久故障
                自身.清计时器()#清计时器
                自身.上下文.logger.warn('schedule: dispatch append failed for agent "'+str(取字段(自身.智能体,'id'))+'": '+渲染抛出(错误))#记警告
                return False#未成功
            return True#已派发
        try:#在空闲相位认领维护
            维护=解开(自身.智能体.runMaintenance(维护体))#维护回合
        except Exception:#空闲相位被占
            if 自身.仍权威():#仍权威
                自身.等待空闲()#等空闲再试
            return#本轮放弃
        if not 维护:#未派发则停
            return#停
        try:#派发后耐久屏障
            冲洗日程持久(自身.上下文,取字段(自身.智能体,'session'))#flush 派发事件
        except Exception as 错误:#屏障失败
            if 自身.仍权威():#仍权威
                自身.上下文.logger.warn('schedule: dispatch barrier failed for agent "'+str(取字段(自身.智能体,'id'))+'": '+渲染抛出(错误))#记警告
            return#本轮结束
        if 自身.可跑():#继续下一轮
            自身.请求驱动()#再驱

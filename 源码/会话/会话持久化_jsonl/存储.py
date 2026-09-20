"""JSONL 提供方的会话存储运行时：写句柄变更链、活事件路由与后端跟踪器。"""
import threading#批定时器与链
from ...模型后端.llm import 结构化克隆,错误链#深拷贝与错误链
from ..会话持久化.修订 import 会话持久化修订#修订品牌
from ..会话持久化.存储契约 import 物化追加批,断言连续#存储契约
from ..会话持久化.句柄 import (#句柄错误
    会话已存在错误,#已存在
    会话已有写主错误,#已有写主
    会话只读错误,#只读
    会话句柄已关闭错误,#已关闭
    会话持久化未找到错误,#未找到
)#句柄面

活写批最大延迟毫秒=200#活写批最大延迟

class jsonl会话句柄:#JSONL 会话句柄
    """变更在每句柄链上串行；路由活事件有界缓冲并经与显式追加相同的链排空。"""
    def __init__(自身,存储,标识,头,访问,状态,租约=None):#构造
        """记下存储面、身份、访问、可变状态与可选租约。"""
        自身._存储=存储#存储面
        自身.id=标识#会话 id
        自身.header=头#头
        自身.access=访问#访问
        自身._状态=状态#可变状态
        自身._租约=租约#可选租约
        自身._链=[]#串行锁用事件
        自身._链锁=threading.Lock()#链锁
        自身._关闭中=None#关闭承诺标记
        自身._已观察长度=0#已观察长度
        自身._缓冲=[]#活写缓冲
        自身._批定时器=None#批定时器
        自身._排空暂停=False#排空暂停
        自身._排空中=None#单飞排空

    @property
    def inheritedEventCount(自身):#继承事件数
        """与日志一并存储的精确 fork 继承前缀长度。"""
        return 自身._状态['inheritedEventCount']#状态

    def 读(自身,偏移=0,长度=None,选项=None):#读取
        """读取合法连续逻辑日志的一段。"""
        自身._断言打开('read')#已关闭拒绝
        if not isinstance(偏移,int) or isinstance(偏移,bool) or 偏移<0:#偏移非法
            raise TypeError(f'read offset must be a non-negative safe integer, got {偏移}')#类型错误
        if 长度 is None:#默认
            长度=9007199254740991#剩余全部
        if not isinstance(长度,int) or isinstance(长度,bool) or 长度<0:#长度非法
            raise TypeError(f'read length must be a non-negative safe integer, got {长度}')#类型错误
        信号=选项.get('signal') if 选项 else None#取消
        _若已中止(信号)#取消
        预热=自身._状态.get('primed')#预热
        if 预热 is not None:#有预热
            if 自身.access=='write':#写句柄
                结果=自身._读预热(预热,偏移,长度)#切片
            else:#读句柄
                当代路径=自身._存储.解析当代日志(自身.id,信号)#解析当代
                if 当代路径 is None:#尚无当代
                    结果=自身._读预热(预热,偏移,长度)#仍用预热
                else:#当代已发布
                    自身._状态['primed']=None#丢弃预热
                    结果=自身._读当代(当代路径,偏移,长度,信号)#读当代
        elif 自身.access=='write' and not 自身._状态['materialized']:#未物化写
            结果={'eventState':'detached','events':[]}#空
        else:#从存储读
            当代路径=自身._存储.解析当代日志(自身.id,信号)#解析
            if 当代路径 is not None:#有当代
                结果=自身._读当代(当代路径,偏移,长度,信号)#读
            elif 自身._存储.有挂起会话(自身.id):#挂起
                结果={'eventState':'detached','events':[]}#空
            else:#未找到
                raise 会话持久化未找到错误(自身.id)#未找到
        return 结果#返回

    def _读预热(自身,源,偏移,长度):#读预热
        """从本句柄保留的已准备历史前缀读取。"""
        自身._已观察长度=max(自身._已观察长度,len(源['events']))#观察
        return {'eventState':源['eventState'],'events':源['events'][偏移:偏移+长度]}#切片

    def _读当代(自身,路径,偏移,长度,信号=None):#读当代
        """读当代物理代并强制单调视图。"""
        源=自身._存储.读已存日志(路径,自身.id,信号)#读
        if len(源['events'])<自身._已观察长度:#缩短
            raise RuntimeError(f'session "{自身.id}": stored log shrank below a previously observed prefix ({len(源["events"])} < {自身._已观察长度})')#错误
        自身._已观察长度=len(源['events'])#更新
        return {'eventState':源['eventState'],'events':源['events'][偏移:偏移+长度]}#切片

    def 追加(自身,事件列表,选项=None):#追加
        """耐久追加连续批次。"""
        自身._断言打开('append')#断言
        批次=物化追加批(事件列表)#物化
        信号=选项.get('signal') if 选项 else None#取消
        def 链上追加():#链上操作
            """持久化连续批。"""
            _若已中止(信号)#取消
            自身._持久化连续(批次)#持久化
        return 自身._运行('append',链上追加)#串入链

    def 刷盘(自身,选项=None):#刷盘
        """耐久屏障；尚未追加时物化仅头产物。"""
        信号=选项.get('signal') if 选项 else None#取消
        def 链上刷盘():#链上
            """刷盘实现。"""
            _若已中止(信号)#取消
            if 自身.access!='write':#读句柄
                raise 会话只读错误(自身.id,'flush')#拒绝
            if 自身._状态['materialized']:#已物化
                return#空操作
            自身._确保租约()#租约
            自身._存储.持久化头(自身.header,自身._状态['inheritedEventCount'])#仅头
            自身._状态['materialized']=True#标记
        return 自身._运行('flush',链上刷盘)#串入链

    def 关闭(自身):#关闭
        """释放句柄；写句柄先排空活缓冲。幂等。"""
        if 自身._关闭中 is not None:#已关闭中
            return 自身._关闭中#返回
        完成=threading.Event()#完成事件
        失败槽=[None]
        def 执行关闭():#关闭体
            """排空、释租、释放簿记。"""
            排空失败=None#排空失败
            try:#排空循环
                while True:#直至缓冲空
                    try:#排空
                        自身.排空活写()#排空
                    except BaseException as 错误:
                        排空失败=错误#记录
                        break#退出
                    #等链：本实现同步链，无需额外等待
                    if len(自身._缓冲)==0:#空
                        break
            finally:#释放
                失败列表=[]
                if 排空失败 is not None:#有排空失败
                    失败列表.append(排空失败 if isinstance(排空失败,Exception) else Exception(错误链(排空失败)))#规范化
                try:#释租
                    if 自身._租约 is not None:#有租约
                        自身._租约.释放()#释放
                except BaseException as 释错:
                    失败列表.append(释错 if isinstance(释错,Exception) else Exception(错误链(释错)))#规范化
                自身._存储.释放句柄(自身,自身._状态['materialized'])#簿记
                if len(失败列表)>1:#多失败
                    失败槽[0]=ExceptionGroup(f'session "{自身.id}": close failed to drain and to release its write lock',失败列表)#聚合
                elif len(失败列表)==1:#单失败
                    失败槽[0]=失败列表[0]#单
                完成.set()#完成
        自身._关闭中=完成#标记关闭中
        执行关闭()#同步关闭（Python 端口）
        if 失败槽[0] is not None:#有失败
            raise 失败槽[0]#抛出

    def 入队活写(自身,事件,报告后台失败):#入队活事件
        """缓冲一条已发布活会话事件，并武装有界批窗口。"""
        自身._缓冲.append(结构化克隆(事件))#深拷贝入缓冲
        if 自身._批定时器 is not None or 自身._排空暂停:#已有定时器或暂停
            return#返回
        def 到期():#批到期
            """排空并报告失败。"""
            自身._批定时器=None#清引用
            try:#排空
                自身.排空活写()#排空
            except BaseException as 错误:
                报告后台失败(错误)#报告
        自身._批定时器=threading.Timer(活写批最大延迟毫秒/1000,到期)#定时器
        自身._批定时器.daemon=True#守护
        自身._批定时器.start()

    def 排空活写(自身):#排空活缓冲
        """经变更链耐久排空路由活缓冲。"""
        if 自身._排空中 is not None:#单飞
            自身._排空中.wait()#加入
            return
        事件=threading.Event()#本轮
        自身._排空中=事件#记下
        失败=None
        try:#排空
            自身._排空缓冲()#实现
        except BaseException as 错误:
            失败=错误#记录
        finally:#清引用
            自身._排空中=None#清空
            事件.set()#唤醒等待者
        if 失败 is not None:#有失败
            raise 失败#抛出

    def _排空缓冲(自身):#排空缓冲实现
        """取出缓冲并持久化。"""
        if 自身._批定时器 is not None:#有定时器
            自身._批定时器.cancel()#清除
            自身._批定时器=None#清引用
        自身._排空暂停=False#恢复
        while len(自身._缓冲)>0:#非空
            def 链上排空():#链上
                """持久化一批活事件。"""
                批次=自身._缓冲[:]#取出
                自身._缓冲.clear()#清空
                try:#持久化
                    自身._持久化连续(物化追加批(批次))#物化并持久化
                except BaseException:
                    自身._缓冲=批次+自身._缓冲#按序放回
                    自身._排空暂停=True#暂停
                    raise#抛出
            自身._入队链(链上排空)#串入链

    def _持久化连续(自身,批次):#持久化连续批
        """连续性、租约、撕裂尾修复、存储写、状态推进。"""
        if 自身.access!='write':#读句柄
            raise 会话只读错误(自身.id,'append')#拒绝
        if len(批次)==0:#空
            return#返回
        自身._确保租约()#租约
        断言连续(自身.id,批次,自身._状态['cursor'])#连续
        if 自身._状态.get('tornTruncateTo') is not None:#有截断
            自身._存储.截断撕裂尾(自身.header,自身._状态['tornTruncateTo'])#截断
            自身._状态['tornTruncateTo']=None
        if 自身._状态.get('recoveredTail') is not None:#有恢复尾
            尾=自身._状态['recoveredTail']#尾
            if len(尾)>0:#非空
                自身._存储.持久化批次(自身.header,尾,自身._状态['materialized'],自身._状态['inheritedEventCount'])#写尾
            自身._状态['recoveredTail']=None
        自身._存储.持久化批次(自身.header,批次,自身._状态['materialized'],自身._状态['inheritedEventCount'])#写批
        自身._状态['materialized']=True#已物化
        自身._状态['cursor']+=len(批次)#推进
        自身._状态['primed']=None#清预热
        自身._已观察长度=自身._状态['cursor']#观察

    def _确保租约(自身):#确保租约
        """首次耐久写前持有跨进程写锁。"""
        if 自身._租约 is None:#惰性
            自身._租约=自身._存储.取得写租约(自身.header)#取得

    def _入队链(自身,操作):#入队链
        """串到句柄链（同步实现）。"""
        with 自身._链锁:#串行
            操作()#执行

    def _运行(自身,操作名,操作):#运行变更
        """公开变更操作。"""
        自身._断言打开(操作名)#入队前
        def 包():#包一层
            """执行前再断言。"""
            自身._断言打开(操作名)#再断言
            操作()#执行
        自身._入队链(包)#串入

    def _断言打开(自身,操作):#断言未关闭
        """已关闭拒绝。"""
        if 自身._关闭中 is not None:#关闭中
            raise 会话句柄已关闭错误(自身.id,操作)#拒绝

class jsonl后端跟踪器:#JSONL 后端跟踪器
    """每会话 id 单一活跃写者、挂起未物化会话与拆卸清扫。"""
    def __init__(自身,名):#构造
        """记下后端标签。"""
        自身.name=名#名
        自身.打开句柄=set()#打开集
        自身._写者={}#id -> 句柄|None
        自身._挂起={}#id -> 挂起
        自身._计数=0#修订计数

    def 登记已创建(自身,头,继承事件数):#登记已创建
        """声明写所有权并记录挂起未物化会话。"""
        if 头['id'] in 自身._写者:#已有
            raise 会话已存在错误(头['id'])#拒绝
        自身._写者[头['id']]=None#占位
        自身._计数+=1#递增
        自身._挂起[头['id']]={#挂起
            'header':头,#头
            'revision':会话持久化修订(f'memory:{自身.name}:{自身._计数}'),#内存修订
            'inheritedEventCount':继承事件数,#继承
        }#结束

    def 声明写(自身,标识):#声明写
        """为已有会话声明写所有权。"""
        if 标识 in 自身._写者:#已有
            raise 会话已有写主错误(标识)#拒绝
        自身._写者[标识]=None#占位

    def 释放声明(自身,标识):#释放声明
        """回滚失败的写打开。"""
        自身._写者.pop(标识,None)#删除

    def 挂起项(自身,标识):#取挂起
        """已创建但未物化会话的挂起条目。"""
        return 自身._挂起.get(标识)#查

    def 有挂起(自身,标识):#是否挂起
        """本进程是否仍跟踪挂起会话。"""
        return 标识 in 自身._挂起#查

    def 挂起条目(自身):#挂起迭代
        """迭代挂起会话。"""
        return 自身._挂起.items()#条目

    def 已物化(自身,标识):#已物化
        """耐久物化后丢弃挂起。"""
        自身._挂起.pop(标识,None)#删

    def 收养(自身,句柄):#收养句柄
        """跟踪打开句柄；写句柄绑定为活事件路由。"""
        自身.打开句柄.add(句柄)#加入
        if 句柄.access=='write':#写
            自身._写者[句柄.id]=句柄#绑定
        return 句柄#返回

    def 释放(自身,句柄,已物化):#释放句柄
        """关闭时释放簿记。"""
        自身.打开句柄.discard(句柄)#删除
        if 句柄.access!='write':#读
            return
        自身._写者.pop(句柄.id,None)#删写者
        if not 已物化:#从未物化
            自身._挂起.pop(句柄.id,None)#清挂起

    def 刷全部(自身):#刷全部
        """排空并刷每个活跃写句柄。"""
        错误列表=[]#错误
        for 写者 in list(自身._写者.values()):#快照
            if 写者 is None:#构造中
                continue#跳过
            try:#刷
                写者.排空活写()#排空
                写者.刷盘()#刷盘
            except 会话句柄已关闭错误:#已关闭
                continue#跳过
            except BaseException as 错误:
                错误列表.append(错误)#记录
        if len(错误列表)>0:#有失败
            raise ExceptionGroup(f'{自身.name} flush failed',错误列表)#聚合

    def 写者(自身,标识):#取写者
        """返回会话的活跃写句柄（若有）。"""
        return 自身._写者.get(标识)#查

    def 安装(自身,上下文):#安装路由与拆卸
        """安装活会话路由与拆卸（与协调器二选一时慎用，以免双写）。"""
        def 会话事件(会话,事件):#事件
            """入队活写。"""
            if 会话.id not in 自身._写者:#无
                return#忽略
            写者=自身._写者[会话.id]#写者
            写者.入队活写(事件,lambda 错误:上下文.日志.警告(
                f'session-persistence: background write for session "{会话.id}" failed (buffered events retained): {错误}'
            ))#入队
        上下文.监听('session/event',会话事件)#监听
        def 会话刷盘(会话):#刷盘
            """排空并刷。"""
            if 会话.id not in 自身._写者:#无
                return None#无
            写者=自身._写者[会话.id]#写者
            写者.排空活写()#排空
            写者.刷盘()#刷
            return None
        上下文.监听('session/flush',会话刷盘)#监听
        def 会话已拆除(会话):#拆除
            """关闭写句柄。"""
            if 会话.id not in 自身._写者:#无
                return#忽略
            写者=自身._写者[会话.id]#写者
            try:#关闭
                写者.关闭()#关闭
            except BaseException as 错误:
                上下文.日志.警告(f'session-persistence: final drain for session "{会话.id}" failed: {错误}')#警告
        上下文.监听('session/disposed',会话已拆除)#监听

def _若已中止(信号):#取消检查
    """已中止则抛。"""
    if 信号 is None:#无
        return#无事
    if 信号.is_set():#已中止
        raise InterruptedError('aborted')#包装

__all__=[#公开面
    '活写批最大延迟毫秒','jsonl会话句柄','jsonl后端跟踪器',
]#公开面结束

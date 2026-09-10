"""每会话存储句柄：通向已存会话仅追加事件日志的一条打开通道。"""
import math#安全整数
from .预备 import 持久化错误#包异常基类

安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER
会话访问=('read','write')#会话访问模式
会话句柄读结果字段=('eventState','events')#读取结果：别名状态加事件切片
会话句柄追加选项字段=('signal',)#追加选项
会话句柄刷盘选项字段=('signal',)#刷盘选项
会话句柄读选项字段=('signal',)#读取选项

__all__=[#公开面
    '会话访问','会话句柄读结果字段','会话句柄追加选项字段','会话句柄刷盘选项字段','会话句柄读选项字段',
    '会话持久化未找到错误','会话已存在错误','会话已有写主错误','会话只读错误',
    '会话所有权丢失错误','会话句柄已关闭错误','会话句柄',
]#公开面结束

def 外来安全整数(值):#外来 JSON 安全整数
    """外来入口的安全整数校验，排除布尔。"""
    if isinstance(值,bool):#布尔不是整数
        return False#拒绝
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#安全范围
    if isinstance(值,float) and math.isfinite(值) and 值==int(值):#整值浮点
        return abs(值)<=安全整数上限#安全范围
    return False#其它类型

class 会话持久化未找到错误(持久化错误):#未找到
    """请求的已存会话不存在。"""
    def __init__(自身,标识):#构造
        """记下缺失身份。"""
        自身.id=标识#会话 id
        super().__init__('session "'+str(标识)+'" not found')#文案
        自身.name='SessionPersistenceNotFoundError'#固定错误名

class 会话已存在错误(持久化错误):#已存在
    """创建时会话 id 已存在。"""
    def __init__(自身,标识):#构造
        """记下冲突身份。"""
        自身.id=标识#会话 id
        super().__init__('session "'+str(标识)+'" already exists')#文案
        自身.name='SessionAlreadyExistsError'#固定错误名

class 会话已有写主错误(持久化错误):#已有写主
    """写打开时所有权已被占用。"""
    def __init__(自身,标识):#构造
        """记下被争用的会话身份。"""
        自身.id=标识#会话 id
        super().__init__('session "'+str(标识)+'" is already owned by another writer')#文案
        自身.name='SessionAlreadyOwnedError'#固定错误名

class 会话只读错误(持久化错误):#只读
    """读句柄上拒绝变更操作。"""
    def __init__(自身,标识,操作):#构造
        """记下会话与被拒操作。"""
        自身.id=标识#会话 id
        自身.操作=操作#操作名
        super().__init__('session "'+str(标识)+'" handle is read-only; cannot '+str(操作))#文案
        自身.name='SessionReadOnlyError'#固定错误名

class 会话所有权丢失错误(持久化错误):#所有权丢失
    """写所有权在句柄生命周期内丢失。"""
    def __init__(自身,标识):#构造
        """记下丢失所有权的会话。"""
        自身.id=标识#会话 id
        super().__init__('session "'+str(标识)+'" write ownership was lost')#文案
        自身.name='SessionOwnershipLostError'#固定错误名

class 会话句柄已关闭错误(持久化错误):#已关闭
    """已关闭句柄上的操作。"""
    def __init__(自身,标识,操作):#构造
        """记下会话与被拒操作。"""
        自身.id=标识#会话 id
        自身.操作=操作#操作名
        super().__init__('session "'+str(标识)+'" handle is closed; cannot '+str(操作))#文案
        自身.name='SessionHandleClosedError'#固定错误名

class 会话句柄:#会话句柄
    """通向已存会话的一条打开通道；读不回退到已观察点之下，写句柄能读到自己成功追加。"""
    def __init__(自身,标识,头,访问,继承事件数,后端):#构造
        """记下身份、头、访问模式、继承切点与后端回调。"""
        自身.id=标识#会话 id
        自身.header=头#不可变已存头
        自身.access=访问#访问模式
        自身.inheritedEventCount=继承事件数#继承事件数
        自身._后端=后端#读/追加/刷盘/关闭回调表
        自身._已关闭=False#是否已关闭
        自身._已观察长度=0#本句柄已观察前缀长度

    def _断言打开(自身,操作):#已关闭守卫
        """已关闭句柄一律拒绝。"""
        if 自身._已关闭:#已关闭
            raise 会话句柄已关闭错误(自身.id,操作)#拒绝

    def 读(自身,偏移=0,长度=None,选项=None):#读取事件切片
        """读取合法连续逻辑日志的一段，附带事件值的所有权状态。"""
        自身._断言打开('read')#已关闭拒绝
        if (not 外来安全整数(偏移)) or 偏移<0:#偏移非法
            raise TypeError('read offset must be a non-negative safe integer, got '+str(偏移))#类型错误
        if 长度 is None:#默认到末尾
            长度=安全整数上限#剩余全部
        if (not 外来安全整数(长度)) or 长度<0:#长度非法
            raise TypeError('read length must be a non-negative safe integer, got '+str(长度))#类型错误
        信号=选项['signal'] if 选项 is not None and 'signal' in 选项 else None#可选取消
        源=自身._后端['read'](偏移,长度,信号)#后端读
        事件列表=源['events']#切片
        if 偏移==0 and len(事件列表)<自身._已观察长度:#从 0 读却缩短
            raise 持久化错误('session "'+str(自身.id)+'": stored log shrank below a previously observed prefix ('+str(len(事件列表))+' < '+str(自身._已观察长度)+')')#缩短错误
        if 偏移==0:#全前缀观察
            自身._已观察长度=max(自身._已观察长度,len(事件列表))#更新观察
        else:#后缀观察
            自身._已观察长度=max(自身._已观察长度,偏移+len(事件列表))#更新观察
        return {'eventState':源['eventState'],'events':事件列表}#返回结果

    def 追加(自身,事件列表,选项=None):#追加事件批
        """追加连续批次以续写当前逻辑末尾。"""
        自身._断言打开('append')#已关闭拒绝
        if 自身.access!='write':#读句柄
            raise 会话只读错误(自身.id,'append')#拒绝
        信号=选项['signal'] if 选项 is not None and 'signal' in 选项 else None#可选取消
        自身._后端['append'](事件列表,信号)#后端追加

    def 刷盘(自身,选项=None):#刷盘屏障
        """耐久屏障：已确认追加均耐久。"""
        自身._断言打开('flush')#已关闭拒绝
        if 自身.access!='write':#读句柄
            raise 会话只读错误(自身.id,'flush')#拒绝
        信号=选项['signal'] if 选项 is not None and 'signal' in 选项 else None#可选取消
        if 'flush' in 自身._后端:#有刷盘
            自身._后端['flush'](信号)#后端刷盘

    def 入队活写(自身,事件,报告后台失败):#入队活写
        """缓冲一条活会话事件（若后端提供 enqueueLive / 入队活写）。"""
        自身._断言打开('enqueueLive')#已关闭拒绝
        if '入队活写' in 自身._后端:#中文键
            自身._后端['入队活写'](事件,报告后台失败)#委托
            return#结束
        if 'enqueueLive' in 自身._后端:#英文键
            自身._后端['enqueueLive'](事件,报告后台失败)#委托
            return#结束
        raise 持久化错误('session "'+str(自身.id)+'" handle does not support live enqueue')#缺口

    def 排空活写(自身):#排空活写
        """耐久排空路由活缓冲（若后端提供）。"""
        自身._断言打开('drainLive')#已关闭拒绝
        if '排空活写' in 自身._后端:#中文键
            return 自身._后端['排空活写']()#委托
        if 'drainLive' in 自身._后端:#英文键
            return 自身._后端['drainLive']()#委托
        return None#无活缓冲面则空操作

    def 关闭(自身):#关闭句柄
        """释放句柄；写句柄完成待定耐久并释放写所有权。幂等。"""
        if 自身._已关闭:#已关闭
            return#空操作
        自身._已关闭=True#标记关闭
        if 'close' in 自身._后端:#有关闭
            自身._后端['close']()#后端关闭

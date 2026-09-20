import threading,uuid#线程与子 id
from concurrent.futures import Future as 原生结果#结果 Future
from ...内核.会话 import 会话标识#品牌
from ...sdk.客户端.高层 import 深求装备#Harness 高层 API
from ..子智能体.错误 import 子智能体错误#缝内失败
默认关闭超时毫秒=10000#shutdown 上限
默认处置eof宽限毫秒=6000#EOF 宽限
默认处置宽限毫秒=3000#处置宽限

__all__=['默认关闭超时毫秒','默认处置eof宽限毫秒','默认处置宽限毫秒','启动sdk运行']#公开面

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._原生结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._原生结果.done():#尚未结算
            自身._原生结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._原生结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._原生结果.set_exception(错误)#原样拒绝
            else:#非异常
                自身._原生结果.set_exception(子智能体错误(str(错误),'ERROR'))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._原生结果.result(timeout=超时)#取结果或抛错

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位

class sdk跑:
    """持有者所有的 SDK 一次性跑。载荷字段 id/localAgent/result 为线协议键；拆除入口仅 销毁。"""
    def __init__(自身,标识,结果,拆除):
        """记下身份、结果任务与拆除闭包。"""
        自身.id=标识#父作用域跑 id
        自身.localAgent=None#远程无本地智能体
        自身.result=结果#结果任务
        自身._拆除=拆除#拆除闭包

    def 销毁(自身):
        """等待结果落定并关闭装备。"""
        return 自身._拆除()#同一闭包

def 启动sdk运行(请求,规格):
    """用深求装备驱动一个独立子运行时。请求与规格为 dict；父为智能体对象。"""
    父=请求['parent']#父
    if 'cwd' in 规格 and 规格['cwd'] is not None:#规格覆盖
        工作目录=规格['cwd']#覆盖
    else:#继承父会话
        父头=父.session.header#父会话头
        工作目录=父头['cwd'] if 'cwd' in 父头 else None#cwd
    if 工作目录 is None:#无 cwd
        raise 子智能体错误('subagent-dsh-sdk: parent session has no cwd','NO_CWD')#拒绝
    子标识=会话标识(str(uuid.uuid4()))#子 id
    装备选项={#装备选项
        'launch':{'dshHome':规格['dshHome'],'env':规格['env'] if 'env' in 规格 else {}},#启动
        'cwd':工作目录,#工作目录
        'provider':规格['provider'] if 'provider' in 规格 else 'deepseek-official',#提供方
        'model':规格['model'] if 'model' in 规格 else 'deepseek-v4-flash',#模型
    }#选项骨架
    if 'maxTokens' in 规格 and 规格['maxTokens'] is not None:#有上限
        装备选项['maxTokens']=规格['maxTokens']#写入
    装备=深求装备(装备选项)#构造装备
    提示=请求['prompt']#提示
    信号=请求['signal'] if 'signal' in 请求 else None#取消
    if 已中止(信号):#已取消
        raise 子智能体错误('aborted','CANCELLED')#取消
    结果任务=操作任务()#结果
    def 工作者():
        """后台握手、跑一轮并关闭装备。"""
        try:#跑
            装备.启动运行时()#握手
            会话=装备.会话(str(子标识))#开会话
            输出=会话.运行(提示)#跑一轮
            结果任务.兑现({'output':[{'type':'text','text':str(输出)}],'stopReason':'completed'})#成功
        except BaseException as 错误:#失败
            结果任务.拒绝(错误)#拒绝
        finally:#关
            装备.关闭()#关闭装备
    threading.Thread(target=工作者,daemon=True).start()#启动
    def 拆除():
        """等结果落定后再关装备。"""
        结果任务.等待()#等结果
        装备.关闭()#关
    return sdk跑(子标识,结果任务,拆除)#句柄

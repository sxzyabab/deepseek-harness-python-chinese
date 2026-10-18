'内存中的 Node REPL：每次求值有自己的绑定，输出归到当次求值'
import ast,threading#最后一条表达式与关闭等待
from ...基础设施.js特性 import PromiseEX as 期约#期约
from .异常 import 节点ptc错误#本包异常
from .环境 import 启动环境名#启动环境白名单
from .通道 import json通道#分帧
from .引导 import (#程序侧捕获与绑定
    日志缓冲,制作控制台垫片,捕获流写入,制作绑定错误类,制作命名空间,接线回复,准备完成,准备异常,
)#引导结束

__all__=['运行持久主程序']#仅中文公开名

class 路由缓冲:#把捕获写到当前求值
    '当前求值已经结束时丢弃'
    def __init__(自身,当前):#当前求值盒
        '当前是单元素列表，求值结束时换成空'
        自身._当前=当前#盒

    def 压入(自身,文本):#一条捕获
        '只有仍活跃的求值才入账'
        求值=自身._当前[0]#当前
        if 求值 is not None and 求值['active']:#仍在这次求值里
            求值['logs'].压入(文本)#入账

def 清空程序环境(进程状态):#清掉继承的凭据
    '保留原生子进程启动路径，再换成程序看得见的空环境'
    for 键 in list(进程状态.env.keys()):#逐个键
        if 键.upper() not in 启动环境名:#不在启动白名单
            del 进程状态.env[键]#删掉
    进程状态.env=type(进程状态.env)()#程序看见的空环境

def 求值保留(源码,命名空间):#在保留的命名空间里求值
    '顶层 return 不支持。最后一条是表达式时，它的值就是完成值'
    树=ast.parse(源码,'ptc-repl','exec')#语句
    if len(树.body)==0:#空程序
        return None#无完成值
    末句=树.body[-1]#最后一条
    if type(末句) is ast.Expr:#表达式语句
        前文=树.body[:-1]#前面的语句
        if len(前文)>0:#有语句
            模块=ast.Module(body=前文,type_ignores=[])#只执行前文
            ast.fix_missing_locations(模块)#补位置
            exec(compile(模块,'ptc-repl','exec'),命名空间,命名空间)#保留赋值
        表达式=ast.Expression(末句.value)#最后的表达式
        ast.fix_missing_locations(表达式)#补位置
        return eval(compile(表达式,'ptc-repl','eval'),命名空间,命名空间)#完成值
    exec(compile(树,'ptc-repl','exec'),命名空间,命名空间)#没有完成表达式
    return None#无完成值

def 运行持久主程序(流,最大消息字节,进程状态):#顺序求值直到宿主关掉控制通道
    """顺序服务求值，直到拥有它的宿主关掉控制通道。
    流是继承的私有控制端。
    最大消息字节是控制帧与排队输出上限。
    进程状态是子进程的环境、输出与目录，只绑在 REPL 上下文里。
    返回期约：通道关闭且 REPL 放开流之后解决
    """
    if type(最大消息字节) is not int or 最大消息字节<=0 or 最大消息字节>0xffffffff:#非法上限
        raise 节点ptc错误('invalid control message limit')#拒绝
    清空程序环境(进程状态)#先清环境
    当前=[None]#ALS 的当前求值
    已关=期约()#宿主关闭
    未决={}#调用 id 到期约
    下一标识={'value':1}#跨求值累加
    错误表={}#全局到错误类
    回复表=[]#回复监听
    命名空间={'__builtins__':__builtins__,'_':None,'_error':None,'process':进程状态}#保留的 REPL 上下文
    路由=路由缓冲(当前)#控制台与标准流
    命名空间['console']=制作控制台垫片(路由)#五个级别
    捕获流写入(路由,进程状态.stdout)#标准输出
    捕获流写入(路由,进程状态.stderr)#标准错误
    通道盒=[]#构造期间读线程可能先失败
    def 解决关闭():#只解决一次
        '宿主关闭或传输失败'
        if 已关.状态=='pending':#尚未解决
            已关.解决()#关闭
    def 发送(标识,载荷):#程序到宿主
        '写出失败则关掉通道'
        if len(通道盒)==0:#通道还没装上
            return#忽略
        def 写出失败(错误):#传输失败
            '关掉并结束主程序'
            _=错误#失败原因由通道另报
            通道盒[0].关闭()#关
            解决关闭()#结束
        通道盒[0].发送帧({'id':标识,'payload':载荷}).捕获(写出失败)#包在 id 里
    class 程序端口:#绑定端口
        '求值结束后再调用绑定会拒绝'
        def 发消息(自身,消息):#程序发出
            '没有活跃求值时拒绝'
            求值=当前[0]#当前
            if 求值 is None or not 求值['active']:#求值已结束
                raise 节点ptc错误('PTC evaluation has ended; call this function from a new run_code evaluation')#拒绝
            发送(求值['id'],消息)#归到这次求值
        def 监听(自身,事件,监听器):#挂回复
            '只接 message'
            if 事件=='message':#回复
                回复表.append(监听器)#记下
    端口=程序端口()#绑定用
    接线回复(端口,未决)#回复进未决表
    def 处理运行(消息):#一条 run
        '换目录、安装绑定，再在保留的命名空间里求值'
        if 'id' not in 消息 or 'data' not in 消息 or 'cwd' not in 消息:#宿主帧缺字段
            raise 节点ptc错误('invalid persistent PTC run frame')#协议
        标识=消息['id']#这次求值
        数据=消息['data']#引导
        def 记日志(文本):#一条程序日志
            '发给宿主'
            发送(标识,{'type':'log','text':文本})#日志帧
        def 报告触顶():#输出触顶
            '发给宿主'
            发送(标识,{'type':'output-limit'})#触顶帧
        缓冲=日志缓冲(数据['maxOutputBytes'],记日志,报告触顶)#这次的账
        求值={'id':标识,'logs':缓冲,'maxOutputBytes':数据['maxOutputBytes'],'active':True}#这次求值
        def 结束(片段):#恰好一条 done
            '先标成不活跃，再拒绝未完成的绑定'
            if not 求值['active']:#已经结束
                return#忽略
            求值['active']=False#结束
            if 当前[0] is 求值:#仍是当前
                当前[0]=None#后来的输出不再归这里
            for 调用 in list(未决.values()):#未完成的绑定
                if 调用.状态=='pending':#还没结算
                    调用.拒绝(节点ptc错误('PTC evaluation ended before the binding completed'))#拒绝
            未决.clear()#清空
            完成帧={'type':'done'}#终态
            完成帧.update(片段)#完成值或失败
            发送(标识,完成帧)#恰好一条
        求值['结束']=结束#给期约回调
        当前[0]=求值#这次求值
        try:#安装并求值
            try:#换目录
                进程状态.chdir(消息['cwd'])#宿主给的目录
            except OSError:#系统错误会带上路径
                raise 节点ptc错误('could not change the persistent PTC working directory')#不把路径写进消息
            for 命名空间项 in 数据['namespaces']:#每个命名空间
                描述=命名空间项['errorClass'] if 'errorClass' in 命名空间项 else None#错误类
                if 描述 is None:#这次没声明
                    错误表.pop(命名空间项['global'],None)#不再使用旧构造器
                    continue#下一个
                先前=错误表.get(命名空间项['global'])#上一份
                if 先前 is not None and 先前['name']==描述['name'] and 先前['memberNameProperty']==描述['memberNameProperty']:#同一份
                    continue#复用构造器
                构造器=制作绑定错误类(描述)#新构造器
                错误表[命名空间项['global']]={'name':描述['name'],'memberNameProperty':描述['memberNameProperty'],'constructor':构造器}#换掉
            类表={}#制作命名空间要的表
            for 全局名,记录 in 错误表.items():#仍有效的类
                类表[全局名]=记录['constructor']#构造器
            空间列表=制作命名空间(数据,端口,未决,下一标识,类表)#绑定对象
            下标=0#与 namespaces 对齐
            for 命名空间项 in 数据['namespaces']:#安装到保留上下文
                命名空间[命名空间项['global']]=空间列表[下标]#替换这个全局
                if 'errorClass' in 命名空间项 and 命名空间项['errorClass'] is not None:#有错误类
                    命名空间[命名空间项['errorClass']['name']]=类表[命名空间项['global']]#类名也可见
                下标+=1#下一个
            源码=数据['code']#程序体
            #前导花括号在 Python 里已是表达式，不能再加分号
            try:#求值
                结果值=求值保留(源码,命名空间)#完成值
            except BaseException as 错误:#程序失败
                结束(准备异常(错误,缓冲.剩余输出字节(),数据['maxOutputBytes']))#异常终态
                return#已终态
            if hasattr(结果值,'然后'):#顶层期约
                def 成功(值):#期约兑现
                    '完成值进 done'
                    结束(准备完成(值,缓冲.剩余输出字节(),数据['maxOutputBytes']))#完成
                def 失败(错误):#期约拒绝
                    '拒绝进 done'
                    结束(准备异常(错误,缓冲.剩余输出字节(),数据['maxOutputBytes']))#异常
                结果值.然后(成功,失败)#等它
                return#终态在回调里
            结束(准备完成(结果值,缓冲.剩余输出字节(),数据['maxOutputBytes']))#同步完成值
        except BaseException as 错误:#换目录或安装失败
            结束(准备异常(错误,缓冲.剩余输出字节(),数据['maxOutputBytes']))#异常终态
    def 接收(原始,字节):#一帧
        '回复分给监听；已有活跃求值时再来一帧就关掉'
        _=字节#子进程不按帧长限额
        if type(原始) is not dict:#非对象
            raise 节点ptc错误('invalid persistent PTC frame')#协议
        if 原始.get('type')=='reply':#宿主回复
            for 监听器 in 回复表:#逐个
                监听器(原始)#结算调用
            return#完
        if 当前[0] is not None and 当前[0]['active']:#上一次还没结束
            if len(通道盒)>0:#已装上
                通道盒[0].关闭()#拒绝并发
            解决关闭()#结束
            return#不再求值
        处理运行(原始)#新的一次
    def 失败(错误,种类):#通道失败
        '一律关掉并结束主程序'
        _=错误#原因不改写终态
        _=种类#协议与传输都结束
        if len(通道盒)>0:#已装上
            通道盒[0].关闭()#关
        解决关闭()#结束
    通道=json通道(流,最大消息字节,接收,失败)#分帧
    通道盒.append(通道)#给回调
    进程状态.控制读线程=通道.读线程#入口等到读线程结束
    def 就绪失败(错误):#ready 没写出
        '关掉并结束'
        _=错误#传输失败
        通道.关闭()#关
        解决关闭()#结束
    通道.发送帧({'type':'ready'}).捕获(就绪失败)#握手
    def 收尾(忽略=None):#主程序结束
        '标掉当前求值并关掉通道'
        if 当前[0] is not None:#还有求值对象
            当前[0]['active']=False#不再接收输出
        通道.关闭()#关
        return 忽略#保持兑现
    def 收尾失败(错误):#关闭期约被拒绝
        '仍然收尾，再继续拒绝'
        收尾()#清理
        失败期约=期约()#拒绝回执
        失败期约.拒绝(错误)#原错误
        return 失败期约#继续拒绝
    return 已关.然后(收尾,收尾失败)#关闭后收尾

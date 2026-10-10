'在调用会话既有文件政策下，运行有时限、可取消、不经 shell 的命令'
import threading#定时器与等待门
from ...基础设施.通用工具 import 启动守护线程#守护线程
from ...内核.智能体循环.中止与并发 import 中止控制器#发出中止
from ...工具.超时 import 超时原因,取超时#超时原因
from .类型 import 工作树错误#本包错误
__all__=['运行命令']#仅中文公开名

git清空键=(#清掉继承的仓库、属性树、命令行配置与替换引用选择器
    'GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR','GIT_INDEX_FILE','GIT_OBJECT_DIRECTORY',
    'GIT_ALTERNATE_OBJECT_DIRECTORIES','GIT_CONFIG','GIT_CONFIG_PARAMETERS','GIT_CONFIG_COUNT',
    'GIT_CEILING_DIRECTORIES','GIT_PREFIX','GIT_SHALLOW_FILE','GIT_GRAFT_FILE',
    'GIT_REPLACE_REF_BASE','GIT_ATTR_SOURCE',
)#清空键结束
工作树超时码='WORKTREE_TIMEOUT'#命令截止的超时码

def 抛出若已中止(信号):
    '已中止则抛出。超时改写成人可读的中文，其余原因原样抛出'
    if 信号 is None or not 信号.is_set():#无信号或仍活着
        return#继续
    原因=getattr(信号,'原因',None)#中止原因
    超时=取超时(原因,工作树超时码) if 原因 is not None else None#本命令的超时
    if 超时 is not None:#时限先到
        raise 工作树错误('工作树命令超过 '+str(超时.timeoutMs)+' 毫秒')#给人看的超时
    if isinstance(原因,BaseException):#已有异常原因
        raise 原因#原样抛出
    raise 工作树错误('工作树操作已取消')#没有原因的取消

def 等待期约(期约对象):
    '阻塞到期约结算。拒绝时抛出原因'
    箱={'值':None,'错误':None,'有错':False}#结算箱
    完成=threading.Event()#结算门
    def 成功(值):
        '兑现后记下并开门'
        箱['值']=值#值
        完成.set()#开门
        return 值#交回链式
    def 失败(错误):
        '拒绝后记下并开门'
        箱['错误']=错误#原因
        箱['有错']=True#有错
        完成.set()#开门
    期约对象.然后(成功,失败)#挂上结算
    if not 完成.is_set() and 期约对象.状态=='fulfilled':#已经兑现但回调没开门
        箱['值']=期约对象.数据#直接取
        完成.set()#开门
    elif not 完成.is_set() and 期约对象.状态=='rejected':#已经拒绝但回调没开门
        箱['错误']=期约对象.数据#直接取
        箱['有错']=True#有错
        完成.set()#开门
    完成.wait()#阻塞到结算
    if 箱['有错']:#拒绝
        错误=箱['错误']#原因
        if isinstance(错误,BaseException):#异常原因
            raise 错误#抛出
        raise 工作树错误(str(错误))#其它原因收成错误
    return 箱['值']#兑现值

def 运行命令(上下文,配置,政策,工作目录,参数表,信号,允许退出码=None,环境=None):
    '运行参数表并等待受管进程范围结束。返回有界标准输出与退出码'
    if 允许退出码 is None:#缺省只认成功
        允许退出码=(0,)#退出码 0
    if 环境 is None:#没有命令本地环境
        环境={}#空覆盖
    截止=中止控制器()#本命令的截止
    停止=threading.Event()#命令结束后停掉监听
    def 到期():
        '时限到达时标上超时原因'
        if not 停止.is_set():#尚未收尾
            截止.中止(超时原因(工作树超时码,配置['timeoutMs']))#超时先胜出
    定时=threading.Timer(配置['timeoutMs']/1000.0,到期)#墙钟
    定时.daemon=True#不挡住进程退出
    if 信号 is not None and 信号.is_set():#调用方已经取消
        截止.中止(getattr(信号,'原因',None))#沿用调用方原因
    else:#融合调用方取消
        定时.start()#武装时限
        def 听上游():
            '调用方中止后把原因交给截止'
            while not 停止.is_set():#命令还没结束
                if 信号 is not None and 信号.is_set():#调用方已取消
                    截止.中止(getattr(信号,'原因',None))#转发原因
                    return#结束
                if 停止.wait(0.05):#收尾或再等一拍
                    return#结束
        if 信号 is not None:#有上游才听
            启动守护线程(听上游)#监听
    try:#跑完再收定时器
        抛出若已中止(截止.信号)#开始前
        程序=上下文.subprocess.解析可执行文件(参数表[0],None,截止.信号)#解析可执行文件
        命令=[程序]+list(参数表[1:])#字面参数，不经 shell
        if 政策['mode']=='danger-full-access':#完全放开不包装
            包装=命令#原参数表
        else:#按调用会话政策隔离
            隔离政策=dict(政策)#拷贝政策
            隔离政策['mode']=政策['mode']#保持本次模式
            包装=上下文.sandbox.隔离(命令,隔离政策,截止.信号)['argv']#沙箱参数表
        抛出若已中止(截止.信号)#派生前再查
        子环境={}#先清空 Git 选择器
        for 键 in git清空键:#逐个墓碑
            子环境[键]=None#删掉继承值
        子环境['GIT_TERMINAL_PROMPT']='0'#不弹交互提示
        子环境['GIT_LFS_SKIP_SMUDGE']='1'#不拉取 LFS 大文件
        子环境.update(环境)#命令本地覆盖写在清空之后
        句柄=上下文.subprocess.启动({#派生受管进程
            'argv':包装,#已隔离或原样的参数表
            'cwd':工作目录,#规范工作目录
            'env':子环境,#环境
            'signal':截止.信号,#取消
            'graceMs':配置['graceMs'],#终止宽限
            'stdio':{#三路
                'stdin':'ignore',#不读标准输入
                'stdout':{'maxBytes':配置['maxOutputBytes']},#有界标准输出
                'stderr':{'maxBytes':配置['maxOutputBytes']},#有界标准错误
            },#stdio结束
        })#启动结束
        def 到点终止():
            '截止先到时升级终止这棵进程树。子进程自己的取消监听目前不会执行'
            while not 停止.is_set():#命令还没收尾
                if 截止.信号.is_set():#超时或调用方取消
                    句柄.终止()#TERM 再在宽限后 KILL
                    return#结束
                if 停止.wait(0.05):#收尾或再等一拍
                    return#结束
        启动守护线程(到点终止)#听截止
        try:#等结局后再终止
            结局=等待期约(句柄.done)#进程关闭
            抛出若已中止(截止.信号)#结束后再查取消
            收集=句柄.collected#两路都按收集模式启动
            标准出=收集['stdout'].自偏移读取(0)#从头读标准输出
            标准误=收集['stderr'].自偏移读取(0)#从头读标准错误
            退出码=结局['exitCode']#退出码
            if 退出码 is None or 退出码 not in 允许退出码:#信号死亡或不在允许表
                标记=结局['signal'] if 结局['signal'] is not None else 退出码#信号或退出码
                raise 工作树错误('工作树命令失败（'+str(标记)+'）：'+标准误['text'].strip())#带上标准错误
            if 标准出['lossy']:#标准输出被截断
                raise 工作树错误('工作树命令输出超过 maxOutputBytes')#拒绝不完整输出
            return {'stdout':标准出['text'],'exitCode':退出码}#完整标准输出
        finally:#无论成败都收进程树
            句柄.终止()#升级终止
            等待期约(句柄.等待退出())#等到整树退出
    finally:#卸定时器与监听
        停止.set()#停监听
        定时.cancel()#卸墙钟

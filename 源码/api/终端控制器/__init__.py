'会话拥有的用户终端，权限与执行环境的系统用户相同'
import re#终端身份
from threading import Event as 事件#创建与拆除汇合
from ...依赖.schemastery import 字符串字段,列表字段,正整数字段,自然数字段#配置字段
from ...依赖.工具 import 聚合错误#多路清理失败
from ...基础设施.通用工具.数值判定 import 最大安全整数#时序上限
from ...类型化远程调用.协议 import 远程服务,远程 as _远程,远程错误#宿主远程方法
from ..网关.流协议 import 已中止,若中止则抛 as 若已中止则抛出#取消
from ...客户端.连接.rpc import 中止信号,中止控制器#取消
from .命令解释器 import 发现命令解释器,解析命令解释器#壳
from .浏览器终端 import 浏览器终端,是安全整数#PTY 与屏幕
from .保持 import 终端保持,等到结果#失败分配的清理
from . import (
    异常,#视图失败
    类型,#数据说明
    输出跟随,#跟随队列
)

__all__=['客户端']#包根只导出客户端包，不转发里面的类

身份形态=re.compile(r'^[\w-]{1,128}\Z',re.ASCII)#终端身份
依赖=['subprocess','sandboxPolicy','workingDirectory','typert']#执行提供方与网关


class 配置模式:
    '部署限额与可选壳剖面'
    def __init__(自身):
        '准备字段校验器'
        自身.候选=列表字段(字符串字段(最小长度=1))#候选名
        自身.参数=列表字段(字符串字段())#壳参数
        自身.文本=字符串字段()#路径与显示名
        自身.终端数=正整数字段()#至少 1
        自身.列数=正整数字段(最小=2)#至少 2
        自身.行数=正整数字段()#至少 1
        自身.回滚=自然数字段()#可以为 0
        自身.缓冲=正整数字段(最小=1024)#至少 1024
        自身.输入=正整数字段()#至少 1
        自身.宽限=正整数字段()#至少 1
        自身.无人=自然数字段(最大=最大安全整数)#0 表示不回收
        自身.轮询=正整数字段(最大=最大安全整数)#至少 1
        自身.重试=正整数字段(最大=最大安全整数)#至少 1

    def 校验数据(自身,数据=None):
        '缺省补上默认。非法则拒绝'
        if 数据 is None:#省略配置
            数据={}#空对象
        if not isinstance(数据,dict):#不是对象
            raise TypeError('终端配置必须是对象')#拒绝

        def 取整(字段,键,默认):
            '缺键用默认，布尔不算整数'
            if 键 not in 数据 or 数据[键] is None:#缺省
                值=默认#默认
            else:#调用方给了
                值=数据[键]#原值
            if isinstance(值,bool):#布尔不是整数
                raise TypeError('终端配置 '+键+' 必须是整数')#拒绝
            字段.校验数据(值)#区间
            return 值#通过的值

        if 'shell' not in 数据 or 数据['shell'] is None:#不覆盖默认壳
            壳=None#交给执行环境
        else:#显式剖面
            剖面=数据['shell']#对象
            if not isinstance(剖面,dict):#不是对象
                raise TypeError('终端配置 shell 必须是对象')#拒绝
            自身.文本.校验数据(剖面['path'])#可执行路径
            自身.文本.校验数据(剖面['name'])#显示名
            if 'args' in 剖面 and 剖面['args'] is not None:#给了参数
                自身.参数.校验数据(剖面['args'])#字符串列表
                参数=list(剖面['args'])#拷贝
            else:#缺省空列表
                参数=[]#空
            壳={'path':剖面['path'],'name':剖面['name'],'args':参数}#剖面
        if 'shellCandidates' in 数据 and 数据['shellCandidates'] is not None:#给了候选
            自身.候选.校验数据(数据['shellCandidates'])#非空字符串
            候选=list(数据['shellCandidates'])#拷贝
        else:#缺省
            候选=['zsh','bash','fish','pwsh','powershell','cmd']#常见壳
        return {#归一化后的配置
            'shell':壳,#可选剖面
            'shellCandidates':候选,#选择器候选
            'maxTerminals':取整(自身.终端数,'maxTerminals',8),#每会话上限
            'maxCols':取整(自身.列数,'maxCols',500),#列
            'maxRows':取整(自身.行数,'maxRows',200),#行
            'scrollback':取整(自身.回滚,'scrollback',1000),#回滚行
            'maxBufferedBytes':取整(自身.缓冲,'maxBufferedBytes',2*1024*1024),#跟随缓冲
            'maxInputBytes':取整(自身.输入,'maxInputBytes',64*1024),#单次输入
            'disposeGraceMs':取整(自身.宽限,'disposeGraceMs',1000),#终止宽限
            'unattendedTimeoutMs':取整(自身.无人,'unattendedTimeoutMs',7200000),#无人值守
            'activityPollIntervalMs':取整(自身.轮询,'activityPollIntervalMs',30000),#活动轮询
            'cleanupRetryMs':取整(自身.重试,'cleanupRetryMs',60000),#清理重试
        }#配置结束


class 终端控制器(远程服务):
    '类型化远程控制短暂的、属于会话的终端进程'
    inject=依赖#框架槽
    Config=配置模式()#框架槽

    def __init__(自身,上下文,配置值):
        '挂上进程拆除。配置已经过校验'
        super().__init__(上下文,'terminalController',{'namespace':'terminal'})#服务名与命名空间
        自身.配置值=配置值#限额与壳
        自身.拥有者={}#会话 id 到拥有者
        自身.寿命=中止控制器()#控制器寿命

        def 拆除效果():
            '拆掉全部会话拥有者'

            def 清理():
                '聚合清理失败'
                自身.寿命.中止配套信号(RuntimeError('Terminal controller disposed'))#中止新的分配
                失败=[]#错误
                for 标识,拥有 in list(自身.拥有者.items()):#逐个会话
                    try:#一路失败不挡住其余
                        自身._拆除拥有者(标识,拥有)#拆
                    except BaseException as 错误:#收下
                        失败.append(错误)#记下
                if len(失败)>0:#有失败
                    raise 聚合错误(失败,'Browser terminal cleanup failed')#聚合

            return 清理#拆除器

        上下文.副作用(拆除效果,'terminal-controller.processes')#登记

    @_远程
    def environment(自身,agent,signal):
        '读取会话当前目录和终端限额。不访问文件系统，也不查壳'
        若已中止则抛出(signal)#请求取消
        执行=自身._执行环境(agent)#提供方
        工作目录=执行['workingDirectory']#工作目录服务
        return {#已记录的目录和限额。保留中的终端仍用自己的进程目录
            'cwd':工作目录.取当前目录(agent.session),#已记录目录
            'maxInputBytes':自身.配置值['maxInputBytes'],#单次输入
            'maxBufferedBytes':自身.配置值['maxBufferedBytes'],#入站缓冲
            'maxCols':自身.配置值['maxCols'],#列
            'maxRows':自身.配置值['maxRows'],#行
            'scrollback':自身.配置值['scrollback'],#回滚
        }#环境

    @_远程
    def shells(自身,agent,signal):
        '在会话的执行环境里发现已安装的壳。配置或系统默认在前'
        若已中止则抛出(signal)#请求取消
        执行=自身._执行环境(agent)#提供方
        return 发现命令解释器(执行['subprocess'],自身.配置值['shell'],自身.配置值['shellCandidates'],signal)#已核验列表

    @_远程
    def list(自身,sessionId):
        '列出保留的终端。不解析、也不激活智能体'
        拥有=自身.拥有者.get(sessionId)#这一次宿主寿命里的会话
        if 拥有 is None:#没有
            return []#空
        结果=[]#信息
        for 终端 in 拥有['terminals'].values():#已提交
            结果.append(终端.info)#信息
        for 分配 in 拥有['allocations'].values():#失败后仍占名额的分配
            结果.append(分配['info'])#信息
        return 结果#列表

    @_远程
    def create(自身,agent,request,signal):
        '按调用方给出的身份分配一次用户壳。已提交的终端在断线后仍在'
        若已中止则抛出(自身.寿命.信号)#控制器已拆
        标识=request['id']#幂等身份
        if 身份形态.match(标识) is None:#非法
            raise RuntimeError('Invalid terminal identity')#拒绝
        自身._尺寸(request['cols'],request['rows'])#尺寸
        拥有=自身._拥有者(agent)#会话拥有者
        若已中止则抛出(拥有['lifetime'].信号)#拥有者已拆
        自身._要求开着(拥有,标识)#关闭过的身份不能再建
        已有=拥有['terminals'].get(标识)#已提交
        if 已有 is not None:#幂等
            return 已有.info#现有
        进行=拥有['pending'].get(标识)#同一次分配还在进行
        if 进行 is not None:#等它
            进行.wait()#汇合
            if 进行.错误 is not None:#那一次失败
                raise 进行.错误#同一失败
            自身._要求开着(拥有,标识)#等待期间被关闭
            return 进行.值.info#提交结果
        占用=set(list(拥有['terminals'])+list(拥有['pending'])+list(拥有['allocations']))#身份
        if len(占用)>=自身.配置值['maxTerminals']:#满了
            raise 远程错误('terminal/limit-reached','Session terminal limit reached',{'limit':自身.配置值['maxTerminals']})#限额
        完成=事件()#这一次分配
        完成.错误=None#失败写在这一次上
        完成.值=None#成功时的终端
        拥有['pending'][标识]=完成#发布进行中，关闭可以等它
        融合=中止信号.任一([signal,自身.寿命.信号,拥有['lifetime'].信号])#三路取消
        try:#分配、提交、监视
            终端=自身._生成(agent,拥有,request,融合)#可能留下失败分配
            拥有['terminals'][标识]=终端#提交
            拥有['allocations'].pop(标识,None)#摘掉残留

            def 关闭中():
                '终止前先关上身份'
                拥有['closedIds'].add(标识)#记

            def 已关():
                '成功终止后摘掉这一条'
                拥有['terminals'].pop(标识,None)#摘

            def 失败时(错误):
                '后台清理失败只记日志'
                自身.ctx.日志.错误('Browser terminal cleanup failed',错误)#诊断

            终端.监视(自身.配置值,关闭中,已关,失败时)#提交后才监视
            自身._要求开着(拥有,标识)#监视前被关闭则拒绝，进程仍留下
            完成.值=终端#等同一分配的人拿走它
            return 终端.info#已提交
        except BaseException as 错误:#创建失败由创建报告
            完成.错误=错误#等的人看见同一失败
            raise#原样
        finally:#进行中的记录在落定后摘掉
            完成.set()#放开等待
            拥有['pending'].pop(标识,None)#摘掉

    @_远程({'mode':'stream'})
    def retain(自身,sessionId,id,signal):
        '为窗口保持已有终端。不激活智能体，也不拿输入控制'
        拥有=自身.拥有者.get(sessionId)#可以是未激活的已保存布局
        终端=None if 拥有 is None else 拥有['terminals'].get(id)#已提交
        已关=拥有 is not None and id in 拥有['closedIds']#已关闭
        寿命尽=拥有 is not None and 已中止(拥有['lifetime'].信号)#拥有者已拆
        if 终端 is None or 已关 or 寿命尽:#正在关或没有
            raise 远程错误('terminal/unavailable','Terminal is closing or unavailable',{})#拒绝
        yield from 终端.保持进程(signal)#确认后保持到取消

    @_远程({'mode':'stream'})
    def attach(自身,agent,id,signal):
        '把输入和输出接到一条物理远程流。取消不结束进程，输入不重放'
        try:#上下文没有调用时按属性缺失
            调用=自身.ctx.invocation#这一次远程调用
        except AttributeError:#网关没放上
            调用=None#没有
        if 调用 is None:#必须在远程调用里
            raise RuntimeError('Terminal attachment requires a Remote invocation')#拒绝
        窗口=getattr(调用,'uplinkWindow',None)#没有入站上限时缺席
        yield from 自身._终端(agent,id).附着(调用.uplink(),自身.配置值,signal,窗口)#屏幕、输出和确认

    @_远程
    def rename(自身,agent,id,title):
        '改显示名，不改壳'
        if len(title.strip())==0 or len(title)>120:#空白或超长
            raise RuntimeError('Terminal title must contain 1–120 characters')#拒绝
        自身._终端(agent,id).重命名(title.strip())#发布

    @_远程
    def close(自身,agent,id):
        '关闭身份并杀掉进程范围。重复关闭成功。清理失败则留下以便重试'
        拥有=自身._拥有者(agent)#会话
        拥有['closedIds'].add(id)#以后不能再创建
        进行=拥有['pending'].get(id)#创建可能已经发布了分配
        if 进行 is not None:#等创建落定
            进行.wait()#创建自己报告失败。关闭仍拥有已分配的进程
        终端=拥有['terminals'].get(id)#已提交
        if 终端 is not None:#有进程
            终端.关闭()#清理
            拥有['terminals'].pop(id,None)#摘掉
            return#完成
        分配=拥有['allocations'].get(id)#失败残留
        if 分配 is None:#没有可关的
            return#重复关闭成功
        分配['cleanup'].关闭()#清理残留
        拥有['allocations'].pop(id,None)#摘掉

    def _拥有者(自身,agent):
        '没有则创建，并挂上智能体拆除'
        标识=agent.id#会话 id
        拥有=自身.拥有者.get(标识)#已有
        if 拥有 is not None:#已有
            return 拥有#复用
        拥有={#新的会话拥有者
            'terminals':{},#已提交
            'pending':{},#进行中
            'allocations':{},#失败残留
            'closedIds':set(),#已关身份
            'lifetime':中止控制器(),#寿命
            'cleanup':None,#拆除任务
        }#拥有
        自身.拥有者[标识]=拥有#登记
        持有=拥有#闭包

        def 拆除效果():
            '拆这一个拥有者'

            def 清理():
                '委托拆除'
                自身._拆除拥有者(标识,持有)#拆

            return 清理#拆除器

        agent.ctx.副作用(拆除效果,'terminal-controller.owner')#智能体拆除时拆终端
        return 拥有#拥有者

    def _拆除拥有者(自身,标识,拥有):
        '等进行中的创建，关终端，拆残留。失败则清掉任务以便再试'
        已有=拥有['cleanup']#已经开始的那一次
        if 已有 is not None:#加入
            已有.wait()#等
            if 已有.错误 is not None:#失败
                raise 已有.错误#同一失败
            return#成功
        拥有['lifetime'].中止配套信号(RuntimeError('Terminal Session owner disposed'))#拆开保持
        完成=事件()#这一次
        完成.错误=None#失败写在这一次上
        拥有['cleanup']=完成#记下
        try:#等进行中，再关
            for 任务 in list(拥有['pending'].values()):#创建成败都等
                任务.wait()#全部结算
            失败=[]#错误
            for 终端 in list(拥有['terminals'].values()):#已提交
                try:#关
                    终端.释放()#停监视并清理
                except BaseException as 错误:#收下
                    失败.append(错误)#记下
            for 分配 in list(拥有['allocations'].values()):#残留
                try:#拆保持
                    分配['cleanup'].释放()#拆
                except BaseException as 错误:#收下
                    失败.append(错误)#记下
            if len(失败)>0:#有失败
                raise 聚合错误(失败,'Session terminal cleanup failed')#聚合
            拥有['terminals'].clear()#清空
            拥有['allocations'].clear()#清空
            自身.拥有者.pop(标识,None)#摘掉会话
        except BaseException as 错误:#失败后允许再拆
            完成.错误=错误#加入者看见
            拥有['cleanup']=None#清掉任务
            完成.set()#放开
            raise#原样
        完成.set()#成功

    def _终端(自身,agent,id):
        '取已提交的终端。不存在或已关闭则拒绝'
        拥有=自身.拥有者.get(agent.id)#拥有者
        终端=None if 拥有 is None else 拥有['terminals'].get(id)#已提交
        if 终端 is None:#没有
            raise 远程错误('terminal/unavailable','Terminal no longer exists in this Session',{})#拒绝
        自身._要求开着(拥有,id)#已关闭
        return 终端#终端

    def _要求开着(自身,拥有,标识):
        '这个身份已经关闭则拒绝'
        if 标识 in 拥有['closedIds']:#已关
            raise 远程错误('terminal/unavailable','Terminal was closed in this Session',{})#拒绝

    def _尺寸(自身,列,行):
        '列和行必须是限额内的安全整数'
        if (not 是安全整数(列) or 列<2 or 列>自身.配置值['maxCols']
                or not 是安全整数(行) or 行<1 or 行>自身.配置值['maxRows']):#超出
            raise RuntimeError('Terminal dimensions exceed the configured limits')#拒绝

    def _执行环境(自身,agent):
        '智能体上下文选择执行提供方，不注入消费服务'
        子进程=agent.ctx.获取服务('subprocess')#子进程
        沙箱政策=agent.ctx.获取服务('sandboxPolicy')#沙箱政策
        if 子进程 is None or 沙箱政策 is None:#缺一
            raise RuntimeError('The Session execution environment requires subprocess and sandbox policy providers')#拒绝
        工作目录=agent.ctx.获取服务('workingDirectory')#工作目录
        if 工作目录 is None:#缺
            raise RuntimeError('The Session execution environment requires a working-directory provider')#拒绝
        return {'subprocess':子进程,'sandboxPolicy':沙箱政策,'workingDirectory':工作目录}#提供方

    def _生成(自身,agent,拥有,request,signal):
        '拉起终端。提交前失败则用保持清理，并可能留下占名额的分配'
        执行=自身._执行环境(agent)#提供方
        目录=执行['workingDirectory'].ensure(agent,signal)#确保目录还在
        if 'shellPath' not in request:#用默认壳
            壳=解析命令解释器(执行['subprocess'],自身.配置值['shell'],signal)#配置或环境默认
        else:#调用方指定了发现结果里的路径
            壳=None#尚未命中
            for 项 in 自身.shells(agent,signal):#再核验一次
                if 项['path']==request['shellPath']:#命中
                    壳=项#用这条
                    break#停
        if 壳 is None:#这个环境里没有
            raise RuntimeError('Selected shell is not available in this execution environment')#拒绝
        句柄=执行['subprocess'].启动终端({#分配 PTY
            'argv':[壳['path'],*壳['args']],#程序和参数
            'cwd':目录,#会话目录
            'cols':request['cols'],#列
            'rows':request['rows'],#行
            'terminalType':'xterm-256color',#TERM
            'env':{'DSH_SESSION_ID':agent.id},#会话
            'shellActivity':True,#活动观察
            'graceMs':自身.配置值['disposeGraceMs'],#终止宽限
            'signal':signal,#分配取消
        })#句柄
        信息={#初始元数据
            'id':request['id'],#身份
            'shell':壳,#壳
            'title':壳['name'],#标题
            'cwd':目录,#初始目录
            'cols':request['cols'],#列
            'rows':request['rows'],#行
            'state':'running',#运行
            'exitCode':None,#尚未退出
        }#信息
        try:#提交前再看取消
            若已中止则抛出(signal)#已取消则不提交
            return 浏览器终端(句柄,信息,自身.配置值['scrollback'],自身.配置值['maxBufferedBytes'])#终端
        except BaseException as 错误:#留下占名额的失败分配

            def 终止():
                '关上身份、终止进程并摘掉分配'
                拥有['closedIds'].add(request['id'])#不能再建
                等到结果(句柄.终止())#等进程静止
                拥有['allocations'].pop(request['id'],None)#摘掉

            def 失败时(清理错误):
                '自动清理失败只记日志'
                自身.ctx.日志.错误('Browser terminal allocation cleanup failed',清理错误)#诊断

            清理=终端保持(自身.配置值,句柄.检查活动,终止,失败时)#可重试清理
            说明=str(错误)#失败说明
            拥有['allocations'][request['id']]={#占着名额
                'info':{**信息,'state':'failed','error':说明},#失败信息
                'cleanup':清理,#清理
            }#残留
            try:#立刻关一次
                清理.关闭()#终止
            except BaseException as 清理错误:#清理也失败
                raise 聚合错误([错误,清理错误],'Terminal allocation cleanup failed')#两份失败
            raise 错误#创建仍然失败


default=终端控制器#类插件
inject=依赖#框架槽
Config=终端控制器.Config#框架槽
from . import 客户端#浏览器侧模型。放在类定义之后，避免加载客户端时本包还没有默认导出

import re,threading#身份形态与拆除线程
from ...依赖.schemastery import 字符串字段,正整数字段,自然数字段,列表字段
from ...依赖.工具 import 聚合错误#拆除失败
from ...内核.作用域 import 操作任务#分配任务
from ...typert.协议 import 远程服务,远程 as _远程
from ...工具.超时 import 中止控制器,若已中止则抛出,合成信号,已中止#中止
from .外壳 import 发现外壳,解析外壳#壳
from .浏览器终端 import 浏览器终端#PTY 视图
from .保持 import 终端保持#保持与回收
from .类型 import 远程错误#限额与身份

__all__=['依赖','默认','配置','终端控制器']

配置={#部署限额与可选壳剖面
    'shellCandidates':列表字段(字符串字段(最小长度=1),默认值=['zsh','bash','fish','pwsh','powershell','cmd']),#候选
    'maxTerminals':正整数字段(默认值=8),#每会话上限
    'maxCols':正整数字段(最小=2,默认值=500),#列
    'maxRows':正整数字段(默认值=200),#行
    'scrollback':自然数字段(默认值=1000),#回滚
    'maxBufferedBytes':正整数字段(最小=1024,默认值=2*1024*1024),#跟随缓冲
    'maxInputBytes':正整数字段(默认值=64*1024),#单次输入
    'disposeGraceMs':正整数字段(默认值=1000),#终止宽限
    'unattendedTimeoutMs':自然数字段(默认值=7200000),#无人值守超时
    'activityPollIntervalMs':正整数字段(默认值=30000),#活动轮询
    'cleanupRetryMs':正整数字段(默认值=60000),#清理重试
}

身份形态=re.compile(r'^[\w-]{1,128}\Z',re.ASCII)#终端/附着 id

def _流方法(方法):#标流式 Remote
    """mode=stream。"""
    方法._typert_remote_marker={'invocation':{'kind':'direct','mode':'stream'}}#标记
    return 方法#方法

class 终端控制器(远程服务):#会话范围浏览器终端
    """类型化 Remote 控制短暂的会话终端进程。"""
    def __init__(自身,上下文,配置值):#构造
        """挂拆除；不依赖 sessionProjections。"""
        super().__init__(上下文,'terminalController',{'namespace':'terminal'})#登记
        自身.配置值=配置值 if 配置值 is not None else {}
        自身.拥有者={}#会话 id → 拥有
        自身.寿命=中止控制器()#寿命
        def 拆除效果():
            """拆全部拥有者。"""
            def 清理():#拆除器
                """聚合失败。"""
                自身.寿命.中止(远程错误('gateway/internal','Terminal controller disposed',{}))#中止
                失败=[]#错误
                for 标识,拥有 in list(自身.拥有者.items()):#逐个
                    try:#拆
                        自身._拆除拥有者(标识,拥有)#拆
                    except BaseException as 错误:
                        失败.append(错误)#收
                if len(失败)>0:#有
                    raise 聚合错误(失败,'Browser terminal cleanup failed')#聚合
            return 清理#拆除器
        上下文.副作用(拆除效果,'terminal-controller.processes')#登记

    @_远程
    def environment(自身,智能体,信号):#工作目录与限额
        """不解析壳。"""
        若已中止则抛出(信号)#中止
        执行=自身._执行环境(智能体)#提供方
        头=智能体.session.header if hasattr(智能体.session,'header') else None#头
        会话目录=头.cwd if 头 is not None and hasattr(头,'cwd') else None#会话 cwd
        if 会话目录 is None and isinstance(头,dict):#dict 头
            会话目录=头.get('cwd')#cwd
        根=执行['sandboxPolicy'].workspaceRoot#工作区根
        return {
            'cwd':会话目录 if 会话目录 is not None else 根,#工作区
            'maxInputBytes':自身.配置值.get('maxInputBytes',64*1024),#输入
            'maxCols':自身.配置值.get('maxCols',500),#列
            'maxRows':自身.配置值.get('maxRows',200),#行
            'scrollback':自身.配置值.get('scrollback',1000),#回滚
        }#环境

    @_远程
    def shells(自身,智能体,信号):#已安装壳
        """配置或系统默认在前。"""
        若已中止则抛出(信号)#中止
        执行=自身._执行环境(智能体)#提供方
        壳=自身.配置值.get('shell')#可选剖面
        候选=自身.配置值.get('shellCandidates',['zsh','bash','fish','pwsh','powershell','cmd'])#候选
        return 发现外壳(执行['subprocess'],壳,候选,信号)#列表

    @_远程
    def list(自身,会话标识):#保留终端
        """不激活智能体。"""
        拥有=自身.拥有者.get(会话标识)#拥有
        if 拥有 is None:#无
            return []#空
        结果=[]#信息
        for 终端 in 拥有['terminals'].values():#已提交
            结果.append(终端.info)#信息
        for 分配 in 拥有['allocations'].values():#失败残留
            结果.append(分配['info'])#信息
        return 结果#列表

    @_远程
    def create(自身,智能体,请求,信号):#幂等分配
        """已提交则返回现有；关闭后的身份不能再建。"""
        若已中止则抛出(自身.寿命.信号)#已拆
        标识=请求['id']#id
        if 身份形态.match(标识) is None:#非法
            raise 远程错误('gateway/bad-request','Invalid terminal identity',{})#拒绝
        自身._尺寸(请求['cols'],请求['rows'])#尺寸
        拥有=自身._拥有(智能体)#拥有
        若已中止则抛出(拥有['lifetime'].信号)#拥有者拆
        自身._要求开着(拥有,标识)#未关闭
        已有=拥有['terminals'].get(标识)#已提交
        if 已有 is not None:#有
            return 已有.info#现有
        进行=拥有['pending'].get(标识)#进行中
        if 进行 is not None:#等同一分配
            终端=进行.等待()#等
            自身._要求开着(拥有,标识)#仍开
            return 终端.info#信息
        if 标识 in 拥有['allocations']:#失败残留
            raise 远程错误('gateway/bad-request','Close the failed terminal allocation before creating it again',{})#拒绝
        占用=set(list(拥有['terminals'].keys())+list(拥有['pending'].keys())+list(拥有['allocations'].keys()))#身份
        上限=自身.配置值.get('maxTerminals',8)#上限
        if len(占用)>=上限:#满
            raise 远程错误('terminal/limit-reached','Session terminal limit reached',{'limit':上限})#限额
        融合=合成信号(信号,自身.寿命.信号,拥有['lifetime'].信号)#融合
        任务=自身._分配任务(智能体,拥有,请求,融合)#任务
        拥有['pending'][标识]=任务#进行中
        try:#等
            终端=任务.等待()#终端
            拥有['terminals'][标识]=终端#提交
            拥有['allocations'].pop(标识,None)#摘残留
            def 关闭中():
                """关闭 id。"""
                拥有['closedIds'].add(标识)#记
            def 已关():
                """摘终端。"""
                拥有['terminals'].pop(标识,None)#摘
            def 失败汇(错误):
                """日志。"""
                print('Browser terminal cleanup failed',错误)#日志
            终端.监视(自身.配置值,关闭中,已关,失败汇)#监视
            自身._要求开着(拥有,标识)#仍开
            return 终端.info#信息
        finally:#摘进行
            拥有['pending'].pop(标识,None)#摘

    @_流方法
    def retain(自身,会话标识,标识,信号):#窗口保持
        """不激活 Agent。"""
        拥有=自身.拥有者.get(会话标识)#拥有
        终端=None if 拥有 is None else 拥有['terminals'].get(标识)#终端
        if 终端 is None or (拥有 is not None and 标识 in 拥有['closedIds']) or (拥有 is not None and 已中止(拥有['lifetime'].信号)):#不可用
            raise 远程错误('terminal/unavailable','Terminal is closing or unavailable',{})#拒绝
        yield from 终端.保持(信号)#保持

    @_流方法
    def follow(自身,智能体,标识,附着标识,信号):#附着不绑进程寿命
        """屏幕恢复后跟输出与元数据。"""
        if 身份形态.match(附着标识) is None:#非法
            raise 远程错误('gateway/bad-request','Invalid terminal attachment identity',{})#拒绝
        yield from 自身._终端(智能体,标识).跟随(附着标识,信号)#跟随

    @_远程
    def write(自身,智能体,标识,附着标识,数据):#原始输入
        """含 Tab 与控制字符。"""
        上限=自身.配置值.get('maxInputBytes',64*1024)#上限
        if len(数据.encode('utf-8'))>上限:#超
            raise 远程错误('gateway/bad-request','Terminal input exceeds the configured limit',{})#拒绝
        自身._终端(智能体,标识).写入(附着标识,数据)#写

    @_远程
    def resize(自身,智能体,标识,附着标识,列,行):#尺寸
        """PTY 与恢复屏。"""
        自身._尺寸(列,行)#校验
        自身._终端(智能体,标识).调整尺寸(附着标识,列,行)#调

    @_远程
    def rename(自身,智能体,标识,标题):#显示名
        """1–120 字符。"""
        去空白=标题.strip()#去空白
        if len(去空白)==0 or len(标题)>120:#非法
            raise 远程错误('gateway/bad-request','Terminal title must contain 1–120 characters',{})#拒绝
        自身._终端(智能体,标识).重命名(去空白)#改

    @_远程
    def close(自身,智能体,标识):#关身份并杀进程范围
        """重复关闭成功；清理失败则保留以便重试。"""
        拥有=自身._拥有(智能体)#拥有
        拥有['closedIds'].add(标识)#记住关闭
        进行=拥有['pending'].get(标识)#进行中创建
        if 进行 is not None:#等创建
            try:#等
                进行.等待()#等
            except BaseException:#创建失败仍拥有已分配进程
                pass
        终端=拥有['terminals'].get(标识)#已提交
        if 终端 is not None:#有
            终端.关闭()#关
            拥有['terminals'].pop(标识,None)#摘
        else:#残留分配
            分配=拥有['allocations'].get(标识)#残留
            if 分配 is None:#无
                return#成功
            分配['cleanup'].close()#关
            拥有['allocations'].pop(标识,None)#摘

    def _拥有(自身,智能体):#按会话
        """没有则创建并挂智能体拆除。"""
        标识=智能体.id#会话 id
        拥有=自身.拥有者.get(标识)#已有
        if 拥有 is None:#新建
            拥有={
                'terminals':{},#已提交
                'pending':{},#进行中
                'allocations':{},#失败残留
                'closedIds':set(),#已关身份
                'lifetime':中止控制器(),#寿命
                'cleanup':None,#拆除任务
            }#拥有
            自身.拥有者[标识]=拥有#登记
            持有=拥有#闭包
            def 拆除效果():#智能体拆除
                """拆本拥有者。"""
                def 清理():#拆除器
                    """委托。"""
                    自身._拆除拥有者(标识,持有)#拆
                return 清理#拆除器
            智能体.ctx.副作用(拆除效果,'terminal-controller.owner')
        return 拥有

    def _拆除拥有者(自身,标识,拥有):#一次
        """等进行中创建，关终端，杀残留。"""
        if 拥有['cleanup'] is not None:#已开始
            拥有['cleanup'].wait()#等
            return
        完成=threading.Event()#完成
        拥有['cleanup']=完成#记下
        拥有['lifetime'].中止(远程错误('gateway/internal','Terminal Session owner disposed',{}))#中止
        try:#拆
            for 任务 in list(拥有['pending'].values()):#进行中
                try:#等
                    任务.等待()#等
                except BaseException:#忽略
                    pass
            失败=[]#错误
            for 终端 in list(拥有['terminals'].values()):#终端
                try:#关
                    终端.关闭()#关
                except BaseException as 错误:
                    失败.append(错误)#收
            for 分配 in list(拥有['allocations'].values()):#残留
                try:#拆除保持
                    分配['cleanup'].dispose()#拆
                except BaseException as 错误:
                    失败.append(错误)#收
            if len(失败)>0:#有
                拥有['cleanup']=None#可重试
                完成.set()#放行等待者
                raise 聚合错误(失败,'Session terminal cleanup failed')#聚合
            拥有['terminals'].clear()#清空
            拥有['allocations'].clear()#清空
            自身.拥有者.pop(标识,None)#摘
        finally:#广播
            完成.set()#完

    def _终端(自身,智能体,标识):#已提交
        """不存在则拒绝。"""
        拥有=自身.拥有者.get(智能体.id)#拥有
        终端=None if 拥有 is None else 拥有['terminals'].get(标识)#终端
        if 终端 is None:#无
            raise 远程错误('terminal/unavailable','Terminal no longer exists in this Session',{})#拒绝
        自身._要求开着(拥有,标识)#未关闭
        return 终端#终端

    def _要求开着(自身,拥有,标识):#未关闭身份
        """已关则拒绝。"""
        if 标识 in 拥有['closedIds']:#已关
            raise 远程错误('terminal/unavailable','Terminal was closed in this Session',{})#拒绝

    def _尺寸(自身,列,行):#限额内安全整数
        """超出则拒绝。"""
        最大列=自身.配置值.get('maxCols',500)#列
        最大行=自身.配置值.get('maxRows',200)#行
        if (isinstance(列,bool) or not isinstance(列,int) or 列<2 or 列>最大列
                or isinstance(行,bool) or not isinstance(行,int) or 行<1 or 行>最大行):#非法
            raise 远程错误('gateway/bad-request','Terminal dimensions exceed the configured limits',{})#拒绝

    def _执行环境(自身,智能体):#Agent 上下文上的提供方
        """智能体上下文选择执行提供方，不依赖消费服务。"""
        子进程=智能体.ctx.获取服务('subprocess',False)#子进程
        沙箱政策=智能体.ctx.获取服务('sandboxPolicy',False)#政策
        if 子进程 is None or 沙箱政策 is None:#缺
            raise 远程错误('gateway/bad-request','The Session execution environment requires subprocess and sandbox policy providers',{})#拒绝
        return {'subprocess':子进程,'sandboxPolicy':沙箱政策}#提供方

    def _分配任务(自身,智能体,拥有,请求,信号):#后台 spawn
        """返回可等待任务。"""
        任务=操作任务()#任务
        def 在线程执行():#线程
            """spawn。"""
            try:#分配
                值=自身._生成(智能体,拥有,请求,信号)#终端
                任务.兑现(值)#完
            except BaseException as 错误:
                任务.拒绝(错误)#拒绝
        threading.Thread(target=在线线程执行).start()#跑
        return 任务#任务

    def _生成(自身,智能体,拥有,请求,信号):#spawnTerminal
        """失败则经 TerminalRetention 清理并可能留下 allocations。"""
        环境=自身.environment(智能体,信号)#环境
        执行=自身._执行环境(智能体)#提供方
        if 'shellPath' not in 请求:#默认
            壳=解析外壳(执行['subprocess'],自身.配置值.get('shell'),信号)
        else:#指定
            列表=自身.shells(智能体,信号)#发现
            壳=None#未命中
            for 项 in 列表:
                if 项['path']==请求['shellPath']:#命中
                    壳=项#记下
                    break#停
        if 壳 is None:#不可用
            raise 远程错误('gateway/bad-request','Selected shell is not available in this execution environment',{})#拒绝
        句柄=执行['subprocess'].启动终端({
            'argv':[壳['path'],*壳['args']],#参数
            'cwd':环境['cwd'],#目录
            'cols':请求['cols'],#列
            'rows':请求['rows'],#行
            'terminalType':'xterm-256color',#TERM
            'env':{'DSH_SESSION_ID':智能体.id},#会话
            'shellActivity':True,#活动观察
            'graceMs':自身.配置值.get('disposeGraceMs',1000),#宽限
            'signal':信号,#中止
        })#句柄
        信息={
            'id':请求['id'],#id
            'shell':壳,#壳
            'title':壳['name'],#标题
            'cwd':环境['cwd'],#目录
            'cols':请求['cols'],#列
            'rows':请求['rows'],#行
            'state':'running',#运行
            'exitCode':None,#码
        }#信息
        try:#提交
            若已中止则抛出(信号)#中止
            return 浏览器终端(句柄,信息,自身.配置值.get('scrollback',1000),自身.配置值.get('maxBufferedBytes',2*1024*1024))#终端
        except BaseException as 错误:
            def 观察():
                """活动。"""
                return 句柄.检查活动() if hasattr(句柄,'检查活动') else 句柄.inspectActivity()#活动
            def 终止():
                """关残留。"""
                拥有['closedIds'].add(请求['id'])#记
                句柄.终止()#终止
                拥有['allocations'].pop(请求['id'],None)#摘
            def 失败汇(清理错误):
                """日志。"""
                print('Browser terminal allocation cleanup failed',清理错误)#日志
            清理=终端保持(自身.配置值,观察,终止,失败汇)#保持清理
            拥有['allocations'][请求['id']]={
                'info':{**信息,'state':'failed','error':str(错误)},
                'cleanup':清理,#清理
            }#残留
            try:#关
                清理.close()#关
            except BaseException as 清理错误:
                raise 聚合错误([错误,清理错误],'Terminal allocation cleanup failed')#聚合
            raise 错误#原样

依赖=['subprocess','sandboxPolicy','typert']
默认=终端控制器
Config=配置#框架槽
default=默认#框架槽
inject=依赖#框架槽
终端控制器.inject=依赖#框架槽

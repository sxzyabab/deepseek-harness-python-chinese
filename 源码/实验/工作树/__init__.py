'新建 Git 分支与检出，再把调用会话的工作目录改到那里'
import threading,uuid#在途门与生成名称
from ...依赖.cordis.服务 import 服务#服务基类
from ...内核.智能体循环.中止与并发 import 中止控制器#寿命中止
from ...基础设施.通用工具 import 启动守护线程#融合监听
from ...基础设施.通用工具.数值判定 import 是否正安全整数#正安全整数
from ...工具.超时 import 定时器延迟上限毫秒#定时器延迟上限
from .类型 import 工作树错误,创建请求字段,创建结果字段,是相对路径,创建结果#类型与错误
from .目录 import 准备目录脚本#沙箱内的目录分配子程序
from .进程 import 运行命令,抛出若已中止#有界命令

默认目录='.agents/worktrees'#源仓库内的相对检出池
默认名称前缀='worktree-'#自动名称前缀
默认git命令='git'#Git 2.45 或更新的可执行名
默认node命令='node'#沙箱内分配目录用的 Node
默认超时毫秒=60_000#单条命令时限
默认宽限毫秒=3_000#子进程终止宽限
默认输出字节=65_536#每路输出捕获上限
整数键=('timeoutMs','graceMs','maxOutputBytes')#必须为正整数的配置键

def 读取配置(配置值,键,缺省):
    '缺席用缺省；显式给出的值交给后面的校验'
    if not isinstance(配置值,dict) or 键 not in 配置值:#没有这份配置或没有该键
        return 缺省#缺省
    return 配置值[键]#调用方的值

def 要求正整数(键,值):
    '拒绝布尔、非安全整数，以及超过定时器上限的数'
    if isinstance(值,bool) or not 是否正安全整数(值) or 值>定时器延迟上限毫秒:#非法
        raise 工作树错误('工作树：'+键+' 必须是不超过 '+str(定时器延迟上限毫秒)+' 的正整数')#给人看的说明
    return int(值)#收成整数

def 融合两路(寿命信号,调用信号):
    '谁先中止就把原因交给融合信号。返回信号，以及创建结束时要调用的停止函数'
    融合=中止控制器()#融合控制器
    停止=threading.Event()#创建结束后停监听
    if 寿命信号.is_set():#服务已拆除
        融合.中止(getattr(寿命信号,'原因',None))#拆除原因
    elif 调用信号.is_set():#调用方已取消
        融合.中止(getattr(调用信号,'原因',None))#调用方原因
    else:#两路都还活着
        def 听(源):
            '这一路中止后转发原因'
            while not 停止.is_set() and not 融合.信号.is_set():#还没有胜出，创建也没结束
                if 源.is_set():#这一路到了
                    融合.中止(getattr(源,'原因',None))#转发
                    return#结束
                if 停止.wait(0.05):#创建结束或再等一拍
                    return#结束
        启动守护线程(听,寿命信号)#听拆除
        启动守护线程(听,调用信号)#听调用方
    def 停止融合():
        '创建结束后不再听这两路'
        停止.set()#叫醒监听
    return 融合.信号,停止融合#信号与停止函数

def 解析配置(配置值):
    '补上缺省，并按服务构造时的规则拒绝非法配置'
    if 配置值 is None:#纤程没给配置
        配置值={}#空配置
    if not isinstance(配置值,dict):#不是对象
        raise 工作树错误('工作树：配置必须是对象')#拒绝
    目录=读取配置(配置值,'directory',默认目录)#检出池
    if not 是相对路径(目录):#必须是相对目录
        raise 工作树错误('工作树：directory 必须是不含点段的相对目录')#拒绝
    名称前缀=读取配置(配置值,'namePrefix',默认名称前缀)#自动名称前缀
    if not isinstance(名称前缀,str) or 名称前缀.startswith('-') or not 是相对路径(名称前缀+'name'):#前缀不能构成相对分支
        raise 工作树错误('工作树：namePrefix 必须能生成相对分支名')#拒绝
    已解析={#完整配置
        'directory':目录,#检出池
        'namePrefix':名称前缀,#名称前缀
    }#字符串部分
    for 键,缺省 in (('gitCommand',默认git命令),('nodeCommand',默认node命令)):#两个可执行名
        命令=读取配置(配置值,键,缺省)#命令
        if not isinstance(命令,str) or len(命令.strip())==0:#空白
            raise 工作树错误('工作树：'+键+' 不能为空')#拒绝
        已解析[键]=命令#保留原文，只拒绝空白
    缺省整数={'timeoutMs':默认超时毫秒,'graceMs':默认宽限毫秒,'maxOutputBytes':默认输出字节}#整数缺省
    for 键 in 整数键:#三个限额
        已解析[键]=要求正整数(键,读取配置(配置值,键,缺省整数[键]))#校验
    return 已解析#完整配置

class 配置模式:
    '供纤程在启动前调用的配置校验'
    def 校验数据(自身,数据=None):
        '缺省补齐并拒绝非法配置，返回完整配置'
        return 解析配置(数据)#归一化

class 工作树服务(服务):
    '在已挂载的文件系统与沙箱下创建保留的 Git 工作树，成功后才进入它'
    def __init__(自身,上下文,配置值=None):
        '校验配置，以 worktrees 登记，并在拆除时中止在途创建'
        super().__init__(上下文,'worktrees')#服务名 worktrees
        自身.配置=解析配置(配置值)#完整限额与路径
        自身.上下文=上下文#本插件上下文；服务查找走这里，不走没有声明这些依赖的调用方
        自身.寿命=中止控制器()#服务寿命
        自身.锁=threading.Lock()#保护在途集合
        自身.在途=set()#尚未结束的创建
        def 寿命效果():
            '拆除时中止并等到在途创建结束'
            def 拆除():
                '中止寿命信号并等待每一笔在途创建'
                自身.寿命.中止(工作树错误('工作树服务已拆除'))#后来的创建会看见这个原因
                with 自身.锁:#抄一份再等，避免边等边改集合
                    门列表=list(自身.在途)#当前在途
                for 门 in 门列表:#逐个等待
                    门.wait()#创建结束
            return 拆除#拆除器
        上下文.副作用(寿命效果,'worktrees.lifetime()')#随插件拆除

    def 创建(自身,智能体,请求=None,信号=None):
        '在钉住的本地修订上新建分支与检出，然后进入它。已有分支或路径会失败'
        停止融合=None#创建结束后停掉融合监听
        if 信号 is None:#只有服务寿命
            操作信号=自身.寿命.信号#拆除即取消
        else:#调用方与寿命，谁先中止谁生效
            操作信号,停止融合=融合两路(自身.寿命.信号,信号)#融合
        抛出若已中止(操作信号)#开始前
        门=threading.Event()#这笔创建的结束门
        with 自身.锁:#登记在途
            自身.在途.add(门)#拆除时会等它
        try:#结束时摘掉
            return 自身.创建检出(智能体,自身.解析请求(请求),操作信号)#创建并进入
        finally:#无论成败都结束这笔
            if 停止融合 is not None:#有融合监听
                停止融合()#停掉
            门.set()#叫醒拆除
            with 自身.锁:#摘掉
                自身.在途.discard(门)#不再等待

    def 解析请求(自身,请求):
        '缺省名称用前缀加 UUID，缺省修订用 HEAD'
        if 请求 is None:#缺省空请求
            请求={}#空请求
        if not isinstance(请求,dict):#不是对象
            raise 工作树错误('工作树请求必须是对象')#拒绝
        if 'name' in 请求 and 请求['name'] is not None:#调用方给了名称
            分支=请求['name']#新分支，也是检出目录名
        else:#生成名称
            分支=自身.配置['namePrefix']+str(uuid.uuid4())#前缀加 UUID
        if not isinstance(分支,str) or not 是相对路径(分支) or 分支.startswith('-'):#不是相对分支名
            raise 工作树错误('工作树名称必须是相对 Git 分支名')#拒绝
        if 'from' in 请求 and 请求['from'] is not None:#调用方给了修订
            修订=请求['from']#本地提交、分支或标签
        else:#缺省当前头
            修订='HEAD'#不抓取
        if not isinstance(修订,str) or len(修订)==0:#空修订
            raise 工作树错误('工作树 from 必须是本地提交、分支或标签')#拒绝
        return {'branch':分支,'revision':修订}#规格

    def 创建检出(自身,智能体,规格,信号):
        '解析源仓库、拒绝已有分支与路径，再在沙箱里分配目录并检出'
        上下文=自身.上下文#本服务注入的文件系统、沙箱、子进程与工作目录
        当前目录=上下文.workingDirectory.ensure(智能体,信号)#当前目录；目录消失时回到原项目
        政策=上下文.sandboxPolicy.解析({'session':智能体.session})#这次调用的文件政策
        def 跑git(目录,参数,允许退出码=None,环境=None):
            '带上关闭钩子与文件系统监视的 git 参数'
            return 运行命令(#有界 git
                上下文,自身.配置,政策,目录,
                [自身.配置['gitCommand'],'--no-lazy-fetch','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false']+list(参数),
                信号,允许退出码,环境,
            )#跑完
        跑git(当前目录,['check-ref-format','refs/heads/'+规格['branch']])#分支名必须是合法引用
        根输出=跑git(当前目录,['rev-parse','--show-toplevel'])#源检出根
        顶层=根输出['stdout']#可能带一行换行
        if 顶层.endswith('\r\n'):#Windows 换行
            顶层=顶层[:-2]#去掉这一行
        elif 顶层.endswith('\n'):#Unix 换行
            顶层=顶层[:-1]#去掉这一行
        根目标=上下文.fs.解析(顶层,{'cwd':当前目录,'signal':信号})#稳定目标
        仓库根=上下文.fs.进程路径(根目标)#执行世界中的仓库根
        基线=跑git(仓库根,['rev-parse','--verify','--end-of-options',规格['revision']+'^{commit}'])#钉住提交
        基线提交=基线['stdout'].strip()#提交对象名
        已有=跑git(仓库根,['show-ref','--verify','--quiet','refs/heads/'+规格['branch']],[0,1])#0 表示分支已存在
        if 已有['exitCode']==0:#已有同名分支
            raise 工作树错误('工作树分支已存在：'+规格['branch'])#不覆盖
        池目标=上下文.fs.解析(自身.配置['directory'],{'cwd':仓库根,'signal':信号})#检出池
        池路径=上下文.fs.进程路径(池目标)#执行世界中的池
        目的目标=上下文.fs.解析(规格['branch'],{'cwd':池路径,'signal':信号})#新检出
        路径=上下文.fs.进程路径(目的目标)#执行世界中的检出路径
        if 上下文.fs.链接状态(路径,None,信号) is not None:#路径已经存在
            raise 工作树错误('工作树路径已存在')#不覆盖
        try:#分配、检出、禁用过滤器，成功后才进入
            运行命令(#沙箱内独占建目录
                上下文,自身.配置,政策,仓库根,
                [自身.配置['nodeCommand'],'--input-type=module','-e',准备目录脚本,池路径,路径],
                信号,
            )#目录分配结束
            跑git(仓库根,['--work-tree',仓库根,'worktree','add','--no-checkout','-b',规格['branch'],'--',路径,基线提交])#登记工作树，先不检出
            已配置=跑git(路径,['config','--null','--name-only','--get-regexp','^filter\\.'],[0,1])#列出过滤器键；没有则退出码 1
            驱动=set()#需要关掉的过滤器名
            for 键 in 已配置['stdout'].split('\0'):#以空字节分隔
                分隔=键.rfind('.')#属性名前的点
                if 分隔>len('filter.') and 键[分隔+1:] in ('clean','smudge','process','required'):#四个会跑外部程序的属性
                    驱动.add(键[len('filter.'):分隔])#过滤器名
            覆盖={'GIT_CONFIG_COUNT':str(len(驱动)*4)}#每个过滤器四条临时配置，不改仓库配置
            下标=0#配置序号
            for 驱动名 in 驱动:#逐个过滤器
                for 属性 in ('clean','smudge','process','required'):#清掉外部过滤
                    覆盖['GIT_CONFIG_KEY_'+str(下标)]='filter.'+驱动名+'.'+属性#键
                    覆盖['GIT_CONFIG_VALUE_'+str(下标)]='false' if 属性=='required' else ''#required 为假，其余清空
                    下标+=1#下一对
            跑git(路径,['--work-tree',路径,'reset','--hard','--no-recurse-submodules',基线提交],None,覆盖)#检出钉住的提交
            规范路径=上下文.workingDirectory.set(智能体,路径,信号)#成功后才成为当前目录
            return 创建结果(规范路径,规格['branch'],基线提交,仓库根)#线协议结果
        except Exception as 错误:#分配或检出失败；不自动删除已创建的分支与目录
            文本=getattr(错误,'message',None)#已有给人看的说明
            if not isinstance(文本,str):#没有 message
                文本=str(错误)#字符串化
            raise 工作树错误('未能完成工作树 '+规格['branch']+'。已创建的检出和分支会保留。'+文本) from 错误#保留现场

__all__=['工作树服务','工作树错误','创建请求字段','创建结果字段','解析配置']#公开面；框架槽不入表

def 应用(上下文,配置值=None):
    '构造并登记工作树服务'
    return 工作树服务(上下文,配置值)#类插件同一构造

名称='worktree'#Cordis 插件名
依赖=['workingDirectory','fs','subprocess','sandbox','sandboxPolicy']#工作目录、文件系统、子进程、沙箱与政策
配置=配置模式()#启动前校验

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=工作树服务#框架槽；加载器把类当插件
工作树服务.name=名称#类插件显示名
工作树服务.inject=依赖#类插件依赖
工作树服务.Config=配置#类插件配置

'一个会话的有效目录、耐久变更，以及给模型的当前目录上下文'
import os,threading,weakref#路径判定、同会话串行、会话弱表
from ...基础设施.通用工具 import 紧凑json编码#模型可见路径的 JSON 引用
from ...依赖.cordis.服务 import 服务#服务基类
from ...模型后端.llm import 创建用户消息#目录变更通知

包名='@deepseek-ai/dsh-working-directory'
名称='working-directory'
依赖=['fs','sessionProjections','systemPrompt']#文件系统、投影、系统提示词
__all__=['包名','名称','依赖','应用','默认','工作目录服务','工作目录错误']

class 工作目录错误(Exception):
    '工作目录拒绝的配置、空路径或不存在的目录'
    def __init__(自身,消息,请求路径=None):
        '请求路径只作属性，不进入消息文本'
        super().__init__(消息)#消息
        自身.请求路径=请求路径#调用方自取；消息里不放路径

class 工作目录配置:
    '加载器配置。缺省收成空对象并交回，绝对路径由构造器判定'
    def 校验数据(自身,数据=None):
        'None 变成空对象，使省略配置仍能用启动目录'
        if 数据 is None:#未给配置
            return {}#空对象
        if not isinstance(数据,dict):#不是对象
            raise 工作目录错误('工作目录配置必须是对象')#拒绝
        return dict(数据)#交回副本

配置模式=工作目录配置()#框架 Config 槽的值

class 中止信号(threading.Event):
    '本服务寿命通道。Event 本身就是信号'
    def __init__(自身):
        '创建未中止的通道'
        super().__init__()#未置位
        自身.原因=None#中止时抛出的异常

class 中止控制器:
    '发出本服务寿命中止'
    def __init__(自身):
        '创建配套信号'
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):
        '只生效一次'
        if 自身.信号.is_set():#已经中止
            return#只生效一次
        自身.信号.原因=原因#记下原因
        自身.信号.set()#置位

class 合并信号:
    '寿命通道与调用方通道。文件系统只轮询 is_set，不订阅中止'
    def __init__(自身,寿命,调用方):
        '寿命在前：两边都已中止时先抛服务拆除'
        自身._寿命=寿命#服务寿命
        自身._调用方=调用方#本次调用

    def is_set(自身):
        '任一路已置位'
        if 自身._寿命 is not None and 自身._寿命.is_set():#寿命已中止
            return True#已中止
        return 自身._调用方 is not None and 自身._调用方.is_set()#调用方

    @property
    def 原因(自身):
        '已中止那一路的原因；寿命优先'
        if 自身._寿命 is not None and 自身._寿命.is_set():#寿命已中止
            return getattr(自身._寿命,'原因',None)#寿命原因
        if 自身._调用方 is not None and 自身._调用方.is_set():#调用方已中止
            return getattr(自身._调用方,'原因',None)#调用方原因
        return None#未中止

def 若已中止则抛出(信号):
    '已中止则抛出承载原因；没有异常原因时抛工作目录错误'
    if 信号 is None or not 信号.is_set():#无信号或仍活着
        return#仍活着
    原因=getattr(信号,'原因',None)#承载
    if isinstance(原因,BaseException):#已是异常
        raise 原因#原样抛出
    raise 工作目录错误('工作目录操作已中止')#没有可抛的原因

def 校验绝对目录(状态):
    '投影只接受空值或非空绝对路径，拒绝值不写进消息'
    if 状态 is None:#尚未记录
        return None#空值合法
    if isinstance(状态,str) and len(状态)>0 and os.path.isabs(状态):#非空绝对路径
        return 状态#原样
    raise ValueError('工作目录投影必须是非空绝对路径或空值')#拒绝

def 解析回退目录(配置值):
    '省略 defaultDirectory 时用进程启动目录；给出的值必须已是绝对路径'
    if 配置值 is None or 'defaultDirectory' not in 配置值 or 配置值['defaultDirectory'] is None:#省略
        return os.getcwd()#启动目录
    目录=配置值['defaultDirectory']#配置值
    if not isinstance(目录,str) or not os.path.isabs(目录):#不是绝对路径
        raise 工作目录错误('工作目录：defaultDirectory 必须是绝对路径')#拒绝
    return 目录#采用

class 工作目录服务(服务):
    '一个会话的有效目录。变更写入会话日志，并在下一次请求里告诉模型'
    def __init__(自身,上下文,配置值):
        '登记投影、当前目录上下文，以及拆除时中止在途操作'
        回退=解析回退目录(配置值)#先判定回退，失败则不登记服务
        super().__init__(上下文,'workingDirectory')#服务名
        自身.默认目录=回退#无记录时的回退
        自身._寿命=中止控制器()#拆除时中止
        自身._待定=weakref.WeakKeyDictionary()#会话到锁
        自身._表锁=threading.Lock()#建锁
        自身._条件=threading.Condition()#等在途操作
        自身._进行中=0#在途计数
        自身._进行中线程=set()#在途线程

        def 初始目录(头):
            '头里没有 cwd 时投影为空，不把回退目录写进状态'
            if 'cwd' not in 头 or 头['cwd'] is None:#头未记录
                return None#空
            return 头['cwd']#原项目

        def 折叠目录(状态,事件):
            '只有目录变更事件推进状态，其余事件保持原对象'
            if 事件['type']=='working-directory/change':#目录变更
                return 事件['data']['cwd']#新目录
            return 状态#原对象

        def 视图目录(状态):
            '主机状态即客户端视图'
            return 状态#原样

        自身.所属上下文.sessionProjections.登记({
            'key':'workingDirectory',#投影键
            'stateVersion':1,#状态版本
            'stateSchema':校验绝对目录,#主机校验
            'init':初始目录,#初始
            'apply':折叠目录,#折叠
            'wire':{'viewSchema':校验绝对目录,'view':视图目录},#视图
        })#登记投影

        def 目录文本(组装上下文):
            '没有智能体时不贡献文本'
            智能体=组装上下文['agent'] if 'agent' in 组装上下文 else None#智能体
            if 智能体 is None:#无会话
                return ''#空文本
            return 自身._上下文文本(智能体.session)#当前目录

        自身.所属上下文.systemPrompt.上下文({
            'name':'working-directory:current',#上下文名
            'order':自身.所属上下文.systemPrompt.获取上下文顺序('WORKING_DIRECTORY'),#中央顺序
            'required':True,#抑制运行时上下文时仍应留下
            'interpolate':False,#路径按字面量，不插值
            'text':目录文本,#文本
        })#登记上下文
        自身.所属上下文.监听('system-prompt/assemble',自身._组装时,{'前置':True})#先确保目录再让后续监听器看见

        def 寿命效果():
            '拆除时中止寿命，并等其他线程的在途操作结束'
            def 拆除():
                '本线程若正在操作里，不等自己，避免拆卸卡住'
                自身._寿命.中止(工作目录错误('工作目录服务已拆除'))#中止在途
                本线程=threading.get_ident()#拆除线程
                with 自身._条件:
                    while True:
                        他人=自身._进行中#在途
                        if 本线程 in 自身._进行中线程:#含自己
                            他人-=1#排除自己
                        if 他人<=0:#没有其他线程
                            return#结束
                        自身._条件.wait()#等其他人结束
            return 拆除#拆除器
        自身.所属上下文.副作用(寿命效果,'workingDirectory.lifetime')#插件寿命

    def 取当前目录(自身,会话):
        '不做文件系统访问。没有已提交记录时用部署回退目录'
        状态=自身.所属上下文.sessionProjections.状态(会话,'workingDirectory')#已提交
        if 状态 is None:#尚未记录
            return 自身.默认目录#回退
        return 状态#已提交目录

    def ensure(自身,智能体,信号=None):
        '目录还在时返回已记录路径，不换成规范进程路径。消失时先提交回到原项目。投影仍为空时补记一条变更'
        def 动作(控制):
            '在串行临界区内确保'
            return 自身._确保(智能体,控制)#确保
        return 自身._串行(智能体,信号,动作)#同会话串行

    def set(自身,智能体,路径,信号=None):
        '返回前提交规范绝对路径。相对路径按当前目录解析。已有进程各自保留自己的目录'
        def 动作(控制):
            '在串行临界区内切换'
            return 自身._切换(智能体,路径,控制)#切换
        return 自身._串行(智能体,信号,动作)#同会话串行

    def _确保(自身,智能体,控制):
        '目录还在则可能补记；否则提交恢复后的原项目'
        当前=自身.取当前目录(智能体.session)#已记录或回退
        目标=自身.所属上下文.fs.解析(当前,{'signal':控制})#解析当前
        信息=自身.所属上下文.fs.状态(目标,控制)#元数据
        若已中止则抛出(控制)#读完后再看取消
        智能体.ctx.纤程.断言活动()#智能体纤程仍在
        if 信息 is not None and 信息['type']=='directory':#仍是目录
            if 自身.所属上下文.sessionProjections.状态(智能体.session,'workingDirectory') is None:#还没提交过
                智能体.session.追加('working-directory/change',{'cwd':当前})#把回退记成已提交
            return 当前#已记录路径
        头=智能体.session.header#会话头
        if 'cwd' not in 头 or 头['cwd'] is None:#头没有原项目
            原始=自身.默认目录#回退
        else:#有原项目
            原始=头['cwd']#原项目
        已恢复=自身._要求目录(原始,原始,控制)#原项目必须存在
        自身._提交(智能体,已恢复,True,控制)#先提交再返回
        return 已恢复#规范路径

    def _切换(自身,智能体,路径,控制):
        '空 cd 拒绝；其余交给目录存在性检查'
        if len(路径)==0:#空字符串
            raise 工作目录错误('工作目录：cd 不能为空')#拒绝
        目录=自身._要求目录(路径,自身.取当前目录(智能体.session),控制)#相对当前目录
        自身._提交(智能体,目录,False,控制)#先提交再返回
        return 目录#规范路径

    def _上下文文本(自身,会话):
        '模型读这句，措辞固定'
        return f'Current working directory: {紧凑json编码(自身.取当前目录(会话))}.'#当前目录

    def _要求目录(自身,路径,当前目录,信号):
        '解析后必须是已存在的目录，返回执行世界的规范路径'
        目标=自身.所属上下文.fs.解析(路径,{'cwd':当前目录,'signal':信号})#相对当前目录
        信息=自身.所属上下文.fs.状态(目标,信号)#元数据
        若已中止则抛出(信号)#读完后再看取消
        if 信息 is None or 信息['type']!='directory':#缺失或不是目录
            raise 工作目录错误('工作目录：目录不存在',路径)#不把路径写入消息
        return 自身.所属上下文.fs.进程路径(目标)#规范进程路径

    def _提交(自身,智能体,目录,已恢复,信号):
        '目录没变则不写事件。通知入队失败只警告，不回滚已追加的变更'
        若已中止则抛出(信号)#提交前
        智能体.ctx.纤程.断言活动()#智能体纤程仍在
        先前=自身.取当前目录(智能体.session)#提交前的有效目录
        if 先前==目录:#没有变化
            return#不写事件、不通知
        智能体.session.追加('working-directory/change',{'cwd':目录})#先提交
        先前引=紧凑json编码(先前)#模型可见引用
        目录引=紧凑json编码(目录)#模型可见引用
        if 已恢复:#原目录不可用
            文本=f'The working directory {先前引} is unavailable. The working directory is now {目录引}.'#恢复通知
        else:#主动切换
            文本=f'The working directory changed from {先前引} to {目录引}.'#切换通知
        通知=创建用户消息({
            'content':[{'type':'text','text':文本}],#通知正文
            'source':{'kind':'working-directory'},#来源种类
        })#用户消息
        try:#通知失败不影响已提交目录
            智能体.注入(通知)#下一步注入，不唤醒
        except Exception as 错误:#注入的失败类型不固定；已追加的目录事件不回滚
            自身.所属上下文.日志.警告(f'工作目录已提交，但无法排队其通知：{type(错误).__name__}: {错误}')#警告

    def _组装时(自身,_装配,上下文载荷,下一步):
        '先确保目录，再让瀑布继续；回来后用已提交目录覆盖或补上当前目录上下文'
        智能体=上下文载荷['agent'] if 'agent' in 上下文载荷 else None#智能体
        if 智能体 is None:#无会话
            return 下一步()#不改组装
        信号=上下文载荷['signal'] if 'signal' in 上下文载荷 else None#本次组装的取消
        自身.ensure(智能体,信号)#确保在后续监听器之前
        装配=下一步()#其余瀑布
        若已中止则抛出(自身._寿命.信号)#只认服务寿命，不认本次调用信号
        文本=自身._上下文文本(智能体.session)#确保之后的目录
        贡献=None#已有条目
        for 条目 in 装配['contexts']:#按名找
            if 条目['name']=='working-directory:current':#当前目录上下文
                贡献=条目#命中
                break#停止
        if 贡献 is None:#瀑布拿掉了
            装配['contexts'].insert(0,{'name':'working-directory:current','text':文本,'interpolate':False})#补回最前
        else:#改成确保之后的文本
            贡献['text']=文本#覆盖
            贡献['interpolate']=False#不插值
        return 装配#权威组装

    def _串行(自身,智能体,信号,动作):
        '同一会话的目录操作不交错。锁不可重入。在途计数在拿到锁之后才加，避免拆除线程持锁等待尚未进临界区的排队者'
        控制=自身._控制信号(信号)#寿命加调用方
        锁=自身._会话锁(智能体.session)#该会话的锁
        线程=threading.get_ident()#当前线程
        已计入=False#是否已进入在途账
        with 锁:#同会话排队
            with 自身._条件:
                自身._进行中+=1#进入临界区后才计入
                自身._进行中线程.add(线程)#记下线程
                已计入=True#销账只针对已计入的
            try:#临界区内失败也要销账
                若已中止则抛出(控制)#轮到时已取消则不做
                智能体.ctx.纤程.断言活动()#智能体纤程仍在
                return 动作(控制)#执行
            finally:#先销账再释放会话锁
                if 已计入:#已进入在途账
                    with 自身._条件:
                        自身._进行中-=1#离开
                        自身._进行中线程.discard(线程)#摘掉线程
                        自身._条件.notify_all()#拆除侧重查

    def _控制信号(自身,信号):
        '没给调用方信号时只看服务寿命'
        if 信号 is None:#未给
            return 自身._寿命.信号#只看寿命
        return 合并信号(自身._寿命.信号,信号)#两路

    def _会话锁(自身,会话):
        '每个会话一把锁，会话回收后锁一并消失'
        with 自身._表锁:#建锁互斥
            锁=自身._待定.get(会话)#已有
            if 锁 is None:#第一次
                锁=threading.Lock()#新锁
                自身._待定[会话]=锁#记下
            return 锁#该会话的锁

def 应用(上下文,配置值):
    '注册 workingDirectory 服务'
    工作目录服务(上下文,配置值)#构造即登记

默认=工作目录服务
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置模式#框架槽
default=默认#框架槽
工作目录服务.inject=依赖#框架槽
工作目录服务.Config=配置模式#框架槽
工作目录服务.name=名称#框架槽

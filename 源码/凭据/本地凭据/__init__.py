"""以 `$DSH_HOME/.credentials.yaml` 为文件后端的凭证提供方，按各层受信任程度叠在环境之上：

```text
inherited process environment      (read-only, wins)
> $DSH_HOME/.credentials.yaml      (provider-managed, writable)
> <invocation cwd>/.env            (read-only fallback)
> $DSH_HOME/.env                   (read-only fallback)
```

继承来的进程环境胜出，因为 `DEEPSEEK_API_KEY=… dsh`、CI 密钥或容器 `-e` 是本次运行的显式意图；内部无法编辑它，所以必须*看得见地*只读，而不是静默遮蔽写入。它下面的一切都输给托管存储，因此模型页写入的密钥会立刻生效，即使用户 `.env` 里还躺着旧密钥。

启动项目可以提供密钥，因为产品信任它所启动的项目。它排在托管存储之下，因此通过模型页存入的密钥不会被某次检出碰巧带着的密钥顶掉。

该文件是提供方管理的可写源：每次写入都在跨进程写锁下先重读文档，再只补丁自己的键——注释和所有未触碰条目的格式得以保留——外部编辑经能力缝热发布；每次重载整份替换快照，已删条目绝不会留在内存里。

文档只装凭证，所以它是严格的 CredentialRef 到字符串映射，而不是 dotenv 文件：Harness 拥有、且从不物化进环境的存储，不能同时充当用户的环境层；若它兼作环境层，会把非密钥条目挡在自己的优先级后面，让它们静默不可达。
"""
import os,threading#路径与操作链线程
from ...依赖 import cordis,schemastery#外部依赖胶水
模式=schemastery.模式#配置校验
服务=cordis.服务#服务初始化符号
已兑现=cordis.工具.已兑现#操作链已兑现
承诺=cordis.工具.承诺#操作链承诺
from ..凭据 import 凭证提供方,凭证引用#凭证提供方基类与引用品牌化
from ..原子写入 import 原子写文件,带文件锁#文件锁与原子写
from ..工作区路径 import 规范化监视路径,解析主目录#监视路径规范化与主目录解析
from ..启动环境 import 取启动环境#启动环境读取
from .文档 import 凭证文件名,解析凭证文档,渲染文档,断言仅所有者,是否缺席,读文档文本#文档解析与权限
from .监视 import 监视#文档热重载监视
互斥锁=threading.Lock#链尾互斥
工作线程=threading.Thread#操作线程

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '配置模式','取字段','试取','解析规格','本地凭证提供方','默认',
]#公开面结束

配置模式=模式.对象({#插件配置字段
    'path':模式.字符串(),#可选文档路径
    'dshHome':模式.字符串(),#可选 harness 主目录
    'watch':模式.布尔().默认(True),#默认监视
    'debounceMs':模式.数字().最小(0).默认(100),#默认稳定窗口
})#插件配置模式

def 取字段(对象,键):#读取映射或对象上的字段
    """读取映射或对象上的字段。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#按键
    return getattr(对象,键)#按属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    if isinstance(对象,dict):#映射
        return 对象.get(键)#按键
    return getattr(对象,键,None)#按属性

def 解析规格(配置):#把配置收成运行时规格
    """从插件配置解析运行时规格：显式 `path` 胜出，否则文档位于 harness 主目录下的 `.credentials.yaml`。默认值在这里给出，绝不内联。"""
    路径=试取(配置,'path')#显式文档路径
    主目录=试取(配置,'dshHome')#可选 harness 主目录
    监视开关=试取(配置,'watch')#是否监视
    防抖毫秒=试取(配置,'debounceMs')#写入稳定窗口
    if 监视开关 is None:#默认开启监视
        监视开关=True#默认 true
    if 防抖毫秒 is None:#默认 100ms
        防抖毫秒=100#默认稳定窗口
    if 路径 is None:#文档位于主目录
        文件名=os.path.abspath(os.path.join(解析主目录(主目录),凭证文件名))#主目录下默认文件
    else:
        文件名=os.path.abspath(路径)#显式路径胜出
    return {'filename':文件名,'watch':监视开关,'debounceMs':防抖毫秒}#运行时规格

class 本地凭证提供方(凭证提供方):#本地文件凭证提供方
    """以文件为后端的凭证提供方（`$DSH_HOME/.credentials.yaml`）。"""
    Config=配置模式#插件配置模式
    def __init__(自身,ctx,配置):#构造本地提供方
        """用上下文与配置构造本地提供方。编程式构造可能绕过 Schemastery 归一化；无论哪条路径都在这一步显式解析同一套默认值。"""
        super().__init__(ctx)#登记 credentials 服务
        自身.config=配置#原始插件配置
        自身.配置=配置#中文别名
        自身.规格=解析规格(配置)#解析运行时规格
        # 上次读取或持久化的原始文档文本；文件缺席时为 None。
        # 内容等于这份缓存的监视事件是空操作，这也就是自我写入抑制。
        自身.文本=None#文档文本缓存（自我写入抑制用）
        自身.值表={}#已解析文档快照；每次重载整份替换
        # 单一互斥操作链：监视重载与行编辑按队列顺序一次一个（已结算尾），因此编辑绝不能从并发重载正在替换的文本里渲染。
        自身.操作链=已兑现(None)#互斥操作链
        自身.链锁=互斥锁()#更新链尾的锁
        自身.已关闭=False#拆除时置位：拒绝新写入，让飞行中的工作空操作
        自身.__dict__[服务.初始化]=自身._初始化#登记 Service.init

    def 是否已关闭(自身):#跨等待读取关闭标志
        """`已关闭` 的不透明读取：控制流无法把它收窄过等待点。"""
        return 自身.已关闭#返回当前关闭状态

    def _初始化(自身):#服务生命周期
        """登记拆除排水，启动时读盘，可选地监视外部编辑。"""
        def 排水():#拒绝新操作并结算已排队的
            """排水：拒绝新操作，再结算已排队的，只有存储静止后拆除才完成。"""
            自身.已关闭=True#拒绝新写入
            with 自身.链锁:#读取链尾
                尾=自身.操作链#当前链尾
            尾.等待()#等操作链静止
        yield 排水#登记拆除排水
        自身.启动读取()#启动时读盘
        if not 自身.规格['watch']:#未开监视则到此为止
            return#无监视器
        稳定=自身.规格['debounceMs']#稳定窗口
        监视器=监视(规范化监视路径(自身.规格['filename']),{
            'ignoreInitial':True,#忽略初始扫描
            'awaitWriteFinish':{
                'stabilityThreshold':稳定,#稳定窗口
                'pollInterval':max(1,min(稳定,10)),#轮询间隔夹在 1 与窗口之间且不超过 10
            },#写入稳定配置结束
        })#创建监视器
        def 收到全部(*位置参数):#任意文件系统事件
            """任意文件系统事件。"""
            if 自身.已关闭:#已关闭则忽略
                return#忽略
            自身.排队刷新()#排队重载
        def 收到就绪(*位置参数):#监视器就绪
            """初始读取与监视器自身启动竞态：那次读取与监视器生效之间写入的变更不会再发火。就绪时再对一次账，补上缺口。"""
            if 自身.已关闭:#已关闭则忽略
                return#忽略
            # 初始读取与监视器自身启动竞态：那次读取与监视器生效之间写入的变更不会再发火。就绪时再对一次账，补上缺口。
            自身.排队刷新()#就绪时再对账一次
        def 收到错误(错误):#监视出错
            """监视出错。"""
            自身.ctx.logger.warn('credentials-local: watcher error on %s',自身.规格['filename'])#警告监视失败
            自身.ctx.logger.warn(错误)#再打印错误对象
        监视器.on('all',收到全部)#all 监听结束
        监视器.on('ready',收到就绪)#ready 监听结束
        监视器.on('error',收到错误)#error 监听结束
        def 拆除监视():#监视拆除
            """静止：停止接事件，关闭监视器，再等掉已排队或飞行中的操作，使拆除后不再发布。"""
            自身.已关闭=True#拒绝新操作
            监视器.close()#关闭监视器
            with 自身.链锁:#读取链尾
                尾=自身.操作链#当前链尾
            尾.等待()#等操作链静止
        yield 拆除监视#登记监视拆除

    def 继承值(自身,引用):#读取进程环境层
        """一条引用的继承环境值；空或未设置时为 None。"""
        条目=取启动环境(自身.ctx).getFrom(引用,['process'])#只查 process 层
        if 条目 is None:#该层没有
            return None#缺席
        值=取字段(条目,'value')#层提供的值
        if 值 is not None and len(值)>0:#非空才算有
            return 值#继承值
        return None#空值当缺席

    def dotenv回退(自身,引用):#读取 dotenv 回退层
        """一条引用的 `.env` 回退——在托管存储之下，从不在其上。启动项目高于用户主目录文件，与环境分层一致：更具体的位置胜出。"""
        条目=取启动环境(自身.ctx).getFrom(引用,['project-env','user-env'])#项目 .env 再用户 .env
        if 条目 is None:#两层都没有
            return None#缺席
        值=取字段(条目,'value')#层提供的值
        if 值 is not None and len(值)>0:#非空才算有
            return 条目#回退条目
        return None#空值当缺席

    def 解析(自身,引用):#按层解析引用
        """按层解析引用。继承环境胜出，然后托管文件，最后 dotenv 回退。"""
        继承=自身.继承值(引用)#进程环境优先
        if 继承 is not None:#继承环境胜出
            return {'value':继承,'source':'env'}#只读环境层
        已存=自身.值表.get(引用)#再查托管文件
        if 已存 is not None:#文件层命中
            return {'value':已存,'source':'file'}#文件层
        回退=自身.dotenv回退(引用)#最后 dotenv 回退
        if 回退 is not None:#回退层命中
            return {'value':取字段(回退,'value'),'source':取字段(回退,'source')}#回退层
        return None#各层皆无

    def 描述(自身,引用):#描述引用而不给值
        """描述引用而不给值。只有继承环境不可写：那是本进程无法编辑的一层。用户 `.env` 值在要紧的意义上可写——存一个键就会把它替换成生效的那一个。"""
        if 自身.继承值(引用) is not None:#进程环境正在供应
            return {'configured':True,'source':'env','writable':False}#只读已配置
        已存=自身.值表.get(引用)#再查托管文件
        if 已存 is not None:#文件层可写
            return {'configured':True,'source':'file','writable':True}#文件层可写
        回退=自身.dotenv回退(引用)#再查 dotenv
        if 回退 is not None:#回退层可写
            return {'configured':True,'source':取字段(回退,'source'),'writable':True}#回退层可写
        return {'configured':False,'writable':True}#未配置但可写

    def 设置(自身,引用,值):#写入可写源
        """写入可写源。空值不得存，改用移除。"""
        if len(值)==0:#空值不得存
            raise Exception('credentials-local: an empty value cannot be stored for "'+引用+'"; use unset')#改用 unset
        自身.写入(引用,值)#排队行编辑

    def 移除(自身,引用):#删除可写源条目
        """删除可写源条目。"""
        自身.写入(引用,None)#以无值表示删键

    def 入队(自身,操作):#串行排队
        """把一次互斥文档操作排到此前所有操作之后。失败也不断链。"""
        结果=承诺()#本次结果
        新尾=承诺()#结算尾
        with 自身.链锁:#接到链尾
            前=自身.操作链#此前所有操作
            自身.操作链=新尾#更新链尾
        def 执行():#接到链尾后运行
            """接到链尾后运行本次操作。"""
            前.等待()#等前面的结算尾
            try:
                结果.兑现(操作())#本次成功
            except Exception as 错误:
                结果.拒绝(错误)#本次失败交给调用方
            新尾.兑现(None)#结算尾，失败也不断链
        工作=工作线程(target=执行)#操作线程
        工作.daemon=True#不挡住退出
        工作.start()#启动
        return 结果#把本次结果交给调用方

    def 排队刷新(自身):#排队监视重载
        """排队一次重载；只有逃出扇出的不变量违规能让它拒绝，随后记成错误并保持操作链存活。"""
        def 刷新并捕获():#重载失败不得静默停热重载
            """重载失败不得静默停热重载。"""
            try:
                自身.刷新()#监视触发的重载
            except Exception as 错误:
                自身.ctx.logger.error('credentials-local: reload commit failed at %s',自身.规格['filename'])#记录提交失败
                自身.ctx.logger.error(错误)#再打印失败对象
        自身.入队(刷新并捕获)#排队，不等待

    def 写入(自身,引用,值):#排队一次行编辑
        """排队一次行编辑；入口检查尽早拒绝，队列在运行时再判定一次。"""
        动词='unset' if 值 is None else 'set'#用于错误文案的动词
        if 自身.是否已关闭():#已拆除
            raise Exception('credentials-local is disposed: cannot '+动词+' "'+引用+'"')#拒绝新写入
        自身.断言未被遮蔽(引用,动词)#入口处拒绝会被环境遮蔽的写
        def 操作():#真正写入排进互斥链
            """真正写入排进互斥链。"""
            if 自身.是否已关闭():#排队期间可能已拆除
                raise Exception('credentials-local was disposed before the queued "'+引用+'" '+动词+' ran')#排队项作废
            自身.断言未被遮蔽(引用,动词)#运行时再判定：排队期间环境可能已变
            os.makedirs(os.path.dirname(自身.规格['filename']),exist_ok=True,mode=0o700)#写锁的独占创建需要父目录存在；0700，因为 harness 主目录装着用户私有数据
            def 持锁():#跨进程写锁内的读改写
                """读改写：并入本进程尚未观察到的盘上状态——仍在监视器防抖窗口内的外部编辑、监视器漏掉的变更、或其他进程的写入——使下面的行编辑绝不能复活一份过期文档。"""
                自身.从盘面对账()#先与盘面对账
                已有=自身.值表.get(引用)#当前是否已有该键
                if 值 is None and 已有 is None:#删一个本就不在的键是空操作
                    return None#空操作
                下一文本=渲染文档(自身.文本,引用,值)#渲染下一份文本
                原子写文件(自身.规格['filename'],下一文本,{'mode':0o600,'dirMode':0o700})#0600：装着密钥的文档绝不能全局可读
                自身.文本=下一文本#更新文本缓存
                if 值 is None:#删除则去掉快照键
                    自身.值表.pop(引用,None)#去掉快照键
                else:
                    自身.值表[引用]=值#设置则写入快照
                自身.通知已更新(引用)#提交之后：坏掉的观察者绝不能让这次持久写入看起来失败（INVARIANT 失败仍会重抛）
                return None#写入完成
            带文件锁(自身.规格['filename'],持锁)#跨进程写锁
            return None#操作完成
        自身.入队(操作).等待()#等到本次写入结算

    def 断言未被遮蔽(自身,引用,动词):#拒绝被环境遮蔽的写
        """拒绝会被继承环境遮蔽成看似无效果的写入。只有那一层能遮蔽写入：本提供方解析的其余层都排在正在写的文档之下。"""
        if 自身.继承值(引用) is not None:#进程环境正在供应
            raise Exception('credentials-local: "'+引用+'" is supplied read-only by the launching environment, so '+动词+' would be shadowed; unset it in the shell you start dsh from instead')#抛出遮蔽错误

    def 启动读取(自身):#启动读盘
        """启动读取：缺席文件是空存储；无效文件让插件激活失败，因为一份存在却不可信的凭证文档绝不能当成“没有存凭证”。不可信 ≠ 无。"""
        断言仅所有者(自身.规格['filename'])#先检查仅所有者可读（0600 / umask）
        try:#按 utf8 读文档
            文本=读文档文本(自身.规格['filename'])#按 utf8 读文档
        except Exception as 错误:#读失败
            if not 是否缺席(错误):#非缺席则原样抛出
                raise 错误#原样抛出
            return#缺席则空存储（缺席才是“无”；存在却不可信绝不能当无）
        自身.值表=解析凭证文档(文本,自身.规格['filename'])#解析进快照；无效则激活失败
        自身.文本=文本#缓存原文（供后续自我写入抑制比对）

    def 刷新(自身):#监视触发的重载
        """监视事件后重读文档。未变内容（包括本提供方自己的写入）是空操作；不可读文档保留上一份好快照并警告——活着的热重载绝不能把进程打下来。逃出扇出的不变量违规不是重载失败，会传到队列的错误面。"""
        if 自身.已关闭:#已关闭则不再发布
            return#空操作
        try:#尝试对账
            自身.从盘面对账()#按盘面发布差值
        except Exception as 错误:#对账失败
            if getattr(错误,'code',None)=='INVARIANT':#不变量失败继续抛
                raise 错误#继续抛
            自身.ctx.logger.warn('credentials-local: reload failed at %s; keeping the last good document',自身.规格['filename'])#警告并保留
            自身.ctx.logger.warn(错误)#再打印失败对象

    def 从盘面对账(自身):#与盘面对账并发布
        """把盘上文本与缓存比较，把任何差异发布进能力缝。缺席发布空存储；不可读或无效文档抛出，好让各调用方自选策略——重载警告并保留上一份好快照，写入大声失败而不是覆盖一份它读不懂的文档。"""
        # 每次重载和每次写入前再检查 mode：外部编辑器或还原的备份可能在启动后放宽权限；启动时检过一次不够。
        断言仅所有者(自身.规格['filename'])#从盘对账：再检仅所有者可读（0600 / umask）
        try:#读盘
            文本=读文档文本(自身.规格['filename'])#按 utf8 读文档
        except Exception as 错误:#读失败
            if not 是否缺席(错误):#非缺席则原样抛出
                raise 错误#原样抛出
            文本=None#缺席当成空文档
        # 未变内容（包括本提供方自己的写入）是空操作——文本缓存自我写入抑制；已关闭则不再发布。
        if 文本==自身.文本 or 自身.是否已关闭():#自我写入抑制或已关闭
            return#空操作
        下一={} if 文本 is None else 解析凭证文档(文本,自身.规格['filename'])#解析下一份快照
        变更=自身.变更引用(自身.值表,下一)#算出变更引用
        自身.文本=文本#更新文本缓存
        自身.值表=下一#整份替换快照
        for 引用 in 变更:#逐条扇出已提交变更
            自身.通知已更新(引用)#扇出

    def 变更引用(自身,先前,下一):#计算变更引用
        """存储值已变的条目；解析器已经证明每个键都可寻址。"""
        变更=[]#收集变更
        已见=set()#并集去重
        键列表=[]#保持先先前、再下一的插入序
        for 键 in list(先前.keys())+list(下一.keys()):#并集遍历
            if 键 in 已见:#已收过
                continue#跳过
            已见.add(键)#记下
            键列表.append(键)#按插入序
        for 键 in 键列表:#并集遍历
            if 先前.get(键)==下一.get(键):#值未变则跳过
                continue#跳过
            变更.append(凭证引用(键))#键已证明可品牌化
        return 变更#返回变更列表

Config=配置模式#Cordis 配置模式
默认=本地凭证提供方#默认导出
default=本地凭证提供方#Cordis 默认导出

"""以 `$DSH_HOME/.credentials.yaml` 为文件后端的凭证提供方，按各层受信任程度叠在环境之上：

```text
inherited process environment      (read-only, wins)
> $DSH_HOME/.credentials.yaml      (provider-managed, writable)
> <invocation cwd>/.env            (read-only fallback)
> $DSH_HOME/.env                   (read-only fallback)
```

继承来的进程环境胜出，因为 `DEEPSEEK_API_KEY=… dsh`、CI 密钥或容器 `-e` 是本次运行的显式意图；内部无法编辑它，所以必须*看得见地*只读，而不是静默遮蔽写入。它下面的一切都输给托管存储，因此模型页写入的密钥会立刻生效，即使用户 `.env` 里还躺着旧密钥。

启动项目可以提供密钥，因为产品信任它所启动的项目。它排在托管存储之下，因此通过模型页存入的密钥不会被某次检出碰巧带着的密钥顶掉。

文档只装凭证：版本化根下的 `refs`（CredentialRef→字符串）与 `records`（CredentialKey→记录），不是 dotenv 文件。Harness 拥有、且从不物化进环境的存储，不能同时充当用户的环境层。
"""
import os,queue,threading#路径、队列与线程
from concurrent.futures import Future as _原生Future#单次操作结果
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,布尔字段,数字字段#配置字段
服务=cordis.服务#服务初始化符号
from ..凭据 import 凭证提供方,凭证引用,解析凭证键#凭证提供方基类与键
from ...工具.原子写入 import 原子写文件,带文件锁#文件锁与原子写
from ...工具.主目录路径 import 规范化监视路径,解析主目录#监视路径规范化与主目录解析
from ...工具.启动环境 import 取启动环境#启动环境读取
from .文档 import (#文档解析与权限
    凭证文件名,文档版本,解析凭证文档,渲染扁平迁移,渲染引用,渲染记录,
    断言仅所有者,是否缺席,读文档文本,同json值,断言可存api密钥,断言json值,
)#文档面
from .监视 import 监视#文档热重载监视

class _操作任务:#本文件内单次入队结果
    """单次入队操作的 Future 包装，只留等待。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def 等待(自身,超时=None):#阻塞等待
        """阻塞等到结算。"""
        return 自身._future.result(timeout=超时)#取结果或抛错

class _串行操作链:#本文件内互斥队列
    """单工作者线程串行跑文档操作。"""
    def __init__(自身):#启动工作者
        """启动工作者线程。"""
        自身._队列=queue.Queue()#待跑操作
        自身._工作者=threading.Thread(target=自身._执行操作循环,daemon=True)#工作者
        自身._工作者.start()#启动
    def _执行操作循环(自身):#工作者循环
        """逐项执行入队操作。"""
        while True:#常驻
            结果,操作=自身._队列.get()#取下一项
            try:#跑操作
                结果.兑现(操作())#成功
            except BaseException as 错误:#失败
                结果.拒绝(错误)#拒绝
            finally:#无论成败
                自身._队列.task_done()#标记完成
    def 入队(自身,操作):#排入串行链
        """把操作排到此前所有操作之后，返回本次结果。"""
        结果=_操作任务()#本次结果
        自身._队列.put((结果,操作))#入队
        return 结果#交给调用方
    def 等待静止(自身):#排空队列
        """等到已入队操作全部跑完。"""
        自身._队列.join()#等 task_done

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '配置模式','解析规格','本地凭证提供方','默认','本地凭据错误',
]#公开面结束

配置模式={#插件配置字段
    'path':字符串字段(),#可选文档路径
    'dshHome':字符串字段(),#可选 harness 主目录
    'watch':布尔字段(默认值=True),#默认监视
    'debounceMs':数字字段(最小=0,默认值=100),#默认稳定窗口
}#插件配置模式

class 本地凭据错误(Exception):
    """本地凭证提供方失败。"""
    pass#消息在构造时传入

def 解析规格(配置):
    """从插件配置解析运行时规格：显式 `path` 胜出，否则文档位于 harness 主目录下的 `.credentials.yaml`。默认值在这里给出，绝不内联。配置为 dict。"""
    路径=配置['path'] if 配置 is not None and 'path' in 配置 else None#显式文档路径
    主目录=配置['dshHome'] if 配置 is not None and 'dshHome' in 配置 else None#可选 harness 主目录
    监视开关=配置['watch'] if 配置 is not None and 'watch' in 配置 else None#是否监视
    防抖毫秒=配置['debounceMs'] if 配置 is not None and 'debounceMs' in 配置 else None#写入稳定窗口
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
        自身.配置=配置#原始插件配置
        自身.规格=解析规格(配置)#解析运行时规格
        # 上次读取或持久化的原始文档文本；文件缺席时为 None。
        # 内容等于这份缓存的监视事件是空操作，这也就是自我写入抑制。
        自身.文本=None#文档文本缓存（自我写入抑制用）
        自身.值表={}#已解析引用快照；每次重载整份替换
        自身.记录表={}#已解析记录快照；每次重载整份替换
        # 单一互斥操作链：监视重载与行编辑按队列顺序一次一个，因此编辑绝不能从并发重载正在替换的文本里渲染。
        自身.操作链=_串行操作链()#互斥操作队列
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
            自身.操作链.等待静止()#等操作链静止
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
            自身.ctx.日志.警告('credentials-local: watcher error on %s',自身.规格['filename'])#警告监视失败
            自身.ctx.日志.警告(错误)#再打印错误对象
        监视器.on('all',收到全部)#all 监听结束
        监视器.on('ready',收到就绪)#ready 监听结束
        监视器.on('error',收到错误)#error 监听结束
        def 拆除监视():#监视拆除
            """静止：停止接事件，关闭监视器，再等掉已排队或飞行中的操作，使拆除后不再发布。"""
            自身.已关闭=True#拒绝新操作
            监视器.close()#关闭监视器
            自身.操作链.等待静止()#等操作链静止
        yield 拆除监视#登记监视拆除

    def 继承值(自身,引用):#读取进程环境层
        """一条引用的继承环境值；空或未设置时为 None。"""
        条目=取启动环境(自身.ctx).从中取(引用,['process'])#只查 process 层
        if 条目 is None:#该层没有
            return None#缺席
        值=条目['value']#层提供的值
        if 值 is not None and len(值)>0:#非空才算有
            return 值#继承值
        return None#空值当缺席

    def dotenv回退(自身,引用):#读取 dotenv 回退层
        """一条引用的 `.env` 回退——在托管存储之下，从不在其上。启动项目高于用户主目录文件，与环境分层一致：更具体的位置胜出。"""
        条目=取启动环境(自身.ctx).从中取(引用,['project-env','user-env'])#项目 .env 再用户 .env
        if 条目 is None:#两层都没有
            return None#缺席
        值=条目['value']#层提供的值
        if 值 is not None and len(值)>0:#非空才算有
            return 条目#回退条目
        return None#空值当缺席

    def 解析(自身,引用):#按层解析引用
        """按层解析引用。继承环境胜出，然后托管文件，最后 dotenv 回退。"""
        继承=自身.继承值(引用)#进程环境优先
        if 继承 is not None:#继承环境胜出
            return {'value':继承,'source':'env'}#只读环境层
        已存=自身.值表[引用] if 引用 in 自身.值表 else None#再查托管文件
        if 已存 is not None:#文件层命中
            return {'value':已存,'source':'file'}#文件层
        回退=自身.dotenv回退(引用)#最后 dotenv 回退
        if 回退 is not None:#回退层命中
            return {'value':回退['value'],'source':回退['source']}#回退层
        return None#各层皆无

    def 描述(自身,引用):#描述引用而不给值
        """描述引用而不给值。只有继承环境不可写：那是本进程无法编辑的一层。用户 `.env` 值在要紧的意义上可写——存一个键就会把它替换成生效的那一个。"""
        if 自身.继承值(引用) is not None:#进程环境正在供应
            return {'configured':True,'source':'env','writable':False}#只读已配置
        已存=自身.值表[引用] if 引用 in 自身.值表 else None#再查托管文件
        if 已存 is not None:#文件层可写
            return {'configured':True,'source':'file','writable':True}#文件层可写
        回退=自身.dotenv回退(引用)#再查 dotenv
        if 回退 is not None:#回退层可写
            return {'configured':True,'source':回退['source'],'writable':True}#回退层可写
        return {'configured':False,'writable':True}#未配置但可写

    def 设置(自身,引用,值):#写入可写源
        """写入可写源。空值不得存，改用移除。"""
        if len(值)==0:#空值不得存
            raise 本地凭据错误('credentials-local: an empty value cannot be stored for "'+引用+'"; use unset')#改用 unset
        自身.写入(引用,值)#排队行编辑

    def 移除(自身,引用):#删除可写源条目
        """删除可写源条目。"""
        自身.写入(引用,None)#以无值表示删键

    def 读记录(自身,键):
        """读一条已存记录；未存时为 None。"""
        return 自身.记录表[键] if 键 in 自身.记录表 else None#快照

    def 描述记录(自身,键):
        """为配置面描述一条记录，不暴露其值。"""
        已存=自身.读记录(键)#读
        if 已存 is None:#未存
            return {'configured':False,'writable':True}#未配置
        return {'configured':True,'kind':已存['kind'],'writable':True}#已存

    def 列举记录(自身):
        """枚举每条已存记录的地址与标签。"""
        return [{'key':解析凭证键(键),'kind':记录['kind']} for 键,记录 in 自身.记录表.items()]#条目

    def 修改记录(自身,键,变更):
        """对一条记录的读-改-写，持久进 versioned records 节。"""
        if 自身.是否已关闭():#已拆除
            raise 本地凭据错误('credentials-local is disposed: cannot modify "'+键+'"')#拒绝
        def 操作():
            """真正修改排进互斥链。"""
            if 自身.是否已关闭():#排队期间拆除
                raise 本地凭据错误('credentials-local was disposed before the queued "'+键+'" modify ran')#拒绝
            os.makedirs(os.path.dirname(自身.规格['filename']),exist_ok=True,mode=0o700)#父目录
            def 持锁():
                """持锁读改写。"""
                自身.从盘面对账()#对账
                当前=自身.记录表.get(键)#当前
                下一份=变更(当前)#决策
                if 下一份 is None:#不动
                    return 当前#当前
                if 下一份['kind']=='grant':#grant
                    断言json值('record "'+键+'" payload',下一份['payload'],set())#载荷
                else:
                    断言可存api密钥(键,下一份)#api-key
                下一文本=渲染记录(自身.文本,键,下一份)#渲染
                原子写文件(自身.规格['filename'],下一文本,{'mode':0o600,'dirMode':0o700})#写
                自身.文本=下一文本#缓存
                自身.记录表[键]=下一份#快照
                自身.通知记录已更新(键)#扇出
                return 下一份#新
            return 带文件锁(自身.规格['filename'],持锁)#持锁
        return 自身.入队(操作).等待()#等到

    def 删除记录(自身,键):
        """移除一条记录；本就不存在则为空操作。"""
        if 自身.是否已关闭():#已拆除
            raise 本地凭据错误('credentials-local is disposed: cannot delete "'+键+'"')#拒绝
        def 操作():
            """真正删除排进互斥链。"""
            if 自身.是否已关闭():#排队期间拆除
                raise 本地凭据错误('credentials-local was disposed before the queued "'+键+'" delete ran')#拒绝
            os.makedirs(os.path.dirname(自身.规格['filename']),exist_ok=True,mode=0o700)#父目录
            def 持锁():
                """持锁删除。"""
                自身.从盘面对账()#对账
                if 键 not in 自身.记录表:#本就不在
                    return None#空
                下一文本=渲染记录(自身.文本,键,None)#渲染删
                原子写文件(自身.规格['filename'],下一文本,{'mode':0o600,'dirMode':0o700})#写
                自身.文本=下一文本#缓存
                自身.记录表.pop(键,None)#快照
                自身.通知记录已更新(键)#扇出
                return None#完成
            带文件锁(自身.规格['filename'],持锁)#持锁
            return None#完成
        自身.入队(操作).等待()#等到

    def 入队(自身,操作):#串行排队
        """把一次互斥文档操作排到此前所有操作之后。"""
        return 自身.操作链.入队(操作)#队列串行

    def 排队刷新(自身):#排队监视重载
        """排队一次重载；只有逃出扇出的不变量违规能让它拒绝，随后记成错误并保持操作链存活。"""
        def 刷新并捕获():#重载失败不得静默停热重载
            """重载失败不得静默停热重载。"""
            try:#监视触发的重载
                自身.刷新()#重载
            except Exception as 错误:#刷新可抛文档解析与不变量错误，无法再收窄
                自身.ctx.日志.错误('credentials-local: reload commit failed at %s',自身.规格['filename'])#记录提交失败
                自身.ctx.日志.错误(错误)#再打印失败对象
        自身.入队(刷新并捕获)#排队，不等待

    def 写入(自身,引用,值):#排队一次行编辑
        """排队一次行编辑；入口检查尽早拒绝，队列在运行时再判定一次。"""
        动词='unset' if 值 is None else 'set'#用于错误文案的动词
        if 自身.是否已关闭():#已拆除
            raise 本地凭据错误('credentials-local is disposed: cannot '+动词+' "'+引用+'"')#拒绝新写入
        自身.断言未被遮蔽(引用,动词)#入口处拒绝会被环境遮蔽的写
        def 操作():#真正写入排进互斥链
            """真正写入排进互斥链。"""
            if 自身.是否已关闭():#排队期间可能已拆除
                raise 本地凭据错误('credentials-local was disposed before the queued "'+引用+'" '+动词+' ran')#排队项作废
            自身.断言未被遮蔽(引用,动词)#运行时再判定：排队期间环境可能已变
            os.makedirs(os.path.dirname(自身.规格['filename']),exist_ok=True,mode=0o700)#写锁的独占创建需要父目录存在；0700，因为 harness 主目录装着用户私有数据
            def 持锁():#跨进程写锁内的读改写
                """读改写：并入本进程尚未观察到的盘上状态——仍在监视器防抖窗口内的外部编辑、监视器漏掉的变更、或其他进程的写入——使下面的行编辑绝不能复活一份过期文档。"""
                自身.从盘面对账()#先与盘面对账
                已有=自身.值表.get(引用)#当前是否已有该键
                if 值 is None and 已有 is None:#删一个本就不在的键是空操作
                    return None#空操作
                下一文本=渲染引用(自身.文本,引用,值)#渲染下一份文本
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
            raise 本地凭据错误('credentials-local: "'+引用+'" is supplied read-only by the launching environment, so '+动词+' would be shadowed; unset it in the shell you start dsh from instead')#抛出遮蔽错误

    def 启动读取(自身):#启动读盘
        """启动读取：缺席文件是空存储；无效文件让插件激活失败。识别的预发布扁平布局先就地升级。"""
        断言仅所有者(自身.规格['filename'])#先检查仅所有者可读（0600 / umask）
        try:#按 utf8 读文档
            文本=读文档文本(自身.规格['filename'])#按 utf8 读文档
        except OSError as 错误:
            if not 是否缺席(错误):
                raise 错误
            return
        if 渲染扁平迁移(文本) is not None:#需迁移
            文本=自身.迁移扁平文档()#就地升级
        文档=解析凭证文档(文本,自身.规格['filename'])#解析
        自身.值表=文档['refs']#引用快照
        自身.记录表=文档['records']#记录快照
        自身.文本=文本#缓存原文

    def 迁移扁平文档(自身):
        """识别的预发布扁平布局的一次性升级。"""
        def 持锁():
            """持锁迁移。"""
            当前=读文档文本(自身.规格['filename'])#重读
            已迁=渲染扁平迁移(当前)#再识别
            if 已迁 is None:#已非扁平
                return 当前#原样
            原子写文件(自身.规格['filename'],已迁,{'mode':0o600,'dirMode':0o700})#写出
            自身.ctx.日志.信息(
                'credentials-local: migrated %s to the version %d layout; values are unchanged',
                自身.规格['filename'],文档版本,
            )#记日志
            return 已迁#新文本
        return 带文件锁(自身.规格['filename'],持锁)#持锁

    def 刷新(自身):#监视触发的重载
        """监视事件后重读文档。未变内容（包括本提供方自己的写入）是空操作；不可读文档保留上一份好快照并警告——活着的热重载绝不能把进程打下来。逃出扇出的不变量违规不是重载失败，会传到队列的错误面。"""
        if 自身.已关闭:#已关闭则不再发布
            return#空操作
        try:#尝试对账
            自身.从盘面对账()#按盘面发布差值
        except Exception as 错误:#对账失败
            if getattr(错误,'code',None)=='INVARIANT':#不变量失败继续抛
                raise 错误#继续抛
            自身.ctx.日志.警告('credentials-local: reload failed at %s; keeping the last good document',自身.规格['filename'])#警告并保留
            自身.ctx.日志.警告(错误)#再打印失败对象

    def 从盘面对账(自身):#与盘面对账并发布
        """把盘上文本与缓存比较，把任何差异发布进能力缝。缺席发布空存储；不可读或无效文档抛出，好让各调用方自选策略——重载警告并保留上一份好快照，写入大声失败而不是覆盖一份它读不懂的文档。"""
        # 每次重载和每次写入前再检查 mode：外部编辑器或还原的备份可能在启动后放宽权限；启动时检过一次不够。
        断言仅所有者(自身.规格['filename'])#从盘对账：再检仅所有者可读（0600 / umask）
        try:#读盘
            文本=读文档文本(自身.规格['filename'])#按 utf8 读文档
        except OSError as 错误:
            if not 是否缺席(错误):
                raise 错误
            文本=None
        # 未变内容（包括本提供方自己的写入）是空操作——文本缓存自我写入抑制；已关闭则不再发布。
        if 文本==自身.文本 or 自身.是否已关闭():#自我写入抑制或已关闭
            return#空操作
        下一={'refs':{},'records':{}} if 文本 is None else 解析凭证文档(文本,自身.规格['filename'])#解析下一份快照
        变更引用=自身.变更引用(自身.值表,下一['refs'])#变更引用
        变更记录=自身.变更记录(自身.记录表,下一['records'])#变更记录
        自身.文本=文本#更新文本缓存
        自身.值表=下一['refs']#整份替换引用
        自身.记录表=下一['records']#整份替换记录
        for 引用 in 变更引用:#逐条扇出引用
            自身.通知已更新(引用)#扇出
        for 键 in 变更记录:#逐条扇出记录
            自身.通知记录已更新(键)#扇出

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

    def 变更记录(自身,先前,下一):
        """存储值已变的记录。"""
        变更=[]#收集
        已见=set()#去重
        for 键 in list(先前.keys())+list(下一.keys()):#并集
            if 键 in 已见:#已收
                continue#跳
            已见.add(键)#记
            if 同json值(先前.get(键),下一.get(键)):#未变
                continue#跳
            变更.append(解析凭证键(键))#记下
        return 变更#列表

Config=配置模式#Cordis 配置模式
默认=本地凭证提供方#默认导出
default=本地凭证提供方#Cordis 默认导出

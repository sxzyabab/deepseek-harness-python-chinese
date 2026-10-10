'已加载的模组、引擎引发的事件，以及模组 $ 调用再引发的事件。不依赖 Cordis'
import threading,time#定时器与睡眠
from .链 import 派发,引擎来源,钩子超时错误,最内时钟#链与睡眠时的预算
from .接口 import 创建模组接口#$
from .值 import 消息,记录,是有限数,兑现#入参与内置操作
from .模块 import 钩子注册表,登记模组#注册表

__all__=['操作被拒错误','模组引擎']

class 操作被拒错误(Exception):
    '引擎行为用 { deny } 回答一次 $ 调用'
    def __init__(自身,原因):
        '原因会变成调用方看见的拒绝文本'
        super().__init__(原因)#消息
        自身.原因=原因#拒绝文本

def 中止异常(信号):
    '睡眠被取消时抛出的异常'
    原因=getattr(信号,'原因',None)#承载原因
    if isinstance(原因,BaseException):#已经是异常
        return 原因#原样
    if 原因 is None:#没有原因
        return RuntimeError('$.clock.sleep 已取消')#默认
    return RuntimeError('$.clock.sleep 已取消：'+消息(原因))#带上原因

def 睡眠除非(毫秒,信号):
    '等待毫秒，或在取消、钩子预算到点时失败。同步代码中间插不进超时，只在等待处检查'
    if 信号 is not None and 信号.is_set():#开始前已取消
        raise 中止异常(信号)#取消
    截止=time.monotonic()+毫秒/1000#墙钟截止
    while True:#切片等待
        if 信号 is not None and 信号.is_set():#等待中取消
            raise 中止异常(信号)#取消
        时钟=最内时钟()#调用睡眠的那条钩子
        if 时钟 is not None and 时钟.到点():#预算用完
            raise 钩子超时错误(时钟.毫秒)#算作钩子超时
        剩余=截止-time.monotonic()#还要睡多久
        if 剩余<=0:#睡完
            return#结束
        步=剩余 if 剩余<0.05 else 0.05#最多 50 毫秒看一次
        if 时钟 is not None and 时钟.忙起 is not None:#预算还在走
            预算剩=时钟.剩余毫秒()/1000#秒
            if 预算剩<=0:#刚好到点
                raise 钩子超时错误(时钟.毫秒)#超时
            if 预算剩<步:#不要睡过到点
                步=预算剩#缩短
        time.sleep(步)#这一小段

def 状态槽(插件,键):
    '$.state 的槽：插件名、空字符、键'
    if not isinstance(插件,str) or not isinstance(键,str):#两个都必须是字符串
        raise TypeError('$.state 需要 { plugin, key } 字符串')#类型
    return 插件+'\u0000'+键#槽名

class 定时器集:
    '一个模组在一次会话里的定时器。关闭后不再接受新的，并等到已在跑的回调结束'
    def __init__(自身,报告,属主):
        '报告收定时回调的失败'
        自身.报告=报告#诊断
        自身.属主=属主#模组名
        自身.活动=[]#还没触发的一次性定时器
        自身.取消间隔=[]#间隔的停止函数
        自身.运行=[]#正在跑的回调线程
        自身.已关=False#关闭后拒绝新定时器
        自身.锁=threading.Lock()#活动表

    def 之后(自身,毫秒,函数):
        '到点跑一次。返回带 cancel 的对象'
        if 自身.已关:#已卸载
            return {'cancel':lambda:None}#空取消
        def 到点():
            '到点后跑回调'
            with 自身.锁:#摘掉
                if 定时 in 自身.活动:#还在
                    自身.活动.remove(定时)#摘掉
            自身.跑(函数)#跑
        定时=threading.Timer(0 if 毫秒<0 else 毫秒/1000,到点)#一次性
        定时.daemon=True#不挡住进程退出
        with 自身.锁:#登记
            自身.活动.append(定时)#活动
        定时.start()#启动
        def 取消():
            '取消这一次'
            定时.cancel()#取消定时
            with 自身.锁:#摘掉
                if 定时 in 自身.活动:#还在
                    自身.活动.remove(定时)#摘掉
        return {'cancel':取消}#模组拿去取消

    def 每隔(自身,毫秒,函数):
        '按间隔反复跑。返回带 cancel 的对象'
        if 自身.已关:#已卸载
            return {'cancel':lambda:None}#空取消
        停=threading.Event()#取消门
        间隔=0 if 毫秒<0 else 毫秒/1000#秒
        def 循环():
            '每次等到间隔，除非已取消'
            while not 自身.已关 and not 停.wait(间隔):#到点且没关
                if 自身.已关:#关闭发生在等待之后
                    return#停
                自身.跑(函数)#这一拍
        线程=threading.Thread(target=循环,daemon=True)#先登记再启动
        def 取消():
            '停掉后续间隔'
            停.set()#唤醒等待
        with 自身.锁:#记下以便关闭
            自身.取消间隔.append(取消)#关闭时调用
            自身.运行.append(线程)#关闭时等待它退出
        线程.start()#启动
        return {'cancel':取消}#模组拿去取消

    def 关闭(自身):
        '取消尚未触发的定时器，并等到已在跑的回调结束'
        自身.已关=True#拒绝新的
        with 自身.锁:#取出
            定时们=list(自身.活动)#一次性
            取消们=list(自身.取消间隔)#间隔
            自身.活动.clear()#清掉
            自身.取消间隔.clear()#清掉
        for 定时 in 定时们:#逐个取消
            定时.cancel()#不再触发
        for 取消 in 取消们:#停间隔
            取消()#唤醒
        已等=set()#已经等过的线程
        while True:#回调里可能又启动回调
            with 自身.锁:#取出还没等的
                线程们=[线程 for 线程 in 自身.运行 if 线程 not in 已等]#新的
            if len(线程们)==0:#没有了
                break#结束
            for 线程 in 线程们:#逐个
                已等.add(线程)#记下
                线程.join()#等到结束

    def 跑(自身,函数):
        '在守护线程里跑回调。失败记一行。先登记再启动，关闭才能等得到'
        def 体():
            '跑完后把自己从运行表拿掉'
            try:#回调可抛
                兑现(函数())#若返回期约则等到它
            except Exception as 错误:#失败
                自身.报告(自身.属主+'：定时回调失败：'+消息(错误))#一行
            finally:#离开运行表
                with 自身.锁:#摘掉
                    if 线程 in 自身.运行:#还在
                        自身.运行.remove(线程)#摘掉
        线程=threading.Thread(target=体,daemon=True)#先创建
        with 自身.锁:#登记
            if 自身.已关:#关闭发生在创建之后
                return#不再跑
            自身.运行.append(线程)#关闭时等待
        线程.start()#启动

class 模组引擎:
    '已加载模组，以及两种到达它们的方式：引擎引发，或更早模组的 $ 调用'
    def __init__(自身,选项):
        '选项给出操作表、状态键、预算和诊断'
        自身.选项=选项#构造选项
        自身.注册表=钩子注册表()#模组与钩子
        自身.状态={}#会话键到槽表
        自身.定时器={}#会话键加模组名到定时器集
        自身.下一顺序=0#加载顺序

    def 添加(自身,定义):
        '跑 register，并把钩子放在此前所有模组的里面'
        for 已有 in 自身.注册表.列出():#同名先拒绝，文案和注册表那条不同
            if 已有['name']==定义['name']:#同名
                raise RuntimeError('模组 "'+定义['name']+'" 没加载：已有同名模组')#拒绝
        顺序=自身.下一顺序#这次的位置
        自身.下一顺序+=1#下一个
        做出=登记模组(定义,顺序)#可能抛加载错误
        自身.注册表.添加(做出['mod'],做出['hooks'])#放入
        return 做出['mod']#已加载模组

    def 发起(自身,事件,输入,核心,选项):
        '引擎引发一个事件，外层钩子先跑'
        return 自身.发起已选(事件,自身.注册表.选择(事件),None,输入,核心,选项)#没有引发者

    def 发起已选(自身,事件,钩子,引发者,输入,核心,选项):
        '用调用方已经选好的钩子引发。引发者缺席时来源是引擎'
        信号=选项['signal'] if 'signal' in 选项 and 选项['signal'] is not None else threading.Event()#没有信号就用不取消的门
        来源=引擎来源 if 引发者 is None else {'plugin':引发者['name'],'tier':'user'}#来源
        请求={
            'event':事件,#事件名
            'input':输入,#入参
            'core':核心,#最底行为
            'origin':来源,#来源
            'hooks':钩子,#外层在前
            'api':lambda 钩子,时钟:自身.接口(钩子['mod'],时钟,选项['binding'],信号),#$
            'budgetMs':自身.选项['budgetMs'],#钩子预算
            'catchBudgetMs':自身.选项['catchBudgetMs'],#处理函数预算
            'signal':信号,#取消
            'report':自身.选项['report'],#诊断
        }#派发请求
        if 'validateNext' in 选项 and 选项['validateNext'] is not None:#要拒绝改写
            请求['validateNext']=选项['validateNext']#带上
        return 派发(请求)#结果

    def 调用(自身,模组,操作,输入,绑定,信号):
        '把一次 $ 调用当成事件，只让更早的模组看见，然后用引擎行为回答'
        def 核心(事件):
            '引擎行为。操作被拒变成 { deny }'
            try:#其余错误是事件自己的失败
                return {'value':兑现(自身.操作核(操作,事件,{'mod':模组,'binding':绑定,'signal':信号,'engine':自身}))}#值
            except 操作被拒错误 as 拒绝:#故意拒绝
                return {'deny':拒绝.原因}#拒绝
        钩子=[] if 操作=='tool.call' else 自身.注册表.选择(操作,模组)#tool.call 由工具管道引发，这里不再来一次
        结果=派发({
            'event':操作,#事件名
            'input':输入,#入参
            'core':核心,#引擎行为
            'origin':{'plugin':模组['name'],'tier':'user'},#调用方模组
            'hooks':钩子,#更早的模组
            'api':lambda 钩子,时钟:自身.接口(钩子['mod'],时钟,绑定,信号),#$
            'budgetMs':自身.选项['budgetMs'],#预算
            'catchBudgetMs':自身.选项['catchBudgetMs'],#处理函数预算
            'signal':信号,#取消
            'report':自身.选项['report'],#诊断
        })#派发
        if not isinstance(结果,dict) or ('value' not in 结果 and 'deny' not in 结果):#没有约定的形状
            raise RuntimeError(操作+'：钩子既没返回 { value } 也没返回 { deny }')#不能用
        if isinstance(结果.get('deny'),str):#字符串拒绝
            raise RuntimeError(操作+' 被拒绝：'+结果['deny'])#调用失败
        return 结果.get('value')#值，可以是 None

    def 接口(自身,模组,时钟,绑定,信号):
        '为一个模组在一次事件里做出 $'
        return 创建模组接口({
            'mod':模组,#模组
            'clock':时钟,#预算，钩子外为 None
            'invoke':lambda 操作,输入:自身.调用(模组,操作,输入,绑定,信号),#引发
            'timers':自身.定时器集(模组,自身.选项['stateKey'](绑定)),#这次会话的定时器
            'report':自身.选项['report'],#诊断
        })#$

    def 忘记会话(自身,键):
        '忘掉一次会话的 $.state，并关掉它的事件启动的定时器'
        if 键 in 自身.状态:#有状态
            del 自身.状态[键]#删掉
        前缀=键+'\u0000'#这个会话的定时器
        待关=[]#要关的
        for 定时键 in list(自身.定时器):#逐个
            if 定时键.startswith(前缀):#属于这次会话
                待关.append(自身.定时器.pop(定时键))#摘下
        for 定时 in 待关:#关掉
            定时.关闭()#等到回调结束

    def 描述(自身,模组):
        '这个模组的 hooks 行'
        return 自身.注册表.描述(模组)#委托

    def 卸载(自身,名字):
        '卸掉钩子并取消定时器'
        自身.注册表.移除(名字)#钩子
        后缀='\u0000'+名字#这个模组的定时器
        待关=[]#要关的
        for 定时键 in list(自身.定时器):#逐个
            if 定时键.endswith(后缀):#属于这个模组
                待关.append(自身.定时器.pop(定时键))#摘下
        for 定时 in 待关:#关掉
            定时.关闭()#等到回调结束

    def 丢弃(自身):
        '卸掉全部分组并关掉全部定时器'
        for 模组 in list(自身.注册表.列出()):#逐个
            自身.卸载(模组['name'])#卸掉
        自身.状态.clear()#清状态

    def 定时器集(自身,模组,会话键):
        '这个模组在这个会话键下的定时器。没有就建'
        定时键=会话键+'\u0000'+模组['name']#键
        已有=自身.定时器.get(定时键)#已有
        if 已有 is None:#没有
            已有=定时器集(自身.选项['report'],模组['name'])#新建
            自身.定时器[定时键]=已有#记下
        return 已有#定时器集

    def 操作核(自身,操作,输入,上下文):
        '部署提供的行为优先。没有时，引擎自己回答 state 和 clock.now、clock.sleep'
        提供=自身.选项['ops'](操作)#部署的行为
        if 提供 is not None:#有
            return 提供(输入,上下文)#交给它
        字段=记录(输入)#入参字段
        if 操作=='state.get':#读
            槽=状态槽(字段.get('plugin'),字段.get('key'))#槽
            键=自身.选项['stateKey'](上下文['binding'])#会话键
            读到=自身.选项.get('onStateRead')#可选订阅
            if 读到 is not None:#要通知
                读到(键,槽)#绘制可以订阅
            表=自身.状态.get(键)#这次会话
            值=None if 表 is None or 槽 not in 表 else 表[槽]#缺席是 None
            return {'value':值}#带 value 键，即使值是 None
        if 操作=='state.set':#写
            槽=状态槽(字段.get('plugin'),字段.get('key'))#槽
            键=自身.选项['stateKey'](上下文['binding'])#会话键
            表=自身.状态.get(键)#这次会话
            if 表 is None:#还没有
                表={}#新建
                自身.状态[键]=表#记下
            表[槽]=字段.get('value')#写入，可以是 None
            写到=自身.选项.get('onStateWritten')#可选通知
            if 写到 is not None:#要通知
                写到(键,槽)#订阅了的条带重画
            return None#无值
        if 操作=='clock.now':#现在
            return int(time.time()*1000)#纪元毫秒
        if 操作=='clock.sleep':#睡眠
            毫秒=字段.get('ms')#毫秒
            if not 是有限数(毫秒) or 毫秒<0:#必须是非负有限数
                raise TypeError('$.clock.sleep 需要非负的毫秒数')#类型
            睡眠除非(毫秒,上下文['signal'])#等待
            return None#无值
        raise RuntimeError('没有 '+操作+' 的实现')#没人提供

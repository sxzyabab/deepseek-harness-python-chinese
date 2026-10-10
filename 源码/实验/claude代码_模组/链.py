'一条事件的钩子链。钩子抛错、超时或没给出对象就跳过；已经调用过 next 时保留底下的结果'
import threading,time#活动时钟与预算
from .值 import 消息,深冻结值,是结果对象,是期约,兑现#入参冻结与期约
from .匹配器 import 匹配器命中#字段匹配在运行时做

__all__=['钩子超时错误','改写被拒错误','引擎来源','派发','压入时钟','弹出时钟','最内时钟']

_时钟局部=threading.local()#当前线程上、由外到内的预算时钟

def 压入时钟(时钟):
    '钩子开始时压入它的预算时钟'
    栈=getattr(_时钟局部,'栈',None)#当前栈
    if 栈 is None:#还没有
        栈=[]#新建
        _时钟局部.栈=栈#挂上
    栈.append(时钟)#最内层在末尾

def 弹出时钟():
    '钩子结束时弹出'
    栈=getattr(_时钟局部,'栈',None)#当前栈
    if 栈:#有
        栈.pop()#弹出

def 最内时钟():
    '正在跑的最内层钩子的时钟；没有则 None'
    栈=getattr(_时钟局部,'栈',None)#当前栈
    if not 栈:#空
        return None#没有
    return 栈[-1]#最内层

class 钩子超时错误(Exception):
    '钩子自己的运行时间用完了'
    def __init__(自身,预算毫秒):
        '记下上限'
        super().__init__('跑过了它的 '+str(预算毫秒)+' 毫秒上限')#给人看的原因
        自身.预算毫秒=预算毫秒#上限

class 改写被拒错误(Exception):
    '钩子要求的改写这个宿主不提供'
    def __init__(自身,原因):
        '记下原因'
        super().__init__(原因)#原样

class 无结果错误(Exception):
    '钩子结算时没有给出结果对象'
    def __init__(自身):
        '固定文案'
        super().__init__('没有返回结果')#跳过原因

引擎来源={'plugin':'engine','tier':'core'}#引擎自己的来源

class 预算时钟:
    '只计算钩子自己在忙的时间。等待 next 或 $ 时暂停。$.clock.sleep 不暂停'
    def __init__(自身,毫秒):
        '毫秒是这份钩子的上限'
        自身.毫秒=毫秒#上限
        自身.已花=0#已经计入的毫秒
        自身.忙起=None#当前这段从何时开始
        自身.暂停数=0#嵌套暂停
        自身.已停=False#结算后不再计时

    def 剩余毫秒(自身):
        '离到点还剩多少毫秒'
        忙=0 if 自身.忙起 is None else time.perf_counter()*1000-自身.忙起#当前这段
        剩余=自身.毫秒-自身.已花-忙#还剩
        if 剩余<0:#不能为负
            return 0#到点
        return 剩余#还剩

    def 到点(自身):
        '正在计时并且时间已经用完'
        return (not 自身.已停) and 自身.忙起 is not None and 自身.剩余毫秒()<=0#只在忙的时候到点

    def 开始(自身):
        '从现在起算忙'
        if 自身.已停:#已经结算
            return#不再计
        自身.忙起=time.perf_counter()*1000#起点

    def 暂停(自身):
        '等待 next 或 $ 时停表。嵌套暂停要逐层恢复'
        if 自身.已停:#已经结算
            return#不再计
        自身.暂停数+=1#多一层
        if 自身.忙起 is not None:#这段要入账
            自身.已花+=time.perf_counter()*1000-自身.忙起#入账
            自身.忙起=None#停表

    def 恢复(自身):
        '等待结束，最外层恢复时继续计时'
        if 自身.已停 or 自身.暂停数==0:#不能恢复
            return#停着
        自身.暂停数-=1#少一层
        if 自身.暂停数==0:#全部恢复
            自身.忙起=time.perf_counter()*1000#重新起算

    def 停止(自身):
        '钩子已结算，之后不能再到点'
        if 自身.忙起 is not None:#还有一段没入账
            自身.已花+=time.perf_counter()*1000-自身.忙起#入账
        自身.已停=True#停止
        自身.忙起=None#清掉

class 预算视图:
    'next.budget。字段名保持 ms 与 remainingMs'
    def __init__(自身,毫秒,时钟):
        '毫秒是上限，时钟给出剩余'
        自身.ms=毫秒#上限
        自身._时钟=时钟#活的时钟

    @property
    def remainingMs(自身):
        '现在还剩的毫秒'
        return 自身._时钟.剩余毫秒()#活的剩余

def 失败分类(错误):
    '跳过一行的尾巴，以及 .catch 看见的 kind 与 message'
    if isinstance(错误,钩子超时错误):#超时
        return {'kind':'timeout','message':错误.args[0],'line':'超时，'+错误.args[0]}#超时行
    if isinstance(错误,(无结果错误,改写被拒错误)):#这两种直接用消息
        return {'kind':'throw','message':错误.args[0],'line':错误.args[0]}#消息本身
    if isinstance(错误,BaseException):#其它异常
        名=type(错误).__name__#异常名
        文本=消息(错误)#消息
        return {'kind':'throw','message':名+': '+文本,'line':'抛出了 '+名+': '+文本}#带名字
    return {'kind':'throw','message':消息(错误),'line':'抛出了 '+消息(错误)}#非异常

def 等到计入预算(值,时钟,信号):
    '钩子若返回期约，等待时预算继续走。同步返回值不因墙钟超时被判超时'
    if not 是期约(值):#同步结果
        return 值#原样
    盒={'完':False,'好':False,'值':None,'错':None}#结算盒
    门=threading.Event()#结算门
    def 成功(数据):
        '兑现'
        盒['好']=True#成功
        盒['值']=数据#值
        盒['完']=True#完
        门.set()#开门
    def 失败(错误):
        '拒绝'
        盒['错']=错误#原因
        盒['完']=True#完
        门.set()#开门
    值.然后(成功,失败)#挂上
    while not 盒['完']:#还没结算
        if 时钟.到点():#预算用完
            raise 钩子超时错误(时钟.毫秒)#超时
        if 信号 is not None and 信号.is_set():#事件取消
            原因=getattr(信号,'原因',None)#承载原因
            if isinstance(原因,BaseException):#异常
                raise 原因#原样
            raise RuntimeError('事件已取消')#默认文案
        门.wait(0.05)#短等
    if not 盒['好']:#拒绝
        错误=盒['错']#原因
        if isinstance(错误,BaseException):#异常
            raise 错误#原样
        raise RuntimeError(消息(错误))#包起来
    return 盒['值']#兑现值

class 下一步:
    '钩子收到的 next。signal、origin、budget、to、error、called 这些名字给模组读'
    def __init__(自身,调用,信号,来源,预算毫秒,时钟,跳层文案):
        '调用是真正往下走的函数'
        自身._调用=调用#往下
        自身.signal=信号#取消
        自身.origin=来源#谁引发的
        自身.budget=预算视图(预算毫秒,时钟)#预算
        自身.error=None#只有 .catch 才有
        自身.called=False#失败钩子是否调用过 next
        自身._跳层文案=跳层文案#to 的错误

    def __call__(自身,事件):
        '往下跑'
        return 自身._调用(事件)#结果

    def to(自身,*位置参数):
        '跳层不提供，调用必定抛错'
        raise RuntimeError(自身._跳层文案)#始终抛

def 派发(请求):
    '从最外层钩子跑到引擎行为。next 会阻塞到它底下结束'
    钩子们=请求['hooks']#已选中的钩子，外层在前

    def 从(下标,输入):
        '从这一下标往下，跳过匹配器没中的钩子'
        序号=下标#当前
        while 序号<len(钩子们):#还有钩子
            钩子=钩子们[序号]#这一条
            匹配器=钩子['matcher']#可选匹配器
            if 匹配器 is not None and not 匹配器命中(匹配器,输入):#没中
                序号+=1#下一条
                continue#跳过
            return 跑钩子(钩子,序号,输入)#跑这一条
        return 兑现(请求['core'](输入))#引擎行为

    def 跑钩子(钩子,下标,输入):
        '跑一条钩子。失败则试 .catch，再不行就用底下已经跑出的结果'
        冻结=深冻结值(输入)#钩子看见的入参
        时钟=预算时钟(请求['budgetMs'])#这条钩子的预算
        状态={'放弃':False,'调用过':False,'底下':None,'底下错':None,'拒绝':None}#闭包状态
        def 调用(事件):
            '一次 next。第二次把第一次的结果交回去'
            状态['调用过']=True#调用过
            if 状态['底下']=='完成':#已经成功
                return 状态['底下值']#同一份
            if 状态['底下']=='失败':#已经失败
                raise 状态['底下错']#同一错误
            if 状态['放弃']:#钩子已被放弃
                return None#不再往下
            校验=请求.get('validateNext')#可选改写检查
            if 校验 is not None:#要检查
                try:#检查抛错则这条钩子失败
                    校验(事件,钩子)#检查钩子交下去的入参
                except Exception as 错误:#拒绝改写
                    拒绝=错误 if isinstance(错误,Exception) else RuntimeError(消息(错误))#异常
                    状态['拒绝']={'error':拒绝}#记下
                    raise 拒绝#交给钩子
            时钟.暂停()#等待底下不计入这条钩子
            状态['底下']='进行'#只跑一次
            try:#底下抛错要记下来
                状态['底下值']=从(下标+1,事件)#阻塞到结束
                状态['底下']='完成'#成功
                return 状态['底下值']#结果
            except Exception as 错误:#底下失败
                状态['底下错']=错误#记下
                状态['底下']='失败'#失败
                raise#原样
            finally:#无论成败都恢复计时
                时钟.恢复()#恢复
        下一步对象=下一步(
            调用,请求['signal'],请求['origin'],请求['budgetMs'],时钟,
            'next.to 只对 prependPlugins 或 appendPlugins 里的模组可用',
        )#钩子的 next
        接口=请求['api'](钩子,时钟)#这条钩子的 $
        时钟.开始()#开始计时
        压入时钟(时钟)#供 $.clock.sleep 查看
        try:#结算后一定停表
            try:#钩子失败走跳过
                结果=钩子['hook'](接口,冻结,下一步对象)#同步调用
                结果=等到计入预算(结果,时钟,请求['signal'])#返回的期约才受预算约束
                if not 是结果对象(结果):#不是对象
                    raise 无结果错误()#跳过
                时钟.停止()#已经给出答案
                if 状态['底下']=='失败':#钩子自己接住了底下的失败，事件仍用钩子的答案
                    请求['report'](钩子['mod']['name']+'：'+请求['event']+'：钩子已经给出答案之后，底下的链失败了：'+消息(状态['底下错']))#一行
                return 结果#钩子的答案
            except Exception as 错误:#钩子失败或底下失败
                状态['放弃']=True#后续 next 不再新开底下
                if 状态['底下错'] is not None and 错误 is 状态['底下错']:#失败的是引擎或更底层
                    raise#事件自己的失败
                用=状态['拒绝']['error'] if 状态['拒绝'] is not None and 错误 is 状态['拒绝']['error'] else 错误#改写被拒优先
                失败=失败分类(用)#分类
                已报=钩子['reported']#这条钩子报过的种类
                if 失败['kind'] not in 已报:#每种报一次
                    已报.add(失败['kind'])#记下
                    请求['report'](钩子['mod']['name']+'：'+请求['event']+' 钩子被跳过：'+失败['line'])#一行
                if 钩子['catchHandler'] is not None:#有 .catch
                    答出=跑捕获(钩子,下标,冻结,{'kind':失败['kind'],'message':失败['message']},状态)#给处理函数机会
                    if 答出 is not None or 状态.get('捕获答了') is True:#null 也是答案
                        return 状态.get('捕获值',答出)#处理函数的答案
                if 状态['底下']=='完成':#底下已经跑完
                    return 状态['底下值']#用那份结果
                if 状态['底下']=='失败':#底下失败
                    raise 状态['底下错']#事件失败
                return 从(下标+1,输入)#用钩子收到的入参继续
        finally:#停表并离开时钟栈
            时钟.停止()#停止
            弹出时钟()#弹出

    def 跑捕获(钩子,下标,输入,失败,状态):
        '失败钩子的 .catch。已经跑过的底下不会再跑第二次'
        时钟=预算时钟(请求['catchBudgetMs'])#处理函数自己的上限
        处理放弃=False#处理函数失败后不再新开
        def 调用(事件):
            '处理函数的 next，和钩子共用底下状态'
            if 状态['底下']=='完成':#钩子已经跑过
                return 状态['底下值']#交回
            if 状态['底下']=='失败':#钩子底下失败了
                raise 状态['底下错']#交回
            if 处理放弃:#处理函数已放弃
                return None#不再往下
            校验=请求.get('validateNext')#同样不许改写
            if 校验 is not None:#要检查
                try:#失败则 next 拒绝
                    校验(事件,钩子)#检查
                except Exception as 错误:#拒绝
                    raise 错误 if isinstance(错误,Exception) else RuntimeError(消息(错误))#原样
            时钟.暂停()#等待不计入处理函数
            状态['底下']='进行'#只跑一次
            try:#记下成败
                状态['底下值']=从(下标+1,事件)#往下
                状态['底下']='完成'#成功
                return 状态['底下值']#结果
            except Exception as 错误:#失败
                状态['底下错']=错误#记下
                状态['底下']='失败'#失败
                raise#原样
            finally:#恢复
                时钟.恢复()#恢复
        下一步对象=下一步(
            调用,请求['signal'],请求['origin'],请求['catchBudgetMs'],时钟,
            'next.to 在 .catch 处理函数里不可用',
        )#处理函数的 next
        下一步对象.error=失败#失败种类
        下一步对象.called=状态['调用过']#钩子是否调用过 next
        接口=请求['api'](钩子,时钟)#同一个模组的 $
        时钟.开始()#开始
        压入时钟(时钟)#压入
        try:#停表
            try:#处理函数失败只记一行
                处理=钩子['catchHandler']#处理函数
                结果=处理(接口,输入,下一步对象)#同步调用
                结果=等到计入预算(结果,时钟,请求['signal'])#期约受预算约束
                if 是结果对象(结果):#对象，含 null
                    状态['捕获答了']=True#连 None 也算答了
                    状态['捕获值']=结果#答案
                    return 结果#答案
            except Exception as 错误:#处理函数自己失败
                请求['report'](钩子['mod']['name']+'：'+请求['event']+' .catch 处理函数被跳过：'+失败分类(错误)['line'])#一行
            return None#没答上
        finally:#放弃后续 next 并停表
            处理放弃=True#不再新开
            时钟.停止()#停止
            弹出时钟()#弹出

    return 从(0,请求['input'])#从最外层开始

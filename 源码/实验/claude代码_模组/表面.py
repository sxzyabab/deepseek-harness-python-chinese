'提示上方的条带：经 ui.render 绘制，按住按钮回调，状态变化或模组要求时重画'
import json,threading#同一棵树保持代数；刷新要能从定时器重入
from .元素 import 序列化树,树问题#校验与序列化
from .值 import 消息#失败文案

__all__=['表面表']

class 会话条带:
    '一次会话的当前画面'
    def __init__(自身):
        '还没画过'
        自身.代数=0#0 表示还没画
        自身.树=None#序列化树或 None
        自身.订阅=set()#上次绘制读过的 $.state 槽
        自身.动作={}#当前代的按钮回调
        自身.观察者=set()#快照监听
        自身.绘制中=False#有一次绘制在跑
        自身.待再画=False#绘制期间又要求了一次
        自身.已关=False#忘掉之后不再画
        自身.唤醒=set()#停掉观看
        自身.收集=None#绘制期间记下读过的槽
        自身.锁=threading.Lock()#观察队列不用这把锁

    def 快照(自身):
        '当前代'
        return {'generation':自身.代数,'tree':自身.树}#快照

class 表面表:
    '按会话号放条带'
    def __init__(自身,宿主):
        '宿主负责列数、行数、引发 ui.render 和跑按钮'
        自身.宿主=宿主#宿主
        自身.条带表={}#会话号到条带
        自身.已丢弃=False#丢弃后不再画
        自身.锁=threading.Lock()#合并同时来的刷新

    def 当前(自身,会话号):
        '最新快照。还没画过就先画一次'
        条带=自身.取条带(会话号)#条带
        if 条带.代数==0:#还没画
            自身.刷新(会话号)#画一次
        return 条带.快照()#当前代

    def 观看(自身,会话号,信号):
        '先给出当前快照，之后每次重画给一次，直到信号取消'
        条带=自身.取条带(会话号)#条带
        队列=[]#还没交出的快照
        醒=threading.Event()#有新快照或该结束了
        队锁=threading.Lock()#队列
        def 观察(快照):
            '放进队列并唤醒'
            with 队锁:#放入
                队列.append(快照)#一份
                醒.set()#唤醒
        条带.观察者.add(观察)#订阅
        条带.唤醒.add(醒.set)#关掉时唤醒
        try:#离开时退订
            首=自身.当前(会话号)#第一次可能就是绘制
            已交=首['generation']#已经交出的代
            yield 首#先给当前
            while (信号 is None or not 信号.is_set()) and not 条带.已关:#还在看
                with 队锁:#取一份
                    if len(队列)>0:#有
                        下一份=队列.pop(0)#最早的
                    else:#没有
                        下一份=None#空
                        醒.clear()#准备再等
                if 下一份 is None:#没有新的
                    醒.wait(0.05)#短等，取消也能结束
                    continue#再看
                if 下一份['generation']<=已交:#第一次绘制可能通知两次
                    continue#不重复交
                已交=下一份['generation']#记下
                yield 下一份#新的一代
        finally:#退订
            条带.观察者.discard(观察)#不再通知
            条带.唤醒.discard(醒.set)#不再唤醒

    def 刷新(自身,会话号):
        '重画。绘制期间再来的请求合并成绘制结束后的再一次'
        条带=自身.取条带(会话号)#条带
        with 自身.锁:#只让一次绘制在跑
            if 条带.绘制中:#已经在画
                条带.待再画=True#结束再来一次
                return#合并
            条带.绘制中=True#占住
        while True:#至少画一次
            自身.画一次(会话号,条带)#画
            with 自身.锁:#看还有没有合并来的
                if not 条带.待再画:#没有
                    条带.绘制中=False#放开
                    return#结束
                条带.待再画=False#再画一次

    def 按下(自身,会话号,代数,动作编号):
        '跑按钮回调并重画。旧一代的按下忽略'
        条带=自身.取条带(会话号)#条带
        动作=条带.动作.get(动作编号) if 代数==条带.代数 else None#必须是当前代
        if 动作 is None:#没有这个按钮
            自身.宿主['report']('条带按键被忽略：第 '+str(代数)+' 代的 '+动作编号+' 不在当前画面（第 '+str(条带.代数)+' 代）')#一行
            return 条带.快照()#不变
        自身.宿主['runAction'](会话号,动作)#跑回调
        自身.刷新(会话号)#重画
        return 条带.快照()#新画面

    def 读了状态(自身,会话号,槽):
        '绘制期间读了 $.state，就订阅这个槽'
        条带=自身.条带表.get(会话号)#可能还没有
        if 条带 is not None and 条带.收集 is not None:#正在收集
            条带.收集.add(槽)#订阅

    def 写了状态(自身,会话号,槽):
        '订阅过的槽被写下时重画'
        条带=自身.条带表.get(会话号)#可能没有
        if 条带 is None or 槽 not in 条带.订阅:#没订阅
            return#不画
        自身.刷新(会话号)#重画

    def 忘掉(自身,会话号):
        '结束观看，并且不再画'
        条带=自身.条带表.get(会话号)#可能没有
        if 条带 is None:#没有
            return#不用
        del 自身.条带表[会话号]#摘掉
        条带.已关=True#停止
        条带.观察者.clear()#不再通知
        for 唤醒 in list(条带.唤醒):#逐个
            唤醒()#结束观看

    def 丢弃(自身):
        '全部忘掉'
        自身.已丢弃=True#不再画
        for 会话号 in list(自身.条带表):#逐个
            自身.忘掉(会话号)#结束

    def 取条带(自身,会话号):
        '没有就建一条'
        条带=自身.条带表.get(会话号)#已有
        if 条带 is None:#没有
            条带=会话条带()#新建
            自身.条带表[会话号]=条带#记下
        return 条带#条带

    def 画一次(自身,会话号,条带):
        '引发 ui.render，树变了才增加代数'
        if 自身.已丢弃 or 条带.已关:#已经停
            return#不画
        输入={
            'component':'AbovePrompt',#提示上方
            'surface':'AbovePrompt',#条带
            'props':{
                'bodyColumns':自身.宿主['columns'],#列
                'hasSurvey':False,#没有调查
                'isWorking':False,#不标正在工作
                'maxRows':自身.宿主['rows'],#行
            },
            'viewport':{'columns':自身.宿主['columns']},#视口
        }#绘制入参
        条带.收集=set()#这次读到的槽
        try:#绘制失败就画空
            树=自身.宿主['render'](会话号,输入)#模组的树
        except Exception as 错误:#失败
            自身.宿主['report']('条带绘制失败：'+消息(错误))#一行
            树=None#空
        条带.订阅.clear()#换订阅
        for 槽 in 条带.收集:#这次读过的
            条带.订阅.add(槽)#留下
        条带.收集=None#停止收集
        问题=树问题(树)#校验
        if 问题 is not None:#不合法
            自身.宿主['report']('ui.render 钩子返回的树没通过校验：'+问题)#一行
            树=None#改画空
        动作={}#这一代的回调
        def 收下(回调):
            '分配 a0、a1'
            编号='a'+str(len(动作))#递增
            动作[编号]=回调#宿主留着
            return 编号#放进树
        序列=序列化树(树,收下)#序列化
        下一棵=None if len(序列)==0 else 序列#空树是 null
        if 条带.代数>0 and json.dumps(下一棵,ensure_ascii=False,separators=(',',':'))==json.dumps(条带.树,ensure_ascii=False,separators=(',',':')):#同一幅画，键顺序也要一致
            条带.动作.clear()#换回调
            条带.动作.update(动作)#新闭包
            return#代数不变
        条带.代数+=1#新的一代
        条带.树=下一棵#换树
        条带.动作.clear()#换回调
        条带.动作.update(动作)#这一代
        快照=条带.快照()#通知用
        for 观察 in list(条带.观察者):#逐个
            观察(快照)#唤醒观看

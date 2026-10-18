'一条可作答的提问卡片，以及计划审阅的收窄'
from ....模块.客户端.通告 import 取握手窗口
from ...异常 import 提问拒绝#线路拒绝

__all__=['待答提问','计划审阅于','结算撰写']

无名提问前缀=None#同一次加载共用，避免没名字的旧卡片复用草稿
下一提问键=0#没带调用标识的卡片序号


def 现在():
    '浏览器时钟的毫秒'
    return 取握手窗口().Date.now()#当前时刻


def 取无名前缀():
    '第一次需要时向浏览器要 16 字节，之后一直用这一份'
    global 无名提问前缀
    if 无名提问前缀 is not None:#已经有了
        return 无名提问前缀#复用
    窗口=取握手窗口()#浏览器
    字节=窗口.crypto.getRandomValues(窗口.Uint8Array(16))#随机字节
    片段=[]#十六进制
    下标=0#当前位置
    while 下标<16:#逐字节
        片段.append(format(int(字节[下标]),'02x'))#两位
        下标+=1#下一字节
    无名提问前缀=''.join(片段)#拼成前缀
    return 无名提问前缀#这一次加载的前缀


def 结算撰写(结算,失败句):
    '调用结算。异常原样抛出，其它失败包成失败句'
    try:#结算一次
        结算()#写入决定
        return#成功
    except Exception:#已经是异常
        raise#原样抛出
    except BaseException as 错误:#不是 Exception 的失败
        包装=Exception(失败句)#失败句
        包装.__cause__=错误#原来的原因
        raise 包装#抛出包装


def 计划审阅于(问题列表):
    '收成一张计划审阅。不符合就交给通用提问'
    if len(问题列表)!=1:#必须只有一道
        return None#不是审阅
    问题=问题列表[0]#这一道
    意图=问题.get('intent')#呈现意图
    if not isinstance(意图,dict) or 意图.get('kind')!='plan-review' or 问题.get('detail') is None:#不是计划，或没有正文
        return None#不是审阅
    if 问题.get('multiSelect') is True:#多选表达不了
        return None#不是审阅
    选项表=问题.get('options')#选项
    if 选项表 is None:#没有选项
        选项表=[]#当空表
    if len(选项表)>2:#超过两个答案
        return None#不是审阅
    批准=None#同意那一项
    拒绝=None#另一个选项
    for 选项 in 选项表:#逐项
        if 选项.get('label')==意图.get('approve'):#点名的同意
            if 批准 is None:#只取第一项
                批准=选项#记下
        elif 拒绝 is None:#第一个不同的标签
            拒绝=选项#记下
    if 批准 is None:#没有同意项
        return None#不是审阅
    审阅={#卡片用的字段
        'id':问题['id'],#回声编号
        'question':问题['question'],#无障碍名
        'plan':问题['detail'],#计划正文
        'approve':批准,#同意选项
    }
    if 意图.get('callId') is not None:#宿主点了名
        审阅['callId']=意图['callId']#用来重新打开
    if 拒绝 is not None:#还有另一个选项
        审阅['decline']=拒绝#拒绝选项
    return 审阅#可以画审阅卡


class 待答提问:
    '一张可作答的卡片。kind、key、sessionId 给会话待处理交互用'
    def __init__(自身,会话标识,问题列表,调用标识=None,同胞=None,审阅答案=None):
        '记下会话、问题和调用。没带调用标识就另给一个不会撞上的键'
        global 下一提问键
        自身.sessionId=会话标识#所属会话
        自身.questions=问题列表#整批问题
        自身.kind='question' if 计划审阅于(问题列表) is None else 'plan-review'#呈现判别
        自身.callId=调用标识#工具调用；没有则为 None
        自身.review=审阅答案#已结算的答案；活卡片没有
        自身.dismissal='cancel' if 调用标识 is None else 'hide'#关掉面板时做什么
        自身._状态='open'#投影状态
        自身._瀑布=None#当前瀑布通道
        自身._远程=None#继续之后的远程通道
        自身._座位=None#作曲座位
        自身._计时等待=False#这次请求带了截止时间
        自身._定时=None#倒计时句柄
        自身._截止=None#正在走的截止时刻
        自身._剩余毫秒=None#暂停下来的剩余
        自身._聚焦=False#焦点按住了倒计时
        自身._已动=False#已经改过草稿
        自身._按住=False#用户选择慢慢回答
        自身._已关=False#已经从登记表拿掉
        自身._同胞=同胞#这一会话还活着的键
        自身._监听=set()#快照订阅
        if 调用标识 is None:#宿主没点名
            下一提问键+=1#下一张用新序号
            自身.key='question:'+取无名前缀()+':'+str(下一提问键)#不会复用旧草稿
        else:#按调用对齐
            自身.key=待答提问.键于(会话标识,调用标识)#渲染键
        自身._快照=自身._造快照()#第一份快照

    @staticmethod
    def 键于(会话标识,调用标识):
        '工具调用的卡片键。宿主请求和投影用同一串'
        return 'question:'+str(会话标识)+':'+str(调用标识)#渲染键

    def 活键(自身):
        '这一会话还要留着的草稿键，包含自己'
        if 自身._同胞 is None:#没有同胞表
            return [自身.key]#只留自己
        return 自身._同胞()#登记表里的键

    def subscribe(自身,监听):
        '订阅快照变化，返回退订'
        自身._监听.add(监听)#加入
        def 退订():
            '摘掉这个监听'
            自身._监听.discard(监听)#摘掉
        return 退订#退订

    def getSnapshot(自身):
        '当前稳定快照。没变之前是同一份'
        return 自身._快照#快照

    def _造快照(自身):
        '按现在的通道、等待和关闭状态做一份快照'
        if 自身._瀑布 is not None:#瀑布还在
            通道='waterfall'#走瀑布
        elif 自身._状态=='continued' and 自身._远程 is not None:#已经继续且有远程
            通道='rpc'#走远程
        else:#还不能提交
            通道='none'#没有通道
        if 自身._状态=='continued':#工作已继续
            等待态='continued'#仍可回答
        elif 自身._按住:#用户要求一直等
            等待态='waiting'#不倒计时
        elif 自身._已动:#已经改过
            等待态='editing'#编辑冻结
        elif 自身._聚焦:#焦点按住
            等待态='focused'#焦点冻结
        else:#还在走
            等待态='counting'#倒计时
        if 自身._计时等待:#带了时限
            if 自身._截止 is None:#暂停着
                剩余=0 if 自身._剩余毫秒 is None else 自身._剩余毫秒#停住的剩余
            else:#正在走
                剩余=自身._截止-现在()#还剩
                if 剩余<0:#不能为负
                    剩余=0#到点
            倒计时={'remainingMs':剩余,'running':自身._截止 is not None}#倒计时
        else:#没有时限
            倒计时=None#不显示
        return {#给界面读
            'state':自身._状态,#投影状态
            'waitState':等待态,#等待呈现
            'countdown':倒计时,#倒计时
            'channel':通道,#提交通道
            'closed':自身._已关,#是否已关闭
        }

    def _发布(自身):
        '换一份快照，重排倒计时，再通知监听'
        自身._快照=自身._造快照()#新快照
        自身._重排()#定时器
        for 监听 in list(自身._监听):#逐个
            监听()#通知

    def _重排(自身):
        '有截止时间且还没关才每秒走一格。藏起面板也继续走'
        要=自身._截止 is not None and not 自身._已关#需要定时器
        if 要==(自身._定时 is not None):#已经是这个状态
            return#不动
        窗口=取握手窗口()#浏览器
        if not 要:#停掉
            窗口.clearInterval(自身._定时)#清掉
            自身._定时=None#记下
            return
        def 滴答():
            '到点就超时，否则刷新剩余'
            自身._滴答()#走一格
        自身._定时=窗口.setInterval(滴答,1000)#每秒

    def _滴答(自身):
        '截止时间到了就超时，否则只刷新剩余'
        截止=自身._截止#当前截止
        if 截止 is None:#定时器已经不该走
            return#停
        if 现在()>=截止:#到点
            自身.超时()#结算超时
            return
        自身._发布()#刷新剩余

    def 接上瀑布(自身,通道):
        '接上这一次转发来的瀑布。焦点或编辑会先把倒计时按住'
        自身._瀑布=通道#通道
        自身._计时等待=通道['截止'] is not None#是否计时
        if not 自身._按住 and not 自身._已动:#还没被按住
            自身._截止=通道['截止']#开始走
            if 自身._聚焦 and 通道['截止'] is not None:#焦点先到了
                剩余=通道['截止']-现在()#还剩
                if 剩余<0:#不能为负
                    剩余=0#到点
                自身._剩余毫秒=剩余#按住
                自身._截止=None#先不走
        自身._发布()#通知

    def 拆下瀑布(自身,通道):
        '这条瀑布已经结算或取消。卡片还留着'
        if 自身._瀑布 is not 通道:#不是这一条
            return#不动
        自身._瀑布=None#摘掉
        自身._计时等待=False#不再计时
        自身._截止=None#清掉截止
        自身._发布()#通知

    def 有瀑布(自身):
        '宿主这次请求还接在卡片上'
        return 自身._瀑布 is not None#还在

    def 接上远程(自身,通道):
        '问题已经继续之后，用远程把答案送回去'
        自身._远程=通道#通道
        自身._发布()#通知

    def 接上座位(自身,座位):
        '记下这块面板怎么从作曲座位撤下'
        自身._座位=座位#座位

    def 设状态(自身,状态):
        '抄投影行的 open 或 continued'
        if 自身._状态==状态:#没变
            return#不动
        自身._状态=状态#记下
        自身._发布()#通知

    def 慢慢答(自身):
        '停掉倒计时，之后一直等'
        if 自身._按住:#已经停了
            return#不动
        自身._按住=True#一直等
        自身._聚焦=False#不再算焦点
        自身._剩余毫秒=None#不恢复
        自身._截止=None#停表
        自身._发布()#通知

    def 按住焦点(自身,时刻=None):
        '焦点先到时把还没改过的倒计时按住'
        if 自身._按住 or 自身._已动 or 自身._聚焦:#已经按住或改过
            return#不动
        if 时刻 is None:#没给时刻
            时刻=现在()#现在
        if 自身._截止 is None:#没有正在走的表
            自身._剩余毫秒=None#无剩余
        else:#按住当前剩余
            剩余=自身._截止-时刻#还剩
            if 剩余<0:#不能为负
                剩余=0#到点
            自身._剩余毫秒=剩余#记下
        自身._截止=None#先停
        自身._聚焦=True#焦点按住
        自身._发布()#通知

    def 放开焦点(自身,时刻=None):
        '焦点离开后，把按住的剩余重新走起来'
        if not 自身._聚焦:#没按住
            return#不动
        if 时刻 is None:#没给时刻
            时刻=现在()#现在
        自身._聚焦=False#放开
        if 自身._计时等待 and 自身._剩余毫秒 is not None:#还有剩余
            自身._截止=时刻+自身._剩余毫秒#重新走
        else:#没有可恢复的剩余
            自身._截止=None#不走
        自身._剩余毫秒=None#已放回截止
        自身._发布()#通知

    def 开始编辑(自身,时刻=None):
        '第一次改草稿后不再用前台截止时间'
        if 自身._按住 or 自身._已动:#已经停过或改过
            return#不动
        if 时刻 is None:#没给时刻
            时刻=现在()#现在
        if 自身._剩余毫秒 is None and 自身._截止 is not None:#还在走
            剩余=自身._截止-时刻#还剩
            if 剩余<0:#不能为负
                剩余=0#到点
            自身._剩余毫秒=剩余#留下
        自身._已动=True#已经编辑
        自身._聚焦=False#不再算焦点
        自身._截止=None#停表
        自身._发布()#通知

    def 超时(自身):
        '本地倒计时到零。瀑布用超时拒绝，卡片还留着'
        if 自身._按住 or 自身._已动 or 自身._聚焦:#被按住了
            return#不超时
        通道=自身._瀑布#当前瀑布
        if 通道 is None:#没有瀑布
            return#不拒绝
        自身._瀑布=None#先摘掉
        自身._计时等待=False#不再计时
        自身._截止=None#清掉
        通道['拒绝']('ASK_TIMED_OUT')#超时
        自身._发布()#通知

    def 委托(自身):
        '把还活着的瀑布交给下一环'
        if 自身._瀑布 is not None:#还有瀑布
            自身._瀑布['委托']()#交给下一环

    def 关闭(自身):
        '从登记表拿掉。挂着的撰写器会清掉草稿'
        if 自身._已关:#已经关了
            return#不动
        自身._已关=True#记下
        自身._发布()#通知

    def 作答(自身,答案):
        '整批答案走瀑布；已经继续则走远程'
        瀑布=自身._瀑布#当前瀑布
        if 瀑布 is not None:#还在瀑布上
            def 写入():
                '把整批答案交给瀑布'
                瀑布['解决'](答案)#解决
            结算撰写(写入,'pending question settlement failed')#只结算一次
            return
        远程=自身._远程#远程通道
        if 自身._状态=='continued' and 远程 is not None:#已经继续
            接受=远程['作答'](答案)#送出
            if 接受 is not True:#已经不能回答
                raise Exception('this question is no longer answerable')#拒绝
            return
        raise Exception('no channel accepts an answer yet')#还没有通道

    def 收起(自身):
        '带调用标识的只离开座位。没点名的则取消这次请求'
        if 自身.dismissal=='hide':#还能从工具调用打开
            def 隐藏():
                '从作曲座位撤下面板'
                if 自身._座位 is not None:#有座位
                    自身._座位['隐藏']()#撤下
            结算撰写(隐藏,'pending question hide failed')#只撤一次
            return
        瀑布=自身._瀑布#当前瀑布
        if 瀑布 is None:#不能取消
            raise Exception('no channel accepts a cancellation yet')#还没有通道
        def 取消():
            '用取消码拒绝瀑布'
            瀑布['拒绝']('ASK_CANCELLED')#取消
        结算撰写(取消,'pending question cancellation failed')#只取消一次

'非所有者对等端的远程方法访问控制'
import json#主体身份按键序稳定的 JSON 比较
import threading#快照代际等待
from ...类型化远程调用.协议 import 远程服务,远程 as _远程#远程服务与流方法标记
from .快照 import 远程访问快照键#页面注入键

包名='@deepseek-ai/dsh-api-remote-access'#npm 包名
跟随动作='remoteAccess/follow'#每个对等端都能读自己的快照
允许={'kind':'allow'}#允许
无允许={'kind':'deny','reason':'no-allow'}#没有策略或没有绑定允许
策略失败={'kind':'deny','reason':'policy-failed'}#策略抛错
所有者主体={'kind':'owner'}#所有者不受检查
所有者基线={'type':'baseline','owner':True}#所有者快照只有这一帧
已允许={'kind':'allow'}#求值内部的允许
已失败={'kind':'failed'}#求值内部的失败

def 已中止(信号):
    '信号按 _事件 定死。无信号视为未中止'
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#置位即中止

def 主体于(调用):
    '远程调用上的非所有者主体。所有者与调用外都是空'
    if 调用 is None:#不在远程调用里
        return None#可信进程内
    对等=调用['peer'] if isinstance(调用,dict) else getattr(调用,'peer',None)#对等端
    主体=None if 对等 is None else (对等['principal'] if isinstance(对等,dict) and 'principal' in 对等 else getattr(对等,'principal',None))#主体
    if 主体 is None or 主体['kind']=='owner':#所有者不当成受限主体
        return None#空
    return 主体#非所有者

def 规范json(值):
    '键序无关的 JSON 文本，用来比较主体'
    if isinstance(值,list):#数组
        return '['+','.join(规范json(项) for 项 in 值)+']'#逐项
    if isinstance(值,dict):#对象
        键列表=sorted(值)#键序
        return '{'+','.join(json.dumps(键)+':'+规范json(值[键]) for 键 in 键列表)+'}'#稳定键序
    return json.dumps(值)#标量

def 同一资源(左,右):
    '种类相同且标识相同。global 没有标识'
    return 左['kind']==右['kind'] and 左.get('id')==右.get('id')#种类与标识

def 同一动作(左,右):
    '动作列表按顺序逐项相同'
    if len(左)!=len(右):#长度不同
        return False#不同
    for 下标,动作 in enumerate(左):#逐项
        if 动作!=右[下标]:#某一项不同
            return False#不同
    return True#相同

def 等到中止(信号):
    '阻塞到这一代被取消'
    if 已中止(信号):#已经取消
        return#不必再等
    信号._事件.wait()#阻塞

class 访问跟随者:
    '一个打开的非所有者快照代际。变化合并到读者被唤醒'
    def __init__(自身,主体):
        '主体是这一代的调用者，不会是所有者'
        自身.主体=主体#调用者
        自身.已脏=False#是否有未读变化
        自身._唤醒=threading.Event()#唤醒读者

    def 触碰(自身):
        '标成过期并唤醒读者'
        自身.已脏=True#有变化
        自身._唤醒.set()#唤醒

    def 已变化(自身,信号):
        '等到过期或取消。过期为真，取消为假'
        while not 自身.已脏 and not 已中止(信号):#还干净且仍活着
            自身._唤醒.wait(0.05)#短等，取消也能退出
        自身.已脏=False#这一轮已消费
        return not 已中止(信号)#取消则停

class 远程访问服务(远程服务):
    '策略登记表、网关判定、列表过滤，以及每个对等端的访问快照'
    def __init__(自身,上下文):
        '以 remoteAccess 登记，卸载时结束全部快照代际'
        super().__init__(上下文,'remoteAccess')#服务键
        自身.策略表={}#种类到策略
        自身.已报告=set()#上次作废以来已经记过失败的策略
        自身.跟随者集合=set()#打开的非所有者代际
        自身.寿命=threading.Event()#卸载时置位
        def 登记寿命():
            '卸载时结束全部打开的快照代际'
            def 拆除():
                '置位寿命，正在等的代际退出'
                自身.寿命.set()#取消
            return 拆除#交给纤程
        上下文.副作用(登记寿命,'remoteAccess: snapshot generations')#卸载钩子
        def 注入首页(网页上下文):
            '网页首页注入行先放所有者基线'
            def 写入(表):
                '追加全局注入行'
                表.append({'kind':'global','name':远程访问快照键,'value':所有者基线})#所有者基线
            网页上下文.监听('webserver/index-inject',写入)#首页注入
        上下文.inject(['webServer'],注入首页)#有网页服务才挂

    def 登记策略(自身,种类,策略):
        '为一个非所有者主体种类登记策略。重复登记抛错。返回拆除器'
        if 种类 in 自身.策略表:#已有
            raise RuntimeError('remote access: principal kind '+json.dumps(种类)+' already has a policy')#重复
        条目={'kind':种类,'policy':策略}#这一条
        def 安装():
            '进入作用域时登记，离开时撤掉'
            自身.策略表[种类]=条目#登记
            自身.作废快照()#重算打开的快照
            def 撤掉():
                '撤掉这一条并重算'
                自身.策略表.pop(种类,None)#撤
                自身.作废快照()#重算
            return 撤掉#拆除
        拆除=自身.ctx.副作用(安装,'remoteAccess.registerPolicy('+json.dumps(种类)+')')#作用域
        def 拆除器():
            '调用方拆除这一次登记'
            拆除()#撤
        return 拆除器#返回

    def 作废快照(自身,主体=None):
        '通知绑定或条件答案可能已变。省略主体则作废全部'
        自身.已报告.clear()#下次失败再记日志
        键=None if 主体 is None else 规范json(主体)#指定主体
        for 跟随者 in list(自身.跟随者集合):#打开的代际
            if 键 is None or 规范json(跟随者.主体)==键:#命中
                跟随者.触碰()#唤醒

    def 判定访问(自身,请求):
        '判定一次已解析资源的请求。所有者与 remoteAccess/follow 直接允许'
        主体=请求['principal']#调用者
        动作=请求['action']#动作
        if 主体['kind']=='owner' or 动作==跟随动作:#所有者或读自己的快照
            return 允许#允许
        条目=自身.策略表.get(主体['kind'])#该种类的策略
        if 条目 is None:#没有策略
            return 无允许#拒绝
        绑定列表=自身._绑定于(条目,主体,动作)#一次绑定
        if 绑定列表 is None:#策略抛错
            return 策略失败#失败
        for 资源 in 请求['resources']:#每一项资源都要允许
            求值=自身._求值(条目,绑定列表,动作,资源,请求.get('args'))#这一项
            if 求值['kind']=='allow':#这项过了
                continue#下一项
            if 求值['kind']=='failed':#条件抛错
                return 策略失败#失败
            拒绝=求值.get('refusal')#第一个拒绝条件
            if 拒绝 is not None:#条件给了原因
                return 拒绝#用它
            return 自身._说明(条目,请求)#否则问说明
        return 允许#全部资源都允许

    def 是否允许(自身,资源):
        '在远程方法内部过滤一项资源。所有者或方法外为真'
        调用=自身.ctx.invocation#当前调用
        主体=主体于(调用)#非所有者
        if 调用 is None or 主体 is None:#方法外或所有者
            return True#不过滤
        动作=调用['request']['namespace']+'/'+调用['request']['method']#端点
        条目=自身.策略表.get(主体['kind'])#策略
        if 条目 is None:#没有
            return False#不允许
        绑定列表=自身._绑定于(条目,主体,动作)#绑定
        return 绑定列表 is not None and 自身._求值(条目,绑定列表,动作,资源,None)['kind']=='allow'#无参数判定

    def 取得快照基线(自身,主体):
        '页面在快照流接上之前使用的基线'
        if 主体['kind']=='owner':#所有者
            return 所有者基线#只有所有者帧
        return {'type':'baseline','owner':False,'grants':自身._授予于(主体)}#当前授予

    @_远程({'mode':'stream'})
    def follow(自身,信号):
        '流式交出本对等端的访问快照。先给基线，作废后再给更新与移除帧'
        if 已中止(信号):#已取消
            return#空
        主体=主体于(自身.ctx.invocation)#调用者
        if 主体 is None:#所有者或调用外
            yield 自身.取得快照基线(所有者主体)#所有者基线
            等到中止(信号)#直到取消
            return#结束
        跟随者=访问跟随者(主体)#这一代
        自身.跟随者集合.add(跟随者)#登记
        try:#代际结束就摘掉
            已发送=自身._授予于(主体)#当前授予
            yield {'type':'baseline','owner':False,'grants':已发送}#基线
            while 跟随者.已变化(信号):#有变化且未取消
                下一份=自身._授予于(主体)#新授予
                上一份=已发送#旧授予
                已发送=下一份#记下
                for 授予 in 下一份:#新增或动作变了
                    之前=None#同资源的旧授予
                    for 项 in 上一份:#找同资源
                        if 同一资源(项['resource'],授予['resource']):#命中
                            之前=项#记下
                            break#停
                    if 之前 is None or not 同一动作(之前['actions'],授予['actions']):#变了
                        yield {'type':'upsert','grant':授予}#更新
                for 授予 in 上一份:#消失的资源
                    还在=False#是否仍在
                    for 项 in 下一份:#找
                        if 同一资源(项['resource'],授予['resource']):#还在
                            还在=True#记下
                            break#停
                    if not 还在:#没了
                        yield {'type':'remove','resource':授予['resource']}#移除
        finally:#无论成败都摘掉
            自身.跟随者集合.discard(跟随者)#摘掉

    def _绑定于(自身,条目,主体,用途):
        '调用一次绑定。失败记一次日志并返回空'
        try:#策略失败只影响这一问
            return 条目['policy'].绑定(主体)#当前绑定
        except Exception as 错误:#收住
            自身._报告(条目,'list bindings for '+用途,错误)#记一次
            return None#失败

    def _求值(自身,条目,绑定列表,动作,资源,参数):
        '找资源匹配且角色列出该动作、条件允许的绑定'
        拒绝=None#第一个拒绝
        for 绑定 in 绑定列表:#逐条
            if not 同一资源(绑定['resource'],资源) or 动作 not in 绑定['role']['actions']:#不相关
                continue#下一条
            条件=绑定.get('condition')#可选条件
            if 条件 is None:#无条件即允许
                return 已允许#允许
            try:#条件抛错算策略失败
                请求={'action':动作,'resource':资源}#条件请求
                if 参数 is not None:#调用才有参数
                    请求['args']=参数#带上
                判定=条件(请求)#问条件
            except Exception as 错误:#收住
                自身._报告(条目,'evaluate a condition for '+动作,错误)#记一次
                return 已失败#失败
            if 判定['kind']=='allow':#条件允许
                return 已允许#允许
            if 拒绝 is None:#记下第一个拒绝
                拒绝=判定#原因
        return {'kind':'refuse','refusal':拒绝}#没有绑定允许

    def _说明(自身,条目,请求):
        '说明给出的原因，没有则 no-allow。说明抛错则 policy-failed'
        说明=getattr(条目['policy'],'说明',None)#可选
        原因=None#说明的原因
        try:#说明抛错算策略失败
            if 说明 is not None:#有说明
                原因=说明(请求)#问
        except Exception as 错误:#收住
            自身._报告(条目,'explain a refusal of '+请求['action'],错误)#记一次
            return 策略失败#失败
        if 原因 is None:#没有更具体的原因
            return 无允许#no-allow
        return {'kind':'deny','reason':原因}#带原因

    def _授予于(自身,主体):
        '按绑定首次出现的资源顺序，列出无参数时会被判定允许的端点动作'
        条目=自身.策略表.get(主体['kind'])#策略
        if 条目 is None:#没有
            return []#空
        绑定列表=自身._绑定于(条目,主体,'a snapshot')#绑定
        if 绑定列表 is None:#失败
            return []#空
        授予列表=[]#结果
        见过=[]#已经出过的资源
        for 绑定 in 绑定列表:#首次出现顺序
            资源=绑定['resource']#资源
            if any(同一资源(项,资源) for 项 in 见过):#已经处理
                continue#跳
            见过.append(资源)#记下
            候选=set()#非事件动作
            for 项 in 绑定列表:#同一资源的角色动作
                if not 同一资源(项['resource'],资源):#别的资源
                    continue#跳
                for 动作 in 项['role']['actions']:#角色动作
                    if not str(动作).startswith('event:'):#事件不进快照
                        候选.add(动作)#候选
            动作列表=sorted(动作 for 动作 in 候选 if 自身._求值(条目,绑定列表,动作,资源,None)['kind']=='allow')#允许的
            if len(动作列表)>0:#有才发授予
                授予列表.append({'resource':资源,'actions':动作列表})#一条
        return 授予列表#授予

    def _报告(自身,条目,动作,错误):
        '每个策略在下次作废前只记一次失败'
        if 条目 in 自身.已报告:#已经记过
            return#静默
        自身.已报告.add(条目)#记下
        自身.ctx.logger.warn('remote access: the '+json.dumps(条目['kind'])+' policy failed to '+动作+'; its further failures are not logged until access state changes')#一次
        自身.ctx.logger.warn(错误)#原因

__all__=['包名','远程访问服务','默认','跟随动作','远程访问快照键']
默认=远程访问服务#框架槽
default=默认#框架槽

'有界共享与独占预留未发布 Session'
from ...基础设施.js特性 import PromiseEX as 期约#中文别名的期约
from ...基础设施.通用工具 import 启动守护线程#转发中止的监视线程
from .异常 import 持久化错误,中止错误#本包异常

def 已中止(信号):
    '信号按 Event 定死。无信号视为未中止'
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event 已置位

def 若已中止则抛出(信号):
    '已中止则抛出承载原因的异常'
    if not 已中止(信号):#无信号或仍活着
        return#仍活着
    if 信号.原因 is not None:#有承载异常
        raise 信号.原因#抛出
    raise 中止错误()#默认中止

def 尚未越过截止():
    '排队观察默认尚未越过截止'
    return False#尚未开始

def 观察排队取消(操作,信号,已开始=None):
    '给排队观察者一份即时取消视图，而不取消共享工作。返回期约'
    if 已开始 is None:#缺省未开始
        已开始=尚未越过截止#尚未越过截止
    if 信号 is None:#无取消
        return 操作#直接返回共享操作
    包装=期约()#观察包装
    def 共享成功(值):
        '共享成功：包装尚未被取消结算时才跟随'
        if 包装.状态=='pending':#只结算一次
            包装.解决(值)#解决观察
    def 共享失败(原因):
        '共享失败：包装尚未被取消结算时才跟随'
        if 包装.状态=='pending':#只结算一次
            包装.拒绝(原因)#原样拒绝
    def 在取消():
        '观察者取消：尚未越过截止则即时拒绝'
        if 已开始():#已越过截止则忽略
            return#忽略
        if 包装.状态!='pending':#已结算
            return#无事
        try:
            若已中止则抛出(信号)#应抛中止错误
        except BaseException as 原因:#拿到原因
            包装.拒绝(原因)#原样拒绝
            return
        包装.拒绝(中止错误('queued observation abort event lacked an aborted signal'))#无中止却收到取消
    def 转发中止():
        '等到来源置位后拒绝观察包装'
        信号.等待()#阻塞到中止
        在取消()#转发取消
    操作.然后(共享成功,共享失败)#跟随共享操作
    if 已中止(信号):#已经取消
        在取消()#立刻处理
    else:
        启动守护线程(转发中止)#转发中止线程
    return 包装#观察期约

会话预备预留字段=('entry','source','state')#一份独占持有的预备源及其已提交持久化状态（所属条目、预备源、已提交状态）
预备源字段=('session',)#预备源最小字段：未发布 Session
预备阶段=('loading','ready','committing','reserved')#预备条目阶段词表
预备条目字段=('id','result','phase','source','reservation','reservationSettled','settleReservation')#预备池条目字段约定

class 会话预备池:
    '每协调器的冷读共享、独占预留与就绪条目 LRU'
    def __init__(自身,容量):
        '记下 LRU 容量'
        自身.容量=容量#LRU容量
        自身.条目={}#id到条目；插入序作LRU

    def 有(自身,标识):
        '本池当前是否知道一个未发布身份'
        return 标识 in 自身.条目#查表

    def 检查(自身,标识,加载,信号=None):
        '观察一份预备源，同一 id 的在途读取共享。返回期约，解决值是预备源'
        结果=期约()#本次检查的结算点
        条目=自身.取或建条目(标识,加载)#取或创建条目
        观察=条目['result'] if 信号 is None else 观察排队取消(条目['result'],信号)#带取消则套观察
        def 已加载(加载结果):
            '加载完成：取条目上的源，没有就用加载结果，就绪则触碰LRU'
            源=条目['source'] if 'source' in 条目 else None#条目上的源
            if 源 is None:#尚未挂源
                源=加载结果#用加载结果
            if 自身.条目.get(标识) is 条目 and 条目['phase']=='ready':#就绪则触碰LRU
                自身.触碰(条目)#触碰
            结果.解决(源)#返回源
        观察.然后(已加载,结果.拒绝)#等加载
        return 结果#调用方对期约链接 然后 与 捕获

    def 预留(自身,标识,加载,提交,信号=None):
        '在提交其挂起的耐久修复后预留一份就绪源。返回期约，解决值是预留或 None'
        结果=期约()#本次预留的结算点
        条目=自身.取或建条目(标识,加载)#取或创建条目
        def 提交预留():
            '别人的预留结束后：提交耐久修复并构造预留'
            if 自身.条目.get(标识) is not 条目:#条目已失效
                结果.解决(None)#无预留
                return
            源=条目['source']#就绪源
            结算任务=期约()#新的结算
            条目['phase']='committing'#进入提交
            条目['reservationSettled']=结算任务#挂上等待
            条目['settleReservation']=结算任务.解决#挂上结算
            def 提交失败(错误):
                '提交失败：摘掉条目后拒绝'
                自身.摘掉(条目)#摘掉条目
                结果.拒绝(错误)
            def 提交完成(已提交):
                '耐久修复完成：为空则丢弃，否则换上提交后的源并构造预留'
                if 已提交 is None:#提交决定丢弃
                    自身.摘掉(条目)#摘掉
                    结果.解决(None)#无预留
                    return
                条目['source']=已提交['source']#换上提交后的源
                try:
                    若已中止则抛出(信号)#已取消则失败
                except BaseException as 错误:#取消，放回就绪后拒绝
                    自身.标就绪(条目)#放回就绪
                    结果.拒绝(错误)
                    return
                if 自身.条目.get(标识) is not 条目:#条目已失效
                    结果.解决(None)#无预留
                    return
                预留={'entry':条目,'source':已提交['source'],'state':已提交['state']}#构造预留
                条目['phase']='reserved'#进入预留
                条目['reservation']=预留#挂上预留
                结果.解决(预留)#返回预留
            try:
                提交期约=提交(源)#耐久修复，返回期约
            except BaseException as 错误:#提交同步失败
                提交失败(错误)
                return
            提交期约.然后(提交完成,提交失败)#等耐久修复
        def 等预留结束(等待结果=None):
            '等别人的预留结束；仍在预留则继续等，否则提交'
            if not (自身.条目.get(标识) is 条目 and 条目['phase']!='ready'):#没有别人的预留了
                提交预留()
                return
            结算=条目['reservationSettled'] if 'reservationSettled' in 条目 else None#预留结算期约
            if 结算 is None:#丢失等待者
                结果.拒绝(持久化错误('session "'+str(标识)+'" preparation lost its reservation waiter'))#丢失等待者
                return
            观察结算=结算 if 信号 is None else 观察排队取消(结算,信号)#带取消则套观察
            观察结算.然后(等预留结束,结果.拒绝)#等待
        加载观察=条目['result'] if 信号 is None else 观察排队取消(条目['result'],信号)#带取消则套观察
        加载观察.然后(等预留结束,结果.拒绝)#等加载
        return 结果#调用方对期约链接 然后 与 捕获

    def 按会话取预留(自身,会话):
        '返回 Session 发布用的精确预留，拒绝别名'
        条目=自身.条目.get(会话.id)#查条目
        if 条目 is None:#无条目
            return None#无预备
        标识=条目['id']#会话id
        源=条目['source'] if 'source' in 条目 else None#源
        源会话=None if 源 is None else 源['session']#精确会话
        if 条目['phase']=='reserved' and 源会话 is 会话 and 条目.get('reservation') is not None:#精确匹配预留
            return 条目['reservation']#返回预留
        raise 持久化错误('cannot publish session "'+str(标识)+'": persisted state already owns this identity')#别名或非预留

    def 附着(自身,预留):
        '在其精确 Session 已挂接后消费一份预留'
        条目=预留['entry']#所属条目
        if 自身.条目.get(条目['id']) is not 条目 or 条目.get('reservation') is not 预留:#不再是这份预留
            raise 持久化错误('session "'+str(条目['id'])+'" preparation is no longer reserved')#预留已失效
        自身.摘掉(条目)#摘掉条目

    def 丢弃(自身,预留):
        '消费一份调用方只需要已提交检查的预留'
        条目=预留['entry']#所属条目
        if 自身.条目.get(条目['id']) is not 条目 or 条目.get('reservation') is not 预留:#已不是这份
            return#无事
        自身.摘掉(条目)#摘掉

    def 释放(自身,预留,可复用):
        '把可复用的未发布预留放回就绪 LRU'
        条目=预留['entry']#所属条目
        if 自身.条目.get(条目['id']) is not 条目 or 条目.get('reservation') is not 预留 or 条目['phase']!='reserved':#已不是这份预留
            return#无事
        if not 可复用:#不可复用
            自身.摘掉(条目)#摘掉
            return
        条目.pop('reservation',None)#清预留
        自身.标就绪(条目)#放回就绪

    def 使失效(自身,标识):
        '耐久日志变化后丢弃一份预备视图'
        条目=自身.条目.get(标识)#查条目
        if 条目 is not None:#有则摘掉
            自身.摘掉(条目)#摘掉

    def 丢弃就绪(自身,标识,期望):
        '丢弃一份精确的陈旧就绪源，不打扰独占拥有方'
        条目=自身.条目.get(标识)#查条目
        if 条目 is None or 条目.get('source') is not 期望:#不是这份源
            return 'missing'#缺失
        if 条目['phase']!='ready':#被预留占用
            return 'retained'#保留
        自身.摘掉(条目)#摘掉就绪
        return 'discarded'#已丢弃

    def 断言可写(自身,标识):
        '未发布 Session 独占预留该 id 时拒绝写入'
        条目=自身.条目.get(标识)#当前条目
        阶段=None if 条目 is None else 条目['phase']#当前阶段
        if 阶段=='committing' or 阶段=='reserved':#独占中
            raise 持久化错误('cannot append session "'+str(标识)+'" while its persisted preparation is reserved')#拒绝追加

    def 取走就绪(自身,标识):
        '为已经串行化的追加采纳移除一份完成条目'
        条目=自身.条目.get(标识)#查条目
        if 条目 is None or 条目['phase']!='ready' or 'source' not in 条目:#非就绪
            return None#无就绪
        源=条目['source']#源
        自身.摘掉(条目)#摘掉
        return 源#返回源

    def 取或建条目(自身,标识,加载):
        '取或创建条目'
        已有=自身.条目.get(标识)#已有条目
        if 已有 is not None:#复用
            return 已有#复用
        延迟=期约()#延迟结果
        条目={'id':标识,'result':延迟,'phase':'loading'}#新条目
        自身.条目[标识]=条目#入表
        def 加载失败(错误):
            '加载失败：摘掉条目并拒绝观察者'
            自身.摘掉(条目)#摘掉
            延迟.拒绝(错误)#拒绝观察者
        def 加载完成(源):
            '挂上源并决议观察者'
            try:
                if 自身.条目.get(标识) is 条目:#仍是本条目
                    条目['source']=源#挂上源
                    自身.标就绪(条目)#标就绪
                延迟.解决(源)#决议观察者
            except BaseException as 错误:#挂源失败
                加载失败(错误)
        try:
            加载期约=加载()#启动冷加载，返回期约
        except BaseException as 错误:#同步失败
            加载失败(错误)
            return 条目#返回已失败条目
        加载期约.然后(加载完成,加载失败)#等冷加载
        return 条目#返回条目

    def 标就绪(自身,条目):
        '标就绪'
        if 自身.条目.get(条目['id']) is not 条目:#已不是本条目
            return#无事
        条目['phase']='ready'#就绪
        结算=条目.pop('settleReservation',None)#取出结算
        条目.pop('reservationSettled',None)#清等待
        if 结算 is not None:#有结算
            结算()#唤醒等待者
        自身.触碰(条目)#触碰LRU

    def 摘掉(自身,条目):
        '摘掉条目'
        if 自身.条目.get(条目['id']) is not 条目:#已不是本条目
            return#无事
        del 自身.条目[条目['id']]#从表删除
        结算=条目.pop('settleReservation',None)#取出结算
        条目.pop('reservationSettled',None)#清等待
        if 结算 is not None:#有结算
            结算()#唤醒等待者

    def 触碰(自身,条目):
        'LRU 触碰'
        标识=条目['id']#会话id
        if 标识 in 自身.条目:#先摘掉
            del 自身.条目[标识]#摘掉
        自身.条目[标识]=条目#再插到末尾
        就绪数=0#就绪计数
        for 候选 in 自身.条目.values():#数就绪
            if 候选['phase']=='ready':#就绪
                就绪数+=1#就绪加一
        if 就绪数<=自身.容量:#未超容量
            return#无事
        for 键,候选 in list(自身.条目.items()):#淘汰最旧就绪
            if 候选['phase']!='ready':#跳过非就绪
                continue#下一条
            del 自身.条目[键]#删最旧就绪
            return#只删一个

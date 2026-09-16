"""有界共享与独占预留未发布 Session。"""
import threading#后台观察与加载
from threading import Event as 事件#单次操作结算门

class 持久化错误(Exception):
    """会话持久化包的异常基类。"""

class 中止错误(持久化错误):
    """取消通道已中止。"""
    def __init__(自身,消息='aborted',种类=None):
        """用消息与可选控制流种类构造。"""
        super().__init__(消息)#错误消息原样英文
        if 种类 is not None:#有控制流种类
            自身.种类=种类#按结构识别，不做类型嗅探

class 操作任务:
    """单次操作结算；只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._完成=事件()#结算门
        自身._值=None#成功值
        自身._错误=None#失败原因

    def 兑现(自身,值=None):
        """成功结算。"""
        if 自身._完成.is_set():#已结算
            return 值#幂等
        自身._值=值#记下
        自身._完成.set()#开门
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算；非异常则包成本包错误。"""
        if 自身._完成.is_set():#已结算
            return#幂等
        if isinstance(错误,BaseException):#已是异常
            自身._错误=错误#原样
        else:#非异常
            包装=持久化错误('task rejected')#包装拒绝
            包装.原因=错误#附加信息做成属性
            自身._错误=包装#记下
        自身._完成.set()#开门

    def 等待(自身,超时=None):
        """阻塞等到结算；失败原样抛。"""
        if not 自身._完成.wait(超时):#超时未结算
            raise TimeoutError('operation timed out')#超时
        if 自身._错误 is not None:#失败
            raise 自身._错误#原样抛
        return 自身._值#成功值

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出承载原因的异常。"""
    if 信号 is None:#无信号
        return#无信号
    if not 信号._事件.is_set():#仍活着
        return#仍活着
    if 信号._异常 is not None:#有承载异常
        raise 信号._异常#抛出
    raise 中止错误()#默认中止

def 尚未越过截止():
    """排队观察默认尚未越过截止。"""
    return False#尚未开始

def 观察排队取消(操作,信号,已开始=None):
    """给排队观察者一份即时取消视图，而不取消共享工作。"""
    if 已开始 is None:#缺省未开始
        已开始=尚未越过截止#尚未越过截止
    if 信号 is None:#无取消
        return 操作#直接返回共享操作
    包装=操作任务()#观察包装
    已结算=[False]#是否已结算
    def 完成(回调):
        """只结算一次。"""
        if 已结算[0]:#已结算
            return#无事
        已结算[0]=True#标记
        回调()#执行结算
    def 兑现包装(值):
        """共享成功。"""
        def 写下():
            """写入包装兑现。"""
            包装.兑现(值)#兑现观察
        完成(写下)#只结算一次
    def 拒绝包装(原因):
        """共享失败。"""
        def 写下():
            """写入包装拒绝。"""
            包装.拒绝(原因)#原样拒绝
        完成(写下)#只结算一次
    def 在取消():
        """观察者取消。"""
        if 已开始():#已越过截止则忽略
            return#忽略
        def 即时拒绝():
            """即时拒绝。"""
            try:
                若已中止则抛出(信号)#应抛中止错误
            except BaseException as 原因:#拿到原因
                包装.拒绝(原因)#原样拒绝
                return#结束
            包装.拒绝(中止错误('queued observation abort event lacked an aborted signal'))#无中止却收到取消
        完成(即时拒绝)#即时拒绝
    def 观察共享():
        """后台等共享操作。"""
        try:
            值=操作.等待()#等待共享任务
            兑现包装(值)#成功
        except BaseException as 原因:#失败
            拒绝包装(原因)#失败
    def 转发中止():
        """等到来源置位后拒绝观察包装。"""
        信号._事件.wait()#阻塞到中止
        在取消()#转发取消
    线程=threading.Thread(target=观察共享)#后台
    线程.daemon=True#不挡退出
    线程.start()#启动
    if 已中止(信号):#已经取消
        在取消()#立刻处理
    else:
        中止监视线程=threading.Thread(target=转发中止)#转发中止线程
        中止监视线程.daemon=True#不挡退出
        中止监视线程.start()#启动
    return 包装#观察任务

会话预备预留字段=('entry','source','state')#一份独占持有的预备源及其已提交持久化状态（所属条目、预备源、已提交状态）
预备源字段=('session',)#预备源最小字段：未发布 Session
预备阶段=('loading','ready','committing','reserved')#预备条目阶段词表
预备条目字段=('id','result','phase','source','reservation','reservationSettled','settleReservation')#预备池条目字段约定

class 会话预备池:
    """每协调器的冷读共享、独占预留与就绪条目 LRU。"""
    def __init__(自身,容量):
        """记下 LRU 容量。"""
        自身.容量=容量#LRU容量
        自身.条目={}#id到条目；插入序作LRU

    def 有(自身,标识):
        """本池当前是否知道一个未发布身份。"""
        return 标识 in 自身.条目#查表

    def 检查(自身,标识,加载,信号=None):
        """观察一份预备源，同一 id 的在途读取共享。"""
        条目=自身.取或建条目(标识,加载)#取或创建条目
        if 信号 is None:#无取消
            已加载=条目['result'].等待()#直接等加载
        else:
            已加载=观察排队取消(条目['result'],信号).等待()#带取消
        源=条目['source'] if 'source' in 条目 else None#条目上的源
        if 源 is None:#尚未挂源
            源=已加载#用加载结果
        if 自身.条目.get(标识) is 条目 and 条目['phase']=='ready':#就绪则触碰LRU
            自身.触碰(条目)#触碰
        return 源#返回源

    def 预留(自身,标识,加载,提交,信号=None):
        """在提交其挂起的耐久修复后预留一份就绪源。"""
        条目=自身.取或建条目(标识,加载)#取或创建条目
        if 信号 is None:#无取消
            条目['result'].等待()#等加载
        else:
            观察排队取消(条目['result'],信号).等待()#等加载
        while 自身.条目.get(标识) is 条目 and 条目['phase']!='ready':#等别人的预留结束
            结算=条目['reservationSettled'] if 'reservationSettled' in 条目 else None#预留结算任务
            if 结算 is None:#丢失等待者
                raise 持久化错误('session "'+str(标识)+'" preparation lost its reservation waiter')#丢失等待者
            if 信号 is None:#无取消则直接等
                结算.等待()#等待
            else:
                观察排队取消(结算,信号).等待()#等待
        if 自身.条目.get(标识) is not 条目:#条目已失效
            return None#无预留
        源=条目['source']#就绪源
        结算任务=操作任务()#新的结算
        条目['phase']='committing'#进入提交
        条目['reservationSettled']=结算任务#挂上等待
        条目['settleReservation']=结算任务.兑现#挂上结算
        已提交=None#提交结果
        try:
            已提交=提交(源)#耐久修复
        except BaseException:#提交失败
            自身.摘掉(条目)#摘掉条目
            raise#上抛
        if 已提交 is None:#提交决定丢弃
            自身.摘掉(条目)#摘掉
            return None#无预留
        条目['source']=已提交['source']#换上提交后的源
        try:
            若已中止则抛出(信号)#已取消则失败
        except BaseException:#取消
            自身.标就绪(条目)#放回就绪
            raise#上抛取消
        if 自身.条目.get(标识) is not 条目:#条目已失效
            return None#无预留
        预留={'entry':条目,'source':已提交['source'],'state':已提交['state']}#构造预留
        条目['phase']='reserved'#进入预留
        条目['reservation']=预留#挂上预留
        return 预留#返回预留

    def 按会话取预留(自身,会话):
        """返回 Session 发布用的精确预留，拒绝别名。"""
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
        """在其精确 Session 已挂接后消费一份预留。"""
        条目=预留['entry']#所属条目
        if 自身.条目.get(条目['id']) is not 条目 or 条目.get('reservation') is not 预留:#不再是这份预留
            raise 持久化错误('session "'+str(条目['id'])+'" preparation is no longer reserved')#预留已失效
        自身.摘掉(条目)#摘掉条目

    def 丢弃(自身,预留):
        """消费一份调用方只需要已提交检查的预留。"""
        条目=预留['entry']#所属条目
        if 自身.条目.get(条目['id']) is not 条目 or 条目.get('reservation') is not 预留:#已不是这份
            return#无事
        自身.摘掉(条目)#摘掉

    def 释放(自身,预留,可复用):
        """把可复用的未发布预留放回就绪 LRU。"""
        条目=预留['entry']#所属条目
        if 自身.条目.get(条目['id']) is not 条目 or 条目.get('reservation') is not 预留 or 条目['phase']!='reserved':#已不是这份预留
            return#无事
        if not 可复用:#不可复用
            自身.摘掉(条目)#摘掉
            return#结束
        条目.pop('reservation',None)#清预留
        自身.标就绪(条目)#放回就绪

    def 使失效(自身,标识):
        """耐久日志变化后丢弃一份预备视图。"""
        条目=自身.条目.get(标识)#查条目
        if 条目 is not None:#有则摘掉
            自身.摘掉(条目)#摘掉

    def 丢弃就绪(自身,标识,期望):
        """丢弃一份精确的陈旧就绪源，不打扰独占拥有方。"""
        条目=自身.条目.get(标识)#查条目
        if 条目 is None or 条目.get('source') is not 期望:#不是这份源
            return 'missing'#缺失
        if 条目['phase']!='ready':#被预留占用
            return 'retained'#保留
        自身.摘掉(条目)#摘掉就绪
        return 'discarded'#已丢弃

    def 断言可写(自身,标识):
        """未发布 Session 独占预留该 id 时拒绝写入。"""
        条目=自身.条目.get(标识)#当前条目
        阶段=None if 条目 is None else 条目['phase']#当前阶段
        if 阶段=='committing' or 阶段=='reserved':#独占中
            raise 持久化错误('cannot append session "'+str(标识)+'" while its persisted preparation is reserved')#拒绝追加

    def 取走就绪(自身,标识):
        """为已经串行化的追加采纳移除一份完成条目。"""
        条目=自身.条目.get(标识)#查条目
        if 条目 is None or 条目['phase']!='ready' or 条目.get('source') is None:#非就绪
            return None#无就绪
        源=条目['source']#源
        自身.摘掉(条目)#摘掉
        return 源#返回源

    def 取或建条目(自身,标识,加载):
        """取或创建条目。"""
        已有=自身.条目.get(标识)#已有条目
        if 已有 is not None:#复用
            return 已有#复用
        延迟=操作任务()#延迟结果
        条目={'id':标识,'result':延迟,'phase':'loading'}#新条目
        自身.条目[标识]=条目#入表
        try:
            源=加载()#启动冷加载并拿到源
        except BaseException as 错误:#同步失败
            自身.摘掉(条目)#摘掉
            延迟.拒绝(错误)#拒绝观察者
            return 条目#返回已失败条目
        def 观察加载():
            """后台挂上源并决议观察者。"""
            try:
                if 自身.条目.get(标识) is 条目:#仍是本条目
                    条目['source']=源#挂上源
                    自身.标就绪(条目)#标就绪
                延迟.兑现(源)#决议观察者
            except BaseException as 错误:#挂源失败
                自身.摘掉(条目)#摘掉
                延迟.拒绝(错误)#拒绝观察者
        线程=threading.Thread(target=观察加载)#后台加载
        线程.daemon=True#不挡退出
        线程.start()#启动
        return 条目#返回条目

    def 标就绪(自身,条目):
        """标就绪。"""
        if 自身.条目.get(条目['id']) is not 条目:#已不是本条目
            return#无事
        条目['phase']='ready'#就绪
        结算=条目.pop('settleReservation',None)#取出结算
        条目.pop('reservationSettled',None)#清等待
        if 结算 is not None:#有结算
            结算()#唤醒等待者
        自身.触碰(条目)#触碰LRU

    def 摘掉(自身,条目):
        """摘掉条目。"""
        if 自身.条目.get(条目['id']) is not 条目:#已不是本条目
            return#无事
        del 自身.条目[条目['id']]#从表删除
        结算=条目.pop('settleReservation',None)#取出结算
        条目.pop('reservationSettled',None)#清等待
        if 结算 is not None:#有结算
            结算()#唤醒等待者

    def 触碰(自身,条目):
        """LRU 触碰。"""
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

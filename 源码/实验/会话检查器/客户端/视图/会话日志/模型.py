'按会话窗口增量投影原始行，助手流的子行不丢增量'

from ......客户端.存储 import 创建快照存储#行和记录的可观察仓
from ......模型后端.llm.助手流 import 展开助手流#耐久流拆回带时增量
from .分组 import 会话日志分组#回合和步骤祖先
from .流 import 助手日志流#一块助手流

class 会话日志模型:
    '会话自己的日志投影。只有表格在看的时候才订阅事件窗'
    def __init__(自身,源):
        '先收下当前窗口。订阅留到表格开始看'
        自身.源=源#会话事件窗
        自身.行仓=创建快照存储([])#表格顺序
        自身.记录={}#行键到记录仓
        自身.根列表=[]#每条根事件
        自身.尝试={}#活动尝试
        自身.分组=会话日志分组()#当前范围
        自身.已结算根={}#序号到仍在窗口里的活动行键
        自身.流缓存={}#耐久流身份到展开结果
        自身.修订=-1#已收下的修订
        自身.订阅数=0#正在看的人数
        自身.断开=None#事件窗退订
        自身.接受中=False#收下过程中不把每一条记录单独扇出去
        自身.行监听=[]#表格监听
        自身.记录停={}#记录仓到退订
        自身.接受(源.getSnapshot())#构造时先有第一份

    def getSnapshot(自身):
        '当前表格顺序。单元格内容在各自的记录仓里'
        return 自身.行仓.getSnapshot()#行列表

    def 聊天锚(自身,键):
        '选中行对应的原始事件。子行再带上那一块增量'
        自身.接受(自身.源.getSnapshot())#先对齐窗口
        根=None#拥有这行的事件
        for 候选 in 自身.根列表:#逐根
            根键=候选['row']['key']#根行键
            if 根键==键 or (候选['stream'] is not None and 键.startswith(根键+'/chunk:')):#根或它的增量
                根=候选#找到
                break#停
        if 根 is None:#行已经不在
            return None#没有锚
        仓=自身.记录.get(键)#记录仓
        if 仓 is None:#没有记录
            return None#没有锚
        记录=仓.getSnapshot()#当前记录
        if 记录 is None:#已清空
            return None#没有锚
        锚={'event':根['entry']['event']}#原始事件
        if 根['row']['key']!=键:#选的是增量行
            锚['chunk']=记录['value']#这一块增量
        return 锚#交给对话定位

    def 选取(自身,目标):
        '在已加载日志里找被点中的对话对象，不造新记录'
        窗=自身.源.getSnapshot()#当前窗口
        自身.接受(窗)#对齐
        条目列表=窗.entries#已加载条目

        def 同一步(条目):
            '回合必须相同。点了步骤时步骤也要相同'
            数据=条目['event'].get('data') if isinstance(条目.get('event'),dict) else None#事件数据
            if not isinstance(数据,dict) or 目标.get('turn') is None:#没有回合
                return False#不是
            if 数据.get('turn')!=目标.get('turn'):#回合不同
                return False#不是
            if 目标.get('step') is None:#只要求回合
                return True#是
            return 数据.get('step')==目标.get('step')#步骤也相同

        调用=None#工具调用行
        if 目标.get('callId') is not None:#点了调用
            for 条目 in 条目列表:#找调用
                事件=条目.get('event') or {}#事件
                数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#数据
                if 事件.get('type')=='tool/call' and 数据.get('callId')==目标.get('callId'):#同一调用
                    调用=条目#命中
                    break#停
        锚条目=None#序号相同的行
        if 目标.get('anchorSeq') is not None:#有序号
            for 条目 in 条目列表:#找序号
                if (条目.get('event') or {}).get('seq')==目标.get('anchorSeq'):#同一序号
                    锚条目=条目#命中
                    break#停
        助手=None#助手步骤
        if 目标.get('nodeKind')=='assistant-step':#点的是助手
            下标=len(条目列表)-1#从后往前
            while 下标>=0:#最后一条优先
                条目=条目列表[下标]#这一条
                事件=条目.get('event') or {}#事件
                if 同一步(条目) and (事件.get('type') in ('assistant/message','assistant/attempt') or 条目.get('type')=='transient'):#同一步的助手
                    助手=条目#命中
                    break#停
                下标=下标-1#更早一条
        步骤=None#步骤开始
        if 目标.get('step') is not None:#有步骤
            for 条目 in 条目列表:#找开始
                事件=条目.get('event') or {}#事件
                if 事件.get('type')=='step/start' and 同一步(条目):#同一步的开始
                    步骤=条目#命中
                    break#停
        回合=None#回合开始
        if 目标.get('turn') is not None:#有回合
            for 条目 in 条目列表:#找开始
                事件=条目.get('event') or {}#事件
                数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#数据
                if 事件.get('type')=='turn/start' and 数据.get('turn')==目标.get('turn'):#这个回合
                    回合=条目#命中
                    break#停
        兜底=None#同一步的任意行
        for 条目 in 条目列表:#最后兜底
            if 同一步(条目):#同一步
                兜底=条目#第一份
                break#停
        条目=调用 or 锚条目 or 助手 or 步骤 or 回合 or 兜底#按优先级
        if 条目 is None:#都没有
            return None#没有行
        if 条目.get('type')=='transient':#活动尝试
            键='attempt:'+str(条目['event']['data']['attemptId'])#尝试行
        else:#耐久事件
            序号=条目['event']['seq']#序号
            键=自身.已结算根.get(序号)#结算后仍用尝试键
            if 键 is None:#普通事件
                键='event:'+str(序号)#事件行
        if 目标.get('groupPart')=='reasoning':#推理部位优先块开始子行
            for 行 in 自身.行仓.getSnapshot():#在当前顺序里找
                if 行.get('parent')!=键:#不是这个助手的子行
                    continue#下一行
                仓=自身.记录.get(行['key'])#子行记录
                值=None if 仓 is None else (仓.getSnapshot() or {}).get('value')#增量
                if isinstance(值,dict) and 值.get('type')=='block-start' and 值.get('blockType')=='reasoning':#推理块开始
                    return 行['key']#用这一子行
        return 键#根行

    def subscribe(自身,监听):
        '结构变化时通知。第一个订阅者才去订事件窗'
        停行=自身.行仓.subscribe(监听)#结构变化
        首次=自身.订阅数==0#从没有人看到有人
        自身.订阅数=自身.订阅数+1#加上
        if 首次:#开始看
            def 源变了():
                '事件窗变了就收下'
                自身.接受(自身.源.getSnapshot())#对齐
            自身.断开=自身.源.订阅(源变了)#事件源的方法是订阅
            自身.接受(自身.源.getSnapshot())#再对齐一次
        自身.行监听.append(监听)#记录变化也通知这一个
        for 仓 in 自身.记录.values():#已有记录
            自身.接记录(仓)#以后变化也扇出
        def 退订():
            '卸掉这一份，最后一个人离开时拆事件窗'
            停行()#行仓
            自身.订阅数=自身.订阅数-1#减一
            if 监听 in 自身.行监听:#还在
                自身.行监听.remove(监听)#卸掉
            if 自身.订阅数==0:#没人看了
                if 自身.断开 is not None:#有事件订阅
                    自身.断开()#拆
                自身.断开=None#清空
                for 停 in 自身.记录停.values():#记录扇出
                    停()#拆
                自身.记录停.clear()#清空
        return 退订#交给钩子

    def 行(自身,键):
        '没有记录时先给一个空仓，之后再填'
        仓=自身.记录.get(键)#已有
        if 仓 is None:#第一次
            仓=创建快照存储(None)#空记录
            自身.记录[键]=仓#留下
            自身.接记录(仓)#有人看就扇出
        return 仓#可观察记录

    def 放入(自身,键,记录):
        '值的身份没变就不替换快照'
        自身.行(键)#保证仓在
        仓=自身.记录[键]#记录仓
        当前=仓.getSnapshot()#上一份
        if 当前 is None or 当前.get('value') is not 记录['value']:#值换了
            仓.set(记录)#发布

    def 接记录(自身,仓):
        '记录自己变了也让表格重画。收下过程中由行仓统一通知'
        if 自身.订阅数==0:#没人看
            return#不订
        标识=id(仓)#仓身份
        if 标识 in 自身.记录停:#已经订过
            return#不重复
        def 转发():
            '把这一条记录的变化告诉表格'
            if 自身.接受中:#整窗还在收
                return#等行仓一次通知
            for 回调 in list(自身.行监听):#每个监听
                回调()#重画
        自身.记录停[标识]=仓.subscribe(转发)#记下退订

    def 接受(自身,窗):
        '修订没变就跳过。连续追加只加新条目，否则整窗重放'
        if 窗.revision==自身.修订:#同一修订
            return#不用重做
        自身.接受中=True#先别逐条扇出
        变更=窗.change#这次变更
        if 变更.get('kind')=='settle-assistant' and 变更.get('entry') is not None:#活动行落成耐久
            父='attempt:'+str(变更.get('attemptId'))#尝试键
            if 父 in 自身.尝试:#这份尝试还在
                自身.已结算根[变更['entry']['event']['seq']]=父#序号仍指向尝试行
        追加=窗.revision==自身.修订+1 and 变更.get('kind')=='append'#紧挨着的追加
        if not 追加:#不能增量
            自身.根列表.clear()#根账清空
            自身.尝试.clear()#尝试清空
            自身.分组=会话日志分组()#范围重新走
        if 追加:#沿用已有行
            下一=list(自身.行仓.getSnapshot())#拷贝一份再改
            条目列表=变更.get('entries') or []#只加新的
        else:#整窗
            下一=[]#从头
            条目列表=窗.entries#全部
        for 条目 in 条目列表:#按顺序加
            自身.加条目(条目,下一)#一根或一组增量
        自身.修订=窗.revision#记下
        if not 追加:#整窗替换后丢掉窗口外的记录
            自身.修剪(下一)#只留还在的行
        自身.行仓.set(下一)#一次发布顺序
        自身.接受中=False#结束

    def 修剪(自身,行列表):
        '窗口里不再有的行清掉记录，结算映射也只留还在的根'
        留下=set(行['key'] for 行 in 行列表)#还在的键
        for 序号,键 in list(自身.已结算根.items()):#结算映射
            if 键 not in 留下:#根已经不在
                del 自身.已结算根[序号]#丢掉
        for 键,仓 in list(自身.记录.items()):#记录仓
            if 键 not in 留下:#行没了
                仓.set(None)#先发布空
                del 自身.记录[键]#再移走
                停=自身.记录停.pop(id(仓),None)#扇出
                if 停 is not None:#订过
                    停()#拆

    def 加根(自身,键,条目,行列表,流=None):
        '在分组里放一根，并记下它在行列表里的位置'
        行=自身.分组.追加({'key':键,'depth':0},条目['event'])#补上回合或步骤祖先
        根={'row':行,'entry':条目,'stream':流,'ordinal':len(自身.根列表),'offset':len(行列表)}#根账
        自身.根列表.append(根)#记账
        行列表.append(行)#放进行列表
        return 根#给增量使用

    def 加条目(自身,条目,行列表):
        '活动尝试合成一行，耐久助手再展开子增量'
        if 条目.get('type')=='transient':#活动增量
            事件=条目['event']#事件
            数据=事件['data']#尝试数据
            父='attempt:'+str(数据['attemptId'])#尝试行键
            尝试=自身.尝试.get(父)#已有尝试
            if 尝试 is None:#第一次见到
                尝试=自身.加根(父,条目,行列表,助手日志流(父))#建根和流
                自身.尝试[父]=尝试#记住
            块数=自身.加块(尝试,行列表,事件['time'],数据['chunk'],str(数据['turn'])+'/'+str(数据['step']))#插入增量
            自身.放入(父,{#尝试行本身
                'type':'assistant/live',#活动类型
                'identity':数据['attemptId'],#尝试身份
                'location':str(数据['turn'])+'/'+str(数据['step']),#回合/步骤
                'time':事件['time'],#时间
                'value':{'attemptId':数据['attemptId'],'turn':数据['turn'],'step':数据['step'],'chunks':块数},#当前块数
            })#发布尝试行
            return#活动行结束
        事件=条目['event']#耐久事件
        键=自身.已结算根.get(事件['seq'])#结算后的尝试键
        if 键 is None:#普通事件
            键='event:'+str(事件['seq'])#事件键
        数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#数据
        if 'turn' in 数据:#有回合
            位置=str(数据['turn'])#回合
            if 'step' in 数据:#还有步骤
                位置=位置+'/'+str(数据['step'])#回合/步骤
        else:#没有位置
            位置=''#空
        自身.放入(键,{'type':事件.get('type'),'identity':str(事件.get('seq')),'time':事件.get('time'),'location':位置,'value':事件})#根记录是事件本身
        if 事件.get('type') in ('assistant/message','assistant/attempt'):#助手正文
            层次=助手日志流(键)#这棵流
            根=自身.加根(键,条目,行列表,层次)#根行
            流=数据.get('stream')#紧凑流
            增量=None if 流 is None else 自身.流缓存.get(id(流))#展开过没有
            if 增量 is None:#第一次
                增量=展开助手流(流 or [])#拆回带时块
                if 流 is not None:#有原流才缓存
                    自身.流缓存[id(流)]=增量#按身份
            for 一项 in 增量:#逐块
                自身.加块(根,行列表,一项['time'],一项['chunk'],位置)#插入
        else:#普通事件
            自身.加根(键,条目,行列表)#只有根

    def 加块(自身,根,行列表,时间,块,位置):
        '把一块插到助手根下面，并后移后面的根'
        流=根['stream']#助手流
        结果=流.追加(块)#层级决定插在哪
        行=dict(结果['row'])#拷贝
        行['depth']=行['depth']+根['row']['depth']#加上根的深度
        行列表.insert(根['offset']+1+结果['position'],行)#插到根后面
        if 'header' in 结果:#块头要换成合上
            头行=dict(结果['header']['row'])#新头
            头行['depth']=头行['depth']+根['row']['depth']#同样加深
            行列表[根['offset']+1+结果['header']['position']]=头行#替换原头
        序号=根['ordinal']+1#后面的根
        while 序号<len(自身.根列表):#每个后续根
            自身.根列表[序号]['offset']=自身.根列表[序号]['offset']+1#让出一个位置
            序号=序号+1#下一个
        自身.放入(结果['key'],{'type':块.get('type'),'identity':str(结果['index']),'time':时间,'location':位置,'value':块})#增量记录
        if 'collapsed' in 结果:#推理折叠摘要
            仓=自身.记录.get(结果['collapsed']['key'])#块头记录
            先前=None if 仓 is None else 仓.getSnapshot()#上一份
            if 仓 is not None and 先前 is not None and 先前.get('collapsedSummary')!=结果['collapsed']['summary']:#摘要变了
                下一=dict(先前)#拷贝
                下一['collapsedSummary']=结果['collapsed']['summary']#新摘要
                仓.set(下一)#发布
        return 流.长度#当前块数

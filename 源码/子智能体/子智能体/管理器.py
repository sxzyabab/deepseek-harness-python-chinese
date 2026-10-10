import os#路径
import uuid#子体会话 id
import weakref#根池不留住已死根
from ...基础设施.js特性 import PromiseEX as 期约#期约
from ...模型后端.llm import 内容含图片,推理力度标识#图片与推理力度
from ...模型后端.llm.异常 import 错误链#错误链
from ...内核.会话 import 会话标识#会话 id 品牌
from ...内核.智能体循环.中止与并发 import 中止控制器,已中止 as 信号已中止#融合中止
from ...内核.智能体循环.异常 import 中止错误#默认中止
from .激活操作 import (
    激活池,子体锁,激活智能体,要求本地激活,观察本地失败,捕获本地结果,弱集合,
)#激活记录
from .描述符播种 import 创建智能体消息,附可续跑返回指引,创建结算消息#模型可见消息
from .描述符 import 折叠子智能体描述符,快照子智能体描述符#描述符
from .目录 import 建立目录子体,建立外部目录子体#父目录
from .深度 import 断言子智能体最大深度#深度形态
from .子体 import (
    追加委托策略覆盖,应用子体组合,捕获委托策略覆盖,子会话元数据,
    解析子智能体选项,解析子深度,
)#子体
from .异常 import 子智能体错误#缝内失败
from .内部 import 是相邻智能体发消息工具#标准 send_message
from .结构化 import 挂上结构化运行时#结构化输出
from ...模型后端.llm.消息 import 创建用户消息#宿主来源的用户消息

__all__=['子智能体管理器']#仅中文公开名

def 失败消息(错误):
    '只取执行或拆除失败的外层文案'
    if isinstance(错误,BaseException):#异常
        return str(错误)#消息
    return 'unknown teardown failure'#未知

def 期约对():
    '带解决与拒绝的期约'
    盒={'期约':期约()}#结算点
    def 解决(值=None):
        '兑现'
        盒['期约'].解决(值)#兑现
    def 拒绝(错误=None):
        '拒绝'
        盒['期约'].拒绝(错误)#拒绝
    盒['解决']=解决#解决
    盒['拒绝']=拒绝#拒绝
    return 盒#对

def 确保期约(值):
    '同步返回值也接成期约'
    if hasattr(值,'然后'):#已是期约
        return 值#原样
    结果=期约()#包装
    结果.解决(值)#兑现
    return 结果#期约

def 会话序号(会话):
    '下一序号。Python 会话的 seq 是方法'
    序号=会话.seq#属性或方法
    return 序号() if callable(序号) else 序号#调用或读取

def 头取(头,键):
    '会话头字段'
    if isinstance(头,dict):#映射
        return 头[键] if 键 in 头 else None#键
    return getattr(头,键,None)#属性

def 若中止则抛出(信号):
    '已中止则抛出承载原因'
    if 信号 is None:#无信号
        return#未中止
    已置位=信号已中止(信号) if hasattr(信号,'is_set') else False#内核信号
    if not 已置位 and hasattr(信号,'_事件'):#工具信号
        已置位=bool(信号._事件.is_set())#置位
    if not 已置位:#仍活着
        return#返回
    原因=getattr(信号,'原因',None)#内核原因
    if 原因 is None:#工具原因
        原因=getattr(信号,'_异常',None)#异常
    if isinstance(原因,BaseException):#已是异常
        raise 原因#抛出
    raise 中止错误()#默认

def 是中止错误(错误):
    '取消是否中止了物化'
    名=getattr(错误,'name',None) or type(错误).__name__#错误名
    return 名 in ('AbortError','中止错误') or isinstance(错误,中止错误)#中止

def 融合调用方中止(调用方,控制器):
    '调用方信号中止时转发给物化控制器。返回摘掉监听的函数'
    def 转发():
        '等到调用方中止再转发原因'
        if hasattr(调用方,'等待'):#内核信号
            调用方.等待()#阻塞
        elif hasattr(调用方,'_事件'):#工具信号
            调用方._事件.wait()#阻塞
        elif hasattr(调用方,'wait'):#Event
            调用方.wait()#阻塞
        原因=getattr(调用方,'原因',None)#原因
        if 原因 is None:#工具
            原因=getattr(调用方,'_异常',None)#异常
        控制器.中止(原因)#转发
    if 调用方 is None:#无
        return lambda: None#空
    if hasattr(调用方,'is_set') and 调用方.is_set() or (hasattr(调用方,'_事件') and 调用方._事件.is_set()):#已经中止
        原因=getattr(调用方,'原因',None) or getattr(调用方,'_异常',None)#原因
        控制器.中止(原因)#立刻
        return lambda: None#不用再听
    from ...基础设施.通用工具 import 启动守护线程#听信号
    启动守护线程(转发)#后台
    return lambda: None#线程不可摘；控制器中止后线程自行结束

class 子智能体管理器:
    '拥有子体启动、消息准入、冷恢复与执行寿命'
    def __init__(自身,上下文,宿主,最大活跃子体):
        '在服务的智能体注入上下文里建造管理器'
        自身._上下文=上下文#智能体可用的上下文
        自身._宿主=宿主#提供方派发与观察
        自身._最大活跃子体=最大活跃子体#容量读取
        自身._驻留={}#子会话 id → 活激活
        自身._根池=weakref.WeakKeyDictionary()#根 → 池
        自身._物化=[]#已准入、尚未发布或回滚的物化
        自身._锁=子体锁()#每子串行
        自身._关闭中的范围={}#根 id → {根, 成员集, 根对象}
        自身._排空中=False#管理器是否在排空
        def 激活所有者(子上下文):
            '私有作用域，智能体句柄挂在这里'
            自身._所有者上下文=子上下文#创建与恢复用
        纤程=上下文.启动插件(激活所有者)#私有插件
        自身._所有者纤程=纤程#拆除时先排空再卸作用域
        def 智能体已拆除(载荷):
            '精确根离开注册表后关闭其准入截止'
            智能体=载荷['agent'] if isinstance(载荷,dict) and 'agent' in 载荷 else None#智能体
            if 智能体 is None:#没有
                return#忽略
            自身._关闭中的范围.pop(id(智能体),None)#摘掉
        上下文.监听('agent/disposed',智能体已拆除)#根离开
        def 寿命():
            '反向拆除：先排空，再卸私有作用域'
            def 卸作用域():
                '卸私有插件'
                if 纤程.拆除 is not None:#有拆除器
                    纤程.拆除()#卸
            def 排空管理器():
                '排空已准入的子体'
                自身.排空()#启动排空
            yield 卸作用域#先登记，后执行
            yield 排空管理器#后登记，先执行
        上下文.副作用(寿命,'subagents.manager()')#命名副作用

    def 打断(自身,目标会话标识,权威):
        '在人类父地址或精确活祖先下打断活子体的当前执行'
        if 权威['kind']=='ancestor':#祖先
            调用方=权威['agent']#调用方
            if 自身._上下文.agents.获取(调用方.id) is not 调用方:#不是精确活祖先
                raise 子智能体错误('interrupting "'+str(目标会话标识)+'" requires the exact live ancestor agent','UNAUTHORIZED')#拒绝
            if 调用方.id==目标会话标识:#自己
                raise 子智能体错误('agent "'+str(调用方.id)+'" cannot interrupt itself','UNAUTHORIZED')#拒绝
        激活=自身._驻留.get(目标会话标识)#活激活
        if 激活 is None:#没有
            return#空操作
        if 权威['kind']=='user':#人类父
            if 激活['parent'].id!=权威['parentSessionId']:#不是这个父
                raise 子智能体错误('subagent "'+str(目标会话标识)+'" belongs to another parent session','UNAUTHORIZED')#拒绝
        elif 权威['agent'] not in 激活['ancestry']:#不是活后代
            raise 子智能体错误(
                'subagent "'+str(目标会话标识)+'" is not a live descendant of agent "'+str(权威['agent'].id)+'"',
                'UNAUTHORIZED',
            )#拒绝
        if 激活['closing'] is not None:#已在拆除
            return#不再发第二次取消
        种类='user' if 权威['kind']=='user' else 'parent'#取消种类
        if 激活['kind']=='local':#本地
            激活['handle'].智能体.取消({'kind':种类},{'keepInbox':True})#保留收件箱
        else:#外部
            激活['controller'].中止({'kind':种类})#停掉单次执行
            自身.拆除(激活).捕获(lambda _错误: None)#拆除失败由结算观察报告

    def 排空(自身):
        '关闭准入，等已准入物化发布或回滚，再按子优先拆除活激活'
        结果=期约()#排空结果
        自身._排空中=True#不再准入
        for 待定 in list(自身._物化):#已准入物化
            待定['controller'].中止()#取消
        def 物化已落定(_值=None):
            '物化都落定后拆根'
            被拥有=set()#有主的子
            for 激活 in 自身._驻留.values():#每个激活
                被拥有.update(激活['ownedChildren'])#记下子
            根列表=[激活 for 激活 in 自身._驻留.values() if 激活['childId'] not in 被拥有]#没有被别的激活拥有
            自身._拆除根(根列表,'activation(s)').然后(结果.解决,结果.拒绝)#拆除
        if len(自身._物化)==0:#没有在途
            物化已落定()#直接拆
        else:#等待
            期约.全部([项['settled']['期约'] for 项 in list(自身._物化)]).然后(物化已落定,结果.拒绝)#全部落定
        return 结果#期约

    def 等待子体(自身,父):
        '加入进行中的子体工作，空闲且收件箱只是停着的不挡住宿主完成'
        结果=期约()#是否观察过工作
        观察到=[False]#是否加入过
        def 一轮():
            '看一遍当前后代'
            待定=[项 for 项 in 自身._物化 if 父 in 项['lineage']]#谱系含父的物化
            孩子们=[项 for 项 in 自身._驻留.values() if 激活智能体(项) is not 父 and 父 in 项['ancestry']]#后代激活
            if any(项['kind']=='local' and 项['handle'].智能体.状态!='idle' for 项 in 孩子们):#有非空闲本地子
                观察到[0]=True#观察过
            等待=[]#要等的期约
            for 项 in 孩子们:#先等本地空闲
                if 项['kind']=='local':#本地
                    等待.append(项['handle'].智能体.等到空闲())#空闲
            def 空闲之后(_值=None):
                '空闲后再决定等什么'
                再等=[]#第二轮
                for 项 in 孩子们:#逐个
                    if 项['kind']=='external' or 项['closing'] is not None:#外部或在关
                        再等.append(项['result']['期约'].捕获(lambda _错误: None))#等结果
                        continue#下一个
                    if 项['handle'].智能体.状态!='idle':#又忙了
                        再等.append(项['handle'].智能体.等到空闲())#再等空闲
                        continue#下一个
                    if len(项['ownedChildren'])>0:#还有子
                        if any(标识 not in 自身._驻留 for 标识 in 项['ownedChildren']):#子还在准备
                            再等.append(项['poke']['期约'])#等唤醒
                        continue#下一个
                    收件箱=项['handle'].智能体.inbox#收件箱
                    if 项['failureAt'] is None and (len(收件箱.下一轮队列)>0 or len(收件箱.下一步队列)>0):#停着的后续
                        continue#不挡完成
                    再等.append(期约.竞速([项['result']['期约'].捕获(lambda _错误: None),项['poke']['期约']]))#结果或唤醒
                for 项 in 待定:#物化
                    再等.append(项['settled']['期约'])#等发布或回滚
                def 等完(_值=None):
                    '有等待就再看一遍'
                    新物化=any(父 in 项['lineage'] and 项 not in 待定 for 项 in 自身._物化)#新物化
                    新孩子=any(
                        激活智能体(项) is not 父 and 父 in 项['ancestry'] and 项 not in 孩子们
                        for 项 in 自身._驻留.values()
                    )#新孩子
                    if 新物化 or 新孩子:#期间又出现了
                        一轮()#再看
                        return#返回
                    结果.解决(观察到[0])#没有更多等待
                if len(再等)>0:#还有
                    观察到[0]=True#观察过
                    期约.全部(再等).然后(等完,结果.拒绝)#等完再看
                else:#没有等待
                    等完()#检查新出现的
            if len(等待)>0:#先等空闲
                期约.全部(等待).然后(空闲之后,结果.拒绝)#空闲后
            else:#已经空闲
                空闲之后()#继续
        try:#同步段
            一轮()#开始
        except BaseException as 错误:#同步失败
            结果.拒绝(错误)#拒绝
        return 结果#期约

    def 排空后代(自身,父列表):
        '停掉精确活宿主父之下的受管子孙'
        结果=期约()#排空结果
        根集=[父 for 父 in 父列表 if 自身._上下文.agents.获取(父.id) is 父]#仍是精确活父
        if len(根集)==0:#没有活根
            结果.解决()#空操作
            return 结果#已兑现
        for 根 in 根集:#每个根
            自身._关闭成员(根).add(根)#自己也在截止里
        目标=[]#要拆的激活
        for 激活 in list(自身._驻留.values()):#每个激活
            孩子=激活智能体(激活)#本地孩子
            谱系=自身._活谱系(孩子 if 孩子 is not None else 激活['parent'])#向上的活谱系
            主人=[根 for 根 in 根集 if 孩子 is not 根 and 根 in 激活['ancestry']]#拥有它的根
            if len(主人)==0:#不在这些树里
                continue#跳过
            目标.append(激活)#要拆
            for 主人项 in 主人:#每个根
                成员=自身._关闭成员(主人项)#成员集
                if 孩子 is not None:#本地孩子
                    成员.add(孩子)#记下
                for 智能体 in 谱系:#谱系
                    成员.add(智能体)#记下
        物化=[]#相关物化
        for 项 in list(自身._物化):#每个物化
            主人=[根 for 根 in 根集 if 根 in 项['lineage']]#相关根
            for 主人项 in 主人:#每个根
                成员=自身._关闭成员(主人项)#成员集
                for 智能体 in 项['lineage']:#谱系
                    成员.add(智能体)#记下
            if len(主人)>0:#属于这些树
                项['controller'].中止()#取消
                物化.append(项)#要等
        被拥有=set()#目标内部的子
        for 激活 in 目标:#每个目标
            被拥有.update(激活['ownedChildren'])#记下
        目标根=[激活 for 激活 in 目标 if 激活['childId'] not in 被拥有]#先拆这些
        for 激活 in 目标:#同步开始拆除
            自身.拆除(激活).捕获(lambda _错误: None)#失败稍后汇总
        def 物化完(_值=None):
            '物化落定后拆根'
            自身._拆除根(目标根,'scoped activation(s)').然后(结果.解决,结果.拒绝)#拆根
        if len(物化)==0:#没有
            物化完()#直接
        else:#等待
            期约.全部([项['settled']['期约'] for 项 in 物化]).然后(物化完,结果.拒绝)#等待
        return 结果#期约

    def 排空子体(自身,父,子标识列表):
        '释放一个精确活父选中的驻留直接子'
        结果=期约()#结果
        if 自身._上下文.agents.获取(父.id) is not 父:#不是精确活父
            结果.拒绝(子智能体错误('selected child teardown requires the exact live parent agent','UNAUTHORIZED'))#拒绝
            return 结果#期约
        目标=[]#选中的
        try:#逐个授权
            for 子标识 in dict.fromkeys(子标识列表):#去重保序
                激活=自身._驻留.get(子标识)#驻留
                if 激活 is None:#不在
                    continue#空操作
                if 激活['parent'].id!=父.id or 父 not in 激活['ancestry']:#不是直接子
                    raise 子智能体错误(
                        'subagent "'+str(子标识)+'" is not a direct child of agent "'+str(父.id)+'"',
                        'UNAUTHORIZED',
                    )#拒绝
                目标.append(激活)#收下
        except BaseException as 错误:#授权失败
            结果.拒绝(错误)#拒绝
            return 结果#期约
        for 激活 in 目标:#开始拆
            自身.拆除(激活).捕获(lambda _错误: None)#失败由拆根汇总
        自身._拆除根(目标,'selected activation(s)').然后(结果.解决,结果.拒绝)#等待
        return 结果#期约

    def 启动本地(自身,规格):
        '启动可续跑后台子体，初始收件箱接受时兑现'
        结果=期约()#激活加消息 id
        释放持有=[lambda: None]#失败路径释放
        try:#同步前置
            请求=规格['request']#请求
            父=请求['parent']#父
            自身._断言准入(父)#还在准入
            if 规格['delivery']=='caller':#调用方投递
                持久化=自身._上下文.获取服务('sessionPersistence')#可选
            else:#父投递
                持久化=自身._要求持久化()#必须有
            断言子智能体最大深度(请求['maxDepth'] if 'maxDepth' in 请求 else None)#深度形态
            子标识=规格['childId'] if 'childId' in 规格 and 规格['childId'] is not None else 会话标识(str(uuid.uuid4()))#预留或新 id
            自身._断言子标识可用(子标识)#未被占用
            子深度=解析子深度(父,请求['maxDepth'] if 'maxDepth' in 请求 else None)#子深度
            智能体选项=解析子智能体选项(父,请求['agentOptions'] if 'agentOptions' in 请求 else None,子深度)#路由
            描述符输入={'mode':'continuable','provider':规格['provider'],'label':规格['label']}#描述符
            if 'provider' in 智能体选项:#有提供方
                描述符输入['agentProvider']=智能体选项['provider']#记下
            if 'model' in 智能体选项:#有模型
                描述符输入['agentModel']=智能体选项['model']#记下
            if 'reasoningEffort' in 智能体选项 and 智能体选项['reasoningEffort'] is not None:#有力度
                描述符输入['agentReasoningEffort']=智能体选项['reasoningEffort']#记下
            if 'persona' in 请求 and 请求['persona'] is not None:#人设
                描述符输入['persona']=请求['persona']#记下
            if 'toolFilter' in 请求 and 请求['toolFilter'] is not None:#过滤
                描述符输入['toolFilter']=请求['toolFilter']#记下
            描述符=快照子智能体描述符(描述符输入)#分离
            委托策略=捕获委托策略覆盖(父)#委托当时的策略
            释放持有[0]=自身._持有所有权(父,子标识)#父不能先结算
        except BaseException as 错误:#前置失败
            结果.拒绝(错误)#拒绝
            return 结果#期约
        def 失败(错误):
            '释放持有并拒绝'
            try:#释放
                释放持有[0]()#只释放本次加上的
            finally:#再拒绝
                结果.拒绝(错误)#原错
        def 目录好了(工作目录):
            '目录就绪后请提供方准备'
            def 准备好了(已准备):
                '准备好后在子锁里物化并提交'
                try:#取消与准入
                    若中止则抛出(规格['signal'])#调用方取消
                    自身._断言准入(父)#仍准入
                except BaseException as 错误:#失败
                    失败(错误)#拒绝
                    return#返回
                种子=已准备['seed'] if isinstance(已准备,dict) and 'seed' in 已准备 else None#种子
                def 临界():
                    '锁内创建并接受初始提示'
                    return 自身._锁内启动本地(规格,子标识,父,工作目录,种子,智能体选项,描述符,委托策略,持久化)#期约
                自身._锁.运行(子标识,临界).然后(结果.解决,失败)#消息 id 与回执
            确保期约(自身._宿主['准备可续跑'](规格['provider'],{
                'sessionId':子标识,#预留 id
                'cwd':工作目录,#目录
                'parent':父,#父
                'signal':规格['signal'],#信号
            })).然后(准备好了,失败)#准备
        自身._解析目录(请求,规格['signal']).然后(目录好了,失败)#目录
        return 结果#期约

    def _锁内启动本地(自身,规格,子标识,父,工作目录,种子,智能体选项,描述符,委托策略,持久化):
        '子锁内的本地启动。返回期约，兑现值含 childId 与 messageId'
        结果=期约()#结果
        请求=规格['request']#请求
        try:#锁内同步检查
            若中止则抛出(规格['signal'])#取消
            自身._断言准入(父)#准入
            自身._断言子标识可用(子标识)#可用
        except BaseException as 错误:#失败
            结果.拒绝(错误)#拒绝
            return 结果#期约
        def 统计之后(已存):
            '预留 id 尚未持久化才创建'
            try:#再查
                若中止则抛出(规格['signal'])#取消
                自身._断言准入(父)#准入
                自身._断言子标识可用(子标识)#可用
                if 已存 is not None:#已经存在
                    raise 子智能体错误('subagent "'+str(子标识)+'" already exists','DUPLICATE_CHILD')#拒绝
            except BaseException as 错误:#失败
                结果.拒绝(错误)#拒绝
                return#返回
            继承=0 if 种子 is None else len(种子)#前缀长度
            def 已物化(激活):
                '物化后提交初始提示并写目录'
                孩子=要求本地激活(激活)['handle'].智能体#本地孩子
                工具表=自身._上下文.获取服务('tools')#工具
                定义=None if 工具表 is None else 工具表.获取('send_message',孩子)#可见定义
                if 规格['delivery']!='caller' and 是相邻智能体发消息工具(定义):#标准发消息工具
                    提示=附可续跑返回指引(父.id,请求['prompt'])#加返回指引
                else:#不加
                    提示=请求['prompt']#原提示
                def 提交目录():
                    '父目录记下这个可续跑子'
                    建立目录子体(父.session,孩子.session.header,描述符)#目录
                自身._提交已物化(激活,提示,{'source':{'kind':'user'},'signal':规格['signal'],'delivery':'queue'},父,提交目录).然后(
                    lambda 消息标识: 结果.解决({**自身._回执(激活),'childId':子标识,'messageId':消息标识}),
                    结果.拒绝,
                )#提交
            自身._物化({
                'kind':'local',#本地
                'childId':子标识,#子 id
                'provider':规格['provider'],#提供方
                'parent':父,#父
                'create':{#全新创建
                    'cwd':工作目录,#目录
                    'seed':种子,#种子
                    'meta':子会话元数据(父,解析子深度(父,请求['maxDepth'] if 'maxDepth' in 请求 else None),种子 is not None),#元数据
                    'inheritedEventCount':继承,#继承条数
                    'delegatedPolicies':委托策略,#策略
                    'descriptor':描述符,#描述符
                },#创建结束
                'agentOptions':智能体选项,#选项
                'composition':{'persona':请求['persona'] if 'persona' in 请求 else None,'toolFilter':请求['toolFilter'] if 'toolFilter' in 请求 else None},#组合
                'signal':规格['signal'],#信号
                'delivery':规格['delivery'],#投递
                'outputSchema':请求['outputSchema'] if 'outputSchema' in 请求 else None,#输出模式
            }).然后(已物化,结果.拒绝)#物化
        if 'childId' in 规格 and 规格['childId'] is not None and 持久化 is not None:#预留 id 要查持久化
            try:#统计
                if hasattr(持久化,'stat'):#上游方法名
                    已存=持久化.stat(子标识,{'signal':规格['signal']})#统计
                else:#本树的观察
                    已存=持久化.观察(子标识,{'signal':规格['signal']})#是否已有
            except BaseException as 错误:#统计失败
                结果.拒绝(错误)#拒绝
                return 结果#期约
            确保期约(已存).然后(统计之后,结果.拒绝)#继续
        else:#不用查
            统计之后(None)#继续
        return 结果#期约

    def 启动外部(自身,规格):
        '在激活所有权下启动外部后端'
        结果=期约()#回执
        父=规格['request']['parent']#父
        try:#准入
            自身._断言准入(父)#准入
        except BaseException as 错误:#失败
            结果.拒绝(错误)#拒绝
            return 结果#期约
        待定标识=会话标识(str(uuid.uuid4()))#占位，真正 id 由跑给出
        try:#持有
            释放=自身._持有所有权(父,待定标识)#持有
        except BaseException as 错误:#失败
            结果.拒绝(错误)#拒绝
            return 结果#期约
        已建立=[None]#成功物化的激活
        def 收尾失败(错误):
            '回滚后拒绝，最后释放持有'
            def 结束(_值=None):
                '释放并拒绝'
                释放()#释放
                结果.拒绝(错误)#原错
            if 已建立[0] is None:#还没物化
                结束()#直接
                return#返回
            def 回滚失败(清理错误):
                '回滚失败只记警告'
                自身._上下文.日志.警告('subagent "'+str(已建立[0]['childId'])+'" admission rollback failed: '+失败消息(清理错误))#警告
                结束()#仍拒绝原错
            自身.拆除(已建立[0]).然后(结束,回滚失败)#先拆
        def 目录好了(工作目录):
            '目录就绪后物化外部跑'
            def 启动跑(信号):
                '把已解析目录交给提供方'
                请求=dict(规格['request'])#拷贝
                请求['cwd']=工作目录#绝对目录
                请求['label']=规格['label']#标签
                请求['signal']=信号#物化信号
                return 自身._宿主['启动外部'](规格['provider'],请求)#跑
            def 已物化(激活):
                '父目录记下外部执行并宣布'
                try:#准入与活父
                    自身._断言准入(父)#准入
                    自身._断言活父(父,激活['childId'])#活父
                    若中止则抛出(规格['signal'])#取消
                    if 规格['delivery']=='parent':#父投递才进目录
                        建立外部目录子体(父.session,激活['childId'],规格['label'])#外部目录
                    自身._宣布(激活)#开始观察
                except BaseException as 错误:#失败
                    已建立[0]=激活#回滚它
                    收尾失败(错误)#回滚
                    return#返回
                释放()#成功后持有留给活激活
                结果.解决(自身._回执(激活))#回执
            自身._物化({
                'kind':'external',#外部
                'childId':待定标识,#占位，物化时换成跑 id
                'provider':规格['provider'],#提供方
                'parent':父,#父
                'signal':规格['signal'],#信号
                'delivery':规格['delivery'],#投递
                'start':启动跑,#启动
            }).然后(已物化,收尾失败)#物化
        自身._解析目录(规格['request'],规格['signal']).然后(目录好了,收尾失败)#目录
        return 结果#期约

    def _解析目录(自身,请求,信号):
        '在父仍拥有启动时捕获显式或继承的目录'
        结果=期约()#绝对目录
        显式=请求['cwd'] if 'cwd' in 请求 else None#显式
        if 显式 is not None and os.path.isabs(显式):#已经绝对
            try:#取消
                若中止则抛出(信号)#取消
            except BaseException as 错误:#失败
                结果.拒绝(错误)#拒绝
                return 结果#期约
            结果.解决(显式)#原样
            return 结果#期约
        def 父目录好了(父目录):
            '相对路径按父目录解析'
            try:#取消
                若中止则抛出(信号)#取消
                相对='.' if 显式 is None else 显式#省略即当前
                结果.解决(os.path.abspath(os.path.join(父目录,相对)))#绝对
            except BaseException as 错误:#失败
                结果.拒绝(错误)#拒绝
        try:#确保父目录
            确保期约(自身._上下文.workingDirectory.ensure(请求['parent'],信号)).然后(父目录好了,结果.拒绝)#确保
        except BaseException as 错误:#同步失败
            结果.拒绝(错误)#拒绝
        return 结果#期约

    def 发送消息(自身,发送方,目标标识,内容,选项):
        '把模型撰写的消息投到直接父或直接可续跑子'
        结果=期约()#消息 id
        try:#授权
            if 自身._上下文.agents.获取(发送方.id) is not 发送方:#不是精确活发送方
                raise 子智能体错误('message delivery requires the exact live sender agent','UNAUTHORIZED')#拒绝
            自身._断言准入(发送方)#准入
            发送方激活=自身._驻留.get(发送方.id)#自己的激活
            if 发送方激活 is not None and 发送方激活['kind']=='local' and 发送方激活['handle'].智能体 is 发送方 and 发送方激活['parent'].id==目标标识:#发给直接父
                若中止则抛出(选项['signal'])#取消
                结果.解决(自身._发给父(发送方激活,发送方,内容))#同步投递
                return 结果#期约
            if 头取(发送方.session.header,'parentSession')==目标标识:#头说是父但自己不是驻留可续跑子
                raise 子智能体错误(
                    'agent "'+str(发送方.id)+'" is not a resident continuable child and cannot send to parent "'+str(目标标识)+'"',
                    'UNAUTHORIZED',
                )#拒绝
        except BaseException as 错误:#失败
            结果.拒绝(错误)#拒绝
            return 结果#期约
        return 自身._投递到子(发送方,目标标识,内容,{'signal':选项['signal'],'delivery':'steer'})#转向子

    def 排队提示(自身,父,子标识,内容,来源,信号):
        '把人类提示排成直接子的独立回合'
        return 自身._投递到子(父,子标识,内容,{'source':来源,'signal':信号,'delivery':'queue'})#排队

    def 转向提示(自身,父,子标识,内容,来源,信号):
        '把宿主提示转到直接可续跑子的最近一步'
        return 自身._投递到子(父,子标识,内容,{'source':来源,'signal':信号,'delivery':'steer'})#转向

    def _投递(自身,激活,消息,投递):
        '在拆除开始前同步接受本地输入'
        if 激活['closing'] is not None:#正在关
            raise 子智能体错误('subagent activation is being disposed; the message was not accepted','ACTIVATION_CLOSING')#拒绝
        本地=要求本地激活(激活)#必须本地
        结构化=本地['structured']#附件
        if 结构化 is not None and 结构化['acceptsInput']() is False:#输入已关
            raise 子智能体错误('subagent is submitting or has submitted its structured result; the message was not accepted','INPUT_CLOSED')#拒绝
        if 投递=='steer':#转向
            本地['handle'].智能体.转向(消息)#最近一步
        else:#排队
            本地['handle'].智能体.后续(消息)#下一轮

    def _断言子标识可用(自身,子标识):
        '拒绝已被活智能体或会话占用的子身份'
        会话表=自身._上下文.获取服务('sessions')#会话
        会话占用=会话表 is not None and 会话表.获取(子标识) is not None#活会话
        if 子标识 in 自身._驻留 or 自身._上下文.agents.获取(子标识) is not None or 会话占用:#已占用
            raise 子智能体错误('subagent "'+str(子标识)+'" already exists','DUPLICATE_CHILD')#拒绝

    def _持有所有权(自身,父,子标识):
        '在可续跑父的拥有集里预登记，避免父在子还在建立时结算'
        父激活=自身._驻留.get(父.id)#父激活
        if 父激活 is None or 激活智能体(父激活) is not 父:#父不是受管驻留
            return lambda: None#不用持有
        if 父激活['closing'] is not None:#父在拆
            raise 子智能体错误(
                'subagent parent "'+str(父.id)+'" is being disposed; the child was not established',
                'ACTIVATION_CLOSING',
            )#拒绝
        if 子标识 in 父激活['ownedChildren']:#已经有
            return lambda: None#不重复加
        父激活['ownedChildren'].add(子标识)#预登记
        def 释放():
            '失败路径只拿掉本次加上、且还没有活激活的持有'
            活=自身._驻留.get(子标识)#活激活
            if 活 is not None and 活['closing'] is None:#已经属于活激活
                return#留给完成拆除
            if 子标识 in 父激活['ownedChildren']:#仍是本次持有
                父激活['ownedChildren'].discard(子标识)#拿掉
                自身._唤醒(父激活)#父可以再看结算
        return 释放#释放器

    def _醒着发送(自身,父,消息,投递):
        '驻留父走激活投递，否则直接投到智能体'
        父激活=自身._驻留.get(父.id)#父激活
        if 父激活 is not None and 激活智能体(父激活) is 父:#受管父
            try:#投递
                自身._投递(父激活,消息,投递)#接受
            finally:#唤醒
                自身._唤醒(父激活)#再看结算
            return#结束
        if 投递=='steer':#转向
            父.转向(消息)#转向
        else:#排队
            父.后续(消息)#后续

    def _断言准入(自身,智能体):
        '管理器或这条精确父树开始排空后拒绝新准入'
        关闭=自身._关闭拆除于(智能体)#哪一次拆除
        if 关闭 is None:#还开着
            return#允许
        if 关闭=='manager':#整个管理器
            文案='subagents are draining; the operation was not admitted'#管理器
        else:#某棵父树
            文案='subagents below parent "'+str(关闭.id)+'" are draining; the operation was not admitted'#父树
        raise 子智能体错误(文案,'DRAINING')#拒绝

    def _授权谱系(自身,父,子标识,父会话):
        '按耐久直接父谱系授权'
        自身._断言活父(父,子标识)#活父
        if 父会话!=父.id:#不是这个父
            raise 子智能体错误('subagent "'+str(子标识)+'" belongs to another parent session','UNAUTHORIZED')#拒绝

    def _断言活父(自身,父,子标识):
        '注册表条目变了就拒绝父权威'
        if 自身._上下文.agents.获取(父.id) is not 父:#不是精确活父
            raise 子智能体错误('subagent "'+str(子标识)+'" delivery requires the exact live parent agent','UNAUTHORIZED')#拒绝

    def _物化(自身,输入):
        '创建或恢复一个子智能体并发布其激活'
        结果=期约()#激活
        try:#准入
            自身._断言准入(输入['parent'])#准入
            若中止则抛出(输入['signal'])#取消
        except BaseException as 错误:#失败
            结果.拒绝(错误)#拒绝
            return 结果#期约
        谱系=自身._活谱系(输入['parent'])#当时的活谱系
        父激活=自身._驻留.get(输入['parent'].id)#父激活
        池=父激活['pool'] if 父激活 is not None else 自身._根池于(输入['parent'])#容量池
        try:#预留
            释放槽=池.预留(自身._最大活跃子体())#槽
        except BaseException as 错误:#满了
            结果.拒绝(错误)#拒绝
            return 结果#期约
        落定=期约对()#物化落定
        控制器=中止控制器()#排空可取消
        物化={'lineage':谱系,'settled':落定,'controller':控制器}#记录
        自身._物化.append(物化)#记下
        融合=中止控制器()#调用方或排空
        融合调用方中止(输入['signal'],融合)#调用方
        def 控制器中止时转发():
            '排空控制器中止后转发'
            控制器.信号.等待()#阻塞
            融合.中止(控制器.信号.原因)#转发
        if 控制器.信号.is_set():#已经
            融合.中止(控制器.信号.原因)#立刻
        else:#去听
            from ...基础设施.通用工具 import 启动守护线程#听
            启动守护线程(控制器中止时转发)#后台
        输入=dict(输入)#拷贝
        输入['signal']=融合.信号#两路中止
        def 失败(错误):
            '回滚槽位；中止后再报准入'
            释放槽()#归还
            try:#中止可能是排空
                if 是中止错误(错误):#中止
                    自身._断言准入(输入['parent'])#排空则换成 DRAINING
            except BaseException as 准入错误:#准入失败优先
                错误=准入错误#换成它
            if 物化 in 自身._物化:#还在表里
                自身._物化.remove(物化)#摘掉
            落定['解决']()#物化结束
            结果.拒绝(错误)#拒绝
        def 成功(激活):
            '发布完成'
            if 物化 in 自身._物化:#还在表里
                自身._物化.remove(物化)#摘掉
            落定['解决']()#物化结束
            结果.解决(激活)#激活
        自身._跟踪物化(输入,谱系,池,释放槽).然后(成功,失败)#跟踪
        return 结果#期约

    def 拆除(自身,激活):
        '经记忆化的关闭事务停止并释放一个激活'
        return 自身._关闭(激活,lambda: 自身._完成拆除(激活,True))#停止

    def _关闭(自身,激活,释放):
        '同步关闭准入，并共享同一次释放'
        if 激活['closing'] is not None:#已有事务
            return 激活['closing']#同一份
        完成=期约对()#事务
        激活['closing']=完成['期约']#发布
        确保期约(释放()).然后(完成['解决'],完成['拒绝'])#释放
        return 完成['期约']#事务

    def _拆除根(自身,根列表,失败主语):
        '拆除互不依赖的根，全部落定后再报告失败'
        结果=期约()#结果
        if len(根列表)==0:#没有
            结果.解决()#空
            return 结果#期约
        失败们=[]#收集
        剩余=[len(根列表)]#还没落定的
        def 一棵(激活):
            '拆一棵并收集失败'
            def 成功(_值=None):
                '这一棵好了'
                收口()#收口
            def 失败(错误):
                '记下失败'
                失败们.append(错误)#收集
                收口()#收口
            def 收口():
                '全部落定后汇总'
                剩余[0]-=1#减一
                if 剩余[0]>0:#还没完
                    return#等
                if len(失败们)==0:#都成功
                    结果.解决()#兑现
                    return#结束
                结果.拒绝(子智能体错误(
                    'subagent teardown failed for '+str(len(失败们))+' '+失败主语+': '
                    +'; '.join(失败消息(项) for 项 in 失败们),
                    'ACTIVATION_TEARDOWN_FAILED',
                ))#汇总
            自身.拆除(激活).然后(成功,失败)#拆
        for 激活 in 根列表:#逐棵
            一棵(激活)#开始
        return 结果#期约

    def _关闭成员(自身,根):
        '一个精确排空根保留的成员集'
        现有=自身._关闭中的范围.get(id(根))#已有
        if 现有 is not None:#有
            return 现有['成员']#集合
        成员=set()#新集合
        自身._关闭中的范围[id(根)]={'根':根,'成员':成员}#记下
        return 成员#集合

    def _活谱系(自身,智能体):
        '从智能体向上的当前可解析谱系'
        谱系=[智能体]#自己
        见过=set([智能体.id])#防环
        父会话=头取(智能体.session.header,'parentSession')#父会话
        while 父会话 is not None:#还有父
            父=自身._上下文.agents.获取(父会话)#活父
            if 父 is None or 父.id in 见过:#没有或成环
                break#停
            谱系.append(父)#加上
            见过.add(父.id)#见过
            父会话=头取(父.session.header,'parentSession')#再向上
        return 谱系#谱系

    def _关闭拆除于(自身,智能体):
        '关闭这条谱系可续跑准入的那次拆除'
        if 自身._排空中:#管理器
            return 'manager'#管理器
        谱系=自身._活谱系(智能体)#谱系
        for 记录 in 自身._关闭中的范围.values():#每个根
            if 智能体 in 记录['成员'] or 记录['根'] in 谱系:#成员或根在谱系里
                return 记录['根']#这个根
        return None#还开着

    def _根池于(自身,父):
        '根的池只解析一次'
        池=自身._根池.get(父)#已有
        if 池 is None:#没有
            池=激活池()#新建
            自身._根池[父]=池#记下
        return 池#池

    def _跟踪物化(自身,输入,父谱系,池,释放槽):
        '把一次物化做到发布或回滚'
        结果=期约()#激活
        子标识=输入['childId']#可能被外部跑替换
        try:#入口取消
            若中止则抛出(输入['signal'])#取消
        except BaseException as 错误:#失败
            结果.拒绝(错误)#拒绝
            return 结果#期约
        if 输入['kind']=='external':#外部
            自身._物化外部(输入,父谱系,池,释放槽,结果)#外部
        else:#本地
            自身._物化本地(输入,父谱系,池,释放槽,结果)#本地
        return 结果#期约

    def _物化外部(自身,输入,父谱系,池,释放槽,结果):
        '启动外部跑并发布激活'
        控制器=中止控制器()#跑自己的取消
        融合调用方中止(输入['signal'],控制器)#调用方取消则停跑
        def 跑好了(跑):
            '跑发布后换成它的 id'
            跑.result.捕获(lambda _错误: None)#结果拒绝不变成未处理
            子标识=跑.id#提供方铸造的 id
            try:#id 必须可用
                自身._断言子标识可用(子标识)#可用
            except BaseException as 错误:#占用
                def 已拆(_值=None):
                    '拆完再拒绝'
                    结果.拒绝(错误)#原错
                确保期约(跑.销毁() if hasattr(跑,'销毁') else 跑.dispose()).然后(已拆,已拆)#先拆
                return#返回
            资源={'kind':'external','run':跑,'controller':控制器}#资源
            自身._发布激活(输入,子标识,资源,父谱系,池,释放槽,结果)#发布
        确保期约(输入['start'](控制器.信号)).然后(跑好了,结果.拒绝)#启动

    def _物化本地(自身,输入,父谱系,池,释放槽,结果):
        '创建或恢复本地智能体并发布激活'
        创建=输入['create'] if 'create' in 输入 else None#没有则是冷恢复
        结构化盒=[None]#设置里挂上的附件
        子标识=输入['childId']#子 id
        def 设置(子上下文,孩子):
            '未发布窗口：全新创建才追加描述符与委托策略'
            if 创建 is not None:#全新
                孩子.session.追加('subagent/descriptor',创建['descriptor'])#描述符
                追加委托策略覆盖(孩子.session,创建['delegatedPolicies'])#策略
                工作目录=子上下文.获取服务('workingDirectory')#工作目录
                if 工作目录 is None:#没有
                    raise Exception('local subagents require the working-directory service')#必须有
                工作目录.set(孩子,创建['cwd'],输入['signal'])#提交目录
            组合=输入['composition']#组合
            应用子体组合(子上下文,输入['parent'],{键:值 for 键,值 in 组合.items() if 值 is not None})#组合
            if 'outputSchema' in 输入 and 输入['outputSchema'] is not None:#结构化
                def 可以完成():
                    '没有未发布子，收件箱也空'
                    激活=自身._驻留.get(子标识)#自己的激活
                    拥有=0 if 激活 is None else len(激活['ownedChildren'])#子数
                    return 拥有==0 and len(孩子.inbox.下一步队列)==0 and len(孩子.inbox.下一轮队列)==0#可以交
                结构化盒[0]=挂上结构化运行时(子上下文,输入['outputSchema'],可以完成)#附件
        选项={'parentAgent':输入['parent'],'agentOptions':输入['agentOptions'],'signal':输入['signal'],'setup':设置}#共用
        if 创建 is None:#冷恢复
            选项['resumeSessionId']=子标识#要加载的会话
            句柄期约=自身._所有者上下文.agents.恢复(选项)#恢复
        else:#创建
            选项['sessionId']=子标识#预留 id
            选项['meta']=创建['meta']#元数据
            选项['inheritedEventCount']=创建['inheritedEventCount']#继承
            if 创建['seed'] is not None:#有种子
                选项['seed']=创建['seed']#种子
            句柄期约=自身._所有者上下文.agents.创建(选项)#创建
        def 句柄好了(句柄):
            '句柄发布后登记激活'
            资源={
                'kind':'local',#本地
                'handle':句柄,#句柄
                'outputStart':会话序号(句柄.智能体.session),#后缀起点
                'structured':结构化盒[0],#附件
                'failureAt':None,#尚无失败
                'poke':期约对(),#唤醒
            }#资源
            自身._发布激活(输入,子标识,资源,父谱系,池,释放槽,结果)#发布
        确保期约(句柄期约).然后(句柄好了,结果.拒绝)#句柄

    def _发布激活(自身,输入,子标识,资源,父谱系,池,释放槽,结果):
        '登记激活、发开始边；失败则回滚未发布的激活'
        父=输入['parent']#父
        观察者=自身._宿主['观察激活'](输入['provider'],子标识,父)#观察者
        成员=父谱系 if 资源['kind']=='external' else [资源['handle'].智能体,*父谱系]#谱系
        激活={
            'pool':池,#池
            'releaseSlot':释放槽,#释放槽
            'childId':子标识,#子 id
            'parent':父,#父
            'delivery':输入['delivery'] if 'delivery' in 输入 and 输入['delivery'] is not None else 'parent',#投递
            'result':期约对(),#结果
            'closing':None,#尚未关闭
            'ancestry':弱集合(成员),#弱谱系
            'ownedChildren':set(),#拥有的子
            'observer':观察者,#观察者
            'announced':False,#尚未接受过投递
            **资源,#种类资源
        }#激活
        激活['result']['期约'].捕获(lambda _错误: None)#结果拒绝不变成未处理
        自身._驻留[子标识]=激活#登记
        try:#准入后的发布检查
            自身._断言准入(父)#准入
            若中止则抛出(输入['signal'])#取消
            if 自身._上下文.agents.获取(父.id) is not 父:#父不活了
                raise 子智能体错误('subagent parent is no longer live','UNAUTHORIZED')#拒绝
            自身._取得所有权(父,子标识)#父拥有
            def 唤醒结算():
                '失败或收件箱变化时再看结算'
                自身._唤醒(激活)#唤醒
            if 激活['kind']=='local':#本地
                观察本地失败(激活,唤醒结算)#失败
                孩子上下文=激活['handle'].智能体.ctx#子上下文
                孩子上下文.监听('agent/inbox/inserted',唤醒结算)#插入
                孩子上下文.监听('agent/inbox/claimed',唤醒结算)#领取
                孩子上下文.监听('agent/inbox/discarded',唤醒结算)#丢弃
            观察者['start'](激活智能体(激活))#开始边
        except BaseException as 错误:#未发布就失败
            def 已回滚(_值=None):
                '回滚结束再抛原错'
                结果.拒绝(错误)#原错
            自身._回滚未发布(激活,错误).然后(已回滚,已回滚)#回滚失败不掩盖原错
            return#返回
        结果.解决(激活)#已发布

    def _宣布(自身,激活):
        '初始接受记下之后才开始结算观察'
        if 激活['announced']:#已经
            return#返回
        激活['announced']=True#接受过
        if 激活['kind']=='local':#本地
            自身._观察本地结算(激活)#观察
        else:#外部
            def 结束(_值=None):
                '结果落定后关闭，不额外停止'
                自身._关闭(激活,lambda: 自身._完成拆除(激活,False)).捕获(
                    lambda 错误: 自身._报告拆除失败(激活,错误),
                )#失败只记警告
            激活['run'].result.然后(结束,结束)#成败都关

    def _回滚未发布(自身,激活,错误):
        '释放还没发出开始边的激活'
        def 释放():
            '拆句柄、摘登记、拒绝结果'
            落定=期约()#释放结果
            句柄=激活['handle'].拆除() if 激活['kind']=='local' else (激活['run'].销毁() if hasattr(激活['run'],'销毁') else 激活['run'].dispose())#拆除
            def 收尾(_值=None):
                '无论拆除成败都摘掉'
                自身._驻留.pop(激活['childId'],None)#摘登记
                激活['releaseSlot']()#归还槽
                自身._放开所有权(激活['childId'])#放开父
                激活['result']['拒绝'](错误)#拒绝结果
                落定.解决()#释放完成
            确保期约(句柄).然后(收尾,收尾)#成败都收尾
            return 落定#期约
        return 自身._关闭(激活,释放)#共享关闭

    def _取得所有权(自身,父,子标识):
        '把子登记进受管父的拥有集'
        父激活=自身._驻留.get(父.id)#父
        if 父激活 is None:#父不受管
            return#不用
        if 父激活['closing'] is not None:#父在拆
            raise 子智能体错误(
                'subagent parent "'+str(父.id)+'" is being disposed; the child was not established',
                'ACTIVATION_CLOSING',
            )#拒绝
        父激活['ownedChildren'].add(子标识)#拥有
        自身._唤醒(父激活)#父再看结算

    def _放开所有权(自身,子标识):
        '从活主人的集合里拿掉这个子'
        for 候选 in list(自身._驻留.values()):#每个激活
            if 子标识 in 候选['ownedChildren']:#拥有它
                候选['ownedChildren'].discard(子标识)#拿掉
                自身._唤醒(候选)#再看结算

    def _唤醒(自身,激活):
        '让结算观察再检查驻留'
        if 激活['kind']=='external':#外部没有 poke
            return#返回
        激活['poke']['解决']()#兑现当前
        激活['poke']=期约对()#换一个新的

    def _观察本地结算(自身,激活):
        '跟着一个本地激活直到自然结算'
        def 一轮():
            '空闲后在锁里决定等、重试或关闭'
            空闲观察=激活['poke']#这一轮的唤醒
            def 已空闲(_值=None):
                '空闲后读结算状态'
                if 激活['closing'] is not None:#已经在关
                    return#停
                def 读状态():
                    '锁内读状态'
                    return 自身._结算状态(激活,空闲观察)#状态
                def 状态好了(就绪):
                    '按状态继续'
                    if 就绪=='closed':#已关
                        return#停
                    if 就绪=='retry' or 就绪=='wait':#重试或等待
                        if 就绪=='wait':#等唤醒
                            空闲观察['期约'].然后(lambda _值: 一轮(),lambda _错误: 一轮())#再来
                        else:#立刻再看
                            一轮()#再来
                        return#返回
                    最终序号=会话序号(激活['handle'].智能体.session)#关闭前的序号
                    def 已冲刷(_值=None):
                        '冲刷后再次确认并进入维护关闭'
                        def 决定():
                            '锁内做最后决定'
                            状态=自身._结算状态(激活,空闲观察)#再读
                            if 状态!='ready':#变了
                                return 状态#字符串
                            if 会话序号(激活['handle'].智能体.session)!=最终序号:#又有事件
                                return 'retry'#重试
                            try:#占用空闲阶段
                                def 维护(_信号):
                                    '维护窗口里开始自然关闭'
                                    自身._关闭(激活,lambda: 自身._完成拆除(激活,False))#不额外停止
                                激活['handle'].智能体.执行维护(维护)#维护
                            except BaseException:#空闲阶段已被占用
                                return 'retry'#重试
                            return {'done':激活['closing']}#关闭事务
                        def 决定好了(尝试):
                            '字符串就继续，否则等关闭'
                            if isinstance(尝试,str):#还没关
                                if 尝试=='closed':#已关
                                    return#停
                                一轮()#继续
                                return#返回
                            def 关闭失败(错误):
                                '自然结算的拆除失败只记一次'
                                自身._报告拆除失败(激活,错误)#警告
                            尝试['done'].然后(lambda _值: None,关闭失败)#等关闭
                        自身._锁.运行(激活['childId'],决定).然后(决定好了,lambda 错误: 自身._报告拆除失败(激活,错误))#决定
                    自身._冲刷最终状态(激活).然后(已冲刷,已冲刷)#冲刷失败也继续
                自身._锁.运行(激活['childId'],读状态).然后(状态好了,lambda 错误: 自身._报告拆除失败(激活,错误))#读状态
            激活['handle'].智能体.等到空闲().然后(已空闲,lambda 错误: 自身._报告拆除失败(激活,错误))#等空闲
        一轮()#开始

    def _报告拆除失败(自身,激活,错误):
        '自然结算观察结束后只报告一次拆除失败'
        自身._上下文.日志.警告('subagent "'+str(激活['childId'])+'" activation teardown failed: '+失败消息(错误))#警告

    def _结算状态(自身,激活,观察):
        '关闭准入前检查待处理输入和拥有的子'
        if 激活['closing'] is not None:#已关
            return 'closed'#已关
        if 激活['poke'] is not 观察:#观察过期
            return 'retry'#重试
        收件箱=激活['handle'].智能体.inbox#收件箱
        if len(激活['ownedChildren'])>0:#还有子
            return 'wait'#等
        if 激活['failureAt'] is None and (len(收件箱.下一轮队列)>0 or len(收件箱.下一步队列)>0):#还有输入
            return 'wait'#等
        return 'ready'#可以关

    def _完成拆除(自身,激活,停止):
        '同步传播停止，释放前等后代启动回滚'
        结果=期约()#拆除结果
        自身._唤醒(激活)#观察者醒来
        子标识=激活['childId']#子 id
        失败列表=[]#边界失败
        跑结果=[{'output':[],'stopReason':'error'}]#默认
        结果失败=[None]#跑结果自己的拒绝
        外部拆除=[None]#停止时提前开始的外部拆除
        孩子=激活智能体(激活)#本地孩子
        def 细节(错误):
            '本地用错误链，外部只用外层文案'
            if 孩子 is None:#外部
                return 失败消息(错误)#外层
            return 错误链(错误)#链
        def 收口():
            '摘登记、通知父、结算观察者，再按拆除失败拒绝'
            失败=None#汇总
            if len(失败列表)==1:#一条
                失败=失败列表[0]#那条
            elif len(失败列表)>1:#多条
                失败=子智能体错误(
                    'subagent "'+str(子标识)+'" activation teardown failed at '+str(len(失败列表))+' boundaries: '
                    +'; '.join(细节(项) for 项 in 失败列表),
                    'ACTIVATION_TEARDOWN_FAILED',
                    {'cause':失败列表},
                )#汇总
            自身._驻留.pop(子标识,None)#摘登记
            激活['releaseSlot']()#归还槽
            终态=跑结果[0] if 失败 is None else {'output':[],'stopReason':'error'}#拆除失败不算子体成功
            自身._通知结算(激活,跑结果[0])#用捕获到的结果通知，不用拆除失败覆盖后的终态边事实以外的那份
            自身._放开所有权(子标识)#放开父
            激活['observer']['settle'](终态)#终态边
            if 结果失败[0] is None:#跑结果干净
                激活['result']['解决'](跑结果[0])#兑现捕获结果
            else:#跑结果拒绝
                激活['result']['拒绝'](结果失败[0])#拒绝
            if 失败 is not None:#拆除失败
                结果.拒绝(失败)#拒绝
            else:#干净
                结果.解决()#兑现
        def 拆句柄():
            '拆本地句柄或外部跑'
            if 激活['kind']=='local':#本地
                拆除期约=激活['handle'].拆除()#句柄
            else:#外部
                已有=外部拆除[0]#停止时已经开始的
                拆除期约=已有 if 已有 is not None else (激活['run'].销毁() if hasattr(激活['run'],'销毁') else 激活['run'].dispose())#拆除
            def 句柄失败(错误):
                '句柄拆除失败'
                失败列表.append(子智能体错误(
                    'subagent "'+str(子标识)+'" activation handle disposal failed: '+细节(错误),
                    'ACTIVATION_TEARDOWN_FAILED',
                    {'cause':错误},
                ))#记下
                收口()#继续
            确保期约(拆除期约).然后(lambda _值: 收口(),句柄失败)#拆完收口
        def 跑好了(值):
            '跑结果兑现'
            跑结果[0]=值#记下
            拆句柄()#拆句柄
        def 跑坏了(错误):
            '跑结果或停止失败'
            结果失败[0]=错误#记下
            失败列表.append(子智能体错误(
                'subagent "'+str(子标识)+'" activation teardown failed: '+细节(错误),
                'ACTIVATION_TEARDOWN_FAILED',
                {'cause':错误},
            ))#记下
            拆句柄()#仍拆句柄
        try:#按种类取结果
            if 激活['kind']=='external':#外部
                if 停止:#要停
                    激活['controller'].中止({'kind':'parent'})#父停止
                    外部拆除[0]=确保期约(激活['run'].销毁() if hasattr(激活['run'],'销毁') else 激活['run'].dispose())#有的后端要拆除才结算结果
                    外部拆除[0].捕获(lambda _错误: None)#先吞，句柄阶段再记
                确保期约(激活['run'].result).然后(跑好了,跑坏了)#等结果
            else:#本地
                自身._停止本地后捕获(激活,停止,跑好了,跑坏了,失败列表)#停止并捕获
        except BaseException as 错误:#同步失败
            跑坏了(错误)#按跑失败
        return 结果#期约

    def _停止本地后捕获(自身,激活,停止,成功,失败,失败列表):
        '本地停止时先拆子孙并等到空闲，再捕获结果'
        if not 停止:#自然结算
            try:#捕获
                成功(捕获本地结果(激活))#捕获
            except BaseException as 错误:#捕获失败
                失败(错误)#失败
            return#结束
        激活['handle'].智能体.取消({'kind':'parent'})#停止
        空闲=激活['handle'].智能体.等到空闲()#等空闲
        孩子们=[自身._驻留[标识] for 标识 in 激活['ownedChildren'] if 标识 in 自身._驻留]#活着的子
        待定=[项 for 项 in 自身._物化 if 激活['handle'].智能体 in 项['lineage']]#还在物化的
        拆除们=[自身.拆除(孩子) for 孩子 in 孩子们]#拆子
        for 项 in 待定:#取消物化
            项['controller'].中止()#取消
        拆除们.extend(项['settled']['期约'] for 项 in 待定)#等物化
        def 子孙完(结算列表):
            '子孙失败记下来，再等空闲和冲刷'
            原因们=[]#失败
            for 项 in 结算列表:#逐个
                状态=项['status'] if isinstance(项,dict) else getattr(项,'status',None)#状态
                if 状态=='rejected':#拒绝
                    原因们.append(项['reason'] if isinstance(项,dict) else getattr(项,'reason',None))#原因
            if len(原因们)>0:#有失败
                失败列表.append(子智能体错误(
                    'subagent "'+str(激活['childId'])+'" child teardown failed: '+'; '.join(失败消息(项) for 项 in 原因们),
                    'ACTIVATION_TEARDOWN_FAILED',
                ))#记下，不覆盖跑结果
            def 已空闲(_值=None):
                '空闲后冲刷再捕获'
                def 已冲刷(_值=None):
                    '捕获'
                    try:#捕获
                        成功(捕获本地结果(激活))#捕获
                    except BaseException as 错误:#失败
                        失败(错误)#失败
                自身._冲刷最终状态(激活).然后(已冲刷,已冲刷)#冲刷
            空闲.然后(已空闲,失败)#空闲失败算跑失败
        if len(拆除们)==0:#没有子孙
            子孙完([])#直接
        else:#等待
            期约.全部已结算(拆除们).然后(子孙完,失败)#全部结算

    def _通知结算(自身,激活,终态):
        '清理之后把捕获到的执行结果交给耐久直接父'
        if not 激活['announced'] or 激活['delivery']=='caller':#没宣布或调用方自己收结果
            return#不通知
        try:#投递
            父=自身._上下文.agents.获取(激活['parent'].id)#活父
            if 父 is not 激活['parent']:#不是当时那个父
                return#不投
            消息=创建结算消息(激活['childId'],终态,激活智能体(激活) is not None)#可续跑与否
            if 自身._关闭拆除于(父) is not None:#父树正在排空
                父.注入(消息)#注入，不唤醒
                return#结束
            自身._醒着发送(父,消息,'queue' if 父.状态=='idle' else 'steer')#空闲排队，否则转向
        except BaseException as 错误:#通知失败
            自身._上下文.日志.警告(
                'subagent "'+str(激活['childId'])+'" settlement notice was not delivered to its parent: '+错误链(错误),
            )#警告

    def _冲刷最终状态(自身,激活):
        '自然结算关闭准入前尽力做最后一次会话冲刷'
        结果=期约()#总是兑现
        try:#冲刷
            会话表=激活['handle'].智能体.ctx.sessions#会话服务
            确保期约(会话表.flush(激活['handle'].智能体.session)).然后(结果.解决,lambda 错误: 自身._冲刷失败(激活,错误,结果))#冲刷
        except BaseException as 错误:#没有 flush 或同步失败
            自身._冲刷失败(激活,错误,结果)#警告后继续
        return 结果#期约

    def _冲刷失败(自身,激活,错误,结果):
        '冲刷失败只警告，恢复时持久化状态可能旧或缺'
        自身._上下文.日志.警告(
            'subagent "'+str(激活['childId'])+'" best-effort final session flush failed; '
            +'the persisted state may be unavailable or stale on resume: '+错误链(错误),
        )#警告
        结果.解决()#不阻断结算

    def _回执(自身,激活):
        '能力绑在这一次激活上，不是以后同 id 的另一次'
        return {'childId':激活['childId'],'result':激活['result']['期约'],'dispose':lambda: 自身.拆除(激活)}#回执

    def _投递到子(自身,父,子标识,内容,选项):
        '父发起的投递：驻留或冷恢复'
        结果=期约()#消息 id
        try:#准入与持有
            自身._断言准入(父)#准入
            释放=自身._持有所有权(父,子标识)#持有
        except BaseException as 错误:#失败
            结果.拒绝(错误)#拒绝
            return 结果#期约
        def 失败(错误):
            '释放后拒绝'
            释放()#释放
            结果.拒绝(错误)#原错
        自身._投递后续(父,子标识,内容,选项).然后(结果.解决,失败)#投递
        return 结果#期约

    def _投递后续(自身,父,子标识,内容,选项):
        '持有之下的投递循环'
        结果=期约()#消息 id
        def 一轮():
            '锁里看驻留、关闭或冷恢复'
            def 临界():
                '返回消息 id、关闭期约，或 None 表示要重试'
                临界结果=期约()#临界结果
                激活=自身._驻留.get(子标识)#驻留
                if 激活 is None:#不在
                    return 自身._冷恢复(父,子标识,内容,选项)#冷恢复期约
                try:#必须能续跑
                    要求本地激活(激活)#外部则拒绝
                except BaseException as 错误:#不能
                    临界结果.拒绝(错误)#拒绝
                    return 临界结果#期约
                拆除中=激活['closing']#关闭事务
                if 拆除中 is not None:#正在关
                    拆除中.然后(lambda _值: 临界结果.解决(None),lambda _错误: 临界结果.解决(None))#关完重试
                    return 临界结果#期约
                def 图片之后(_值=None):
                    '图片检查后再看是不是刚开始关'
                    if 激活['closing'] is not None:#刚关
                        激活['closing'].然后(lambda _值2: 临界结果.解决(None),lambda _错误: 临界结果.解决(None))#重试
                        return#返回
                    try:#提交
                        消息标识=自身._提交已接受(激活,内容,选项,父)#同步接受
                        自身._宣布(激活)#宣布
                        临界结果.解决(消息标识)#消息 id
                    except BaseException as 错误:#失败
                        临界结果.拒绝(错误)#拒绝
                if 内容含图片(内容):#有图片
                    自身._断言能收图片(要求本地激活(激活)['handle'].智能体,选项['signal']).然后(图片之后,临界结果.拒绝)#检查
                else:#无图片
                    图片之后()#直接提交
                return 临界结果#期约
            def 临界好了(活):
                'None 表示输给了拆除截止，重试'
                if 活 is not None:#接受了
                    结果.解决(活)#兑现
                    return#结束
                try:#重试前再查
                    自身._断言准入(父)#准入
                    若中止则抛出(选项['signal'])#取消
                except BaseException as 错误:#失败
                    结果.拒绝(错误)#拒绝
                    return#结束
                一轮()#重试
            自身._锁.运行(子标识,临界).然后(临界好了,结果.拒绝)#锁
        一轮()#开始
        return 结果#期约

    def _发给父(自身,激活,发送方,内容):
        '驻留可续跑子把消息发给活着的直接父'
        if 激活['closing'] is not None:#正在拆
            raise 子智能体错误(
                'subagent "'+str(发送方.id)+'" activation is being disposed; the message was not delivered',
                'ACTIVATION_CLOSING',
            )#拒绝
        父=自身._上下文.agents.获取(激活['parent'].id)#活父
        if 父 is not 激活['parent']:#不活
            raise 子智能体错误('direct parent is not live; the message was not delivered','PARENT_UNAVAILABLE')#拒绝
        消息=创建智能体消息(发送方,内容)#相邻消息
        自身._发送智能体消息(父,消息)#转向
        return 消息['id']#消息 id

    def _发送智能体消息(自身,父,消息):
        '发送智能体消息时只翻译目标自己的拒绝'
        try:#发送
            自身._醒着发送(父,消息,'steer')#转向
        except BaseException as 错误:#目标拒绝
            raise 子智能体错误('direct parent is not live; the message was not delivered','PARENT_UNAVAILABLE',{'cause':错误})#翻译

    def _冷恢复(自身,父,子标识,内容,选项):
        '从持久化描述符冷恢复子体并提交等待中的回合'
        结果=期约()#消息 id
        try:#查询
            查询=自身._要求会话查询()#查询
            观察=查询.observeSession(子标识,{'signal':选项['signal']})#观察
        except BaseException as 错误:#读不到
            try:#取消优先
                若中止则抛出(选项['signal'])#取消
            except BaseException as 取消:#取消
                结果.拒绝(取消)#取消
                return 结果#期约
            结果.拒绝(子智能体错误('subagent "'+str(子标识)+'" is unavailable','NOT_RESUMABLE',{'cause':错误}))#不可恢复
            return 结果#期约
        try:#授权与描述符
            自身._断言准入(父)#准入
            自身._授权谱系(父,子标识,头取(观察.header,'parentSession'))#谱系
            事件=观察.events#事件
            继承=观察.inheritedEventCount#继承
            描述符=折叠子智能体描述符(事件[继承:])#描述符
            if 描述符 is None or 描述符['mode']!='continuable':#不能续
                raise 子智能体错误(
                    'subagent "'+str(子标识)+'" has no supported continuation state and cannot be resumed; choose a different target',
                    'NOT_RESUMABLE',
                )#拒绝
            智能体选项={}#从描述符重建
            if 'agentProvider' in 描述符:#提供方
                智能体选项['provider']=描述符['agentProvider']#提供方
            if 'agentModel' in 描述符:#模型
                智能体选项['model']=描述符['agentModel']#模型
            if 'agentReasoningEffort' in 描述符:#力度
                智能体选项['reasoningEffort']=推理力度标识(描述符['agentReasoningEffort'])#品牌
            组合={'persona':描述符['persona'] if 'persona' in 描述符 else None,'toolFilter':描述符['toolFilter'] if 'toolFilter' in 描述符 else None}#组合
        except BaseException as 错误:#失败
            if hasattr(观察,'close'):#释放观察
                观察.close()#关
            结果.拒绝(错误)#拒绝
            return 结果#期约
        if hasattr(观察,'close'):#释放观察
            观察.close()#关
        def 已物化(激活):
            '物化后提交这条消息'
            自身._提交已物化(激活,内容,选项,父).然后(结果.解决,结果.拒绝)#提交
        def 物化失败(错误):
            '取消优先，子智能体错误原样，其余不可恢复'
            try:#取消
                若中止则抛出(选项['signal'])#取消
            except BaseException as 取消:#取消
                结果.拒绝(取消)#取消
                return#结束
            if isinstance(错误,子智能体错误):#已是缝内错误
                结果.拒绝(错误)#原样
            else:#其他
                结果.拒绝(子智能体错误('subagent "'+str(子标识)+'" is unavailable','NOT_RESUMABLE',{'cause':错误}))#包装
        自身._物化({
            'kind':'local',#本地
            'childId':子标识,#子 id
            'provider':描述符['provider'],#描述符里的提供方
            'parent':父,#父
            'agentOptions':智能体选项,#路由
            'composition':组合,#组合
            'signal':选项['signal'],#信号
        }).然后(已物化,物化失败)#物化
        return 结果#期约

    def _提交已物化(自身,激活,内容,选项,父,提交=None):
        '接受已物化的子，提交创建事实，失败则释放'
        结果=期约()#消息 id
        def 接受(_值=None):
            '图片检查通过后同步接受'
            try:#关闭与接受
                if 激活['closing'] is not None:#正在关
                    raise 子智能体错误('subagent "'+str(激活['childId'])+'" is closing','ACTIVATION_CLOSING')#拒绝
                消息标识=自身._提交已接受(激活,内容,选项,父)#接受
                if 提交 is not None:#创建事实
                    提交()#目录
                自身._宣布(激活)#宣布
                结果.解决(消息标识)#消息 id
            except BaseException as 错误:#失败则拆
                def 已拆(_值2=None):
                    '拆完再抛原错'
                    结果.拒绝(错误)#原错
                def 拆失败(清理错误):
                    '拆除也失败只记警告'
                    自身._上下文.日志.警告(
                        'subagent continuation: disposal after admission or catalog append failure also failed: '+str(清理错误),
                    )#警告
                    结果.拒绝(错误)#原错
                自身.拆除(激活).然后(已拆,拆失败)#拆
        if 内容含图片(内容):#有图片
            自身._断言能收图片(要求本地激活(激活)['handle'].智能体,选项['signal']).然后(接受,结果.拒绝)#检查
        else:#无图片
            接受()#直接
        return 结果#期约

    def _提交已接受(自身,激活,内容,选项,父):
        '在最后一道同步准入上建造并提交消息'
        if 'source' not in 选项 or 选项['source'] is None:#相邻智能体
            消息=创建智能体消息(父,内容)#父撰写
        else:#宿主来源
            消息=创建用户消息({'content':内容,'source':选项['source']})#保留来源
        若中止则抛出(选项['signal'])#取消
        自身._断言准入(父)#准入
        自身._授权谱系(父,激活['childId'],激活['parent'].id)#谱系
        自身._取得所有权(父,激活['childId'])#拥有
        try:#投递
            自身._投递(激活,消息,选项['delivery'])#接受
        finally:#唤醒
            自身._唤醒(激活)#再看结算
        return 消息['id']#消息 id

    def _断言能收图片(自身,智能体,信号):
        '固定模型不收图片时拒绝'
        结果=期约()#结果
        选项=智能体.options#选项
        提供方=选项['provider'] if isinstance(选项,dict) and 'provider' in 选项 else None#提供方
        模型=选项['model'] if isinstance(选项,dict) and 'model' in 选项 else None#模型
        if 提供方 is None or 模型 is None:#没有固定路由
            结果.解决()#留给投影
            return 结果#期约
        语言模型=自身._上下文.获取服务('llm')#语言模型
        if 语言模型 is None:#没有注册表
            结果.解决()#留给投影
            return 结果#期约
        try:#解析
            信息=语言模型.解析模型信息(提供方,模型,信号)#模型信息
            模态=信息['inputModalities'] if isinstance(信息,dict) and 'inputModalities' in 信息 else None#模态
            if 模态 is not None and 'image' not in 模态:#不收图片
                raise 子智能体错误('Model "'+str(模型)+'" does not support image input.','MODEL_DOES_NOT_SUPPORT_IMAGES')#拒绝
            结果.解决()#可以
        except BaseException as 错误:#失败
            结果.拒绝(错误)#拒绝
        return 结果#期约

    def _要求持久化(自身):
        '可续跑子体必须有持久化'
        持久化=自身._上下文.获取服务('sessionPersistence')#持久化
        if 持久化 is None:#没有
            raise 子智能体错误(
                'continuable subagents require session persistence (load a dsh-session-persistence backend)',
                'PERSISTENCE_UNAVAILABLE',
            )#拒绝
        return 持久化#服务

    def _要求会话查询(自身):
        '冷观察要用会话查询'
        查询=自身._上下文.获取服务('sessionQuery')#查询
        if 查询 is None:#没有
            raise 子智能体错误(
                'continuable subagents require session query (load @deepseek-ai/dsh-session-query)',
                'CONTINUATION_UNAVAILABLE',
            )#拒绝
        return 查询#服务

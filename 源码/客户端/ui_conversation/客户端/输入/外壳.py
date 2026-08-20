"""纯输入机上的会话输入外壳：唯一机器调用方与效果执行器。

对齐上游 `ui-conversation/src/client/input/facade.ts`。公开面仅中文名。
拥有 InputState store（机器状态 + 队列叠加）、通知通道与提交事务管道。
"""
from .机 import 输入机#纯输入状态机

__all__=['快照仓库','会话输入壳','守卫档']#仅中文公开名

空队列=()#缺席队列
空词表={}#无管道词表

class 快照仓库:#简易 SnapshotStore
    """值 + 订阅；对齐 createSnapshotStore。"""
    def __init__(自身,初值):#播种
        """记下初值。"""
        自身.状态=初值#当前
        自身.监听者=set()#订阅者

    def getSnapshot(自身):#读
        """返回当前值。"""
        return 自身.状态#值

    def subscribe(自身,回调):#订阅
        """登记。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一份):#替换
        """写入并通知。"""
        自身.状态=下一份#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

def 守卫档(相位):#阶段 → 守卫档
    """plain / claimed / frozen。"""
    if 相位=='plain':#明文
        return 'plain'#可编
    if 相位=='claimed':#已认领
        return 'claimed'#认领档
    return 'frozen'#裁决/提交中

def 接续(结果,成功,失败=None):#统一 then/同步结果
    """有 then 则挂回调；否则当即成功。禁止 async/await。"""
    then=getattr(结果,'then',None)#Promise 面
    if callable(then):#异步面
        if 失败 is None:#仅成功
            then(成功)#挂
        else:#双臂
            then(成功,失败)#挂
        return#结束
    try:#同步
        成功(结果)#当即
    except Exception as 错:#同步抛错
        if 失败 is not None:#有失败臂
            失败(错)#走失败

class 会话输入壳:#每会话输入外壳
    """作用域事件应用动词 + setDraft/submit + 发布的 InputState store。"""
    def __init__(自身,依赖):#注入依赖并发布初态
        """斜杠/弹层面都是 thunk。"""
        自身.依赖=依赖#依赖
        自身.核心=输入机({'now':依赖.get('now') or __import__('time').time})#真实 now；可注入
        自身.通知序号=0#通知序号
        自身.上次草稿=''#上次镜像
        自身.图片标识们=[]#本草稿图 id
        自身.已拆除=False#拆除后丢迟到结算
        自身.镜像写出=None#草稿持久化
        自身.notices=快照仓库(None)#通知 store
        自身.state=快照仓库(自身.合成())#初态
        自身.actions={#公开动作面
            'setDraft':lambda 文:自身.setDraft(文),#写草稿
            'addImages':lambda 标识们:自身.addImages(标识们),#加图
            'removeImage':lambda 标识:自身.removeImage(标识),#删图
            'pruneImages':lambda 标识们:自身.pruneImages(标识们),#修剪
            'submit':lambda:自身.submit('queue'),#以 queue 提交
        }#动作结束
        队列=依赖.get('queue')#队列读面
        if 队列 is not None and hasattr(队列,'subscribe'):#有队列
            队列.subscribe(lambda:自身.发布())#队列变则重发
        自身.lexicon={#词表观察源
            'getSnapshot':自身.读词表,#读
            'subscribe':自身.订词表,#订
        }#词表结束

    def 读词表(自身):#读热词表
        """无管道则空。"""
        触发=自身.取触发()#控制器
        if 触发 is None:#无
            return 空词表#空
        词=getattr(触发,'lexicon',None)#词表
        if 词 is None:#无
            return 空词表#空
        return 词.getSnapshot() if hasattr(词,'getSnapshot') else 空词表#快照

    def 订词表(自身,回调):#订热词表
        """无管道则空订阅。"""
        触发=自身.取触发()#控制器
        if 触发 is None:#无
            return lambda:None#空退订
        词=getattr(触发,'lexicon',None)#词表
        if 词 is None or not hasattr(词,'subscribe'):#无
            return lambda:None#空退订
        return 词.subscribe(回调)#退订器

    def 取触发(自身):#解析触发控制器
        """thunk 惰性解析。"""
        解析=自身.依赖.get('inputTriggers')#thunk
        return 解析() if callable(解析) else None#结果

    def 取弹层(自身):#解析弹层关闭面
        """thunk 惰性解析。"""
        解析=自身.依赖.get('popup')#thunk
        return 解析() if callable(解析) else None#结果

    def setDraft(自身,文本,编辑范围=None):#写草稿
        """唯一草稿写入路径。"""
        事件={'type':'draft-changed','draft':文本}#事件
        if 编辑范围 is not None:#有形态
            事件['editRange']=编辑范围#带上
        自身.执行(自身.核心.dispatch(事件))#派发

    def addImages(自身,标识们):#追加图片
        """忙碌准入相位拒绝。"""
        if 自身.snapshot['phase'] in ('adjudicating','submitting'):#忙碌
            return False#拒绝
        if len(标识们)==0:#空
            return True#成功
        自身.图片标识们=list(自身.图片标识们)+list(标识们)#追加
        自身.发布()#发布
        return True#已追加

    def removeImage(自身,标识):#移除一张图
        """滤掉该 id。"""
        下一=[项 for 项 in 自身.图片标识们 if 项!=标识]#滤
        if len(下一)==len(自身.图片标识们):#无变化
            return#停
        自身.图片标识们=下一#写回
        自身.发布()#发布

    def pruneImages(自身,可用):#修剪失效图
        """只保留仍在册的。"""
        留=set(可用)#在册
        下一=[项 for 项 in 自身.图片标识们 if 项 in 留]#滤
        if len(下一)==len(自身.图片标识们):#无变化
            return#停
        自身.图片标识们=下一#写回
        自身.发布()#发布

    def restoreImages(自身,标识们):#恢复失败尝试的图
        """缺的插到前面。"""
        当前=set(自身.图片标识们)#已有
        缺=[项 for 项 in 标识们 if 项 not in 当前]#缺的
        自身.图片标识们=缺+list(自身.图片标识们)#插前
        自身.发布()#发布

    def commitSend(自身,图片标识们):#提交发送成功
        """不记撤销；去掉已送图。"""
        已送=set(图片标识们)#已送
        自身.图片标识们=[项 for 项 in 自身.图片标识们 if 项 not in 已送]#去掉
        自身.执行(自身.核心.dispatch({'type':'send-committed'}))#机器提交

    def undo(自身):#撤销
        """派发撤销。"""
        自身.执行(自身.核心.dispatch({'type':'undo'}))#撤销

    def redo(自身):#重做
        """派发重做。"""
        自身.执行(自身.核心.dispatch({'type':'redo'}))#重做

    def pasteBegin(自身,文本,选区,分量=None,代数=None):#开始粘贴
        """一次事务贴选区。"""
        事件={'type':'paste-begin','text':文本,'selection':选区}#事件
        if 分量 is not None:#有分量
            事件['components']=分量#带上
        if 代数 is not None:#有代数
            事件['generation']=代数#带上
        自身.执行(自身.核心.dispatch(事件))#派发

    def invalidatePaste(自身):#作废粘贴
        """结束粘贴尝试。"""
        自身.执行(自身.核心.dispatch({'type':'invalidate-paste'}))#作废

    def submit(自身,模式='queue'):#提交
        """空草稿有图直送；否则 enter。"""
        快=自身.snapshot#快照
        if 快['draft'].strip()=='' and len(自身.图片标识们)>0:#空草稿有图
            if 快['phase']=='plain':#明文
                自身.依赖['defaultSink']('',list(自身.图片标识们),模式)#直送
            return#停
        自身.执行(自身.核心.dispatch({'type':'enter','mode':模式}))#回车
        相位=自身.snapshot['phase']#回车后
        if 相位 in ('adjudicating','submitting'):#已锁定
            弹=自身.取弹层()#弹层
            if 弹 is not None and hasattr(弹,'dismiss'):#可关
                弹.dismiss()#关
            触发=自身.取触发()#触发
            if 触发 is not None and hasattr(触发,'track'):#可跟踪
                下=自身.snapshot#替换后
                触发.track(下['draft'],0,{'tier':'frozen'},下['draftRev'])#冻结档

    def track(自身,草稿,光标):#跟踪草稿与光标
        """守卫由相位导出。"""
        触发=自身.取触发()#触发
        if 触发 is not None and hasattr(触发,'track'):#可
            触发.track(草稿,光标,{'tier':守卫档(自身.snapshot['phase'])},自身.snapshot['draftRev'])#跟踪

    def arbitrate(自身,键,合成中):#仲裁按键
        """无管道则 pass。"""
        触发=自身.取触发()#触发
        if 触发 is None or not hasattr(触发,'arbitrate'):#无
            return 'pass'#放行
        return 触发.arbitrate(键,合成中)#裁决

    def steerQueue(自身):#导入队列
        """有依赖才执行。"""
        转向=自身.依赖.get('steerQueue')#thunk
        if callable(转向):#有
            转向()#执行

    def space(自身):#空格裁决
        """true = 已应用认领/插入。"""
        触发=自身.取触发()#触发
        if 触发 is None or not hasattr(触发,'onSpace'):#无
            return False#未消费
        已吃=触发.onSpace()#是否吃掉
        if 已吃:#已应用
            下=自身.snapshot#替换后
            触发.track(下['draft'],len(下['draft']),{'tier':守卫档(下['phase'])},下['draftRev'])#再跟踪
        return 已吃#是否消费

    def dismissPopup(自身):#关闭弹层
        """框外交互。"""
        弹=自身.取弹层()#弹层
        if 弹 is not None and hasattr(弹,'dismiss'):#可
            弹.dismiss()#关

    def beginCommand(自身,认领,跨度):#开始命令
        """机器是否接受。"""
        前=自身.核心.state['draftRev']#派发前
        自身.执行(自身.核心.dispatch({'type':'begin-command','claim':认领,'span':跨度}))#派发
        后=自身.核心.state#派发后
        return 后['phase']=='claimed' and 后['draftRev']!=前#已认领且修订前进

    def insertReference(自身,引用,跨度):#插入引用
        """机器是否接受。"""
        前=自身.核心.state['draftRev']#派发前
        自身.执行(自身.核心.dispatch({'type':'insert-ref','reference':引用,'span':跨度}))#派发
        return 自身.核心.state['draftRev']!=前#修订前进

    def consumeToken(自身,守卫):#消费令牌
        """跨度 CAS 再拼接；裸令牌清空。"""
        快=自身.核心.state#机态
        种=守卫.get('kind') if isinstance(守卫,dict) else getattr(守卫,'kind',None)#种
        if 种=='span':#跨度
            跨度=守卫.get('span') if isinstance(守卫,dict) else getattr(守卫,'span',None)#跨度
            if 跨度 is None or 跨度.get('draftRev')!=快['draftRev']:#对不上
                return False#放弃
            草稿=快['draft']#草稿
            自身.setDraft(草稿[:跨度['start']]+草稿[跨度['end']:])#切掉
            return True#已拼
        令牌=守卫.get('token') if isinstance(守卫,dict) else getattr(守卫,'token','')#令牌
        if 快['draft'].strip()!=令牌:#对不上
            return False#放弃
        自身.setDraft('')#清空
        return True#已清

    def insertText(自身,文本,跨度):#插入纯文本
        """CAS 再拼接；不铸造出现。"""
        快=自身.核心.state#机态
        if 跨度.get('draftRev')!=快['draftRev']:#对不上
            return False#放弃
        草稿=快['draft']#草稿
        自身.setDraft(草稿[:跨度['start']]+文本+草稿[跨度['end']:])#替换
        return True#已拼

    def notify(自身,级别,正文):#浮出通知
        """脱离的命令结果。"""
        自身.通知序号+=1#前进
        自身.notices.set({'level':级别,'text':正文,'seq':自身.通知序号})#写入

    def dispose(自身):#拆除外壳
        """中止进行中尝试。"""
        自身.已拆除=True#后续丢弃
        自身.执行(自身.核心.dispatch({'type':'release'}))#释放

    @property
    def snapshot(自身):#当前输入状态
        """读现场。"""
        return 自身.state.getSnapshot()#store 快照

    def bindMirror(自身,写出):#绑定镜像写出
        """绑定即采纳；返回解绑。"""
        自身.镜像写出=写出#记下
        def 解绑():#解绑
            """仍是自己才清。"""
            if 自身.镜像写出 is 写出:#仍是
                自身.镜像写出=None#清
        return 解绑#退订器

    def 执行(自身,效应们):#执行效果并发布
        """逐条执行后叠队列发布。"""
        for 效应 in 效应们:#逐条
            自身.跑效应(效应)#执行
        自身.发布()#发布

    def 跑效应(自身,效应):#按效果类型分发
        """notice / adjudicate / begin-submit / default-sink。"""
        种=效应.get('type')#标签
        if 种=='notice':#通知
            自身.通知序号+=1#前进
            自身.notices.set({'level':效应['level'],'text':效应['text'],'seq':自身.通知序号})#写
            return#停
        if 种=='adjudicate':#裁决
            自身.裁决(效应['attempt'],效应['draft'])#问控制器
            return#停
        if 种=='begin-submit':#开始提交
            自身.开始提交(效应['attempt'],效应['claim'],效应['args'])#claim.submit
            return#停
        if 种=='default-sink':#默认汇
            自身.序列化汇(效应['draft'],效应['mode'])#序列化后发送
            return#停

    def 序列化汇(自身,草稿,模式):#序列化后送默认汇
        """无芯片同步直送；有芯片经控制器序列化引用。"""
        图们=list(自身.图片标识们)#本批图
        出现表=自身.核心.state['occurrences']#出现
        if len(出现表)==0:#无芯片
            自身.依赖['defaultSink'](草稿.strip(),图们,模式)#直送
            return#停
        触发=自身.取触发()#控制器
        已取消={'v':False}#取消旗
        def 序列化一项(项):#序列化单个出现
            """无控制器则抛。"""
            if 触发 is None:#无
                raise Exception('no serializer for reference source "'+str(项.get('source'))+'"')#失败
            信号=type('S',(),{'aborted':False})()#简易信号
            信号.aborted=已取消['v']#同步旗
            return {'offset':项['offset'],'text':触发.serializeReference(项['source'],项['ref'],信号)}#偏移与模型形
        try:#顺序执行（禁止 async）
            部件=[序列化一项(项) for 项 in 出现表]#全部
            if 自身.已拆除:#已拆
                return#丢
            出=''#缓冲
            游标=0#游标
            for 部 in 部件:#按出现序
                出+=草稿[游标:部['offset']]+部['text']#拼
                游标=部['offset']+1#跳占位
            出+=草稿[游标:]#尾
            自身.依赖['defaultSink'](出.strip(),图们,模式)#送汇
        except Exception as 错:#任一失败
            已取消['v']=True#取消其余
            if 自身.已拆除:#已拆
                return#丢
            自身.notify('error',str(错))#浮出，草稿保留
    def 裁决(自身,尝试,草稿):#回车裁决
        """未挂管道：'/' 行当普通消息。"""
        触发=自身.取触发()#控制器
        if 触发 is None:#未挂
            自身.执行(自身.核心.dispatch({'type':'adjudicated','attempt':尝试,'outcome':None}))#无挑选
            return#停
        def 成功(结局):#挑选结果
            """过期则丢。"""
            if 自身.已失效(尝试):#过期
                return#丢
            自身.执行(自身.核心.dispatch({'type':'adjudicated','attempt':尝试,'outcome':结局}))#喂机
        def 失败(错):#裁决抛错
            """过期则丢。"""
            if 自身.已失效(尝试):#过期
                return#丢
            消息=str(错)#文案
            自身.执行(自身.核心.dispatch({'type':'adjudication-failed','attempt':尝试,'message':消息}))#失败
        接续(触发.adjudicate(草稿.strip(),尝试['signal']),成功,失败)#问控制器

    def 开始提交(自身,尝试,认领,参数):#开始提交事务
        """对会话作用域做 claim.submit。"""
        def 成功(结局):#业务结果
            """过期则丢。"""
            if 自身.已失效(尝试):#过期
                return#丢
            好=结局.get('kind')=='success' if isinstance(结局,dict) else getattr(结局,'kind',None)=='success'#成功否
            自身.执行(自身.核心.dispatch({'type':'submit-settled','attempt':尝试,'ok':好,'outcome':结局}))#结算
        def 失败(错):#提交抛错
            """过期则丢。"""
            if 自身.已失效(尝试):#过期
                return#丢
            自身.执行(自身.核心.dispatch({'type':'submit-settled','attempt':尝试,'ok':False,'message':str(错)}))#失败结算
        提交=认领.get('submit') if isinstance(认领,dict) else getattr(认领,'submit',None)#submit
        if not callable(提交):#无
            失败(Exception('claim.submit unavailable'))#失败
            return#停
        接续(提交(参数,自身.依赖['actx']),成功,失败)#在会话作用域提交

    def 已失效(自身,尝试):#迟到结算守卫
        """拆除或已中止。"""
        信号=尝试.get('signal') if isinstance(尝试,dict) else None#信号
        中止=getattr(信号,'aborted',False) if 信号 is not None else False#中止
        return 自身.已拆除 or 中止#失效

    def 合成(自身):#机器状态叠图片与队列
        """叠图与队列。"""
        核心=自身.核心.state#机态
        队列面=自身.依赖.get('queue')#队列
        队列=队列面.getSnapshot() if 队列面 is not None and hasattr(队列面,'getSnapshot') else list(空队列)#队列
        return {**核心,'imageIds':list(自身.图片标识们),'queue':list(队列)}#叠好

    def 发布(自身):#发布状态并按需镜像
        """草稿变了才镜像。"""
        下一=自身.合成()#叠好
        自身.state.set(下一)#写入
        if 下一['draft']!=自身.上次草稿:#草稿变
            自身.上次草稿=下一['draft']#记下
            if 自身.镜像写出 is not None:#有绑定
                自身.镜像写出(下一['draft'])#写出

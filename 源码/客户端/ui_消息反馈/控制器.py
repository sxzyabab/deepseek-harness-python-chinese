from ...基础设施.js特性 import PromiseEX as 期约#中文别名的期约
from ...基础设施.通用工具 import 观察者集合
from .异常 import 消息反馈错误#本包异常

__all__=['消息反馈控制器','消息反馈错误','描述失败','成功结果','已拆除结果']#仅中文公开名

空条目表={}#空条目
初始视图={'status':'cold','items':空条目表,'error':None}#冷启动
成功结果={'ok':True}#成功常量
已拆除结果={'ok':False,'error':{'code':'disposed','message':'feedback controller is disposed'}}#拆除形

def 描述失败(码):#失败码 → 可读文案
    '一条业务失败码的可读文案'
    if 码=='session-not-found':#会话不在
        return 'this session is no longer persisted'#文案
    if 码=='target-not-found':#消息不在
        return 'this message is not a persisted assistant message'#文案
    if 码=='version-conflict':#冲突
        return 'feedback changed elsewhere'#文案
    if 码=='note-blank':#空白 note
        return 'a note must contain a non-whitespace character'#文案
    if 码=='note-too-large':#过长
        return 'the note is too long'#文案
    return 码#未知原样

def 失败(码):#业务失败形
    '按码构造拒绝臂'
    return {'ok':False,'error':{'code':码,'message':描述失败(码)}}#失败

def 载体失败(错误):#载体失败原样
    '宿主给出的码与文案'
    码=错误['code'] if 错误 is not None and 'code' in 错误 else None#码
    消息=错误['message'] if 错误 is not None and 'message' in 错误 else None#文案
    return {'ok':False,'error':{'code':码,'message':消息}}#原样

class 消息反馈控制器:#每会话反馈对象层
    '一个实例支撑该 Session 内每条消息的控件'
    def __init__(自身,远程,会话标识):#注入远程面与会话身份
        '冷启动视图'
        自身.远程=远程#messageFeedback Remote
        自身.会话标识=会话标识#会话 id
        自身.视图=dict(初始视图)#当前视图
        自身.视图['items']={}#独立条目表
        自身.监听者=观察者集合()#订阅者
        自身.加载承诺=None#在飞列表
        自身.操作尾=期约()#变更队列尾，起点立刻解决
        自身.操作尾.解决()
        自身.已拆除=False#是否拆除

    def getSnapshot(自身):#读视图
        '返回缓存的不可变视图'
        return 自身.视图#视图

    def subscribe(自身,监听):#订阅视图替换
        '登记订阅者，返回退订'
        return 自身.监听者.订阅(监听)#退订器

    def ensure(自身):#加载一次
        '失败的加载仍可重试。返回期约，解决值是结果'
        if 自身.视图['status']=='ready':#已就绪
            已就绪=期约()#无需再加载
            已就绪.解决(成功结果)#成功
            return 已就绪
        return 自身.refresh()#刷新

    def refresh(自身):#重读权威列表
        '并发调用折叠到同一次在飞读取。返回期约，解决值是结果'
        if 自身.加载承诺 is not None:#已有在飞
            return 自身.加载承诺#共享
        自身.发布({'status':'loading','items':自身.视图['items'],'error':None})#标 loading
        任务=自身.加载()#列表读取
        自身.加载承诺=任务#共享
        def 清句柄(结算结果=None):#结算后清在飞句柄
            '结算后清在飞句柄'
            自身.加载承诺=None#清
        任务.然后(清句柄,清句柄)#成败都清
        return 任务

    def resync(自身):#串行化后再读列表
        '重连走本路径，避免盖掉在飞变更'
        def 刷新():#重读
            '列表刷新'
            return 自身.refresh()#刷新
        return 自身.变更(刷新,播种=False)#不预播种

    def rate(自身,消息标识,评价,条目=None):#创建或替换反馈
        '条目精确存储 text/category；空条目替换已存说明与类别'
        if 条目 is None:#默认空
            条目={}#空记录
        def 操作():#串行化体
            '对着已提交条目写入'
            表=自身.视图['items']#条目表
            观察=表[消息标识] if 消息标识 in 表 else None#已观察
            return 自身.提交写入(消息标识,评价,条目,观察)#put
        return 自身.变更(操作)#串行化

    def retract(自身,消息标识,评价):#撤回匹配的已提交评分
        '当前评分仍匹配才 delete，否则空操作'
        def 操作():#串行化体
            '对着已存值核对'
            表=自身.视图['items']#条目表
            观察=表[消息标识] if 消息标识 in 表 else None#已观察
            已评=观察['rating'] if 观察 is not None and 'rating' in 观察 else None#已评
            if 已评==评价:#仍匹配
                return 自身.提交删除(消息标识,观察)#收回
            已变=期约()#已变则空操作
            已变.解决(成功结果)
            return 已变
        return 自身.变更(操作)#串行化

    def dispose(自身):#拆除
        '所属 fiber 卸载时拒绝后续工作'
        自身.已拆除=True#拒绝
        自身.监听者=观察者集合()#清订阅

    def 提交写入(自身,消息标识,评价,条目,观察):#put 并调和冲突
        '按观察版本 put；条目 text→note、category 原样'
        请求={'sessionId':自身.会话标识,'messageId':消息标识,'rating':评价}#请求
        if 观察 is not None and 'version' in 观察:#有观察版本
            请求['ifVersion']=观察['version']#带上
        else:#无观察
            请求['ifVersion']=None#显式 null
        if 'text' in 条目 and 条目['text'] is not None:#有正文
            请求['note']=条目['text']#作 note
        if 'category' in 条目 and 条目['category'] is not None:#有类别
            请求['category']=条目['category']#类别
        落定=期约()#本次提交的结算点，解决值是结果
        def 已返回(载体):
            '远程返回：按载体与业务结果调和'
            try:
                if not 载体['ok']:#载体失败
                    落定.解决(载体失败(载体['error'] if 'error' in 载体 else None))#原样
                    return
                结果=载体['value']#业务结果
                if 结果['ok']:#成功
                    自身.提交(消息标识,结果['value'])#写入权威
                    落定.解决(成功结果)#成功
                    return
                错误=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
                if 'code' in 错误 and 错误['code']=='version-conflict':#冲突
                    自身.提交(消息标识,错误['current'])#调和
                落定.解决(失败(错误['code'] if 'code' in 错误 else None))#业务失败
            except BaseException as 错误:#调和失败交给调用方
                落定.拒绝(错误)
        自身.远程.put(请求).然后(已返回,落定.拒绝)#提交
        return 落定

    def 提交删除(自身,消息标识,观察):#delete 并调和冲突
        '按观察版本 delete'
        请求={'sessionId':自身.会话标识,'messageId':消息标识}#请求
        if 'version' in 观察:#有版本
            请求['ifVersion']=观察['version']#带上
        落定=期约()#本次提交的结算点，解决值是结果
        def 已返回(载体):
            '远程返回：按载体与业务结果调和'
            try:
                if not 载体['ok']:#载体失败
                    落定.解决(载体失败(载体['error'] if 'error' in 载体 else None))#原样
                    return
                结果=载体['value']#业务结果
                if 结果['ok']:#成功
                    自身.提交(消息标识,None)#删除条目
                    落定.解决(成功结果)#成功
                    return
                错误=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
                if 'code' in 错误 and 错误['code']=='version-conflict':#冲突
                    自身.提交(消息标识,错误['current'])#调和
                落定.解决(失败(错误['code'] if 'code' in 错误 else None))#业务失败
            except BaseException as 错误:#调和失败交给调用方
                落定.拒绝(错误)
        自身.远程.delete(请求).然后(已返回,落定.拒绝)#提交
        return 落定

    def 加载(自身):#拉列表并发布
        '拉取整个 sidecar。返回期约，解决值是结果'
        落定=期约()#本次加载的结算点
        def 传输失败(错误):
            '传输抛错；RPC 异常契约未定，传输层抛出类型未收窄，故不能换成更窄的类型'
            if 自身.已拆除:#拆除后
                落定.解决(成功结果)#不再发布
                return
            消息=str(错误)#文案
            自身.发布({'status':'error','items':自身.视图['items'],'error':消息})#标 error
            落定.解决({'ok':False,'error':{'code':'transport','message':消息}})#传输失败
        def 已返回(载体):
            '远程返回：按载体与业务结果发布视图'
            try:#列表
                if 自身.已拆除:#拆除后
                    落定.解决(成功结果)#不再发布
                    return
                if not 载体['ok']:#载体失败
                    错=载体['error'] if 'error' in 载体 else None#错误
                    自身.发布({'status':'error','items':自身.视图['items'],'error':错['message'] if 错 is not None and 'message' in 错 else None})#标 error
                    落定.解决(载体失败(错))#失败
                    return
                结果=载体['value']#业务结果
                if not 结果['ok']:#业务失败
                    错=结果['error'] if 'error' in 结果 else None#错误
                    码=错['code'] if 错 is not None and 'code' in 错 else None#码
                    自身.发布({'status':'error','items':自身.视图['items'],'error':描述失败(码)})#标 error
                    落定.解决(失败(码))#失败
                    return
                值=结果['value'] if 'value' in 结果 else None#值
                项列表=值['items'] if 值 is not None and 'items' in 值 and 值['items'] is not None else []#逐条
                条目表={}#重建
                for 项 in 项列表:#逐条
                    条目表[项['messageId']]=项#写入
                自身.发布({'status':'ready','items':条目表,'error':None})#就绪
                落定.解决(成功结果)#成功
            except Exception as 错误:#发布路径抛错同样按传输失败收口
                传输失败(错误)
        try:
            自身.远程.list({'sessionId':自身.会话标识}).然后(已返回,传输失败)#列
        except Exception as 错误:#远程同步段失败
            传输失败(错误)
        return 落定

    def 变更(自身,操作,播种=True):#串行化变更
        '排队操作总是对着已提交版本比较。操作返回期约；返回期约，解决值是结果'
        守卫结果=None#守卫写上，同级回调结算
        def 折成传输失败(错误):
            '传输抛错；RPC 异常契约未定，传输层抛出类型未收窄，故不能换成更窄的类型'
            守卫结果.解决({'ok':False,'error':{'code':'transport','message':str(错误)}})#折成已结算形
        def 执行操作():
            '跑操作体，失败折成传输失败'
            try:#执行
                操作().然后(守卫结果.解决,折成传输失败)#操作体
            except Exception as 错误:#操作同步段失败
                折成传输失败(错误)
        def 已确保(已载):
            '播种完成：失败则不再变更，等待期间拆除则拒绝，否则执行操作'
            if not 已载['ok']:#播种失败
                守卫结果.解决(已载)#不再变更
                return
            if 自身.已拆除:#等待期间拆除
                守卫结果.解决(已拆除结果)#拒绝
                return
            执行操作()
        def 守卫():#入队后的守卫
            '拆除检查 + 可选预播种，返回期约'
            nonlocal 守卫结果
            守卫结果=期约()#守卫的结算点
            if 自身.已拆除:#已拆除
                守卫结果.解决(已拆除结果)#拒绝
                return 守卫结果
            if 播种:#预播种
                自身.ensure().然后(已确保,守卫结果.拒绝)#确保列表
            else:
                执行操作()
            return 守卫结果
        链尾=自身.操作尾#当前队列尾
        本次=期约()#本次变更
        新尾=期约()#新队列尾
        自身.操作尾=新尾#先挂新尾
        def 守卫完成(值):
            '守卫落定：写入结果并放行'
            本次.解决(值)#写入结果
            新尾.解决()#放行
        def 守卫失败(错误):
            '守卫抛错：交给等待方并放行'
            本次.拒绝(错误)#交给等待方
            新尾.解决()#放行
        def 执行串行链(前任结果=None):#接到链尾后跑守卫
            '前一变更落定（成败相同对待，链尾必须挺过失败）后跑守卫；无论成败都放行链'
            try:#跑守卫
                守卫期约=守卫()
            except BaseException as 错误:#守卫同步段抛错
                守卫失败(错误)
                return
            守卫期约.然后(守卫完成,守卫失败)
        链尾.然后(执行串行链,执行串行链)#串行链
        return 本次

    def 提交(自身,消息标识,项):#替换或删除一条条目
        '其余条目保持同一引用'
        条目表=dict(自身.视图['items'])#拷贝
        if 项 is None:#删除
            if 消息标识 in 条目表:#有
                del 条目表[消息标识]#删
        else:#写入
            条目表[消息标识]=项#写
        自身.发布({'status':'ready','items':条目表,'error':None})#就绪

    def 发布(自身,视图):#替换视图并通知
        '可观察边界吞掉订阅者失败'
        自身.视图=视图#替换
        自身.监听者.通知()#通知

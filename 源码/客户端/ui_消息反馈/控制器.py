"""浏览器本地对象层：覆盖一个 Session 的持久消息反馈 sidecar。

对齐上游 `ui-message-feedback/src/client/controller.ts`。公开面仅中文名。
宿主拥有逐条 compare-and-set；version-conflict 应答携带权威条目。
"""
import threading#串行链
from concurrent.futures import Future as _原生Future#单次操作结果

__all__=['消息反馈控制器','消息反馈错误','描述失败','成功结果','已拆除结果']#仅中文公开名

空条目表={}#空条目
初始视图={'status':'cold','items':空条目表,'error':None}#冷启动
成功结果={'ok':True}#成功常量
已拆除结果={'ok':False,'error':{'code':'disposed','message':'feedback controller is disposed'}}#拆除形

class 消息反馈错误(Exception):
    """本包消息反馈失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

class 操作任务:#本文件内单次操作结果
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):#构造未决任务
        """构造未决任务。"""
        自身._未来=_原生Future()#底层 Future

    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身._未来.done():#尚未结算
            自身._未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身._未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._未来.set_exception(错误)#原样拒绝
            else:#非异常
                自身._未来.set_exception(消息反馈错误(str(错误)))#包装拒绝

    def 等待(自身,超时=None):#阻塞等待
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

def 已结算(值=None):#立刻结算的任务
    """立刻兑现的操作任务。"""
    任务=操作任务()#新任务
    任务.兑现(值)#立刻成功
    return 任务#已完成

def 描述失败(码):#失败码 → 可读文案
    """一条业务失败码的可读文案。"""
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
    """按码构造拒绝臂。"""
    return {'ok':False,'error':{'code':码,'message':描述失败(码)}}#失败

def 载体失败(错误):#载体失败原样
    """宿主给出的码与文案。"""
    码=错误['code'] if 错误 is not None and 'code' in 错误 else None#码
    消息=错误['message'] if 错误 is not None and 'message' in 错误 else None#文案
    return {'ok':False,'error':{'code':码,'message':消息}}#原样

class 消息反馈控制器:#每会话反馈对象层
    """一个实例支撑该 Session 内每条消息的控件。"""
    def __init__(自身,远程,会话标识):#注入远程面与会话身份
        """冷启动视图。"""
        自身.远程=远程#messageFeedback Remote
        自身.会话标识=会话标识#会话 id
        自身.视图=dict(初始视图)#当前视图
        自身.视图['items']={}#独立条目表
        自身.监听者=set()#订阅者
        自身.加载承诺=None#在飞列表
        自身.操作尾=已结算(None)#变更队列尾
        自身.已拆除=False#是否拆除

    def getSnapshot(自身):#读视图
        """返回缓存的不可变视图。"""
        return 自身.视图#视图

    def subscribe(自身,监听):#订阅视图替换
        """登记订阅者，返回退订。"""
        自身.监听者.add(监听)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(监听)#删除
        return 退订#退订器

    def ensure(自身):#加载一次
        """失败的加载仍可重试。"""
        if 自身.视图['status']=='ready':#已就绪
            return 成功结果#成功
        return 自身.refresh()#刷新

    def refresh(自身):#重读权威列表
        """并发调用折叠到同一次在飞读取。"""
        if 自身.加载承诺 is not None:#已有在飞
            return 自身.加载承诺.等待()#共享
        自身.发布({'status':'loading','items':自身.视图['items'],'error':None})#标 loading
        def 拉完():#列表读取
            """结算后清在飞句柄。"""
            try:#拉
                return 自身.加载()#加载
            finally:#清句柄
                自身.加载承诺=None#清
        任务=已结算(拉完())#记下
        自身.加载承诺=任务#共享
        return 任务.等待()#结算

    def resync(自身):#串行化后再读列表
        """重连走本路径，避免盖掉在飞变更。"""
        def 刷新():#重读
            """列表刷新。"""
            return 自身.refresh()#刷新
        return 自身.变更(刷新,播种=False)#不预播种

    def rate(自身,消息标识,评价,条目=None):#创建或替换反馈
        """条目精确存储 text/category；空条目替换已存说明与类别。"""
        if 条目 is None:#默认空
            条目={}#空记录
        def 操作():#串行化体
            """对着已提交条目写入。"""
            表=自身.视图['items']#条目表
            观察=表[消息标识] if 消息标识 in 表 else None#已观察
            return 自身.提交写入(消息标识,评价,条目,观察)#put
        return 自身.变更(操作)#串行化

    def retract(自身,消息标识,评价):#撤回匹配的已提交评分
        """当前评分仍匹配才 delete，否则空操作。"""
        def 操作():#串行化体
            """对着已存值核对。"""
            表=自身.视图['items']#条目表
            观察=表[消息标识] if 消息标识 in 表 else None#已观察
            已评=观察['rating'] if 观察 is not None and 'rating' in 观察 else None#已评
            if 已评==评价:#仍匹配
                return 自身.提交删除(消息标识,观察)#收回
            return 成功结果#已变则空操作
        return 自身.变更(操作)#串行化

    def dispose(自身):#拆除
        """所属 fiber 卸载时拒绝后续工作。"""
        自身.已拆除=True#拒绝
        自身.监听者.clear()#清订阅

    def 提交写入(自身,消息标识,评价,条目,观察):#put 并调和冲突
        """按观察版本 put；条目 text→note、category 原样。"""
        请求={'sessionId':自身.会话标识,'messageId':消息标识,'rating':评价}#请求
        if 观察 is not None and 'version' in 观察:#有观察版本
            请求['ifVersion']=观察['version']#带上
        else:#无观察
            请求['ifVersion']=None#显式 null
        if 'text' in 条目 and 条目['text'] is not None:#有正文
            请求['note']=条目['text']#作 note
        if 'category' in 条目 and 条目['category'] is not None:#有类别
            请求['category']=条目['category']#类别
        载体=自身.远程.put(请求).等待()#提交
        if not 载体['ok']:#载体失败
            return 载体失败(载体['error'] if 'error' in 载体 else None)#原样
        结果=载体['value']#业务结果
        if 结果['ok']:#成功
            自身.提交(消息标识,结果['value'])#写入权威
            return 成功结果#成功
        错误=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
        if 'code' in 错误 and 错误['code']=='version-conflict':#冲突
            自身.提交(消息标识,错误['current'])#调和
        return 失败(错误['code'] if 'code' in 错误 else None)#业务失败

    def 提交删除(自身,消息标识,观察):#delete 并调和冲突
        """按观察版本 delete。"""
        请求={'sessionId':自身.会话标识,'messageId':消息标识}#请求
        if 'version' in 观察:#有版本
            请求['ifVersion']=观察['version']#带上
        载体=自身.远程.delete(请求).等待()#提交
        if not 载体['ok']:#载体失败
            return 载体失败(载体['error'] if 'error' in 载体 else None)#原样
        结果=载体['value']#业务结果
        if 结果['ok']:#成功
            自身.提交(消息标识,None)#删除条目
            return 成功结果#成功
        错误=结果['error'] if 'error' in 结果 and 结果['error'] is not None else {}#错误
        if 'code' in 错误 and 错误['code']=='version-conflict':#冲突
            自身.提交(消息标识,错误['current'])#调和
        return 失败(错误['code'] if 'code' in 错误 else None)#业务失败

    def 加载(自身):#拉列表并发布
        """拉取整个 sidecar。"""
        try:#列表
            载体=自身.远程.list({'sessionId':自身.会话标识}).等待()#列
            if 自身.已拆除:#拆除后
                return 成功结果#不再发布
            if not 载体['ok']:#载体失败
                错=载体['error'] if 'error' in 载体 else None#错误
                自身.发布({'status':'error','items':自身.视图['items'],'error':错['message'] if 错 is not None and 'message' in 错 else None})#标 error
                return 载体失败(错)#失败
            结果=载体['value']#业务结果
            if not 结果['ok']:#业务失败
                错=结果['error'] if 'error' in 结果 else None#错误
                码=错['code'] if 错 is not None and 'code' in 错 else None#码
                自身.发布({'status':'error','items':自身.视图['items'],'error':描述失败(码)})#标 error
                return 失败(码)#失败
            值=结果['value'] if 'value' in 结果 else None#值
            项列表=值['items'] if 值 is not None and 'items' in 值 and 值['items'] is not None else []#逐条
            条目表={}#重建
            for 项 in 项列表:#逐条
                条目表[项['messageId']]=项#写入
            自身.发布({'status':'ready','items':条目表,'error':None})#就绪
            return 成功结果#成功
        except Exception as 错误:#传输抛错；RPC 异常契约未定，传输层抛出类型未收窄，故不能换成更窄的 except
            if 自身.已拆除:#拆除后
                return 成功结果#不再发布
            消息=str(错误)#文案
            自身.发布({'status':'error','items':自身.视图['items'],'error':消息})#标 error
            return {'ok':False,'error':{'code':'transport','message':消息}}#传输失败

    def 变更(自身,操作,播种=True):#串行化变更
        """排队操作总是对着已提交版本比较。"""
        def 守卫():#入队后的守卫
            """拆除检查 + 可选预播种。"""
            if 自身.已拆除:#已拆除
                return 已拆除结果#拒绝
            if 播种:#预播种
                已载=自身.ensure()#确保列表
                if not 已载['ok']:#播种失败
                    return 已载#不再变更
                if 自身.已拆除:#等待期间拆除
                    return 已拆除结果#拒绝
            try:#执行
                return 操作()#操作体
            except Exception as 错误:#传输抛错；RPC 异常契约未定，传输层抛出类型未收窄，故不能换成更窄的 except
                return {'ok':False,'error':{'code':'transport','message':str(错误)}}#折成已结算形
        链尾=自身.操作尾#当前队列尾
        本次=操作任务()#本次变更
        新尾=操作任务()#新队列尾
        自身.操作尾=新尾#先挂新尾
        def 执行串行链():#接到链尾后跑守卫
            """串行链体。"""
            try:#等前一变更
                try:#前一失败也继续
                    链尾.等待()#等链尾
                except BaseException:#吞掉
                    pass#链尾必须挺过失败
                try:#跑守卫
                    本次.兑现(守卫())#写入结果
                except BaseException as 错误:#守卫抛错
                    本次.拒绝(错误)#交给等待方
            finally:#无论成败都放行链
                新尾.兑现(None)#放行
        线=threading.Thread(target=执行串行链)#串行链
        线.daemon=True#不挡退出
        线.start()#启动
        return 本次.等待()#已结算

    def 提交(自身,消息标识,项):#替换或删除一条条目
        """其余条目保持同一引用。"""
        条目表=dict(自身.视图['items'])#拷贝
        if 项 is None:#删除
            if 消息标识 in 条目表:#有
                del 条目表[消息标识]#删
        else:#写入
            条目表[消息标识]=项#写
        自身.发布({'status':'ready','items':条目表,'error':None})#就绪

    def 发布(自身,视图):#替换视图并通知
        """可观察边界吞掉订阅者失败。"""
        自身.视图=视图#替换
        for 监听 in list(自身.监听者):#逐个
            try:#订阅者失败不得外溢
                监听()#通知
            except Exception as 错误:#抛错；订阅者异常契约未定，故不能换成更窄的 except
                print('[ui-message-feedback] subscriber threw:',错误)#记日志

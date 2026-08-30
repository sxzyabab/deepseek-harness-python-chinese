"""浏览器本地对象层：覆盖一个 Session 的持久消息反馈 sidecar。



对齐上游 `ui-message-feedback/src/client/controller.ts`。公开面仅中文名。

宿主拥有逐条 compare-and-set；version-conflict 应答携带权威条目。

"""

from ...依赖 import cordis#外部依赖胶水
import threading#串行链
from concurrent.futures import Future as _原生Future#单次操作结果
class 操作任务:#单次异步结果
    def __init__(自身):#构造未决任务
        自身._future=_原生Future()#底层 Future
    def 兑现(自身,值=None):#成功结算
        if not 自身._future.done():#尚未结算
            自身._future.set_result(值)#写入结果
        return 值#返回兑现值
    def 拒绝(自身,错误):#失败结算
        if not 自身._future.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._future.set_exception(错误)#原样拒绝
            else:#非异常
                自身._future.set_exception(Exception(错误))#包装拒绝
    def wait(自身,超时=None):#阻塞等待
        return 自身._future.result(timeout=超时)#取结果或抛错
    def 等待(自身,超时=None):#兼容外来调用
        return 自身.wait(超时)#转发

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#本库或外来 thenable

def 已兑现(值=None):#立刻兑现的操作任务
    任务=操作任务()#新任务
    任务.兑现(值)#立刻成功
    return 任务#已完成



__all__=['消息反馈控制器','描述失败','成功结果','已拆除结果']#仅中文公开名



空条目表={}#空条目

初始视图={'status':'cold','items':空条目表,'error':None}#冷启动

成功结果={'ok':True}#成功常量

已拆除结果={'ok':False,'error':{'code':'disposed','message':'feedback controller is disposed'}}#拆除形



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺省#缺席

    return getattr(对象,键,缺省)#属性



def 解开(值):#承诺则等待否则原样

    """承诺则等待，否则原样返回。"""

    if 是否thenable(值):#可等待

        return 值.等待()#等待

    return 值#同步



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

    return {'ok':False,'error':{'code':取字段(错误,'code'),'message':取字段(错误,'message')}}#原样



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

        自身.操作尾=已兑现(None)#变更队列尾

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

        if 取字段(自身.视图,'status')=='ready':#已就绪

            return 成功结果#成功

        return 自身.refresh()#刷新



    def refresh(自身):#重读权威列表

        """并发调用折叠到同一次在飞读取。"""

        if 自身.加载承诺 is not None:#已有在飞

            return 解开(自身.加载承诺)#共享

        自身.发布({'status':'loading','items':自身.视图['items'],'error':None})#标 loading

        def 拉完():#列表读取

            """结算后清在飞句柄。"""

            try:#拉

                return 自身.加载()#加载

            finally:#清句柄

                自身.加载承诺=None#清

        自身.加载承诺=已兑现(拉完())#记下

        return 解开(自身.加载承诺)#结算



    def resync(自身):#串行化后再读列表

        """重连走本路径，避免盖掉在飞变更。"""

        return 自身.变更(lambda:自身.refresh(),播种=False)#不预播种



    def rate(自身,消息标识,评价,附注=None):#创建或替换反馈

        """省略 note 保留已存；clearNote 才删。"""

        def 操作():#串行化体

            """对着已提交条目写入。"""

            观察=自身.视图['items'].get(消息标识)#已观察

            写入附注=附注 if 附注 is not None else 取字段(观察,'note')#沿用或替换

            return 自身.提交写入(消息标识,评价,写入附注,观察)#put

        return 自身.变更(操作)#串行化



    def toggle(自身,消息标识,评价):#切换或收回

        """已匹配则 delete，否则 put。"""

        def 操作():#串行化体

            """对着已存值切换。"""

            观察=自身.视图['items'].get(消息标识)#已观察

            if 取字段(观察,'rating')==评价:#已是该评价

                return 自身.提交删除(消息标识,观察)#收回

            return 自身.提交写入(消息标识,评价,取字段(观察,'note'),观察)#写入

        return 自身.变更(操作)#串行化



    def clearNote(自身,消息标识):#丢掉 note、保留评价

        """无反馈或无 note 则无需调用。"""

        def 操作():#串行化体

            """写入时省略 note。"""

            观察=自身.视图['items'].get(消息标识)#已观察

            if 观察 is None or 取字段(观察,'note') is None:#无需

                return 成功结果#成功

            return 自身.提交写入(消息标识,取字段(观察,'rating'),None,观察)#清 note

        return 自身.变更(操作)#串行化



    def clear(自身,消息标识):#去掉一条反馈

        """无已知条目则已是目标态。"""

        def 操作():#串行化体

            """按观察版本删除。"""

            观察=自身.视图['items'].get(消息标识)#已观察

            if 观察 is None:#无

                return 成功结果#成功

            return 自身.提交删除(消息标识,观察)#删除

        return 自身.变更(操作)#串行化



    def dispose(自身):#拆除

        """所属 fiber 卸载时拒绝后续工作。"""

        自身.已拆除=True#拒绝

        自身.监听者.clear()#清订阅



    def 提交写入(自身,消息标识,评价,附注,观察):#put 并调和冲突

        """按观察版本 put。"""

        请求={'sessionId':自身.会话标识,'messageId':消息标识,'rating':评价,'ifVersion':取字段(观察,'version') if 观察 is not None else None}#请求

        if 附注 is not None:#有 note

            请求['note']=附注#带上

        载体=解开(自身.远程.put(请求))#提交

        if not 取字段(载体,'ok'):#载体失败

            return 载体失败(取字段(载体,'error'))#原样

        结果=取字段(载体,'value')#业务结果

        if 取字段(结果,'ok'):#成功

            自身.提交(消息标识,取字段(结果,'value'))#写入权威

            return 成功结果#成功

        错误=取字段(结果,'error') or {}#错误

        if 取字段(错误,'code')=='version-conflict':#冲突

            自身.提交(消息标识,取字段(错误,'current'))#调和

        return 失败(取字段(错误,'code'))#业务失败



    def 提交删除(自身,消息标识,观察):#delete 并调和冲突

        """按观察版本 delete。"""

        载体=解开(自身.远程.delete({#提交

            'sessionId':自身.会话标识,#会话

            'messageId':消息标识,#消息

            'ifVersion':取字段(观察,'version'),#版本

        }))#结束

        if not 取字段(载体,'ok'):#载体失败

            return 载体失败(取字段(载体,'error'))#原样

        结果=取字段(载体,'value')#业务结果

        if 取字段(结果,'ok'):#成功

            自身.提交(消息标识,None)#删除条目

            return 成功结果#成功

        错误=取字段(结果,'error') or {}#错误

        if 取字段(错误,'code')=='version-conflict':#冲突

            自身.提交(消息标识,取字段(错误,'current'))#调和

        return 失败(取字段(错误,'code'))#业务失败



    def 加载(自身):#拉列表并发布

        """拉取整个 sidecar。"""

        try:#列表

            载体=解开(自身.远程.list({'sessionId':自身.会话标识}))#列

            if 自身.已拆除:#拆除后

                return 成功结果#不再发布

            if not 取字段(载体,'ok'):#载体失败

                自身.发布({'status':'error','items':自身.视图['items'],'error':取字段(取字段(载体,'error'),'message')})#标 error

                return 载体失败(取字段(载体,'error'))#失败

            结果=取字段(载体,'value')#业务结果

            if not 取字段(结果,'ok'):#业务失败

                自身.发布({'status':'error','items':自身.视图['items'],'error':描述失败(取字段(取字段(结果,'error'),'code'))})#标 error

                return 失败(取字段(取字段(结果,'error'),'code'))#失败

            条目表={}#重建

            for 项 in 取字段(取字段(结果,'value'),'items') or []:#逐条

                条目表[取字段(项,'messageId')]=项#写入

            自身.发布({'status':'ready','items':条目表,'error':None})#就绪

            return 成功结果#成功

        except Exception as 错误:#传输抛错

            if 自身.已拆除:#拆除后

                return 成功结果#不再发布

            消息=str(错误) if isinstance(错误,Exception) else 'message feedback list failed'#文案

            自身.发布({'status':'error','items':自身.视图['items'],'error':消息})#标 error

            return {'ok':False,'error':{'code':'transport','message':消息}}#传输失败



    def 变更(自身,操作,播种=True):#串行化变更

        """排队操作总是对着已提交版本比较。"""

        def 守卫(_前=None):#入队后的守卫

            """拆除检查 + 可选预播种。"""

            if 自身.已拆除:#已拆除

                return 已拆除结果#拒绝

            if 播种:#预播种

                已载=自身.ensure()#确保列表

                if not 取字段(已载,'ok'):#播种失败

                    return 已载#不再变更

                if 自身.已拆除:#await 期间拆除

                    return 已拆除结果#拒绝

            try:#执行

                return 操作()#操作体

            except Exception as 错误:#传输抛错

                return {'ok':False,'error':{'code':'transport','message':str(错误)}}#折成已结算形

        链尾=自身.操作尾#当前队列尾

        本次=操作任务()#本次变更

        新尾=操作任务()#新队列尾

        自身.操作尾=新尾#先挂新尾

        def 跑链():#接到链尾后跑守卫

            try:#等前一变更

                try:#前一失败也继续

                    _等待(链尾)#等链尾

                except BaseException:#吞掉

                    pass#链尾必须挺过失败

                try:#跑守卫

                    本次.兑现(守卫())#写入结果

                except BaseException as 错误:#守卫抛错

                    本次.拒绝(错误)#交给等待方

            finally:#无论成败都放行链

                新尾.兑现(None)#放行

        threading.Thread(target=跑链,daemon=True).start()#串行链

        return _等待(本次)#已结算



    def 提交(自身,消息标识,项):#替换或删除一条条目

        """其余条目保持同一引用。"""

        条目表=dict(自身.视图['items'])#拷贝

        if 项 is None:#删除

            条目表.pop(消息标识,None)#删

        else:#写入

            条目表[消息标识]=项#写

        自身.发布({'status':'ready','items':条目表,'error':None})#就绪



    def 发布(自身,视图):#替换视图并通知

        """可观察边界吞掉订阅者失败。"""

        自身.视图=视图#替换

        for 监听 in list(自身.监听者):#逐个

            try:#订阅者失败不得外溢

                监听()#通知

            except Exception as 错误:#抛错

                print('[ui-message-feedback] subscriber threw:',错误)#记日志



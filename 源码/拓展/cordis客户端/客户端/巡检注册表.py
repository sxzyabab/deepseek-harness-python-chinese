from ....客户端.模块.客户端.通告 import 取握手窗口
from ..异常 import 错误#巡检传输失败


__all__=['客户端巡检注册表']


class 客户端巡检注册表:
    '客户端巡检提供方、清单发布和进行中的查询'
    def __init__(自身,宿主):
        '宿主负责同步清单和交回查询结果'
        自身.宿主=宿主#sync / resolve
        自身.提供方={}#标识到登记
        自身.进行中={}#请求标识到 AbortController
        自身._已排队=False#同栈多次发布合并
        自身._同步链=None#上一轮同步

    def 登记(自身,登记):
        '登记一个提供方并发布整份清单。返回可重复调用的拆除器'
        清单=登记['manifest']#可序列化清单
        if 清单['id'].strip()=='':#空标识
            raise 错误('Client Cordis inspect provider id must not be empty')
        if 清单['id'] in 自身.提供方:#重复
            raise 错误('Client Cordis inspect provider "'+清单['id']+'" is already registered')
        名字=set()#方法名
        for 方法 in 清单['methods']:#逐个方法
            if 方法['name'] in 名字:#重复方法
                raise 错误('Client Cordis inspect provider "'+清单['id']+'" repeats method "'+方法['name']+'"')
            名字.add(方法['name'])#记下
        自身.提供方[清单['id']]=登记#收下
        自身.发布()#发布整份
        已拆={'值':False}#拆除只生效一次
        def 拆除():
            '再拆一次是空操作。仍是本次登记才删'
            if 已拆['值']:#已经拆过
                return
            已拆['值']=True#只生效一次
            if 自身.提供方.get(清单['id']) is 登记:#还是这一份
                del 自身.提供方[清单['id']]#摘掉
                自身.发布()#再发布
        return 拆除

    def 发布(自身):
        '发布当前整份清单。同一次调用栈里的多次发布合并成一次'
        if 自身._已排队:#已经排了微任务
            return
        自身._已排队=True#合并
        def 刷():
            '先清排队旗，再把这一份清单送进同步链'
            自身._已排队=False#同步途中可以再排队
            清单=[项['manifest'] for 项 in 自身.提供方.values()]#整份
            先前=自身._同步链#上一轮
            def 本次():
                '等上一轮结束再同步。上一轮失败不堵住这一轮'
                if 先前 is not None:#有上一轮
                    try:#上一轮的失败吞掉
                        先前()#跑完
                    except Exception:#不堵后续
                        pass
                try:#这一轮
                    自身.宿主['sync'](清单)#推清单
                except Exception as 原因:#同步失败只记日志
                    取握手窗口().console.error(
                        '[cordis-client-runner] syncing inspect providers failed:',原因,
                    )
            自身._同步链=本次#链尾
            本次()#同步执行
        取握手窗口().queueMicrotask(刷)#排到这一轮之后

    def 查询(自身,请求):
        '执行并回答。中止之后不再 resolve'
        if 请求['requestId'] in 自身.进行中:#已经在处理
            return
        控制器=取握手窗口().AbortController()#这次查询的中止
        自身.进行中[请求['requestId']]=控制器#记下
        try:#执行
            提供方=自身.提供方.get(请求['provider'])#按标识
            if 提供方 is None:#没有这个提供方
                决议={'ok':False,'reason':'provider-missing','message':'Client inspect provider "'+请求['provider']+'" is unavailable'}
            elif not any(方法['name']==请求['method'] for 方法 in 提供方['manifest']['methods']):#没有这个方法
                决议={'ok':False,'reason':'method-missing','message':'Client inspect provider "'+请求['provider']+'" has no method "'+请求['method']+'"'}
            else:#执行查询
                数据=提供方['query'](请求['method'],请求.get('input'),{#上下文
                    'signal':控制器.signal,#中止信号
                    'sessionId':请求['agentId'],#发起会话
                })
                if 控制器.signal.aborted:#执行期间被中止
                    决议={'ok':False,'reason':'cancelled','message':'Client inspect query was cancelled'}
                else:#成功
                    决议={'ok':True,'data':数据}
        except Exception as 原因:#提供方失败
            if 控制器.signal.aborted:#失败时已经中止
                决议={'ok':False,'reason':'cancelled','message':'Client inspect query was cancelled'}
            else:#提供方自己的错误
                消息=原因.message if isinstance(getattr(原因,'message',None),str) else str(原因)#正文
                决议={'ok':False,'reason':'provider-error','message':消息}
        finally:#无论成败都离开进行中
            自身.进行中.pop(请求['requestId'],None)#摘掉
        if 控制器.signal.aborted:#中止后不再回答
            return
        自身.宿主['resolve'](请求['agentId'],请求['requestId'],决议)#交回宿主

    def 关闭(自身,请求标识):
        '中止进行中的查询'
        控制器=自身.进行中.get(请求标识)#进行中的
        if 控制器 is not None:#还在
            控制器.abort()#中止
        自身.进行中.pop(请求标识,None)#摘掉

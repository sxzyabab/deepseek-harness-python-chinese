import threading#取消事件用 Event

__all__=['客户端巡检注册表','提供客户端巡检','说明']

说明='sync/resolve 需 remote.dynamicCordisRunner；取消/同栈合并发布/串行链本树可跑。'#说明

class 客户端巡检注册表:#ClientCordisInspectRegistry
    """提供方表、进行中查询（可中止）、清单发布与同步串行链。"""
    def __init__(自身,宿主=None):#构造
        """宿主接缝：sync / resolve。"""
        自身.宿主=宿主 or {}#接缝
        自身.提供方={}#id → 登记
        自身.进行中={}#requestId → Event
        自身._待发布=False#排队（publishQueued）
        自身._同步链=None#串行 sync 尾（Promise 链等价）

    def register(自身,登记):#登记
        """幂等拆除器。"""
        清单=登记.get('manifest') if isinstance(登记,dict) else getattr(登记,'manifest',None)#清单
        标识=清单.get('id') if isinstance(清单,dict) else None#id
        if not isinstance(标识,str) or 标识.strip()=='':#空
            raise Exception('客户端 Cordis 巡检提供方 id 不能为空')#抛
        if 标识 in 自身.提供方:#重复
            raise Exception(f'客户端 Cordis 巡检提供方 "{标识}" 已登记')
        名集=set()#方法名
        for 方法 in (清单.get('methods') or []):#每条
            名=方法.get('name')#名
            if 名 in 名集:#重复
                raise Exception(f'客户端 Cordis 巡检提供方 "{标识}" 重复方法 "{名}"')
            名集.add(名)#收入
        自身.提供方[标识]=登记#写入
        自身.publish()#发布
        已拆=False#标志
        def 拆除():#拆除器
            """幂等。"""
            nonlocal 已拆#标志
            if 已拆:#已
                return#停
            已拆=True#标
            if 自身.提供方.get(标识) is 登记:#仍是本条
                自身.提供方.pop(标识,None)#拿掉
                自身.publish()#再发
        return 拆除#器

    def publish(自身):#发布清单
        """同栈多次 publish 合并；开刷先清旗，sync 途中可再排队。"""
        if 自身._待发布:#已排队
            return#停
        自身._待发布=True#标
        自身._刷发布()#同步拍（无 Timer）

    def _刷发布(自身):#实际推清单
        """开刷先清排队旗，再进同步链。"""
        自身._待发布=False#先放行
        清单列表=[]#表
        for 登 in 自身.提供方.values():#每个
            清单=登.get('manifest') if isinstance(登,dict) else getattr(登,'manifest',None)#清单
            if 清单 is not None:#有
                清单列表.append(清单)#加
        上一=自身._同步链#上一尾
        态={'done':False}#本环
        def 链():#串行一环
            """上一成败吞掉；本 sync 失败只记不堵。"""
            if 态['done']:#已跑
                return#幂等
            if 上一 is not None:#等上一
                try:#成败都过
                    上一()#落定
                except Exception:#吞
                    pass#不堵
            同步=自身.宿主.get('sync') if isinstance(自身.宿主,dict) else None#sync
            try:#推
                if callable(同步):#有
                    同步(清单列表)#推给宿主
            except Exception as 错误:#失败只记
                print('[cordis-client-runner] 同步巡检提供方失败:',错误)
            态['done']=True#落定
        自身._同步链=链#新尾
        链()#启动

    def query(自身,请求):#处理查询
        """执行并回答；close 中止则不再 resolve。"""
        标识=请求.get('requestId')#查询 id
        if 标识 in 自身.进行中:#已在处理
            return None#空
        控=threading.Event()#取消事件（AbortController 等价）
        自身.进行中[标识]=控#记下
        决议=None#决议
        try:#跑
            登=自身.提供方.get(请求.get('provider'))#提供方
            if 登 is None:#缺失
                决议={'ok':False,'reason':'provider-missing','message':f'客户端巡检提供方 "{请求.get("provider")}" 不可用'}
            else:#有
                清单=登.get('manifest') if isinstance(登,dict) else getattr(登,'manifest',{})#清单
                方法表=清单.get('methods') or []#方法
                if not any(方法项.get('name')==请求.get('method') for 方法项 in 方法表):#未声明
                    决议={'ok':False,'reason':'method-missing','message':f'客户端巡检提供方 "{请求.get("provider")}" 没有方法 "{请求.get("method")}"'}
                else:#有方法
                    查询=登.get('query') if isinstance(登,dict) else getattr(登,'query',None)#查询
                    数据=查询(请求.get('method'),请求.get('input'),{#上下文
                        'signal':控,#取消事件
                        'sessionId':请求.get('agentId'),#会话
                    }) if callable(查询) else None#执行
                    if 控.is_set():#途中取消
                        决议={'ok':False,'reason':'cancelled','message':'客户端巡检查询已取消'}
                    else:#成功
                        决议={'ok':True,'data':数据}#带数据
        except Exception as 错误:#提供方抛
            if 控.is_set():#取消优先
                决议={'ok':False,'reason':'cancelled','message':'客户端巡检查询已取消'}
            else:#提供方错误
                决议={'ok':False,'reason':'provider-error','message':str(错误)}#错
        finally:#清进行中
            自身.进行中.pop(标识,None)#清
        if 控.is_set():#已取消则不再回答
            return None#停
        落定=自身.宿主.get('解析') if isinstance(自身.宿主,dict) else None#解析
        if callable(落定) and 决议 is not None:#有
            落定(请求.get('agentId'),标识,决议)#推
        return 决议#决议

    def close(自身,请求标识):#关闭查询
        """中止进行中的工作。"""
        控=自身.进行中.get(请求标识)#进行中
        if 控 is not None:#有
            控.set()#中止
        自身.进行中.pop(请求标识,None)#从表拿掉

def 提供客户端巡检(上下文,注册表):#挂服务
    """ctx.提供服务('cordisInspect', registry)。"""
    上下文.提供服务('cordisInspect',注册表)#挂
    return 注册表#表

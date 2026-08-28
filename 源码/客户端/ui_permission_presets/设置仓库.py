"""权限默认设置控制器。



对齐上游 `ui-permission-presets/src/client/settings-store.ts`。公开面仅中文名。

写入只对准 defaultPreset，并带上描述符修订号。

"""

from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定

from .展示 import 显示权限预设#显示名



__all__=['权限设置命名空间','权限默认于','权限预设设置控制器','已加载则刷新权限']#仅中文公开名



权限设置命名空间='permission'#设置 ns 字面量



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



def 权限默认于(视图):#从描述符抽出当前默认

    """读取宿主 defaultPreset 模式编码的动态预设枚举。"""

    值袋=取字段(视图,'value') or {}#当前值

    值=取字段(值袋,'defaultPreset')#defaultPreset

    if not isinstance(值,str):#不是字符串

        raise Exception('permission settings has no defaultPreset value')#拒绝

    try:#复水模式

        from 客户端.schema_form import 再水合模式,路径上节点#schema-form

        节点=路径上节点(再水合模式(取字段(视图,'schema')),['defaultPreset'])#取节点

    except Exception:#导入或解析失败

        节点=None#无节点

    if 节点 is None:#无字段

        raise Exception('permission settings schema has no defaultPreset field')#拒绝

    原始=取字段(节点,'anyOf') or 取字段(节点,'oneOf') or [节点]#联合或单节点

    选项=[]#选项

    for 候选 in 原始:#逐成员

        常量值=取字段(候选,'const')#JSON Schema 常量

        if not isinstance(常量值,str):#非字符串常量

            continue#丢掉

        描述=取字段(候选,'description')#可选描述

        if isinstance(描述,str) and 描述:#有描述

            标签=显示权限预设(常量值,描述)#描述作显示名

        else:#无

            标签=显示权限预设(常量值,常量值)#键本身

        选项.append({'id':常量值,'label':标签})#一条选项

    if not 选项 or not any(项['id']==值 for 项 in 选项):#空或不含当前

        raise Exception('permission settings schema does not advertise its current preset')#拒绝

    return {'currentValue':值,'options':选项}#当前值与选项



class 快照仓库:#简易快照仓库

    """行快照 + 订阅。"""

    def __init__(自身,初值):#播种

        """记下初值。"""

        自身.状态=dict(初值)#状态

        自身.监听者=set()#订阅者



    def getSnapshot(自身):#读快照

        """返回当前状态。"""

        return 自身.状态#状态



    def subscribe(自身,回调):#订阅

        """登记变更回调。"""

        自身.监听者.add(回调)#加入

        def 退订():#退订

            """取消。"""

            自身.监听者.discard(回调)#删除

        return 退订#退订器



    def update(自身,变换):#就地变换并通知

        """调用变换(state)。"""

        变换(自身.状态)#变换

        for 回调 in list(自身.监听者):#通知

            回调()#触发



class 权限预设设置控制器:#权限预设设置控制器

    """把设置读取、写入与推送失效拼在一起。"""

    def __init__(自身,接口):#注入 settings API

        """空闲快照。"""

        自身.接口=接口#settings 面

        自身.store=快照仓库({#行快照

            'status':'idle',#尚未读取

            'error':None,#无错误

            'writable':False,#尚未询问可写性

            'currentValue':'',#尚无当前值

            'options':[],#尚无选项

            'revision':0,#尚无修订

        })#仓库结束

        自身.世代=0#在飞请求世代

        自身.视图=None#最近一次权限命名空间视图



    def load(自身):#拉权限描述符

        """最新请求胜出。"""

        自身.世代+=1#抬世代

        世代=自身.世代#本请求

        自身.store.update(lambda 态:(态.__setitem__('status','loading'),态.__setitem__('error',None)))#标 loading

        try:#describe

            应答=解开(自身.接口.settings.describe({}))#描述

            if 世代!=自身.世代:#过期

                return#丢弃

            结果=取字段(应答,'result')#业务结果

            if not 取字段(结果,'ok'):#业务失败

                raise Exception(取字段(取字段(结果,'error'),'message'))#抛

            视图=None#权限命名空间

            for 项 in 取字段(取字段(结果,'value'),'namespaces') or []:#找

                if 取字段(项,'ns')==权限设置命名空间:#命中

                    视图=项#记下

                    break#找到

            if 视图 is None:#不在描述符

                自身.视图=None#丢掉

                def 写成不可用(态):#不可用

                    """清空。"""

                    态['status']='unavailable'#不可用

                    态['writable']=False#不可写

                    态['currentValue']=''#清空

                    态['options']=[]#清空

                自身.store.update(写成不可用)#写入

                return#结束

            自身.接受(视图,取字段(取字段(结果,'value'),'writable'))#写入快照

        except Exception as 错误:#描述失败

            if 世代!=自身.世代:#过期

                return#丢弃

            自身.失败(错误)#记下失败



    def select(自身,预设):#把一个预设写成后续会话默认

        """无视图或只读则忽略。"""

        视图=自身.视图#缓存视图

        状态=自身.store.getSnapshot()#当前行

        if 视图 is None or not 取字段(状态,'writable'):#不可写

            return#忽略

        自身.世代+=1#抬世代

        世代=自身.世代#本请求

        def 标保存(态):#saving

            """标 saving。"""

            态['status']='saving'#保存中

            态['error']=None#清错误

        自身.store.update(标保存)#写入

        try:#mutate

            应答=解开(自身.接口.settings.mutate({#变更

                'ns':权限设置命名空间,#命名空间

                'ops':[{'op':'set','path':['defaultPreset'],'value':预设}],#只写 defaultPreset

                'expectedRevision':取字段(视图,'revision'),#乐观并发

            }))#结束

            if 世代!=自身.世代:#过期

                return#丢弃

            结果=取字段(应答,'result')#业务结果

            if not 取字段(结果,'ok'):#业务失败

                raise Exception(取字段(取字段(结果,'error'),'message'))#抛

            自身.接受(取字段(结果,'value'),True)#已落地，可写

        except Exception as 错误:#变更失败

            if 世代!=自身.世代:#过期

                return#丢弃

            自身.失败(错误)#记下失败



    def dispose(自身):#拆除

        """作废在飞应答。"""

        自身.世代+=1#抬世代

        自身.视图=None#丢掉视图



    def 接受(自身,视图,可写):#把描述符写入快照

        """抽出当前值与选项。"""

        解析=权限默认于(视图)#解析

        自身.视图=视图#缓存

        def 写就绪(态):#ready

            """写成就绪。"""

            态['status']='ready'#就绪

            态['error']=None#清错误

            态['writable']=可写#可写性

            态['currentValue']=解析['currentValue']#当前默认

            态['options']=解析['options']#选项

            态['revision']=取字段(视图,'revision')#修订

        自身.store.update(写就绪)#写入



    def 失败(自身,错误):#把拒绝写入错误快照

        """Error 取其 message。"""

        def 写错误(态):#error

            """写成错误。"""

            态['status']='error'#错误

            态['error']=str(错误) if isinstance(错误,Exception) else str(错误)#文案

        自身.store.update(写错误)#写入



def 已加载则刷新权限(控制器):#行已打开过才重拉

    """idle 则跳过。"""

    if 取字段(控制器.store.getSnapshot(),'status')=='idle':#尚未打开

        return#跳过

    控制器.load()#刷新



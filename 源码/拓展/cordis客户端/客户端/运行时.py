from ....客户端.模块.客户端.通告 import 取握手窗口
from pywebbridge.基础 import undefined as 未定义#页面上的未定义
from ..异常 import 错误#加载失败
from .求值器 import 动态样式,求值客户端半,客户端重定向#求值与样式
from .门面规则 import 动态上下文门面#插件看到的上下文


__all__=['动态包运行器','错误字段','快照源','模块标识']


class 快照源:
    'getSnapshot 与 subscribe。两次变更之间是同一份'
    def __init__(自身,读取,订阅):
        '记下读和订阅'
        自身._读取=读取#读快照
        自身._订阅=订阅#订阅
    def getSnapshot(自身):
        '当前快照'
        return 自身._读取()
    def subscribe(自身,函数):
        '订阅变更，返回退订'
        return 自身._订阅(函数)
    def __getitem__(自身,键):
        '按字典读取，和属性是同一份'
        if 键=='getSnapshot':#读
            return 自身.getSnapshot
        if 键=='subscribe':#订
            return 自身.subscribe
        raise KeyError(键)


def 模块标识(插件标识):
    '模块表和加载器条目用的标识'
    return 'dyn/'+插件标识


def 错误字段(异常):
    '保住 message 和原来的 stack，不编造栈'
    if 异常 is None or isinstance(异常,(str,int,float,bool)):#标量
        return {'message':str(异常)}
    消息=getattr(异常,'message',None)#Error.message
    if not isinstance(消息,str):#没有字符串消息
        if isinstance(异常,BaseException):#异常
            消息=str(异常)#正文
        else:#其它对象
            消息=str(异常)#转成字符串
    结果={'message':消息}#消息
    栈=getattr(异常,'stack',None)#原栈
    if isinstance(栈,str):#有栈
        结果['stack']=栈#带上
    return 结果


def 可索引(组件):
    '对象和函数能当认领键，标量不行'
    if 组件 is None or isinstance(组件,(str,int,float,bool)):#标量
        return False
    return True


def 成功结果(记录):
    '本页已经活着的成功结果。在等服务也算成功'
    结果={'ok':True,'pluginRunId':记录['包']['pluginRunId']}#成功
    if len(记录['等待'])>0:#还在等
        结果['waitingFor']=记录['等待']#带上
    return 结果


class 动态包运行器:
    '把浏览器半求值、套门面、放进模块表并建成加载器条目'
    def __init__(自身,环境):
        '订上全页入口崩溃。只报告本运行器认领过的组件'
        自身.环境=环境#加载器、模块、槽和两条宿主动词
        自身.现场={}#插件标识到记账
        自身.队列尾={}#插件标识到还没跑完的操作
        自身._忙={}#正在跑的插件
        自身._待办={}#重入时排到当前操作后面
        自身.下一优先级=0#后登记更前
        自身.所有者={}#组件身份到拥有方
        自身.失败={}#插件标识到最近渲染失败
        自身._听=set()#订阅者
        自身._快照缓存=None#两次通知之间不变
        自身._失败缓存=None#两次通知之间不变
        def 入口崩溃(槽,入口,异常,信息):
            '只报告认领过的组件'
            组件=入口.get('component') if isinstance(入口,dict) else getattr(入口,'component',None)#组件
            拥有=自身.所有者.get(id(组件)) if 可索引(组件) else None#认领记录
            if 拥有 is None:#不是我们的
                return
            字段=错误字段(异常)#消息和栈
            消息=字段['message']#崩溃正文
            重定向=None#被扣全局的教学
            for 名字,文本 in 客户端重定向.items():#逐条重定向
                if 名字 in 消息 and 文本 not in 消息:#点到了名字还没带教学
                    重定向=文本#用这一条
                    break
            if str(槽).startswith('factory:'):#工厂
                主体='your component in Factory "'+str(槽)[len('factory:'):]+'"'#工厂名
            else:#槽
                主体='your entry in slot "'+str(槽)+'"'#槽名
            失败消息=主体+' crashed while React rendered it: '+消息#教学
            if 重定向 is not None:#补上重定向
                失败消息=失败消息+'\n'+重定向#同一条教学
            失败={'slot':槽,'message':失败消息,'abdicated':信息['abdicated'] if isinstance(信息,dict) else bool(getattr(信息,'abdicated',False))}#失败
            if 'stack' in 字段:#有栈
                失败['stack']=字段['stack']#带上
            自身.环境['reportRenderFailure'](拥有['agentId'],拥有['pluginId'],拥有['pluginRunId'],失败)#告诉宿主
            自身.失败[拥有['pluginId']]=失败#本页这一份
            自身.通知()#通知
        自身._退订=环境['slots'].onEntryError(入口崩溃)#全页崩溃缝
        def 读失败():
            '渲染失败图'
            if 自身._失败缓存 is None:#还没拍
                自身._失败缓存=dict(自身.失败)#拍一份
            return 自身._失败缓存
        自身.renderFailures=快照源(读失败,自身.订阅)#本页渲染失败

    def 订阅(自身,函数):
        '订阅现场变化，返回退订'
        自身._听.add(函数)#记下
        def 退订():
            '拿掉这个订阅'
            自身._听.discard(函数)#摘掉
        return 退订

    def 取快照(自身):
        '当前加载着的行。两次通知之间是同一份'
        if 自身._快照缓存 is None:#还没拍
            行列表=[]#投影
            for 记录 in 自身.现场.values():#逐个现场
                槽名=[]#去重后的槽
                for 账 in 记录['账本']:#逐行
                    if 账['slot'] not in 槽名:#还没有
                        槽名.append(账['slot'])#记下
                行列表.append({#一行
                    'pluginId':记录['包']['pluginId'],
                    'packageId':记录['包']['packageId'],
                    'pluginRunId':记录['包']['pluginRunId'],
                    'name':记录['包']['name'],
                    'slots':槽名,
                    'styleCount':记录['样式'].数量,
                })
            自身._快照缓存=行列表#拍下
        return 自身._快照缓存

    def 是否已加载(自身,插件标识):
        '本页有没有这份浏览器半'
        return 插件标识 in 自身.现场

    def 加载(自身,半边):
        '按插件串行加载。已经是这一次激活则直接回答'
        def 操作():
            '同一激活空操作；另一激活先拆再挂'
            当前=自身.现场.get(半边['pluginId'])#已有
            if 当前 is not None:#已经在
                if 当前['包']['pluginRunId']==半边['pluginRunId']:#就是这一次
                    return 成功结果(当前)
                自身.拆掉(当前['包']['pluginId'],当前['条目'],当前['样式'])#先拆旧的
            结果=自身.挂载(半边)#挂上
            自身.通知()#通知
            return 结果
        return 自身.入队(半边['pluginId'],操作)

    def 收回(自身,插件标识,运行标识):
        '撤回。运行标识对不上则留下更新的那次'
        def 操作():
            '匹配才拆'
            当前=自身.现场.get(插件标识)#已有
            if 当前 is None or 当前['包']['pluginRunId']!=运行标识:#不是这一次
                return None
            自身.拆掉(插件标识,当前['条目'],当前['样式'])#拆掉
            自身.通知()#通知
            return None
        return 自身.入队(插件标识,操作)

    def 拆除全部(自身):
        '插件拆除路径。卸掉监听和全部现场'
        自身._退订()#不再听崩溃
        for 当前 in list(自身.现场.values()):#逐个
            自身.拆掉(当前['包']['pluginId'],当前['条目'],当前['样式'])#拆掉
        自身.通知()#通知

    def 通知(自身):
        '清缓存并通知订阅者'
        自身._快照缓存=None#下次重拍
        自身._失败缓存=None#下次重拍
        for 函数 in list(自身._听):#复制后再通知
            函数()#通知

    def 入队(自身,标识,操作):
        '接在该包当前操作后面。重入不等待，排到这次返回之后'
        if 自身._忙.get(标识):#正在跑
            自身._待办.setdefault(标识,[]).append(操作)#排后面
            return None
        自身._忙[标识]=True#占住
        try:#跑这一次
            return 操作()#结果
        finally:#无论成败都放后续
            自身._忙[标识]=False#放开
            待办=自身._待办.pop(标识,[])#取出
            for 后续 in 待办:#逐个
                try:#一个失败不堵后面
                    自身.入队(标识,后续)#再入队
                except Exception:#吞掉
                    pass

    def 挂载(自身,半边):
        '求值、登记工厂、创建条目。失败时拆掉已经挂上的部分'
        样式=动态样式(半边['pluginId'])#样式记账
        账本=[]#槽登记
        try:#求值
            def 调用(方法,参数):
                'host.call 进这一包的宿主半'
                return 自身.环境['invoke'](半边['pluginId'],半边['pluginRunId'],方法,参数)
            def 记下(消息):
                '插件自己的 console.error，没有线路'
                取握手窗口().console.error(
                    '[cordis-client-runner] '+半边['pluginId']+' logged an error:',消息,
                )
            插件=求值客户端半(半边['pluginId'],半边['code'],{'invoke':调用,'noteError':记下},样式)#求值
        except Exception as 原因:#求值失败
            样式.拆除全部()#拆样式
            结果={'ok':False,'cause':'evaluate','error':原因}#失败
            结果.update(错误字段(原因))#消息和栈
            return 结果
        包={#包行
            'pluginId':半边['pluginId'],
            'packageId':半边['packageId'],
            'pluginRunId':半边['pluginRunId'],
            'name':半边['name'],
        }
        表面=自身.门面表面(包,半边['agentId'],插件,账本)#套门面
        模块名=模块标识(半边['pluginId'])#dyn/标识
        自身.环境['modules'].invalidate(模块名)#先失效，重载才合法
        窗口=取握手窗口()#当前页
        汇=窗口['__ModuleLoader__']#模块登记门面
        if 汇 is None or 汇 is 未定义:#没有网页壳
            raise 错误('cordis-client-runner: window.__ModuleLoader__ is missing (booted outside the web shell?)')
        def 工厂(_要求):
            '模块导出就是套好门面的插件'
            return 表面
        汇.load({'id':模块名,'factory':工厂})#登记工厂
        条目=自身.环境['loader'].创建({'name':模块名})#创建条目
        配置=自身.环境['loader'].解析(条目)#条目
        纤程=配置.纤程#导入后的纤程
        if 纤程 is None:#导入失败
            自身.拆掉(半边['pluginId'],条目,样式)#拆掉
            return {'ok':False,'cause':'module-import','message':'module import failed (see the browser console)'}
        try:#等激活
            纤程.等待()#启动失败会抛
        except Exception as 原因:#激活失败
            自身.拆掉(半边['pluginId'],条目,样式)#拆掉
            结果={'ok':False,'cause':'activate','error':原因}#失败
            结果.update(错误字段(原因))#消息和栈
            return 结果
        等待=[]#声明了但本页还没有的服务
        for 名字 in 纤程.依赖表:#逐个声明
            if 自身.环境['ctx'].获取服务(名字,False) is None:#还没有
                等待.append(名字)#记下
        记录={'包':包,'条目':条目,'样式':样式,'账本':账本,'等待':等待}#现场
        自身.现场[半边['pluginId']]=记录#现在才算活着
        自身.失败.pop(半边['pluginId'],None)#新的加载清掉旧崩溃
        return 成功结果(记录)

    def 门面表面(自身,包,会话标识,插件,账本):
        'apply 看到门面。函数形态没有 inject，对象形态保留自己的声明'
        def 认领(组件):
            '用组件身份记住拥有方'
            if 可索引(组件):#能当键
                自身.所有者[id(组件)]={'pluginId':包['pluginId'],'pluginRunId':包['pluginRunId'],'agentId':会话标识,'组件':组件}
        def 分配优先级():
            '后登记的数字更小，排序更前'
            自身.下一优先级-=1#先减
            return 自身.下一优先级
        def 报告失败(异常):
            '激活后的门面拒绝交给宿主'
            自身.环境['reportGuardFailure'](会话标识,包['pluginId'],包['pluginRunId'],错误字段(异常))
        def 套好的应用(上下文,配置=None):
            '先套门面再进插件。函数形态和对象形态都走 apply，页面里再区分'
            门面=动态上下文门面(上下文,{#环境
                '包':包,
                '账本':账本,
                '认领':认领,
                '分配优先级':分配优先级,
                '报告失败':报告失败,
            })
            return 插件.apply(门面,配置)
        注入=list(getattr(插件,'inject',[]) or [])#对象形态的声明
        class 表面:
            '模块表导出的插件对象。加载器认 apply、inject 和 name'
        导出=表面()#实例
        导出.name=模块标识(包['pluginId'])#条目名
        导出.inject=注入#声明
        导出.apply=套好的应用#套门面后的入口
        return 导出

    def 拆掉(自身,插件标识,条目,样式):
        '卸条目、失效工厂、拆样式。加载失败时也可以还没有现场'
        自身.现场.pop(插件标识,None)#离开现场
        自身.失败.pop(插件标识,None)#崩溃行不再显示
        配置=自身.环境['loader'].解析(条目)#条目
        纤程=配置.纤程#纤程
        if 纤程 is not None and callable(getattr(纤程,'拆除',None)):#有拆除器
            纤程.拆除()#卸纤程
        自身.环境['loader'].移除(条目)#摘条目
        自身.环境['modules'].invalidate(模块标识(插件标识))#下次还能登记
        样式.拆除全部()#拆样式

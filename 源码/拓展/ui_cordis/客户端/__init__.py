from . import (
    文案,
    卡片模型,
    状态,
    事件,
    槽位,
    动态端口,
    准备行,
    定义行,
    运行行,
    动作行,
    面板,
)

__all__=[
    '文案','卡片模型','状态','事件','槽位','动态端口','准备行','定义行','运行行','动作行','面板',
    '依赖','应用',
]

依赖=['slots','locale','remote','remote.dynamicCordisRunner','dynamicCordisRunner']#所需服务

def 应用(上下文,配置=None):
    '登记文案、清单、工具行和侧栏面板'
    def 挂词典():
        '登记中英文案。界面显示直接写中文，不走翻译函数'
        return 上下文.locale.register(文案.命名空间,{'zh':文案.中文,'en':文案.英文})#拆除时卸掉
    上下文.副作用(挂词典,'ui-cordis: dictionaries')#词典
    远端=上下文.remote.dynamicCordisRunner#宿主运行器

    def 停止(会话标识,插件标识):
        '经远端停止。没在跑也算成功'
        答=远端.stopFromPanel(会话标识,插件标识)#同步结果
        if not 答['ok']:#载体失败
            错误=答['error']#失败
            if isinstance(错误,dict):#字典
                说明=str(错误.get('code'))+': '+str(错误.get('message'))#码和消息
            else:#远程错误对象
                说明=str(getattr(错误,'code',''))+': '+str(getattr(错误,'message',错误))#码和消息
            return {'ok':False,'message':说明}#失败
        值=答['value']#业务结果
        if 值['ok'] or 值.get('reason')=='not-running':#成功或本来没跑
            return {'ok':True}#成功
        return {'ok':False,'message':值['message']}#失败消息

    def 移除(会话标识,插件标识):
        '经远端移除插件和全部包'
        答=远端.undefineFromPanel(会话标识,插件标识)#同步结果
        if not 答['ok']:#载体失败
            错误=答['error']#失败
            if isinstance(错误,dict):#字典
                说明=str(错误.get('code'))+': '+str(错误.get('message'))#码和消息
            else:#远程错误对象
                说明=str(getattr(错误,'code',''))+': '+str(getattr(错误,'message',错误))#码和消息
            return {'ok':False,'message':说明}#失败
        值=答['value']#业务结果
        if 值['ok']:#成功
            return {'ok':True}#成功
        return {'ok':False,'message':值['message']}#失败消息

    def 拉清单():
        '读取整帧插件清单。载体失败就抛出'
        答=远端.inventory()#同步结果
        if not 答['ok']:#载体失败
            错误=答['error']#失败
            if isinstance(错误,dict):#字典
                说明=str(错误.get('code'))+': '+str(错误.get('message'))#码和消息
            else:#远程错误对象
                说明=str(getattr(错误,'code',''))+': '+str(getattr(错误,'message',错误))#码和消息
            raise Exception(说明)#码和消息
        return 答['value']#行

    def 清单读失败(错误):
        '把读取失败打出来'
        print('[ui-cordis] reading the Cordis inventory failed:',错误)#上游原句

    听众=set()#清单订阅
    快照盒={'当前':{'rows':[],'removed':set(),'read':False}}#当前快照
    飞行={'中':None}#正在读时不再另起一次
    世代={'号':0}#重置后作废还没返回的那一次

    def 取快照():
        '当前清单快照'
        return 快照盒['当前']#快照

    def 订阅(函数):
        '快照变了就调用。返回退订'
        听众.add(函数)#加上
        def 退订():
            '不再通知'
            听众.discard(函数)#拿掉
        return 退订#拆除器

    def 发布(下一):
        '换上新快照并通知'
        快照盒['当前']=下一#换引用
        for 监听 in list(听众):#拷一份，监听里可以退订
            监听()#通知

    def 刷新():
        '没有在读才再读。重置过的那一次不发布'
        if 飞行['中'] is not None:#已经在读
            return#不重复
        发出=世代['号']#这一次的代
        飞行['中']=True#占住
        try:#读完一定放开
            try:#失败留在快照上
                行=拉清单()#行
            except Exception as 错误:#读失败
                if 发出!=世代['号']:#已经重置
                    return#丢掉
                清单读失败(错误)#打出来
                消息=str(错误) if str(错误)!='' else 'reading the cordis inventory failed'#空消息用上游缺省句
                当前=快照盒['当前']#还显示原来的行
                发布({
                    'rows':当前['rows'],
                    'removed':当前['removed'],
                    'read':当前['read'],
                    'error':消息,
                })#失败但不把行清空
                return#结束
            if 发出!=世代['号']:#已经重置
                return#丢掉
            当前=快照盒['当前']#上一份
            已移除=set(当前['removed'])#沿用移除记录
            活着=set()#这次还在的插件
            for 行项 in 行:#逐行
                活着.add(行项['pluginId'])#记下
            for 先前 in 当前['rows']:#上一份里消失的
                if 先前['pluginId'] not in 活着:#清单里没有了
                    已移除.add(先前['pluginId'])#记成已移除
            发布({'rows':行,'removed':已移除,'read':True})#读完
        finally:#这一代还有效才放开飞行
            if 发出==世代['号']:#没被重置
                飞行['中']=None#可以再读

    def 退役(插件标识):
        '页面上移除成功后先从行里拿掉，并记入已移除'
        当前=快照盒['当前']#当前
        已移除=set(当前['removed'])#拷贝
        已移除.add(插件标识)#加上
        留下=[]#还显示的行
        for 行项 in 当前['rows']:#逐行
            if 行项['pluginId']!=插件标识:#不是这个
                留下.append(行项)#留下
        下一={'rows':留下,'removed':已移除,'read':当前['read']}#新快照
        if 'error' in 当前:#沿用读取错误
            下一['error']=当前['error']#留下
        发布(下一)#通知

    def 重置():
        '丢掉已读的行。已移除记录留着。进行中的读取作废'
        世代['号']=世代['号']+1#作废
        飞行['中']=None#允许立刻再读
        当前=快照盒['当前']#当前
        发布({'rows':[],'removed':当前['removed'],'read':False})#清空行

    清单={'getSnapshot':取快照,'subscribe':订阅,'refresh':刷新,'retire':退役,'reset':重置}#清单源
    运行器=上下文.dynamicCordisRunner#本页运行面

    def 已加载快照():
        '本页已加载的包'
        return 运行器.getSnapshot()#现场

    def 已加载订阅(函数):
        '现场变了就通知'
        return 运行器.subscribe(函数)#退订器

    已加载={'getSnapshot':已加载快照,'subscribe':已加载订阅}#给钩子用的源

    def 对账():
        '已经读过清单才对账审批'
        快照=清单['getSnapshot']()#当前
        if 快照['read']:#读过
            运行器.reconcileApprovals(快照['rows'])#对账

    def 订阅对账():
        '清单一变就对账'
        return 清单['subscribe'](对账)#退订

    上下文.副作用(订阅对账,'ui-cordis: reconcile pending approvals')#对账

    def 包上线():
        '有包公告就重读'
        清单['refresh']()#重读

    def 包撤回():
        '有撤回就重读'
        清单['refresh']()#重读

    def 新运行请求(请求):
        '清单里还没有这个插件才重读'
        插件=请求['pluginId']#插件
        已有=False#是否已有行
        for 行项 in 清单['getSnapshot']()['rows']:#逐行
            if 行项['pluginId']==插件:#有了
                已有=True#不用读
                break#停
        if not 已有:#缺行
            清单['refresh']()#重读

    def 请求已落定():
        '审批落定就重读'
        清单['refresh']()#重读

    getattr(上下文.remote,'$on')('cordis/dynamic-package',包上线)#包公告
    getattr(上下文.remote,'$on')('cordis/dynamic-retract',包撤回)#撤回
    getattr(上下文.remote,'$on')('cordis/request-run',新运行请求)#新的运行请求
    getattr(上下文.remote,'$on')('cordis/request-run-resolved',请求已落定)#请求落定

    def 重连():
        '换了连接就丢掉旧行再读'
        清单['reset']()#丢掉
        清单['refresh']()#重读

    上下文.监听('connection/reset',重连)#连接重置
    会话仓={}#每个会话一份运行卡索引

    def 运行卡面(会话标识):
        '这个会话的运行卡共用一份索引'
        仓=会话仓.get(会话标识)#已有
        if 仓 is None:#第一次
            指针表={}#键到最新指针
            仓听众=set()#订阅
            缓存={'值':None}#快照缓存
            def 取仓快照():
                '两次变更之间是同一份表'
                if 缓存['值'] is None:#失效了
                    缓存['值']=dict(指针表)#拷贝
                return 缓存['值']#快照
            def 订仓(监听):
                '返回退订'
                仓听众.add(监听)#加上
                def 退订():
                    '不再通知'
                    仓听众.discard(监听)#拿掉
                return 退订#拆除器
            def 观察(指针):
                '只有更大的日志序号能替换'
                当前指针=指针表.get(指针['key'])#现有
                if 当前指针 is not None and 当前指针['seq']>=指针['seq']:#不比现有新
                    return#留下现有的
                指针表[指针['key']]=指针#换上
                缓存['值']=None#失效
                for 监听 in list(仓听众):#通知
                    监听()#变了
            仓={'getSnapshot':取仓快照,'subscribe':订仓,'observe':观察}#这一会话的仓
            会话仓[会话标识]=仓#留下
        def 交给索引(指针):
            '把这张成功的运行卡交给索引'
            仓['observe'](指针)#发布
        return {
            'hooks':{
                'inventory':清单,
                'loaded':已加载,
                'runCards':仓,
                'activeRuns':运行器.activeRuns,
            },
            'onObserveRunCard':交给索引,
        }#运行卡面

    def 面板停止(会话标识,插件标识):
        '停止后重读清单'
        结果=停止(会话标识,插件标识)#停止
        清单['refresh']()#重读
        return 结果#交给面板

    def 面板移除(会话标识,插件标识):
        '移除成功就先从清单拿掉，然后再重读'
        结果=移除(会话标识,插件标识)#移除
        if 结果['ok']:#成功
            清单['retire'](插件标识)#先拿掉
        清单['refresh']()#重读
        return 结果#交给面板

    def 面板批准(请求号,批后续):
        '转发批准'
        return 运行器.approve(请求号,批后续)#批准

    def 面板拒绝(请求号):
        '转发拒绝'
        return 运行器.decline(请求号)#拒绝

    def 面板运行(请求):
        '转发用户运行'
        return 运行器.startUserRun(请求)#运行

    def 面板刷新():
        '重读清单'
        清单['refresh']()#重读

    def 面板注入():
        '面板要的钩子和动作'
        return {
            'hooks':{
                'inventory':清单,
                'activeRuns':运行器.activeRuns,
                'runErrors':运行器.lastRunError,
                'loaded':已加载,
                'renderFailures':运行器.renderFailures,
            },
            'onApprove':面板批准,
            'onDecline':面板拒绝,
            'onRun':面板运行,
            'onStop':面板停止,
            'onRemove':面板移除,
            'onRefresh':面板刷新,
        }#面

    def 登记面板():
        '登记到侧栏底部'
        return 上下文.slots.register({
            'name':'sidebar.footer.action',
            'id':'cordis-panel',
            'locale':文案.命名空间,
            'inject':面板注入,
        },面板.面板)#面板

    上下文.slots.inject('sidebar.footer.action',登记面板)#等槽声明

    def 定义卡面():
        '定义卡只看清单和已加载'
        return {'hooks':{'inventory':清单,'loaded':已加载}}#面

    def 登记定义行():
        '登记定义工具行'
        return 上下文.slots.register({
            'name':'tool.call.toolview',
            'key':'cordis_define',
            'locale':文案.命名空间,
            'inject':定义卡面,
        },定义行.定义行)#定义行

    上下文.slots.inject('tool.call.toolview',登记定义行)#等槽声明

    def 登记运行行():
        '登记运行工具行，并声明包的业务视图槽'
        return 上下文.slots.register({
            'name':'tool.call.toolview',
            'key':'cordis_run',
            'locale':文案.命名空间,
            'children':{槽位.业务视图槽:{'kind':'keyed','scope':'session'}},
            'inject':运行卡面,
        },运行行.运行行)#运行行

    上下文.slots.inject('tool.call.toolview',登记运行行)#等槽声明

    def 登记动作行():
        '停止和移除共用一行，卸下时按相反顺序拆'
        yield 上下文.slots.register({
            'name':'tool.call.toolview',
            'key':'cordis_stop',
            'locale':文案.命名空间,
        },动作行.动作行)#停止
        yield 上下文.slots.register({
            'name':'tool.call.toolview',
            'key':'cordis_undefine',
            'locale':文案.命名空间,
        },动作行.动作行)#移除

    上下文.slots.inject('tool.call.toolview',登记动作行)#等槽声明

inject=依赖#框架槽
apply=应用#框架槽

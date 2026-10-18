from ....基础设施.通用工具 import 紧凑json编码#目标指纹
from threading import Lock as 锁,Thread as 线程#串行调和，单插件限时
from ..异常 import 客户端模块错误#本包异常
from .发行变更 import 发行变更门#只应用本页发行
from .清单 import 解析启动清单,读取发行#清单与发行
from .通告 import 可观察快照,通知订阅者#状态源
from .条目生命周期 import 拆除条目纤程,移除包拥有样式#纤程与样式


__all__=['客户端条目表']#仅中文公开名

活动纤程态=2#FiberState.ACTIVE
失败纤程态=3#FiberState.FAILED
加载超时秒=3#单个插件加载最多等这么久。到点放弃这一条，不杀线程


def 条目目标指纹(清单):
    '修订与请求标识期望代码。URL 只选交付资源，不进指纹'
    return 紧凑json编码([[行['id'],行['rev'],行['inject'],行['external']] for 行 in 清单['modules']])#序列化


def 等返回(结果):
    '上游 await 一个调用的返回值。没有 等待 就当已经落定'
    再等=None if 结果 is None else getattr(结果,'等待',None)#同步封装
    if callable(再等):#返回的是承诺
        再等()#等完


def 调用等待(对象):
    '调用协议方法 await，并等它的返回值'
    等返回(getattr(对象,'await')())#协议方法 await


class 客户端条目表:
    '只管理从宿主清单创建的条目。其它加载器贡献者保留所有权'
    def __init__(自身,模块,索引):
        'Cordis 启动前构造。模块负责到达与物化，索引负责替换失效与裁剪'
        自身.模块=模块#模块系统
        自身.索引=索引#更新、替换失效、裁剪
        自身.快照={'syncing':False,'failures':[]}#条目状态
        自身.监听器=set()#状态订阅
        自身.发行门=发行变更门(模块.manifest.get('release'))#本页发行
        自身.托管={}#包 id 到条目
        自身.修订表={}#包 id 到修订
        自身.装载器=None#页面加载器
        自身.队锁=锁()#串行队列
        自身.已放弃=set()#超时后不再把这条写进托管
        自身.期望=模块.manifest#当前期望清单
        自身.代次=0#代次
        自身.已停=False#已停
        def 读取():
            '当前条目状态'
            return 自身.快照#快照
        def 订阅(监听器):
            '订阅条目状态'
            自身.监听器.add(监听器)#加
            def 退订():
                '去掉这个监听'
                自身.监听器.discard(监听器)#退
            return 退订#退订函数
        自身.state=可观察快照(读取,订阅)#协议名 state

    @property
    def releaseChange(自身):
        '要通告的宿主发行变化。同版或已放下时快照是 None'
        return 自身.发行门.change#协议名 releaseChange

    def dismissRelease(自身):
        '停止通告当前宿主发行。更新仍暂停，直到回到本页发行或重新加载'
        自身.发行门.放下()#放下

    def start(自身,装载器,清单):
        '创建初始名册并保留条目身份。阻塞到初建与激活落定'
        if 自身.装载器 is not None:#已经启动
            raise 客户端模块错误('client-modules: entries already started')#重复启动
        自身.装载器=装载器#记下
        自身.期望=清单#期望
        def 调和拆除工厂():
            '返回作用域拆除器'
            def 拆除():
                '停调和并推进代次'
                自身.已停=True#停
                自身.代次+=1#换代
            return 拆除#拆除器
        装载器.ctx.副作用(调和拆除工厂,'client-modules: entry reconciliation')#协议名 ctx
        def 初建():
            '逐插件创建并记下修订。一条失败，后面的照样创建'
            失败表=[]#这一轮没起来的
            for 插件 in 自身.期望['plugins']:#逐插件
                try:#这一条
                    自身.限时创建(装载器,插件['id'])#到点就放弃这一条
                except Exception as 错误:#失败
                    失败表.append({'id':插件['id'],'message':str(错误)})#记下
            try:#等已经起来的那些激活
                调用等待(装载器)#加载器上的 await
            except Exception as 错误:#激活失败不挡住启动
                失败表.append({'id':'loader','message':str(错误)})#记下
            for 行 in 自身.模块.manifest['modules']:#记修订
                自身.修订表[行['id']]=行['rev']#写入
            if len(失败表)>0:#有没起来的
                自身.发布({'syncing':False,'failures':失败表})#写进条目状态
        自身.入队(初建)#入队

    def sync(自身,图):
        '校验并应用最新宿主图。另一发行不应用，只更新 releaseChange'
        if not 自身.发行门.观察(读取发行(图)):#先比发行
            return#另一发行
        清单=解析启动清单(图)#再校验其余
        if 条目目标指纹(清单)!=条目目标指纹(自身.期望):#目标变了
            自身.代次+=1#换代，取消过时挂载
        自身.期望=清单#期望
        代次=自身.代次#这一代
        def 调和任务(代=代次):
            '调和这一代'
            自身.调和(代)#调和
        自身.入队(调和任务)#入队

    def retry(自身):
        '对照最新图重试失败条目，包含修订没变的'
        自身.代次+=1#换代
        代次=自身.代次#这一代
        def 重试任务(代=代次):
            '重试这一代'
            自身.调和(代)#调和
        自身.入队(重试任务)#入队

    def reload(自身,标识,修订):
        '与图更新同一队列替换一条目。重复修订忽略。另一发行时直接返回'
        if not 自身.发行门.匹配:#不是本页发行
            return#不替换
        模块行=[]#新的模块行
        for 行 in 自身.期望['modules']:#逐行
            if 行['id']==标识:#这一行
                新行=dict(行)#拷
                新行['rev']=修订#换修订
                模块行.append(新行)#收下
            else:#其它行
                模块行.append(行)#原样
        新期望=dict(自身.期望)#拷清单
        新期望['modules']=模块行#换模块行
        自身.期望=新期望#写回
        def 重载任务():
            '入队替换，或在没有条目时重新调和'
            期望行=None#期望行
            for 行 in 自身.期望['modules']:#找行
                if 行['id']==标识:#命中
                    期望行=行#记下
                    break#找到
            if 自身.已停 or 期望行 is None:#已停或图上没有
                return#停
            条目=自身.托管[标识] if 标识 in 自身.托管 else None#托管条目
            if 条目 is None:#导入失败后没有条目
                自身.模块.invalidate(标识,期望行['rev'])#失效
                移除包拥有样式(标识,自身.模块.文档)#拆样式
                自身.调和(自身.代次)#重新调和
                return#停
            if 自身.修订表.get(标识)==修订:#同一修订
                return#忽略
            留下=[失败 for 失败 in 自身.快照['failures'] if 失败['id']!=标识]#去掉这一条的旧失败
            自身.发布({'syncing':True,'failures':留下})#开始同步
            自身.替换(条目,标识,修订,自身.代次)#替换
            自身.发布({'syncing':False,'failures':自身.快照['failures']})#结束
        自身.入队(重载任务,标识)#主题是包 id

    def 发布(自身,快照):
        '写快照并通知监听'
        自身.快照=快照#写
        通知订阅者(自身.监听器,'synchronization')#派发

    def 入队(自身,任务,主题='graph'):
        '串行执行。失败写入状态后，后面的任务仍能入队'
        with 自身.队锁:#串行
            try:#跑任务
                任务()#执行
            except Exception as 错误:#记下后继续向外抛
                留下=[失败 for 失败 in 自身.快照['failures'] if 失败['id']!=主题]#去掉同主题
                自身.发布({'syncing':False,'failures':留下+[{'id':主题,'message':str(错误)}]})#写入失败
                raise#调用方看得到

    def 是否当前代(自身,代次):
        '未停且代次相同'
        return (not 自身.已停) and 代次==自身.代次#当前代

    def 标明加载(自身,标识):
        '启动页上写当前插件名'
        文档=自身.模块.文档#这次握手的文档
        if 文档 is None:#没有文档
            return#停
        提示=文档.querySelector('[data-dsh-boot] .hint')#提示
        if 提示 is None:#启动页已经卸下
            return#停
        名称=标识#包名
        前缀='@deepseek-ai/'#发行前缀
        if 名称.startswith(前缀):#去掉前缀
            名称=名称[len(前缀):]#包名
        提示.textContent='正在加载 '+名称#当前这一条

    def 限时创建(自身,装载器,标识):
        '另开线程创建。等待时放下队锁，创建里再入队不会和这次等待互锁。超时放弃这一条，不杀线程'
        盒子={}#工作线程的结果
        def 跑():
            '写上插件名再创建。异常留在盒子里'
            try:#这一条
                自身.标明加载(标识)#先让页面看得到名字
                自身.创建(装载器,标识)#创建
            except Exception as 错误:#创建失败
                盒子['错误']=错误#交给调用方
        工作=线程(target=跑,daemon=True)#超时后留在后台
        放下锁=自身.队锁.locked()#调用方正在入队
        if 放下锁:#先放开，工作线程才能再入队
            自身.队锁.release()#放下
        try:#等这一条
            工作.start()#开始
            工作.join(加载超时秒)#到点就不再等
        finally:#把锁拿回来，后面的任务仍然串行
            if 放下锁:#刚才放下了
                自身.队锁.acquire()#拿回
        if 工作.is_alive():#还没结束
            自身.已放弃.add(标识)#晚到的创建不再写入托管
            raise TimeoutError(标识+' 加载超过'+str(加载超时秒)+'秒')#这条到此为止
        if '错误' in 盒子:#创建自己失败了
            raise 盒子['错误']#原错误

    def 创建(自身,装载器,标识):
        '即使加载器在插入后拒绝导出，仍保留这条条目。已经放弃的不再写入托管'
        选项={'name':标识}#选项
        条目标识=装载器.ensureId(选项)#协议名 ensureId
        try:#创建
            等返回(装载器.create(选项))#协议名 create
        finally:#插入后仍记下这条条目
            if 标识 not in 自身.已放弃:#调用方还在等这一条
                自身.托管[标识]=装载器.resolve(条目标识)#协议名 resolve

    def 替换(自身,条目,标识,修订,代次):
        '替换一条目的代码'
        自身.索引['invalidateForReplacement'](标识,修订)#先失效
        自身.模块.prefetch(标识)#预取
        if not 自身.是否当前代(代次):#过期
            return#停
        拆除条目纤程(条目)#拆纤程
        移除包拥有样式(标识,自身.模块.文档)#拆样式
        if not 自身.是否当前代(代次):#过期
            return#停
        自身.模块.import_(标识,'',{})#导入
        if not 自身.是否当前代(代次):#过期
            return#停
        等返回(条目.refresh())#刷新
        纤程=getattr(条目,'fiber',None)#协议名 fiber
        if 纤程 is not None:#有纤程
            调用等待(纤程)#等纤程上的 await
        if getattr(条目,'fiber',None) is None:#导入失败
            raise 客户端模块错误('client-modules: '+标识+' import failed (see console)')#见控制台
        自身.修订表[标识]=修订#记修订

    def 调和(自身,代次):
        '按期望清单调和托管条目'
        if not 自身.是否当前代(代次):#过期
            return#停
        装载器=自身.装载器#加载器
        if 装载器 is None:#还没启动
            raise 客户端模块错误('client-modules: entries have not started')#未启动
        清单=自身.期望#期望
        自身.发布({'syncing':True,'failures':[]})#开始
        失败表=[]#本轮失败
        自身.索引['update'](清单,自身.托管.keys())#先刷新描述符
        想要=set(行['id'] for 行 in 清单['plugins'])#仍要的插件
        for 标识 in list(自身.托管.keys()):#逐托管
            if 标识 in 想要:#仍要
                continue#跳过
            条目=自身.托管[标识]#条目
            纤程=getattr(条目,'fiber',None)#纤程
            装载器.remove(条目.id)#移除
            del 自身.托管[标识]#摘托管
            自身.修订表.pop(标识,None)#摘修订
            while 纤程 is not None and getattr(纤程,'inertia',None) is not None:#等惯性
                纤程.inertia.等待()#等这一轮承诺
        for 行 in 清单['modules']:#逐模块
            if not 自身.是否当前代(代次):#过期
                break#停
            try:#调和一行
                条目=自身.托管[行['id']] if 行['id'] in 自身.托管 else None#托管
                if 条目 is None:#新建
                    自身.模块.prefetch(行['id'])#预取
                    if not 自身.是否当前代(代次):#过期
                        break#停
                    自身.模块.import_(行['id'],'',{})#导入
                    if not 自身.是否当前代(代次):#过期
                        break#停
                    自身.限时创建(装载器,行['id'])#到点就放弃这一条
                    自身.修订表[行['id']]=行['rev']#记修订
                elif 自身.修订表.get(行['id'])!=行['rev']:#修订变了
                    自身.替换(条目,行['id'],行['rev'],代次)#替换
                elif getattr(条目,'fiber',None) is None:#没有纤程
                    自身.替换(条目,行['id'],行['rev'],代次)#替换
                elif getattr(条目.fiber,'state',None)==失败纤程态:#失败态
                    条目.fiber.update(条目.options.config)#用配置再更新
            except Exception as 错误:#这一包失败不挡住其它包
                失败表.append({'id':行['id'],'message':str(错误)})#记下
        调用等待(装载器)#等加载器上的 await
        for 标识,条目 in list(自身.托管.items()):#核激活
            if any(失败['id']==标识 for 失败 in 失败表):#这一轮已经失败
                continue#跳过
            纤程=getattr(条目,'fiber',None)#纤程
            if 纤程 is not None and getattr(纤程,'state',None)==活动纤程态:#已活动
                continue#跳过
            try:#等激活
                if 纤程 is None:#没有纤程
                    raise 客户端模块错误('client-modules: '+标识+' import failed (see console)')#见控制台
                调用等待(纤程)#等纤程上的 await
                失败表.append({'id':标识,'message':'client-modules: '+标识+' is waiting for activation'})#仍在等
            except Exception as 错误:#激活失败
                失败表.append({'id':标识,'message':str(错误)})#记下
        根名=[]#加载器上的名字
        for 条目 in 装载器.entries():#逐条目
            根名.append(条目.options.name)#名字
        自身.索引['prune'](根名)#裁剪
        if 自身.是否当前代(代次):#仍是这一代
            自身.发布({'syncing':False,'failures':失败表})#发布结果

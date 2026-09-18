import json#条目目标指纹
from threading import Lock as 锁#串行调和队列
from .清单 import 客户端模块错误,解析启动清单#本包异常与清单解析
from .条目生命周期 import 拆除条目纤程,移除包拥有样式#纤程与样式拆除

__all__=['客户端条目状态','客户端条目表','活动纤程态','失败纤程态']#仅中文公开名

#常量
活动纤程态=2#镜像 Cordis FiberState.ACTIVE
失败纤程态=3#镜像 Cordis FiberState.FAILED

#工具
def 条目目标指纹(清单):
    """修订与请求标识期望代码；URL 只选其不可变交付资源。"""
    return json.dumps([[行['id'],行['rev'],行['inject'],行['external']] for 行 in 清单['modules']],ensure_ascii=False,separators=(',',':'),allow_nan=False)#序列化

class 客户端条目状态(dict):
    """页面本地失败不改变 Host 的包启用态。键：syncing、failures。"""

#
class 客户端条目表:
    """只管理从 Host 清单创建的条目；其它 Loader 贡献者保留所有权。"""
    def __init__(自身,模块,索引):
        """Cordis 启动前构造页面控制器。模块是装载面；索引提供更新/替换失效/裁剪。"""
        自身.模块=模块#模块到达与物化所有者
        自身.索引=索引#私有描述符替换与未用模块清理
        自身.快照={'syncing':False,'failures':[]}#条目状态快照
        自身.监听器=set()#状态订阅
        自身.托管={}#包 id → 条目
        自身.修订表={}#包 id → 修订
        自身.装载器=None#页面 Loader
        自身.队锁=锁()#串行调和
        自身.期望=模块.manifest#初清单
        自身.代次=0#代次
        自身.已停=False#已停
        自身.state=自身#可观察状态源（getSnapshot/subscribe）

    def getSnapshot(自身):
        """页面诊断消费的状态快照。"""
        return 自身.快照#当前快照

    def subscribe(自身,监听器):
        """订阅状态；返回退订器。"""
        自身.监听器.add(监听器)#加
        def 退订():
            """去掉监听。"""
            自身.监听器.discard(监听器)#退
        return 退订#退订器

    def start(自身,装载器,清单):
        """创建初始名册并保留条目身份供后续调和；阻塞至初建落定。"""
        if 自身.装载器 is not None:#已启动
            raise 客户端模块错误('client-modules: entries already started')#已启动
        自身.装载器=装载器#记下
        自身.期望=清单#期望
        def 调和拆除工厂():
            """返回作用域拆除器。"""
            def 拆除():
                """停调和并推进代次。"""
                自身.已停=True#停
                自身.代次+=1#推进代次
            return 拆除#拆除器
        装载器.ctx.副作用(调和拆除工厂,'client-modules: entry reconciliation')#effect 名
        def 初建():
            """逐插件创建并记修订。"""
            for 插件 in 自身.期望['plugins']:#逐插件
                自身.创建(装载器,插件['id'])#创建
            装载器.等待()#等激活
            for 行 in 自身.模块.manifest['modules']:#记修订
                自身.修订表[行['id']]=行['rev']#写入
        自身.入队(初建)#入队初建

    def sync(自身,图):
        """校验并应用最新完整 Host 图；阻塞至调和落定。"""
        清单=解析启动清单(图)#解析
        if 条目目标指纹(清单)!=条目目标指纹(自身.期望):#目标变则换代
            自身.代次+=1#换代
        自身.期望=清单#期望
        代次=自身.代次#代次
        自身.入队(lambda:自身.调和(代次))#调和

    def retry(自身):
        """对照最新图重试失败条目，含未变修订。"""
        自身.代次+=1#换代
        代次=自身.代次#代次
        自身.入队(lambda:自身.调和(代次))#调和

    def reload(自身,标识,修订):
        """与图更新同一队列替换一条目代码；重复修订忽略。"""
        自身.期望={#更新期望修订
            **自身.期望,#展开
            'modules':[{**行,'rev':修订} if 行['id']==标识 else 行 for 行 in 自身.期望['modules']],#改修订
        }#结束期望
        def 重载任务():
            """入队替换或调和。"""
            期望行=None#期望行
            for 行 in 自身.期望['modules']:#找行
                if 行['id']==标识:#命中
                    期望行=行#记下
                    break#找到
            if 自身.已停 or 期望行 is None:#已停或无行
                return#停
            条目=自身.托管[标识] if 标识 in 自身.托管 else None#托管
            if 条目 is None:#无条目
                自身.模块.invalidate(标识,期望行['rev'])#失效
                移除包拥有样式(标识)#拆样式
                自身.调和(自身.代次)#调和
                return#停
            if 标识 in 自身.修订表 and 自身.修订表[标识]==修订:#同修订
                return#跳过
            自身.发布({'syncing':True,'failures':[失败 for 失败 in 自身.快照['failures'] if 失败['id']!=标识]})#清该 id 失败
            自身.替换(条目,标识,修订,自身.代次)#替换
            自身.发布({'syncing':False,'failures':自身.快照['failures']})#结束同步
        自身.入队(重载任务,标识)#subject=id

    def 发布(自身,快照):
        """写快照并通知监听。"""
        自身.快照=快照#写
        for 监听器 in list(自身.监听器):#通知
            try:#隔离
                监听器()#触发
            except Exception as 错误:#抛错
                print('client-modules: synchronization subscriber failed',错误)#诊断

    def 入队(自身,任务,主题='graph'):
        """串行执行；失败写入状态后仍允许后续入队。"""
        with 自身.队锁:#串行
            try:#跑任务
                任务()#执行
            except Exception as 错误:#吞失败进状态
                自身.发布({'syncing':False,'failures':[#写失败
                    *[失败 for 失败 in 自身.快照['failures'] if 失败['id']!=主题],#去掉同 subject
                    {'id':主题,'message':str(错误)},#新失败
                ]})#结束发布
                raise#交调用方

    def 是否当前代(自身,代次):
        """未停且代次匹配。"""
        return (not 自身.已停) and 代次==自身.代次#当前代

    def 创建(自身,装载器,标识):
        """即使 Loader 在插入后拒绝导出，仍保留所有权。"""
        选项={'name':标识}#选项
        条目标识=装载器.ensureId(选项)#确保 id
        try:#创建
            装载器.create(选项)#创建
        finally:#无论成败
            自身.托管[标识]=装载器.resolve(条目标识)#托管

    def 替换(自身,条目,标识,修订,代次):
        """替换一条目代码。"""
        自身.索引['invalidateForReplacement'](标识,修订)#索引失效
        自身.模块.prefetch(标识)#预取
        if not 自身.是否当前代(代次):#过期
            return#停
        拆除条目纤程(条目)#拆纤程
        移除包拥有样式(标识)#拆样式
        if not 自身.是否当前代(代次):#过期
            return#停
        自身.模块.import_(标识,'',{})#导入
        if not 自身.是否当前代(代次):#过期
            return#停
        条目.refresh()#刷新
        纤程=getattr(条目,'fiber',None)#纤程
        if 纤程 is not None:#有纤程
            纤程.等待()#等纤程
        if getattr(条目,'fiber',None) is None:#导入失败
            raise 客户端模块错误('client-modules: '+标识+' import failed (see console)')#导入失败
        自身.修订表[标识]=修订#记修订

    def 调和(自身,代次):
        """按期望清单调和托管条目。"""
        if not 自身.是否当前代(代次):#过期
            return#停
        装载器=自身.装载器#装载器
        if 装载器 is None:#未启动
            raise 客户端模块错误('client-modules: entries have not started')#未启动
        清单=自身.期望#期望
        自身.发布({'syncing':True,'failures':[]})#开始同步
        失败表=[]#失败累加
        自身.索引['update'](清单,自身.托管.keys())#更新索引
        想要=set(行['id'] for 行 in 清单['plugins'])#想要的插件
        for 标识 in list(自身.托管.keys()):#逐托管
            if 标识 in 想要:#仍要
                continue#跳过
            条目=自身.托管[标识]#条目
            纤程=getattr(条目,'fiber',None)#纤程
            装载器.remove(条目.id)#移除
            del 自身.托管[标识]#摘托管
            自身.修订表.pop(标识,None)#摘修订
            while 纤程 is not None and getattr(纤程,'inertia',None) is not None:#等惯性
                惯性=纤程.inertia#惯性
                惯性.wait() if hasattr(惯性,'wait') else None#阻塞
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
                    自身.创建(装载器,行['id'])#创建
                    自身.修订表[行['id']]=行['rev']#记修订
                elif 行['id'] not in 自身.修订表 or 自身.修订表[行['id']]!=行['rev']:#修订变
                    自身.替换(条目,行['id'],行['rev'],代次)#替换
                elif getattr(条目,'fiber',None) is None:#无纤程
                    自身.替换(条目,行['id'],行['rev'],代次)#替换
                elif getattr(条目.fiber,'state',None)==失败纤程态:#失败
                    条目.fiber.update(条目.options.config)#用配置再更新
            except Exception as 错误:#包级失败
                失败表.append({'id':行['id'],'message':str(错误)})#记下
        装载器.等待()#等装载
        for 标识,条目 in list(自身.托管.items()):#核激活
            if any(失败['id']==标识 for 失败 in 失败表):#已失败
                continue#跳过
            纤程=getattr(条目,'fiber',None)#纤程
            if 纤程 is not None and getattr(纤程,'state',None)==活动纤程态:#已活动
                continue#跳过
            try:#等激活
                if 纤程 is None:#无纤程
                    raise 客户端模块错误('client-modules: '+标识+' import failed (see console)')#无纤程
                纤程.等待()#等
                失败表.append({'id':标识,'message':'client-modules: '+标识+' is waiting for activation'})#仍等待
            except Exception as 错误:#失败
                失败表.append({'id':标识,'message':str(错误)})#记下
        根名=[条目.options.name for 条目 in 装载器.entries()]#Loader 根名
        自身.索引['prune'](根名)#裁剪
        if 自身.是否当前代(代次):#仍当前
            自身.发布({'syncing':False,'failures':失败表})#发布结果

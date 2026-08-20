"""可变的加载器条目树。持久化由子类提供。"""
import random
from urllib.parse import urljoin as 拼接网址#new URL 拼接
import cordis
import cosmokit
from cordis.工具 import 全部结算#全部结算
from .组 import 条目组#条目组

未传=object()#对应 TS 未传的 parent（与 null 区分）

class 条目树:
    """可变的加载器条目树。持久化由子类实现 写入。"""
    分隔=':'#嵌套编号分隔符

    def __init__(自身,ctx):
        """扩展带 baseUrl 的上下文并创建根组。"""
        自身.ctx=ctx.extend({'baseUrl':ctx.baseUrl})#子上下文
        自身.context=自身.ctx#派发框架事件的上下文
        自身.enableLogs=None#默认不打插件日志
        自身.store={}#编号到条目
        自身.root=条目组(自身.ctx,自身)#根组
        条目对象=getattr(自身.ctx.fiber,'entry',None)#拥有方条目
        if 条目对象:
            条目对象.subtree=自身#挂上子树

    def 条目们(自身):
        """迭代本树及嵌套子树中的条目。"""
        for 条目对象 in list(自身.store.values()):
            yield 条目对象#本层
            if not 条目对象.subtree:
                continue#没有子树
            yield from 条目对象.subtree.条目们()#嵌套

    def 取任务(自身):
        """返回本树拥有的未完成导入与生命周期任务。"""
        任务列表=[]#进行中的任务
        for 条目对象 in 自身.条目们():
            任务=条目对象._初始化任务#导入任务
            if 任务 is None and 条目对象.fiber:
                任务=条目对象.fiber.inertia#光纤惯性
            if cosmokit.是否非空(任务):
                任务列表.append(任务)#非空才收
        return 任务列表#任务列表

    def 等待(自身):
        """等到本树没有活动导入或生命周期任务。"""
        while True:
            任务列表=自身.取任务()#当前任务
            if 任务列表:
                全部结算(任务列表)#等待已有承诺
                continue#再看是否还有新任务
            失败=[]#光纤失败
            for 条目对象 in 自身.条目们():
                try:
                    条目对象._等待()#等待该光纤
                except BaseException as 错误:
                    失败.append(错误)#收集
            if len(失败)==1:
                raise 失败[0]#单失败原样抛
            if len(失败)>1:
                raise cordis.聚合错误(失败,'loader fibers failed')#多失败聚合
            自身.ctx.reflect.通知(['loader'])#通知依赖方
            if not 自身.取任务():
                return#确实空闲

    def 确保编号(自身,选项):
        """没有 id 则生成树内唯一的随机十六进制编号。"""
        if not 选项.get('id'):
            while True:
                选项['id']=format(int(random.random()*16**8),'x')#近似 toString(16).slice(2,10)
                if 选项['id'] not in 自身.store:
                    break#不碰撞
        return 选项['id']#已有或新编号

    def 解析(自身,编号):
        """按编号解析条目，嵌套编号用分隔符切开。"""
        片段=编号.split(条目树.分隔)#切开
        树=自身#从本树走
        末段=片段.pop()#最后一段是目标
        for 段 in 片段:
            条目对象=树.store.get(段)#中间段
            树=条目对象.subtree if 条目对象 else None#进入子树
            if not 树:
                raise Exception('cannot resolve entry '+编号)#中间缺失
        条目对象=树.store.get(末段)#目标
        if not 条目对象:
            raise Exception('cannot resolve entry '+编号)#没有该条目
        return 条目对象#命中

    def 解析组(自身,编号):
        """解析根组或某条目上的子组。"""
        if not 编号:
            return 自身.root#根组
        条目对象=自身.解析(编号)#先解析条目
        if not 条目对象.subgroup:
            raise Exception('entry '+编号+' is not a group')#不是组
        return 条目对象.subgroup#子组

    def 创建(自身,选项,父=None,位置=None):
        """在根组或嵌套组中创建条目。"""
        if 位置 is None:
            位置=float('inf')#默认追加
        组对象=自身.解析组(父)#目标组
        编号=组对象.创建(选项)#创建
        条目对象=自身.解析(编号)#取出
        if 位置==float('inf'):
            组对象.data.append(条目对象.options)#追加
        else:
            组对象.data.insert(位置,条目对象.options)#插入
        组对象.tree.写入()#持久化
        return 编号#新编号

    def 移除(自身,编号):
        """停止并从父组删除条目。"""
        条目对象=自身.解析(编号)#查出
        条目对象.parent.移除(编号)#父组删除
        条目对象.parent.tree.写入()#持久化

    def 更新(自身,编号,选项,父=未传,位置=None):
        """更新条目，可选地移到另一组。"""
        条目对象=自身.解析(编号)#查出
        源=条目对象.parent#原组
        源下标=-1#原位置
        下标=0#扫描
        while 下标<len(源.data):
            if 源.data[下标] is 条目对象.options:
                源下标=下标#记下身份位置
                break#找到
            下标+=1#前进
        目标=源#默认不移动
        if 父 is not 未传:
            目标=自身.解析组(父)#null 则根组
            源.取消链接(条目对象.options)#从原组 data 摘掉
            if 位置 is None or 位置==float('inf'):
                目标.data.append(条目对象.options)#position ?? Infinity
            else:
                目标.data.insert(位置,条目对象.options)#插入
            条目对象.parent=目标#改父
        try:
            条目对象.更新(选项,False,True)#force 更新
        except BaseException as 错误:
            if 父 is not 未传:
                目标.取消链接(条目对象.options)#从新组摘掉
                插入处=len(源.data) if 源下标<0 else 源下标#回原位
                源.data.insert(插入处,条目对象.options)#插回
                条目对象.parent=源#还父
                try:
                    条目对象.更新({},False,True)#force 空更新
                except BaseException as 回滚错误:
                    raise cordis.聚合错误([错误,回滚错误],'failed to roll back loader entry move '+编号)#移动回滚失败
            raise 错误#原错误
        源.tree.写入()#源树持久化
        if 目标 is not 源:
            目标.tree.写入()#目标树持久化

    def 导入(自身,名称,获取外层栈=None):
        """从说明符或 `cordis:` 内建名导入插件模块。"""
        if 名称.startswith('cordis:'):
            return 自身.ctx.loader.builtins[名称[7:]]#内建表
        def 回调(信息):
            """动态导入并增加栈偏移。"""
            信息.偏移+=3#剥掉 ModuleJob / tracePromise / import 三帧
            内部=getattr(自身.ctx.loader,'internal',None)#Node 内部加载器
            if 内部:
                return 内部.import(名称,自身.ctx.baseUrl,{})#内部导入
            if 名称.startswith('.'):
                目标=拼接网址(str(自身.ctx.baseUrl or ''),名称)#new URL(name, baseUrl).href
                return __import__(目标,fromlist=['*'])#相对导入
            return __import__(名称,fromlist=['*'])#绝对导入
        return cordis.拼接错误(回调,获取外层栈)#拼外层栈

    def 写入(自身):
        """持久化当前树状态。内存树由子类改成空操作。"""
        raise NotImplementedError#abstract write

EntryTree=条目树#英文别名
条目树.sep=条目树.分隔#英文别名
条目树.entries=条目树.条目们#英文别名
条目树.getTasks=条目树.取任务#英文别名
条目树.await_=条目树.等待#英文别名
条目树.ensureId=条目树.确保编号#英文别名
条目树.resolve=条目树.解析#英文别名
条目树.resolveGroup=条目树.解析组#英文别名
条目树.create=条目树.创建#英文别名
条目树.remove=条目树.移除#英文别名
条目树.update=条目树.更新#英文别名
条目树.write=条目树.写入#英文别名

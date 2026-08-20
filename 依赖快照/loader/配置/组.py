"""子条目列表的运行时拥有者与组插件。"""
import cordis
from cordis.工具 import 全局符号#全局符号
from .条目 import 条目#条目类

class 条目组:
    """子加载器条目列表的运行时拥有者。"""
    键=全局符号('cordis.group')#cordis.group

    def __init__(自身,ctx,tree):
        """保存上下文与树，并把自身挂到拥有方条目。"""
        自身.ctx=ctx#所属上下文
        自身.tree=tree#所属条目树
        自身.data=[]#子条目选项列表
        自身.context=ctx#派发框架事件的上下文
        条目对象=getattr(ctx.fiber,'entry',None)#拥有方条目
        if 条目对象:
            条目对象.subgroup=自身#挂上子组

    def 创建(自身,选项):
        """确保编号、移动父引用并强制更新条目。"""
        编号=自身.tree.确保编号(选项)#写入或生成 id
        已有=自身.tree.store.get(编号)#已有条目
        if 已有:
            条目对象=已有#复用
        else:
            条目对象=条目(自身.ctx.loader)#新建
            自身.tree.store[编号]=条目对象#登记
        先前父=条目对象.parent#可能来自另一组
        条目对象.parent=自身#更新父引用
        try:
            条目对象.更新(选项,True,True)#create+force 替换 options
        except BaseException:
            if 已有:
                条目对象.parent=先前父#复用条目则还父
            else:
                自身.tree.store.pop(编号,None)#新建失败则从表里摘掉
            raise#继续抛
        return 条目对象.id#完整编号

    def 取消链接(自身,选项):
        """从 data 里按对象身份摘掉一条选项。"""
        下标=0#扫描
        while 下标<len(自身.data):
            if 自身.data[下标] is 选项:
                自身.data.pop(下标)#按身份删除
                return#只删一次
            下标+=1#前进

    def 移除(自身,编号,是拆除=False):
        """停止条目，可选地从 data 摘掉，并从 store 删除。"""
        条目对象=自身.tree.store.get(编号)#查出条目
        if not 条目对象:
            return#没有该编号
        条目对象._拆除()#停止光纤
        if not 是拆除:
            自身.取消链接(条目对象.options)#从配置列表摘掉
        自身.tree.store.pop(编号,None)#从 store 删除
        自身.context.emit('loader/partial-dispose',条目对象,条目对象.options,False)#完整拆除

    def 更新(自身,配置):
        """按新配置列表创建、删除并在失败时回滚。"""
        旧配置=自身.data#回滚用旧列表
        见过=set()#查重
        for 选项 in 配置:
            编号=自身.tree.确保编号(选项)#先分配 id
            if 编号 in 见过:
                raise TypeError('duplicate loader entry id: '+str(编号))#重复编号
            见过.add(编号)#记下
        旧表={}#旧 id → 选项
        for 选项 in 旧配置:
            旧表[选项.get('id')]=选项#按 id 索引
        新表={}#新 id → 选项
        for 选项 in 配置:
            新表[选项.get('id')]=选项#按 id 索引
        try:
            失败=[]#创建失败
            for 选项 in 配置:
                try:
                    自身.创建(选项)#逐条创建
                except BaseException as 错误:
                    失败.append(错误)#收集
            if 自身.ctx.fiber.uid is None:
                return#树已拆除则不再回滚
            if len(失败)==1:
                raise 失败[0]#单失败原样抛
            if len(失败)>1:
                raise cordis.聚合错误(失败,'loader entries failed to apply')#多失败聚合
            for 编号 in list(旧表.keys()):
                if 编号 not in 新表:
                    自身.移除(编号,True)#去掉新配置没有的旧条目
            自身.data=配置#提交新列表
        except BaseException as 错误:
            回滚错误列表=[]#回滚阶段失败
            for 编号 in list(新表.keys())[::-1]:
                if 编号 in 旧表:
                    continue#旧配置已有则不拆
                try:
                    自身.移除(编号,True)#拆掉新加上的
                except BaseException as 回滚错误:
                    回滚错误列表.append(回滚错误)#记下
            for 选项 in 旧配置:
                try:
                    自身.创建(选项)#重建旧条目
                except BaseException as 回滚错误:
                    回滚错误列表.append(回滚错误)#记下
            自身.data=旧配置#恢复旧列表
            if 回滚错误列表:
                raise cordis.聚合错误([错误]+回滚错误列表,'loader entry rollback failed')#回滚也失败
            raise 错误#只抛原错误

    def 停止(自身):
        """拆除当前 data 里的全部条目。"""
        for 选项 in list(自身.data):
            自身.移除(选项.get('id'),True)#按拆除路径移除

条目组.key=条目组.键#英文别名
条目组.create=条目组.创建#英文别名
条目组.unlink=条目组.取消链接#英文别名
条目组.remove=条目组.移除#英文别名
条目组.update=条目组.更新#英文别名
条目组.stop=条目组.停止#英文别名

class 组(条目组):
    """挂载嵌套加载器条目组的插件。"""
    初始=[]#默认空配置

    def __init__(自身,ctx,config):
        """挂到拥有方条目所在树，并监听本光纤更新。"""
        条目组.__init__(自身,ctx,ctx.fiber.entry.parent.tree)#父树
        自身.config=config#子条目配置
        def 更新监听(配置,不保存=None,下一步=None):
            """组配置更新改走子条目 diff，不重启组插件。"""
            return 自身.更新(配置)#不调用 next
        ctx.on('internal/update',更新监听)#光纤本地钩子

    def _初始化(自身):
        """登记停止释放器并应用子条目配置。"""
        yield 自身.停止#yield () => this.stop()
        自身.更新(自身.config)#await this.update(this.config)

Group=组#英文别名
EntryGroup=条目组#英文别名
组.initial=组.初始#英文别名
setattr(组,条目组.键,True)#Group[EntryGroup.key] = true

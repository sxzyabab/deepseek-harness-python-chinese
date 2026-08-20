"""条目树中的一个已配置插件节点。"""
import cordis
import cosmokit
from cordis.工具 import 全局符号,是否thenable#符号与 thenable
from .工具 import 求值,是否js表达式#表达式求值

def 更新错误(阶段,选项,原因):
    """把条目生命周期失败收成带原因的错误。"""
    if isinstance(原因,BaseException) and 原因.args:
        详情=原因.args[0] if isinstance(原因.args[0],str) else str(原因)#优先消息
    else:
        详情=str(原因)#非错误则字符串化
    错误=Exception('failed to '+阶段+' loader entry '+str(选项.get('id'))+' ('+str(选项.get('name'))+'): '+str(详情))#拼接消息
    if isinstance(原因,BaseException):
        错误.__cause__=原因#Error cause
    return 错误#抛给调用方

def 取出条目(对象,键列表):
    """按键顺序抽出并删除对象上的项。"""
    结果=[]#抽出的键值对
    for 键 in 键列表:
        if 键 not in 对象:
            continue#没有该键
        结果.append((键,对象[键]))#记下
        del 对象[键]#从原对象删除
    return 结果#抽出列表

def 排序键(对象,前置=None,后置=None):
    """把 id/name 提前、config 放最后，其余键按名排序。"""
    if 前置 is None:
        前置=['id','name']#默认前置
    if 后置 is None:
        后置=['config']#默认后置
    部分一=取出条目(对象,前置)#抽出前置键
    部分二=取出条目(对象,后置)#抽出后置键
    其余=取出条目(对象,list(对象.keys()))#抽出剩余
    def 键名(项):
        """排序用键名。"""
        return 项[0]#第一元是键
    其余.sort(key=键名)#按键名排序
    合并={}#按新顺序重建
    for 键,值 in 部分一+其余+部分二:
        合并[键]=值#写入
    对象.update(合并)#写回同一对象
    return 对象#原对象

def 替换键(目标,源):
    """清空目标自有键后再赋上源的键。"""
    目标.clear()#删掉全部自有键
    目标.update(源)#赋上源
    return 目标#同一对象

class 条目:
    """条目树里的一个已配置插件节点。"""
    键=全局符号('cordis.entry')#cordis.entry

    def __init__(自身,加载器):
        """创建条目上下文并派发 entry-init。"""
        自身.loader=加载器#所属加载器
        自身.ctx=加载器.ctx.extend({条目.键:自身})#带条目键的子上下文
        自身.context=自身.ctx#派发框架事件的上下文
        自身.fiber=None#插件光纤
        自身.parent=None#所属条目组
        自身.options={}#序列化选项
        自身.subgroup=None#嵌套组
        自身.subtree=None#嵌套树
        自身._初始化任务=None#进行中的导入任务
        自身._拆除中=0#拆除嵌套计数
        自身.context.emit('loader/entry-init',自身)#通知隔离钩子

    @property
    def id(自身):
        """含嵌套树前缀的稳定条目编号。"""
        from .树 import 条目树#条目树分隔符
        编号=自身.options['id']#本树内编号
        树光纤条目=getattr(自身.parent.tree.ctx.fiber,'entry',None)#树拥有者条目
        if 树光纤条目:
            编号=树光纤条目.id+条目树.分隔+编号#加上祖先前缀
        return 编号#完整编号

    @property
    def disabled(自身):
        """本条目或任一拥有方父条目被禁用时为真。"""
        return 自身._已禁用(自身.options)#按当前选项计算

    def _已禁用(自身,选项):
        """按给定选项计算有效禁用态。"""
        if 选项.get('group'):
            return False#组始终启用
        if 自身._禁用自(选项):
            return True#本层禁用
        条目对象=getattr(自身.parent.ctx.fiber,'entry',None)#父光纤条目
        while 条目对象:
            if 自身._禁用自(条目对象.options):
                return True#祖先禁用
            条目对象=getattr(条目对象.parent.ctx.fiber,'entry',None)#继续上溯
        return False#未禁用

    def _禁用自(自身,选项):
        """`!!js` 表达式对照加载器上下文求值；写回仍保留原节点。"""
        if 是否js表达式(选项.get('disabled')):
            禁用=选项.get('disabled')#原节点
            表达式=禁用['__jsExpr'] if isinstance(禁用,dict) else 禁用.__jsExpr#表达式
            return bool(自身.求值(表达式))#求值后取布尔
        return bool(选项.get('disabled'))#字面量布尔

    def 求值(自身,表达式):
        """对照本条目上下文求值表达式。"""
        return 求值(自身.ctx,表达式)#委托

    def _补丁上下文(自身,差异):
        """瀑布式补丁上下文，必要时按配置更新光纤。"""
        def 内层():
            """重绑原型并按需更新光纤配置。"""
            自身.ctx.__dict__['_原型上下文']=自身.parent.ctx#setPrototypeOf
            光纤=自身.fiber#当前光纤
            if 光纤 and 光纤.uid and ('config' in 差异 or 自身.options.get('group')):
                光纤.update(自身.options.get('config'),True)#不保存地更新配置
        自身.context.waterfall('loader/patch-context',自身,内层)#瀑布

    def 刷新(自身):
        """没有光纤且未禁用时启动条目。"""
        if 自身.fiber:
            return#已在运行
        if 自身.disabled:
            return#禁用
        自身.初始化()#导入并启动

    def _拆除(自身,光纤=None):
        """拆除指定光纤并维护拆除计数。"""
        if 光纤 is None:
            光纤=自身.fiber#默认当前光纤
        if not 光纤:
            return#没有光纤
        if 自身.fiber is 光纤:
            自身.fiber=None#摘掉当前指针
        自身._拆除中+=1#进入拆除
        try:
            结果=光纤.dispose()#拆除光纤
            if 是否thenable(结果):
                结果.等待()#等待异步拆除
        finally:
            自身._拆除中-=1#离开拆除

    def 更新(自身,选项,创建=False,强制=False):
        """合并新选项，按需重启，并通过父树持久化。"""
        先前选项=自身.options#提交前的对象
        遗留=dict(先前选项)#快照
        候选=选项 if 创建 else dict(先前选项)#创建则直接用传入对象
        if not 创建:
            for 键,值 in list(选项.items()):
                if cosmokit.是否可空(值):
                    候选.pop(键,None)#空值删除键
                else:
                    候选[键]=值#写入新值
        排序键(候选)#规范化键序
        差异=[键 for 键 in dict.fromkeys(list(候选.keys())+list(遗留.keys())) if not cosmokit.深度相等(候选.get(键),遗留.get(键))]#算出变化键
        if not 差异 and not 强制:
            return#无变化
        def 提交():
            """创建路径不改写原 options 对象身份。"""
            if 创建:
                return#创建不提交到先前对象
            自身.options=替换键(先前选项,候选)#原地替换键
        先前=自身.fiber#更新前的光纤
        if not (先前 and 先前.uid):
            自身.fiber=None#丢掉无编号光纤
            自身.options=候选#先用候选
            try:
                if not 自身._已禁用(候选):
                    自身.初始化()#启动
            except BaseException:
                自身.options=先前选项#回滚选项
                raise#继续抛
            提交()#提交到原对象
            return#无旧光纤路径结束
        if 自身._已禁用(候选):
            自身.options=候选#先用候选
            try:
                自身._拆除(先前)#拆除旧光纤
            except BaseException as 错误:
                自身.options=先前选项#回滚选项
                raise 更新错误('dispose',候选,错误)#拆除失败
            提交()#提交
            自身.context.emit('loader/partial-dispose',自身,遗留,True)#部分拆除
            return#禁用路径结束
        替换=any(键=='name' or 键=='inject' or 键=='group' for 键 in 差异)#需要换插件
        if not 替换:
            自身.options=候选#先用候选
            try:
                自身._补丁上下文(差异)#就地补丁
            except BaseException as 错误:
                自身.options=先前选项#回滚选项
                try:
                    自身._补丁上下文(差异)#按旧选项再补丁
                except BaseException as 回滚错误:
                    raise 更新错误('rollback',遗留,cordis.聚合错误([错误,回滚错误]))#回滚也失败
                自身.context.emit('loader/partial-dispose',自身,候选,True)#部分拆除
                raise 更新错误('apply',候选,错误)#应用失败
            提交()#提交
            自身.context.emit('loader/partial-dispose',自身,遗留,True)#部分拆除
            return#就地路径结束
        try:
            if 'name' in 差异:
                插件=自身.loader.解开导出(自身.parent.tree.导入(候选.get('name'),自身.取外层栈))#按新名导入
            else:
                运行时=先前.runtime#旧运行时
                插件=运行时['callback'] if isinstance(运行时,dict) else 运行时.callback#旧回调
        except BaseException as 错误:
            raise 更新错误('import',候选,错误)#导入失败
        运行时=先前.runtime#旧运行时
        先前插件=运行时['callback'] if isinstance(运行时,dict) else 运行时.callback#回滚用回调
        自身.options=候选#先用候选
        try:
            自身._拆除(先前)#拆除旧光纤
        except BaseException as 错误:
            自身.options=先前选项#回滚选项
            raise 更新错误('dispose',候选,错误)#拆除失败
        try:
            自身._启动(插件)#用新插件启动
        except BaseException as 错误:
            自身.options=先前选项#回滚选项
            try:
                自身._启动(先前插件)#用旧插件启动
            except BaseException as 回滚错误:
                raise 更新错误('rollback',遗留,cordis.聚合错误([错误,回滚错误]))#回滚也失败
            自身.context.emit('loader/partial-dispose',自身,候选,True)#部分拆除
            raise 更新错误('apply',候选,错误)#应用失败
        提交()#提交
        自身.context.emit('loader/partial-dispose',自身,遗留,True)#部分拆除

    def 取外层栈(自身):
        """拼出配置来源栈帧。"""
        条目对象=自身#从本条目上溯
        结果=[]#栈行
        while 条目对象:
            结果.append('    at '+str(条目对象.parent.tree.ctx.baseUrl)+'#'+str(条目对象.options.get('id')))#配置位置
            条目对象=getattr(条目对象.parent.ctx.fiber,'entry',None)#父条目
        return 结果#外层栈

    def 初始化(自身):
        """导入并启动已配置插件。"""
        try:
            自身._初始化任务=True#占位，供取任务看见
            自身._初始化()#实际导入启动
        finally:
            自身._初始化任务=None#结束占位
            if not 自身.loader.取任务():
                自身.ctx.reflect.通知(['loader'])#没有剩余任务则通知
        自身._等待()#等待光纤结算

    def _等待(自身):
        """等待光纤加载并在失败时改写成 apply 错误。"""
        try:
            光纤=自身.fiber#当前光纤
            if 光纤:
                光纤.等待()#等待结算
        except BaseException as 错误:
            raise 更新错误('apply',自身.options,错误)#应用失败

    def _初始化(自身):
        """导入插件并启动。"""
        try:
            插件=自身.loader.解开导出(自身.parent.tree.导入(自身.options.get('name'),自身.取外层栈))#导入
        except BaseException as 错误:
            raise 更新错误('import',自身.options,错误)#导入失败
        try:
            自身._启动(插件)#启动
        except BaseException as 错误:
            raise 更新错误('apply',自身.options,错误)#应用失败

    def _启动(自身,插件):
        """补丁上下文、登记插件并等待光纤。"""
        光纤=None#启动中的光纤
        try:
            自身._补丁上下文([])#先补丁
            自身.loader.显示日志(自身,'apply')#apply 日志
            光纤=自身.fiber=自身.ctx.registry.plugin(插件,自身.options.get('config'),自身.取外层栈)#启动插件
            光纤.等待()#等待加载
        except BaseException:
            自身._拆除(光纤)#失败则拆除
            raise#继续抛

Entry=条目#英文别名
条目.key=条目.键#英文别名
条目.evaluate=条目.求值#英文别名
条目.refresh=条目.刷新#英文别名
条目.update=条目.更新#英文别名
条目.init=条目.初始化#英文别名
条目.getOuterStack=条目.取外层栈#英文别名
条目._dispose=条目._拆除#英文别名
条目._await=条目._等待#英文别名

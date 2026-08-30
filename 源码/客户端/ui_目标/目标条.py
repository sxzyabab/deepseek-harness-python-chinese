"""目标条与坞适配器。



对齐上游 `ui-goal/src/client/GoalBar.tsx`。公开面仅中文名。

加载/缺席/完成目标不渲染；变更动词来自 inject，实时状态来自投影。

"""

from ...依赖 import cordis#外部依赖胶水


__all__=['目标条','目标坞','阶段标签键']#仅中文公开名



阶段标签键={#可见阶段 → 文案键

    'active':'phase.active',#进行中

    'paused':'phase.paused',#已暂停

    'blocked':'phase.blocked',#受阻

}#阶段键结束



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



class 目标条:#输入坞目标指示条

    """进行中/暂停/受阻目标的条与内联编辑。"""

    def __init__(自身,属性):#按合成 props 构造

        """记下 props。"""

        自身.属性=属性#合成 props

        自身.编辑中=False#是否编辑

        自身.草稿=''#编辑草稿

        自身.进行中=False#动作进行中

        自身.动作错误=None#失败行

        自身.已清目标标识=None#本地已清 id

        自身.存活=True#实例存活



    def 更新(自身,属性):#props 变更

        """目标身份变化时重置本地编辑态。"""

        旧标识=取字段(取字段(自身.属性,'goal'),'id')#旧 id

        自身.属性=属性#最新

        新标识=取字段(取字段(自身.属性,'goal'),'id')#新 id

        if 旧标识!=新标识:#身份变

            自身.编辑中=False#退出编辑

            自身.动作错误=None#清错误

            自身.已清目标标识=None#清本地清标记



    def 卸载(自身):#卸载

        """标死。"""

        自身.存活=False#死



    def 跑动作(自身,动作):#串行 CAS 守卫

        """同一时刻只跑一个变更；返回结果或 None。"""

        if 自身.进行中:#已在跑

            return None#丢弃

        自身.进行中=True#上锁

        自身.动作错误=None#清错误

        try:#执行

            结果=解开(动作())#结算

        except Exception as 原因:#拒绝

            if 自身.存活:#仍活

                自身.进行中=False#解锁

                自身.动作错误=str(原因)#文案

            return None#失败

        if not 自身.存活:#已死

            return None#丢弃

        自身.进行中=False#解锁

        if not 取字段(结果,'ok'):#业务失败

            错误=取字段(结果,'error') or {}#错误

            自身.动作错误=f"{取字段(错误,'message')} ({取字段(错误,'code')})"#失败行

        return 结果#结果



    def 保存编辑(自身):#提交草稿

        """空草稿不提交。"""

        修剪=自身.草稿.strip()#修剪

        if 修剪=='':#空

            return#结束

        编辑=取字段(自身.属性,'onEdit')#动词

        结果=自身.跑动作(lambda:编辑(修剪))#跑

        if 取字段(结果,'ok'):#成功

            自身.编辑中=False#退出



    def 清除(自身,已清标识):#清除目标

        """成功后记下本地已清 id。"""

        清除动词=取字段(自身.属性,'onClear')#动词

        结果=自身.跑动作(清除动词)#跑

        if 取字段(结果,'ok'):#成功

            自身.已清目标标识=已清标识#记下



    def 开始编辑(自身):#进入编辑

        """草稿取当前目标陈述。"""

        目标=取字段(自身.属性,'goal')#目标

        自身.草稿=取字段(目标,'objective') or ''#草稿

        自身.编辑中=True#编辑中



    def 取消编辑(自身):#取消

        """退出编辑。"""

        自身.编辑中=False#退出



    def 视图(自身):#读视图模型

        """加载/缺席/完成/已清返回 None。"""

        目标=取字段(自身.属性,'goal')#目标

        if 目标 is None or 目标 is False:#缺席——上游用 null/undefined；此处 None 含两者

            return None#不渲染

        if 取字段(目标,'phase')=='complete':#完成

            return None#不渲染

        if 取字段(目标,'id')==自身.已清目标标识:#本地已清

            return None#不渲染

        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案

        if 自身.编辑中:#编辑态

            return {#编辑视图

                'mode':'edit',#模式

                'draft':自身.草稿,#草稿

                'pending':自身.进行中,#进行中

                'error':自身.动作错误,#错误

                'objectiveAria':翻译('objective.aria'),#无障碍

                'saveLabel':翻译('action.save'),#保存

                'cancelLabel':翻译('action.cancel'),#取消

                'saveDisabled':自身.进行中 or 自身.草稿.strip()=='',#禁用保存

            }#编辑结束

        阶段=取字段(目标,'phase')#阶段

        受阻理由=取字段(目标,'blockedReason')#受阻

        return {#条视图

            'mode':'bar',#模式

            'phase':阶段,#阶段

            'label':翻译(阶段标签键.get(阶段,'phase.active')),#阶段标签

            'objective':取字段(目标,'objective'),#陈述

            'title':取字段(受阻理由,'message') if 阶段=='blocked' else None,#悬停

            'pending':自身.进行中,#进行中

            'error':自身.动作错误,#错误

            'showPause':阶段=='active',#暂停钮

            'showResume':阶段=='paused',#恢复钮

            'pauseLabel':翻译('action.pause'),#暂停文案

            'resumeLabel':翻译('action.resume'),#恢复文案

            'editLabel':翻译('action.edit'),#编辑文案

            'clearLabel':翻译('action.clear'),#清除文案

            'goalId':取字段(目标,'id'),#id

        }#条结束



    def 暂停(自身):#暂停

        """跑 onPause。"""

        自身.跑动作(取字段(自身.属性,'onPause'))#跑



    def 恢复(自身):#恢复

        """跑 onResume。"""

        自身.跑动作(取字段(自身.属性,'onResume'))#跑



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图



class 目标坞:#坞适配器

    """读 host 计算的 goal 投影；缺席或 null 不渲染。"""

    def __init__(自身,属性):#构造

        """记下 props 并建内嵌目标条。"""

        自身.属性=属性#合成 props

        自身.条=目标条(自身.条属性())#内嵌条



    def 条属性(自身):#合成 GoalBar props

        """从投影取 goal 快照。"""

        用投影=取字段(自身.属性,'useProjection')#投影

        投影=用投影('goal') if 用投影 is not None else None#goal 投影

        if 投影 is None:#缺席

            目标=None#无

        else:#有投影值

            目标=取字段(投影,'goal')#快照；投影为 null 时取字段得 None

        return {#条 props

            'goal':目标,#目标

            'onEdit':取字段(自身.属性,'onEdit'),#编辑

            'onPause':取字段(自身.属性,'onPause'),#暂停

            'onResume':取字段(自身.属性,'onResume'),#恢复

            'onClear':取字段(自身.属性,'onClear'),#清除

            't':取字段(自身.属性,'t',lambda 键,_=None:键),#文案

        }#props 结束



    def 更新(自身,属性):#props 变更

        """刷新并同步内嵌条。"""

        自身.属性=属性#最新

        自身.条.更新(自身.条属性())#同步



    def 卸载(自身):#卸载

        """拆内嵌条。"""

        自身.条.卸载()#拆



    def __call__(自身,属性=None):#组件调用形

        """返回目标条视图。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.条()#条视图



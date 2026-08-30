"""计划模式状态芯片。



对齐上游 `ui-plan/src/client/PlanModeControl.tsx`。公开面仅中文名。

有效目标是计划模式时渲染，并经 exitPlanMode 执行 /plan off。

"""

from ...依赖 import cordis#外部依赖胶水


__all__=['计划芯片']#仅中文公开名



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



class 计划芯片:#composer 计划席位组件

    """只在有效目标为计划模式时渲染；点击执行 /plan off。"""

    def __init__(自身,属性):#按合成 props 构造

        """记下 props。"""

        自身.属性=属性#合成 props

        自身.离开中=False#正在退出

        自身.错误=None#失败行

        自身.存活=True#实例存活



    def 更新(自身,属性):#props 变更

        """刷新合成 props。"""

        自身.属性=属性#最新



    def 卸载(自身):#卸载

        """标死。"""

        自身.存活=False#死



    def 关闭计划(自身):#执行 /plan off

        """无 leaving/locked 守卫：两者会禁用按钮。"""

        自身.离开中=True#离开中

        自身.错误=None#清错误

        退出=取字段(自身.属性,'exitPlanMode')#退出动作

        try:#执行

            失败=解开(退出()) if 退出 is not None else None#结算

        except Exception as 原因:#拒绝

            if not 自身.存活:#已死

                return#丢弃

            自身.离开中=False#结束

            自身.错误=str(原因)#文案

            return#结束

        if not 自身.存活:#已死

            return#丢弃

        自身.离开中=False#结束

        自身.错误=失败#失败行或 None



    def 视图(自身):#读视图模型

        """投影缺席或非目标则 None。"""

        用投影=取字段(自身.属性,'useProjection')#投影选择器

        if 用投影 is None:#无

            return None#不渲染

        计划=用投影('plan')#plan 投影

        if 计划 is None:#缺席

            return None#不渲染

        进行中=取字段(计划,'pending')#待定翻转

        活动=取字段(计划,'active')#当前活动

        目标=(not 活动) if 进行中 else 活动#有效目标

        if not 目标:#非计划模式

            return None#不渲染

        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案

        锁定=取字段(自身.属性,'locked')#锁定

        return {#视图

            'aria':翻译('chip.on.aria'),#无障碍名

            'title':翻译('chip.on.title'),#悬停

            'disabled':bool(锁定) or 自身.离开中,#禁用

            'error':自身.错误,#失败行

            'leaving':自身.离开中,#离开中

        }#视图结束



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用；返回视图或 None。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图



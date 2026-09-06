"""目标条与坞适配器。

对齐上游 `ui-goal/src/client/GoalBar.tsx`。公开面仅中文名。
加载/缺席/完成目标不渲染；变更动词来自 inject，实时状态来自投影。
"""

__all__=['目标条','目标坞','阶段标签键']#仅中文公开名

阶段标签键={#可见阶段 → 文案键
    'active':'phase.active',#进行中
    'paused':'phase.paused',#已暂停
    'blocked':'phase.blocked',#受阻
}#阶段键结束

def 缺省翻译(键,_插值=None):#无文案函数
    """原样返回键。"""
    return 键#键

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
        旧目标=自身.属性['goal'] if 'goal' in 自身.属性 else None#旧目标
        旧标识=旧目标['id'] if 旧目标 is not None and 'id' in 旧目标 else None#旧 id
        自身.属性=属性#最新
        新目标=属性['goal'] if 'goal' in 属性 else None#新目标
        新标识=新目标['id'] if 新目标 is not None and 'id' in 新目标 else None#新 id
        if 旧标识!=新标识:#身份变
            自身.编辑中=False#退出编辑
            自身.动作错误=None#清错误
            自身.已清目标标识=None#清本地清标记

    def 卸载(自身):#卸载
        """标死。"""
        自身.存活=False#死

    def 执行动作(自身,动作):#串行 CAS 守卫
        """同一时刻只跑一个变更；返回结果或 None。"""
        if 自身.进行中:#已在跑
            return None#丢弃
        自身.进行中=True#上锁
        自身.动作错误=None#清错误
        try:#执行
            结果=动作()#注入面已等待
        except Exception as 原因:#拒绝；RPC 异常契约未定，传输层抛出类型未收窄，故不能换成更窄的 except
            if 自身.存活:#仍活
                自身.进行中=False#解锁
                自身.动作错误=str(原因)#文案
            return None#失败
        if not 自身.存活:#已死
            return None#丢弃
        自身.进行中=False#解锁
        if 结果 is None or not 结果['ok']:#业务失败
            错误=结果['error'] if 结果 is not None and 'error' in 结果 and 结果['error'] is not None else {}#错误
            消息=错误['message'] if 'message' in 错误 else None#消息
            码=错误['code'] if 'code' in 错误 else None#码
            自身.动作错误=f"{消息} ({码})"#失败行
        return 结果#结果

    def 保存编辑(自身):#提交草稿
        """空草稿不提交。"""
        修剪=自身.草稿.strip()#修剪
        if 修剪=='':#空
            return#结束
        编辑=自身.属性['onEdit'] if 'onEdit' in 自身.属性 else None#动词
        def 提交编辑():#带草稿的编辑
            """调用 onEdit。"""
            return 编辑(修剪)#提交
        结果=自身.执行动作(提交编辑)#跑
        if 结果 is not None and 结果['ok']:#成功
            自身.编辑中=False#退出

    def 清除(自身,已清标识):#清除目标
        """成功后记下本地已清 id。"""
        清除动词=自身.属性['onClear'] if 'onClear' in 自身.属性 else None#动词
        结果=自身.执行动作(清除动词)#跑
        if 结果 is not None and 结果['ok']:#成功
            自身.已清目标标识=已清标识#记下

    def 开始编辑(自身):#进入编辑
        """草稿取当前目标陈述。"""
        目标=自身.属性['goal'] if 'goal' in 自身.属性 else None#目标
        自身.草稿=目标['objective'] if 目标 is not None and 'objective' in 目标 and 目标['objective'] is not None else ''#草稿
        自身.编辑中=True#编辑中

    def 取消编辑(自身):#取消
        """退出编辑。"""
        自身.编辑中=False#退出

    def 视图(自身):#读视图模型
        """加载/缺席/完成/已清返回 None。"""
        目标=自身.属性['goal'] if 'goal' in 自身.属性 else None#目标
        if 目标 is None:#缺席
            return None#不渲染
        if 'phase' in 目标 and 目标['phase']=='complete':#完成
            return None#不渲染
        if 'id' in 目标 and 目标['id']==自身.已清目标标识:#本地已清
            return None#不渲染
        翻译=自身.属性['t'] if 't' in 自身.属性 and 自身.属性['t'] is not None else 缺省翻译#文案
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
        阶段=目标['phase'] if 'phase' in 目标 else None#阶段
        受阻理由=目标['blockedReason'] if 'blockedReason' in 目标 else None#受阻
        标签键=阶段标签键[阶段] if 阶段 in 阶段标签键 else 'phase.active'#阶段文案键
        return {#条视图
            'mode':'bar',#模式
            'phase':阶段,#阶段
            'label':翻译(标签键),#阶段标签
            'objective':目标['objective'] if 'objective' in 目标 else None,#陈述
            'title':受阻理由['message'] if 阶段=='blocked' and 受阻理由 is not None and 'message' in 受阻理由 else None,#悬停
            'pending':自身.进行中,#进行中
            'error':自身.动作错误,#错误
            'showPause':阶段=='active',#暂停钮
            'showResume':阶段=='paused',#恢复钮
            'pauseLabel':翻译('action.pause'),#暂停文案
            'resumeLabel':翻译('action.resume'),#恢复文案
            'editLabel':翻译('action.edit'),#编辑文案
            'clearLabel':翻译('action.clear'),#清除文案
            'goalId':目标['id'] if 'id' in 目标 else None,#id
        }#条结束

    def 暂停(自身):#暂停
        """跑 onPause。"""
        自身.执行动作(自身.属性['onPause'] if 'onPause' in 自身.属性 else None)#跑

    def 恢复(自身):#恢复
        """跑 onResume。"""
        自身.执行动作(自身.属性['onResume'] if 'onResume' in 自身.属性 else None)#跑

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
        用投影=自身.属性['useProjection'] if 'useProjection' in 自身.属性 else None#投影
        投影=用投影('goal') if 用投影 is not None else None#goal 投影
        if 投影 is None:#缺席
            目标=None#无
        else:#有投影值
            目标=投影['goal'] if 'goal' in 投影 else None#快照
        翻译=自身.属性['t'] if 't' in 自身.属性 and 自身.属性['t'] is not None else 缺省翻译#文案
        return {#条 props
            'goal':目标,#目标
            'onEdit':自身.属性['onEdit'] if 'onEdit' in 自身.属性 else None,#编辑
            'onPause':自身.属性['onPause'] if 'onPause' in 自身.属性 else None,#暂停
            'onResume':自身.属性['onResume'] if 'onResume' in 自身.属性 else None,#恢复
            'onClear':自身.属性['onClear'] if 'onClear' in 自身.属性 else None,#清除
            't':翻译,#文案
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

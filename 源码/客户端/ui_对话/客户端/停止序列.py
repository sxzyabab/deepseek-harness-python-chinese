"""双击 Escape 取消：两次独立按键必须落在同一 Conversation 实例与同一活跃回合。
仅接受已解析的取消目标；occurrence 与 region 用来锁定焦点归属，避免串会话。
"""
import builtins#页面全局

__all__=['停止目标','停止序列']#仅中文公开名

窗口=builtins.window#定时器宿主
性能=builtins.performance#单调时钟

def 停止目标(会话标识,回合,代际,区域,取消):
    """刚解析出的取消目标；代际与区域保住焦点归属。"""
    return {'sessionId':会话标识,'turn':回合,'generation':代际,'region':区域,'cancel':取消}#目标

class 停止序列:
    """短命的第一下按键；真正取消跑起来之前必须清掉。"""
    def __init__(自身,间隔毫秒,释放):
        """间隔毫秒为两下按键允许的最大间隔；释放卸掉第一下挂住的观察。"""
        自身.间隔毫秒=间隔毫秒#已校验间隔
        自身.释放=释放#释放观察
        自身.第一下=None#待确认的第一下
        自身.定时器=None#过期定时器

    def 重置(自身):
        """清掉第一下按键及其过期定时器。"""
        自身.第一下=None#清目标
        窗口.clearTimeout(自身.定时器)#清定时器
        自身.定时器=None#卸句柄
        自身.释放()#释放观察

    def 按下(自身,目标):
        """接受一次合格、非重复的 Escape，对照刚解析的当前状态；返回本下是否已请求取消。"""
        第一下=自身.第一下#先前第一下
        自身.重置()#先清旧态
        if (第一下 is not None and 性能.now()<=第一下['deadline']
            and 第一下['target']['sessionId']==目标['sessionId']
            and 第一下['target']['turn']==目标['turn']
            and 第一下['target']['generation'] is 目标['generation']
            and 第一下['target']['region'] is 目标['region']):#成对
            目标['cancel']()#实际取消
            return True#已取消
        自身.第一下={'target':目标,'deadline':性能.now()+自身.间隔毫秒}#记下第一下
        def 到期():
            """间隔过后作废第一下。"""
            自身.重置()#过期清掉
        自身.定时器=窗口.setTimeout(到期,自身.间隔毫秒+1)#过期定时
        return False#未成对

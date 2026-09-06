"""助手推理披露行（Think 变体），独立于工具行。

对齐上游 `ui-conversation/src/client/chat/ReasoningRow.tsx`。公开面仅中文名。
流式跟末行并节流滚摘要；定稿取首行。
属性为 dict。
"""
from .节流视觉更新 import 节流视觉更新#摘要跟尾节流

__all__=['推理行','首行','末行']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 首行(文本):
    """取第一行。"""
    换行=文本.find('\n')#换行
    return 文本 if 换行==-1 else 文本[:换行]#首行

def 末行(文本):
    """取末可见行。"""
    可见=文本.rstrip()#去尾空白
    换行=可见.rfind('\n')#末换行
    return 可见 if 换行==-1 else 可见[换行+1:]#末行

class 推理行:
    """流式跟末行；定稿取首行。"""

    def __init__(自身,属性=None):
        """记下 props、展开与摘要滚调度。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.展开=False#展开
        自身.摘要滚=节流视觉更新(None)#宿主绑对齐后再调度

    def 更新(自身,属性):
        """刷新并请求摘要滚。"""
        自身.属性=属性 if 属性 is not None else {}#新
        自身.摘要滚.调度()#跟尾/回零

    def 设摘要滚(自身,对齐):
        """每次渲染写最新对齐回调。"""
        自身.摘要滚.设更新(对齐)#绑
        自身.摘要滚.调度()#排

    def 切换(自身):
        """翻转。"""
        自身.展开=not 自身.展开#翻

    def 渲染(自身):
        """DisclosureRow 形。"""
        属性=自身.属性#props
        文本=属性['text'] if 'text' in 属性 and 属性['text'] is not None else ''#文
        运行中=属性['running'] is True if 'running' in 属性 else False#流式
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        摘要=末行(文本) if 运行中 is True else 首行(文本)#摘要
        自身.摘要滚.调度()#跟 running/summary
        return {#行
            'type':'reasoning-row',#类型
            'className':'root',#根
            'data-variant':'think',#变体
            'data-state':'running' if 运行中 is True else 'ok',#态
            'runningA11y':翻译('row.running') if 运行中 is True else None,#无障碍
            'title':'Think',#标题
            'open':自身.展开,#开
            'expandable':True,#可展
            'summary':摘要,#摘要
            'followEnd':运行中,#跟尾
            'body':文本,#体
            'onToggle':自身.切换,#切换
            'scheduleSummaryScroll':自身.设摘要滚,#滚绑
            'tickSummaryScroll':自身.摘要滚.滴答,#帧滴答
            'cssModule':'聊天/推理行.module.css',#样式
            'a11yModule':'聊天/无障碍.module.css',#无障碍样式
        }#结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

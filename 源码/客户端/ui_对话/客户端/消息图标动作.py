"""用户/助手 IconActions 行：复制、可选分支、日期感知时钟。

对齐上游 `ui-conversation/src/client/chat/MessageIconActions.tsx`。公开面仅中文名。
"""
from .消息铬 import 格式化延迟秒,格式化消息时钟,格式化运行时长,格式化每秒令牌,本地日起点,距下一本地午夜毫秒#时钟辅助
import time as 时间模块,threading#墙钟与后台观察

__all__=['消息图标动作','日历日']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 日历日(现在=None):#本地日历日午夜
    """对齐 useCalendarDay 的当前值面（无定时器）。"""
    if 现在 is None:#缺省
        现在=int(时间模块.time()*1000)#毫秒
    return 本地日起点(现在)#午夜

class 消息图标动作:#复制/分支/时钟行
    """共享用户与助手铬。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与复制态。"""
        自身.属性=属性 or {}#合成
        自身.已复制=False#成功铬
        自身.复制中=False#防重入

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 复制(自身):#写剪贴板
        """成功则短时勾。"""
        if 自身.已复制 or 自身.复制中:#忙
            return#停
        文本=取字段(自身.属性,'text') or ''#文本
        写=取字段(自身.属性,'writeClipboard')#宿主写
        自身.复制中=True#闩
        def 完成(成功):#收尾
            """成功亮勾。"""
            自身.复制中=False#清
            if 成功:#成
                自身.已复制=True#勾
        if 写 is None:#无宿主则视为成功（视图层自接）
            完成(True)#成
            return#停
        结果=写(文本)#写
        if hasattr(结果,'wait') or hasattr(结果,'等待'):#可等待
            def 观察():#观察写剪贴板
                """成功则亮勾。"""
                try:#等待
                    值=结果.wait() if hasattr(结果,'wait') else 结果.等待()#结算
                    完成(bool(值))#收尾
                except BaseException:#失败
                    完成(False)#失败
            threading.Thread(target=观察,daemon=True).start()#挂观察
        else:#同步
            完成(bool(结果))#成

    def 清除复制铬(自身):#超时清勾
        """1s 窗后调用。"""
        自身.已复制=False#清

    def 渲染(自身):#结构树
        """时钟位 + 复制 + 额外 + 分支。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        时间=取字段(属性,'time')#时刻
        时钟位=取字段(属性,'clock') or 'start'#位
        日=取字段(属性,'calendarDay')#日席
        if 日 is None:#缺省
            日=日历日()#本日
        时钟=None#时钟元
        if 时间 is not None:#有时
            段=[格式化消息时钟(时间,翻译,日)]#时钟
            运行=取字段(属性,'runMs')#运行
            if 运行 is not None:#有
                段.append(翻译('message.ranFor',{'duration':格式化运行时长(运行,翻译)}))#Ran for
            首=取字段(属性,'ttftMs')#TTFT
            if 首 is not None:#有
                段.append(翻译('message.ttft',{'seconds':格式化延迟秒(首)}))#TTFT
            吞吐=取字段(属性,'tokensPerSecond')#吞吐
            if 吞吐 is not None:#有
                段.append(翻译('message.tokensPerSecond',{'tps':格式化每秒令牌(吞吐)}))#tok/s
            时钟={'side':时钟位,'parts':段}#时钟
        不可分支=bool(取字段(属性,'branchUnavailable'))#不可
        分支=取字段(属性,'onBranch')#分支
        return {#视图
            'type':'message-icon-actions',#类型
            'clock':时钟,#时钟
            'copied':自身.已复制,#勾
            'copyLabel':翻译('copied') if 自身.已复制 else 翻译('copy'),#复制标
            'onCopy':自身.复制,#复制
            'extraActions':取字段(属性,'extraActions'),#额外
            'branch':None if 分支 is None else {#分支
                'unavailable':不可分支,#不可
                'label':翻译('message.branchUnavailable') if 不可分支 else 翻译('message.branch'),#标
                'onClick':None if 不可分支 else 分支,#点
                'reason':翻译('message.branchUnavailable') if 不可分支 else None,#原因
            },#分支结束
            'className':取字段(属性,'className'),#布局类
            'cssModule':'消息图标动作.module.css',#样式
            'nextMidnightMs':距下一本地午夜毫秒(日),#午夜滴答
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

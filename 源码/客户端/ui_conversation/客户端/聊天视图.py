"""默认会话视图：稳定键列表、分页、待定 steering、贴底跟随。

对齐上游 `ui-conversation/src/client/chat/ChatView.tsx`。公开面仅中文名。
"""
from .聊天节点席 import 聊天节点席#节点席
from .消息项 import 待插话泡#pending steering
from .消息铬 import 格式化运行时长#回合时钟
import time as 时间模块#墙钟

__all__=['聊天视图','跟随阈值','运行回合起始','运行回合起点','回合状态','格式运行时长']#仅中文公开名

跟随阈值=24#贴底阈值像素

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 运行回合起始(时间线):#开着的回合 start.time
    """多开回合取最新。"""
    if 时间线 is None:#无
        return None#无
    回合们=取字段(时间线,'turns')#表
    if 回合们 is None:#无
        return None#无
    值们=getattr(回合们,'values',None)#values
    迭代=值们() if callable(值们) else (回合们.values() if isinstance(回合们,dict) else [])#遍历
    最新=None#最新
    for 回合 in 迭代:#扫
        if 取字段(回合,'status')=='open' and 取字段(回合,'start') is not None:#开
            最新=取字段(取字段(回合,'start'),'time')#时
    return 最新#最新

运行回合起点=运行回合起始#别名兼容
格式运行时长=格式化运行时长#别名兼容
def 回合状态(起始时,翻译,现在=None):#Deep diving 行
    """满 15s 显示时钟。"""
    if 现在 is None:#缺省
        现在=int(时间模块.time()*1000)#毫秒
    锚=起始时 if 起始时 is not None else 现在#锚
    经过=max(0,现在-锚)#毫秒
    return {#视图
        'type':'turn-status',#类型
        'label':'Deep diving...',#标签
        'showClock':经过>=15000,#时钟
        'clock':格式化运行时长(经过,翻译) if 经过>=15000 else None,#时长
        'cssModule':'聊天视图.module.css',#样式
    }#结束

class 聊天视图:#conversation.view chat 条目
    """有序 Node 列表 + 滚动语义面。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与滚动态。"""
        自身.属性=属性 or {}#合成
        自身.贴底=True#跟随
        自身.已打开=False#首开跳底
        自身.观测顶=0#程序写顶
        自身.分页锚=None#分页锚
        自身.首序号=None#首 seq
        自身.末键=None#末键
        自身.末转向标识=None#末 steering
        自身.跟随签名=None#跟随签名

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 滚到底(自身):#强制贴底
        """清锚并标记贴底。"""
        自身.分页锚=None#清
        自身.贴底=True#贴
        存=取字段(取字段(自身.属性,'chatScroll'),'save')#存
        if 存 is not None:#有
            存(None)#清记忆

    def 加载更早锚定(自身):#分页前记锚
        """记下当前可见锚后调 loadOlder。"""
        加载=取字段(自身.属性,'loadOlder')#加载
        if 加载 is not None:#有
            加载()#派发

    def 渲染(自身):#结构树
        """列表行 + 状态 + steering + 回底钮。"""
        属性=自身.属性#props
        用会话=取字段(属性,'useSession')#会话
        用会话们=取字段(属性,'useSessions')#列表
        用仓=取字段(属性,'useStore')#仓
        渲染槽=取字段(属性,'renderSlot',lambda *_a,**_k:None)#槽
        会话标识=取字段(属性,'sessionId')#会话
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        def 读(选,缺省=None):#安全读会话
            """钩缺席则缺省。"""
            if 用会话 is None:#无
                return 缺省#缺
            return 用会话(选)#投影
        序=读(lambda s:取字段(取字段(s,'chat'),'order') or [],[])#序
        节点表=读(lambda s:取字段(取字段(s,'chat'),'nodes'))#节点表
        时间线=读(lambda s:取字段(取字段(s,'chat'),'timeline'))#时间线
        收件=读(lambda s:取字段(s,'queue') or [],[])#队列
        运行中=读(lambda s:取字段(s,'running'),False)#运行
        打开态=读(lambda s:取字段(s,'openState'),'cold')#打开
        打开错=读(lambda s:取字段(s,'openError'))#打开错
        还有更早=读(lambda s:取字段(s,'hasMore'),False)#更早
        加载更早中=读(lambda s:取字段(s,'loadingOlder'),False)#加载中
        工作目录=用会话们(lambda s:取字段(取字段(取字段(s,'byId'),会话标识),'cwd')) if 用会话们 is not None else None#cwd
        选中调用=用仓(lambda s:取字段(取字段(s,'selection'),'callId')) if 用仓 is not None else None#选中
        待定转向=[项 for 项 in 收件 if 取字段(项,'placement')=='steering']#steering
        运行起始=运行回合起始(时间线)#起始
        席们=[]#行
        for 节点键 in 序:#逐键
            席=聊天节点席({#席 props
                'nodeKey':节点键,#键
                'useSession':用会话,#会话
                'selectedCallId':选中调用,#选中
                'cwd':工作目录,#cwd
                'openFile':取字段(属性,'openFile'),#打开
                'inspectCall':取字段(属性,'inspectCall'),#检视
                'forkAt':取字段(属性,'forkAt'),#分叉
                'loadImage':取字段(属性,'loadImage'),#载图
                'fileMentions':取字段(属性,'fileMentions'),#提及
                'renderSlot':渲染槽,#槽
                't':翻译,#文案
            })()#渲
            if 席 is not None:#有
                席们.append(席)#入
        转向行=[]#steering 行
        for 项 in 待定转向:#扫
            转向行.append({'id':取字段(项,'id'),'view':待插话泡({'content':取字段(项,'content') or [],'loadImage':取字段(属性,'loadImage'),'t':翻译})()})#行
        return {#视图
            'type':'chat-view',#类型
            'openState':打开态,#打开态
            'loadingHint':翻译('chat.loadingHistory') if 打开态=='loading' else None,#加载
            'openError':None if 打开态!='error' or 打开错 is None else 翻译('chat.loadError',{'message':取字段(打开错,'message'),'code':取字段(打开错,'code')}),#打开错
            'hasMore':还有更早,#更早
            'loadingOlder':加载更早中,#加载中
            'loadOlderLabel':翻译('loading') if 加载更早中 else 翻译('chat.loadOlder'),#分页标
            'onLoadOlder':自身.加载更早锚定,#分页
            'seats':席们,#节点席
            'turnStatus':回合状态(运行起始,翻译) if 运行中 else None,#回合态
            'pendingSteering':转向行,#steering
            'atBottom':自身.贴底,#贴底
            'toBottomLabel':翻译('chat.toBottom'),#回底
            'onToBottom':自身.滚到底,#回底
            'cssModule':'聊天视图.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

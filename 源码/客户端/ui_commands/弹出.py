"""无头 popupSelect 外壳状态与过滤。

对齐上游 `ui-commands/src/client/popup.ts`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定

__all__=['过滤选项','弹出选择控制器','关闭态']#仅中文公开名

关闭态={#关闭快照
    'open':False,'command':None,'status':'pending','options':[],'search':'','active':0,
    'submitting':False,'confirming':None,'acknowledged':False,'error':None,
}#结束

def 过滤选项(选项们,搜索):#按本地搜索过滤
    """标签与详情不区分大小写子串；空白保留全部。"""
    查询=搜索.strip().lower()#查询
    if 查询=='':#空
        return list(选项们)#全部
    出=[]#结果
    for 项 in 选项们:#逐行
        标=str(项.get('label') or '').lower()#标签
        详=str(项.get('detail') or '').lower()#详情
        if 查询 in 标 or 查询 in 详:#命中
            出.append(项)#加
    return 出#过滤后

def 错误文(错误):#失败值收成文案
    """Error 取 message，其余 String。"""
    if isinstance(错误,BaseException) and 错误.args:#异常
        return str(错误.args[0])#消息
    return str(错误)#其它

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

class 简易快照仓:#快照仓
    """订阅 + set。"""
    def __init__(自身,初始):#初始
        """记下状态。"""
        自身.状态=dict(初始)#可变
        自身.订阅们=[]#监听

    def getSnapshot(自身):#读
        """浅拷贝。"""
        return dict(自身.状态)#拷贝

    def subscribe(自身,听):#订阅
        """返回拆除器。"""
        自身.订阅们.append(听)#登记
        def 拆():#拆除
            """去掉。"""
            if 听 in 自身.订阅们:#仍在
                自身.订阅们.remove(听)#删
        return 拆#拆除器

    def set(自身,下一):#整表替换
        """写快照并广播。"""
        自身.状态=dict(下一)#替换
        for 听 in list(自身.订阅们):#广播
            听()#回调

class 弹出选择控制器:#一会话一个弹出选择控制器
    """打开/过滤/选定/确认/关闭。"""
    def __init__(自身,依赖):#注入会话接线
        """记下 consume/focusComposer。"""
        自身.依赖=依赖#接线
        自身.state=简易快照仓(关闭态)#状态仓
        自身.绑定=None#当前打开绑定

    def open(自身,命令,规格,上下文,片段):#打开外壳
        """取代上一层；发布 pending 并拉选项。"""
        if 自身.绑定 is not None:#有旧
            中止=自身.绑定.get('abort')#中止器
            if 中止 is not None:#有
                中止()#中止
        绑定={'command':命令,'spec':规格,'context':上下文,'segment':片段,'abort':lambda:None,'aborted':False}#绑定
        def 中止本次():#中止标记
            """标 aborted。"""
            绑定['aborted']=True#中止
        绑定['abort']=中止本次#写入
        自身.绑定=绑定#记下
        开={**关闭态,'open':True,'command':命令}#pending 打开
        自身.state.set(开)#发布
        自身._加载(绑定)#拉选项

    def _加载(自身,绑定):#按绑定拉一次选项
        """结算权随绑定一起死。"""
        try:#加载
            选项=解开(绑定['spec']['options'](绑定['context'],None))#拉
            if 自身.绑定 is not 绑定:#已换
                return#丢弃
            现=自身.state.getSnapshot()#现
            现.update({'status':'ready','options':list(选项),'active':0,'error':None})#就绪
            自身.state.set(现)#写
        except Exception as 错误:#失败
            if 自身.绑定 is not 绑定:#已换
                return#丢弃
            现=自身.state.getSnapshot()#现
            现.update({'status':'failed','options':[],'active':0,'error':错误文(错误)})#失败
            自身.state.set(现)#写

    def retry(自身):#失败后重拉
        """除非 status 为 failed 否则空操作。"""
        绑定=自身.绑定#绑定
        态=自身.state.getSnapshot()#快照
        if 绑定 is None or not 态['open'] or 态['status']!='failed':#不可
            return#忽略
        态.update({'status':'pending','error':None})#pending
        自身.state.set(态)#写
        自身._加载(绑定)#再拉

    def setSearch(自身,搜索):#改本地搜索
        """纯本地过滤。"""
        态=自身.state.getSnapshot()#快照
        if not 态['open'] or 态['submitting'] or 态['confirming'] is not None or 搜索==态['search']:#不可
            return#忽略
        态.update({'search':搜索,'active':0})#写搜索
        自身.state.set(态)#发布

    def move(自身,方向):#环绕移动高亮
        """+1 下 / -1 上。"""
        态=自身.state.getSnapshot()#快照
        if not 态['open'] or 态['status']!='ready' or 态['submitting'] or 态['confirming'] is not None:#不可
            return#忽略
        行=过滤选项(态['options'],态['search'])#过滤
        if len(行)==0:#无行
            return#忽略
        态['active']=(态['active']+方向+len(行))%len(行)#环绕
        自身.state.set(态)#写

    def highlight(自身,下标):#指针高亮
        """过滤范围内直接设。"""
        态=自身.state.getSnapshot()#快照
        if not 态['open'] or 态['status']!='ready' or 态['submitting'] or 态['confirming'] is not None:#不可
            return#忽略
        行=过滤选项(态['options'],态['search'])#过滤
        if 下标<0 or 下标>=len(行) or 下标==态['active']:#越界或未变
            return#忽略
        态['active']=下标#写
        自身.state.set(态)#发布

    def select(自身,下标):#选定过滤后一行
        """有 confirmation 则进确认态，否则结算。"""
        绑定=自身.绑定#绑定
        态=自身.state.getSnapshot()#快照
        if 绑定 is None or not 态['open'] or 态['status']!='ready' or 态['submitting'] or 态['confirming'] is not None:#不可
            return#忽略
        行=过滤选项(态['options'],态['search'])#过滤
        if 下标<0 or 下标>=len(行):#越界
            return#忽略
        项=行[下标]#选项
        if 项.get('confirmation') is not None:#风险闸
            态.update({'confirming':项,'acknowledged':False,'error':None})#确认态
            自身.state.set(态)#写
            return#等确认
        自身._结算(绑定,项)#直接结算

    def acknowledge(自身,已勾):#更新风险勾选
        """确认闸勾选。"""
        态=自身.state.getSnapshot()#快照
        if not 态['open'] or 态['submitting'] or 态['confirming'] is None or 态['acknowledged']==已勾:#不可
            return#忽略
        态['acknowledged']=已勾#写
        自身.state.set(态)#发布

    def cancelConfirmation(自身):#取消风险闸
        """回到选项挑选。"""
        态=自身.state.getSnapshot()#快照
        if not 态['open'] or 态['submitting'] or 态['confirming'] is None:#不可
            return#忽略
        态.update({'confirming':None,'acknowledged':False})#清
        自身.state.set(态)#写

    def confirm(自身):#确认闸后结算
        """须已勾选。"""
        绑定=自身.绑定#绑定
        态=自身.state.getSnapshot()#快照
        if 绑定 is None or not 态['open'] or 态['submitting'] or 态['confirming'] is None or not 态['acknowledged']:#不可
            return#忽略
        自身._结算(绑定,态['confirming'])#结算

    def _结算(自身,绑定,选项):#跑业务 onSelect
        """成功则消费令牌并关闭。"""
        态=自身.state.getSnapshot()#快照
        if 自身.绑定 is not 绑定 or not 态['open'] or 态['submitting']:#不可
            return#忽略
        态.update({'submitting':True,'confirming':None,'acknowledged':False,'error':None})#单飞
        自身.state.set(态)#写
        try:#业务
            解开(绑定['spec']['onSelect'](选项,绑定['context']))#结算
        except Exception as 错误:#失败
            if 自身.绑定 is not 绑定:#已换
                return#丢
            现=自身.state.getSnapshot()#现
            现.update({'submitting':False,'error':错误文(错误)})#解除提交
            自身.state.set(现)#写
            return#保持打开
        if 自身.绑定 is not 绑定:#迟到
            return#不写
        自身.依赖['consume'](绑定['segment'])#消费令牌
        自身.绑定=None#撤绑定
        自身.state.set(关闭态)#关闭
        自身.依赖['focusComposer']()#还焦

    def dismiss(自身,选项=None):#关闭外壳
        """中止拉取并撤销结算权。"""
        if 自身.绑定 is None:#未开
            return#结束
        自身.绑定['abort']()#中止
        自身.绑定=None#撤
        自身.state.set(关闭态)#关
        if 选项 and 选项.get('focusComposer'):#Escape
            自身.依赖['focusComposer']()#还焦

    def dispose(自身):#作用域拆除
        """中止并清空。"""
        if 自身.绑定 is not None:#有
            自身.绑定['abort']()#中止
        自身.绑定=None#清
        自身.state.set(关闭态)#关

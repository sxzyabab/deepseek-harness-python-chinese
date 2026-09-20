"""Client 侧 Workspace 状态模型，由 Remote 传输与 UI 投影共享。"""
import re#写死 ISO
from datetime import datetime as 日期时间,timedelta as 时间差,timezone as 固定偏移
from zoneinfo import ZoneInfo as 时区
from ....客户端.存储 import 通知订阅者#安全通知

__all__=[#仅中文公开名
    '工作区列表阶段','工作区快照','工作区跟随接收端','客户端工作区模型',
]#公开面结束

工作区列表阶段=('pending','ready')#列表阶段联合
_时刻轮廓=re.compile(#ISO-8601：Z 或 ±HH:MM
    r'^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]+))?(Z|([+-])([0-9]{2}):([0-9]{2}))\Z',
    re.ASCII,
)#写死轮廓

def _解析时刻(值):
    """ISO-8601 → 可比较时间戳；失败为 0。"""
    if 值 is None:#空
        return 0#最旧
    文=str(值)#字符串
    匹配=_时刻轮廓.match(文)#按轮廓
    if 匹配 is None:#形态不对
        return 0#最旧
    try:#按捕获组构造
        年,月,日=int(匹配.group(1)),int(匹配.group(2)),int(匹配.group(3))#日历
        时,分,秒=int(匹配.group(4)),int(匹配.group(5)),int(匹配.group(6))#墙钟
        小数=匹配.group(7) if 匹配.group(7) is not None else ''#小数秒
        微秒=int((小数+'000000')[:6]) if 小数!='' else 0#微秒
        if 匹配.group(8)=='Z':#UTC
            区=时区('UTC')
        else:#数字偏移
            偏移=时间差(hours=int(匹配.group(10)),minutes=int(匹配.group(11)))
            if 匹配.group(9)=='-':#西向
                偏移=-偏移#取负
            区=固定偏移(偏移)
        return 日期时间(年,月,日,时,分,秒,微秒,tzinfo=区).timestamp()
    except (TypeError,ValueError):#非法
        return 0#最旧

def _是否远程失败(错误):
    """值是否像 RemoteFailure（有 code/message）。"""
    if 错误 is None:#空
        return False#否
    if isinstance(错误,dict):#字典信封
        return 'code' in 错误 and 'message' in 错误#键齐
    return hasattr(错误,'code') and hasattr(错误,'message')#对象面

def _插标识到锚前(标识列,标识,锚点=None):
    """本地乐观重排：把标识插到锚点前；省略锚点则追加。"""
    if 标识 not in 标识列 or (锚点 is not None and 锚点 not in 标识列) or 锚点==标识:#非法
        return list(标识列)#原样复制
    去掉=[项 for 项 in 标识列 if 项!=标识]#先移除
    位=len(去掉) if 锚点 is None else 去掉.index(锚点)#插入点
    return 去掉[:位]+[标识]+去掉[位:]#插入

class 客户端工作区模型:
    """拥有 Client Workspace 投影、变更回声，以及流／一元竞态解析。"""

    def __init__(自身,远程):
        """远程为生成的 workspace 命名空间面。"""
        自身._远程=远程#远程面
        自身._行=()#当前行
        自身._归档会话标识=()#当前归档
        自身._状态='loading'#初始加载中
        自身._阶段='pending'#尚未就绪
        自身._错误=None#无错误
        自身._顺序请求代=0#重排请求代
        自身._顺序帧代=0#流顺序代
        自身._已提交顺序=[]#已提交顺序
        自身._已移除=set()#已移除 id
        自身._监听者=set()#订阅者
        自身._快照脏=False#快照是否脏
        自身._待通知=False#是否有待通知
        自身._已调度通知=False#是否已调度
        自身._通知代=0#通知代
        自身._快照缓存=自身._构造快照()#初始快照

    def create(自身,输入):
        """创建或解析 Workspace，并立即合并一元结果。输入含 path。"""
        结果=自身._远程.create(输入)#发远程
        if hasattr(结果,'等待'):#可等待
            结果=结果.等待()#兑现
        if 结果.get('ok'):#成功
            自身._合并(结果['value']['workspace'])#合并
        return 结果#结果

    def rename(自身,工作区标识,标题):
        """重命名 Workspace，并立即合并一元结果。"""
        结果=自身._远程.rename({'workspaceId':工作区标识,'title':标题})#发远程
        if hasattr(结果,'等待'):#可等待
            结果=结果.等待()#兑现
        if 结果.get('ok'):#成功
            自身._合并(结果['value']['workspace'])#合并
        return 结果#结果

    def delete(自身,工作区标识):
        """删除 Workspace，并立即从本地投影移除。"""
        结果=自身._远程.delete({'workspaceId':工作区标识})#发远程
        if hasattr(结果,'等待'):#可等待
            结果=结果.等待()#兑现
        if 结果.get('ok'):#成功
            自身._移除(工作区标识,True)#立即移除
        return 结果#结果

    def insertBefore(自身,工作区标识,锚点=None):
        """乐观移动 Workspace，并与返回的完整顺序对账。"""
        自身._顺序请求代+=1#本请求代
        请求代=自身._顺序请求代#捕获
        帧代=自身._顺序帧代#捕获流代
        本地顺序=[项['workspaceId'] for 项 in 自身._行]#当前本地顺序
        自身._安装顺序(_插标识到锚前(本地顺序,工作区标识,锚点))#乐观安装
        载荷={'workspaceId':工作区标识}#请求
        if 锚点 is not None:#有锚
            载荷['beforeWorkspaceId']=锚点#锚点
        结果=自身._远程.insertBefore(载荷)#发远程
        if hasattr(结果,'等待'):#可等待
            结果=结果.等待()#兑现
        if 请求代==自身._顺序请求代 and 帧代==自身._顺序帧代:#仍最新
            自身._安装顺序(
                结果['value']['workspaceIds'] if 结果.get('ok') else 自身._已提交顺序,
                结果.get('ok'),
            )#对账
        return 结果#结果

    def insertSessionBefore(自身,工作区标识,会话标识,锚点=None):
        """在所属 Workspace 内移动会话，并合并返回行。"""
        载荷={'workspaceId':工作区标识,'sessionId':会话标识}#请求
        if 锚点 is not None:#有锚
            载荷['beforeSessionId']=锚点#锚点
        结果=自身._远程.insertSessionBefore(载荷)#发远程
        if hasattr(结果,'等待'):#可等待
            结果=结果.等待()#兑现
        if 结果.get('ok'):#成功
            自身._合并(结果['value']['workspace'])#合并
        return 结果#结果

    def archiveSession(自身,会话标识):
        """归档一个会话，并安装返回的完整归档集合。"""
        结果=自身._远程.archiveSession({'sessionId':会话标识})#发远程
        if hasattr(结果,'等待'):#可等待
            结果=结果.等待()#兑现
        if 结果.get('ok'):#成功
            自身._安装归档(结果['value']['archivedSessionIds'])#安装
        return 结果#结果

    def replaceBaseline(自身,基线):
        """用一份完整流代际基线替换投影。基线为 dict。"""
        自身._顺序帧代+=1#流顺序代递增
        自身._安装全部行(基线.get('items') or ())#安装全部行
        自身._安装归档(基线.get('archivedSessionIds') or ())#安装归档
        自身._状态='idle'#就绪空闲
        自身._阶段='ready'#列表就绪
        自身._错误=None#清除错误
        自身._失效()#通知订阅者

    def upsertView(自身,工作区):
        """合并当前 follow 代际解码出的一次 Workspace upsert。"""
        自身._合并(工作区)#委托

    def removeView(自身,工作区标识):
        """应用当前 follow 代际解码出的一次 Workspace 移除。"""
        自身._移除(工作区标识)#委托

    def replaceOrder(自身,工作区标识列):
        """用当前 follow 代际替换 Host 确认的顺序。"""
        自身._顺序帧代+=1#流顺序代递增
        自身._安装顺序(工作区标识列,True)#作为已提交安装

    def replaceArchived(自身,归档会话标识列):
        """用当前 follow 代际替换已归档会话集合。"""
        自身._安装归档(归档会话标识列)#安装归档

    def handleCarrierFailure(自身):
        """丢失载体重连时保持最近完整投影可见。"""
        自身._状态='loading'#显示加载中
        自身._错误=None#可重试，清错误
        自身._失效()#通知

    def handleStreamFailure(自身,错误):
        """发布不可重试的流或协议失败。"""
        if not _是否远程失败(错误):#非远程失败
            raise 错误#上抛
        自身._状态='error'#进入错误态
        自身._错误=错误#保存失败
        自身._失效()#通知

    def subscribe(自身,监听):
        """订阅 Workspace 状态失效；返回取消订阅函数。"""
        自身._监听者.add(监听)#登记
        return lambda:自身._监听者.discard(监听)#取消

    def getSnapshot(自身):
        """读取缓存状态，必要时先重建。"""
        自身._刷新快照()#按需重建
        return 自身._快照缓存#缓存

    def _构造快照(自身):
        """构造不可变快照 dict。"""
        return {#快照
            'items':自身._行,#行
            'archivedSessionIds':自身._归档会话标识,#归档
            'state':自身._状态,#连接态
            'phase':自身._阶段,#列表阶段
            'error':自身._错误,#错误
        }#结束

    def _安装归档(自身,归档会话标识列):
        """安装归档集。"""
        列=tuple(归档会话标识列)#固化
        if len(列)==len(自身._归档会话标识) and all(列[i]==自身._归档会话标识[i] for i in range(len(列))):#无变化
            return#跳过
        自身._归档会话标识=列#安装
        自身._失效()#通知

    def _安装顺序(自身,工作区标识列,已提交=False):
        """按排名安装顺序。"""
        if 已提交:#提交则缓存
            自身._已提交顺序=list(工作区标识列)#缓存
        排名={标识:序 for 序,标识 in enumerate(工作区标识列)}#排名表
        行=tuple(sorted(
            自身._行,
            key=lambda 项:排名.get(项['workspaceId'],10**18),
        ))#按排名排序
        if all(行[i] is 自身._行[i] for i in range(len(行))) and len(行)==len(自身._行):#未变
            return#跳过
        自身._行=行#安装
        自身._失效()#通知

    def _合并(自身,视图):
        """合并一行 Workspace。视图为 dict。"""
        标识=视图['workspaceId']#id
        if 标识 in 自身._已移除:#已移除则拒绝复活
            return#跳过
        下标=next((i for i,项 in enumerate(自身._行) if 项['workspaceId']==标识),-1)#定位
        已有=自身._行[下标] if 下标>=0 else None#已有行
        if 已有 is not None and _解析时刻(视图.get('updatedAt'))<_解析时刻(已有.get('updatedAt')):#更旧
            return#丢
        if 标识 not in 自身._已提交顺序:#未知 id
            自身._已提交顺序=[标识]+自身._已提交顺序#插到顺序头
        if 下标==-1:#新建
            自身._行=(视图,)+自身._行#插头
        else:#替换
            自身._行=tuple(视图 if i==下标 else 项 for i,项 in enumerate(自身._行))#替换
        自身._失效()#通知

    def _移除(自身,工作区标识,立即=False):
        """移除一行。"""
        自身._已移除.add(工作区标识)#记入已移除
        自身._已提交顺序=[标识 for 标识 in 自身._已提交顺序 if 标识!=工作区标识]#从顺序去掉
        行=tuple(项 for 项 in 自身._行 if 项['workspaceId']!=工作区标识)#过滤
        if len(行)==len(自身._行):#无变化
            if 立即:#立即通知
                自身._失效(True)#通知
            return
        自身._行=行#安装
        自身._失效(立即)#通知

    def _安装全部行(自身,视图列):
        """安装全部行并记顺序。"""
        已装={}#按 id 去重
        for 视图 in 视图列:#逐行
            标识=视图['workspaceId']#id
            if 标识 not in 自身._已移除:#跳过已移除
                已装[标识]=视图#写入
        自身._行=tuple(已装.values())#安装行
        自身._已提交顺序=[视图['workspaceId'] for 视图 in 视图列]#安装顺序

    def _失效(自身,立即=False):
        """标记失效并调度通知。"""
        自身._快照脏=True#脏
        自身._待通知=True#待通知
        if 立即:#立即
            自身._通知代+=1#作废已调度
            自身._已调度通知=False#清调度
            自身._冲刷()#立即派发
            return
        if 自身._已调度通知:#已调度则合并
            return#跳过
        自身._已调度通知=True#标记
        自身._通知代+=1#本代
        代=自身._通知代#捕获
        def 后台通知():
            """微任务派发。"""
            if 代!=自身._通知代:#已作废
                return#跳过
            自身._已调度通知=False#清调度
            自身._冲刷()#派发
        import threading#延迟导入
        threading.Thread(target=后台通知,daemon=True,name='workspace-controller-notify').start()#调度

    def _冲刷(自身):
        """派发通知。"""
        if not 自身._待通知 or len(自身._监听者)==0:#无待办或无订阅者
            return#跳过
        自身._待通知=False#清除
        自身._刷新快照()#重建
        通知订阅者(自身._监听者,'[workspace-controller]')#安全通知

    def _刷新快照(自身):
        """按需重建快照。"""
        if not 自身._快照脏:#不脏
            return#跳过
        自身._快照脏=False#清脏
        自身._快照缓存=自身._构造快照()#重建

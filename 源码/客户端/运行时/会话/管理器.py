"""会话管理器：实例簇 + 帧分发入口 + 列表状态。

对齐上游 `runtime/src/client/sessions/manager.ts`。公开面仅中文名。
由会话运行时构造并持有（每个客户端运行时一份）。
列表数据从不进 zustand；消费方经订阅/取列表快照连接。

依赖未迁：.会话（会话/Session）、会话远程面（SessionRemotes，仅构造入参）、
会话组装运行时（ConversationRuntime，仅构造入参）。
"""
import asyncio#刷新火忘
import threading#名册防抖定时器
import time#本地 updatedAt
from ..有序基线 import 合并有序基线#列表顺序合并
from .通知器 import 通知器#批通知
from .投影仓库 import 投影值仓库#每会话投影
from .谱系 import 展平谱系#列表行展平
from .会话 import 会话#依赖未迁：实例簇元素

__all__=['会话管理器','会话列表阶段']#仅中文公开名

会话列表阶段=('pending','ready')#列表到达阶段

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 折叠传输错误(错误):#载体抛错 → 业务错误支
    """对齐 apiproxy transportError：internal + 空 details。"""
    if isinstance(错误,BaseException):#异常
        消息=str(错误)#取 message
    else:#其它
        消息=str(错误)#String()
    return {'ok':False,'error':{'code':'internal','message':消息,'details':{}}}#失败支

def 缓冲请求键(信封):#缓冲帧身份
    """为尚未实例化的会话保留的帧的稳定身份。"""
    帧=取字段(信封,'payload')#帧载荷
    种类=取字段(帧,'type')#帧类型
    if 种类=='approval/requested':#审批
        return 'a:'+str(取字段(帧,'approvalId'))#审批键
    if 种类=='question/requested':#提问
        return 'q:'+str(取字段(信封,'rpcId'))#提问键
    if 种类=='session/queue':#队列快照
        return 'queue'#单槽
    return None#其它类型不缓冲

def 提问交互状态(提问们):#提问 → 侧栏状态
    """在线边界匹配 ui-user-questions 的二元计划评审路由。"""
    if 提问们 is None or len(提问们)!=1:#非单题
        return 'question'#普通提问
    提问=提问们[0]#唯一一题
    意图=取字段(提问,'intent')#可选意图
    if 取字段(意图,'kind')!='plan-review' or 取字段(提问,'detail') is None:#不是计划评审
        return 'question'#普通提问
    if 取字段(提问,'multiSelect') is True:#多选不是二元评审
        return 'question'#普通提问
    选项们=取字段(提问,'options') or []#选项
    if len(选项们)>2:#超过两个选项
        return 'question'#普通提问
    批准=取字段(意图,'approve')#批准标签
    for 选项 in 选项们:#扫标签
        if 取字段(选项,'label')==批准:#有批准标签
            return 'plan-review'#计划评审
    return 'question'#否则普通提问

def 工作区附着会话标识(错误):#从附着失败取已发布 id
    """宿主契约与客户端工程独立构建期间的临时源平面桥。"""
    if 取字段(错误,'code')!='workspace-attach-failed':#不匹配
        return None#无
    细节=取字段(错误,'details') or {}#细节
    return 取字段(细节,'sessionId')#已发布会话 id

def 应用变更(摘要们,变更):#应用一次列表变更
    """应用一次列表变更，不推导展示顺序。"""
    种类=变更['kind']#变更种类
    if 种类=='upsert':#插入或补全
        摘要=变更['summary']#新摘要
        标识=取字段(摘要,'sessionId')#会话 id
        已有=None#已有行
        for 项 in 摘要们:#查找
            if 取字段(项,'sessionId')==标识:#命中
                已有=项#记下
                break#停
        if 已有 is None:#新 id 前置
            return [摘要]+list(摘要们)#前置
        填好=dict(已有) if isinstance(已有,dict) else dict(已有.__dict__)#保住已有
        # blank 只降不升：陈旧的 true 永不重新隐藏已浮出会话
        填好['blank']=bool(取字段(已有,'blank')) and bool(取字段(摘要,'blank'))#双方都空白才空白
        if 取字段(已有,'cwd') is None and 取字段(摘要,'cwd') is not None:#只填缺 cwd
            填好['cwd']=取字段(摘要,'cwd')#写入
        if 取字段(已有,'parentSessionId') is None and 取字段(摘要,'parentSessionId') is not None:#只填缺父
            填好['parentSessionId']=取字段(摘要,'parentSessionId')#写入
        if 取字段(已有,'origin') is None and 取字段(摘要,'origin') is not None:#只填缺来源
            填好['origin']=取字段(摘要,'origin')#写入
        if 取字段(摘要,'agentPreset') is not None:#最新胜出
            填好['agentPreset']=取字段(摘要,'agentPreset')#覆盖预设
        if (取字段(填好,'cwd')==取字段(已有,'cwd')#字段都没变
            and 取字段(填好,'parentSessionId')==取字段(已有,'parentSessionId')
            and 取字段(填好,'origin')==取字段(已有,'origin')
            and 取字段(填好,'blank')==取字段(已有,'blank')
            and 取字段(填好,'agentPreset')==取字段(已有,'agentPreset')):
            return list(摘要们)#拷贝数组但行对象不变
        return [填好 if 取字段(项,'sessionId')==标识 else 项 for 项 in 摘要们]#替换该行
    if 种类=='remove':#移除
        return [项 for 项 in 摘要们 if 取字段(项,'sessionId')!=变更['sessionId']]#拿掉
    if 种类=='status':#运行状态
        标识=变更['sessionId']#目标
        运行中=变更['running']#新 running
        结果=[]#新列表
        for 项 in 摘要们:#逐行
            if 取字段(项,'sessionId')!=标识:#其它行
                结果.append(项)#不动
                continue#下一行
            旧运行=取字段(项,'running')#旧 running
            旧空白=取字段(项,'blank')#旧 blank
            if 旧运行!=运行中 or (运行中 and 旧空白):#需要更新
                新行=dict(项) if isinstance(项,dict) else dict(项.__dict__)#拷贝
                新行['running']=运行中#更新 running
                新行['blank']=bool(旧空白) and (not 运行中)#开跑则降 blank
                结果.append(新行)#写入
            else:#无变
                结果.append(项)#原样
        return 结果#返回
    if 种类=='activity':#活动时间
        标识=变更['sessionId']#目标
        时刻=变更['updatedAt']#新时间
        结果=[]#新列表
        for 项 in 摘要们:#逐行
            if 取字段(项,'sessionId')==标识 and 时刻>取字段(项,'updatedAt'):#只向前
                新行=dict(项) if isinstance(项,dict) else dict(项.__dict__)#拷贝
                新行['updatedAt']=时刻#更新时间
                结果.append(新行)#写入
            else:#不动
                结果.append(项)#原样
        return 结果#返回
    if 种类=='engaged':#本地首次发送
        标识=变更['sessionId']#目标
        结果=[]#新列表
        for 项 in 摘要们:#逐行
            if 取字段(项,'sessionId')==标识 and 取字段(项,'blank'):#仍空白
                新行=dict(项) if isinstance(项,dict) else dict(项.__dict__)#拷贝
                新行['blank']=False#降下空白
                结果.append(新行)#写入
            else:#不动
                结果.append(项)#原样
        return 结果#返回
    raise Exception('sessions.applyMutation: unknown kind '+str(种类))#未知种类

def _火忘(协程):#无环时吞掉（对齐 void refresh）
    """fire-and-forget 刷新。"""
    try:#有环
        asyncio.get_running_loop().create_task(协程)#挂任务
    except RuntimeError:#无环
        pass#宿主稍后驱动

class 会话管理器:#会话对象层管理器
    """实例簇 + 帧入口 + 会话列表。"""

    def __init__(自身,接口,远程,恢复选中=None,恢复地址=None,会话运行时=None):#会话管理器
        """共享线客户端、Remote 面、可选恢复选择与会话注册表。

        @param 接口 - 共享线客户端。
        @param 远程 - 会话 Remote 面（依赖未迁类型）。
        @param 恢复选中 - 持久化的真实会话选择候选。
        @param 恢复地址 - 可选恢复的子智能体地址。
        @param 会话运行时 - 可选会话组装运行时（依赖未迁类型）。
        """
        自身._接口=接口#共享线客户端
        自身._远程=远程#Remote 面
        自身._会话运行时=会话运行时#可选会话注册表
        自身._会话们={}#常驻实例簇 sessionId → 会话
        自身._待缓冲={}#未实例化会话的帧缓冲
        自身._挂起交互={}#侧栏挂起状态 sessionId → {键→状态}
        自身._完成提醒=set()#完成提醒
        自身._上次运行={}#上次 running
        自身._投影仓库们={}#每会话投影存储
        自身._摘要们=[]#当前列表摘要
        自身._列表状态='idle'#拉取活动轴
        自身._列表阶段='pending'#到达阶段
        自身._列表错误=None#拉取错误
        自身._列表在飞=None#飞行中的列表拉取
        自身._列表变更=None#飞行中变更日志
        自身._地址们={}#子智能体地址
        自身._名册们={}#已加载名册
        自身._名册在飞={}#飞行中的名册拉取
        自身._名册过期=set()#过期名册
        自身._开着名册=set()#菜单正开着的名册
        自身._名册防抖={}#名册刷新防抖 Timer
        自身._任务按会话={}#会话 → 任务
        自身._选中=恢复选中#当前选中
        if 恢复地址 is not None:#恢复子智能体地址
            自身._地址们[取字段(恢复地址,'childSessionId')]=恢复地址#写入
        自身._行缓存={}#行对象身份缓存
        自身._条目缓存=()#行数组引用缓存
        自身._通知器=通知器(自身._建快照写入)#脏时重建列表快照
        自身._列表快照缓存=自身._建列表快照()#编出初始快照

    def _建快照写入(自身):#通知器回调
        """重建写入缓存。"""
        自身._列表快照缓存=自身._建列表快照()#重建

    # ---- 选择 ----

    def 选中(自身,会话标识):#选中会话
        """选中一个已列出的会话，或一个保留的名册寻址子项。

        @param 会话标识 - 已列出或名册寻址的会话 id。
        """
        地址=自身.导航地址(会话标识)#解析导航地址
        if (not any(取字段(摘要,'sessionId')==会话标识 for 摘要 in 自身._摘要们)#不在列表
            and 地址 is None):#也没有地址
            raise Exception('sessions.select: unknown session '+str(会话标识))#未知会话
        if 地址 is not None:#有寻址
            自身._地址们[会话标识]=地址#保留寻址
        已有=自身._会话们.get(会话标识)#已有实例
        if 已有 is not None:#配置传输
            if 地址 is None:#普通会话
                已有.配置子智能体(None,False)#无父可用性
            else:#子智能体
                名册=自身._名册们.get(取字段(地址,'parentSessionId'))#父名册
                已有.配置子智能体(地址,bool(取字段(名册,'parentAvailable')) if 名册 is not None else False)#名册可用性
        自身._选中=会话标识#记下选中
        自身._完成提醒.discard(会话标识)#清完成点
        _火忘(自身.刷新子智能体(会话标识))#刷新其直接子名册
        自身._通知器.立刻通知()#立刻发布列表

    def 选中子智能体(自身,地址):#选中子智能体
        """经其持久直接父地址选中一个健康子项。

        @param 地址 - 名册导出的父子 id。
        """
        父标识=取字段(地址,'parentSessionId')#父 id
        子标识=取字段(地址,'childSessionId')#子 id
        模式=取字段(地址,'mode')#模式
        名册=自身._名册们.get(父标识)#父名册
        条目=None#名册行
        if 名册 is not None:#有名册
            for 候选 in (取字段(名册,'entries') or []):#扫行
                if 取字段(候选,'id')==子标识:#命中
                    条目=候选#记下
                    break#停
        if (条目 is None or 取字段(条目,'kind')!='child'#不是健康子项
            or 取字段(条目,'mode')!=模式):
            raise Exception('sessions.selectSubagent: '+str(子标识)+' is not a healthy catalog child')#不健康
        自身._地址们[子标识]=地址#保留地址
        已有=自身._会话们.get(子标识)#已有实例
        if 已有 is not None:#配置
            已有.配置子智能体(地址,bool(取字段(名册,'parentAvailable')) if 名册 is not None else False)#配置
        自身._选中=子标识#选中子会话
        自身._完成提醒.discard(子标识)#清完成点
        _火忘(自身.刷新子智能体(子标识))#刷新其子名册
        自身._通知器.立刻通知()#立刻发布列表

    def 清空选择(自身):#清空选择
        """清掉选择（布局落到无会话视图状态）。"""
        自身._选中=None#无当前会话
        自身._通知器.立刻通知()#立刻发布列表

    def 子智能体地址(自身,会话标识):#读保留地址
        """返回为一个子项保留的持久名册地址。

        @param 会话标识 - 可能的已寻址子 id。
        @returns 直接父地址，若导航发现过一个。
        """
        return 自身._地址们.get(会话标识)#按子 id 查

    def 导航地址(自身,会话标识):#解析导航地址
        """解析面包屑导航地址，但不保留传输权威。

        @param 会话标识 - 已加载名册里可能的子 id。
        @returns 保留的或名册导出的直接父地址。
        """
        保留=自身._地址们.get(会话标识)#已保留的地址
        if 保留 is not None:#优先保留
            return 保留#返回
        for 父会话标识,名册 in 自身._名册们.items():#每份已加载名册
            for 条目 in (取字段(名册,'entries') or []):#扫行
                if 取字段(条目,'kind')=='child' and 取字段(条目,'id')==会话标识:#找到子项
                    return {#导出地址
                        'parentSessionId':父会话标识,#父
                        'childSessionId':会话标识,#子
                        'mode':取字段(条目,'mode'),#模式
                    }#结束
        return None#没有地址

    # ---- 实例管理 ----

    def 丢掉(自身,会话标识):#丢掉实例
        """丢掉一个会话实例（作用域拆除伴侣：实例与作用域共享同一生命周期）。

        @param 会话标识 - 要丢掉的会话。
        """
        自身._会话们.pop(会话标识,None)#从簇里拿掉

    def 取得(自身,会话标识):#取得或建造实例
        """惰性建造：返回已有实例或构造一个（不自动打开）。

        @param 会话标识 - 要取得的会话。
        @returns 常驻实例。
        """
        对象=自身._会话们.get(会话标识)#已有实例
        if 对象 is None:#尚未建造
            对象=自身._创建会话(会话标识)#构造
            自身._会话们[会话标识]=对象#放入簇
            缓冲=自身._待缓冲.pop(会话标识,None)#取出缓冲
            if 缓冲 is not None:#有缓冲帧
                for 信封 in 缓冲:#逐条重放
                    对象.处理复用信封(取字段(信封,'rpcId'),取字段(信封,'payload'))#重放
            摘要=None#列表摘要
            for 项 in 自身._摘要们:#查找
                if 取字段(项,'sessionId')==会话标识:#命中
                    摘要=项#记下
                    break#停
            if 摘要 is not None:#在列表上
                对象.处理空白(取字段(摘要,'blank'))#同步空白位
                对象.处理运行中(取字段(摘要,'running'))#同步运行位
            else:#不在列表上，可能是名册子项
                地址=自身._地址们.get(会话标识)#保留地址
                子行=None#子行
                if 地址 is not None:#有地址
                    名册=自身._名册们.get(取字段(地址,'parentSessionId'))#父名册
                    for 条目 in (取字段(名册,'entries') or [] if 名册 is not None else []):#扫行
                        if 取字段(条目,'kind')=='child' and 取字段(条目,'id')==会话标识:#命中
                            子行=条目#记下
                            break#停
                if 子行 is not None and 取字段(子行,'kind')=='child':#找到名册子项
                    对象.处理空白(False)#名册子项非空白
                    对象.处理运行中(取字段(子行,'activity')=='running')#按名册活动同步
        return 对象#常驻实例

    def _创建会话(自身,会话标识):#构造一个会话
        """对象层构造。"""
        地址=自身._地址们.get(会话标识)#可选子智能体地址
        选项={'首次浮出':自身._首次浮出回调(会话标识),'投影们':自身._投影仓库(会话标识)}#公共选项
        if 地址 is not None:#有地址才铺传输
            名册=自身._名册们.get(取字段(地址,'parentSessionId'))#父名册
            选项['地址']=地址#子智能体地址
            选项['父可用']=bool(取字段(名册,'parentAvailable')) if 名册 is not None else False#父可用性
        if 自身._会话运行时 is not None:#可选会话注册表
            选项['会话运行时']=自身._会话运行时#写入
        return 会话(会话标识,自身._接口,自身._远程,选项)#构造

    def _首次浮出回调(自身,会话标识):#闭包回调
        """发送方的本地首次发送翻转镜像进列表行。"""
        def 回调(_已浮出):#首次接受
            """记下浮出变更（身份取自构造闭包，对齐 engaged.sessionId）。"""
            自身._记录变更({'kind':'engaged','sessionId':会话标识})#记下浮出
        return 回调#返回

    def 重建会话注册表(自身):#重建会话注册表
        """一次合并的注册表事务后重建每个常驻会话。"""
        for 对象 in 自身._会话们.values():#每个实例
            对象.重建会话注册表()#重建

    def _投影仓库(自身,会话标识):#取得或创建投影存储
        """常驻每会话投影存储（按需创建；比实例化更长寿）。"""
        仓库=自身._投影仓库们.get(会话标识)#已有存储
        if 仓库 is None:#尚未创建
            仓库=投影值仓库()#新建
            仓库.订阅任意(lambda:自身._通知器.标脏())#任意键变则脏列表
            自身._投影仓库们[会话标识]=仓库#放入映射
        return 仓库#常驻存储

    async def 刷新子智能体(自身,父会话标识):#刷新名册
        """刷新一份直接子名册，复用其飞行中的请求。

        @param 父会话标识 - 名册所有者。
        """
        已有=自身._名册在飞.get(父会话标识)#飞行中的拉取
        if 已有 is not None:#复用
            return await 已有['承诺']#等待同一趟
        上一份=自身._名册们.get(父会话标识)#上一份名册
        可展开行=set()#本趟可展开覆盖
        活动行={}#本趟活动覆盖
        自身._名册们[父会话标识]={#先进入 loading
            'entries':取字段(上一份,'entries') if 上一份 is not None else [],#保住旧行
            'parentAvailable':bool(取字段(上一份,'parentAvailable')) if 上一份 is not None else False,#保住旧可用性
            'state':'loading',#加载中
            'error':None,#清错误
        }#结束 loading 快照
        自身._通知器.标脏()#刷新列表

        async def 一趟():#本趟拉取
            """请求名册并结算。"""
            try:#请求名册
                响应=await 自身._接口.subagents.list({'parentSessionId':父会话标识})#拉直接子
                结果=取字段(响应,'result',响应)#取出 result
                if 取字段(结果,'ok'):#成功
                    值=取字段(结果,'value')#名册值
                    在飞=自身._名册在飞.get(父会话标识)#飞行记录
                    覆盖=取字段(在飞,'父可用覆盖') if 在飞 is not None else None#移除覆盖
                    父可用=覆盖 if 覆盖 is not None else 取字段(值,'parentAvailable')#已解析可用性
                    自身._名册们[父会话标识]={#写入就绪名册
                        **(值 if isinstance(值,dict) else {}),#宿主名册字段
                        'entries':自身._叠名册覆盖(取字段(值,'entries') or [],可展开行,活动行),#叠覆盖
                        'parentAvailable':父可用,#可用性
                        'state':'ready',#就绪
                        'error':None,#无错误
                    }#结束就绪快照
                    for 子标识,地址 in list(自身._地址们.items()):#每个已寻址子
                        if 取字段(地址,'parentSessionId')!=父会话标识:#不是本父
                            continue#跳过
                        实例=自身._会话们.get(子标识)#实例
                        if 实例 is not None:#中继
                            实例.处理子智能体父可用(父可用)#中继父可用性
                else:#业务失败
                    在飞=自身._名册在飞.get(父会话标识)#飞行记录
                    覆盖=取字段(在飞,'父可用覆盖') if 在飞 is not None else None#移除覆盖
                    自身._名册们[父会话标识]={#写入错误名册
                        'entries':自身._叠名册覆盖(#叠覆盖到旧行
                            取字段(上一份,'entries') if 上一份 is not None else [],可展开行,活动行),#旧行
                        'parentAvailable':覆盖 if 覆盖 is not None else (bool(取字段(上一份,'parentAvailable')) if 上一份 is not None else False),#可用性
                        'state':'error',#错误
                        'error':取字段(结果,'error'),#记下错误
                    }#结束错误快照
            except Exception as 错误:#传输失败
                折叠=折叠传输错误(错误)#折成 RPC 错误
                在飞=自身._名册在飞.get(父会话标识)#飞行记录
                覆盖=取字段(在飞,'父可用覆盖') if 在飞 is not None else None#移除覆盖
                自身._名册们[父会话标识]={#写入错误名册
                    'entries':自身._叠名册覆盖(#叠覆盖到旧行
                        取字段(上一份,'entries') if 上一份 is not None else [],可展开行,活动行),#旧行
                    'parentAvailable':覆盖 if 覆盖 is not None else (bool(取字段(上一份,'parentAvailable')) if 上一份 is not None else False),#可用性
                    'state':'error',#错误
                    'error':None if 取字段(折叠,'ok') else 取字段(折叠,'error'),#记下折叠错误
                }#结束传输错误快照
            finally:#无论成败
                自身._名册在飞.pop(父会话标识,None)#清飞行记录
                if 父会话标识 in 自身._名册过期:#过期则再拉
                    自身._名册过期.discard(父会话标识)#清过期
                    _火忘(自身.刷新子智能体(父会话标识))#尾随刷新
                自身._通知器.标脏()#刷新列表

        任务=一趟()#本趟协程
        try:#有运行中事件环
            承诺=asyncio.get_running_loop().create_task(任务)#可共享 Task
        except RuntimeError:#无环
            承诺=任务#裸协程
        自身._名册在飞[父会话标识]={#记下飞行中
            '承诺':承诺,#本趟 promise
            '可展开行':可展开行,#本趟可展开覆盖
            '活动行':活动行,#本趟活动覆盖
            '父可用覆盖':None,#尚无移除覆盖
        }#结束 inflight
        return await 承诺#交给调用方

    def 设子智能体名册开闭(自身,父会话标识,开着):#名册菜单开关
        """标记名册菜单是否在消费直播成员更新。

        @param 父会话标识 - 名册所有者。
        @param 开着 - 当前菜单状态。
        """
        if 开着:#打开菜单
            自身._开着名册.add(父会话标识)#记下正开着
            _火忘(自身.刷新子智能体(父会话标识))#立刻刷新
        else:#关闭菜单
            自身._开着名册.discard(父会话标识)#不再开着
            定时器=自身._名册防抖.pop(父会话标识,None)#未触发的防抖
            if 定时器 is not None:#有定时器
                定时器.cancel()#取消

    # ---- 列表 API ----

    async def 刷新列表(自身):#刷新列表
        """经 session.list 全量刷新（单飞：飞行中的调用被复用）。"""
        if 自身._列表在飞 is not None:#复用飞行中的
            return await 自身._列表在飞#等待同一趟
        自身._列表状态='loading'#进入加载
        自身._列表错误=None#清错误
        已确立=list(自身._摘要们)#拉取前已有摘要
        变更们=[]#本趟变更日志
        自身._列表变更=变更们#开始记录飞行中变更
        自身._通知器.标脏()#刷新加载态

        async def 一趟():#本趟拉取
            """请求列表并结算。"""
            try:#请求列表
                响应=await 自身._接口.sessions.list({})#拉全量列表
                结果=取字段(响应,'result',响应)#取出 result
                if 取字段(结果,'ok'):#成功
                    值=取字段(结果,'value')#列表值
                    响应行=list(取字段(值,'items') or [])#响应行
                    if 自身._列表阶段=='pending':#首次到达
                        基线=响应行#直接用响应
                    else:#与已有顺序合并
                        基线=合并有序基线(已确立,响应行,lambda 摘要:取字段(摘要,'sessionId'))#合并
                    for 项 in 基线:#每条基线摘要
                        标识=取字段(项,'sessionId')#id
                        if 标识 not in 自身._上次运行:#首次观察只记录
                            自身._上次运行[标识]=取字段(项,'running')#记下
                    摘要们=基线#从基线起叠变更
                    for 变更 in 变更们:#每条飞行中变更
                        摘要们=应用变更(摘要们,变更)#应用到摘要
                        自身._摘要们=摘要们#立刻可见，供对账
                        自身._对账完成提醒()#每条后对账提醒
                    自身._摘要们=摘要们#最终摘要
                    自身._列表状态='idle'#拉取结束
                    自身._列表阶段='ready'#到达完成
                    自身._对账完成提醒()#再对账一次
                    for 项 in 自身._摘要们:#每条摘要
                        实例=自身._会话们.get(取字段(项,'sessionId'))#已有实例
                        if 实例 is None:#未实例化
                            continue#跳过
                        实例.处理空白(取字段(项,'blank'))#同步空白位
                        实例.处理运行中(取字段(项,'running'))#同步运行位
                    for 项 in 响应行:#响应里的每行
                        块=取字段(项,'projections')#可选投影块
                        if 块 is None:#本行无投影
                            continue#跳过
                        仓库=自身._投影仓库(取字段(项,'sessionId'))#该会话存储
                        值表=取字段(块,'values') or {}#键值
                        切面=取字段(块,'asOfSeq')#切面序号
                        if isinstance(值表,dict):#按键写入
                            for 键 in list(值表.keys()):#每个键
                                仓库.应用(键,值表[键],切面)#按键写入
                else:#业务失败
                    自身._列表状态='error'#进入错误
                    自身._列表错误=取字段(结果,'error')#记下错误
            except Exception as 错误:#传输失败
                自身._列表状态='error'#进入错误
                折叠=折叠传输错误(错误)#折成 RPC 错误
                自身._列表错误=None if 取字段(折叠,'ok') else 取字段(折叠,'error')#记下折叠错误
            finally:#无论成败
                自身._列表变更=None#停止记录飞行中变更
                自身._列表在飞=None#清飞行指针
                自身._通知器.标脏()#刷新列表

        任务=一趟()#本趟协程
        try:#有运行中事件环
            自身._列表在飞=asyncio.get_running_loop().create_task(任务)#可共享 Task
        except RuntimeError:#无环
            自身._列表在飞=任务#裸协程
        return await 自身._列表在飞#交给调用方

    async def 搜索(自身,查询,取消信号=None):#搜索会话内容
        """搜索可见会话消息内容，不把瞬时查询状态加进列表快照。

        @param 查询 - 非空字面短语。
        @param 取消信号 - 被取代 UI 查询的取消。
        @returns 宿主结果或折叠后的传输错误。
        """
        try:#调用宿主
            响应=await 自身._接口.sessions.search({'query':查询},取消信号)#搜索
            return 取字段(响应,'result',响应)#原样返回
        except Exception as 错误:#传输失败
            return 折叠传输错误(错误)#折成 RPC 错误

    async def 创建(自身,选项=None):#创建会话
        """契约 session.create；成功时立刻合并进 summaries。

        @param 选项 - 目标工作区或工作目录，外加可选的调用方持有 id。
        @returns 创建结果。
        """
        if 选项 is None:#默认空
            选项={}#空
        try:#调用宿主
            共享={}#可选预分配 id
            if 取字段(选项,'sessionId') is not None:#有预分配
                共享['sessionId']=取字段(选项,'sessionId')#写入
            if 取字段(选项,'workspaceId') is not None:#有工作区
                载荷={'workspaceId':取字段(选项,'workspaceId'),**共享}#按工作区创建
            else:#否则按目录
                载荷=dict(共享)#拷贝共享
                if 取字段(选项,'cwd') is not None:#有目录
                    载荷['cwd']=取字段(选项,'cwd')#写入
            响应=await 自身._接口.sessions.create(载荷)#请求创建
            结果=取字段(响应,'result',响应)#结果
            if 取字段(结果,'ok'):#成功
                值=取字段(结果,'value')#创建值
                摘要={'sessionId':取字段(值,'sessionId'),'updatedAt':int(time.time()*1000),'running':False,'blank':True}#新生空白
                if 取字段(选项,'cwd') is not None:#可选工作目录
                    摘要['cwd']=取字段(选项,'cwd')#写入
                if 取字段(值,'agentPreset') is not None:#可选预设
                    摘要['agentPreset']=取字段(值,'agentPreset')#写入
                自身._记录变更({'kind':'upsert','summary':摘要})#立刻插入
            else:#失败，可能已发布实体
                已发布=工作区附着会话标识(取字段(结果,'error'))#附件失败里的已发布 id
                if 已发布 is not None:#有已发布 id
                    自身._记录变更({'kind':'upsert','summary':{#插入占位行
                        'sessionId':已发布,#已发布会话
                        'updatedAt':int(time.time()*1000),#本地时间
                        'running':False,#尚未跑
                        'blank':True,#仍空白
                    }})#结束占位 upsert
            return 结果#原样返回
        except Exception as 错误:#传输失败
            return 折叠传输错误(错误)#折成 RPC 错误

    async def 分叉(自身,选项):#fork 会话
        """契约 session.fork；成功时立刻把子项合并进 summaries。

        @param 选项 - 源会话以及可选的切点 seq。
        @returns fork 结果（子会话 id）。
        """
        try:#调用宿主
            源标识=取字段(选项,'sessionId')#源会话
            源=None#源摘要
            for 项 in 自身._摘要们:#查找
                if 取字段(项,'sessionId')==源标识:#命中
                    源=项#记下
                    break#停
            载荷={'sessionId':源标识}#源会话
            if 取字段(选项,'atSeq') is not None:#可选切点
                载荷['atSeq']=取字段(选项,'atSeq')#写入
            响应=await 自身._接口.sessions.fork(载荷)#请求 fork
            结果=取字段(响应,'result',响应)#结果
            if 取字段(结果,'ok'):#成功
                子标识=取字段(取字段(结果,'value'),'sessionId')#子 id
            else:#失败
                子标识=工作区附着会话标识(取字段(结果,'error'))#附着失败里的已发布 id
            if 子标识 is not None:#有子 id
                摘要={'sessionId':子标识,'updatedAt':int(time.time()*1000),'running':False,'blank':False,'parentSessionId':源标识}#带着历史
                if 源 is not None and 取字段(源,'cwd') is not None:#继承工作目录
                    摘要['cwd']=取字段(源,'cwd')#写入
                自身._记录变更({'kind':'upsert','summary':摘要})#立刻插入子行
            return 结果#原样返回
        except Exception as 错误:#传输失败
            return 折叠传输错误(错误)#折成 RPC 错误

    def _合并摘要(自身,摘要):#合并摘要
        """插入或补全一份本地合成摘要。"""
        自身._记录变更({'kind':'upsert','summary':摘要})#走 upsert 变更

    def 记下智能体预设(自身,会话标识,智能体预设):#记下预设
        """记录宿主确认的组合切换。

        @param 会话标识 - 被切换的会话。
        @param 智能体预设 - 宿主确认的预设 id。
        """
        自身._记录变更({'kind':'upsert','summary':{#upsert 当前预设
            'sessionId':会话标识,#会话
            'updatedAt':int(time.time()*1000),#本地时间
            'running':False,#空白会话上的预设
            'blank':True,#空白
            'agentPreset':智能体预设,#预设
        }})#结束 upsert

    def _记录变更(自身,变更):#记录列表变更
        """立刻应用，并在列表响应飞行中时保留以供重放。"""
        if 自身._列表变更 is not None:#飞行中则追加日志
            自身._列表变更.append(变更)#追加
        自身._摘要们=应用变更(自身._摘要们,变更)#立刻应用到摘要
        自身._对账完成提醒()#对账完成提醒
        自身._通知器.标脏()#刷新列表

    # ---- 订阅 API ----

    def 订阅(自身,监听器):#订阅列表变更
        """列表快照失效订阅入口。

        @param 监听器 - 变更回调。
        @returns 取消订阅函数。
        """
        return 自身._通知器.订阅(监听器)#交给通知器

    def 取列表快照(自身):#读缓存列表快照
        """缓存的列表快照（无监听者时脏了才惰性重建）。

        @returns 缓存引用（稳定直到下次 flush）。
        """
        自身._通知器.确保新鲜()#脏则先重建
        return 自身._列表快照缓存#稳定引用

    def _跟踪挂起(自身,会话标识,键,状态):#跟踪挂起
        """添加或刷新一个稳定的挂起交互身份。"""
        映射=自身._挂起交互.get(会话标识)#该会话的挂起映射
        if 映射 is None:#尚无映射
            映射={}#新建
            自身._挂起交互[会话标识]=映射#放入
        if 映射.get(键)==状态:#状态未变
            return#不动
        映射[键]=状态#写入或刷新
        自身._通知器.标脏()#刷新侧栏点

    def _结算挂起(自身,会话标识,键):#结算挂起
        """结算一个挂起交互身份，不打扰兄弟等待。"""
        映射=自身._挂起交互.get(会话标识)#该会话的挂起映射
        if 映射 is None or 键 not in 映射:#没有该项
            return#不动
        del 映射[键]#删除
        if len(映射)==0:#空则拿掉会话键
            del 自身._挂起交互[会话标识]#拿掉
        自身._通知器.标脏()#刷新侧栏点

    # ---- ConnectionController 汇 ----

    def 处理复用信封(自身,信封):#处理一条 mux 帧
        """mux 帧入口：带 sessionId 的帧只给已实例化会话。

        @param 信封 - 带着线 rpcId 的帧。
        """
        帧=取字段(信封,'payload')#帧载荷
        种类=取字段(帧,'type')#帧类型
        if 种类=='stream/error':#Controller 已把这当作流失败
            return#忽略
        if (种类=='session/event'#会话事件
            and 取字段(取字段(帧,'event'),'type')=='user/message'#用户消息
            and 取字段(取字段(取字段(帧,'event'),'data'),'source') is not None
            and 取字段(取字段(取字段(取字段(帧,'event'),'data'),'source'),'kind')=='user'):#来源是用户
            自身._记录变更({'kind':'activity','sessionId':取字段(帧,'sessionId'),'updatedAt':取字段(取字段(帧,'event'),'time')})#记下活动时间
        if 种类=='session/projection':#成品宿主计算值
            自身._投影仓库(取字段(帧,'sessionId')).应用(取字段(帧,'key'),取字段(帧,'value'),取字段(帧,'seq'))#按更高 seq 写入
            自身._通知器.标脏()#立刻刷新列表
            return#投影帧不继续分发
        if 种类=='session/jobs':#后台任务整集快照
            任务们=取字段(帧,'jobs') or []#任务集
            会话标识=取字段(帧,'sessionId')#会话
            if len(任务们)==0:#空集 → 缺键
                自身._任务按会话.pop(会话标识,None)#删
            else:#非空则后写
                自身._任务按会话[会话标识]=tuple(任务们)#写入
            自身._通知器.标脏()#刷新任务
            return#任务帧不继续分发
        if 种类=='session/subscribed':#新 mux 代际基线
            仓库=自身._投影仓库们.get(取字段(帧,'sessionId'))#投影存储
            if 仓库 is not None:#有
                仓库.截断(取字段(帧,'lastSeq'))#截断过期投影
            自身._任务按会话.pop(取字段(帧,'sessionId'),None)#丢掉上代任务镜像
            自身._通知器.标脏()#刷新列表
            缓冲=自身._待缓冲.get(取字段(帧,'sessionId'))#未实例化缓冲
            if 缓冲 is not None:#有缓冲
                留下=[项 for 项 in 缓冲 if 取字段(取字段(项,'payload'),'type')!='session/queue']#丢掉队列快照
                if len(留下)!=len(缓冲):#确实丢掉了队列
                    if len(留下)==0:#空则拿掉
                        自身._待缓冲.pop(取字段(帧,'sessionId'),None)#删
                    else:#否则写回
                        自身._待缓冲[取字段(帧,'sessionId')]=留下#写回
        if 种类=='approval/requested':#审批请求
            自身._跟踪挂起(取字段(帧,'sessionId'),'a:'+str(取字段(帧,'approvalId')),'approval')#点亮审批
        elif 种类=='approval/resolved':#审批已结算
            自身._结算挂起(取字段(帧,'sessionId'),'a:'+str(取字段(帧,'approvalId')))#熄灭审批
        elif 种类=='question/requested':#提问请求
            自身._跟踪挂起(#点亮提问或计划评审
                取字段(帧,'sessionId'),#会话
                'q:'+str(取字段(信封,'rpcId')),#提问键
                提问交互状态(取字段(帧,'questions')),#二元计划评审或普通提问
            )#结束跟踪
        elif 种类=='question/resolved':#提问已结算
            自身._结算挂起(取字段(帧,'sessionId'),'q:'+str(取字段(帧,'questionRpcId')))#熄灭提问
        会话标识=取字段(帧,'sessionId')#会话 id
        实例=自身._会话们.get(会话标识)#已实例化会话
        if 实例 is None:#尚未建造
            if 种类 in ('approval/requested','question/requested','session/queue'):#可缓冲
                缓冲=自身._待缓冲.get(会话标识) or []#已有或新建缓冲
                if 种类=='approval/requested':#审批
                    键='a:'+str(取字段(帧,'approvalId'))#审批键
                elif 种类=='question/requested':#提问
                    键='q:'+str(取字段(信封,'rpcId'))#提问键
                else:#队列
                    键='queue'#队列槽
                先前=-1#已有同身份
                for 下标,项 in enumerate(缓冲):#查找
                    if 缓冲请求键(项)==键:#命中
                        先前=下标#记下
                        break#停
                if 先前==-1:#新身份则追加
                    缓冲=list(缓冲)+[信封]#追加
                else:#否则覆盖重放
                    缓冲=list(缓冲)#拷贝
                    缓冲[先前]=信封#覆盖
                自身._待缓冲[会话标识]=缓冲#写回
                return#已缓冲
            if 种类 in ('approval/resolved','question/resolved'):#结算
                缓冲=自身._待缓冲.get(会话标识)#已有缓冲
                if 缓冲 is None:#没有可结算的
                    return#停
                if 种类=='approval/resolved':#审批结算
                    键='a:'+str(取字段(帧,'approvalId'))#审批键
                else:#提问结算
                    键='q:'+str(取字段(帧,'questionRpcId'))#提问键
                先前=-1#找同身份
                for 下标,项 in enumerate(缓冲):#查找
                    if 缓冲请求键(项)==键:#命中
                        先前=下标#记下
                        break#停
                if 先前!=-1:#去掉未实例化等待
                    缓冲=list(缓冲)#拷贝
                    del 缓冲[先前]#删
                if len(缓冲)==0:#空则拿掉
                    自身._待缓冲.pop(会话标识,None)#删
                else:#写回
                    自身._待缓冲[会话标识]=缓冲#写回
                return#已压缩
            return#其它帧丢掉，打开时历史回填
        实例.处理复用信封(取字段(信封,'rpcId'),帧)#交给实例

    def 处理宿主信封(自身,信封):#处理一条宿主帧
        """宿主帧入口：列表维护 + 每实例 running/removed/agent-error 中继。

        @param 信封 - 带着线 rpcId 的帧。
        """
        帧=取字段(信封,'payload')#帧载荷
        种类=取字段(帧,'type')#帧类型
        if 种类=='host/session-added':#新会话出现
            摘要={'sessionId':取字段(帧,'sessionId'),'updatedAt':int(time.time()*1000),'running':False,'blank':取字段(帧,'blank')}#新生行
            if 取字段(帧,'parentSessionId') is not None:#可选父
                摘要['parentSessionId']=取字段(帧,'parentSessionId')#写入
            if 取字段(帧,'origin') is not None:#可选来源
                摘要['origin']=取字段(帧,'origin')#写入
            if 取字段(帧,'cwd') is not None:#可选工作目录
                摘要['cwd']=取字段(帧,'cwd')#写入
            if 取字段(帧,'agentPreset') is not None:#可选预设
                摘要['agentPreset']=取字段(帧,'agentPreset')#写入
            自身._合并摘要(摘要)#插入或补全摘要
            实例=自身._会话们.get(取字段(帧,'sessionId'))#已有实例
            if 实例 is not None:#同步空白位
                实例.处理空白(取字段(帧,'blank'))#同步
            if 取字段(帧,'origin')=='subagent' and 取字段(帧,'parentSessionId') is not None:#子智能体发布
                自身._标记名册父可展开(取字段(帧,'parentSessionId'))#父行可展开
            父标识=取字段(帧,'parentSessionId')#父
            if 父标识 is not None and (自身._选中==父标识 or 父标识 in 自身._开着名册):#父被选中或菜单开着
                自身._调度名册刷新(父标识)#防抖刷新名册
            return#已处理
        if 种类=='host/session-removed':#会话移除
            会话标识=取字段(帧,'sessionId')#会话
            摘要=None#列表摘要
            for 候选 in 自身._摘要们:#查找
                if 取字段(候选,'sessionId')==会话标识:#命中
                    摘要=候选#记下
                    break#停
            持久子智能体=(取字段(摘要,'origin')=='subagent') or (会话标识 in 自身._地址们)#持久子智能体
            if 持久子智能体:#只停跑
                自身._记录变更({'kind':'status','sessionId':会话标识,'running':False})#回到空闲
            else:#从列表拿掉
                自身._记录变更({'kind':'remove','sessionId':会话标识})#移除
            自身._更新名册活动(会话标识,False)#名册活动变空闲
            实例=自身._会话们.get(会话标识)#实例
            if 持久子智能体:#激活拆离不是持久子删除
                if 实例 is not None:#停跑
                    实例.处理运行中(False)#停跑
            else:#普通移除
                if 实例 is not None:#打移除标
                    实例.处理已移除()#中继
            自身._待缓冲.pop(会话标识,None)#已移除会话的缓冲帧不得重放
            自身._挂起交互.pop(会话标识,None)#已移除会话不能再等人回答
            自身._任务按会话.pop(会话标识,None)#丢掉任务镜像
            if not 持久子智能体:#普通移除才丢掉投影
                自身._投影仓库们.pop(会话标识,None)#丢掉
            在飞名册=自身._名册在飞.get(会话标识)#本会话作为父的飞行名册
            if 在飞名册 is not None:#有飞行拉取
                在飞名册['父可用覆盖']=False#强制父不可用
                自身._名册过期.add(会话标识)#结算后再拉
            拥有名册=自身._名册们.get(会话标识)#本会话拥有的名册
            if 拥有名册 is not None and 取字段(拥有名册,'parentAvailable'):#仍标父可用
                新名册=dict(拥有名册)#拷贝
                新名册['parentAvailable']=False#立刻关掉
                自身._名册们[会话标识]=新名册#写回
            for 子标识,地址 in list(自身._地址们.items()):#每个已寻址子
                if 取字段(地址,'parentSessionId')!=会话标识:#不是本父
                    continue#跳过
                子实例=自身._会话们.get(子标识)#子实例
                if 子实例 is not None:#中继
                    子实例.处理子智能体父可用(False)#中继父不可用
            return#已处理
        if 种类=='host/session-status':#运行状态
            自身._记录变更({'kind':'status','sessionId':取字段(帧,'sessionId'),'running':取字段(帧,'running')})#更新列表 running
            实例=自身._会话们.get(取字段(帧,'sessionId'))#实例
            if 实例 is not None:#中继
                实例.处理运行中(取字段(帧,'running'))#中继到实例
            自身._更新名册活动(取字段(帧,'sessionId'),取字段(帧,'running'))#更新名册活动
            return#已处理
        if 种类=='host/agent-error':#无回合位置的智能体错误
            实例=自身._会话们.get(取字段(帧,'sessionId'))#实例
            if 实例 is not None:#中继
                实例.处理智能体错误(取字段(帧,'message'))#中继到实例
            return#不反映进列表
        return#stream/error 忽略；未知帧忽略

    def 处理已断开(自身):#连接代际死去
        """一个连接代际死去的时刻：丢掉代际作用域的直播状态。"""
        if len(自身._挂起交互)>0:#有侧栏挂起点
            自身._挂起交互.clear()#清掉代际状态
            自身._通知器.标脏()#刷新侧栏
        for 会话标识,缓冲 in list(自身._待缓冲.items()):#每个未实例化缓冲
            留下=[项 for 项 in 缓冲 if 取字段(取字段(项,'payload'),'type') not in ('approval/requested','question/requested')]#丢掉可回答请求
            if len(留下)==len(缓冲):#没有可回答项
                continue#跳过
            if len(留下)==0:#空则拿掉
                自身._待缓冲.pop(会话标识,None)#删
            else:#否则写回
                自身._待缓冲[会话标识]=留下#写回

    def 处理已连接(自身):#新连接代际就绪
        """每个连接代际之后：刷新会话基线并重建已打开窗口。"""
        _火忘(自身.刷新列表())#刷新列表基线
        选中地址=自身._地址们.get(自身._选中) if 自身._选中 is not None else None#当前寻址
        if 选中地址 is not None:#刷新选中子的父名册
            _火忘(自身.刷新子智能体(取字段(选中地址,'parentSessionId')))#刷新父
        if 自身._选中 is not None:#刷新选中会话自己的名册
            _火忘(自身.刷新子智能体(自身._选中))#刷新
        for 父会话标识 in list(自身._开着名册):#刷新正开着的菜单
            _火忘(自身.刷新子智能体(父会话标识))#刷新
        for 对象 in list(自身._会话们.values()):#重建已打开窗口
            _火忘(对象.重同步())#resync

    def _调度名册刷新(自身,父会话标识):#防抖刷新名册
        """一个父名册被选中或开着时，防抖成员再拉。"""
        if 父会话标识 in 自身._名册防抖:#已有定时器
            return#复用

        def 到期():#50ms 后
            """结算后刷新或立刻刷新。"""
            自身._名册防抖.pop(父会话标识,None)#先拿掉定时器
            if 父会话标识 in 自身._名册在飞:#仍在飞
                自身._名册过期.add(父会话标识)#标记过期
                return#等结算后尾随刷新
            _火忘(自身.刷新子智能体(父会话标识))#立即刷新

        定时器=threading.Timer(0.05,到期)#防抖窗口
        定时器.daemon=True#守护
        自身._名册防抖[父会话标识]=定时器#记下定时器
        定时器.start()#启动

    def _更新名册活动(自身,子会话标识,运行中):#更新名册活动
        """把一次 Agent 驱动的变迁应用到已加载和飞行中的名册。"""
        活动='running' if 运行中 else 'inactive'#活动值
        for 在飞 in 自身._名册在飞.values():#每个飞行拉取
            在飞['活动行'][子会话标识]=活动#覆盖本趟响应
        有变=False#已加载名册是否有变
        for 父会话标识,名册 in list(自身._名册们.items()):#每份已加载名册
            需要=False#是否需要改
            for 条目 in (取字段(名册,'entries') or []):#扫行
                if (取字段(条目,'kind')=='child' and 取字段(条目,'id')==子会话标识#目标子行
                    and 取字段(条目,'activity')!=活动):#活动不一致
                    需要=True#要改
                    break#停
            if not 需要:#活动已一致
                continue#下一份
            新行们=[]#映射新行
            for 条目 in (取字段(名册,'entries') or []):#逐行
                if 取字段(条目,'kind')!='child' or 取字段(条目,'id')!=子会话标识:#其它行不动
                    新行们.append(条目)#原样
                else:#改活动
                    新条目=dict(条目) if isinstance(条目,dict) else dict(条目.__dict__)#拷贝
                    新条目['activity']=活动#写入
                    新行们.append(新条目)#写入
            有变=True#有变
            新名册=dict(名册)#拷贝名册
            新名册['entries']=新行们#写回行
            自身._名册们[父会话标识]=新名册#写回名册
        if 有变:#有变才刷新
            自身._通知器.标脏()#刷新

    def _标记名册父可展开(自身,父会话标识):#标记父可展开
        """一次直接子智能体发布后，保住并投影正向可展开提示。"""
        自身._应用名册父可展开(父会话标识)#应用到已加载名册
        for 在飞 in 自身._名册在飞.values():#覆盖飞行响应
            在飞['可展开行'].add(父会话标识)#写入

    def _应用名册父可展开(自身,父会话标识):#应用到已加载名册
        """把一次正向可展开提示应用到每份含该唯一行 id 的已加载名册。"""
        有变=False#是否有变
        for 名册父标识,名册 in list(自身._名册们.items()):#每份已加载名册
            需要=False#是否需要改
            for 条目 in (取字段(名册,'entries') or []):#扫行
                if (取字段(条目,'kind')=='child' and 取字段(条目,'id')==父会话标识#该子行
                    and not 取字段(条目,'hasChildren')):#尚未展开
                    需要=True#要改
                    break#停
            if not 需要:#已有子女或不是它
                continue#下一份
            新行们=[]#映射新行
            for 条目 in (取字段(名册,'entries') or []):#逐行
                if (取字段(条目,'kind')!='child' or 取字段(条目,'id')!=父会话标识#其它行
                    or 取字段(条目,'hasChildren')):#已有子女
                    新行们.append(条目)#不动
                else:#标可展开
                    新条目=dict(条目) if isinstance(条目,dict) else dict(条目.__dict__)#拷贝
                    新条目['hasChildren']=True#标可展开
                    新行们.append(新条目)#写入
            有变=True#有变
            新名册=dict(名册)#拷贝
            新名册['entries']=新行们#写回
            自身._名册们[名册父标识]=新名册#写回名册
        if 有变:#有变才刷新
            自身._通知器.标脏()#刷新

    def _叠名册覆盖(自身,条目们,可展开行,活动行):#叠请求局部覆盖
        """把请求局部行变更折进一份名册结果再发布。"""
        结果=[]#叠后的行
        for 条目 in 条目们:#每行
            if 取字段(条目,'kind')!='child':#非子行不动
                结果.append(条目)#原样
                continue#下一行
            标识=取字段(条目,'id')#行 id
            活动=活动行.get(标识)#可选活动覆盖
            if 标识 not in 可展开行 and 活动 is None:#无覆盖
                结果.append(条目)#原样
                continue#下一行
            新条目=dict(条目) if isinstance(条目,dict) else dict(条目.__dict__)#拷贝
            if 标识 in 可展开行:#可展开
                新条目['hasChildren']=True#写入
            if 活动 is not None:#活动
                新条目['activity']=活动#写入
            结果.append(新条目)#叠后行
        return 结果#返回

    def _对账完成提醒(自身):#对账完成提醒
        """对照最新摘要对账完成提醒，在每次变更和拉取后急切进行。"""
        见到=set()#本轮仍在摘要里的 id
        for 项 in 自身._摘要们:#每条摘要
            标识=取字段(项,'sessionId')#id
            见到.add(标识)#记下仍在
            上次=自身._上次运行.get(标识)#上次 running
            本次=取字段(项,'running')#本次
            if 上次 is None:#首次观察
                自身._上次运行[标识]=本次#只记录，不武装
                continue#下一行
            if 上次 and (not 本次):#true→false 边沿
                if 标识!=自身._选中:#未选中才武装
                    自身._完成提醒.add(标识)#武装
            elif 本次:#又开跑
                自身._完成提醒.discard(标识)#解除提醒
            自身._上次运行[标识]=本次#记下本次
        for 标识 in list(自身._上次运行.keys()):#上次观察过的 id
            if 标识 not in 见到:#已不在摘要则丢掉
                del 自身._上次运行[标识]#删
        for 标识 in list(自身._完成提醒):#已武装的提醒
            if 标识 not in 见到:#已不在摘要则丢掉
                自身._完成提醒.discard(标识)#删

    def _建列表快照(自身):#编出列表快照
        """给侧栏用的不可变会话列表快照。"""
        合并=[]#带标题摘要
        for 摘要 in 自身._摘要们:#每条摘要叠标题
            投影仓库=自身._投影仓库们.get(取字段(摘要,'sessionId'))#该会话存储
            标题=投影仓库.取('title') if 投影仓库 is not None else None#标题格
            投影值们=投影仓库.值们() if 投影仓库 is not None else None#全部投影值
            行=dict(摘要) if isinstance(摘要,dict) else dict(摘要.__dict__)#原摘要
            if isinstance(标题,str) and 标题!='':#非空字符串才铺标题
                行['title']=标题#写入
            if 投影值们 is not None:#有值才铺投影
                行['projectionValues']=投影值们#写入
            合并.append(行)#收入
        挂起交互={}#每会话一个侧栏状态
        for 会话标识,交互们 in 自身._挂起交互.items():#每个有挂起的会话
            状态们=list(交互们.values())#全部状态
            状态=None#提问优先于审批
            for 候选 in 状态们:#找非审批
                if 候选!='approval':#提问或计划评审
                    状态=候选#记下
                    break#停
            if 状态 is None and len(状态们)>0:#全是审批
                状态=状态们[0]#取第一个
            if 状态 is not None:#有状态才写入
                挂起交互[会话标识]=状态#写入
        新鲜=展平谱系(合并,挂起交互,自身._完成提醒)#展平谱系
        条目们=[]#恢复行对象身份
        for 条目 in 新鲜:#每行
            标识=取字段(条目,'sessionId')#id
            先前=自身._行缓存.get(标识)#上一份同行
            if (先前 is not None#每个字段都匹配则复用引用
                and 取字段(先前,'updatedAt')==取字段(条目,'updatedAt')
                and 取字段(先前,'running')==取字段(条目,'running')
                and 取字段(先前,'blank')==取字段(条目,'blank')
                and 取字段(先前,'agentPreset')==取字段(条目,'agentPreset')
                and 取字段(先前,'parentSessionId')==取字段(条目,'parentSessionId')
                and 取字段(先前,'cwd')==取字段(条目,'cwd')
                and 取字段(先前,'origin')==取字段(条目,'origin')
                and 取字段(先前,'title')==取字段(条目,'title')
                and 取字段(先前,'depth')==取字段(条目,'depth')
                and 取字段(先前,'pendingInteraction')==取字段(条目,'pendingInteraction')
                and 取字段(先前,'projectionValues') is 取字段(条目,'projectionValues')
                and 取字段(先前,'completed')==取字段(条目,'completed')):
                条目们.append(先前)#复用旧对象
            else:#新引用
                自身._行缓存[标识]=条目#记下新对象
                条目们.append(条目)#新引用
        for 标识 in list(自身._行缓存.keys()):#缓存里的 id
            if not any(取字段(项,'sessionId')==标识 for 项 in 条目们):#已不在列表
                del 自身._行缓存[标识]#丢掉
        同序=(len(条目们)==len(自身._条目缓存)#数组引用是否可复用
            and all(条目们[i] is 自身._条目缓存[i] for i in range(len(条目们))))
        if not 同序:#顺序或身份变了才换数组
            自身._条目缓存=tuple(条目们)#换
        选中=自身._选中#当前选择
        if (选中 is not None#有选择
            and (any(取字段(项,'sessionId')==选中 for 项 in 自身._条目缓存) or 选中 in 自身._地址们)):#在列表上或已寻址
            当前=选中#露出
        else:#否则掩盖
            当前=None#掩盖
        return {#列表快照
            'items':自身._条目缓存,#稳定行数组
            'current':当前,#校验后的选中
            'state':自身._列表状态,#拉取活动
            'phase':自身._列表阶段,#到达阶段
            'error':自身._列表错误,#拉取错误
            'subagentsByParent':dict(自身._名册们),#名册字典
            'jobsBySession':dict(自身._任务按会话),#任务字典
            'currentAddress':自身._地址们.get(当前) if 当前 is not None else None,#当前寻址
        }#结束返回

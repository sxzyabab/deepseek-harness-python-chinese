"""包私有工作区实体。"""
import os
from datetime import datetime#ISO 时间戳
from zoneinfo import ZoneInfo#UTC 时区
from .路径 import 规范化真实路径
__all__=['工作区错误','工作区移动无效错误','工作区实体宿主字段','工作区实体']

class 工作区错误(Exception):
    """工作区包的一般错误。"""

class 工作区移动无效错误(Exception):
    """insertSessionBefore 点名了未入账的会话或锚。"""
    def __init__(自身,消息):
        """记下非法移动诊断。"""
        super().__init__(消息)

工作区实体宿主字段=('table','sessionPath','readSessionHeader','rememberSessionPath')#宿主机械

class 工作区实体:
    """唯一的消费方工作区实现；只由注册表构造。"""
    def __init__(自身,宿主,标识,记录):
        """记下注册表机械、稳定 id 与当前快照。宿主是 dict。"""
        自身.宿主=宿主
        自身.id=标识
        自身.记录=记录

    @property
    def path(自身):
        """规范路径。"""
        return 自身.记录['path']

    @property
    def title(自身):
        """展示标题。"""
        return 自身.记录['title']

    @property
    def createdAt(自身):
        """创建时刻。"""
        return 自身.记录['createdAt']

    @property
    def updatedAt(自身):
        """最近变更。"""
        return 自身.记录['updatedAt']

    @property
    def sessionIds(自身):
        """投影后的会话账本：cwd 仍匹配本工作区的成员。"""
        return [会话 for 会话 in 自身.记录['sessionIds'] if 自身.宿主['sessionPath'](会话)==自身.记录['path']]

    def setTitle(自身,标题):
        """设置标题。"""
        def 换标题(记录):
            """写链换标题。"""
            return {**记录,'title':标题}
        return 自身.变更(换标题)

    def attachSession(自身,会话号):
        """挂接会话；尚未入账时按头的 cwd 校验。头是 dict。"""
        if 会话号 not in 自身.记录['sessionIds']:#尚未入账才校验
            头=自身.宿主['readSessionHeader'](会话号)#同步
            if 'cwd' not in 头 or 头['cwd'] is None:
                raise 工作区错误("cannot attach session: its stored header carries no cwd to validate against")#不夹路径
            try:
                cwd=规范化真实路径(头['cwd'])
            except OSError as 错误:
                raise 工作区错误("cannot attach session: its cwd does not resolve, so it cannot be validated") from 错误
            if not os.path.isdir(cwd):
                raise 工作区错误("cannot attach session: its cwd is not a directory")
            if cwd!=自身.记录['path']:
                raise 工作区错误("cannot attach session: its cwd does not match this workspace")
            自身.宿主['rememberSessionPath'](会话号,cwd)
        def 前置入账(记录):
            """尚未入账则前置，已入账则原样。"""
            if 会话号 in 记录['sessionIds']:
                return 记录
            return {**记录,'sessionIds':[会话号,*记录['sessionIds']]}
        return 自身.变更(前置入账)

    def insertSessionBefore(自身,会话号,锚会话号=None):
        """按锚重排会话账本。"""
        def 重排(记录):
            """写链变更。"""
            if 会话号 not in 记录['sessionIds']:
                raise 工作区移动无效错误("cannot move session: the session is not accounted")
            if 锚会话号 is not None and 锚会话号 not in 记录['sessionIds']:
                raise 工作区移动无效错误("cannot move session: the anchor session is not accounted")
            if 锚会话号==会话号:
                return 记录
            去掉=[项 for 项 in 记录['sessionIds'] if 项!=会话号]
            位置=len(去掉) if 锚会话号 is None else 去掉.index(锚会话号)
            新顺序=去掉[:位置]+[会话号]+去掉[位置:]
            if 新顺序==记录['sessionIds']:
                return 记录
            return {**记录,'sessionIds':新顺序}
        return 自身.变更(重排)

    def detachSession(自身,会话号):
        """卸下会话，幂等。"""
        def 卸下(记录):
            """已入账则去掉，否则原样。"""
            if 会话号 not in 记录['sessionIds']:
                return 记录
            return {**记录,'sessionIds':[项 for 项 in 记录['sessionIds'] if 项!=会话号]}
        return 自身.变更(卸下)

    def status(自身):
        """目录状态：ok 或 missing-dir。"""
        try:
            return 'ok' if os.path.isdir(自身.记录['path']) else 'missing-dir'
        except OSError:
            return 'missing-dir'

    def 变更(自身,函数):
        """唯一写路径。无变更则返回同一快照对象，表 update 据此跳过写盘。"""
        def 更新(当前):
            """表更新函数。"""
            已改=函数(当前)
            修剪=[会话 for 会话 in 已改['sessionIds'] if 自身.宿主['sessionPath'](会话)==已改['path']]
            if 已改 is 当前 and len(修剪)==len(当前['sessionIds']):
                return 当前#同一对象，调用方据此跳过写盘
            return {**已改,'sessionIds':修剪,'updatedAt':datetime.now(ZoneInfo('UTC')).isoformat()}
        下一=自身.宿主['table']().update(自身.id,更新)#同步
        自身.记录=下一

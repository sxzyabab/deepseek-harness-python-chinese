"""包私有工作区实体。对齐上游 workspace/src/entity.ts。"""
import os#stat
from ...内核.会话 import 会话标识#会话 id 品牌
from .路径 import 规范化真实路径#路径规范化
__all__=['工作区移动无效错误','工作区实体宿主字段','工作区实体']#仅中文公开名

无变更哨兵=Exception('workspace record unchanged (internal sentinel)')#写链空操作哨兵

class 工作区移动无效错误(Exception):#移动非法
    """insertSessionBefore 点名了未入账的会话或锚。"""
    def __init__(自身,消息):#构造
        super().__init__(消息)#消息
        自身.name='WorkspaceMoveInvalidError'#错误名

工作区实体宿主字段=('table','sessionPath','readSessionHeader','rememberSessionPath')#宿主机械

class 工作区实体:#唯一工作区实现
    """唯一的消费方工作区实现；只由注册表构造。"""
    def __init__(自身,宿主,标识,记录):#构造实体
        自身._宿主=宿主#注册表机械
        自身.id=标识#稳定 id
        自身._记录=记录#当前快照

    @property
    def path(自身):#规范路径
        return 自身._记录['path']#来自快照

    @property
    def title(自身):#展示标题
        return 自身._记录['title']#来自快照

    @property
    def createdAt(自身):#创建时刻
        return 自身._记录['createdAt']#来自快照

    @property
    def updatedAt(自身):#最近变更
        return 自身._记录['updatedAt']#来自快照

    @property
    def sessionIds(自身):#投影后的会话账本
        return [会话 for 会话 in 自身._记录['sessionIds'] if 自身._宿主['sessionPath'](会话)==自身._记录['path']]#cwd 匹配

    def setTitle(自身,标题):#设置标题
        return 自身._变更(lambda 记录: {**记录,'title':标题})#写链换标题

    def attachSession(自身,会话号):#挂接会话
        if 会话号 not in 自身._记录['sessionIds']:#尚未入账才校验
            头=解开(自身._宿主['readSessionHeader'](会话号))#读头
            if 头.get('cwd') is None:#无 cwd
                raise Exception(f"cannot attach session '{会话号}' to workspace '{自身._记录['path']}': its stored header carries no cwd to validate against")#拒绝
            try:#规范化 cwd
                cwd=规范化真实路径(头['cwd'])#realpath
            except OSError as 错误:#解析失败
                raise Exception(f"cannot attach session '{会话号}' to workspace '{自身._记录['path']}': its cwd '{头['cwd']}' does not resolve, so it cannot be validated") from 错误#拒绝
            if not os.path.isdir(cwd):#不是目录
                raise Exception(f"cannot attach session '{会话号}' to workspace '{自身._记录['path']}': its cwd '{头['cwd']}' is not a directory")#拒绝
            if cwd!=自身._记录['path']:#路径不匹配
                raise Exception(f"cannot attach session '{会话号}' to workspace '{自身._记录['path']}': its cwd resolves to '{cwd}'")#拒绝
            自身._宿主['rememberSessionPath'](会话号,cwd)#发布索引
        return 自身._变更(lambda 记录: 记录 if 会话号 in 记录['sessionIds'] else {**记录,'sessionIds':[会话号,*记录['sessionIds']]})#前置入账

    def insertSessionBefore(自身,会话号,锚会话号=None):#按锚重排
        def 变更(记录):#写链变更
            if 会话号 not in 记录['sessionIds']:#未入账
                raise 工作区移动无效错误(f"cannot move session '{会话号}' in workspace '{记录['path']}': the session is not accounted")#拒绝
            if 锚会话号 is not None and 锚会话号 not in 记录['sessionIds']:#锚未入账
                raise 工作区移动无效错误(f"cannot move session '{会话号}' before '{锚会话号}' in workspace '{记录['path']}': the anchor session is not accounted")#拒绝
            if 锚会话号==会话号:#自己锚自己
                return 记录#不变
            去掉=[项 for 项 in 记录['sessionIds'] if 项!=会话号]#去掉被移动
            位置=len(去掉) if 锚会话号 is None else 去掉.index(锚会话号)#插入点
            新顺序=去掉[:位置]+[会话号]+去掉[位置:]#新顺序
            return 记录 if 新顺序==记录['sessionIds'] else {**记录,'sessionIds':新顺序}#可能不变
        return 自身._变更(变更)#写链

    def detachSession(自身,会话号):#卸下会话
        return 自身._变更(lambda 记录: {**记录,'sessionIds':[项 for 项 in 记录['sessionIds'] if 项!=会话号]} if 会话号 in 记录['sessionIds'] else 记录)#幂等

    def status(自身):#目录状态
        try:#stat
            return 'ok' if os.path.isdir(自身._记录['path']) else 'missing-dir'#目录可用
        except OSError:#任何 stat 失败
            return 'missing-dir'#不可用

    def _变更(自身,函数):#唯一写路径
        def 更新(当前):#表更新函数
            已改=函数(当前)#应用变更
            修剪=[会话 for 会话 in 已改['sessionIds'] if 自身._宿主['sessionPath'](会话)==已改['path']]#修剪候选
            if 已改 is 当前 and len(修剪)==len(当前['sessionIds']):#完全无变更
                raise 无变更哨兵#中止槽
            from datetime import datetime,timezone#时间戳
            return {**已改,'sessionIds':修剪,'updatedAt':datetime.now(timezone.utc).isoformat()}#盖戳
        try:#跑 update
            下一=解开(自身._宿主['table']().update(自身.id,更新))#写链槽
        except Exception as 错误:#捕获
            if 错误 is 无变更哨兵:#空操作
                return#结束
            raise 错误#其余上抛
        自身._记录=下一#替换快照

def 解开(值):#承诺则等待
    """承诺则等待，否则原样返回。"""
    等待=getattr(值,'wait',None) or getattr(值,'等待',None)#取 wait
    if callable(等待):#可等待
        return 等待()#等待
    return 值#同步

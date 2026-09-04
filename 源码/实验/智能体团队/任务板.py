"""共享 Team 任务 DAG 命令与经运行时充实的视图。

对齐上游 `agent-team/src/task-board.ts`。公开面仅中文名。
"""
import copy#脱离视图
from .错误 import 团队错误#领域错误
from .名册 import 解析活跃成员#活跃成员解析
from .任务图 import 断言任务图候选,任务图错误#图校验
from .类型 import 团队标识,团队任务标识#身份
from .校验 import 必填文本,写范围#输入规范化

__all__=['团队任务板']#仅中文公开名

任务图错误码={#图违例→错误码
    'missing':'TEAM_TASK_NOT_FOUND',#缺失
    'duplicate':'TEAM_INVALID_ARGUMENT',#重复
    'cycle':'TEAM_TASK_DEPENDENCY_CYCLE',#成环
}#映射结束

def 范围重叠(左,右):#范围是否重叠
    """两个规范化文件或目录前缀是否在路径分量上重叠。"""
    return 左==右 or 左.startswith(右+'/') or 右.startswith(左+'/')#重叠

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 团队任务板:#任务板
    """拥有 Team 任务限制、授权、转换与派生视图。"""
    def __init__(自身,日志,最大任务数):#构造
        """记下日志与任务上限。"""
        自身._日志=日志#日志
        自身._最大任务数=最大任务数#任务上限

    def 创建(自身,成员关系,请求):#建任务
        """在 Team Lead 日志中创建一条无主 pending 任务。"""
        根=成员关系['root']#Lead
        def 操作():#事务体
            """创建事务。"""
            状态=自身._日志.状态(根)#状态
            活动数=len([任务 for 任务 in 状态['tasks'] if 任务['status']!='deleted'])#活动数
            if 活动数>=自身._最大任务数:#上限
                raise 团队错误('Team task limit '+str(自身._最大任务数)+' reached','TEAM_TASK_LIMIT')#上限
            标识=团队任务标识('task-'+str(状态['nextTaskNumber']))#新 id
            if any(任务['id']==标识 for 任务 in 状态['tasks']):#id 耗尽
                raise 团队错误('Team task id space exhausted','TEAM_TASK_LIMIT')#id 耗尽
            任务={#快照
                'id':标识,#任务身份
                'revision':1,#版本
                'subject':必填文本(取字段(请求,'subject'),'subject',200),#标题
                'description':必填文本(取字段(请求,'description'),'description',16_384),#详情
                'status':'pending',#待处理
                'blockedBy':自身._依赖(取字段(请求,'blockedBy') or [],状态),#依赖
                'writeScopes':自身._写范围们(取字段(请求,'writeScopes') or []),#写范围
            }#快照结束
            自身._断言任务图(状态,任务)#图校验
            自身._日志.追加并刷新(根,'team/task',{'version':2,'teamId':团队标识(根.id),'task':任务})#持久
            return 自身._任务视图(根,状态,任务)#视图
        return 自身._日志.事务(根.id,操作)#串行

    def 获取(自身,成员关系,标识):#取任务
        """返回一条任务，含已删除 tombstone。"""
        根=成员关系['root']#Lead
        状态=自身._日志.状态(根)#状态
        任务=None#查找
        for 候选 in 状态['tasks']:#扫
            if 候选['id']==标识:#命中
                任务=候选#记下
                break#结束
        if 任务 is None:#未找到
            raise 团队错误('team task "'+str(标识)+'" not found','TEAM_TASK_NOT_FOUND')#未找到
        return 自身._任务视图(根,状态,任务)#视图

    def 列表(自身,成员关系):#列任务
        """按数字创建顺序列出当前未删除任务。"""
        根=成员关系['root']#Lead
        状态=自身._日志.状态(根)#状态
        return [自身._任务视图(根,状态,任务) for 任务 in 状态['tasks'] if 任务['status']!='deleted']#视图们

    def 更新(自身,调用方,成员关系,请求):#更新任务
        """compare-and-set 一次已授权的任务转换。"""
        根=成员关系['root']#Lead
        def 操作():#事务体
            """更新事务。"""
            状态=自身._日志.状态(根)#状态
            当前=None#查找
            for 任务 in 状态['tasks']:#扫
                if 任务['id']==取字段(请求,'taskId'):#命中
                    当前=任务#记下
                    break#结束
            if 当前 is None:#未找到
                raise 团队错误('team task "'+str(取字段(请求,'taskId'))+'" not found','TEAM_TASK_NOT_FOUND')#未找到
            if 当前['revision']!=取字段(请求,'expectedRevision'):#过期
                raise 团队错误(#过期
                    'stale team task "'+当前['id']+'" revision '+str(取字段(请求,'expectedRevision'))#文案前
                    +'; current revision is '+str(当前['revision']),#文案后
                    'TEAM_TASK_STALE_REVISION',#码
                )#抛出
            if 当前['status']=='deleted':#已删
                raise 团队错误('team task "'+当前['id']+'" is deleted','TEAM_TASK_DELETED')#已删
            下一=自身._下一快照(调用方,成员关系,状态,当前,请求)#动作转换
            任务={**下一,'revision':当前['revision']+1}#递增版本
            自身._断言任务图(状态,任务)#图校验
            自身._日志.追加并刷新(根,'team/task',{'version':2,'teamId':团队标识(根.id),'task':任务})#持久
            return 自身._任务视图(根,状态,任务)#视图
        return 自身._日志.事务(根.id,操作)#串行

    def _下一快照(自身,调用方,成员关系,状态,当前,请求):#动作转换
        """按动作计算下一快照（不含 revision）。"""
        是领导=成员关系['role']=='lead'#是否 Lead
        是所有者=当前.get('ownerId')==调用方.id#是否 owner
        def 授权所有者():#owner 或 Lead
            """任务变更授权。"""
            if not 是领导 and not 是所有者:#未授权
                raise 团队错误('task mutation requires its owner or Team Lead','TEAM_TASK_UNAUTHORIZED')#未授权
        动作=取字段(请求,'action')#动作
        if 动作=='claim':#认领
            return 自身._认领(调用方,状态,当前)#认领
        if 动作=='release':#释放
            授权所有者()#授权
            if 当前['status']!='in_progress':#非法
                raise 团队错误('only an in-progress task can be released','TEAM_TASK_INVALID_TRANSITION')#非法
            return 自身._去所有者({**当前,'status':'pending'})#释放
        if 动作=='edit':#编辑
            授权所有者()#授权
            return 自身._编辑(当前,请求)#编辑
        if 动作=='set_dependencies':#改依赖
            授权所有者()#授权
            if 取字段(请求,'blockedBy') is None:#缺字段
                raise 团队错误('set_dependencies requires blocked_by','TEAM_INVALID_ARGUMENT')#缺字段
            return {**当前,'blockedBy':自身._依赖(取字段(请求,'blockedBy'),状态,当前['id'])}#改依赖
        if 动作=='complete':#完成
            授权所有者()#授权
            if 当前['status']!='in_progress':#非法
                raise 团队错误('only an in-progress task can complete','TEAM_TASK_INVALID_TRANSITION')#非法
            return {**当前,'status':'completed'}#完成
        if 动作=='reopen':#重开
            授权所有者()#授权
            if 当前['status']!='completed':#非法
                raise 团队错误('only a completed task can reopen','TEAM_TASK_INVALID_TRANSITION')#非法
            return 自身._去所有者({**当前,'status':'pending'})#重开
        if 动作=='reassign':#改派
            return 自身._改派(成员关系,状态,当前,请求,是领导)#改派
        if 动作=='delete':#删除
            授权所有者()#授权
            return 自身._删除(状态,当前)#删除
        raise 团队错误('unsupported task action '+str(动作),'TEAM_INVALID_ARGUMENT')#未知动作

    def _认领(自身,调用方,状态,当前):#认领
        """认领一条就绪 pending 任务。"""
        所有者=当前.get('ownerId')#当前 owner
        if 所有者 is not None and 所有者!=调用方.id:#已被他人认领
            raise 团队错误('team task "'+当前['id']+'" is owned by another member','TEAM_TASK_ALREADY_CLAIMED')#已认领
        if 当前['status']!='pending' or not 自身._任务就绪(状态,当前):#未就绪
            raise 团队错误('team task "'+当前['id']+'" is not ready to claim','TEAM_TASK_BLOCKED')#阻塞
        return {**当前,'status':'in_progress','ownerId':调用方.id}#认领

    def _编辑(自身,当前,请求):#编辑
        """编辑标题、详情或写范围。"""
        if (取字段(请求,'subject') is None and 取字段(请求,'description') is None
                and 取字段(请求,'writeScopes') is None):#空编辑
            raise 团队错误('task edit requires subject, description, or write_scopes','TEAM_INVALID_ARGUMENT')#空编辑
        下一=dict(当前)#拷贝
        if 取字段(请求,'subject') is not None:#新标题
            下一['subject']=必填文本(取字段(请求,'subject'),'subject',200)#标题
        if 取字段(请求,'description') is not None:#新详情
            下一['description']=必填文本(取字段(请求,'description'),'description',16_384)#详情
        if 取字段(请求,'writeScopes') is not None:#新写范围
            下一['writeScopes']=自身._写范围们(取字段(请求,'writeScopes'))#写范围
        return 下一#编辑结果

    def _改派(自身,成员关系,状态,当前,请求,是领导):#改派
        """Lead 改派或清空 owner。"""
        if not 是领导:#仅 Lead
            raise 团队错误('only the Team Lead can reassign tasks','TEAM_LEAD_REQUIRED')#仅 Lead
        if 当前['status'] not in ('pending','in_progress'):#非法状态
            raise 团队错误('only a pending or in-progress task can be reassigned','TEAM_TASK_INVALID_TRANSITION')#非法
        所有者名=取字段(请求,'owner')#新 owner 名
        if 所有者名 is None or len(所有者名.strip())==0:#清空
            return 自身._去所有者({**当前,'status':'pending'})#清空
        if not 自身._任务就绪(状态,当前):#阻塞
            raise 团队错误('team task "'+当前['id']+'" is blocked','TEAM_TASK_BLOCKED')#阻塞
        受派=解析活跃成员(成员关系['root'],状态,所有者名)#受派人
        return {**当前,'status':'in_progress','ownerId':受派['id']}#改派

    def _删除(自身,状态,当前):#删除
        """删除无依赖者的任务。"""
        for 任务 in 状态['tasks']:#查依赖者
            if 任务['status']!='deleted' and 任务['id']!=当前['id'] and 当前['id'] in 任务['blockedBy']:#仍阻塞
                raise 团队错误('team task "'+当前['id']+'" still blocks "'+任务['id']+'"','TEAM_TASK_HAS_DEPENDENTS')#有依赖者
        return {**当前,'status':'deleted'}#删除

    def _依赖(自身,值们,状态,自身标识=None):#规范化依赖
        """对照当前任务图校验并去重依赖 id。"""
        已见=set()#已见
        结果=[]#结果
        for 标识 in 值们:#逐依赖
            if 标识==自身标识:#自指
                raise 团队错误('a team task cannot block itself','TEAM_TASK_DEPENDENCY_CYCLE')#自指
            if 标识 in 已见:#重复
                raise 团队错误('duplicate blocker "'+str(标识)+'"','TEAM_INVALID_ARGUMENT')#重复
            任务=None#查找
            for 候选 in 状态['tasks']:#扫
                if 候选['id']==标识:#命中
                    任务=候选#记下
                    break#结束
            if 任务 is None or 任务['status']=='deleted':#缺失
                raise 团队错误('blocker task "'+str(标识)+'" not found','TEAM_TASK_NOT_FOUND')#缺失
            已见.add(标识)#记已见
            结果.append(标识)#追加
        return 结果#依赖表

    def _写范围们(自身,值们):#写范围
        """规范化并去重任务写范围。"""
        return list(dict.fromkeys(写范围(值) for 值 in 值们))#去重保序

    def _断言任务图(自身,状态,候选):#断言图
        """把共享任务图校验映射到稳定命令错误码。"""
        try:#试校验
            断言任务图候选(状态['tasks'],候选)#图校验
        except 任务图错误 as 错误:#映射
            raise 团队错误(str(错误),任务图错误码[错误.违例],{'cause':错误})#映射
        except Exception:#其它
            raise#上抛

    def _任务就绪(自身,状态,任务):#是否就绪
        """当前全部 blocker 是否已完成。"""
        for 标识 in 任务['blockedBy']:#逐 blocker
            命中=None#查找
            for 候选 in 状态['tasks']:#扫
                if 候选['id']==标识:#命中
                    命中=候选#记下
                    break#结束
            if 命中 is None or 命中['status']!='completed':#未完成
                return False#未就绪
        return True#就绪

    def _去所有者(自身,任务):#去 owner
        """移除可选 owner 字段。"""
        下一=dict(任务)#拷贝
        下一.pop('ownerId',None)#去掉
        return 下一#无 owner

    def _任务视图(自身,根,状态,任务):#任务视图
        """构建带 owner 名、就绪性与写范围重叠警告的任务视图。"""
        所有者名=None#owner 名
        所有者标识=任务.get('ownerId')#owner id
        if 所有者标识 is not None:#有 owner
            if 所有者标识==根.id:#Lead
                所有者名='lead'#伪名
            else:#teammate
                for 成员 in 状态['members']:#扫
                    if 成员['id']==所有者标识:#命中
                        所有者名=成员['name']#名字
                        break#结束
        警告=set()#写范围警告
        for 其它 in 状态['tasks']:#扫其它进行中
            if 其它['id']==任务['id'] or 其它['status']!='in_progress':#跳过
                continue#下一
            if any(范围重叠(左,右) for 左 in 任务['writeScopes'] for 右 in 其它['writeScopes']):#重叠
                警告.add('write scopes overlap with '+其它['id'])#警告
        视图={#视图体
            'id':任务['id'],#身份
            'revision':任务['revision'],#版本
            'subject':任务['subject'],#标题
            'description':任务['description'],#详情
            'status':任务['status'],#状态
            'blockedBy':copy.deepcopy(任务['blockedBy']),#依赖
            'writeScopes':copy.deepcopy(任务['writeScopes']),#写范围
            'ready':任务['status']=='pending' and 自身._任务就绪(状态,任务),#就绪
            'writeScopeWarnings':list(警告),#警告
        }#视图骨架
        if 所有者名 is not None:#有 owner 名
            视图['ownerName']=所有者名#展开
        return 视图#视图

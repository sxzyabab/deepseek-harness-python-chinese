"""冷安全会话列表与搜索投影。

对齐上游 `session-controller/src/list.ts`。公开面仅中文名。
"""
from .常量 import 会话搜索结果上限,会话搜索片段最大码点,会话搜索查询最大字符#常量
from .工具 import 取字段,解开,远程错误,远程错误消息#辅助

__all__=['应用会话列表元数据','截断unicode码点','会话列表']#仅中文公开名

冷摘要批大小=16#冷摘要批大小
搜索提供方调用上限=100#搜索调用预算
消息类型=set(['user/message','assistant/message'])#可搜索类型

def 应用会话列表元数据(状态,事件):#折叠列表元数据
    """按事件推进 sessionListMetadata。"""
    空白=取字段(状态,'blank') and 取字段(事件,'type')!='turn/start'#仍空白
    最近提示=取字段(状态,'lastPromptAt')#原值
    if 取字段(事件,'type')=='user/message' and 取字段(取字段(取字段(事件,'data'),'source'),'kind')=='user':#用户消息
        最近提示=取字段(事件,'time')#更新时间
    if 空白==取字段(状态,'blank') and 最近提示==取字段(状态,'lastPromptAt'):#未变
        return 状态#原样
    return {'blank':空白,'lastPromptAt':最近提示}#新状态

def 截断unicode码点(文本,最大码点):#截断码点
    """保留至多最大码点的 Unicode 前缀。"""
    计数=0#计数
    结束=0#字节结束
    for 码点 in 文本:#逐码点
        if 计数==最大码点:#达到
            return 文本[:结束]#截断
        计数+=1#加一
        结束+=len(码点)#前进
    return 文本#原样

class 会话列表:#列表与搜索
    """拥有列表投影注册、冷摘要与授权搜索。"""

    def __init__(自身,上下文,冷空白探测最大字节):#构造
        """注册 sessionListMetadata 列。"""
        自身._上下文=上下文#Cordis
        自身._冷上限=冷空白探测最大字节#冷探测上限
        上下文.sessionProjections.register({#列表元数据列
            'key':'sessionListMetadata',#键
            'init':lambda:{'blank':True,'lastPromptAt':None},#初值
            'apply':应用会话列表元数据,#折叠
            'wire':{'view':lambda 状态:状态},#直通
            'stateVersion':1,#版本
        })#register
        def 挂附件(附件上下文):#等 attachments
            """注册 imageLimits 列。"""
            上下文.sessionProjections.register({#imageLimits
                'key':'imageLimits',#键
                'init':lambda:None,#状态
                'apply':lambda 状态,_:状态,#不变
                'wire':{'view':lambda _:附件上下文.attachments.imageLimits},#视图
                'stateVersion':1,#版本
            })#register
        上下文.inject(['attachments'],挂附件)#inject

    def 摘要(自身,会话):#附着摘要
        """构建当前附着会话摘要。"""
        投影=自身._投影(取字段(会话,'header'),会话)#投影
        元数据=取字段(取字段(投影,'values'),'sessionListMetadata') if 投影 is not None else None#元数据
        智能体=自身._上下文.agents.get(取字段(会话,'id'))#智能体
        return {#摘要
            'sessionId':取字段(会话,'id'),#id
            'updatedAt':自身._更新时间(取字段(会话,'header'),元数据),#活动
            'running':取字段(智能体,'status')=='running' if 智能体 is not None else False,#运行中
            'blank':取字段(元数据,'blank') if 元数据 is not None else 取字段(会话,'seq')==0,#空白
            **自身._列表字段(取字段(会话,'header')),#头字段
            **({} if 投影 is None else {'projections':投影}),#投影
        }#结束

    def 列表(自身,信号=None):#列全部
        """读可见附着与持久会话摘要。"""
        if 信号 is not None and 信号已中止(信号):#取消
            raise 远程错误('gateway/cancelled','session list was aborted',{})#取消
        记录们=解开(自身._上下文.sessionQuery.listSessions(信号))#列持久
        条目=[]#结果
        冷头们=[]#冷头
        for 记录 in 记录们:#逐条
            头=取字段(记录,'header')#头
            活=自身._上下文.sessions.get(取字段(头,'id'))#附着
            if 活 is not None:#附着
                条目.append(自身.摘要(活))#摘要
                continue#下一条
            if 取字段(头,'cwd') is None:#无 cwd
                continue#跳过
            冷头们.append(头)#冷
        for 偏移 in range(0,len(冷头们),冷摘要批大小):#分批
            批=冷头们[偏移:偏移+冷摘要批大小]#一批
            for 头 in 批:#逐头
                条目.append(解开(自身._冷摘要(头,信号)))#冷摘要
        条目.sort(key=lambda 项:取字段(项,'updatedAt'),reverse=True)#按活动降序
        return 条目#列表

    def 搜索(自身,查询,信号):#搜索
        """搜索可见消息内容。"""
        规范化=自身._规范化查询(查询)#规范化
        if 信号已中止(信号):#取消
            raise 远程错误('gateway/cancelled','session search was aborted',{})#取消
        提供方=自身._上下文.get('sessionQuery')#查询服务
        if 提供方 is None:#缺席
            raise 远程错误('gateway/internal','session search is unavailable: this deployment does not mount @deepseek-ai/dsh-session-query',{})#拒绝
        try:#搜索循环
            可见=解开(提供方.listSessions(信号))#可见
            可见标识=set(取字段(取字段(记录,'header'),'id') for 记录 in 可见 if 取字段(取字段(记录,'header'),'cwd') is not None)#id 集
            if len(可见标识)==0:#空
                return {'items':[],'hasMore':False}#空结果
            授权=[]#命中
            已接受=set()#去重
            游标=None#continuation
            调用次数=0#预算
            页上限=会话搜索结果上限#页大小
            while len(授权)<=会话搜索结果上限:#收集
                if 信号已中止(信号):#取消
                    raise 远程错误('gateway/cancelled','session search was aborted',{})#取消
                if 调用次数>=搜索提供方调用上限:#超预算
                    raise Exception('session search provider exceeded work budget')#失败
                调用次数+=1#计数
                请求={'query':规范化,'eventFilters':[{'kind':'type','values':['user/message','assistant/message']},{'kind':'surface','values':['current']}],'limit':页上限}#请求
                if 游标 is not None:#续页
                    请求['cursor']=游标#游标
                页=解开(提供方.searchSessions(请求,{'signal':信号}))#搜索
                for 命中 in 取字段(页,'items') or []:#逐命中
                    if len(授权)>会话搜索结果上限:#超上限
                        continue#跳过
                    头标识=取字段(取字段(命中,'header'),'id')#会话
                    最佳=取字段(命中,'bestMatch')#最佳
                    if (头标识 not in 可见标识 or 取字段(最佳,'sessionId')!=头标识 or 取字段(最佳,'surface')!='current' or 取字段(最佳,'type') not in 消息类型 or 头标识 in 已接受):#过滤
                        continue#跳过
                    已接受.add(头标识)#记下
                    授权.append({'sessionId':头标识,'snippet':截断unicode码点(取字段(最佳,'snippet'),会话搜索片段最大码点)})#收录
                游标=取字段(页,'nextCursor')#下一游标
                if len(授权)>会话搜索结果上限 or 游标 is None:#结束
                    break#退出
            return {'items':授权[:会话搜索结果上限],'hasMore':len(授权)>会话搜索结果上限}#结果
        except 远程错误:#已是 Remote
            raise#原样
        except Exception as 错误:#其它
            if 信号已中止(信号):#取消
                raise 远程错误('gateway/cancelled','session search was aborted',{})#取消
            raise 远程错误('gateway/internal','session search failed: '+远程错误消息(错误),{})#内部

    def _规范化查询(自身,查询):#规范化查询
        """修剪并校验搜索查询。"""
        规范化=str(查询 or '').strip()#修剪
        if 规范化=='':#空
            raise 远程错误('gateway/bad-request','session search query must not be empty',{})#拒绝
        if len(规范化)>会话搜索查询最大字符:#太长
            raise 远程错误('gateway/bad-request','session search query too long',{})#拒绝
        if '\0' in 规范化:#NUL
            raise 远程错误('gateway/bad-request','session search query must not contain NUL',{})#拒绝
        return 规范化#返回

    def _冷摘要(自身,头,信号):#冷摘要一条
        """为冷会话构建摘要。"""
        缓存=自身._投影(头,None)#缓存投影
        投影=缓存#默认
        if 取字段(取字段(取字段(缓存,'values'),'sessionListMetadata'),'blank') is not False:#需探测
            探测=自身._探测小冷(头,信号)#探测
            if 探测 is not None:#有结果
                投影=探测#采用
        竞态=自身._上下文.sessions.get(取字段(头,'id'))#竞态附着
        if 竞态 is not None:#已附着
            return 自身.摘要(竞态)#活摘要
        元数据=取字段(取字段(投影,'values'),'sessionListMetadata') if 投影 is not None else None#元数据
        return {#冷摘要
            'sessionId':取字段(头,'id'),#id
            'updatedAt':自身._更新时间(头,元数据),#活动
            'running':False,#冷会话不运行
            'blank':取字段(元数据,'blank') if 元数据 is not None else False,#空白未知为可见
            **自身._列表字段(头),#头字段
            **({} if 投影 is None else {'projections':投影}),#投影
        }#结束

    def _探测小冷(自身,头,信号):#小冷探测
        """小工件全量观测。"""
        if 自身._冷上限==0:#禁用
            return None#跳过
        持久=自身._上下文.get('sessionPersistence')#持久
        if 持久 is None:#无
            return None#跳过
        位置=持久.locate(头) if hasattr(持久,'locate') else None#定位
        if 位置 is None:#无位置
            return None#跳过
        try:#观测
            观测=解开(自身._上下文.sessionQuery.observeSession(取字段(头,'id'),{'signal':信号,'projectionMode':'all'}))#观测
            try:#读投影
                块=取字段(观测,'projections')#投影块
                if 块 is None:#无
                    return None#跳过
                return {'asOfSeq':取字段(块,'asOfSeq'),'values':取字段(块,'values')}#提示
            finally:#关闭
                关闭=getattr(观测,'close',None)#close
                if callable(关闭):#可关
                    关闭()#关
        except Exception:#失败
            return None#可见但未知

    def _投影(自身,头,会话):#读缓存投影
        """读列表提示投影块。"""
        try:#读缓存
            if 会话 is None:#冷
                缓存=自身._上下文.get('sessionProjectionCache')#缓存服务
                块=None if 缓存 is None else 缓存.cachedSnapshot(头)#冷快照
            else:#活
                块=自身._上下文.sessionProjections.cachedSnapshot(会话)#活快照
            if 块 is None or len(取字段(块,'values') or {})==0:#空
                return None#无
            return {'asOfSeq':取字段(块,'asOfSeq'),'values':取字段(块,'values')}#块
        except Exception:#失败
            return None#无列

    def _更新时间(自身,头,元数据):#更新时间
        """取列表排序时间。"""
        最近=0 if 元数据 is None else (取字段(元数据,'lastPromptAt') or 0)#最近提示
        return max(取字段(头,'createdAt') or 0,最近)#最大

    def _列表字段(自身,头):#列表附加字段
        """投影头中的列表字段。"""
        结果={}#结果
        if 取字段(头,'parentSession') is not None:#父会话
            结果['parentSessionId']=取字段(头,'parentSession')#父
        if 取字段(头,'origin') is not None:#来源
            结果['origin']=取字段(头,'origin')#origin
        if 取字段(头,'cwd') is not None:#cwd
            结果['cwd']=取字段(头,'cwd')#cwd
        return 结果#返回

def 信号已中止(信号):#读中止
    """AbortSignal 是否已中止。"""
    return bool(getattr(信号,'aborted',False)) if 信号 is not None else False#aborted

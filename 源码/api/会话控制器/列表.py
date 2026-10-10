'冷安全会话列表与搜索投影'
import time
from .常量 import 会话搜索结果上限,会话搜索片段最大字节,会话搜索查询最大字节#常量
from .远程错误与并发 import 远程错误消息,已中止#远程错误消息与中止
from .异常 import 远程错误#本包异常

__all__=['应用会话列表元数据','截断码位','会话列表']#仅中文公开名

搜索提供方调用上限=100#搜索调用预算
消息类型=set(['user/message','assistant/message'])#可搜索类型

def 应用会话列表元数据(状态,事件):
    '按事件推进 sessionListMetadata。状态与事件为 dict'
    空白=状态['blank'] and 事件['type']!='turn/start'#仍空白
    最近提示=状态['lastPromptAt'] if 'lastPromptAt' in 状态 else None#原值
    源=事件['data']['source'] if 'data' in 事件 and isinstance(事件['data'],dict) and 'source' in 事件['data'] else None#来源
    种类=源['kind'] if isinstance(源,dict) and 'kind' in 源 else None#kind
    if 事件['type']=='user/message' and 种类=='user':#用户消息
        最近提示=事件['time']#更新时间
    if 空白==状态['blank'] and 最近提示==(状态['lastPromptAt'] if 'lastPromptAt' in 状态 else None):#未变
        return 状态#原样
    return {'blank':空白,'lastPromptAt':最近提示}#新状态

def 初值列表元数据():
    'sessionListMetadata 初值'
    return {'blank':True,'lastPromptAt':None}#初值

def 直通视图(状态):
    '线上直通'
    return 状态#原样

def 不变折叠(状态,_事件):
    'imageLimits 状态不变'
    return 状态#不变

def 按更新时间(项):
    '列表排序键。项为 dict'
    return 项['updatedAt']#活动时间

def 截断码位(值,上限):
    '最长前缀，至多上限个 Unicode 码位'
    计数=0#已数
    for 下标,字 in enumerate(值):#逐码位
        if 计数==上限:#到顶
            return 值[:下标]#前缀
        计数+=1#推进
    return 值#未超

class 会话列表:
    '拥有列表投影注册、冷摘要与授权搜索'

    def __init__(自身,上下文,工作切片毫秒=16):
        '注册 sessionListMetadata 列'
        自身._上下文=上下文#Cordis
        自身._工作切片毫秒=工作切片毫秒#让出预算
        上下文.sessionProjections.register({#列表元数据列
            'key':'sessionListMetadata',#键
            'init':初值列表元数据,#初值
            'apply':应用会话列表元数据,#折叠
            'wire':{'view':直通视图},#直通
            'stateVersion':1,#版本
        })#register
        def 挂附件(附件上下文):
            '注册 imageLimits 列'
            def 视图图像上限(_状态):
                '读附件上限'
                return 附件上下文.attachments.imageLimits#视图
            def 初值图像上限():
                '无状态'
                return None#状态
            上下文.sessionProjections.register({#imageLimits
                'key':'imageLimits',#键
                'init':初值图像上限,#状态
                'apply':不变折叠,#不变
                'wire':{'view':视图图像上限},#视图
                'stateVersion':1,#版本
            })#register
        上下文.依赖启动(['attachments'],挂附件)#依赖启动

    def 摘要(自身,会话):
        '构建当前附着会话摘要'
        投影=自身._投影(会话.header,会话)#投影
        元数据=投影['values']['sessionListMetadata'] if 投影 is not None and 'values' in 投影 and 'sessionListMetadata' in 投影['values'] else None#元数据
        智能体=自身._上下文.agents.get(会话.id)#智能体
        条目={#摘要
            'sessionId':会话.id,#id
            'updatedAt':自身._更新时间(会话.header,元数据),#活动
            'agentAvailable':智能体 is not None and getattr(智能体,'session',None) is 会话,#同一会话
            'formatStatus':'current',#当前格式
            'running':智能体.status=='running' if 智能体 is not None else False,#运行中
            'blank':元数据['blank'] if 元数据 is not None else 会话.seq==0,#空白
        }#基础
        条目.update(自身._列表字段(会话.header))#头字段
        if 投影 is not None:#有投影
            条目['projections']=投影#投影
        return 条目

    def 列表(自身,信号=None):
        '读可见附着与持久会话摘要'
        if 信号 is not None and 已中止(信号):#取消
            raise 远程错误('gateway/cancelled','session list was aborted',{})#取消
        记录列表=自身._上下文.sessionQuery.listSessions(信号)#列持久
        条目=[]#结果
        冷记录=[]#冷记录
        让出期限=time.perf_counter()+自身._工作切片毫秒/1000.0#让出
        for 记录 in 记录列表:#逐条，记录为 dict
            if 信号 is not None and 已中止(信号):#取消
                raise 远程错误('gateway/cancelled','session list was aborted',{})#取消
            头=记录['header']#头
            活=自身._上下文.sessions.get(头['id'])#附着
            if 活 is not None:#附着
                条目.append(自身.摘要(活))#摘要
            elif 'cwd' in 头 and 头['cwd'] is not None:#有 cwd
                冷记录.append(记录)#冷
            if time.perf_counter()>=让出期限:#让出
                time.sleep(0)#让出
                if 信号 is not None and 已中止(信号):#取消
                    raise 远程错误('gateway/cancelled','session list was aborted',{})#取消
                让出期限=time.perf_counter()+自身._工作切片毫秒/1000.0#重置
        for 记录 in 冷记录:#冷摘要
            if 信号 is not None and 已中止(信号):#取消
                raise 远程错误('gateway/cancelled','session list was aborted',{})#取消
            条目.append(自身._冷摘要(记录))#冷摘要
            if time.perf_counter()>=让出期限:#让出
                time.sleep(0)#让出
                if 信号 is not None and 已中止(信号):#取消
                    raise 远程错误('gateway/cancelled','session list was aborted',{})#取消
                让出期限=time.perf_counter()+自身._工作切片毫秒/1000.0#重置
        条目.sort(key=按更新时间,reverse=True)#按活动降序
        return 条目#列表

    def 搜索(自身,查询,信号):
        '搜索可见消息内容'
        规范化=自身._规范化查询(查询)#规范化
        if 已中止(信号):#取消
            raise 远程错误('gateway/cancelled','session search was aborted',{})#取消
        提供方=自身._上下文.获取服务('sessionQuery')#查询服务
        if 提供方 is None:#缺席
            raise 远程错误('gateway/internal','session search is unavailable: this deployment does not mount @deepseek-ai/dsh-session-query',{})#拒绝
        try:
            可见=提供方.listSessions(信号)#可见
            可见标识=set()#id 集
            for 记录 in 可见:#逐条
                头=记录['header']#头
                if 'cwd' in 头 and 头['cwd'] is not None:#有 cwd
                    可见标识.add(头['id'])#记下
            if len(可见标识)==0:#空
                return {'items':[],'hasMore':False}#空结果
            授权=[]#命中
            已接受=set()#去重
            见过游标=set()#续页游标
            游标=None#continuation
            调用次数=0#预算
            页上限=会话搜索结果上限#页大小
            while len(授权)<=会话搜索结果上限:#收集
                if 已中止(信号):#取消
                    raise 远程错误('gateway/cancelled','session search was aborted',{})#取消
                if 调用次数>=搜索提供方调用上限:#超预算
                    raise ValueError('session search provider exceeded the '+str(搜索提供方调用上限)+'-call work budget')
                调用次数+=1#计数
                请求游标=游标#本页游标
                请求上限=页上限#本页上限
                请求={'query':规范化,'eventFilters':[{'kind':'type','values':['user/message','assistant/message']},{'kind':'surface','values':['current']}],'limit':请求上限}#请求
                if 请求游标 is not None:#续页
                    请求['cursor']=请求游标#游标
                try:#搜索
                    页=提供方.searchSessions(请求,{'signal':信号})#搜索，页为 dict
                except Exception as 错误:#提供方拒绝
                    if 已中止(信号):#取消
                        raise#交给外层
                    码=getattr(错误,'code',None)#查询码
                    if 请求游标 is None and 码=='SESSION_QUERY_INVALID_LIMIT' and 请求上限>1:#缩小页
                        页上限=max(1,请求上限//2)#减半
                        continue#重试
                    if 请求游标 is not None and 码=='SESSION_QUERY_STALE_CURSOR':#游标过期
                        授权.clear()#清空
                        已接受.clear()#清空
                        见过游标.clear()#清空
                        游标=None#从头
                        continue#重试
                    raise#其余
                命中列表=页['items'] if 'items' in 页 and 页['items'] is not None else []#命中
                if len(命中列表)>请求上限:#超页
                    raise ValueError('session search provider returned '+str(len(命中列表))+' items; maximum is '+str(请求上限))
                for 命中 in 命中列表:#逐命中
                    if len(授权)>会话搜索结果上限:#超上限
                        continue#跳过
                    头标识=命中['header']['id']#会话
                    最佳=命中['bestMatch']#最佳
                    if 头标识 not in 可见标识:#不可见
                        continue#跳过
                    if 最佳['sessionId']!=头标识 or 最佳['surface']!='current' or 最佳['type'] not in 消息类型 or 头标识 in 已接受:#过滤
                        continue#跳过
                    已接受.add(头标识)#记下
                    授权.append({'sessionId':头标识,'snippet':截断码位(最佳['snippet'],会话搜索片段最大字节)})#收录
                游标=页['nextCursor'] if 'nextCursor' in 页 else None#下一游标
                if 游标 is not None:#有续页
                    if 游标 in 见过游标:#重复
                        raise ValueError('session search provider repeated a continuation cursor')
                    见过游标.add(游标)#记下
                if len(授权)>会话搜索结果上限 or 游标 is None:
                    break#退出
            return {'items':授权[:会话搜索结果上限],'hasMore':len(授权)>会话搜索结果上限}#结果
        except 远程错误:
            raise#原样
        except Exception as 错误:
            if 已中止(信号) or getattr(错误,'code',None)=='SESSION_QUERY_ABORTED':#取消
                raise 远程错误('gateway/cancelled','session search was aborted',{})#取消
            raise 远程错误('gateway/internal','session search failed: '+远程错误消息(错误),{})#内部

    def _规范化查询(自身,查询):
        '修剪并校验搜索查询'
        规范化=str(查询 if 查询 is not None else '').strip()#修剪，?? 语义保留空串
        if 规范化=='':#空
            raise 远程错误('gateway/bad-request','session search query must not be empty',{})#拒绝
        if len(规范化)>会话搜索查询最大字节:#太长，按码位
            raise 远程错误('gateway/bad-request','session search query must contain at most '+str(会话搜索查询最大字节)+' UTF-16 code units',{})#拒绝
        if '\0' in 规范化:#NUL
            raise 远程错误('gateway/bad-request','session search query must not contain NUL',{})#拒绝
        return 规范化#返回

    def _冷摘要(自身,记录):
        '为冷会话构建摘要。记录含 header 与可选 formatStatus'
        头=记录['header'] if isinstance(记录,dict) and 'header' in 记录 else 记录#头
        投影=自身._投影(头,None)#缓存投影
        元数据=投影['values']['sessionListMetadata'] if 投影 is not None and 'values' in 投影 and 'sessionListMetadata' in 投影['values'] else None#元数据
        条目={#冷摘要
            'sessionId':头['id'],#id
            'updatedAt':自身._更新时间(头,元数据),#活动
            'agentAvailable':False,#冷
            'running':False,#冷会话不运行
            'blank':元数据['blank'] if 元数据 is not None and 'blank' in 元数据 else False,#空白未知为可见
        }#基础
        if isinstance(记录,dict) and 记录.get('formatStatus') is not None:#格式状态
            条目['formatStatus']=记录['formatStatus']#写入
        条目.update(自身._列表字段(头))#头字段
        if 投影 is not None:#有投影
            条目['projections']=投影#投影
        return 条目

    def _投影(自身,头,会话):
        '读列表提示投影块。头为 dict'
        try:
            if 会话 is None:#冷
                种类='cached'#缓存序列
                缓存=自身._上下文.获取服务('sessionProjectionCache')#缓存服务
                块=None#块
                if 缓存 is not None:#有缓存
                    块=缓存.cachedSnapshot(头)#冷快照
                    if 块 is None and hasattr(缓存,'cachedPredecessorTitle'):#标题前驱
                        块=缓存.cachedPredecessorTitle(头)#前驱
            else:#活
                种类='sequenced'#活序列
                块=自身._上下文.sessionProjections.cachedSnapshot(会话)#活快照
            if 块 is None:#无
                return None#无
            值列表=块['values'] if isinstance(块,dict) and 'values' in 块 else getattr(块,'values',None)#值
            if 值列表 is None or len(值列表)==0:#空
                return None#无
            序号=块['asOfSeq'] if isinstance(块,dict) else 块.asOfSeq#水位
            return {'kind':种类,'asOfSeq':序号,'values':值列表}#块
        except (OSError,ValueError,TypeError,KeyError,AttributeError):
            return None#无列

    def _更新时间(自身,头,元数据):
        '取列表排序时间。头与元数据为 dict'
        最近=0#默认
        if 元数据 is not None and 'lastPromptAt' in 元数据 and 元数据['lastPromptAt'] is not None:#有最近提示
            最近=元数据['lastPromptAt']#最近提示
        创建=头['createdAt'] if 'createdAt' in 头 and 头['createdAt'] is not None else 0#创建
        return max(创建,最近)#最大

    def _列表字段(自身,头):
        '投影头中的列表字段。头为 dict'
        结果={}#结果
        if 'parentSession' in 头 and 头['parentSession'] is not None:#父会话
            结果['parentSessionId']=头['parentSession']#父
        if 'origin' in 头 and 头['origin'] is not None:#来源
            结果['origin']=头['origin']#origin
        if 'cwd' in 头 and 头['cwd'] is not None:#cwd
            结果['cwd']=头['cwd']#cwd
        return 结果#返回

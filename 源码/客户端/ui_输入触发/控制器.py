"""InputTriggerController：触发管道的每会话半边。

对齐上游 `ui-input-trigger/src/client/controller.ts`。公开面仅中文名。
拥有全部可变交互状态——权威触发命中、菜单仓库、候选拉取生命周期。
"""
from .探测 import 检测触发#光标处触发检测
from .菜单归约 import 菜单关闭,铺分组,菜单归约#关菜单态、铺组、归约

__all__=['触发控制器','简易快照仓']#仅中文公开名

class 简易快照仓:#快照仓
    """订阅 + set。"""
    def __init__(自身,初始):#初始
        """记下状态。"""
        自身.状态=dict(初始) if isinstance(初始,dict) else 初始#可变
        自身.订阅们=[]#监听

    def getSnapshot(自身):#读
        """浅拷贝 dict。"""
        if isinstance(自身.状态,dict):#映射
            return dict(自身.状态)#拷贝
        return 自身.状态#原样

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
        自身.状态=dict(下一) if isinstance(下一,dict) else 下一#替换
        for 听 in list(自身.订阅们):#广播
            听()#回调

class 触发控制器:#每会话触发控制器
    """全部变更留在内部；MenuView 从 menu 渲染，点选送回 pick。"""
    def __init__(自身,依赖):#注入依赖并预热名册
        """作用域诞生时预热：一次性预热名册。"""
        自身.依赖=依赖#依赖
        自身.menu=简易快照仓(dict(菜单关闭))#菜单快照
        自身.launcher=简易快照仓(None)#启动器当前源
        自身.lexicon=简易快照仓({})#按触发分组的热词表
        自身.命中=None#当前触发命中
        自身.拉取=None#在飞的候选拉取取消旗
        自身.已拆除=False#作用域已拆除
        自身.词表拆除们={}#词表订阅 disposer
        投影=自身._投影()#会话投影
        名册=依赖['roster']#源名册
        for 源 in 名册['all']():#诞生时名册里的每个源
            暖=源.get('warm') if isinstance(源,dict) else getattr(源,'warm',None)#可选预热
            if 暖 is not None:#有
                暖(投影)#预热
            自身._盯词表(源,投影)#接词表失效通道
        自身._刷新词表()#发布聚合词表

    def track(自身,草稿,光标,守卫,草稿修订):#跟踪草稿/光标
        """喂给触发检测并驱动菜单。"""
        if 自身.已拆除:#已拆除则忽略
            return#结束
        启动中=自身.launcher.getSnapshot() is not None#是否经启动器打开
        自身._清启动器()#键入跟踪清掉启动器态
        原始=检测触发(草稿,光标,守卫)#光标处检测触发
        if 原始 is None:#光标处无活触发
            自身.命中=None#清权威命中
            自身._停拉取()#中止在飞拉取
            自身._归约({'type':'close'})#关菜单
            return#本轮结束
        命中=dict(原始)#拷贝
        跨度=dict(命中['span'])#跨度拷贝
        跨度['draftRev']=草稿修订#打上当前草稿修订号
        命中['span']=跨度#写回
        前=自身.menu.getSnapshot()#变更前菜单快照
        同=not 启动中 and 前.get('open') and 前.get('hit') is not None#启动器未开且菜单已开且有命中
        if 同:#比触发与查询与跨度
            前命=前['hit']#前命中
            同=(前命.get('trigger')==命中['trigger'] and 前命.get('query')==命中['query']
                and 前命.get('span',{}).get('start')==命中['span']['start']
                and 前命.get('span',{}).get('end')==命中['span']['end'])#未变
        自身.命中=命中#写下权威命中
        if 同:#查询未变则不重拉
            return#结束
        名册=自身.依赖['roster']['sources'](命中['trigger'])#该触发下的源
        if not 名册:#该触发下没有源
            自身._停拉取()#中止在飞拉取
            自身._归约({'type':'close'})#关菜单
            return#无菜单可开
        if 启动中 or not 前.get('open') or 前.get('hit') is None or 前['hit'].get('trigger')!=命中['trigger']:#启动器/新开/换了触发
            自身.menu.set(铺分组(自身.menu.getSnapshot(),[s.get('name') if isinstance(s,dict) else getattr(s,'name',None) for s in 名册]))#按名册重铺
        自身._归约({'type':'hit','hit':命中})#写入命中
        自身._拉候选(命中,名册)#拉本世代候选

    def toggleSource(自身,源名,命中):#切换单源菜单
        """再点同一源则关掉。"""
        if 自身.已拆除:#已拆除则忽略
            return#结束
        if 自身.launcher.getSnapshot()==源名 and 自身.menu.getSnapshot().get('open'):#同一源已展开
            自身.dismiss()#再点则关掉
            return#已关闭
        匹配=next((s for s in 自身.依赖['roster']['sources'](命中.get('trigger')) if (s.get('name') if isinstance(s,dict) else getattr(s,'name',None))==源名),None)#按名找源
        if 匹配 is None:#名册里没有
            自身.dismiss()#关掉残留菜单
            return#无法打开
        自身._停拉取()#中止在飞拉取
        自身.命中=命中#记下合成命中
        自身.launcher.set(源名)#记下启动器源名
        自身.menu.set(铺分组(自身.menu.getSnapshot(),[源名]))#只铺这一组
        自身._归约({'type':'hit','hit':命中})#写入命中
        自身._拉候选(命中,[匹配])#只拉这一源

    def pick(自身,源名,下标):#指针点选候选
        """把点中的候选走 onPick，再经作用域输入事件执行。"""
        态=自身.menu.getSnapshot()#当前菜单
        命中=自身.命中#权威命中
        if 自身.已拆除 or not 态.get('open') or 命中 is None:#拆除/关菜单/无命中
            return#忽略
        组=next((g for g in 态.get('groups') or [] if g.get('source')==源名),None)#按源名找组
        候选=None#项
        if 组 is not None and 组.get('status')=='ready':#就绪
            项们=组.get('items') or []#列表
            if 0<=下标<len(项们):#下标合法
                候选=项们[下标]#该项
        if 候选 is None:#组未就绪或下标越界
            return#忽略
        源=next((s for s in 自身.依赖['roster']['sources'](命中['trigger']) if (s.get('name') if isinstance(s,dict) else getattr(s,'name',None))==源名),None)#按名找源
        if 源 is None:#名册里没有
            return#忽略
        点选=源.get('onPick') if isinstance(源,dict) else getattr(源,'onPick',None)#点选入口
        结果=点选({'candidate':候选,'session':自身._投影(),'position':命中['position'],'via':'menu','span':命中['span']}) if 点选 else None#点选
        自身._停拉取()#中止在飞拉取
        自身._归约({'type':'close'})#关菜单
        自身._执行(结果,命中['span'])#执行认领/插入

    def arbitrate(自身,键,合成中):#键盘仲裁
        """consumed / pick-highlighted / pass。"""
        if 合成中 or 自身.已拆除:#合成中或已拆除则放行
            return 'pass'#放行
        态=自身.menu.getSnapshot()#当前菜单
        if not 态.get('open'):#菜单未开则放行
            return 'pass'#放行
        if 键=='up':#上移高亮
            自身._归约({'type':'move','dir':-1})#高亮上移一项
            return 'consumed'#已消费
        if 键=='down':#下移高亮
            自身._归约({'type':'move','dir':1})#高亮下移一项
            return 'consumed'#已消费
        if 键=='escape':#关闭菜单
            自身._停拉取()#中止在飞拉取
            自身._归约({'type':'close'})#关菜单
            return 'consumed'#已消费
        if 键=='enter':#回车点选高亮项
            高亮=态.get('highlight')#高亮
            if 高亮 is None:#无高亮则放行
                return 'pass'#放行
            自身.pick(高亮['source'],高亮['index'])#走普通点选路径
            return 'pick-highlighted'#已点选高亮
        return 'pass'#未知键放行

    def onSpace(自身):#空格裁决
        """输入实际应用了认领/插入时为 True。"""
        命中=自身.命中#权威命中
        if 自身.已拆除 or 命中 is None or 命中.get('position')!='leading':#拆除/无命中/非前导
            return False#不裁
        令牌=命中['trigger']+命中['query']#触发字符加查询
        投影=自身._投影()#会话投影
        for 源 in 自身.依赖['roster']['sources'](命中['trigger']):#该触发下按登记顺序
            钩=源.get('matchSpace') if isinstance(源,dict) else getattr(源,'matchSpace',None)#空格钩子
            if 钩 is None:#无空格钩子
                continue#跳过
            结果=钩(投影,令牌)#同步问热状态
            if 结果 is None:#未认领
                continue#继续
            if 结果=='handled':#源内部处理完毕
                return True#已处理
            return 自身._执行(结果,命中['span'])#认领/插入/文本
        return False#无人认领

    def dismiss(自身):#外部关掉菜单
        """例如指针点在 composer 区域外。"""
        if 自身.已拆除:#已拆除则忽略
            return#结束
        自身._停拉取()#中止在飞拉取
        自身._归约({'type':'close'})#关菜单

    def dispose(自身):#随作用域拆除
        """关闭并中止。"""
        自身.已拆除=True#拒绝后续跟踪
        自身._停拉取()#中止在飞拉取
        自身._归约({'type':'close'})#关菜单
        自身.命中=None#清权威命中
        for 拆 in list(自身.词表拆除们.values()):#退订全部词表通道
            拆()#拆
        自身.词表拆除们.clear()#清空

    def sourceRemoved(自身,源):#源已从名册拆除
        """丢掉已拆除源的菜单组。"""
        态=自身.menu.getSnapshot()#当前菜单
        触发=源.get('trigger') if isinstance(源,dict) else getattr(源,'trigger',None)#触发
        名=源.get('name') if isinstance(源,dict) else getattr(源,'name',None)#名
        if 态.get('open') and 态.get('hit') is not None and 态['hit'].get('trigger')==触发:#菜单正开着该触发
            自身._归约({'type':'source-failed','generation':态.get('generation'),'source':名})#静默摘掉该组
        拆=自身.词表拆除们.pop(源,None)#退订词表通道
        if 拆 is not None:#有
            拆()#拆
        自身._刷新词表()#重聚合词表

    def sourceAdded(自身,源):#源在诞生后登记
        """预热它并把其卷折进活词表。"""
        投影=自身._投影()#会话投影
        暖=源.get('warm') if isinstance(源,dict) else getattr(源,'warm',None)#可选预热
        if 暖 is not None:#有
            暖(投影)#预热
        自身._盯词表(源,投影)#接词表失效通道
        自身._刷新词表()#重聚合词表

    def _投影(自身):#会话投影
        """仅稳定身份。"""
        return {'sessionId':自身.依赖['sessionId']}#投影

    def _执行(自身,结果,跨度):#执行点选结果
        """经作用域输入事件；True = 输入已应用。"""
        作用域=自身.依赖['actx']#派发主体
        if 结果 is None or 结果=='handled':#未应用
            return False#否
        if not hasattr(作用域,'bail'):#无 bail
            return False#否
        if isinstance(结果,dict) and 'claim' in 结果:#认领命令
            return 作用域.bail(作用域,'slash/input-begin-command',{'claim':结果['claim'],'span':跨度}) is True#开始命令
        if isinstance(结果,dict) and 'text' in 结果:#纯文本替换
            return 作用域.bail(作用域,'slash/input-insert-text',{'text':结果['text'],'span':跨度}) is True#插入文本
        if isinstance(结果,dict) and 'insert' in 结果:#引用插入
            return 作用域.bail(作用域,'slash/input-insert-reference',{'reference':结果['insert'],'span':跨度}) is True#插入引用
        return False#未知

    def _刷新词表(自身):#重聚合热词表
        """重新轮询每个带词表的源并发布聚合卷。"""
        投影=自身._投影()#会话投影
        卷={}#按触发累积名字
        for 源 in 自身.依赖['roster']['all']():#全部源按登记顺序
            词=源.get('lexicon') if isinstance(源,dict) else getattr(源,'lexicon',None)#词表钩子
            if 词 is None:#无词表钩子
                continue#跳过
            try:#问该源的热卷
                名们=词(投影)#同步拉取名字
            except Exception as 错误:#源实现抛错
                名=源.get('name') if isinstance(源,dict) else getattr(源,'name',None)#名
                print('[ui-input-trigger] source "'+str(名)+'" lexicon failed:',错误)#失败只记日志
                continue#跳过该源
            if 名们 is None:#卷尚未热
                continue#跳过
            触发=源.get('trigger') if isinstance(源,dict) else getattr(源,'trigger',None)#触发
            前=卷.get(触发)#同触发上已有的名字
            卷[触发]=list(名们) if 前 is None else list(前)+list(名们)#无则写入，有则拼接
        自身.lexicon.set(卷)#发布聚合词表

    def _盯词表(自身,源,投影):#订阅词表失效
        """无钩子或无卷的源从不通知。"""
        词=源.get('lexicon') if isinstance(源,dict) else getattr(源,'lexicon',None)#词表
        订=源.get('subscribeLexicon') if isinstance(源,dict) else getattr(源,'subscribeLexicon',None)#订阅
        if 词 is None or 订 is None:#无钩子则不订
            return#结束
        自身.词表拆除们[源]=订(投影,lambda:自身._刷新词表())#接到失效通道

    def _拉候选(自身,命中,名册):#拉本世代候选
        """为一世代命中启动候选拉取，取代上一轮。"""
        自身._停拉取()#取代上一轮
        取消={'aborted':False}#本轮取消源
        自身.拉取=取消#记下以便 supersede
        世代=自身.menu.getSnapshot().get('generation')#本命中世代
        投影=自身._投影()#会话投影
        for 源 in 名册:#逐源即发即弃
            名=源.get('name') if isinstance(源,dict) else getattr(源,'name',None)#源名
            候选=源.get('candidates') if isinstance(源,dict) else getattr(源,'candidates',None)#拉候选
            if 候选 is None:#无
                continue#跳过
            try:#不 await 语义：同步或可等待
                项们=候选(投影,{'query':命中['query'],'position':命中['position'],'signal':取消})#按查询拉候选
                if hasattr(项们,'等待'):#可等待
                    项们=项们.等待()#等待
                if 取消['aborted']:#已被新一轮取代
                    continue#丢
                自身._归约({'type':'source-settled','generation':世代,'source':名,'items':list(项们 or [])})#写入该组
            except Exception as 错误:#源失败
                if 取消['aborted']:#已被新一轮取代
                    continue#丢
                print('[ui-input-trigger] source "'+str(名)+'" candidates failed:',错误)#失败只记日志
                自身._归约({'type':'source-failed','generation':世代,'source':名})#静默摘掉该组

    def _停拉取(自身):#中止在飞拉取
        """有则 abort。"""
        if 自身.拉取 is not None:#有
            自身.拉取['aborted']=True#标中止
            自身.拉取=None#清掉句柄

    def _清启动器(自身):#清启动器
        """有启动器则清掉。"""
        if 自身.launcher.getSnapshot() is not None:#有
            自身.launcher.set(None)#清掉

    def _归约(自身,事件):#归约菜单
        """把菜单事件送进纯归约并写回仓库。"""
        现=自身.menu.getSnapshot()#当前菜单
        下一=菜单归约(现,事件)#纯归约
        if 下一 is not 现:#有变化才写回（引用或内容）
            自身.menu.set(下一)#写回
        if not 下一.get('open'):#关菜单时清启动器
            自身._清启动器()#清

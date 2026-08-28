"""拥有 Code Dispatch 配对，并把它的私有父下标投影进会话快照暴露的递归 Tool 调用约定。

对齐上游 `runtime/src/client/sessions/tool-call-tree.ts`。公开面仅中文名。
"""
import json#参数原文序列化

__all__=['工具调用树最大深度','工具调用树']#仅中文公开名

工具调用树最大深度=256#超过则拒绝这条边

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 同引用列表(左,右):#引用级比较两份只读列表
    """两份只读列表是否逐项引用相等。"""
    if len(左)!=len(右):#长度先相等
        return False#不等
    下标=0#逐项
    while 下标<len(左):#比较
        if 左[下标] is not 右[下标]:#引用不等
            return False#不等
        下标+=1#下一个
    return True#同一组引用

class 工具调用树:#工具调用树
    """拥有 Code Dispatch 配对与递归投影。"""

    def __init__(自身):#空树
        """清空全部由事件导出的子调用。"""
        自身._子按父={}#父 callId → 子调用
        自身._深度按调用={}#callId → 根起深度
        自身._投影按调用={}#callId → 投影缓存
        自身._修订=0#树修订
        自身._节点缓存=None#节点列表投影缓存
        自身._运行缓存=None#运行中根调用投影缓存

    def 重置(自身):#清空树
        """回放新窗口之前忘掉全部由事件导出的子调用。"""
        自身._子按父.clear()#丢掉父子边
        自身._深度按调用.clear()#丢掉深度
        自身._投影按调用.clear()#丢掉块缓存
        自身._修订+=1#抬修订

    def 应用(自身,事件):#折一条事件
        """属于 Code Dispatch 生命周期时折进一条事件。

        @param 事件 - 当前活窗口或历史窗口里的 Session 事件。
        @returns 该事件是否被当成子调用生命周期事件消费。
        """
        类型=取字段(事件,'type')#类型
        数据=取字段(事件,'data')#载荷
        if 类型=='tool/code-dispatch-start':#子调用开始
            运行中={#运行中子调用
                'callId':取字段(数据,'subCallId'),#子调用 id
                'name':取字段(数据,'name'),#工具名
                'argsRaw':json.dumps(取字段(数据,'arguments'),ensure_ascii=False),#参数原文
                'turn':0,#子调用不占回合
                'step':0,#子调用不占步骤
                'time':取字段(事件,'time'),#开始时间
                'callView':None,#尚无检视
                'subCalls':[],#投影时再挂孙调用
            }#结束
            父标识=取字段(数据,'parentCallId')#父 id
            兄弟=list(自身._子按父.get(父标识) or [])#已有兄弟
            if not 自身._接受边(父标识,取字段(数据,'subCallId')):#环或超深
                return True#消费但不挂边
            兄弟.append(运行中)#追加
            自身._子按父[父标识]=兄弟#写回
            自身._修订+=1#树变了
            return True#已消费
        if 类型!='tool/code-dispatch':#其它事件留给组装器
            return False#未消费
        父标识=取字段(数据,'parentCallId')#父 id
        子标识=取字段(数据,'subCallId')#子 id
        兄弟=list(自身._子按父.get(父标识) or [])#已有兄弟
        位置=-1#是否已有 start
        查=0#扫描
        while 查<len(兄弟):#找
            if 取字段(兄弟[查],'callId')==子标识:#命中
                位置=查#记下
                break#停
            查+=1#下一个
        if 位置==-1 and not 自身._接受边(父标识,子标识):#未见 start 且边不安全
            return True#消费但不挂
        已开始=None if 位置==-1 else 兄弟[位置]#对应的运行中行
        结算={#结算后的结果节点
            'kind':'tool-result',#结果
            'seq':取字段(事件,'seq'),#结算序号
            'time':取字段(事件,'time'),#结算时间
            'callId':子标识,#子调用 id
            'call':{'name':取字段(数据,'name'),'argsRaw':json.dumps(取字段(数据,'arguments'),ensure_ascii=False)},#调用面
            'callTime':取字段(已开始,'time') if 已开始 is not None else None,#开始时间
            'content':取字段(数据,'content'),#结果内容
            'isError':取字段(数据,'isError'),#是否错误
            'callView':None,#检视留给组装器
            'resultView':None,#结果检视
            'subCalls':[],#投影时再挂孙调用
        }#结束
        if 位置==-1:#未见 start
            兄弟.append(结算)#直接追加结算行
        else:#原地换成结算行
            兄弟[位置]=结算#替换
        自身._子按父[父标识]=兄弟#写回
        自身._修订+=1#树变了
        return True#已消费

    def 投影节点(自身,节点们):#投影节点列表
        """给节点列表里所有已结算根挂上递归投影后的子调用。"""
        缓存=自身._节点缓存#缓存
        if 缓存 is not None and 缓存['source'] is 节点们 and 缓存['revision']==自身._修订:#命中
            return 缓存['value']#复用
        投影=[]#新列表
        for 节点 in 节点们:#逐节点
            if 取字段(节点,'kind')!='tool-result':#非结果节点原样
                投影.append(节点)#原样
            else:#给结果根挂子树
                投影.append(自身._投影块(节点))#投影
        值=节点们 if 同引用列表(节点们,投影) else 投影#全未变则保留原列表引用
        自身._节点缓存={'source':节点们,'revision':自身._修订,'value':值}#记下
        return 值#投影结果

    def 投影运行中调用(自身,调用们):#投影运行中根
        """给所有运行中根调用挂上递归投影后的子调用。"""
        缓存=自身._运行缓存#缓存
        if 缓存 is not None and 缓存['source'] is 调用们 and 缓存['revision']==自身._修订:#命中
            return 缓存['value']#复用
        投影=[自身._投影块(调用) for 调用 in 调用们]#每个根挂子树
        值=调用们 if 同引用列表(调用们,投影) else 投影#全未变则保留
        自身._运行缓存={'source':调用们,'revision':自身._修订,'value':值}#记下
        return 值#投影结果

    def _投影块(自身,块):#投影一块
        """递归挂子调用。"""
        调用标识=取字段(块,'callId')#callId
        子们=自身._子按父.get(调用标识)#树里的子
        if 子们 is None:#否则用块自带
            子们=取字段(块,'subCalls') or []#自带
        投影子=[自身._投影块(子) for 子 in 子们]#递归投影子孙
        子值=子们 if 同引用列表(子们,投影子) else 投影子#子孙引用是否都没变
        缓存=自身._投影按调用.get(调用标识)#该块上次投影
        if 缓存 is not None and 缓存['source'] is 块 and 同引用列表(缓存['children'],子值):#命中
            return 缓存['value']#复用块
        if 取字段(块,'subCalls') is 子值:#子列表就是块自带的那份
            值=块#整块原样
        else:#只换 subCalls
            值=dict(块) if isinstance(块,dict) else dict(块.__dict__)#拷贝
            值['subCalls']=子值#换子
        自身._投影按调用[调用标识]={'source':块,'children':子值,'value':值}#刷新块缓存
        return 值#投影结果

    def _接受边(自身,父调用标识,子调用标识):#是否挂边
        """仅当每个递归消费方都能安全遍历时才接受这条边。"""
        if 自身._会成环(父调用标识,子调用标识):#成环则拒
            return False#拒
        待定=[{#待抬深度的节点
            'callId':子调用标识,#新子调用
            'depth':(自身._深度按调用.get(父调用标识) or 1)+1,#父深度再加一层
        }]#结束种子
        更新={}#本边要写入的新深度
        游标=0#广度
        while 游标<len(待定):#按广度走子树
            候选=待定[游标]#当前
            游标+=1#前进
            已知=更新.get(候选['callId'])#本轮已定深度
            if 已知 is None:#无
                已知=自身._深度按调用.get(候选['callId'])#或树上已有
            if 已知 is None:#未见过则当根深 1
                已知=1#根深
            if 候选['depth']<=已知:#这条路径没有更深
                continue#跳过
            if 候选['depth']>工具调用树最大深度:#超安全上限则整边拒
                return False#拒
            更新[候选['callId']]=候选['depth']#记下更深值
            for 孩子 in 自身._子按父.get(候选['callId']) or []:#已有孙调用也要抬
                待定.append({'callId':取字段(孩子,'callId'),'depth':候选['depth']+1})#入队
        for 调用标识,深度 in 更新.items():#提交新深度
            自身._深度按调用[调用标识]=深度#写入
        return True#边可挂

    def _会成环(自身,父调用标识,子调用标识):#挂上是否成环
        """若把子挂到父下会在已有子树里成环，则返回 True。"""
        if 父调用标识==子调用标识:#自环
            return True#环
        待定=[子调用标识]#从子调用向下走
        已访=set(待定)#已访问
        游标=0#广度
        while 游标<len(待定):#广度
            调用标识=待定[游标]#当前
            游标+=1#前进
            for 孩子 in 自身._子按父.get(调用标识) or []:#已有子孙
                子标识=取字段(孩子,'callId')#子 id
                if 子标识==父调用标识:#走回父则成环
                    return True#环
                if 子标识 in 已访:#已走过
                    continue#跳过
                已访.add(子标识)#标记
                待定.append(子标识)#继续向下
        return False#没有走到父

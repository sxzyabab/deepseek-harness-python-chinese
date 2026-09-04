"""Worker 拥有的源代数、观测分发与扩展传输。"""
#对齐上游 worker/bridge/hub.ts 段1

__all__=['检查器源注册表']#仅中文公开名

检查器协议版本=1#协议版本占位（共享层未迁时本地）

def _json字节长(值):#估计JSON字节
    """粗估帧字节。"""
    import json#JSON
    return len(json.dumps(值,ensure_ascii=False).encode('utf-8'))#字节

def _解析源帧(值,每帧上限):#解析源帧占位
    """委托共享解析；此处要求已是映射。"""
    if not isinstance(值,dict):#非对象
        raise ValueError('inspector protocol: invalid source frame')#抛错
    记录=值.get('records')#记录
    if isinstance(记录,list) and len(记录)>每帧上限:#超限
        raise ValueError('inspector protocol: too many records')#抛错
    return 值#返回

class 检查器源注册表:#源注册表
    """每个 Host 与 Client 源代数的串行 Worker 侧所有者。"""
    def __init__(自身,消费者们,最大帧字节,每帧记录上限):#构造
        """保存消费者与上限。"""
        自身._消费者们=消费者们#消费者
        自身._最大帧字节=最大帧字节#帧字节上限
        自身._每帧记录上限=每帧记录上限#每帧记录上限
        自身._源们={}#源状态表
        自身._状态监听=set()#状态监听
        自身._事件监听=set()#事件监听

    def 接收(自身,连接,值):#接收帧
        """解析并应用一帧；畸形输入仅关闭其源传输。"""
        try:#解析应用
            帧=_解析源帧(值,自身._每帧记录上限)#解析
            if _json字节长(帧)>自身._最大帧字节:#超字节
                raise ValueError(f'inspector protocol: source frame exceeds {自身._最大帧字节} bytes')#抛错
            自身._应用(连接,帧)#应用
        except Exception as 错误:#畸形
            信息=str(错误)#信息
            连接['send']({'v':检查器协议版本,'t':'source/rejected','code':'invalid-frame','message':信息})#拒绝
            连接['close'](1008,信息)#关闭

    def 断开(自身,连接,原因):#断开连接
        """移除已关闭连接承载的每一个代数。"""
        for 源id in list(自身._源们.keys()):#扫源
            状态=自身._源们[源id]#取状态
            if 状态['connection'] is not 连接:#非本连接
                continue#跳过
            del 自身._源们[源id]#删除
            for 消费者 in 自身._消费者们:#通知消费者
                消费者.关闭(状态['source'],原因)#关闭
            自身._发出({'type':'closed','source':状态['source'],'reason':原因})#发出关闭
        自身._通知状态()#刷新状态

    def 描述(自身):#描述源
        """读取诊断 CDP 域的当前源状态。"""
        结果=[]#视图
        for 状态 in 自身._源们.values():#映射视图
            结果.append({#视图行
                'sourceId':状态['source']['sourceId'],#源id
                'generation':状态['source']['generation'],#代数
                'kind':状态['source']['kind'],#种类
                'label':状态['source']['label'],#标签
                'capabilities':[能力['type'] for 能力 in 状态['source']['capabilities']],#能力类型
                'expectedSequence':状态['expectedSequence'],#期望序号
                'dropped':状态['dropped'],#丢弃
                'topics':dict(状态['topicCounts']),#主题
            })#append结束
        return 结果#返回

    def 订阅状态(自身,监听):#订阅状态
        """订阅源状态变更。"""
        自身._状态监听.add(监听)#加入
        return lambda:自身._状态监听.discard(监听)#释放

    def 订阅事件(自身,监听):#订阅事件
        """订阅源准入、移除与类型化扩展帧。"""
        自身._事件监听.add(监听)#加入
        return lambda:自身._事件监听.discard(监听)#释放

    def 发送(自身,源,帧):#发送控制帧
        """仅向仍活动的源代数发送类型化控制帧。"""
        状态=自身._源们.get(源['sourceId'])#取状态
        if 状态 is None or 状态['source']['generation']!=源['generation']:#代数不符
            return False#失败
        if _json字节长(帧)>自身._最大帧字节:#超字节
            raise ValueError(f'inspector protocol: Worker source frame exceeds {自身._最大帧字节} bytes')#抛错
        状态['connection']['send'](帧)#发送
        return True#成功

    def 关闭(自身):#关闭注册表
        """关闭每一个源并遗忘全部状态。"""
        for 状态 in list(自身._源们.values()):#扫源
            for 消费者 in 自身._消费者们:#通知
                消费者.关闭(状态['source'],'inspector worker stopped')#通知
            自身._发出({'type':'closed','source':状态['source'],'reason':'inspector worker stopped'})#发出
        自身._源们.clear()#清空
        自身._通知状态()#刷新

    def _应用(自身,连接,帧):#应用帧
        """按帧类型更新源状态。"""
        if 帧.get('t')=='source/open':#打开
            自身._打开(连接,帧['source'],帧['topics'])#打开源
            return#返回
        状态=自身._源们.get(帧.get('sourceId'))#取状态
        if 状态 is None or 状态['connection'] is not 连接 or 状态['source']['generation']!=帧.get('generation'):#归属不符
            raise ValueError('inspector protocol: frame does not belong to the active source generation')#抛错
        if 帧['t']=='source/close':#关闭
            del 自身._源们[帧['sourceId']]#删除
            for 消费者 in 自身._消费者们:#通知
                消费者.关闭(状态['source'],'source closed')#通知
            自身._发出({'type':'closed','source':状态['source'],'reason':'source closed'})#发出
            自身._通知状态()#刷新
            return#返回
        if 帧['t']=='client-runtime/response':#Runtime响应
            自身._断言能力(状态,'client','client-runtime','Client Runtime')#能力
            自身._发出({'type':'client-runtime-response','source':状态['source'],'frame':帧})#发出
            return#返回
        if 帧['t']=='client-console/event':#Console事件
            自身._断言能力(状态,'client','client-console','Client Console')#能力
            自身._发出({'type':'client-console-event','source':状态['source'],'frame':帧})#发出
            return#返回
        if 帧['t']=='client-sources/response':#源响应
            自身._断言能力(状态,'client','client-sources','Client Sources')#能力
            自身._发出({'type':'client-source-response','source':状态['source'],'frame':帧})#发出
            return#返回
        自身._断言主题(状态,帧.get('records',[]))#校验主题
        if 帧['t']=='source/replace':#替换
            自身._替换记录(状态,帧)#替换
            return#返回
        自身._追加记录(连接,状态,帧)#追加

    def _断言能力(自身,状态,种类,能力类型,标签):#断言能力
        """要求源种类与能力。"""
        if 状态['source']['kind']!=种类 or not any(c['type']==能力类型 for c in 状态['source']['capabilities']):#无能力
            raise ValueError(f'inspector protocol: source did not declare {标签}')#抛错

    def _替换记录(自身,状态,帧):#替换记录
        """应用 replace 帧。"""
        状态['expectedSequence']=帧['nextSequence']#更新期望
        记录们=[{**记录,'sequence':帧['nextSequence']+索引} for 索引,记录 in enumerate(帧['records'])]#带序号
        for 消费者 in 自身._消费者们:#替换
            消费者.替换(状态['source'],记录们)#替换记录
        自身._计数(状态,帧['records'])#计数
        自身._通知状态()#刷新

    def _追加记录(自身,连接,状态,帧):#追加记录
        """应用 append 帧或请求重快照。"""
        间隙=帧['firstSequence']-状态['expectedSequence']#序号间隙
        if 间隙<0 or 间隙!=帧['droppedBefore']:#间隙不符
            连接['send']({#请求重快照
                'v':检查器协议版本,'t':'source/resnapshot',#类型
                'sourceId':状态['source']['sourceId'],#源id
                'generation':状态['source']['generation'],#代数
                'expectedSequence':状态['expectedSequence'],#期望
                'reason':f"expected sequence {状态['expectedSequence']}, received {帧['firstSequence']}",#原因
            })#send结束
            return#返回
        状态['dropped']+=帧['droppedBefore']#累计丢弃
        记录们=[{**记录,'sequence':帧['firstSequence']+索引} for 索引,记录 in enumerate(帧['records'])]#带序号
        状态['expectedSequence']=帧['firstSequence']+len(帧['records'])#推进期望
        for 消费者 in 自身._消费者们:#追加
            消费者.追加(状态['source'],记录们)#追加
        自身._计数(状态,帧['records'])#计数
        连接['send']({#确认追加
            'v':检查器协议版本,'t':'source/append-acknowledged',#类型
            'sourceId':状态['source']['sourceId'],#源id
            'generation':状态['source']['generation'],#代数
            'nextSequence':状态['expectedSequence'],#下一序号
        })#确认结束
        自身._通知状态()#刷新

    def _打开(自身,连接,源,主题们):#打开源
        """登记新代数并接受。"""
        if 源['kind']!=连接['kind']:#种类不符
            raise ValueError('inspector protocol: source kind does not match its carrier')#抛错
        接受=set(主题们)#接受主题
        旧=自身._源们.get(源['sourceId'])#旧代数
        if 旧 is not None:#有旧
            for 消费者 in 自身._消费者们:#关闭旧
                消费者.关闭(旧['source'],'source generation replaced')#关闭旧
            自身._发出({'type':'closed','source':旧['source'],'reason':'source generation replaced'})#发出
        自身._源们[源['sourceId']]={#登记新
            'source':源,'topics':接受,'connection':连接,#连接
            'expectedSequence':1,'dropped':0,'topicCounts':{},#计数
        }#set结束
        连接['send']({'v':检查器协议版本,'t':'source/accepted','sourceId':源['sourceId'],'generation':源['generation']})#接受
        自身._发出({'type':'opened','source':源})#发出打开
        自身._通知状态()#刷新

    def _断言主题(自身,状态,记录们):#断言主题
        """记录主题须已声明。"""
        for 记录 in 记录们:#扫记录
            if '*' not in 状态['topics'] and 记录['topic'] not in 状态['topics']:#未声明
                raise ValueError(f"inspector protocol: source did not declare topic {记录['topic']!r}")#抛错

    def _计数(自身,状态,记录们):#计数主题
        """累加主题计数。"""
        for 记录 in 记录们:#扫记录
            主题=记录['topic']#主题
            状态['topicCounts'][主题]=状态['topicCounts'].get(主题,0)+1#累加

    def _通知状态(自身):#通知状态
        """隔离调用状态监听。"""
        for 监听 in list(自身._状态监听):#扫监听
            try:#隔离调用
                监听()#回调
            except Exception:#观察者故障
                pass#诊断观察者与源准入及后续观察者隔离

    def _发出(自身,事件):#发出事件
        """隔离调用事件监听。"""
        for 监听 in list(自身._事件监听):#扫监听
            try:#隔离调用
                监听(事件)#回调
            except Exception:#消费者故障
                pass#协议消费者与源准入及兄弟消费者隔离

from .轨迹节点 import 轨迹节点#包成轨迹视图节点
from .轨迹记录 import 轨迹错误#本包异常

__all__=['登记轨迹请求头定义']#仅中文公开名

def 轨迹系统消息定义(检视):#系统消息定义工厂
    """inspect 由 uiConversation.inspectSystemPrompt 提供。"""
    def 匹配(事件):#认领系统消息或非 append 表面
        """system/message 或位置替换。"""
        if 事件['type']=='system/message':#系统
            return {'id':str(事件['seq']),'role':'start'}#开
        if 'surfaceOp' in 事件 and 事件['surfaceOp']!='append':#非 append
            return {'id':str(事件['seq']),'role':'start'}#开
        return None#不匹配
    def 开始(_上下文,匹配项,读取器):#起始
        """解释并可选合成请求头。"""
        先前项=读取器.previous('trajectory-system-message')#先前
        先前=先前项['state'] if 先前项 is not None and 'state' in 先前项 else None#态
        态=检视(先前,匹配项['event'])#解释
        节点=态['effective'] if 'effective' in 态 else None#有效
        if 态.get('uncertain') is True:#不确定
            头项=读取器.previous('trajectory-request-header')#请求头
            头=头项['state'] if 头项 is not None and 'state' in 头项 else None#态
            if 头 is None:#无头
                return 态#原样
            提示=dict(头['prompt']) if 'prompt' in 头 and 头['prompt'] is not None else {}#提示
            提示['system']=''#清空系统
            事件=匹配项['event']#事件
            return {**态,'header':{'seq':事件['seq'],'time':事件['time'],'location':匹配项.get('location'),'prompt':提示}}#合成头
        先前有效=先前['effective'] if 先前 is not None and 'effective' in 先前 else None#先前有效
        引入=态['introduced'] if 'introduced' in 态 else None#引入
        if 节点 is None or (先前有效 is not None and 节点.get('text')==先前有效.get('text')) or (引入 is not None and 引入.get('update') is not True):#未改
            if 先前 is not None and 'header' in 先前 and 先前['header'] is not None:#保留旧头
                return {**态,'header':先前['header']}#带旧头
            return 态#原样
        头项=读取器.previous('trajectory-request-header')#请求头
        头=头项['state'] if 头项 is not None and 'state' in 头项 else None#态
        系统头=先前['header'] if 先前 is not None and 'header' in 先前 else None#系统合成头
        if 系统头 is not None and (头 is None or 系统头['seq']>头['seq']):#取较新
            先前头=系统头#系统头
        else:#否则
            先前头=头#请求头
        if 先前头 is None:#无先前
            return 态#原样
        提示=dict(先前头['prompt']) if 'prompt' in 先前头 and 先前头['prompt'] is not None else {}#提示
        提示['system']=节点['text'] if 'text' in 节点 else ''#覆盖系统
        return {#带合成头
            **态,#状态
            'header':{#合成头
                'seq':节点['seq'],'time':节点['time'],#坐标
                'prompt':提示,#提示
                'change':{'seq':节点['seq'],'time':节点['time'],'kind':'system','previous':先前头['prompt']},#变更
                'location':匹配项.get('location'),#位置
            },#头结束
        }#结束
    def 更新(上下文,_匹配项=None):#原样
        """状态不变。"""
        return 上下文['state'] if 'state' in 上下文 else None#态
    def 建视图(上下文):#构建视图
        """合成头或 append 引入渲卡。"""
        态=上下文['state'] if 'state' in 上下文 else None#态
        起始=上下文['start'] if 'start' in 上下文 else None#起始
        事件=起始['event'] if 起始 is not None and 'event' in 起始 else None#事件
        if 态 is not None and 'header' in 态 and 态['header'] is not None and 事件 is not None and 态['header'].get('seq')==事件.get('seq'):#本事件合成头
            return 轨迹节点(上下文,态['header']['seq'],{'kind':'request-header','header':态['header']})#请求头
        引入=态['introduced'] if 态 is not None and 'introduced' in 态 else None#引入
        if 引入 is not None and 引入.get('text','')!='' and 事件 is not None and 事件.get('type')=='system/message' and 事件.get('surfaceOp')=='append':#append 卡
            return 轨迹节点(上下文,引入['seq'],{'kind':'system-prompt','prompt':引入})#系统提示
        return None#无
    return {#定义
        'kind':'trajectory-system-message','target':'trajectory',#kind/目标
        'match':匹配,'start':开始,'update':更新,'buildViewNode':建视图,#生命周期
    }#结束

def 轨迹请求头定义(检视):#请求头定义工厂
    """inspect 由 uiConversation.inspectRequestPrompt 提供。"""
    def 匹配(事件):#只匹配请求头
        """用序号当节点 id。"""
        if 事件['type']=='request/header':#请求头
            return {'id':str(事件['seq']),'role':'start'}#起步
        return None#其余不匹配
    def 开始(_上下文,匹配项,读取器):#初始化
        """对照系统节点检视。"""
        事件=匹配项['event']#事件
        if 事件['type']!='request/header':#必须
            raise 轨迹错误('trajectory-request-header start requires request/header')#抬错
        头项=读取器.previous('trajectory-request-header')#上一条请求头
        头=头项['state'] if 头项 is not None and 'state' in 头项 else None#态
        系统项=读取器.previous('trajectory-system-message')#系统消息
        系统态=系统项['state'] if 系统项 is not None and 'state' in 系统项 else None#态
        系统头=系统态['header'] if 系统态 is not None and 'header' in 系统态 else None#合成头
        if 系统头 is not None and (头 is None or 系统头['seq']>头['seq']):#取较新
            先前=系统头['prompt'] if 'prompt' in 系统头 else None#提示
        else:#否则
            先前=头['prompt'] if 头 is not None and 'prompt' in 头 else None#提示
        系统=系统态['effective'] if 系统态 is not None and 'effective' in 系统态 else None#有效
        检视结果=检视(先前,事件,系统)#检视
        提示=检视结果['prompt'] if 'prompt' in 检视结果 else None#提示
        变更=检视结果['change'] if 'change' in 检视结果 else None#变更
        if 变更 is None and 系统头 is not None and (头 is None or 系统头['seq']>头['seq']):#继承系统变更
            变更=系统头['change'] if 'change' in 系统头 else None#变更
        事实={'seq':事件['seq'],'time':事件['time'],'prompt':提示,'location':匹配项.get('location')}#事实
        if 变更 is not None:#有变更
            事实['change']=变更#变更
        return 事实#请求头事实
    def 更新(上下文,_匹配项=None):#原样
        """状态不变。"""
        return 上下文['state'] if 'state' in 上下文 else None#态
    def 建视图(上下文):#构建视图
        """尚无状态则不贡献。"""
        状态=上下文['state'] if 'state' in 上下文 else None#事实
        if 状态 is None:#无
            return None#不贡献
        return 轨迹节点(上下文,状态.get('seq'),{'kind':'request-header','header':状态})#请求头贡献
    return {#定义
        'kind':'trajectory-request-header','target':'trajectory',#kind/目标
        'match':匹配,'start':开始,'update':更新,'buildViewNode':建视图,#生命周期
    }#结束

def 登记轨迹请求头定义(上下文):#向会话事件注册
    """注册轨迹系统提示节点与请求头事实。"""
    def 检视系统(先前,事件):#系统检视
        """委托服务。"""
        return 上下文.uiConversation.inspectSystemPrompt(先前,事件)#结果
    def 检视请求(先前,事件,系统):#请求检视
        """委托服务。"""
        return 上下文.uiConversation.inspectRequestPrompt(先前,事件,系统)#结果
    上下文.uiConversation.events.register(轨迹系统消息定义(检视系统))#系统
    上下文.uiConversation.events.register(轨迹请求头定义(检视请求))#请求头

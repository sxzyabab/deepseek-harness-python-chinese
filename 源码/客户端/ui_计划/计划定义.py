from .计划 import 已提交计划#解析已提交计划

__all__=['计划定义']#仅中文公开名

def 匹配(事件):
    """命中 exit_plan_mode 提交。"""
    计划=已提交计划(事件)#解析
    if 计划 is None:#无关
        return None#无
    角色='update' if 事件['type']=='tool/ptc-dispatch' else 'start'#角色
    return {'id':计划['callId'],'role':角色}#匹配

def 起始(_上下文,匹配项):
    """起始态。"""
    return 已提交计划(匹配项['event'])#计划

def 更新(上下文):
    """更新保留态。"""
    return 上下文['state']#态

def 构建视图节点(上下文):
    """构建隐藏视图节点。"""
    起始项=上下文['start'] if 'start' in 上下文 and 上下文['start'] is not None else None#起始
    if 起始项 is None and 'matches' in 上下文 and len(上下文['matches'])>0:#回退首匹配
        起始项=上下文['matches'][0]#首项
    数据=上下文['state'] if 'state' in 上下文 else None#态
    if 数据 is None and 起始项 is not None:#无态则从事件解
        数据=已提交计划(起始项['event'])#解
    if 数据 is None or 起始项 is None:#缺
        return None#无
    return {#视图节点
        'key':上下文['key'],'kind':'submitted-plan','id':上下文['id'],'target':'chat',#身份
        'anchorSeq':起始项['event']['seq'],'location':起始项['location'],#位置
        'visibility':'hidden','data':数据,#隐藏
    }#节点

计划定义={#对话节点定义
    'kind':'submitted-plan',#种
    'target':'chat',#目标
    'match':匹配,#匹配
    'start':起始,#起始
    'update':更新,#更新
    'buildViewNode':构建视图节点,#视图
}#定义结束

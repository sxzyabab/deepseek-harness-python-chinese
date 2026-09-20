"""启发式上下文构成投影的纯折叠。公开面仅中文名。"""
from ...内核.会话 import 归一请求头,是否表面事件#规范请求头与表面判定
from .类型 import 计量错误#计量异常
from .计价 import 计价工具令牌#工具计价
from .表面折叠 import 计划表面令牌,提交表面令牌#计划/提交

__all__=['分解投影定义']#仅中文公开名

class 分解视图模式:
    """上下文分解线路载荷模式。"""
    @staticmethod
    def parse(值):
        """校验三个非负整数。值必须是 dict。"""
        if not isinstance(值,dict):#必须是对象
            raise 计量错误('contextBreakdown view must be an object')#拒绝
        需要=('systemTokens','toolsTokens','messageTokens')#三个数字
        for 键 in 值:#自有键
            if 键 not in 需要:#未知键
                raise 计量错误('contextBreakdown view unknown key "'+键+'"')#严格
        结果={}#输出
        for 键 in 需要:#逐项
            if 键 not in 值:#缺键
                raise 计量错误('contextBreakdown view missing key "'+键+'"')#必填
            数字=值[键]#字段值
            if isinstance(数字,bool) or not isinstance(数字,(int,float)) or 数字!=int(数字) or 数字<0:#入口校验非负整数，先排除 bool
                raise 计量错误('contextBreakdown view '+键+' must be a nonnegative integer')#非负整数
            结果[键]=int(数字)#收成int
        return 结果#校验后的视图

def 分解初态():
    """初始空节点与零合计。"""
    return {'nodes':[],'breakdown':{'systemTokens':0,'toolsTokens':0,'messageTokens':0}}#初态

def 分解转移(状态,事件):
    """折一条分解事件。事件为 dict。"""
    if 事件['type']=='request/header':#新请求头
        工具=计价工具令牌(归一请求头(事件['data']['header']))#仅工具
        if 工具==状态['breakdown']['toolsTokens']:#未变
            return 状态#原样
        分解=dict(状态['breakdown'])#拷贝合计
        分解['toolsTokens']=工具#更新工具
        return {'nodes':状态['nodes'],'breakdown':分解}#新状态
    if not 是否表面事件(事件):#非表面
        return 状态#原样
    计划=计划表面令牌(状态['nodes'],事件)#只读计划
    节点列表=list(状态['nodes'])#可写副本
    提交表面令牌(节点列表,{
        'tokens':计划['tokens'],#本事件价格
        'deltaTokens':计划['deltaTokens'],#增量
        'node':{'seq':事件['seq'],'heuristicTokens':计划['tokens'],'system':事件['type']=='system/message'},#带系统分类
        'target':计划['target'],#提交目标
    })#提交
    系统=0#末个非空系统
    for 节点 in reversed(节点列表):#从末向前
        if 节点.get('system') and 节点['heuristicTokens']>0:#非空系统
            系统=节点['heuristicTokens']#记下
            break#找到即停
    合计=状态['breakdown']#旧合计
    消息=合计['systemTokens']+合计['messageTokens']+计划['deltaTokens']-系统#其余为消息
    if 系统==合计['systemTokens'] and 消息==合计['messageTokens']:#合计未变
        分解=合计#沿用
    else:#新合计
        分解={'systemTokens':系统,'toolsTokens':合计['toolsTokens'],'messageTokens':消息}#写回
    return {'nodes':节点列表,'breakdown':分解}#新状态

def 分解视图(状态):
    """只暴露分解合计。"""
    return dict(状态['breakdown'])#对外三数

分解投影定义={
    'key':'contextBreakdown',#投影键
    'schema':分解视图模式,#视图模式
    'init':分解初态,#初始空
    'apply':分解转移,#折一条事件
    'view':分解视图,#去掉内部节点
    'stateVersion':4,#状态版本
}#分解投影定义结束

"""测量服务的按位置表面折叠。公开面仅中文名。"""
from ...内核.会话 import 事件派生消息#从事件导出消息
from .类型 import 计量错误#计量异常
from .计价 import 计价消息,计价结构块#消息与结构计价

__all__=['计划表面令牌','提交表面令牌','折叠表面令牌']#仅中文公开名

def 收集投影附件(块列表,图片列表,文件列表):#收集投影附件
    """收集投影附件出现处及其结构价格。"""
    图片令牌=0#图片结构合计
    文件令牌=0#文件结构合计
    for 块 in 块列表:#逐块
        种类=块.get('type')#类型
        if 种类=='image':#图片
            图片列表.append(块)#记下整块，含 offloaded
            图片令牌+=计价结构块(块)#结构价格
        elif 种类=='file':#文件
            文件列表.append(块['attachment'])#记下引用
            文件令牌+=计价结构块(块)#结构价格
    return {'imageTokens':图片令牌,'fileTokens':文件令牌}#结构合计

def 分析节点(序号,消息):#分析节点
    """从表面事件派生消息构建一个已计价节点。"""
    if 消息 is None:#无消息
        return {#空节点
            'seq':序号,#序号
            'heuristicTokens':0,#零
            'tokens':0,#兼容旧字段
            'imageStructuralTokens':0,#零
            'fileStructuralTokens':0,#零
            'images':[],#无图
            'files':[],#无文件
        }#返回结束
    启发式=计价消息(消息)#启发式
    图片列表=[]#图片
    文件列表=[]#文件
    结构=收集投影附件(消息.get('content') or [],图片列表,文件列表)#结构
    return {#节点
        'seq':序号,#序号
        'heuristicTokens':启发式,#启发式
        'tokens':启发式,#兼容旧 tokens 字段
        'imageStructuralTokens':结构['imageTokens'],#图片结构
        'fileStructuralTokens':结构['fileTokens'],#文件结构
        'images':图片列表,#图片列表
        'files':文件列表,#文件列表
    }#返回结束

def 计划表面令牌(节点列表,事件):#校验并计价，不改表面
    """校验并计价一条表面事件，不变更表面。事件与节点均为 dict。"""
    节点=分析节点(事件['seq'],事件派生消息(事件))#分析节点
    令牌数=节点['heuristicTokens']#本事件价格
    操作=事件['surfaceOp']#表面操作
    if 操作=='append':#追加
        return {'tokens':令牌数,'deltaTokens':令牌数,'node':节点,'target':'append'}#追加计划
    起点下标=-1#范围起点
    终点下标=-1#范围终点
    下标=0#扫描下标
    起点序号=操作['startSeq']#声明起点
    终点序号=操作['endSeq']#声明终点
    for 项 in 节点列表:#逐个节点
        if 起点下标==-1 and 项['seq']==起点序号:#命中起点
            起点下标=下标#记下起点
        if 终点下标==-1 and 项['seq']==终点序号:#命中终点
            终点下标=下标#记下终点
        下标+=1#前进一步
    if 起点下标==-1 or 终点下标==-1 or 起点下标>终点下标:#范围对不上
        raise 计量错误('token surface: replace at seq '+str(事件['seq'])+' has invalid current range '+str(起点序号)+'-'+str(终点序号))#范围非法
    被遮蔽=0#被替换价格
    for 项 in 节点列表[起点下标:终点下标+1]:#含端切片
        被遮蔽+=项['heuristicTokens'] if 'heuristicTokens' in 项 else 项['tokens']#合计被遮蔽价格
    return {'tokens':令牌数,'deltaTokens':令牌数-被遮蔽,'node':节点,'target':{'startIdx':起点下标,'endIdx':终点下标}}#替换计划

def 提交表面令牌(节点列表,计划):#原地提交计划
    """把一条已校验计划原地应用到已计价表面。"""
    if 计划['target']=='append':#追加
        节点列表.append(计划['node'])#推入节点
        return
    目标=计划['target']#替换目标
    起点=目标['startIdx']#起点
    终点=目标['endIdx']#终点
    节点列表[起点:终点+1]=[计划['node']]#用本事件替换该范围

def 折叠表面令牌(节点列表,事件):#兼容旧一体折叠
    """把一条表面事件折到已计价表面上。事件与节点均为 dict。"""
    计划=计划表面令牌(节点列表,事件)#只读计划
    下一=list(节点列表)#拷贝
    提交表面令牌(下一,计划)#提交
    return {'tokens':计划['tokens'],'nodes':下一,'deltaTokens':计划['deltaTokens']}#价格减去被遮蔽

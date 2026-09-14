from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈

__all__=['检索块','默认检索最大行','复制文本','显示计数','摘要文案','展平行']#仅中文公开名

默认检索最大行=16#与终端同预算

def 复制文本(属性):
    """不受封顶/折叠影响。属性为 dict。"""
    if ('kind' in 属性) and 属性['kind']=='paths':#路径形
        路径=属性['paths'] if 'paths' in 属性 and 属性['paths'] is not None else []#路径
        return '\n'.join(路径)#路径
    块=[]#文件块
    文件列表=属性['files'] if 'files' in 属性 and 属性['files'] is not None else []#文件
    for 文件 in 文件列表:#逐文件
        行=[文件['path'] if 'path' in 文件 and 文件['path'] is not None else '']#路径头
        匹配列表=文件['matches'] if 'matches' in 文件 and 文件['matches'] is not None else []#匹配
        for 匹配 in 匹配列表:#匹配
            号=匹配['lineNumber'] if 'lineNumber' in 匹配 else None#号
            文=匹配['line'] if 'line' in 匹配 and 匹配['line'] is not None else ''#文
            行.append(str(号)+': '+str(文))#行
        块.append('\n'.join(行))#一块
    return '\n\n'.join(块)#拼

def 显示计数(属性):
    """matches=匹配行总和；paths=路径数。"""
    if ('kind' in 属性) and 属性['kind']=='paths':#路径
        路径=属性['paths'] if 'paths' in 属性 and 属性['paths'] is not None else []#路径
        return len(路径)#数
    总=0#累
    文件列表=属性['files'] if 'files' in 属性 and 属性['files'] is not None else []#文件
    for 文件 in 文件列表:#文件
        匹配列表=文件['matches'] if 'matches' in 文件 and 文件['matches'] is not None else []#匹配
        总+=len(匹配列表)#匹配
    return 总#数

def 摘要文案(属性,显示,截断,总计):
    """截断时 显示 X / 共 N。"""
    计数=('显示 '+str(显示)+' / 共 '+str(总计)) if 截断 is True else str(显示)#计数子句
    if ('kind' in 属性) and 属性['kind']=='paths':#路径
        return 计数+' 个路径'#路径单位
    文件列表=属性['files'] if 'files' in 属性 and 属性['files'] is not None else []#文件
    return 计数+' 处匹配 · '+str(len(文件列表))+' 个文件'#匹配单位

def 展平行(属性,已折叠):
    """折叠文件组丢掉其 match 行。"""
    if ('kind' in 属性) and 属性['kind']=='paths':#路径形
        路径=属性['paths'] if 'paths' in 属性 and 属性['paths'] is not None else []#路径
        出=[]#行
        for 径 in 路径:#路径
            出.append({'type':'path','path':径})#路径行
        return 出#路径行
    行列表=[]#累
    文件列表=属性['files'] if 'files' in 属性 and 属性['files'] is not None else []#文件
    for 索引,文件 in enumerate(文件列表):#分组
        折=索引 in 已折叠#折
        匹配列表=文件['matches'] if 'matches' in 文件 and 文件['matches'] is not None else []#匹配
        行列表.append({'type':'file','path':文件['path'] if 'path' in 文件 and 文件['path'] is not None else '','count':len(匹配列表),'index':索引,'collapsed':折})#头
        if 折 is True:#折起
            continue#跳匹配
        for 匹配 in 匹配列表:#匹配行
            行号=匹配['lineNumber'] if 'lineNumber' in 匹配 else None#号
            行列表.append({'type':'match','lineNumber':行号,'line':匹配['line'] if 'line' in 匹配 and 匹配['line'] is not None else '','key':str(索引)+':'+str(行号),'fileIndex':索引})#匹配
    return 行列表#扁

def 行键(行):
    """类型前缀防撞。"""
    种=行['type']#种
    if 种=='match':#匹配
        return 'match:'+行['key']#键
    if 种=='file':#文件
        return 'file:'+str(行['index'])#键
    return 'path:'+行['path']#路径

class 检索块:#检索卡
    """kind=matches|paths；本地展开与文件折叠集。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已展开=False#展开
        自身.已折叠=set()#折叠文件索引
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 切换展开(自身):
        """翻转。"""
        自身.已展开=not 自身.已展开#翻

    def 切换文件(自身,索引):
        """翻转一组。"""
        if 索引 in 自身.已折叠:#已折
            自身.已折叠.discard(索引)#开
        else:#未折
            自身.已折叠.add(索引)#折

    def 渲染(自身):
        """展平+封顶+摘要。"""
        属性=自身.属性#props
        截断=属性['truncated'] is True if 'truncated' in 属性 else False#截断
        总计=属性['total'] if 'total' in 属性 else 0#总计
        最大=属性['maxLines'] if 'maxLines' in 属性 else 默认检索最大行#封顶
        行列表=展平行(属性,自身.已折叠)#扁
        显示=显示计数(属性)#显示数
        空=len(行列表)==0#空；判 length
        自身.反馈.置文本(复制文本(属性))#可复制
        度量=头尾封顶(len(行列表),最大,自身.已展开)#度量
        头=行列表[:度量['headLines']] if 度量['capped'] is True else 行列表#头
        自然尾=行列表[len(行列表)-度量['tailLines']:] if 度量['capped'] is True else []#自然尾
        尾首=自然尾[0] if len(自然尾)>0 else None#尾首；判 length
        尾头=None#恢复的文件头
        if 尾首 is not None and ('type' in 尾首) and 尾首['type']=='match':#尾从匹配起
            文件索引=尾首['fileIndex']#属主
            头已带=False#头未带
            for 行 in 头:#扫头
                if ('type' in 行) and 行['type']=='file' and ('index' in 行) and 行['index']==文件索引:#头已带
                    头已带=True#记下
                    break#停
            if 头已带 is False:#头未带
                for 行 in 行列表:#找头
                    if ('type' in 行) and 行['type']=='file' and ('index' in 行) and 行['index']==文件索引:#命中
                        尾头=行#恢复
                        break#停
        尾=自然尾[1:] if 尾头 is not None else 自然尾#占尾槽
        return {#视图
            'type':'search-block',#类型
            'kind':属性['kind'] if 'kind' in 属性 else None,#形
            'summary':摘要文案(属性,显示,截断,总计),#摘要
            'empty':空,#空
            'head':头,#头
            'tail':尾,#尾
            'tailHeader':尾头,#尾文件头
            'hidden':度量['hidden'],#隐
            'capped':度量['capped'],#封
            'expanded':自身.已展开,#展
            'copied':自身.反馈.已复制,#反馈
            'onCopy':自身.反馈.复制,#复制
            'onToggle':自身.切换展开,#切换
            'onToggleFile':自身.切换文件,#文件折
            'rowKey':行键,#键函数
            'className':属性['className'] if 'className' in 属性 else None,#类
            'cssModule':'检索块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲

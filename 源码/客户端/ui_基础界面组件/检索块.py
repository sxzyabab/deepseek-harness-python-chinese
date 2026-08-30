"""检索结果面：grep 分组匹配或 glob 路径列表。

对齐上游 `ui-primitives/src/SearchBlock.tsx`。公开面仅中文名。
扁平行经头尾封顶；复制写完整结构化结果。
"""
from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈

__all__=['检索块','默认检索最大行','复制文本','显示计数','摘要文案','展平行']#仅中文公开名

默认检索最大行=16#与终端同预算

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 复制文本(属性):#剪贴板全文
    """不受封顶/折叠影响。"""
    if 取字段(属性,'kind')=='paths':#路径形
        return '\n'.join(取字段(属性,'paths') or [])#路径
    块=[]#文件块
    for 文件 in 取字段(属性,'files') or []:#逐文件
        行=[取字段(文件,'path') or '']#路径头
        for 匹配 in 取字段(文件,'matches') or []:#匹配
            行.append(str(取字段(匹配,'lineNumber'))+': '+str(取字段(匹配,'line') or ''))#行
        块.append('\n'.join(行))#一块
    return '\n\n'.join(块)#拼

def 显示计数(属性):#保留结果数
    """matches=匹配行总和；paths=路径数。"""
    if 取字段(属性,'kind')=='paths':#路径
        return len(取字段(属性,'paths') or [])#数
    总=0#累
    for 文件 in 取字段(属性,'files') or []:#文件
        总+=len(取字段(文件,'matches') or [])#匹配
    return 总#数

def 摘要文案(属性,显示,截断,总计):#横幅摘要
    """截断时 显示 X / 共 N。"""
    计数=('显示 '+str(显示)+' / 共 '+str(总计)) if 截断 else str(显示)#计数子句
    if 取字段(属性,'kind')=='paths':#路径
        return 计数+' 个路径'#路径单位
    文件数=len(取字段(属性,'files') or [])#文件数
    return 计数+' 处匹配 · '+str(文件数)+' 个文件'#匹配单位

def 展平行(属性,已折叠):#扁平行
    """折叠文件组丢掉其 match 行。"""
    if 取字段(属性,'kind')=='paths':#路径形
        return [{'type':'path','path':p} for p in (取字段(属性,'paths') or [])]#路径行
    行们=[]#累
    for 索引,文件 in enumerate(取字段(属性,'files') or []):#分组
        折=索引 in 已折叠#折
        匹配们=取字段(文件,'matches') or []#匹配
        行们.append({'type':'file','path':取字段(文件,'path') or '','count':len(匹配们),'index':索引,'collapsed':折})#头
        if 折:#折起
            continue#跳匹配
        for 匹配 in 匹配们:#匹配行
            行号=取字段(匹配,'lineNumber')#号
            行们.append({'type':'match','lineNumber':行号,'line':取字段(匹配,'line') or '','key':str(索引)+':'+str(行号),'fileIndex':索引})#匹配
    return 行们#扁

def 行键(行):#稳定键
    """类型前缀防撞。"""
    种=行['type']#种
    if 种=='match':#匹配
        return 'match:'+行['key']#键
    if 种=='file':#文件
        return 'file:'+str(行['index'])#键
    return 'path:'+行['path']#路径

class 检索块:#检索卡
    """kind=matches|paths；本地展开与文件折叠集。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已展开=False#展开
        自身.已折叠=set()#折叠文件索引
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 切换展开(自身):#封顶切换
        """翻转。"""
        自身.已展开=not 自身.已展开#翻

    def 切换文件(自身,索引):#文件组折叠
        """翻转一组。"""
        if 索引 in 自身.已折叠:#已折
            自身.已折叠.discard(索引)#开
        else:#未折
            自身.已折叠.add(索引)#折

    def 渲染(自身):#结构树
        """展平+封顶+摘要。"""
        属性=自身.属性#props
        截断=bool(取字段(属性,'truncated'))#截断
        总计=取字段(属性,'total',0)#总计
        最大=取字段(属性,'maxLines',默认检索最大行)#封顶
        行们=展平行(属性,自身.已折叠)#扁
        显示=显示计数(属性)#显示数
        空=len(行们)==0#空
        自身.反馈.置文本(复制文本(属性))#可复制
        度量=头尾封顶(len(行们),最大,自身.已展开)#度量
        头=行们[:度量['headLines']] if 度量['capped'] else 行们#头
        自然尾=行们[len(行们)-度量['tailLines']:] if 度量['capped'] else []#自然尾
        尾首=自然尾[0] if 自然尾 else None#尾首
        尾头=None#恢复的文件头
        if 尾首 is not None and 尾首.get('type')=='match':#尾从匹配起
            文件索引=尾首['fileIndex']#属主
            if not any(r.get('type')=='file' and r.get('index')==文件索引 for r in 头):#头未带
                for 行 in 行们:#找头
                    if 行.get('type')=='file' and 行.get('index')==文件索引:#命中
                        尾头=行#恢复
                        break#停
        尾=自然尾[1:] if 尾头 is not None else 自然尾#占尾槽
        return {#视图
            'type':'search-block',#类型
            'kind':取字段(属性,'kind'),#形
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
            'className':取字段(属性,'className'),#类
            'cssModule':'检索块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲

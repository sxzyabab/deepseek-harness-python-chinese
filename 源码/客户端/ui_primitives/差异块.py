"""文件变更内联差异面。

对齐上游 `ui-primitives/src/DiffBlock.tsx`。公开面仅中文名。
路径头+删/增块；头尾封顶；复制控件写可见 diff 文本。
"""
from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈

__all__=['差异块','默认差异最大行','内容行','建行','复制文本']#仅中文公开名

默认差异最大行=16#与终端块同预算

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 内容行(文本):#一侧文本切行
    """空=零行；尾换行是终止符不是空行。"""
    if 文本=='':#空
        return []#零
    体=文本[:-1] if 文本.endswith('\n') else 文本#剥终止符
    return 体.split('\n')#切

def 建行(差异们):#展平 hunk → 行+计数
    """路径头开新文件；同文件第二 hunk 用 ⋯ 缝。"""
    行们=[]#扁平行
    路径集=set()#去重路径
    增=0#加行
    删=0#删行
    前路径=None#上一路径
    for 项 in 差异们:#逐 hunk
        路径=取字段(项,'path') or ''#路径
        路径集.add(路径)#记
        if 路径!=前路径:#新文件
            行们.append({'kind':'path','text':路径})#路径头
        else:#同文件缝
            行们.append({'kind':'gap','text':'⋯'})#缝
        前路径=路径#更新
        旧=取字段(项,'oldText')#旧侧
        if 旧 is not None:#有删侧
            for 线 in 内容行(旧):#逐行
                行们.append({'kind':'del','text':线})#删
                删+=1#计
        新=取字段(项,'newText') or ''#新侧
        for 线 in 内容行(新):#逐行
            行们.append({'kind':'add','text':线})#增
            增+=1#计
    return {'rows':行们,'added':增,'removed':删,'files':len(路径集)}#结果

def 复制文本(行们):#剪贴板文本
    """带 -/+ /路径/缝 前缀。"""
    出=[]#行
    for 行 in 行们:#逐行
        种=行['kind']#种
        if 种=='del':#删
            出.append('- '+行['text'])#前缀
        elif 种=='add':#增
            出.append('+ '+行['text'])#前缀
        else:#路径或缝
            出.append(行['text'])#原文
    return '\n'.join(出)#拼接

class 差异块:#内联 diff 面
    """空 diffs 返回 None；展开态本地持有。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已展开=False#展开
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 切换展开(自身):#翻转
        """头尾封顶切换。"""
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):#结构树
        """建行+封顶切片。"""
        属性=自身.属性#props
        差异们=取字段(属性,'diffs') or []#hunks
        建成=建行(差异们)#扁
        行们=建成['rows']#行
        if len(行们)==0:#空
            return None#不画
        最大=取字段(属性,'maxLines',默认差异最大行)#封顶
        度量=头尾封顶(len(行们),最大,自身.已展开)#度量
        头=行们[:度量['headLines']] if 度量['capped'] else 行们#头
        尾=行们[len(行们)-度量['tailLines']:] if 度量['capped'] else []#尾
        自身.反馈.置文本(复制文本(行们))#整卡可复制
        return {#视图
            'type':'diff-block',#类型
            'rows':行们,#全行
            'head':头,#头片
            'tail':尾,#尾片
            'added':建成['added'],#+
            'removed':建成['removed'],#-
            'files':建成['files'],#文件数
            'hidden':度量['hidden'],#隐
            'capped':度量['capped'],#封
            'expanded':自身.已展开,#展
            'copied':自身.反馈.已复制,#反馈
            'onCopy':自身.反馈.复制,#复制
            'onToggle':自身.切换展开,#切换
            'className':取字段(属性,'className'),#类
            'footer':'└ +'+str(建成['added'])+' -'+str(建成['removed'])+' · '+str(建成['files'])+' file'+('' if 建成['files']==1 else 's'),#脚
            'cssModule':'差异块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲

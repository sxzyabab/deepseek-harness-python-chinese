from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈

__all__=['读块','默认读最大行']#仅中文公开名

默认读最大行=16#与终端同预算

class 读块:#读卡
    """banner+行号 gutter；复制写窗口原文。"""
    def __init__(自身,属性=None,**关键字参数):
        """合并 props。"""
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已展开=False#展开
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 切换展开(自身):
        """封顶切换。"""
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):
        """配对行号+文本并封顶。"""
        属性=自身.属性#props
        行列=属性['lines'] if 'lines' in 属性 else None#窗口行
        行列表=list(行列) if 行列 is not None else []#空则空表
        总行=属性['totalLines'] if 'totalLines' in 属性 else 0#文件总行
        最大=属性['maxLines'] if 'maxLines' in 属性 else 默认读最大行#封顶
        语言=属性['lang'] if 'lang' in 属性 else None#语法提示
        原文行=[]#原文
        规范=[]#规范行
        for 行 in 行列表:#逐行
            文=行['text'] if 'text' in 行 and 行['text'] is not None else ''#文
            原文行.append(文)#原文
            规范.append({'number':行['number'] if 'number' in 行 else None,'text':文})#规范行
        原文='\n'.join(原文行)#原文
        自身.反馈.置文本(原文)#可复制
        度量=头尾封顶(len(规范),最大,自身.已展开)#度量
        头=规范[:度量['headLines']] if 度量['capped'] is True else 规范#头
        尾=规范[len(规范)-度量['tailLines']:] if 度量['capped'] is True else []#尾
        窗口化=len(规范)<总行#窗口读；判 length
        return {#视图
            'type':'read-block',#类型
            'label':属性['label'] if 'label' in 属性 else None,#标签
            'lang':语言,#语言
            'lines':规范,#全行
            'head':头,#头
            'tail':尾,#尾
            'totalLines':总行,#总
            'windowed':窗口化,#窗口
            'countNote':('显示 '+str(len(规范))+' / '+str(总行)+' 行') if 窗口化 is True else None,#计数注
            'hidden':度量['hidden'],#隐
            'capped':度量['capped'],#封
            'expanded':自身.已展开,#展
            'copied':自身.反馈.已复制,#反馈
            'onCopy':自身.反馈.复制 if len(规范)>0 else None,#空窗不复制；判 length
            'onToggle':自身.切换展开,#切换
            'className':属性['className'] if 'className' in 属性 else None,#类
            'cssModule':'读块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲

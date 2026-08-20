"""终端命令+输出面。

对齐上游 `ui-primitives/src/TerminalBlock.tsx`。公开面仅中文名。
提示行（态点+cwd+命令）、ANSI 输出、退出/信号胶囊、复制控件。
"""
from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈
from .ansi import 解析ansi行#ANSI 行

__all__=['终端块','默认终端最大行','默认标签','提示标签','状态文案','运行态']#仅中文公开名

默认终端最大行=16#输出预算

默认标签={#内置文案
    'signal':lambda 信号:'信号 '+str(信号),
    'exitCode':lambda 码:'退出码 '+str(码),
    'running':'运行中','failed':'失败','done':'已完成',
    'copy':'复制','copied':'复制成功','noOutput':'无输出',
    'collapseAria':'收起输出','collapse':'收起',
    'expandAria':lambda 隐:'展开其余 '+str(隐)+' 行输出',
    'expand':lambda 隐:'… 其余 '+str(隐)+' 行',
}#标签结束

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 提示标签(工作目录,家目录):#cwd 提示
    """家目录坍成 ~；否则末段。"""
    修=re_sub尾分隔(工作目录)#修
    if 家目录 is not None and 修==re_sub尾分隔(家目录):#家
        return '~'#波浪
    段=re_切段(修)#末段
    return 工作目录 if 段=='' else 段#回退整路径

def re_sub尾分隔(路径):#剥尾分隔
    """/\\ 尾。"""
    if not isinstance(路径,str):#非串
        return ''#空
    return 路径.rstrip('/\\')#剥

def re_切段(路径):#末段
    """两分隔都认。"""
    片=路径.replace('\\','/').split('/')#统一
    return 片[-1] if 片 else ''#末

def 状态文案(退出码,信号,标签):#胶囊文案
    """干净退出 None。"""
    if 信号 is not None:#信号优先
        return 标签['signal'](信号) if callable(标签['signal']) else str(信号)#信号
    if 退出码 is not None and 退出码!=0:#非零
        return 标签['exitCode'](退出码) if callable(标签['exitCode']) else str(退出码)#码
    return None#干净

def 运行态(运行中,退出码,信号,标签):#点态+文案
    """ongoing/error/done。"""
    if 运行中:#跑
        return {'state':'ongoing','label':标签['running']}#跑
    if 状态文案(退出码,信号,标签) is not None:#失败
        return {'state':'error','label':标签['failed']}#败
    return {'state':'done','label':标签['done']}#成

class 终端块:#终端卡
    """本地展开；复制写原始 output。"""

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
        """封顶。"""
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):#结构树
        """解析 ANSI 并封顶。"""
        属性=自身.属性#props
        标签=dict(默认标签)#默认
        覆=取字段(属性,'labels') or {}#覆盖
        if isinstance(覆,dict):#字典
            标签.update(覆)#叠
        输出=取字段(属性,'output') or ''#原文
        行们=解析ansi行(输出)#解析
        if len(行们)>1:#可能终止空行
            末=行们[-1]#末行
            if 末 and all((s.get('text') or '')=='' for s in 末):#全空 span
                行们=行们[:-1]#剥终止符行
        elif len(行们)==1 and 行们[0]==[]:#空输出保一行空
            pass#留
        运行中=bool(取字段(属性,'running'))#跑
        退出码=取字段(属性,'exitCode')#码
        信号=取字段(属性,'signal')#信号
        最大=取字段(属性,'maxLines',默认终端最大行)#封顶
        命令=取字段(属性,'command') or ''#命令
        令体=命令[:-1] if 命令.endswith('\n') else 命令#剥尾换行
        命令行=令体.split('\n')#多行命令
        空=all(all((s.get('text') or '').strip()=='' for s in 线) for 线 in 行们)#可见空
        度量=头尾封顶(len(行们),最大 if 最大!=float('inf') else len(行们)+1,自身.已展开)#度量
        头=行们[:度量['headLines']] if 度量['capped'] else 行们#头
        尾=行们[len(行们)-度量['tailLines']:] if 度量['capped'] else []#尾
        自身.反馈.置文本(输出)#原始可复制
        工作目录=取字段(属性,'cwd')#cwd
        家=取字段(属性,'home')#home
        态=运行态(运行中,退出码,信号,标签)#运行态
        状=状态文案(退出码,信号,标签)#胶囊
        return {#视图
            'type':'terminal-block',#类型
            'running':运行中,#跑
            'runState':态,#态
            'status':状,#胶囊
            'commandLines':命令行,#命令行
            'cwdLabel':None if 工作目录 is None else 提示标签(工作目录,家),#cwd 标签
            'lines':行们,#全
            'head':头,#头
            'tail':尾,#尾
            'empty':空,#空
            'hidden':度量['hidden'],#隐
            'capped':度量['capped'],#封
            'expanded':自身.已展开,#展
            'copied':自身.反馈.已复制,#反馈
            'labels':标签,#文案
            'onCopy':自身.反馈.复制 if (not 运行中 and not 空) else None,#复制
            'onToggle':自身.切换展开,#切换
            'className':取字段(属性,'className'),#类
            'cssModule':'终端块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲

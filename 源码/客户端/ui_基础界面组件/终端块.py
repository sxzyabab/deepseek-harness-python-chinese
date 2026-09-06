"""终端命令+输出面。

对齐上游 `ui-primitives/src/TerminalBlock.tsx`。公开面仅中文名。
提示行（态点+cwd+命令）、ANSI 输出、退出/信号胶囊、复制控件。属性与 span 为 dict。
"""
from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈
from .ansi import 解析ansi行#ANSI 行

__all__=['终端块','默认终端最大行','默认标签','提示标签','状态文案','运行态']#仅中文公开名

默认终端最大行=16#输出预算

def 信号文案(信号):
    """信号胶囊。"""
    return '信号 '+str(信号)#文

def 退出码文案(码):
    """退出码胶囊。"""
    return '退出码 '+str(码)#文

def 展开其余无障碍(隐):
    """展开其余 N 行 aria。"""
    return '展开其余 '+str(隐)+' 行输出'#文

def 展开其余标(隐):
    """展开其余 N 行。"""
    return '… 其余 '+str(隐)+' 行'#文

默认标签={#内置文案
    'signal':信号文案,#信号
    'exitCode':退出码文案,#退出码
    'running':'运行中','failed':'失败','done':'已完成',
    'copy':'复制','copied':'复制成功','noOutput':'无输出',
    'collapseAria':'收起输出','collapse':'收起',
    'expandAria':展开其余无障碍,#展开 aria
    'expand':展开其余标,#展开
}#标签结束

def 剥尾分隔(路径):
    """/\\ 尾。"""
    if isinstance(路径,str) is False:#非串
        return ''#空
    return 路径.rstrip('/\\')#剥

def 切末段(路径):
    """两分隔都认。"""
    片=路径.replace('\\','/').split('/')#统一
    return 片[-1] if len(片)>0 else ''#末；判 length

def 提示标签(工作目录,家目录):
    """家目录坍成 ~；否则末段。"""
    修=剥尾分隔(工作目录)#修
    if 家目录 is not None and 修==剥尾分隔(家目录):#家
        return '~'#波浪
    段=切末段(修)#末段
    return 工作目录 if 段=='' else 段#回退整路径

def 状态文案(退出码,信号,标签):
    """干净退出 None。标签.signal/exitCode 为函数。"""
    if 信号 is not None:#信号优先
        return 标签['signal'](信号)#信号
    if 退出码 is not None and 退出码!=0:#非零
        return 标签['exitCode'](退出码)#码
    return None#干净

def 运行态(运行中,退出码,信号,标签):
    """ongoing/error/done。"""
    if 运行中 is True:#跑
        return {'state':'ongoing','label':标签['running']}#跑
    if 状态文案(退出码,信号,标签) is not None:#失败
        return {'state':'error','label':标签['failed']}#败
    return {'state':'done','label':标签['done']}#成

def 段文(段):
    """span.text，缺则空串。段为 dict。"""
    return 段['text'] if 'text' in 段 and 段['text'] is not None else ''#文

class 终端块:#终端卡
    """本地展开；复制写原始 output。"""
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
        """封顶。"""
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):
        """解析 ANSI 并封顶。"""
        属性=自身.属性#props
        标签=dict(默认标签)#默认
        覆=属性['labels'] if 'labels' in 属性 else None#覆盖
        if 覆 is not None:#有覆盖
            标签.update(覆)#叠
        输出=属性['output'] if 'output' in 属性 and 属性['output'] is not None else ''#原文
        行列表=解析ansi行(输出)#解析
        if len(行列表)>1:#可能终止空行；判 length
            末=行列表[-1]#末行
            全空=True#空 span 行（空数组在 JS 为真且 all 空）
            for 段 in 末:#扫
                if 段文(段)!='':#有字
                    全空=False#否
                    break#停
            if 全空 is True:#全空 span
                行列表=行列表[:-1]#剥终止符行
        运行中=属性['running'] is True if 'running' in 属性 else False#跑
        退出码=属性['exitCode'] if 'exitCode' in 属性 else None#码
        信号=属性['signal'] if 'signal' in 属性 else None#信号
        最大=属性['maxLines'] if 'maxLines' in 属性 else 默认终端最大行#封顶
        命令=属性['command'] if 'command' in 属性 and 属性['command'] is not None else ''#命令
        令体=命令[:-1] if 命令.endswith('\n') else 命令#剥尾换行
        命令行=令体.split('\n')#多行命令
        空=True#可见空
        for 线 in 行列表:#扫行
            for 段 in 线:#扫段
                if 段文(段).strip()!='':#有可见
                    空=False#否
                    break#停
            if 空 is False:#已有
                break#停
        度量=头尾封顶(len(行列表),最大,自身.已展开)#度量；maxLines 为 int
        头=行列表[:度量['headLines']] if 度量['capped'] is True else 行列表#头
        尾=行列表[len(行列表)-度量['tailLines']:] if 度量['capped'] is True else []#尾
        自身.反馈.置文本(输出)#原始可复制
        工作目录=属性['cwd'] if 'cwd' in 属性 else None#cwd
        家=属性['home'] if 'home' in 属性 else None#home
        态=运行态(运行中,退出码,信号,标签)#运行态
        状=状态文案(退出码,信号,标签)#胶囊
        return {#视图
            'type':'terminal-block',#类型
            'running':运行中,#跑
            'runState':态,#态
            'status':状,#胶囊
            'commandLines':命令行,#命令行
            'cwdLabel':None if 工作目录 is None else 提示标签(工作目录,家),#cwd 标签
            'lines':行列表,#全
            'head':头,#头
            'tail':尾,#尾
            'empty':空,#空
            'hidden':度量['hidden'],#隐
            'capped':度量['capped'],#封
            'expanded':自身.已展开,#展
            'copied':自身.反馈.已复制,#反馈
            'labels':标签,#文案
            'onCopy':自身.反馈.复制 if (运行中 is False and 空 is False) else None,#复制
            'onToggle':自身.切换展开,#切换
            'className':属性['className'] if 'className' in 属性 else None,#类
            'cssModule':'终端块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):
        """对齐 React。"""
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲

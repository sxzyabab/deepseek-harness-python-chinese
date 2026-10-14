from nicegui import ui as 界面
from ...基础设施.通用工具 import 路径转正斜杠
from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈
from .ansi import 解析ansi行#ANSI 行

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css('''
.终端块{position:relative;margin:16px 0;padding-left:30px;color:var(--dsw-alias-label-primary);background:var(--dsw-alias-markdown-code-block);border-radius:var(--dsw-radius-lg);overflow:hidden;font:var(--dsw-font-markdown-code-block);line-height:22px}
.终端块 .命令{margin:0}
.终端块 pre{margin:0 !important;padding:9px 14px 9px 30px;background:transparent;white-space:pre-wrap}
''')
    样式已登记=True

__all__=['终端块','默认终端最大行','默认标签','提示标签','状态文案','运行态']#仅中文公开名

默认终端最大行=16#输出预算

def 信号文案(信号):
    '信号胶囊'
    return '信号 '+str(信号)#文

def 退出码文案(码):
    '退出码胶囊'
    return '退出码 '+str(码)#文

def 展开其余无障碍(隐):
    '展开其余 N 行 aria'
    return '展开其余 '+str(隐)+' 行输出'#文

def 展开其余标(隐):
    '展开其余 N 行'
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
    '/\\ 尾'
    if isinstance(路径,str) is False:#非串
        return ''#空
    return 路径.rstrip('/\\')#剥

def 切末段(路径):
    '两分隔都认'
    片=路径转正斜杠(路径).split('/')#统一
    return 片[-1] if len(片)>0 else ''#末；判 length

def 提示标签(工作目录,家目录):
    '家目录坍成 ~；否则末段'
    修=剥尾分隔(工作目录)#修
    if 家目录 is not None and 修==剥尾分隔(家目录):#家
        return '~'#波浪
    段=切末段(修)#末段
    return 工作目录 if 段=='' else 段#回退整路径

def 状态文案(退出码,信号,标签):
    '干净退出 None。标签.signal/exitCode 为函数'
    if 信号 is not None:#信号优先
        return 标签['signal'](信号)#信号
    if 退出码 is not None and 退出码!=0:#非零
        return 标签['exitCode'](退出码)#码
    return None#干净

def 运行态(运行中,退出码,信号,标签):
    'ongoing/error/done'
    if 运行中 is True:#跑
        return {'state':'ongoing','label':标签['running']}#跑
    if 状态文案(退出码,信号,标签) is not None:#失败
        return {'state':'error','label':标签['failed']}#败
    return {'state':'done','label':标签['done']}#成

def 段文(段):
    'span.text，缺则空串。段为 dict'
    return 段['text'] if 'text' in 段 and 段['text'] is not None else ''#文

class 终端块:#终端卡
    '本地展开；复制写原始 output'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已展开=False#展开
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 切换展开(自身):
        '封顶'
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):
        '解析 ANSI 并画出命令、输出和复制'
        登记样式()
        属性=自身.属性#props
        标签=dict(默认标签)#默认
        覆=属性['labels'] if 'labels' in 属性 else None#覆盖
        if 覆 is not None:
            标签.update(覆)#叠
        输出=属性['output'] if 'output' in 属性 and 属性['output'] is not None else ''#原文
        行列表=解析ansi行(输出)#解析
        if len(行列表)>1:#可能终止空行；判 length
            末=行列表[-1]#末行
            全空=True#空 span 行（空数组在 JS 为真且 all 空）
            for 段 in 末:#扫
                if 段文(段)!='':
                    全空=False#否
                    break
            if 全空 is True:#全空 span
                行列表=行列表[:-1]#剥终止符行
        运行中=属性['running'] is True if 'running' in 属性 else False#跑
        退出码=属性['exitCode'] if 'exitCode' in 属性 else None#码
        信号=属性['signal'] if 'signal' in 属性 else None#信号
        最大=属性['maxLines'] if 'maxLines' in 属性 else 默认终端最大行#封顶
        命令=属性['command'] if 'command' in 属性 and 属性['command'] is not None else ''#命令
        令体=命令[:-1] if 命令.endswith('\n') else 命令#剥尾换行
        空=True#可见空
        for 线 in 行列表:#扫行
            for 段 in 线:#扫段
                if 段文(段).strip()!='':
                    空=False#否
                    break
            if 空 is False:#已有
                break
        自身.反馈.置文本(输出)#原始可复制
        工作目录=属性['cwd'] if 'cwd' in 属性 else None#cwd
        家=属性['home'] if 'home' in 属性 else None#home
        态=运行态(运行中,退出码,信号,标签)#运行态
        状=状态文案(退出码,信号,标签)#胶囊
        根=界面.column().classes('终端块')#卡
        类名=属性['className'] if 'className' in 属性 else None#类
        if isinstance(类名,str) and 类名!='':
            根.classes(类名)#附
        def 样式串(样式):
            'ANSI 样式写成行内样式'
            if 样式 is None:#无
                return ''#空
            名={'backgroundColor':'background-color','fontWeight':'font-weight','fontStyle':'font-style','textDecoration':'text-decoration','visibility':'visibility','opacity':'opacity','color':'color'}#映射
            段=[]#段
            for 键,值 in 样式.items():#逐项
                css=名[键] if 键 in 名 else 键#名
                段.append(str(css)+':'+str(值))#写
            return ';'.join(段)#拼
        def 画输出(行组):
            '一行一段'
            for 线 in 行组:#逐行
                with 界面.row().style('flex-wrap:nowrap;gap:0'):#行
                    if len(线)==0:#空行
                        界面.label(' ')#占位
                        continue#下
                    for 段 in 线:#逐段
                        文=段文(段)#文
                        标=界面.label(文 if 文!='' else ' ')#段
                        串=样式串(段['style'] if 'style' in 段 else None)#样式
                        if 串!='':
                            标.style(串)#附
        def 重画():
            '按当前展开态重画输出'
            度量=头尾封顶(len(行列表),最大,自身.已展开)#度量
            头=行列表[:度量['headLines']] if 度量['capped'] is True else 行列表#头
            尾=行列表[len(行列表)-度量['tailLines']:] if 度量['capped'] is True else []#尾
            根.clear()
            with 根:#内容
                界面.label(态['label']).classes(态['state'])#运行态
                if 状 is not None:#胶囊
                    界面.label(状)#状态
                if 工作目录 is not None:#目录
                    界面.label(提示标签(工作目录,家))#标签
                if 令体!='':
                    界面.code(令体).classes('命令')#命令
                if 空 is True:#无可见输出
                    界面.label(标签['noOutput'])#空
                else:
                    画输出(头)#头
                    if 度量['capped'] is True:#封顶
                        展=标签['expand']#展开文案
                        展文=展(度量['hidden']) if callable(展) else 展#文案
                        def 点展开():
                            '展开其余行'
                            自身.切换展开()#翻
                            重画()#重画
                        界面.button(展文,on_click=点展开)#展开
                        画输出(尾)#尾
                    elif 度量['hidden']>0 and 自身.已展开 is True:#已展开
                        def 点收起():
                            '收起输出'
                            自身.切换展开()#翻
                            重画()#重画
                        界面.button(标签['collapse'],on_click=点收起)#收起
                if 运行中 is False and 空 is False:#可复制
                    复制文=标签['copied'] if 自身.反馈.已复制 else 标签['copy']#文案
                    def 点复制():
                        '写入剪贴板并刷新文案'
                        自身.反馈.复制()#复制
                        重画()#重画
                    界面.button(复制文,on_click=点复制)#复制
        重画()#首画

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
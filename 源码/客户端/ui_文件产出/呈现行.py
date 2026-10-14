import json#解析参数
from nicegui import ui as 界面
from .异常 import 页面失败文案

def 腾出根(自身):
    '清空仍挂着的根。父级已拆掉时丢掉根，并返回要显示的失败句。'
    旧=getattr(自身,'根',None)
    if 旧 is None:
        return None
    try:
        旧.clear()
    except Exception as 错误:
        自身.根=None
        return 页面失败文案(错误)
    return None

def 标出失败(文案):
    '失败句非空时写在当前页面上'
    if isinstance(文案,str) and 文案!='':
        界面.label(文案)

__all__=['呈现行','文件名摘要']#仅中文公开名

def 文件名摘要(原文):#从参数 JSON 抽路径摘要
    '对齐 fileNames：解析失败则原样返回'
    try:#尝试解析
        参数=json.loads(原文)#解析
    except (json.JSONDecodeError,TypeError):
        return 原文#原样
    if not isinstance(参数,dict) or 'files' not in 参数 or not isinstance(参数['files'],list):#须有 files
        return 原文#原样
    路径=[]#路径表
    for 项 in 参数['files']:#每项
        if isinstance(项,dict) and 'path' in 项 and isinstance(项['path'],str):
            路径.append(项['path'])
    return ', '.join(路径)#逗号连接

def 恒等翻译(键,参数=None):#无文案表
    '返回键本身'
    return 键#键即文案

def 呈现键齐(属性):
    '有阶段或工具块才画。空槽不另写一句'
    if not isinstance(属性,dict):#不是合成 props
        return False#不齐
    if 'phase' in 属性 or 'block' in 属性:#工具视图份额
        return True#齐
    return False#不齐

class 呈现行:#present 工具视图行
    '状态点 + 披露行；展开体为定稿输出。不进输入栏'
    def __init__(自身,属性=None):#构造
        '记下 props 与展开'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.展开=False#展开
        自身.存活=True#存活
        if 呈现键齐(自身.属性):#键齐
            自身.渲染()#构造末尾才画

    def 更新(自身,属性):#刷新
        '记下最新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 卸载(自身):#卸载
        '标死'
        自身.存活=False#死

    def 切换(自身):#翻转展开
        '切换'
        自身.展开=not 自身.展开#翻

    def 视图(自身):#读视图模型
        '投影披露行'
        属性=自身.属性#props
        块=属性['block'] if 'block' in 属性 else {}#工具块
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        检视=属性['inspect'] if 'inspect' in 属性 else None#检视
        阶段=属性['phase'] if 'phase' in 属性 else None#工具阶段
        if 阶段=='preparing':#参数还没到
            return {#准备行
                'type':'present-row',#类型
                'data-tool':'present',#工具
                'data-state':'preparing',#态
                'title':翻译('row.title'),#标题
                'dot':'ongoing',#状态点
                'open':False,#不开
                'expandable':False,#不可展
                'summary':翻译('row.preparing'),#准备
                'paths':'',#尚无路径
                'body':'',#无正文
                'inspectLabel':None,#不检视
                'onInspect':None,#无
                'onToggle':自身.切换,#切换
                'cssModule':'PresentRow.module.css',#样式
            }#准备结束
        已结='kind' in 块#已结算
        if not 已结:#运行中
            状态='running'#跑
        elif 'error' in 块 and 块['error'] is not None and ('code' in 块['error'] and 块['error']['code']=='interrupted'):#中断
            状态='stopped'
        elif 'isError' in 块 and 块['isError'] is True:#失败
            状态='error'#错
        else:#成功
            状态='ok'#好
        if 已结:#已结
            调用=块['call'] if 'call' in 块 and 块['call'] is not None else {}#调用
            参数原文=调用['argsRaw'] if 'argsRaw' in 调用 else ''#参数
        else:#流式
            参数原文=块['argsRaw'] if 'argsRaw' in 块 else ''#参数
        输出=''#输出
        if 已结 and 'content' in 块 and isinstance(块['content'],list):
            段=[]#段
            for 项 in 块['content']:#每块
                if isinstance(项,dict) and 'type' in 项 and 项['type']=='text' and 'text' in 项:#文本
                    段.append(项['text'])#文本
                else:#其它
                    段.append(json.dumps(项,ensure_ascii=False))#JSON
            输出='\n'.join(段)#拼接
        细节=输出#默认输出
        if 细节=='' and 已结 and 'error' in 块 and 块['error'] is not None:#无输出有错
            错误体=块['error']#错误体
            名=错误体['name'] if 'name' in 错误体 else ''#名
            码=错误体['code'] if 'code' in 错误体 else ''#码
            细节=f"{名}: {码}"#细节
        点态='ongoing' if 状态=='running' else ('done' if 状态=='ok' else ('warning' if 状态=='stopped' else 'error'))#状态点
        return {#视图
            'type':'present-row',#类型
            'data-tool':'present',#工具
            'data-state':状态,#态
            'title':翻译('row.title'),#标题
            'dot':点态,#状态点
            'open':自身.展开 and 细节!='',#开
            'expandable':细节!='',#可展
            'summary':翻译(f"row.{状态}"),#摘要态
            'paths':文件名摘要(参数原文),#路径
            'body':细节,#体
            'inspectLabel':翻译('row.inspect') if 检视 is not None else None,#检视文案
            'onInspect':检视,#检视
            'onToggle':自身.切换,#切换
            'cssModule':'PresentRow.module.css',#样式
        }#视图结束

    def 渲染(自身):
        '状态、路径摘要；可展开时给出正文与检视'
        视=自身.视图()
        清除失败=腾出根(自身)
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('present-row')
        with 自身.根:
            标出失败(清除失败)
            with 界面.row():
                界面.label(视['title'])
                界面.label(视['summary'])
                if isinstance(视['paths'],str) and 视['paths']!='':
                    界面.label(视['paths'])
                if 视['expandable'] is True:
                    def 点展开():
                        '展开或收起输出'
                        自身.切换()
                        自身.渲染()
                    界面.button(on_click=点展开).props('icon=expand_more flat round')
            if 视['open'] is True and isinstance(视['body'],str) and 视['body']!='':
                界面.label(视['body']).style('white-space:pre-wrap')
            if isinstance(视['inspectLabel'],str) and 视['inspectLabel']!='' and 视['onInspect'] is not None:
                def 点检视():
                    '打开检视'
                    视['onInspect']()
                界面.button(视['inspectLabel'],on_click=点检视).props('flat no-caps')

    def __call__(自身,属性=None):#组件调用形
        '对齐 React'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()

import json#解析参数

__all__=['呈现行','文件名摘要']#仅中文公开名

def 文件名摘要(原文):#从参数 JSON 抽路径摘要
    """对齐 fileNames：解析失败则原样返回。"""
    try:#尝试解析
        参数=json.loads(原文)#解析
    except Exception:#截断 JSON
        return 原文#原样
    if not isinstance(参数,dict) or 'files' not in 参数 or not isinstance(参数['files'],list):#须有 files
        return 原文#原样
    路径=[]#路径表
    for 项 in 参数['files']:#每项
        if isinstance(项,dict) and 'path' in 项 and isinstance(项['path'],str):#有 path
            路径.append(项['path'])#记下
    return ', '.join(路径)#逗号连接

def 恒等翻译(键,参数=None):#无文案表
    """返回键本身。"""
    return 键#键即文案

class 呈现行:#present 工具视图行
    """状态点 + 披露行；展开体为定稿输出。"""
    def __init__(自身,属性=None):#构造
        """记下 props 与展开。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.展开=False#展开
        自身.存活=True#存活

    def 更新(自身,属性):#刷新
        """记下最新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 卸载(自身):#卸载
        """标死。"""
        自身.存活=False#死

    def 切换(自身):#翻转展开
        """切换。"""
        自身.展开=not 自身.展开#翻

    def 视图(自身):#读视图模型
        """投影披露行。"""
        属性=自身.属性#props
        块=属性['block'] if 'block' in 属性 else {}#工具块
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        检视=属性['inspect'] if 'inspect' in 属性 else None#检视
        已结='kind' in 块#已结算
        if not 已结:#运行中
            状态='running'#跑
        elif 'error' in 块 and 块['error'] is not None and ('code' in 块['error'] and 块['error']['code']=='interrupted'):#中断
            状态='stopped'#停
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
        if 已结 and 'content' in 块 and isinstance(块['content'],list):#有内容
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

    def __call__(自身,属性=None):#组件调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.视图()#渲

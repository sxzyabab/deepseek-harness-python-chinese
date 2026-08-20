"""Bash 工具行样例：keyed toolview 洞上的第三方姿态登记。

对齐上游 `ui-tool/src/client/tool/toolviews/bash-sample.tsx`。公开面仅中文名。
本地复制 ToolRow 整行展开交互；终端卡优先，无终端的执行失败走 IN/OUT 回退。
"""
from .调用模型 import 派生工具行#行模型
from .终端卡模型 import 终端卡模型,终端已失败,终端块文案#终端卡
from .文案 import 会话命名空间#词典席

__all__=['bash行','bash工具视图样例','前导态','状态文案']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 前导态(状态):#前导槽
    """错误/中止换状态点；其余保留 api 图标。"""
    if 状态=='error':#失败
        return 'error'#红点
    if 状态=='stopped':#中止
        return 'warning'#琥珀
    return 'api'#工具图标

def 状态文案(状态,翻译):#无障碍文案
    """ok 为 None。"""
    if 状态=='running':#运行
        return 翻译('bash.running') if callable(翻译) else 'bash.running'#运行
    if 状态=='error':#失败
        return 翻译('bash.failed') if callable(翻译) else 'bash.failed'#失败
    if 状态=='stopped':#中止
        return 翻译('bash.stopped') if callable(翻译) else 'bash.stopped'#中止
    return None#ok

class bash行:#bash 工具行
    """图标+Bash·描述；整行切换终端或通用错误卡。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与本地展开。"""
        自身.属性=属性 or {}#合成
        自身.已展开=False#本地展开

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 切换展开(自身):#整行切换
        """可展开才翻转。"""
        if not 自身.可展开():#不可
            return#不动
        自身.已展开=not 自身.已展开#翻转

    def 会话工作目录(自身):#从会话表取 cwd
        """useSessions 选 byId[sessionId].cwd。"""
        属性=自身.属性#props
        会话标识=取字段(属性,'sessionId')#会话
        用会话=取字段(属性,'useSessions')#钩
        if not callable(用会话) or 会话标识 is None:#无
            return None#缺
        return 用会话(lambda 表:取字段(取字段(取字段(表,'byId'),会话标识),'cwd'))#cwd

    def 可展开(自身):#是否可展开
        """有终端卡或通用错误体。"""
        属性=自身.属性#props
        工具名=取字段(属性,'toolName')#名
        块=取字段(属性,'block')#块
        模型=派生工具行(工具名,块)#行
        终端=终端卡模型(块,自身.会话工作目录())#终端
        态=取字段(模型,'state')#态
        通用错=(终端 is None and 态=='error'
                and (取字段(模型,'body') is not None or 取字段(模型,'output') is not None))#通用错
        return 终端 is not None or 通用错#可

    def 渲染(自身):#结构树
        """与上游 JSX 同构。"""
        属性=自身.属性#props
        工具名=取字段(属性,'toolName')#名
        块=取字段(属性,'block')#块
        翻译=取字段(属性,'t')#文案
        检查=取字段(属性,'inspect')#检查
        模型=派生工具行(工具名,块)#行
        工作目录=自身.会话工作目录()#cwd
        终端=终端卡模型(块,工作目录)#终端
        态=取字段(模型,'state')#态
        if 态=='ok' and 终端 is not None and 终端已失败(终端):#终端失败抬红
            态='error'#红
        通用错=(终端 is None and 取字段(模型,'state')=='error'
                and (取字段(模型,'body') is not None or 取字段(模型,'output') is not None))#通用错
        可展=终端 is not None or 通用错#可展
        打开=自身.已展开 and 可展#实际打开
        失败行=取字段(模型,'errorSummary') if 取字段(模型,'state')=='error' else None#失败首行
        终端描述=取字段(终端,'description') if 终端 is not None else None#描述
        摘要=失败行 if 失败行 is not None else (终端描述 if 终端描述 is not None else 取字段(模型,'summary'))#摘要
        前导='chevron' if 打开 else ('icon-chevron-hover' if 可展 else 前导态(态))#前导
        展开体=None#展开
        if 打开:#打开
            if 终端 is not None:#终端卡
                卡=取字段(终端,'card') or {}#卡
                展开体={#终端体
                    'kind':'terminal',#种
                    'card':卡,#卡
                    'maxLines':None,#Infinity
                    'labels':终端块文案(翻译) if callable(翻译) else None,#文案
                }#结束
            else:#IN/OUT
                展开体={#通用错体
                    'kind':'io',#种
                    'body':取字段(模型,'body'),#入
                    'output':取字段(模型,'output'),#出
                }#结束
        return {#结构树
            'type':'bash-sample-row',#类型
            'variant':'bash',#变体
            'toolName':工具名,#名
            'title':取字段(模型,'title'),#标题
            'summary':摘要,#摘要
            'state':态,#态
            'status':状态文案(态,翻译),#无障碍
            'leading':前导,#前导
            'expandable':可展,#可否
            'open':打开,#打开
            'failureLine':失败行,#失败行
            'body':展开体,#展开体
            'inspect':检查 if 打开 else None,#检查
            'toggle':自身.切换展开,#切换
            'cssModule':'bash样例.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

bash工具视图样例={#登记插件
    'name':'bash-toolview-sample',#名
    'inject':['slots'],#依赖
    'key':'bash',#键
    'locale':会话命名空间,#词典
    'component':bash行,#组件
}#视图结束

"""工具摘要行：单行工具摘要与展开体。

对齐上游 `ui-tool/src/client/tool/components/ToolRow.tsx`。公开面仅中文名。
展开态本地；整行作为展开开关；错误行折叠摘要为失败首行。
卡材料互斥；展开体优先卡再 IN/OUT；code 变体程序走代码块。
"""
from .差异卡模型 import 聊天差异最大行数#diff 封顶
from .读卡模型 import 聊天读最大行数#读封顶
from .检索卡模型 import 聊天检索最大行数#检索封顶
from .终端卡模型 import 终端块文案#终端文案

__all__=['工具行','前导态','状态文案','取字段']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 前导态(状态,图标):#前导槽状态替换
    """错误/中止换状态点；其余保留工具图标（名或节点）。"""
    if 状态=='error':#失败
        return {'type':'state-dot','state':'error'}#红点
    if 状态=='stopped':#中止
        return {'type':'state-dot','state':'warning'}#琥珀
    return 图标#工具图标

def 状态文案(状态,翻译):#无障碍运行态文案
    """ok 态为 None；其余给辅助技术。"""
    if 状态=='running':#运行中
        return 翻译('row.running') if callable(翻译) else 'row.running'#运行
    if 状态=='error':#失败
        return 翻译('row.failed') if callable(翻译) else 'row.failed'#失败
    if 状态=='stopped':#中止
        return 翻译('row.stopped') if callable(翻译) else 'row.stopped'#中止
    return None#ok

class 工具行:#单行工具摘要
    """渲染一行工具调用摘要与可选展开体。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props 与本地展开。"""
        自身.属性=属性 or {}#合成
        自身.已展开=False#本地展开

    def 更新(自身,属性):#刷新 props
        """刷新合成 props。"""
        自身.属性=属性#新

    def 切换展开(自身):#整行切换
        """有体/出/卡才可展开。"""
        if not 自身.可展开():#不可
            return#不动
        自身.已展开=not 自身.已展开#翻转

    def 可展开(自身):#是否可展开
        """有 body/output/卡材料则可。"""
        属性=自身.属性#props
        卡=(
            取字段(属性,'terminal') is not None
            or 取字段(属性,'diff') is not None
            or 取字段(属性,'read') is not None
            or 取字段(属性,'search') is not None
            or 取字段(属性,'web') is not None
        )#任一卡
        return 取字段(属性,'body') is not None or 取字段(属性,'output') is not None or 卡#可展

    def 建展开体(自身):#展开体结构树
        """卡优先；否则 code+IN/OUT。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t')#文案
        变体=取字段(属性,'variant')#变体
        状态=取字段(属性,'state') or 'ok'#态
        体=取字段(属性,'body')#输入
        出=取字段(属性,'output')#输出
        终端=取字段(属性,'terminal')#终端卡
        差异=取字段(属性,'diff')#diff 卡
        读=取字段(属性,'read')#读卡
        检索=取字段(属性,'search')#检索卡
        网页=取字段(属性,'web')#网页卡
        if 终端 is not None:#终端
            return {#终端体
                'kind':'terminal',#种
                'card':取字段(终端,'card'),#卡
                'maxLines':None,#Infinity
                'labels':终端块文案(翻译) if callable(翻译) else None,#文案
                'className':'terminalBody',#类
            }#结束
        if 差异 is not None:#diff
            return {#diff 体
                'kind':'diff',#种
                'card':取字段(差异,'card'),#卡
                'maxLines':聊天差异最大行数,#封顶
                'className':'diffBody',#类
            }#结束
        if 读 is not None:#读
            return {#读体
                'kind':'read',#种
                'card':读,#卡道具
                'maxLines':聊天读最大行数,#封顶
                'className':'readBody',#类
            }#结束
        if 检索 is not None:#检索
            return {#检索体
                'kind':'search',#种
                'card':取字段(检索,'card'),#卡
                'recovery':取字段(检索,'recovery'),#恢复定位
                'maxLines':聊天检索最大行数,#封顶
                'className':'searchBody',#类
            }#结束
        if 网页 is not None:#网页
            return {'kind':'web','card':网页,'className':'webBody'}#网页体
        片=[]#IO 片
        if 变体=='code' and 体 is not None:#代码程序
            片.append({#代码块
                'kind':'code',#种
                'code':体,#程序
                'lang':'typescript',#语法
                'copyLabel':翻译('copy') if callable(翻译) else 'copy',#复制
                'copiedLabel':翻译('copied') if callable(翻译) else 'copied',#已复制
                'className':'codeBody',#类
            })#结束
        卡体=None if 变体=='code' else 体#code 变体不进 IN
        if 卡体 is not None or 出 is not None:#IN/OUT 卡
            段=[]#段
            if 卡体 is not None:#IN
                段.append({'label':'IN','text':卡体,'error':False})#入
            if 卡体 is not None and 出 is not None:#分隔
                段.append({'divider':True})#分隔
            if 出 is not None:#OUT
                段.append({'label':'OUT','text':出,'error':状态=='error'})#出
            片.append({'kind':'io','sections':段})#IO 卡
        return {'kind':'composite','parts':片} if 片 else None#复合或空

    def 渲染(自身):#结构树
        """与上游 JSX 同构。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t')#文案
        状态=取字段(属性,'state') or 'ok'#行态
        失败行=取字段(属性,'errorSummary') if 状态=='error' else None#失败首行
        摘要=失败行 if 失败行 is not None else 取字段(属性,'summary')#摘要
        后缀=None if 失败行 is not None else 取字段(属性,'summarySuffix')#后缀
        路径=取字段(属性,'filePath')#路径
        开文件=取字段(属性,'onOpenFile')#开文件
        文件链=路径 is not None and callable(开文件) and 失败行 is None#路径链
        打开=自身.已展开 and 自身.可展开()#实际打开
        检查=取字段(属性,'inspect')#检查
        return {#结构树
            'type':'tool-row',#类型
            'variant':取字段(属性,'variant'),#变体
            'toolName':取字段(属性,'toolName'),#工具名
            'icon':取字段(属性,'icon'),#图标名/节点（宿主解析）
            'title':取字段(属性,'title'),#标题
            'summary':摘要,#摘要
            'summarySuffix':后缀,#后缀
            'state':状态,#态
            'leading':前导态(状态,取字段(属性,'icon')),#前导
            'status':状态文案(状态,翻译),#无障碍
            'expandable':自身.可展开(),#可否展开
            'open':打开,#打开
            'filePath':路径 if 文件链 else None,#路径链
            'onOpenFile':开文件 if 文件链 else None,#打开文件
            'body':自身.建展开体() if 打开 else None,#展开体
            'inspect':检查 if 打开 else None,#检查回调；字形由宿主挂 inspect-12
            'toggle':自身.切换展开,#切换
            'cssModule':'工具行.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

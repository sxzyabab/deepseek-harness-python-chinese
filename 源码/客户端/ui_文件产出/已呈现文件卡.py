"""已呈现文件卡：身份与默认应用/文件管理器动作。

对齐上游 `ui-deliverables/src/client/PresentedFileCard.tsx`。公开面仅中文名。
props 为槽位合成 dict。
"""
import re#剥尾注

__all__=['已呈现文件卡','卡描述','文件扩展名']#仅中文公开名

_尾注=re.compile(r'\s*(?:\([^()]*\)|（[^（）]*）)\s*$',re.UNICODE)#尾部括号注

def 文件扩展名(路径):#取末段后缀
    """对齐 fileExtension：末段最后一点之后；无或尾点则空。"""
    斜=路径.rfind('/')#正斜
    反=路径.rfind('\\')#反斜
    位=斜 if 斜>反 else 反#末分隔
    名=路径 if 位==-1 else 路径[位+1:]#末段
    点=名.rfind('.')#末点
    return '' if 点<0 else 名[点+1:]#后缀

def 路径末段(路径):#取末段
    """正斜杠或反斜杠分隔的末段。"""
    斜=路径.rfind('/')#正斜
    反=路径.rfind('\\')#反斜
    位=斜 if 斜>反 else 反#末分隔
    return 路径 if 位==-1 else 路径[位+1:]#末段

def 卡描述(描述,回退):#卡副文案
    """剥尾注后空则用回退。"""
    if 描述 is None:#无
        return 回退#回退
    修剪=_尾注.sub('',描述).strip()#剥注
    return 回退 if 修剪=='' else 修剪#空则回退

def 恒等翻译(键,参数=None):#无文案
    """返回键。"""
    return 键#键

class 已呈现文件卡:#单文件交付卡
    """预览钮与打开/揭示菜单；不嵌套按钮。"""
    def __init__(自身,属性=None):#构造
        """记下 props 与菜单开。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.菜单开=False#菜单
        自身.存活=True#存活

    def 更新(自身,属性):#刷新
        """记下最新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 卸载(自身):#卸载
        """标死。"""
        自身.存活=False#死

    def 设菜单(自身,开):#菜单
        """写入开闭。"""
        自身.菜单开=开#记

    def 切换菜单(自身):#翻转菜单
        """翻转。"""
        自身.菜单开=not 自身.菜单开#翻

    def 视图(自身):#读视图模型
        """投影文件卡。"""
        属性=自身.属性#props
        文件=属性['file'] if 'file' in 属性 else {}#文件
        阶段=属性['phase'] if 'phase' in 属性 else None#阶段
        宿主=属性['host'] if 'host' in 属性 else None#宿主
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        预览=属性['onPreview'] if 'onPreview' in 属性 else None#预览
        动作=属性['onAction'] if 'onAction' in 属性 else None#动作
        待定=阶段=='opening' or 阶段=='revealing'#待定
        菜单禁用=待定 or 宿主 is None or ('available' not in 宿主 or 宿主['available'] is not True)#禁用
        if 菜单禁用 and 自身.菜单开:#禁用时关
            自身.菜单开=False#关
        揭示=宿主['fileManager'] if 宿主 is not None and 'fileManager' in 宿主 and 宿主['fileManager'] is not None else 'directory'#揭示面
        路径=文件['path'] if 'path' in 文件 else ''#路径
        名=路径末段(路径)#末段
        元=文件扩展名(名).upper() or 翻译('presented.file')#扩展或「文件」
        描述=文件['description'] if 'description' in 文件 else None#描述
        if 阶段 is None:#无阶段
            状态文=卡描述(描述,元)#描述或扩展
        elif 揭示=='directory' and 阶段=='revealed':#文件夹已开
            状态文=翻译('presented.directoryOpened')#文案
        elif 揭示=='directory' and 阶段=='revealing':#打开中
            状态文=翻译('presented.directoryOpening')#文案
        elif 揭示=='directory' and 阶段=='revealError':#失败
            状态文=翻译('presented.directoryError')#文案
        else:#其它阶段键
            状态文=翻译(f'presented.{阶段}')#阶段文案
        def 选动作(标识):#菜单选中
            """关闭菜单并回调。"""
            自身.菜单开=False#关
            if 动作 is not None:#有回调
                动作('reveal' if 标识=='reveal' else 'open')#动作
        return {#视图
            'type':'presented-file-card',#类型
            'name':名,#名
            'path':路径,#路径
            'status':状态文,#状态
            'previewHint':翻译('presented.preview'),#预览提示
            'error':阶段 in ('error','revealError','nativeUnavailable'),#错误色
            'actionLabel':翻译('presented.action'),#打开
            'previewAria':翻译('presented.previewButton',{'name':路径}),#预览无障碍
            'cardAria':翻译('presented.previewCard',{'name':路径}),#卡无障碍
            'moreAria':翻译('presented.more',{'name':路径}),#更多
            'menuOpen':自身.菜单开 and not 菜单禁用,#菜单开
            'menuDisabled':菜单禁用,#禁用
            'defaultApp':翻译('presented.defaultApp'),#默认应用
            'revealLabel':翻译(f'presented.{揭示}'),#揭示
            'onPreview':预览,#预览
            'onToggleMenu':自身.切换菜单,#菜单
            'onCloseMenu':lambda:自身.设菜单(False),#关菜单
            'onSelect':选动作,#选
            'cssModule':'Deliverables.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.视图()#渲

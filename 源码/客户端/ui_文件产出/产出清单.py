"""交付物行：产出芯片与已呈现文件卡。

对齐上游 `ui-deliverables/src/client/Deliverables.tsx`。公开面仅中文名。
认领含变更路径或已声明文件的收口回合；props 为槽位合成 dict。
"""
from .产出文件 import 产出文件行#产出芯片行
from .已呈现文件卡 import 已呈现文件卡#已呈现文件卡
from .回合产出 import 选出产出文件,收口已呈现#路径选取
from .已呈现 import 已呈现文件网址#打开坐标

__all__=['折叠已呈现上限','选出交付物','产出清单']#仅中文公开名

折叠已呈现上限=4#折叠时最多展示张数

def 选出交付物(所有者):#认领有产出或已呈现的收口
    """对齐 selectDeliverables：两面皆空则 None。"""
    产出=选出产出文件(所有者)#产出路径或 None
    产出表=list(产出) if 产出 is not None else []#空表
    已呈现表=收口已呈现(所有者)#已呈现
    if len(产出表)+len(已呈现表)==0:#皆空
        return None#拒绝
    return {'produced':产出表,'presented':已呈现表}#匹配

class 产出清单:#回合尾交付物行
    """渲染产出芯片与已呈现文件卡；宿主态由注入面提供。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.展开=False#已呈现是否展开
        自身.产出行=None#内嵌产出行
        自身.存活=True#存活

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 卸载(自身):#卸载
        """标死。"""
        自身.存活=False#死

    def 切换展开(自身):#折叠/展开
        """翻转已呈现展开。"""
        自身.展开=not 自身.展开#翻

    def 视图(自身):#读视图模型
        """投影交付物行。"""
        匹配=自身.属性['matched'] if 'matched' in 自身.属性 else {'produced':[],'presented':[]}#匹配
        产出表=list(匹配['produced']) if 'produced' in 匹配 and 匹配['produced'] is not None else []#产出
        已呈现表=list(匹配['presented']) if 'presented' in 匹配 and 匹配['presented'] is not None else []#已呈现
        翻译=自身.属性['t']#文案
        打开文件=自身.属性['openFile']#打开
        会话标识=自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None#会话
        打开已呈现=自身.属性['openPresented'] if 'openPresented' in 自身.属性 else None#原生打开
        用打开态=自身.属性['usePresentedOpen'] if 'usePresentedOpen' in 自身.属性 else None#打开态钩子
        用宿主=自身.属性['usePresentedHost'] if 'usePresentedHost' in 自身.属性 else None#宿主钩子
        重载宿主=自身.属性['reloadPresentedHost'] if 'reloadPresentedHost' in 自身.属性 else None#重载
        用会话=自身.属性['useSessions'] if 'useSessions' in 自身.属性 else None#会话钩子
        工作目录=None#cwd
        if 用会话 is not None and 会话标识 is not None:#有钩子
            def 取目录(态):#读 cwd
                """byId[sessionId].cwd。"""
                表=态['byId'] if 'byId' in 态 else {}#表
                项=表[会话标识] if 会话标识 in 表 else None#项
                return 项['cwd'] if 项 is not None and 'cwd' in 项 else None#cwd
            工作目录=用会话(取目录)#cwd
        打开态=用打开态(lambda 值:值) if 用打开态 is not None else {}#阶段图
        宿主=用宿主(lambda 值:值) if 用宿主 is not None else None#宿主
        可折叠=len(已呈现表)>折叠已呈现上限#可折叠
        展示=已呈现表[:折叠已呈现上限] if 可折叠 and not 自身.展开 else 已呈现表#展示表
        产出面=None#产出行
        if len(产出表)>0:#有产出
            if 自身.产出行 is None:#尚未建
                自身.产出行=产出文件行({'matched':产出表,'openFile':打开文件,'t':翻译})#建
            else:#已有
                自身.产出行.更新({'matched':产出表,'openFile':打开文件,'t':翻译})#刷
            产出面=自身.产出行()#视图
        卡片=[]#已呈现卡
        for 文件 in 展示:#每项
            网址=已呈现文件网址(会话标识,文件['seq'],文件['index']) if 会话标识 is not None else ''#坐标
            阶段=打开态[网址] if 网址 in 打开态 else None#阶段
            def 预览(路=文件['path']):#侧边栏预览
                """openFile。"""
                打开文件(路)#打开
            def 动作(动作名,序=文件['seq'],下=文件['index']):#原生动作
                """openPresented。"""
                if 打开已呈现 is not None and 会话标识 is not None:#有面
                    打开已呈现(会话标识,序,下,动作名)#打开
            卡=已呈现文件卡({#卡 props
                'file':文件,#文件
                'cwd':工作目录,#工作目录
                'phase':阶段,#阶段
                'host':None if 宿主=='error' else 宿主,#宿主
                'onPreview':预览,#预览
                'onAction':动作,#动作
                't':翻译,#文案
            })#卡
            卡片.append(卡())#视图
        return {#视图
            'type':'deliverables',#类型
            'produced':产出面,#产出行
            'hostError':翻译('presented.hostError') if 宿主=='error' else None,#宿主错
            'hostRetry':翻译('presented.retry') if 宿主=='error' else None,#重试
            'reloadHost':重载宿主,#重载
            'unavailable':翻译('presented.unavailable') if 宿主 is not None and 宿主!='error' and ('available' not in 宿主 or 宿主['available'] is not True) else None,#不可用
            'presented':卡片 if len(已呈现表)>0 else None,#已呈现卡
            'single':len(已呈现表)==1,#单卡
            'toggle':{#折叠钮
                'expanded':自身.展开,#展开
                'label':翻译('presented.collapse' if 自身.展开 else 'presented.all',{'count':str(len(已呈现表))}),#文案
                'aria':翻译('presented.collapseAria' if 自身.展开 else 'presented.expandAria',{'count':str(len(已呈现表))}),#无障碍
                'onToggle':自身.切换展开,#切换
            } if 可折叠 else None,#可折叠才有
            'cssModule':'Deliverables.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图

from nicegui import ui as 界面
from .异常 import 页面失败文案
from .回合产出 import 收口已呈现,收口改动#路径选取
from .已呈现 import 已呈现文件网址#打开坐标
from .改动 import 改动摘要网址#摘要键
from .改动文件 import 改动文件,画改动文件#改动卡
from .已呈现文件卡 import 已呈现文件卡#已呈现文件卡

__all__=['折叠已呈现上限','选出交付物','产出清单']#仅中文公开名

折叠已呈现上限=4#折叠时最多展示张数

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

def 选出交付物(所有者):#认领有改动公告或已呈现的收口
    '对齐 selectDeliverables：两面皆空则 None'
    改动=收口改动(所有者)#改动公告
    已呈现表=收口已呈现(所有者)#已呈现
    if 改动 is None and len(已呈现表)==0:#皆空
        return None#拒绝
    return {'changes':改动,'presented':已呈现表}#匹配

class 产出清单:#回合尾交付物行
    '渲染改动文件卡与已呈现文件卡；宿主态由注入面提供'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props
        自身.展开=False#已呈现是否展开
        自身.改动展开=False#改动是否展开
        自身.呈现卡={ }#坐标 → 已呈现文件卡
        自身.存活=True#存活
        自身.已订=False#宿主与摘要只订一次
        自身.已请宿主=False#空宿主只拉一次
        自身.绘制中=False#避免订阅重入
        自身.待重画=False#绘制期间又来了一次
        if isinstance(自身.属性,dict) and 't' in 自身.属性 and 'openFile' in 自身.属性:#键齐
            自身.渲染()#构造末尾才画

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 卸载(自身):#卸载
        '标死'
        自身.存活=False#死

    def 切换展开(自身):#折叠/展开已呈现
        '翻转已呈现展开'
        自身.展开=not 自身.展开#翻

    def 切换改动展开(自身):#折叠/展开改动
        '翻转改动展开'
        自身.改动展开=not 自身.改动展开#翻

    def 订钩子(自身):
        '宿主、摘要、开发者工具或会话目录变了就重画'
        if 自身.已订 is True:#已订
            return#一次
        自身.已订=True#记下
        def 重画():
            '存储变了再画'
            if 自身.存活 is not True:#已卸
                return#停
            if 自身.绘制中 is True:#正在画
                自身.待重画=True#画完再来
                return#停
            自身.渲染()#重画
        for 名 in ('usePresentedHost','usePresentedOpen','useChangesSummary','useShowCodeDiff','useSessions'):#钩子
            用=自身.属性[名] if 名 in 自身.属性 else None#选择器
            订=getattr(用,'_subscribe',None) if 用 is not None else None#框架订阅
            if callable(订):#有方法
                订(重画)#订上

    def 视图(自身):#读视图模型
        '投影交付物行。没有改动也没有已呈现时返回 None，不画空壳'
        匹配=自身.属性['matched'] if 'matched' in 自身.属性 else 选出交付物(自身.属性)#匹配
        if 匹配 is None:#无认领
            return None#与上游 DeliverablesTail 一样不画
        已呈现表=list(匹配['presented']) if 'presented' in 匹配 and 匹配['presented'] is not None else []#已呈现
        公告=匹配['changes'] if 'changes' in 匹配 else None#改动公告
        翻译=自身.属性['t']#文案
        打开文件=自身.属性['openFile']#打开
        会话标识=自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None#会话
        打开已呈现=自身.属性['openPresented'] if 'openPresented' in 自身.属性 else None#原生打开
        打开审阅=自身.属性['openChangesReview'] if 'openChangesReview' in 自身.属性 else None#审阅
        加载摘要=自身.属性['loadChangesSummary'] if 'loadChangesSummary' in 自身.属性 else None#摘要
        用打开态=自身.属性['usePresentedOpen'] if 'usePresentedOpen' in 自身.属性 else None#打开态钩子
        用宿主=自身.属性['usePresentedHost'] if 'usePresentedHost' in 自身.属性 else None#宿主钩子
        用摘要=自身.属性['useChangesSummary'] if 'useChangesSummary' in 自身.属性 else None#摘要钩子
        重载宿主=自身.属性['reloadPresentedHost'] if 'reloadPresentedHost' in 自身.属性 else None#重载
        用会话=自身.属性['useSessions'] if 'useSessions' in 自身.属性 else None#会话钩子
        工作目录=None#cwd
        if 用会话 is not None and 会话标识 is not None:
            def 取目录(态):#读 cwd
                'byId[sessionId].cwd'
                表=态['byId'] if 'byId' in 态 else {}#表
                项=表[会话标识] if 会话标识 in 表 else None#项
                return 项['cwd'] if 项 is not None and 'cwd' in 项 else None#cwd
            工作目录=用会话(取目录)#cwd
        def 取打开态(值):#打开态原样
            '阶段图'
            return 值#值
        打开态=用打开态(取打开态) if 用打开态 is not None else {}#阶段图
        def 取宿主(值):#宿主
            '宿主'
            return 值#值
        宿主=用宿主(取宿主) if 用宿主 is not None else None#宿主
        if 宿主 is None and 重载宿主 is not None and 自身.已请宿主 is not True:#空宿主拉一次
            自身.已请宿主=True#避免重入
            重载宿主()#读桌面
        if 宿主 is not None:#已经有值
            自身.已请宿主=False#下次清空还能再拉
        用代码对比=自身.属性['useShowCodeDiff'] if 'useShowCodeDiff' in 自身.属性 else None#开发者工具
        显示改动=用代码对比(lambda 值:值) is True if 用代码对比 is not None else False#未开则不画改动卡
        改动面=None#改动卡
        if 显示改动 and 公告 is not None and 会话标识 is not None and 用摘要 is not None:
            键=改动摘要网址(会话标识,公告['seq'])#键
            def 取摘要(值):#摘要态
                '按键取'
                return 值[键] if 键 in 值 else None#态
            摘要=用摘要(取摘要)#摘要
            if 摘要 is None and 加载摘要 is not None:#未加载
                加载摘要(会话标识,公告['seq'])#触发
            if isinstance(摘要,dict) and 'files' in 摘要 and len(摘要['files'])>0:
                def 开审阅(下标):#打开审阅
                    'openChangesReview'
                    if 打开审阅 is not None:
                        打开审阅({'sessionId':会话标识,'seq':公告['seq'],'turn':摘要['turn']},下标)#开
                改动面=改动文件({#卡
                    'changes':{'seq':公告['seq'],**摘要},#摘要
                    'cwd':工作目录,#cwd
                    'openReview':开审阅,#审阅
                    't':翻译,#文案
                    'expanded':自身.改动展开,#展开
                    'onToggle':自身.切换改动展开,#切换
                })#视图
        可折叠=len(已呈现表)>折叠已呈现上限#可折叠
        展示=已呈现表[:折叠已呈现上限] if 可折叠 and not 自身.展开 else 已呈现表#展示表
        卡片=[]#已呈现卡
        保留=set()#本轮仍在展示的坐标
        for 文件 in 展示:#每项
            网址=已呈现文件网址(会话标识,文件['seq'],文件['index']) if 会话标识 is not None else ''#坐标
            阶段=打开态[网址] if 网址 in 打开态 else None#阶段
            def 预览(路=文件['path']):#侧边栏预览
                'openFile'
                打开文件(路)#打开
            def 动作(动作名,应用=None,序=文件['seq'],下=文件['index']):#原生动作
                'openPresented'
                if 打开已呈现 is not None and 会话标识 is not None:
                    打开已呈现(会话标识,序,下,动作名,应用)#打开
            画槽=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None#文件动作槽
            def 画动作(序=文件['seq'],下=文件['index'],回调=动作,槽=画槽,可用宿主=宿主,打开阶段=阶段):
                '空槽不补打开文案。在应用中打开登记后才出现'
                if not callable(槽):#没有画槽
                    return#不画
                槽('deliverables.file.actions',{#属主
                    'actionUrl':已呈现文件网址(会话标识,序,下) if 会话标识 is not None else '',#路由
                    'available':isinstance(可用宿主,dict) and 可用宿主.get('available') is True,#桌面
                    'pending':打开阶段 in ('opening','revealing'),#在飞
                    'onAction':回调,#执行
                    't':翻译,#文案
                })
            卡属性={#卡 props
                'file':文件,#文件
                'cwd':工作目录,#工作目录
                'phase':阶段,#阶段
                'host':None if 宿主=='error' else 宿主,#宿主
                'onPreview':预览,#预览
                'onAction':动作,#动作
                '画动作':画动作,#父组件把动作槽画进卡内
                't':翻译,#文案
            }
            旧卡=自身.呈现卡[网址] if 网址 in 自身.呈现卡 else None
            if 旧卡 is None:
                卡=已呈现文件卡(卡属性)
            else:
                旧卡.更新(卡属性)
                卡=旧卡
            自身.呈现卡[网址]=卡
            保留.add(网址)
            卡片.append(卡)#实例
        for 键 in list(自身.呈现卡):
            if 键 not in 保留:
                del 自身.呈现卡[键]
        return {#视图
            'type':'deliverables',#类型
            'changes':改动面,#改动卡
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

    def 渲染(自身):
        '改动卡、宿主错误与已呈现文件。没有产出时不画'
        if 自身.绘制中 is True:#重入
            自身.待重画=True#记下
            return#让外层收尾
        自身.绘制中=True#占住
        try:#整段绘制
            自身._画出()#画
        finally:#放行
            自身.绘制中=False#结束
            if 自身.待重画 is True:#绘制期间又变了
                自身.待重画=False#消费
                自身.渲染()#再画

    def _画出(自身):
        '一次绘制'
        视=自身.视图()
        自身.订钩子()#没有产出也要能在数据到达后重画
        if 视 is None:#本回合没有文件
            腾出根(自身)#清掉上一帧
            return#不画空壳
        清除失败=腾出根(自身)
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('deliverables')
        with 自身.根:
            标出失败(清除失败)
            if isinstance(视['changes'],dict):
                折叠改动=视['changes']['toggle'] if 'toggle' in 视['changes'] else None
                if isinstance(折叠改动,dict) and 折叠改动['onToggle'] is not None:
                    原切换=折叠改动['onToggle']
                    def 切换后重画(_事件=None,原=原切换):
                        '展开状态写在清单上，切换后重画行数'
                        原()
                        自身.渲染()
                    折叠改动['onToggle']=切换后重画
                画改动文件(视['changes'])
            已呈现=视['presented']
            if isinstance(已呈现,list) and len(已呈现)>0:
                if isinstance(视['hostError'],str) and 视['hostError']!='':
                    界面.label(视['hostError'])
                    if isinstance(视['hostRetry'],str) and 视['hostRetry']!='' and 视['reloadHost'] is not None:
                        def 点重试():
                            '重读宿主'
                            视['reloadHost']()
                            自身.渲染()
                        界面.button(视['hostRetry'],on_click=点重试).props('flat no-caps')
                if isinstance(视['unavailable'],str) and 视['unavailable']!='':
                    界面.label(视['unavailable'])
                for 卡 in 已呈现:#卡在自己的根里画预览，并在卡内调用画动作
                    卡.渲染()#父组件负责这一次，构造时不画
                折叠=视['toggle']
                if isinstance(折叠,dict):
                    def 点折叠():
                        '展开或收起已呈现'
                        折叠['onToggle']()
                        自身.渲染()
                    界面.button(折叠['label'],on_click=点折叠).props('flat no-caps')

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()

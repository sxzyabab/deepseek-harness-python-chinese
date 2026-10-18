'把框架钩子收成桌面引导的纯视图'
from ...模块.客户端.通告 import 取握手窗口
from ...ui_对话.异常 import 挂上
from .文案 import 中文
from .上手引导表面 import 上手引导表面
from .桌面上手引导 import 桌面上手引导

__all__=['桌面上手引导入口']

class 桌面上手引导入口:
    '读引导和账号。完成后短暂留着退出动画'
    def __init__(自身,属性):
        '记下壳层动作'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.引导=None
        自身.表面=None
        自身.上次可见=None
        自身.退出=False
        自身.定时=None
        自身.已声明=False
        自身.已订=False
        自身.退订=[]
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '绘制中再来一次只记一笔'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.画出()
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 读(自身,名):
        '整份快照'
        钩=自身.属性.get(名)
        if 钩 is None:
            return {}
        def 全量(快照):
            '原样返回'
            return 快照
        值=钩(全量)
        if isinstance(值,dict):
            return 值
        return {}

    def 画出(自身):
        '加载时盖住工作区。完成后按减动效决定要不要退出动画'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        状态=自身.读('useOnboarding')
        账号=自身.读('useAccount')
        可见状态=状态.get('visible') is True
        if 可见状态:
            桥=getattr(窗口,'dshOnboarding',None)
            if 桥 is not None and 自身.已声明 is not True and hasattr(桥,'setActive'):
                桥.setActive(True)
                自身.已声明=True
        elif 自身.已声明:
            桥=getattr(窗口,'dshOnboarding',None)
            if 桥 is not None and hasattr(桥,'setActive'):
                桥.setActive(False)
            自身.已声明=False
        视图=账号.get('view') if isinstance(账号.get('view'),dict) else None
        已登录=isinstance(视图,dict) and 视图.get('status')=='credential-stored'
        完成=可见状态 is not True and 状态.get('progress',{}).get('step')=='done' and 已登录
        待完成=完成 and 状态.get('status')=='saving'
        已完成=完成 and 状态.get('status')=='ready'
        if 可见状态:
            自身.上次可见=状态
        elif 已完成 is not True and 待完成 is not True:
            自身.上次可见=None
        媒体=窗口.matchMedia('(prefers-reduced-motion: reduce)')
        减动=媒体 is not None and 媒体.matches is True
        退出=已完成 and 自身.上次可见 is not None and 减动 is not True
        if 退出 and 自身.退出 is not True:
            自身.退出=True
            if 自身.定时 is not None:
                窗口.clearTimeout(自身.定时)
            def 结束():
                '退出动画结束'
                自身.退出=False
                自身.上次可见=None
                自身.定时=None
                自身.渲染()
            自身.定时=窗口.setTimeout(结束,180)
        elif 退出 is not True:
            自身.退出=False
        显示=状态 if 可见状态 else 自身.上次可见 if (退出 or 待完成) else None
        盖住=显示 is not None or 状态.get('status')=='loading'
        设可见=属性.get('setVisible')
        if 设可见 is not None:
            设可见(盖住)
        if 显示 is None:
            if 状态.get('status')=='loading':
                载=文档.createElement('div')
                载.setAttribute('role','status')
                载.textContent=中文['onboardingLoading']
                if 自身.表面 is None:
                    自身.表面=上手引导表面({'window':窗口,'children':载})
                else:
                    自身.表面.更新({'window':窗口,'children':载,'exiting':False})
                    自身.表面.渲染()
                挂上(自身.根,自身.表面)
            elif 自身.表面 is not None:
                自身.表面.拆除()
                自身.表面=None
            if 自身.引导 is not None:
                自身.引导.拆除()
                自身.引导=None
            自身.订上()
            return
        展示=显示
        if 待完成:
            展示=dict(显示)
            展示['status']='saving'
        引导属性=dict(属性)
        引导属性['window']=窗口
        引导属性['locale']=中文['onboardingArtworkLocale']
        引导属性['state']=展示
        引导属性['account']=账号
        引导属性['exiting']=退出
        if 自身.引导 is None:
            自身.引导=桌面上手引导(引导属性)
        else:
            自身.引导.更新(引导属性)
            自身.引导.渲染()
        挂上(自身.根,自身.引导)
        自身.订上()

    def 订上(自身):
        '引导或账号变化时重画'
        if 自身.已订:
            return
        def 变更():
            '绘制中只记一笔'
            if 自身.绘制中:
                自身.待重画=True
                return
            自身.渲染()
        for 名 in ('useOnboarding','useAccount'):
            钩=自身.属性.get(名)
            订=getattr(钩,'_subscribe',None) if 钩 is not None else None
            if callable(订):
                自身.退订.append(订(变更))
        自身.已订=True

    def 拆除(自身):
        '卸下桥、定时器和页面'
        窗口=取握手窗口()
        if 自身.已声明:
            桥=getattr(窗口,'dshOnboarding',None)
            if 桥 is not None and hasattr(桥,'setActive'):
                桥.setActive(False)
        自身.已声明=False
        if 自身.定时 is not None:
            窗口.clearTimeout(自身.定时)
            自身.定时=None
        for 退 in 自身.退订:
            退()
        自身.退订=[]
        自身.已订=False
        if 自身.引导 is not None:
            自身.引导.拆除()
        if 自身.表面 is not None:
            自身.表面.拆除()

'串起欢迎、额度、用途、过程和确认，以及共享的充值页'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上,清空子
from ...ui_基础界面组件 import 按钮
from .文案 import 中文
from .上手引导余额 import 有上手引导额度
from .上手引导表面 import 上手引导表面
from .上手引导欢迎步 import 上手引导欢迎步
from .上手引导额度步 import 上手引导额度步
from .上手引导目的步 import 上手引导目的步
from .上手引导过程步 import 上手引导过程步
from .上手引导确认 import 上手引导确认
from .上手引导插图 import 图地址

__all__=['桌面上手引导']

样式模块='桌面上手引导'
页名={
    'welcome':'onboarding_welcome',
    'credit':'onboarding_recharge',
    'purpose':'onboarding_use_case',
    'process':'onboarding_process',
    'done':None,
}
用途埋点={'office':'office','development':'code','both':'code_office'}
过程埋点={'compact':'focus_result','standard':'key_detail','detailed':'full_process'}

def 接上(结果,成功):
    '完成写入后再关确认框'
    if hasattr(结果,'然后'):
        结果.然后(成功)
        return
    然后=getattr(结果,'then',None)
    if callable(然后):
        然后(成功)
        return
    成功(结果)

class 桌面上手引导:
    '当前这一步的页面，以及跳过时的确认'
    def __init__(自身,属性):
        '从持久进度的步骤开始'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.表面=None
        自身.确认框=None
        自身.欢迎=None
        自身.额度=None
        自身.目的=None
        自身.过程=None
        自身.对话框=None
        自身.标题盒={'当前':None}
        自身.页=None
        自身.放开充值=None
        进度=自身.进度()
        自身.显示步=进度.get('step')
        自身.已看页=None
        自身.已看弹窗=None
        自身.动画=None
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 进度(自身):
        '当前状态里的进度'
        状态=自身.属性.get('state')
        if isinstance(状态,dict) and isinstance(状态.get('progress'),dict):
            return 状态['progress']
        return {'step':'welcome','purpose':None,'process':None}

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

    def 埋点(自身,名,属性=None):
        '没有采集器就跳过'
        跟踪=自身.属性.get('track')
        if 跟踪 is not None:
            跟踪(名,属性 if 属性 is not None else {})

    def 去(自身,步):
        '写入下一步'
        更新=自身.属性.get('update')
        if 更新 is not None:
            更新({'step':步})

    def 充值(自身):
        '打开共享的充值页'
        自身.对话框=None
        if 自身.放开充值 is not None:
            自身.放开充值()
        打开=自身.属性.get('openPlatformPage')
        if 打开 is None:
            自身.放开充值=None
            return
        def 结束(_原因=None):
            '这次充值不再占有页面'
            自身.放开充值=None
        自身.放开充值=打开('top-up',结束)

    def 稍后(自身):
        '没有额度就先确认，否则去用途'
        账号=自身.属性.get('account') if isinstance(自身.属性.get('account'),dict) else {}
        细节=账号.get('details') if isinstance(账号.get('details'),dict) else {}
        余额=细节.get('balance')
        if isinstance(余额,dict) and 余额.get('status')=='ready' and 有上手引导额度(余额) is not True:
            自身.对话框='credit'
        else:
            自身.去('purpose')
        自身.渲染()

    def 画出(自身):
        '加载中只显示一句。其余按步骤画页面'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '桌面上手引导样式',
            os.path.join(os.path.dirname(__file__),'桌面上手引导.module.css'),
            样式模块,
        )
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        else:
            清空子(自身.根)
        状态=属性.get('state') if isinstance(属性.get('state'),dict) else {}
        进度=自身.进度()
        目标=进度.get('step')
        可见=状态.get('visible') is True
        忙=状态.get('status') in ('loading','saving') or 属性.get('exiting') is True or 自身.显示步!=目标
        if 可见 and 状态.get('status')=='loading':
            载=文档.createElement('div')
            载.className='loading'
            载.setAttribute('role','status')
            载.setAttribute('data-dsh-css',样式模块)
            载.textContent=中文['onboardingLoading']
            表面=上手引导表面({'window':窗口,'children':载,'exiting':False})
            if 自身.表面 is None:
                自身.表面=表面
            else:
                自身.表面.更新({'window':窗口,'children':载,'exiting':False})
                自身.表面.渲染()
            挂上(自身.根,自身.表面)
            return
        页=页名.get(自身.显示步)
        if 可见 is not True or 页 is None:
            return
        自身.记页(状态,页)
        自身.记弹窗(状态)
        能充=属性.get('openPlatformPage') is not None
        语言=属性.get('locale') or 中文['onboardingArtworkLocale']
        步属性={
            'window':窗口,
            'heading':自身.标题盒,
            'busy':忙,
            'locale':语言,
            't':None,
        }
        子=None
        if 自身.显示步=='welcome':
            def 开始():
                '去额度页'
                自身.点('next')
                自身.去('credit')
            步属性['onStart']=开始
            子=自身.换步(自身,'欢迎',上手引导欢迎步,步属性)
        elif 自身.显示步=='credit':
            def 继续():
                '去用途'
                自身.点('continue')
                自身.去('purpose')
            def 去充值():
                '埋点后打开充值'
                自身.点('charge')
                自身.充值()
            def 稍后():
                '埋点后决定要不要确认'
                自身.点('later')
                自身.稍后()
            步属性['funded']=状态.get('creditFunded') is True
            步属性['canRecharge']=能充
            步属性['onContinue']=继续
            步属性['onRecharge']=去充值
            步属性['onLater']=稍后
            子=自身.换步(自身,'额度',上手引导额度步,步属性)
        elif 自身.显示步=='purpose':
            def 选择(值):
                '写入用途'
                更新=属性.get('update')
                if 更新 is not None:
                    更新({'purpose':值})
            def 继续():
                '办公直接完成，否则去过程'
                自身.点('next')
                if 进度.get('purpose')=='office':
                    完成=属性.get('complete')
                    if 完成 is not None:
                        完成('completed')
                else:
                    自身.去('process')
            步属性['purpose']=进度.get('purpose')
            步属性['onSelect']=选择
            步属性['onContinue']=继续
            子=自身.换步(自身,'目的',上手引导目的步,步属性)
        elif 自身.显示步=='process':
            def 选择(值):
                '写入过程'
                更新=属性.get('update')
                if 更新 is not None:
                    更新({'process':值})
            def 完成步():
                '进入应用'
                自身.点('next')
                完成=属性.get('complete')
                if 完成 is not None:
                    完成('completed')
            步属性['process']=进度.get('process')
            步属性['onSelect']=选择
            步属性['onComplete']=完成步
            子=自身.换步(自身,'过程',上手引导过程步,步属性)
        节=文档.createElement('section')
        节.className='page'
        if 自身.对话框 is not None:
            节.className=节.className+' blurred'
        节.setAttribute('data-desktop-onboarding',自身.显示步 or '')
        节.setAttribute('data-dsh-css',样式模块)
        节.lang=语言
        节.setAttribute('aria-labelledby','desktop-onboarding-title')
        节.setAttribute('aria-busy','true' if 忙 else 'false')
        if 子 is not None:
            挂上(节,子)
        if 状态.get('error') is not None:
            警=文档.createElement('div')
            警.className='status'
            警.setAttribute('role','alert')
            警.setAttribute('data-dsh-css',样式模块)
            警.appendChild(文档.createTextNode(中文['onboardingSaveFailed']))
            def 重试():
                '再写一次'
                回调=属性.get('retry')
                if 回调 is not None:
                    回调()
            钮=按钮({'window':窗口,'disabled':忙,'onClick':重试,'children':中文['onboardingRetry']})
            挂上(警,钮)
            节.appendChild(警)
        if 自身.显示步!='welcome':
            脚=文档.createElement('footer')
            脚.className='navigation'
            脚.setAttribute('data-dsh-css',样式模块)
            回=文档.createElement('button')
            回.type='button'
            回.disabled=忙
            图标=文档.createElement('span')
            图标.className='backIcon'
            图标.setAttribute('aria-hidden','true')
            图标.setAttribute('data-dsh-css',样式模块)
            图标.style.maskImage='url('+图地址('onboarding-back.svg')+')'
            回.appendChild(图标)
            回.appendChild(文档.createTextNode(中文['onboardingBack']))
            def 返回(_事件=None):
                '回到上一步'
                自身.点('back')
                if 自身.显示步=='credit':
                    自身.去('welcome')
                elif 自身.显示步=='purpose':
                    自身.去('credit')
                else:
                    自身.去('purpose')
            回.addEventListener('click',返回)
            跳=文档.createElement('button')
            跳.type='button'
            跳.disabled=忙
            跳.textContent=中文['onboardingSkip']
            def 跳过(_事件=None):
                '额度页和后面的跳过分开确认'
                自身.点('skip')
                自身.对话框='credit-skip' if 自身.显示步=='credit' else 'skip'
                自身.渲染()
            跳.addEventListener('click',跳过)
            脚.appendChild(回)
            脚.appendChild(跳)
            节.appendChild(脚)
        自身.页=节
        表面属性={'window':窗口,'children':节,'exiting':属性.get('exiting') is True}
        if 自身.表面 is None:
            自身.表面=上手引导表面(表面属性)
        else:
            自身.表面.更新(表面属性)
            自身.表面.渲染()
        挂上(自身.根,自身.表面)
        if 自身.对话框 is not None:
            def 关框(按钮名):
                '弹窗埋点后关闭'
                自身.弹窗点(按钮名)
                自身.对话框=None
                自身.渲染()
            def 知道():
                '知道了，去用途'
                自身.弹窗点('know')
                自身.对话框=None
                自身.去('purpose')
                自身.渲染()
            def 去充():
                '弹窗里去充值'
                自身.弹窗点('charge')
                自身.充值()
                自身.渲染()
            def 跳过完成():
                '跳过并在写完后关框'
                自身.弹窗点('enter' if 自身.对话框=='skip' else 'know')
                完成=属性.get('complete')
                def 已完(_值=None):
                    '写完再关'
                    自身.对话框=None
                    自身.渲染()
                if 完成 is None:
                    已完()
                else:
                    接上(完成('skipped'),已完)
            def 关():
                '关闭确认'
                关框('close')
            def 继续设置():
                '留下继续设置'
                关框('setting')
            确认属性={
                'window':窗口,
                'kind':自身.对话框,
                'busy':忙,
                'canRecharge':能充,
                'onClose':关,
                'onContinueSetup':继续设置,
                'onContinue':知道,
                'onRecharge':去充,
                'onSkip':跳过完成,
            }
            if 自身.确认框 is None:
                自身.确认框=上手引导确认(确认属性)
            else:
                自身.确认框.更新(确认属性)
                自身.确认框.渲染()
            挂上(自身.根,自身.确认框)
        题=自身.标题盒.get('当前')
        if 题 is not None:
            题.focus()
        自身.过渡(目标,可见)

    def 换步(自身,持有,名字,类,属性):
        '同一步复用实例'
        现=getattr(自身,名字)
        if 现 is None:
            现=类(属性)
            setattr(自身,名字,现)
        else:
            现.更新(属性)
            现.渲染()
        return 现

    def 记页(自身,状态,页):
        '每一页只记一次浏览'
        if 状态.get('visible') is not True or 自身.属性.get('exiting') is True:
            自身.已看页=None
            return
        if 状态.get('status')=='loading' or 自身.已看页==页:
            return
        自身.已看页=页
        自身.埋点('onboarding_page_view',{'page_name':页})

    def 记弹窗(自身,状态):
        '每个确认框只记一次'
        if 自身.对话框 is None or 状态.get('visible') is not True or 状态.get('status')=='loading' or 自身.显示步=='done':
            自身.已看弹窗=None
            return
        if 自身.已看弹窗==自身.对话框:
            return
        自身.已看弹窗=自身.对话框
        名='skip_setting' if 自身.对话框=='skip' else 'skip_charge'
        自身.埋点('onboarding_popup_view',{'popup_name':名})

    def 点(自身,按钮名):
        '页面按钮埋点，带上当前选择'
        进度=自身.进度()
        页=页名.get(自身.显示步)
        载荷={'page_name':页,'button_name':按钮名}
        if 自身.显示步=='purpose' and 进度.get('purpose') in 用途埋点:
            载荷['selected_content']=用途埋点[进度['purpose']]
        if 自身.显示步=='process' and 进度.get('process') in 过程埋点:
            载荷['selected_content']=过程埋点[进度['process']]
        自身.埋点('onboarding_page_click',载荷)

    def 弹窗点(自身,按钮名):
        '确认框按钮埋点'
        名='skip_setting' if 自身.对话框=='skip' else 'skip_charge'
        自身.埋点('onboarding_popup_click',{'popup_name':名,'button_name':按钮名})

    def 过渡(自身,目标,可见):
        '减动效或没有动画就直接换步'
        if 自身.显示步==目标 or 自身.动画 is not None:
            return
        窗口=取握手窗口()
        媒体=窗口.matchMedia('(prefers-reduced-motion: reduce)')
        减动=媒体 is not None and 媒体.matches is True
        if 可见 is not True or 自身.页 is None or hasattr(自身.页,'animate') is not True or 减动:
            自身.显示步=目标
            自身.渲染()
            return
        动画=自身.页.animate([{'opacity':1},{'opacity':0}],{'duration':40,'fill':'forwards','easing':'ease-out'})
        自身.动画=动画
        def 切(_值=None):
            '淡出后换成目标步'
            自身.动画=None
            自身.显示步=目标
            自身.渲染()
        完成=getattr(动画,'finished',None)
        if 完成 is not None and hasattr(完成,'then'):
            完成.then(切,切)
        else:
            切()

    def 拆除(自身):
        '放开充值页和表面'
        if 自身.放开充值 is not None:
            自身.放开充值()
            自身.放开充值=None
        if 自身.动画 is not None:
            自身.动画.cancel()
            自身.动画=None
        if 自身.表面 is not None:
            自身.表面.拆除()

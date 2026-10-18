'侧栏赠金卡片。画出一帧且页面可见才算展示过'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件
from ...ui_基础界面组件.icons import 图标关闭描边常规
from .文案 import 中文

__all__=['账号须知卡片','仍可花']

样式模块='账号须知'
铃铛='M3.6355 6.93969C3.6355 4.8398 5.33779 3.1375 7.43768 3.1375C9.53757 3.1375 11.23987 4.8398 11.23987 6.93968V11.363H3.6355V6.93969Z'
铃铛线='M1.641 11.3645H12.36M5.053 13.3095H8.9479M7.4375 4.27422V2.70137912'

def 仍可花(到期于):
    '解析不了的时间不算过期'
    窗口=取握手窗口()
    到期=窗口.Date.parse(到期于)
    if 到期 is None or 到期!=到期:
        return True
    return 到期>窗口.Date.now()

class 账号须知卡片:
    '挂在账号按钮上方。关掉也算看过'
    def __init__(自身,属性):
        '记下通知和锚点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.卡片=None
        自身.订单=None
        自身.已报告=False
        自身.位置=None
        自身.拆除器=[]
        自身.绘制中=False
        自身.待重画=False
        通知=自身.属性.get('notice')
        if isinstance(通知,dict):
            自身.订单=通知.get('orderId')
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props。换订单就重新量位置'
        通知=属性.get('notice') if isinstance(属性,dict) else None
        新单=通知.get('orderId') if isinstance(通知,dict) else None
        if 新单!=自身.订单:
            自身.已报告=False
            自身.位置=None
            自身.订单=新单
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

    def 画出(自身):
        '过期不画。有位置后挂到 body'
        自身.拆监听()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '账号须知样式',
            os.path.join(os.path.dirname(__file__),'账号须知.module.css'),
            样式模块,
        )
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
        通知=属性.get('notice') if isinstance(属性.get('notice'),dict) else {}
        if 仍可花(通知.get('expiresAt')) is not True:
            if 自身.卡片 is not None and 自身.卡片.parentNode is not None:
                自身.卡片.remove()
            自身.卡片=None
            return
        锚=属性.get('anchor')
        if 锚 is not None:
            def 量():
                '卡片左边跟侧栏，底边在按钮上方'
                矩形=锚.getBoundingClientRect()
                左=矩形.left
                if 左<8:
                    左=8
                右限=窗口.innerWidth-268
                if 左>右限:
                    左=右限
                底=窗口.innerHeight-矩形.top+4
                if 底<8:
                    底=8
                自身.位置={'left':左,'bottom':底}
                if 自身.卡片 is not None:
                    自身.卡片.style.left=str(左)+'px'
                    自身.卡片.style.bottom=str(底)+'px'
                    自身.卡片.style.visibility='visible'
            量()
            观察=窗口.ResizeObserver(量)
            观察.observe(锚)
            窗口.addEventListener('resize',量)
            窗口.addEventListener('scroll',量,True)
            def 拆量():
                '卸下尺寸监听'
                观察.disconnect()
                窗口.removeEventListener('resize',量)
                窗口.removeEventListener('scroll',量,True)
            自身.拆除器.append(拆量)
        if 自身.卡片 is None:
            卡=文档.createElement('aside')
            卡.className='card'
            卡.setAttribute('data-dsh-css',样式模块)
            文=文档.createElement('div')
            文.className='copy'
            文.setAttribute('role','status')
            文.setAttribute('data-dsh-css',样式模块)
            题行=文档.createElement('div')
            题行.className='title'
            题行.setAttribute('data-dsh-css',样式模块)
            图标=文档.createElement('span')
            图标.className='icon'
            图标.setAttribute('aria-hidden','true')
            图标.setAttribute('data-dsh-css',样式模块)
            图=文档.createElement('svg')
            图.setAttribute('width','14')
            图.setAttribute('height','14')
            图.setAttribute('viewBox','0 0 14 14')
            图.setAttribute('fill','none')
            路=文档.createElement('path')
            路.setAttribute('d',铃铛)
            路.setAttribute('fill','currentColor')
            路.setAttribute('fill-opacity','0.2')
            路.setAttribute('stroke','currentColor')
            路.setAttribute('stroke-width','0.875')
            图.appendChild(路)
            线=文档.createElement('path')
            线.setAttribute('d',铃铛线)
            线.setAttribute('stroke','currentColor')
            线.setAttribute('stroke-width','0.875')
            图.appendChild(线)
            图标.appendChild(图)
            题字=文档.createElement('span')
            题字.textContent=中文['bonusNoticeTitle']
            题行.appendChild(图标)
            题行.appendChild(题字)
            段=文档.createElement('p')
            段.textContent=通知.get('message') or ''
            文.appendChild(题行)
            文.appendChild(段)
            关=文档.createElement('button')
            关.type='button'
            关.className='close'
            关.setAttribute('data-dsh-css',样式模块)
            关.setAttribute('aria-label',中文['close'])
            关.appendChild(图标关闭描边常规({'window':窗口,'size':10}))
            def 点关(_事件=None):
                '关掉就算看过'
                回调=自身.属性.get('onDismiss')
                if 回调 is not None:
                    回调(通知.get('orderId'))
            关.addEventListener('click',点关)
            卡.appendChild(文)
            卡.appendChild(关)
            文档.body.appendChild(卡)
            自身.卡片=卡
        else:
            段=自身.卡片.querySelector('p')
            if 段 is not None:
                段.textContent=通知.get('message') or ''
        if 自身.位置 is None:
            自身.卡片.style.visibility='hidden'
        else:
            自身.卡片.style.left=str(自身.位置['left'])+'px'
            自身.卡片.style.bottom=str(自身.位置['bottom'])+'px'
            自身.卡片.style.visibility='visible'
        if 自身.位置 is not None and 自身.已报告 is not True:
            def 尝试():
                '可见并且过了一帧才上报'
                if 自身.已报告 or 文档.visibilityState=='hidden' or 仍可花(通知.get('expiresAt')) is not True:
                    return
                def 上报():
                    '这一帧已经画上'
                    if 自身.已报告 or 文档.visibilityState=='hidden' or 仍可花(通知.get('expiresAt')) is not True:
                        return
                    自身.已报告=True
                    回调=自身.属性.get('onShown')
                    if 回调 is not None:
                        回调(通知.get('orderId'))
                def 帧到():
                    '这一帧之后再上报'
                    窗口.setTimeout(上报,0)
                帧=窗口.requestAnimationFrame(帧到)
                def 取消():
                    '卸下前取消这一帧'
                    窗口.cancelAnimationFrame(帧)
                自身.拆除器.append(取消)
            尝试()
            文档.addEventListener('visibilitychange',尝试)
            def 拆可见():
                '卸下可见性监听'
                文档.removeEventListener('visibilitychange',尝试)
            自身.拆除器.append(拆可见)

    def 拆监听(自身):
        '清掉上一轮的尺寸和帧监听'
        for 拆 in 自身.拆除器:
            拆()
        自身.拆除器=[]

    def 拆除(自身):
        '从 body 拿掉卡片'
        自身.拆监听()
        if 自身.卡片 is not None and 自身.卡片.parentNode is not None:
            自身.卡片.remove()
        自身.卡片=None

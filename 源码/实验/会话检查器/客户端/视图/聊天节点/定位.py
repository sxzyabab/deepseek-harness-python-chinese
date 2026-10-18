'检查器自己滚动并闪一下目标，不走对话的请求通道'

from ......客户端.模块.客户端.通告 import 取握手窗口
import os#样式文件
from ......客户端.ui_对话.异常 import 注入模块样式文件,标样式模块#检查器样式
from .文档对象 import 已显示,查找聊天目标#候选和可见
from .高亮 import 放置聊天高亮,可见聊天矩形#闪框位置

样式模块='session-inspector'#与表格共用
安静毫秒=150#滚动停下来再闪
滚动键=set(['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' ','Escape'])#会打断平滑滚动的键

def 有盒子(元素):
    '可见而且宽高都大于零'
    if not 已显示(元素):#藏着
        return False#没有盒子
    盒=元素.getBoundingClientRect()#尺寸
    return 盒.width>0 and 盒.height>0#有面积

class 检查器聊天定位器:
    '一次延迟定位和页面上的闪框，不改对话节点'
    def __init__(自身,取根):
        '取根返回当前会话的主对话，没显示时是空'
        自身.取根=取根#主对话
        自身.帧=None#等待中的动画帧
        自身.覆盖=None#闪框
        自身.动画=None#闪动
        自身.取消滚动=None#打断平滑滚动

    def 确保样式(自身,文档):
        '闪框用检查器样式'
        注入模块样式文件(文档,'dsh-session-inspector',os.path.join(os.path.dirname(__file__),'..','检查器.module.css'),样式模块)#只插一次

    def 定位(自身,目标列表):
        '先找能用的出现，找不到就闪整列。减少动态时只滚动不闪'
        自身.拆除()#取消上一次
        窗口=取握手窗口()#页面
        def 到帧():
            '下一帧再量，避免刚展开还没有盒子'
            自身.帧=None#这一帧已到
            根=自身.取根()#当前列
            if 根 is None:#没显示
                return#结束
            for 最初 in 查找聊天目标(根,目标列表):#按偏好
                if not 根.contains(最初):#已经不在这列
                    continue#下一个
                隐藏=[]#hidden=until-found 的祖先
                元素=最初#从目标往上
                while 元素 is not None and 元素 is not 根:#还没到列
                    if 元素.getAttribute('hidden')=='until-found':#折着等匹配
                        隐藏.append(元素)#记下
                    元素=元素.parentElement#上一层
                if len(隐藏)>0 or 可见聊天矩形(最初) is None:#还藏着或不在视口
                    滚动口=根.closest('[data-conversation-scroll]')#对话滚动口
                    if 滚动口 is not None:#有滚动口
                        滚动口.dispatchEvent(窗口.Event('beforematch'))#先通知滚动口
                下标=len(隐藏)-1#从外向内
                while 下标>=0:#逐个展开
                    隐藏[下标].dispatchEvent(窗口.Event('beforematch'))#同步派发。没有 flushSync
                    下标=下标-1#下一个
                if 自身.取根() is not 根:#展开期间列换了
                    return#结束
                行=最初 if 根.contains(最初) else None#还在不在
                if 行 is None or not 有盒子(行):#没有盒子
                    for 候选 in 查找聊天目标(根,目标列表):#再找一个有盒子的
                        if 有盒子(候选):#有面积
                            行=候选#用它
                            break#停
                if 行 is None or not 有盒子(行):#仍然没有
                    continue#下一个最初目标
                if 可见聊天矩形(行) is None:#有盒子但不在视口
                    if not 窗口.matchMedia('(prefers-reduced-motion: reduce)').matches:#允许动画
                        自身.平滑滚动(行,根,目标列表)#滚完再闪
                        return#这次定位结束
                    行.scrollIntoView({'behavior':'instant','block':'center','inline':'nearest'})#立刻滚到中间
                自身.排队闪(行,根,目标列表)#下一帧闪
                return#结束
            if 已显示(根) and 可见聊天矩形(根) is not None:#整列还看得到
                自身.排队闪(根,根,目标列表)#闪整列
        自身.帧=窗口.requestAnimationFrame(到帧)#下一帧

    def 拆除(自身):
        '取消还没完成的滚动，并拿掉闪框'
        窗口=取握手窗口()#页面
        if 自身.帧 is not None:#还有帧
            窗口.cancelAnimationFrame(自身.帧)#取消
        自身.帧=None#清空
        if 自身.取消滚动 is not None:#平滑滚动还在
            自身.取消滚动()#停掉观察
        if 自身.动画 is not None:#闪动还在
            自身.动画.onfinish=None#不再收尾
            自身.动画.cancel()#停
        自身.动画=None#清空
        if 自身.覆盖 is not None:#有闪框
            自身.覆盖.remove()#拿掉
        自身.覆盖=None#清空

    def 排队闪(自身,行,根,目标列表):
        '再等一帧。这一行闪不上就试邻居，最后试整列'
        窗口=取握手窗口()#页面
        def 到帧():
            '列换了就全部取消'
            自身.帧=None#帧已到
            if 自身.取根() is not 根:#不是这一列了
                自身.拆除()#取消
                return#结束
            if 自身.闪(行):#这一行闪上了
                return#结束
            for 候选 in 查找聊天目标(根,目标列表):#邻居
                if 候选 is not 行 and 自身.闪(候选):#闪上了
                    return#结束
            if 行 is not 根 and 自身.闪(根):#整列
                return#结束
            自身.拆除()#都闪不上
        自身.帧=窗口.requestAnimationFrame(到帧)#下一帧

    def 平滑滚动(自身,行,根,目标列表):
        '等滚动停稳再闪。滚轮、触摸、按下或滚动键会立刻停住'
        窗口=取握手窗口()#页面
        父集=set()#目标的祖先
        元素=行.parentElement#从父开始
        while 元素 is not None:#全部祖先
            父集.add(元素)#记下
            元素=元素.parentElement#上一层
        在动=set()#还在滚动的祖先
        进行={'值':True}#这次观察还有效
        安静={'句柄':None}#安静计时
        停帧={'值':None}#scrollend 后再等一帧

        def 事件目标(事件):
            '文档滚动算到滚动元素上，并且必须是目标的祖先'
            目标=窗口.document.scrollingElement if 事件.target is 窗口.document else 事件.target#滚动目标
            if 目标 is not None and 目标 in 父集:#是祖先
                return 目标#这个元素
            return None#无关滚动

        def 清理():
            '卸掉这次滚动观察'
            进行['值']=False#结束
            if 安静['句柄'] is not None:#有计时
                窗口.clearTimeout(安静['句柄'])#清
            if 停帧['值'] is not None:#有帧
                窗口.cancelAnimationFrame(停帧['值'])#取消
            窗口.removeEventListener('scroll',滚动时,True)#滚动
            窗口.removeEventListener('scrollend',滚动结束,True)#结束
            for 类型 in ('wheel','touchstart','pointerdown','keydown'):#打断
                窗口.removeEventListener(类型,打断,True)#卸掉
            自身.取消滚动=None#不再取消

        def 完成():
            '滚动停了就去闪'
            if not 进行['值']:#已经结束
                return#不重复
            清理()#卸观察
            自身.排队闪(行,根,目标列表)#闪

        def 等安静():
            '没有 scrollend 时，安静一会儿也算停'
            if 安静['句柄'] is not None:#旧计时
                窗口.clearTimeout(安静['句柄'])#换一个
            安静['句柄']=窗口.setTimeout(完成,安静毫秒)#150 毫秒

        def 滚动时(事件):
            '祖先在滚就重新等安静'
            目标=事件目标(事件)#是不是祖先
            if 目标 is None:#无关
                return#不管
            在动.add(目标)#还在动
            等安静()#重新计时

        def 滚动结束(事件):
            '全部在动的祖先都结束，再等一帧确认'
            目标=事件目标(事件)#是不是祖先
            if 目标 is None or 目标 not in 在动:#没在记
                return#不管
            在动.discard(目标)#这个停了
            if len(在动)>0 or 停帧['值'] is not None:#还有别的或已经在等帧
                return#再等
            def 确认():
                '这一帧里没有新的滚动就完成'
                停帧['值']=None#帧到了
                if len(在动)==0:#真的停了
                    完成()#去闪
            停帧['值']=窗口.requestAnimationFrame(确认)#再等一帧

        def 停住():
            '把还在惯性滚动的祖先定在当前位置'
            if not 进行['值']:#已经结束
                return#不用
            清理()#卸观察
            for 祖先 in 父集:#每个祖先
                if 祖先.isConnected and (祖先.scrollHeight>祖先.clientHeight or 祖先.scrollWidth>祖先.clientWidth):#还能滚
                    祖先.scrollTo({'top':祖先.scrollTop,'left':祖先.scrollLeft,'behavior':'instant'})#停在这里

        def 打断(事件):
            '用户自己滚动就取消这次定位'
            if 事件.type=='keydown' and 事件.key not in 滚动键:#不是滚动键
                return#不管
            停住()#定住
            自身.拆除()#连闪框一起取消

        自身.取消滚动=停住#拆除时调用
        窗口.addEventListener('scroll',滚动时,{'capture':True,'passive':True})#滚动
        窗口.addEventListener('scrollend',滚动结束,{'capture':True,'passive':True})#结束
        for 类型 in ('wheel','touchstart','pointerdown','keydown'):#用户打断
            窗口.addEventListener(类型,打断,{'capture':True,'passive':True})#捕获
        等安静()#没有滚动事件也要能结束
        行.scrollIntoView({'behavior':'smooth','block':'center','inline':'nearest'})#平滑滚到中间

    def 闪(自身,行):
        '减少动态时不画闪框。放不上就换下一个候选'
        窗口=取握手窗口()#页面
        if 窗口.matchMedia('(prefers-reduced-motion: reduce)').matches:#不要动画
            自身.拆除()#收掉
            return True#算完成
        if not 已显示(行):#不可见
            return False#换下一个
        自身.确保样式(窗口.document)#样式
        覆盖=窗口.document.createElement('div')#闪框
        if not 放置聊天高亮(覆盖,行):#不在视口
            return False#换下一个
        覆盖.className='chatReveal'#闪框类名
        标样式模块(覆盖,样式模块)#模块
        覆盖.setAttribute('data-session-inspector-highlight','reveal')#定位闪框
        覆盖.setAttribute('aria-hidden','true')#不进无障碍树
        窗口.document.body.append(覆盖)#挂上
        自身.覆盖=覆盖#记住
        动画=覆盖.animate([{'opacity':0.65},{'opacity':0.1},{'opacity':0.5},{'opacity':0}],{'duration':700})#闪一下
        自身.动画=动画#记住
        def 结束():
            '只收自己这一次'
            if 自身.动画 is 动画:#还是这一次
                自身.拆除()#拿掉
        动画.onfinish=结束#播完
        return True#已经闪上

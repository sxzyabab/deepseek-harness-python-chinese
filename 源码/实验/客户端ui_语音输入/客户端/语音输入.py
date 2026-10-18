'点按录音。识别文字仍写回原来的会话草稿'
from ....客户端.模块.客户端.通告 import 取握手窗口
import os#样式文件位置
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块#模块样式
from ....客户端.ui_基础界面组件.按钮 import 按钮#麦克风、停止、取消
from ....客户端.ui_基础界面组件.提示泡 import 提示泡#听写
from ....客户端.ui_基础界面组件.状态点 import 状态点#进行中
from ....客户端.ui_基础界面组件.icons import 图标关闭描边常规,图标停止填充常规#关闭和停止
from .音频 import 逐项,音频base64#设备列表和 base64
from .故障文本 import 失败文本#失败句子
from .波形图 import 波形图#录音振幅
from .语音输入安装对话框 import 语音输入安装对话框#还不能录时的引导

__all__=['语音输入','拆录音','麦克风图标']#输入栏活动

样式路径=os.path.join(os.path.dirname(__file__),'语音输入.module.css')#本目录样式
样式模块='VoiceInput'#与样式表对应的模块名
可用阶段=('ready','standby','waking')#可以开始录音的阶段


def 取(对象,键,默认=None):
    '字典用键，对象用同名属性'
    if 对象 is None:#没有
        return 默认#缺省
    if isinstance(对象,dict):#字典
        return 对象[键] if 键 in 对象 else 默认#键
    return getattr(对象,键,默认)#属性


def 全选(值):
    '选择整份快照'
    return 值#原样


def 取窗口(属性):
    '调用方窗口优先，否则用当前页'
    if isinstance(属性,dict) and 属性.get('window') is not None:#份额里带了窗口
        return 属性['window']#调用方窗口
    return 取握手窗口()#当前页


def 设类(节点,*类名):
    '挂上官方类名，让模块样式生效'
    留下=[]#非空类名
    for 名 in 类名:#逐个
        if isinstance(名,str) and 名!='':#有内容
            留下.append(名)#留下
    节点.className=' '.join(留下)#类名保持原文
    return 标样式模块(节点,样式模块)#模块属性


def 拆录音(采集):
    '关闭失败不得盖住识别结果'
    try:#停轨并关闭音频上下文
        采集.拆除()#释放
    except Exception as 关闭错误:#AudioContext 关闭失败
        关闭错误=None#不掩盖录音结果


def 麦克风图标(窗口,边长):
    '按上游麦克风路径画出常规描边。共享图标集里没有这一只'
    文档=窗口.document#文档
    描边宽=1#常规描边
    图=文档.createElement('svg')#图标
    图.setAttribute('width',str(边长))#宽
    图.setAttribute('height',str(边长))#高
    图.setAttribute('viewBox','0 0 16 16')#坐标
    图.setAttribute('fill','none')#不填充底
    图.setAttribute('stroke','currentColor')#跟文字颜色
    图.setAttribute('stroke-width',str(描边宽))#线宽
    图.setAttribute('aria-hidden','true')#按钮自己有名字
    框=文档.createElement('rect')#麦克风头
    框.setAttribute('x',str(4.5+描边宽/2))#左边
    框.setAttribute('y',str(1+描边宽/2))#上边
    框.setAttribute('width',str(7-描边宽))#宽
    框.setAttribute('height',str(10-描边宽))#高
    框.setAttribute('rx',str((7-描边宽)/2))#圆角
    图.appendChild(框)#挂上
    路=文档.createElement('path')#支架
    路.setAttribute('d','M2.35 8.675C3.075 11.3 5.2 13.125 8 13.125C10.8 13.125 12.925 11.3 13.65 8.675M8 13.125V15')#路径
    图.appendChild(路)#挂上
    return 图#节点


class 语音输入:
    '折叠时是一枚麦克风。展开后是采集、识别或重试'
    def __init__(自身,属性=None):
        '记下输入栏份额，并订上就绪'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.窗口=取窗口(自身.属性)#当前页
        自身.根=None#最外层
        自身.阶段='idle'#idle、requesting、recording、transcribing、feedback
        自身.消息=''#失败或冲突说明
        自身.待插入=''#草稿冲突后留下的文字
        自身.引导开=False#还不能录时的模态
        自身.当前=None#正在进行的采集
        自身.代=0#取消后作废旧结果
        自身.会话标识=None#用来发现换了会话
        自身.已同步=False#第一次才装监听
        自身.已挂会话=False#blur、可见性和 Escape
        自身.上次展开=None#上次告诉输入栏的展开态
        自身.上次回调=None#onActiveChange 换了要再通知
        自身.已通知活动=False#卸下时补一次 false
        自身.绘制中=False#避免重入
        自身.待重画=False#绘制中又来了一次
        自身.退订=[]#就绪订阅
        自身.对话框=语音输入安装对话框({'window':自身.窗口,'open':False})#引导
        自身.波形=波形图({'window':自身.窗口,'recording':None,'label':'正在录音…'})#振幅
        钩=自身.属性.get('useSpeechReadiness')#就绪钩子
        if callable(钩) and hasattr(钩,'_subscribe'):#能订
            自身.退订.append(钩._subscribe(自身.源变了))#目录变了就重画
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的输入栏份额'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新
        自身.窗口=取窗口(自身.属性)#窗口可能换了

    def 源变了(自身):
        '就绪变了就重画。可用时关掉引导'
        if 自身.绘制中:#正在画
            自身.待重画=True#等这一轮结束
            return#不重入
        自身.渲染()#重画

    def 读就绪(自身):
        '读共享就绪快照'
        钩=自身.属性.get('useSpeechReadiness')#钩子
        if callable(钩) is False:#没有
            return {'catalog':None,'connected':False,'error':None}#空
        就绪=钩(全选)#整份
        if isinstance(就绪,dict) is False:#不是字典
            return {'catalog':None,'connected':False,'error':None}#空
        return 就绪#快照

    def 找提供方(自身,目录):
        '按当前选择找出提供方'
        if isinstance(目录,dict) is False:#没有目录
            return None#没有
        标识=取(目录.get('selection'),'providerId')#选中的 id
        for 项 in 逐项(目录.get('providers')):#逐个
            if 取(项,'id')==标识:#就是这一个
                return 项#找到
        return None#没有

    def 可用(自身,就绪):
        '已连接，且所选提供方处于可录阶段'
        if isinstance(就绪,dict) is False or 就绪.get('connected') is not True:#没连上
            return False#不能录
        阶段=取(取(自身.找提供方(就绪.get('catalog')),'preparation'),'phase')#准备阶段
        return 阶段 in 可用阶段#ready、standby、waking

    def 反馈(自身,文本):
        '在工具栏里显示一句说明'
        自身.消息=文本#说明
        自身.阶段='feedback'#反馈行
        自身.渲染()#重画

    def 卸监听(自身,作废):
        '摘掉窗口监听。作废时停掉还在进行的采集'
        if 自身.已挂会话:#还挂着
            自身.窗口.removeEventListener('blur',自身.窗口失焦)#失焦
            自身.窗口.document.removeEventListener('visibilitychange',自身.可见变化)#隐藏
            自身.窗口.document.removeEventListener('keydown',自身.按下逃逸)#Escape
            自身.已挂会话=False#记下
        if 作废 is False:#只摘监听
            return#不碰采集
        自身.代=自身.代+1#旧结果作废
        活动=自身.当前#正在进行的
        自身.当前=None#先摘掉
        if 活动 is None:#没有
            return#完
        if 活动.get('计时') is not None:#到时停止还挂着
            自身.窗口.clearTimeout(活动['计时'])#取消
        中止=活动.get('abort')#识别取消
        if 中止 is not None:#有控制器
            中止.abort()#取消识别
        拆录音(活动['capture'])#放掉麦克风

    def 装监听(自身):
        '失焦、页面隐藏和 Escape 都会取消还在录的一段'
        自身.窗口.addEventListener('blur',自身.窗口失焦)#窗口失焦
        自身.窗口.document.addEventListener('visibilitychange',自身.可见变化)#页面隐藏
        自身.窗口.document.addEventListener('keydown',自身.按下逃逸)#Escape
        自身.已挂会话=True#记下

    def 同步会话(自身):
        '换了会话就作废采集，并重新挂监听'
        会话=自身.属性.get('sessionId')#当前会话
        if 自身.已同步 and 自身.会话标识==会话:#还是这一次
            return#不用重置
        if 自身.已同步:#换了会话
            自身.卸监听(True)#先停掉上一次
        自身.会话标识=会话#记下
        自身.待插入=''#清掉待插入
        自身.消息=''#清掉说明
        自身.阶段='idle'#收回麦克风
        自身.引导开=False#关掉引导
        自身.装监听()#重新听
        自身.已同步=True#已经同步过

    def 窗口失焦(自身,事件=None):
        '正在录音时窗口失焦就取消'
        if 自身.当前 is not None and 自身.当前.get('phase')=='recording':#只取消录音
            自身.取消()#取消

    def 可见变化(自身,事件=None):
        '页面隐藏时，除了正在识别，都取消'
        if 自身.窗口.document.hidden and 自身.当前 is not None and 自身.当前.get('phase')!='transcribing':#隐藏
            自身.取消()#取消

    def 按下逃逸(自身,事件):
        '有进行中的采集时，Escape 取消并阻止默认'
        if 取(事件,'key')=='Escape' and 自身.当前 is not None:#正在进行
            if hasattr(事件,'preventDefault'):#事件能取消默认
                事件.preventDefault()#不要关掉别的层
            自身.取消()#取消

    def 按下麦克风(自身,事件):
        '按下时不要抢走草稿里的光标'
        if hasattr(事件,'preventDefault'):#事件能取消默认
            事件.preventDefault()#保持草稿焦点

    def 取消(自身):
        '作废这一轮，收回麦克风'
        自身.卸监听(True)#停采集并摘监听
        自身.装监听()#监听还要留着
        自身.待插入=''#清掉
        自身.消息=''#清掉
        自身.阶段='idle'#收回
        自身.引导开=False#关掉引导
        自身.渲染()#重画

    def 采集出错(自身,失败,轮次,活动):
        '录音中途失败。已经在识别或换了轮次就忽略'
        if 轮次!=自身.代 or 自身.当前 is not 活动 or 活动.get('phase')=='transcribing':#过期
            return#忽略
        自身.当前=None#摘掉
        if 活动.get('计时') is not None:#到时还挂着
            自身.窗口.clearTimeout(活动['计时'])#取消
        中止=活动.get('abort')#识别取消
        if 中止 is not None:#有控制器
            中止.abort()#取消
        自身.反馈(失败文本(失败))#显示中文

    def 结束(自身):
        '停止录音并识别。轮次变了就丢掉结果'
        活动=自身.当前#正在进行的
        if 活动 is None or 活动.get('phase')!='recording':#不是录音中
            return#不用停
        活动['phase']='transcribing'#进入识别
        轮次=自身.代#这一轮
        if 活动.get('计时') is not None:#到时停止
            自身.窗口.clearTimeout(活动['计时'])#取消重复进入
            活动['计时']=None#记下
        自身.阶段='transcribing'#界面
        自身.渲染()#重画
        try:#停、检查大小、识别、插入
            音频=活动['capture'].停止(活动['maxDurationSeconds'])#WAV
            if 轮次!=自身.代:#已经取消
                return#丢掉
            if len(音频)>活动['maxAudioBytes']:#超过上限
                自身.反馈('录音超过服务限制，请缩短录音后重试。')#中文表
                return#不送
            选择=活动['selection']#当时的提供方和语言
            if isinstance(选择,dict):#字典
                请求=dict(选择)#拷贝
            else:#对象
                请求={'providerId':取(选择,'providerId'),'language':取(选择,'language')}#两个字段
            请求['audioBase64']=音频base64(音频)#规范 base64
            结果=自身.属性['transcribe'](请求,活动['abort'].signal)#识别
            if 轮次!=自身.代:#识别期间取消了
                return#丢掉
            if isinstance(结果,dict) and 结果.get('ok') is False:#Remote 失败
                错误=结果.get('error')#错误对象
                if isinstance(错误,dict):#字典
                    消息=str(错误.get('message') or '')#消息
                elif 错误 is None:#没有
                    消息=''#空
                else:#异常或对象
                    消息=str(取(错误,'message',错误))#消息
                自身.反馈('语音识别失败：{message}'.replace('{message}',消息))#中文表
                return#不插入
            值=结果.get('value') if isinstance(结果,dict) else None#识别结果
            文字=取(值,'text','')#文字
            if 文字 is None:#没有
                文字=''#空
            if 文字=='':#没识别到
                自身.反馈('未识别到语音')#中文表
                return#不插入
            动作=自身.属性.get('inputActions')#草稿动作
            插入=取(动作,'insertText')#插入函数
            插上=False#默认没插上
            if callable(插入):#有插入
                插上=插入(文字,活动['span']) is True#按录音开始时的位置
            if 插上 is False:#草稿已经变了
                自身.待插入=文字#留下
                自身.反馈('草稿已被修改。识别文字已保留，可在当前光标位置插入。')#中文表
                return#等用户点插入
            自身.阶段='idle'#收回麦克风
            自身.渲染()#重画
        except Exception as 失败:#停或识别失败
            拆录音(活动['capture'])#确保设备已放
            if 轮次==自身.代:#还是这一轮
                自身.反馈(失败文本(失败))#中文
        finally:#这一轮结束就摘掉当前采集
            if 轮次==自身.代:#没有被更新的轮次取代
                自身.当前=None#摘掉

    def 开始(自身):
        '取得麦克风并开始采集。到时自动停止'
        就绪=自身.读就绪()#当前目录
        目录=就绪.get('catalog') if isinstance(就绪,dict) else None#目录
        if 目录 is None or 自身.可用(就绪) is False or 自身.属性.get('locked') is True or 自身.当前 is not None:#不能开始
            return#离开
        自身.代=自身.代+1#新的一轮
        轮次=自身.代#闭包里用
        动作=自身.属性.get('inputActions')#草稿动作
        捕获=取(动作,'captureInsertion')#记下插入位置
        跨度=捕获() if callable(捕获) else None#开始时的位置
        活动={#这一轮
            'capture':自身.属性['createRecording'](),#插件寿命拥有
            'abort':自身.窗口.AbortController(),#取消识别
            'span':跨度,#插入位置
            'selection':取(目录,'selection'),#当时的选择
            'maxDurationSeconds':取(目录,'maxDurationSeconds'),#最长秒
            'maxAudioBytes':取(目录,'maxAudioBytes'),#最大字节
            'phase':'requesting',#正在要权限
            '计时':None,#到时停止
        }
        自身.当前=活动#记下
        自身.消息=''#清掉旧说明
        自身.待插入=''#清掉旧文字
        自身.阶段='requesting'#界面
        自身.渲染()#重画

        def 出错(失败):
            '采集中途失败'
            自身.采集出错(失败,轮次,活动)#按轮次判断

        try:#打开麦克风
            活动['capture'].开始(出错)#开始录
            if 轮次!=自身.代 or 自身.当前 is not 活动:#已经取消
                return#丢掉
            活动['phase']='recording'#正在录
            自身.阶段='recording'#界面
            自身.渲染()#重画

            def 到时():
                '到达最长时长就停止并识别'
                自身.结束()#停止

            活动['计时']=自身.窗口.setTimeout(到时,活动['maxDurationSeconds']*1000)#到时
        except Exception as 失败:#没打开
            拆录音(活动['capture'])#放掉
            if 轮次==自身.代:#还是这一轮
                自身.当前=None#摘掉
                自身.反馈(失败文本(失败))#中文

    def 点触发(自身):
        '能录就开始，否则打开引导'
        if 自身.可用(自身.读就绪()):#可以录
            自身.开始()#开始
            return#完
        自身.引导开=True#打开引导
        自身.渲染()#重画

    def 插入待定(自身):
        '草稿冲突后，按现在的光标插入留下的文字'
        动作=自身.属性.get('inputActions')#草稿动作
        插入=取(动作,'insertText')#插入函数
        捕获=取(动作,'captureInsertion')#当前位置
        跨度=捕获() if callable(捕获) else None#现在的位置
        if callable(插入) and 插入(自身.待插入,跨度) is True:#插上了
            自身.待插入=''#清掉
            自身.阶段='idle'#收回
            自身.渲染()#重画

    def 关引导(自身):
        '关掉安装或不可用模态'
        自身.引导开=False#关
        自身.渲染()#重画

    def 开详情(自身):
        '关掉模态并打开语音组合包详情'
        自身.引导开=False#关
        打开=自身.属性.get('openSettings')#打开详情
        if callable(打开):#有回调
            打开()#不启动准备
        自身.渲染()#重画

    def 通知展开(自身,展开):
        '展开态变了就告诉输入栏'
        回调=自身.属性.get('onActiveChange')#输入栏回调
        if 自身.上次展开 is 展开 and 自身.上次回调 is 回调:#没变
            return#不用再叫
        自身.上次展开=展开#记下
        自身.上次回调=回调#记下
        自身.已通知活动=True#卸下时要补 false
        if callable(回调):#有回调
            回调(展开)#通知

    def 换根(自身,根):
        '换成新的最外层，并挂回原来的父节点'
        旧=自身.根#上一份
        父=None#挂载点
        if 旧 is not None and 旧 is not 根:#不是同一个
            父=旧.parentNode#记住位置
            旧.remove()#拆掉
        自身.根=根#留下
        if 父 is None:#还没挂过
            父=自身.属性.get('parent')#宿主指定的父节点
        if 父 is not None and 根 is not None and 根.parentNode is not 父:#需要挂上
            父.appendChild(根)#挂上
        return 根#节点

    def 画按钮(自身,类名,点击,标签,图标):
        '画出一枚按钮，补上原子按钮没写的无障碍名，再放上图标'
        节点=按钮({#真实 button
            'window':自身.窗口,#窗口
            'className':类名,#模块类名
            'size':'sm',#小
            'onClick':点击,#点击
        }).渲染()#节点
        if 标签!='':#有名字
            节点.setAttribute('aria-label',标签)#读屏
        if 图标 is not None:#有图标
            节点.appendChild(图标)#放进按钮
        return 节点#节点

    def 画出折叠(自身,就绪):
        '一枚麦克风。不能录时点击打开引导'
        文档=自身.窗口.document#文档
        可用=自身.可用(就绪)#现在能不能录
        锚=文档.createElement('span')#提示泡的锚
        设类(锚,'triggerAnchor')#不参与伸展
        钮=按钮({#麦克风
            'window':自身.窗口,#窗口
            'className':'trigger',#28 宽
            'size':'sm',#小
            'disabled':自身.属性.get('locked') is True,#锁定时不能点
            'onClick':自身.点触发,#开始或打开引导
        }).渲染()#按钮
        钮.setAttribute('aria-label','开始录音' if 可用 else '打开语音输入引导')#中文表
        if 可用 is False:#要打开对话框
            钮.setAttribute('aria-haspopup','dialog')#有对话框
        钮.addEventListener('mousedown',自身.按下麦克风)#不要抢走焦点
        钮.appendChild(麦克风图标(自身.窗口,18))#麦克风
        锚.appendChild(钮)#放进锚
        提示泡({#听写
            'window':自身.窗口,#窗口
            'label':'听写',#中文表
            'disabled':可用 is False,#不能录时不显示
            'side':'top',#上方
            'portal':True,#传到顶层
            'children':锚,#锚是这一枚按钮的外层
        }).渲染()#挂上悬停
        提供方=自身.找提供方(就绪.get('catalog') if isinstance(就绪,dict) else None)#所选
        要安装=就绪.get('connected') is True and 取(提供方,'location')=='host-local' and 取(取(提供方,'preparation'),'phase')=='unprepared'#本地且未准备
        自身.对话框.更新({#引导
            'window':自身.窗口,#窗口
            'open':自身.引导开 and 可用 is False,#不能录才开
            'needsInstallation':要安装,#安装或尚未就绪
            'onDismiss':自身.关引导,#稍后
            'onOpenDetails':自身.开详情,#前往详情
        })
        壳=文档.createElement('span')#不占布局，让按钮和模态都留在槽里
        壳.style.display='contents'#子节点直接参与父布局
        壳.appendChild(锚)#麦克风
        模态=自身.对话框.渲染()#模态或空
        if 模态 is not None:#打开了
            壳.appendChild(模态)#一起挂上
        return 壳#最外层

    def 画出展开(自身,就绪):
        '采集、识别或重试这一行'
        文档=自身.窗口.document#文档
        行=文档.createElement('div')#整行
        设类(行,'captureRow')#横向
        行.setAttribute('data-voice-activity',自身.阶段)#当前阶段，保持英文
        关闭名='丢弃识别文字' if 自身.待插入!='' else '取消'#中文表
        行.appendChild(自身.画按钮('roundButton',自身.取消,关闭名,图标关闭描边常规({'window':自身.窗口,'size':14})))#关闭
        if 自身.阶段=='recording':#正在录
            自身.波形.更新({'window':自身.窗口,'recording':None if 自身.当前 is None else 自身.当前.get('capture'),'label':'正在录音…'})#中文表
            行.appendChild(自身.波形.渲染())#振幅
        else:#权限、识别或反馈
            文=文档.createElement('span')#状态句
            设类(文,'activityMessage')#省略号
            文.setAttribute('role','status')#读屏
            标题=自身.待插入 if 自身.待插入!='' else 自身.消息#悬停看全文
            文.setAttribute('title',标题)#全文
            if 自身.阶段=='requesting' or 自身.阶段=='transcribing':#还在进行
                点=状态点({'window':自身.窗口,'state':'ongoing','size':16}).渲染()#转圈
                if 点 is not None:#画出来了
                    文.appendChild(点)#放在文字前
            if 自身.阶段=='feedback':#显示说明
                句子=自身.消息#失败或冲突
            elif 自身.阶段=='requesting':#要权限
                句子='请允许使用麦克风…'#中文表
            else:#识别
                提供方=自身.找提供方(就绪.get('catalog') if isinstance(就绪,dict) else None)#所选
                if 取(取(提供方,'preparation'),'phase')=='waking':#正在唤醒
                    句子='唤醒中…'#中文表
                else:#普通识别
                    句子='识别中…'#中文表
            字=文档.createElement('span')#文字
            字.textContent=句子#句子
            文.appendChild(字)#挂上
            行.appendChild(文)#状态
        if 自身.阶段=='recording':#可以手动停
            行.appendChild(自身.画按钮('roundButton',自身.结束,'停止并识别',图标停止填充常规({'window':自身.窗口,'size':14})))#停止
        if 自身.阶段=='feedback':#重试或插入
            if 自身.待插入!='':#有留下的文字
                插入钮=按钮({#插入
                    'window':自身.窗口,#窗口
                    'className':'inlineAction',#不伸展
                    'size':'sm',#小
                    'children':'插入文字',#中文表
                    'onClick':自身.插入待定,#按现在的光标插入
                }).渲染()#按钮
                行.appendChild(插入钮)#挂上
            else:#再录一次
                重试=自身.画按钮('roundButton',自身.点触发,'重新录音',麦克风图标(自身.窗口,18))#麦克风
                if 自身.可用(就绪) is False or 自身.属性.get('locked') is True:#不能录
                    重试.disabled=True#禁用
                行.appendChild(重试)#挂上
        return 行#最外层

    def 画出(自身):
        '按阶段画出折叠麦克风或展开行'
        自身.同步会话()#换会话就重置
        就绪=自身.读就绪()#目录
        if 自身.可用(就绪):#已经能录
            自身.引导开=False#关掉引导
        文档=自身.窗口.document#文档
        注入模块样式文件(文档,'语音输入样式',样式路径,样式模块)#样式只插一次
        展开=自身.阶段!='idle'#展开行
        自身.通知展开(展开)#告诉输入栏
        if 展开 is False:#折叠
            return 自身.换根(自身.画出折叠(就绪))#麦克风
        return 自身.换根(自身.画出展开(就绪))#采集行

    def 渲染(自身):
        '重入时记一笔，这一轮结束再画'
        if 自身.绘制中:#正在画
            自身.待重画=True#等结束
            return 自身.根#先交出现在的
        自身.绘制中=True#占住
        try:#画出
            return 自身.画出()#节点
        finally:#放开，并补上错过的一次
            自身.绘制中=False#结束
            if 自身.待重画:#绘制中又来了
                自身.待重画=False#清掉
                自身.渲染()#再画

    def 拆除(自身):
        '卸下后取消采集，并告诉输入栏已经收起'
        for 退 in 自身.退订:#逐个订阅
            if callable(退):#是函数
                退()#退订
        自身.退订=[]#清空
        自身.卸监听(True)#停采集
        自身.波形.拆除()#停动画
        自身.对话框.拆除()#关模态
        if 自身.已通知活动:#告诉过输入栏
            回调=自身.属性.get('onActiveChange')#回调
            if callable(回调):#有
                回调(False)#收起
        自身.已通知活动=False#记下

    def __call__(自身,属性=None):
        '宿主再次绘制时重画'
        if 属性 is not None:#有新份额
            自身.更新(属性)#换上
        return 自身.渲染()#重画

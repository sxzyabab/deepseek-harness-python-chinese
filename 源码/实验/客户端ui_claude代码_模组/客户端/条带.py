'提示上方的模组条带：当前绘制，按钮点击发回宿主'
from ....客户端.模块.客户端.通告 import 取握手窗口
import os#样式文件路径

__all__=['条带','节点']

连接路径=os.path.join#拼样式路径
目录名=os.path.dirname#本文件所在目录
样式标识='dsh-client-ui-claude-code-mods-band'#样式只插一次
颜色表={'yellow','red','green','cyan','blue','magenta','gray','grey','white','black'}#终端色名


def 取色(值):
    '终端色名。grey 收成 gray。不是色名则不写'
    if not isinstance(值,str) or 值 not in 颜色表:#不是这套色名
        return None#不写 data-color
    if 值=='grey':#英式拼写收成样式里的 gray
        return 'gray'
    return 值#原色名


def 旗标(值):
    '只有真才留下，假和缺席都不写属性'
    if 值 is True:#只认布尔真
        return True
    return None#不写


def 单位(值):
    '数字按 4 像素一档。布尔不算数字'
    if isinstance(值,bool) or not isinstance(值,(int,float)):#不是数字
        return None#不写这项间距
    return f'{值*4}px'#一档 4 像素


def 原样(值):
    '选择整份画面'
    return 值#不切片


def 热键文案(热键):
    '热键只作提示，写成方括号'
    return f'[{热键}]'


def 写数据(元素,表):
    '有值才写到元素上。真写成 true'
    for 键,值 in 表.items():#逐个数据属性
        if 值 is None:#缺席不写，避免留下空属性
            continue
        if 值 is True:#布尔真
            元素.setAttribute(键,'true')#属性值 true
        else:#色名等字符串
            元素.setAttribute(键,str(值))


class 节点:
    '序列化树的一个节点：字符串、Text、Button 或 Box'
    def __init__(自身,属性):
        '记下节点并画出'
        自身.属性=属性#node、pending、onPress、hotkeyLabel、文档
        自身.根=None#画出的页面节点
        自身.渲染()

    def 渲染(自身):
        '按类型画出这个节点'
        文档=自身.属性['文档']#页面文档
        节点值=自身.属性['node']#字符串或元素
        if isinstance(节点值,str):#纯文本
            自身.根=文档.createTextNode(节点值)#不包元素
            return 自身.根
        ################################
        #子节点。按钮不把子节点画出来
        ################################
        种类=节点值['type']#Text、Button，其余当 Box
        道具=节点值['props']#元素属性
        子节点表=[]#Text 和 Box 才挂上
        if 种类!='Button':#按钮只画 label 和热键
            for 子 in 节点值['children']:#上游顺序
                子节点表.append(节点({
                    'node':子,#子节点
                    'pending':自身.属性['pending'],#整棵树共用进行中
                    'onPress':自身.属性['onPress'],#按下回调
                    'hotkeyLabel':自身.属性['hotkeyLabel'],#热键文案
                    '文档':文档,#同一份文档
                }))
        if 种类=='Text':#一段文字
            跨=文档.createElement('span')#文字
            跨.className='text'#样式类名保持原文
            写数据(跨,{
                'data-color':取色(道具.get('color')),#终端色
                'data-bold':旗标(道具.get('bold')),#加粗
                'data-dim':旗标(道具.get('dimColor')),#变淡
                'data-italic':旗标(道具.get('italic')),#斜体
                'data-underline':旗标(道具.get('underline')),#下划线
            })
            for 子节点 in 子节点表:#按顺序挂上
                跨.appendChild(子节点.根)
            自身.根=跨
            return 自身.根
        if 种类=='Button':#按钮。没有动作号就只画、不能按
            标签=str(道具['label'])#按钮文字
            热键=道具.get('hotkey')#可能没有
            if not isinstance(热键,str):#只有字符串才显示
                热键=None
            if 'actionId' in 节点值 and 节点值['actionId'] is not None:#有动作号
                动作号=节点值['actionId']
            else:#缺席或 null 当成空
                动作号=''
            进行中=自身.属性['pending']#当前正在按的动作
            禁用=道具.get('disabled') is True or 动作号=='' or 进行中 is not None#任一成立就禁用全部
            钮=文档.createElement('button')#按钮
            钮.className='button'#样式类名保持原文
            钮.setAttribute('type','button')#不要提交
            钮.disabled=禁用#禁用时浏览器不发点击
            if 进行中==动作号:#正在按的这一个
                钮.setAttribute('aria-busy','true')
            else:
                钮.setAttribute('aria-busy','false')
            钮.appendChild(文档.createTextNode(标签))#标签在前
            if 热键 is not None:#热键提示
                热键跨=文档.createElement('span')
                热键跨.className='hotkey'#样式类名保持原文
                热键跨.appendChild(文档.createTextNode(自身.属性['hotkeyLabel'](热键)))
                钮.appendChild(热键跨)
            def 点击(事件=None):
                '点击把动作号交回宿主'
                自身.属性['onPress'](动作号)#用画出时的动作号
            钮.addEventListener('click',点击)#禁用的按钮不会进来
            自身.根=钮
            return 自身.根
        ################################
        #Box：方向、边框、间距
        ################################
        样式={}#只写算出来的间距
        if 'paddingX' in 道具 and 道具['paddingX'] is not None:#优先水平内边距
            水平值=道具['paddingX']
        else:#退回 padding
            水平值=道具.get('padding')
        if 'paddingY' in 道具 and 道具['paddingY'] is not None:#优先垂直内边距
            垂直值=道具['paddingY']
        else:
            垂直值=道具.get('padding')
        水平=单位(水平值)#左右
        垂直=单位(垂直值)#上下
        if 水平 is not None:#左右一起写
            样式['paddingLeft']=水平
            样式['paddingRight']=水平
        if 垂直 is not None:#上下一起写
            样式['paddingTop']=垂直
            样式['paddingBottom']=垂直
        间距=单位(道具.get('gap'))#子项间距
        if 间距 is not None:
            样式['gap']=间距
        有边框='border' in 道具 and 道具['border'] is not False#缺席或 false 没有边框
        盒=文档.createElement('div')#盒子
        盒.className='box'#样式类名保持原文
        写数据(盒,{
            'data-direction':'row' if 道具.get('flexDirection')=='row' else 'column',#方向
            'data-border':True if 有边框 else None,#有边框才写
            'data-color':取色(道具.get('borderColor')) if 有边框 else None,#边框色
        })
        for 键,值 in 样式.items():#行内间距
            setattr(盒.style,键,值)
        for 子节点 in 子节点表:#按顺序挂上
            盒.appendChild(子节点.根)
        自身.根=盒
        return 自身.根


class 条带:
    '提示上方的当前模组绘制。没有树时不留 group'
    def __init__(自身,属性):
        '记下按下和画面，并画出'
        自身.属性=属性#useBand 与 press
        自身.进行中=None#正在按的动作号
        自身.提示=None#失败句
        自身.根=None#渲染器握住的根
        自身.退订=None#画面订阅
        自身.已订=False#只订一次
        自身.绘制中=False#防止重入
        自身.待重画=False#绘制中又脏了
        自身.渲染()

    def 更新(自身,属性):
        '换份额。渲染器接着会再画'
        自身.属性=属性

    def 拆除(自身):
        '退掉画面订阅'
        退=自身.退订#退订函数
        自身.退订=None
        if 退 is not None:#订过
            退()

    def 渲染(自身):
        '没有树时清空。有树则画出条带，按钮点击发回宿主'
        if 自身.绘制中:#这一轮还没画完
            自身.待重画=True#结束再画
            return 自身.根
        自身.绘制中=True#占住
        try:
            窗口=取握手窗口()#当前页
            文档=窗口.document#页面文档
            ################################
            #样式只插一次，类名仍是原文
            ################################
            已有样式=文档.getElementById(样式标识)#已经插过
            if 已有样式 is None:#第一次
                样式节点=文档.createElement('style')#样式
                样式节点.id=样式标识#下次认这个
                样式路径=连接路径(目录名(__file__),'条带.module.css')#同目录样式
                with open(样式路径,'r',encoding='utf-8') as 样式文件:#读完即关
                    样式节点.textContent=样式文件.read()#颜色留在变量里
                文档.head.appendChild(样式节点)#挂到页面
            if 自身.已订 is False:#画面变化要重画
                自身.已订=True
                def 变更():
                    '画面变了就重画'
                    if 自身.绘制中:#正在画
                        自身.待重画=True#结束再画
                        return
                    自身.渲染()
                自身.退订=自身.属性['useBand']._subscribe(变更)#订存储
            画面=自身.属性['useBand'](原样)#上游在这里读取画面
            if 自身.根 is None:#渲染器要一个稳定的根
                自身.根=文档.createElement('span')#不占布局
                自身.根.style.display='contents'#不生成盒子
            while 自身.根.firstChild is not None:#清掉上一帧
                自身.根.firstChild.remove()
            if 画面 is not None and 画面['tree'] is not None:#有树才留 group
                ################################
                #这一帧的按下。代数用画出时的那一版
                ################################
                代数=画面['generation']#按下带上这一代
                def 按下(动作号):
                    '先标进行中，再等宿主。失败写在条带下方'
                    自身.进行中=动作号#这一下进行中
                    自身.提示=None#清掉旧失败
                    自身.渲染()#先画出禁用
                    try:
                        自身.属性['press'](代数,动作号)#同步等宿主返回
                    except Exception as 错误:#按下被拒绝
                        自身.进行中=None#结束进行中
                        原文=getattr(错误,'message',None)#页面错误常有 message
                        if not isinstance(原文,str):#没有消息就转成字符串
                            原文=str(错误)
                        自身.提示='按钮操作失败：{message}'.replace('{message}',原文)#中文表原文
                    else:#按下完成
                        自身.进行中=None#结束进行中
                    自身.渲染()#按结果再画
                带=文档.createElement('div')#条带
                带.className='band'#样式类名保持原文
                带.setAttribute('role','group')#一组控件
                带.setAttribute('aria-label','Claude Code 模组')#中文表 band 的原文
                带.setAttribute('data-generation',str(代数))#这一代
                for 项 in 画面['tree']:#顶层节点
                    外包=文档.createElement('span')#每个顶层节点外包一层
                    外包.className='text'#样式类名保持原文
                    画=节点({
                        'node':项,#这一项
                        'pending':自身.进行中,#进行中则全部禁用
                        'onPress':按下,#点击
                        'hotkeyLabel':热键文案,#方括号提示
                        '文档':文档,#页面文档
                    })
                    外包.appendChild(画.根)#放进外包
                    带.appendChild(外包)
                if 自身.提示 is not None:#失败句
                    提示=文档.createElement('div')#状态
                    提示.className='notice'#样式类名保持原文
                    提示.setAttribute('role','status')#读屏
                    提示.appendChild(文档.createTextNode(自身.提示))
                    带.appendChild(提示)
                自身.根.appendChild(带)#放进不占布局的根
        finally:
            自身.绘制中=False#放开
        if 自身.待重画:#画的时候画面又变了
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

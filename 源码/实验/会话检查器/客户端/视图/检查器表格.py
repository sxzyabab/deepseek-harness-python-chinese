'会话日志和对话分组共用的虚拟表格'

from .....客户端.模块.客户端.通告 import 取握手窗口
import os#样式
from .....客户端.ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块#样式
from .....客户端.ui_基础界面组件.提示泡 import 提示泡#序号提示
from .表格模型 import 检查器表格层级,检查器行已折叠#折叠和粘性
from .表格布局 import 检查器表格布局,检查器行高#滚动锚
from .格式 import 检查器预览#没有现成摘要时
from .原始json import 检查器json#详情文本
from .类型筛选 import 检查器类型筛选#已确认的筛选
from .类型筛选器 import 类型筛选器#筛选按钮
from .检查器详情 import 检查器详情#原文面板
from .检查器对象树 import 检查器json树,检查器对象树#详情树

样式模块='session-inspector'#检查器样式
过扫描=12#视口外多画的行数

def 确保样式(文档):
    '表格和详情共用这一份样式'
    注入模块样式文件(文档,'dsh-session-inspector',os.path.join(os.path.dirname(__file__),'检查器.module.css'),样式模块)#只插一次

def 类名(名字列表):
    '去掉空的类名'
    留下=[]#有效类名
    for 名 in 名字列表:#逐个
        if 名:#有
            留下.append(名)#留下
    return ' '.join(留下)#空格分隔

class 数据行:
    '表格里的一行。记录变了并且允许闪时，用主题高亮闪一下'
    def __init__(自身,属性):
        '记下行和回调'
        自身.属性=属性#属性
        自身.根=None#tr
        自身.先前记录=未读#上一份记录
        自身.先前脉冲=0#上一次定位脉冲
        自身.动画=None#高亮动画

    def 更新(自身,属性):
        '换成新的选中、折叠和记录'
        自身.属性=属性#新属性

    def 拆除(自身):
        '停动画并卸行'
        if 自身.动画 is not None:#还在闪
            自身.动画.cancel()#停
        自身.动画=None#清空
        if 自身.根 is not None:#还在
            自身.根.remove()#拿掉
        自身.根=None#清空

    def 渲染(自身):
        '画出序号、类型、位置、可选时间和预览'
        属性=自身.属性#当前
        窗口=属性['window']#窗口
        文档=窗口.document#文档
        行=属性['row']#行元数据
        记录源=属性['useRecord'](行['key'])#这一行的记录
        记录=None if 记录源 is None else 记录源#钩子已经选出快照
        if callable(getattr(记录源,'getSnapshot',None)):#万一交来的是源
            记录=记录源.getSnapshot()#再读
        变了=自身.先前记录 is not 未读 and 自身.先前记录 is not 记录#记录换了
        自身.先前记录=记录#记下
        导航脉冲=属性.get('pulse') or 0#定位脉冲
        刚定位=导航脉冲>0 and 自身.先前脉冲!=导航脉冲#这一次定位
        自身.先前脉冲=导航脉冲#记下
        if 自身.动画 is not None:#旧动画
            自身.动画.cancel()#停
            自身.动画=None#清空
        if 自身.根 is not None:#重画
            自身.根.remove()#拿掉
        根=文档.createElement('tr')#行
        标样式模块(根,样式模块)#模块
        根.setAttribute('aria-selected','true' if 属性.get('selected') else 'false')#是否选中
        if 属性.get('context'):#筛选留下的祖先
            根.setAttribute('data-inspector-context','')#上下文行
            根.setAttribute('title','匹配记录的父级上下文')#中文说明
        根.className=类名([
            'selected' if 属性.get('selected') else '',
            'sticky' if 属性.get('stickyLevel') is not None else '',
            'contextRow' if 属性.get('context') else '',
        ])#状态类名
        if 属性.get('stickyLevel') is not None:#钉住
            根.style.top=str((属性['stickyLevel']+1)*检查器行高)+'px'#表头之下
            根.style.zIndex=str(9-属性['stickyLevel'])#越外层越高
        序号格=模块节点(文档,'td',样式模块,'identity')#序号
        身份='' if not isinstance(记录,dict) or 记录.get('identity') is None else str(记录.get('identity'))#身份文本
        字=模块节点(文档,'span',样式模块,'identityText')#可聚焦的文本
        字.setAttribute('tabindex','0')#键盘可聚焦
        字.textContent=身份#文本
        提示泡({'window':窗口,'label':身份,'side':'right','portal':True,'children':字}).渲染()#右侧提示
        序号格.appendChild(字)#放入
        根.appendChild(序号格)#序号列
        类型格=文档.createElement('td')#类型
        标样式模块(类型格,样式模块)#模块
        类型格.style.paddingInlineStart=str(8+行.get('depth',0)*20)+'px'#按深度缩进
        if 属性.get('branch'):#有子行
            展开钮=模块节点(文档,'button',样式模块,'disclosure')#展开
            展开钮.setAttribute('type','button')#按钮
            合着=属性.get('collapsed') is True#当前合着
            展开钮.setAttribute('aria-label','展开子行' if 合着 else '收起子行')#中文
            展开钮.setAttribute('aria-expanded','false' if 合着 else 'true')#状态
            展开钮.textContent='▸' if 合着 else '▾'#记号
            def 点展开(事件,这一行=行,元素=根):
                '把这一行和它的位置交给表格'
                属性['toggle'](这一行,元素)#切换
            展开钮.addEventListener('click',点展开)#点击
            类型格.appendChild(展开钮)#放入
        类型钮=模块节点(文档,'button',样式模块,'record')#类型按钮
        类型钮.setAttribute('type','button')#按钮
        类型钮.textContent='' if not isinstance(记录,dict) else str(记录.get('type') or '')#类型
        def 点类型(事件,键=行['key']):
            '选中这一行'
            属性['select'](键)#选择
        类型钮.addEventListener('click',点类型)#点击
        类型格.appendChild(类型钮)#放入
        根.appendChild(类型格)#类型列
        位置格=文档.createElement('td')#位置
        标样式模块(位置格,样式模块)#模块
        位置格.textContent='' if not isinstance(记录,dict) else str(记录.get('location') or '')#T/S
        根.appendChild(位置格)#位置列
        if 属性.get('showTime'):#日志才有时间
            时间格=文档.createElement('td')#时间
            标样式模块(时间格,样式模块)#模块
            时刻=None if not isinstance(记录,dict) else 记录.get('time')#毫秒
            if isinstance(时刻,(int,float)) and not isinstance(时刻,bool):#有时间
                时间格.textContent=窗口.Date(时刻).toISOString().slice(11,23)#UTC 的时分秒
            根.appendChild(时间格)#时间列
        摘要=''#预览
        if isinstance(记录,dict):#有记录
            if 属性.get('collapsed') and 记录.get('collapsedSummary') is not None:#折叠摘要
                摘要=str(记录.get('collapsedSummary'))#用它
            elif 记录.get('summary') is not None:#自带摘要
                摘要=str(记录.get('summary'))#用它
            else:#现算
                摘要=检查器预览(记录.get('value'))#有界预览
        数据格=文档.createElement('td')#数据
        标样式模块(数据格,样式模块)#模块
        预览钮=模块节点(文档,'button',样式模块,'preview')#预览按钮
        预览钮.setAttribute('type','button')#按钮
        预览钮.textContent=摘要#预览
        def 点预览(事件,键=行['key']):
            '点预览也是选中'
            属性['select'](键)#选择
        预览钮.addEventListener('click',点预览)#点击
        数据格.appendChild(预览钮)#放入
        根.appendChild(数据格)#数据列
        自身.根=根#记住
        允许闪=属性.get('flash') or 刚定位#对话新行或刚定位
        if 允许闪 and (变了 or 属性.get('added') or 刚定位) and not 窗口.matchMedia('(prefers-reduced-motion: reduce)').matches:#需要闪
            颜色=窗口.getComputedStyle(根).getPropertyValue('--dsw-specific-bubble-highlight')#主题高亮
            自身.动画=根.animate([{'backgroundColor':颜色},{'backgroundColor':'transparent'}],{'duration':700})#闪一下
        return 根#行

未读=object()#区分还没读过和记录就是空

class 检查器表格:
    '分页的层级表。行键稳定，选中后看原始数据'
    def __init__(自身,属性):
        '记下钩子和本地状态，并画出表'
        自身.属性=属性#属性
        自身.根=None#section
        自身.失败=None#加载更早的失败
        自身.选中=None#选中行键
        自身.对象历史=None#对象导航栈
        自身.揭示=None#要滚到的行
        自身.已应用揭示=None#已经滚过的揭示
        自身.已应用选取=None#已经处理的点选
        自身.披露={}#手动展开
        自身.类型查询=''#已确认的类型片段
        自身.跟随='tail'#tail、scroll、manual
        自身.视口={'offset':0,'height':600}#滚动几何
        自身.披露锚=None#刚点的展开行
        自身.间距世代=0#手动展开后不再沿用上一份空白
        自身.已见={}#行第一次出现的时间
        自身.已初始化=False#已经见过行
        自身.已提交=None#上一份布局
        自身.滚动器=None#滚动容器
        自身.表体=None#tbody
        自身.行实例={}#行键到数据行
        自身.筛选器=None#类型筛选按钮
        自身.详情=None#详情面板
        自身.退订=[]#钩子退订
        自身.已订=False#是否订过
        自身.绘制中=False#避免重入
        自身.待重画=False#绘制中又来了一次
        自身.渲染()#画出

    def 更新(自身,属性):
        '换成新的钩子和点选'
        自身.属性=属性#新属性

    def 拆除(自身):
        '卸订阅、行和详情'
        for 退 in 自身.退订:#每个订阅
            退()#拆
        自身.退订=[]#清空
        自身.已订=False#可再订
        for 行 in 自身.行实例.values():#每一行
            行.拆除()#卸
        自身.行实例.clear()#清空
        if 自身.筛选器 is not None:#筛选
            自身.筛选器.拆除()#卸
        自身.筛选器=None#清空
        if 自身.详情 is not None:#详情
            自身.详情.拆除()#卸
        自身.详情=None#清空
        if 自身.根 is not None:#整表
            自身.根.remove()#拿掉
        自身.根=None#清空

    def 订上(自身):
        '行和会话变化时重画'
        if 自身.已订:#订过
            return#不重复
        自身.已订=True#记下
        def 变更():
            '根已经离开页面就退订，否则重画'
            if 自身.根 is not None and 自身.根.parentNode is None:#被摘掉
                自身.拆除()#卸干净
                return#停
            自身.渲染()#重画
        for 名 in ('useRows','useSession','useRecord'):#三份钩子
            钩=自身.属性.get(名)#钩子
            if 钩 is not None and callable(getattr(钩,'_subscribe',None)):#渲染器的钩子
                自身.退订.append(钩._subscribe(变更))#订

    def 现在(自身):
        '浏览器的当前毫秒'
        return 取握手窗口().performance.now()#性能时钟

    def 套用筛选(自身,查询):
        '确认后回到顶部，并清掉选中和手动展开'
        自身.跟随='scroll'#不要追尾
        自身.类型查询=检查器类型筛选(查询).查询#规范化
        自身.披露={}#展开作废
        自身.间距世代=自身.间距世代+1#空白重新算
        自身.选中=None#清选中
        自身.对象历史=None#清导航
        自身.揭示=None#不清滚动到旧行
        自身.渲染()#重画
        if 自身.滚动器 is not None:#有滚动容器
            自身.滚动器.scrollTop=0#回到顶

    def 切换(自身,行,元素):
        '记住这一行在视口里的位置，再反转折叠'
        if 自身.滚动器 is None:#还没有表
            return#不能量
        自身.跟随='manual'#不要追尾
        宿主=自身.滚动器#滚动容器
        自身.披露锚={'key':行['key'],'top':元素.getBoundingClientRect().top-宿主.getBoundingClientRect().top-宿主.clientTop}#视口内位置
        自身.视口={'offset':宿主.scrollTop,'height':宿主.clientHeight}#量之前的几何
        下一=dict(自身.披露)#拷贝
        下一[行['key']]={'state':行.get('disclosure'),'collapsed':not 检查器行已折叠(行,自身.披露)}#反转
        自身.披露=下一#换上
        自身.渲染()#重画

    def 定位聊天(自身,目标):
        '有导航就把坐标交给主对话'
        导航=自身.属性.get('navigation')#导航
        if 导航 is None:#这张表不定位
            return#停
        导航['reveal'](目标 or {})#闪对话

    def 选择(自身,键):
        '选中行，清掉对象栈，并定位到对话'
        自身.选中=键#选中
        自身.对象历史=None#从这一行重新导航
        导航=自身.属性.get('navigation')#导航
        目标=None if 导航 is None else 导航['target'](键)#这一行的坐标
        自身.定位聊天(目标)#闪对话
        自身.渲染()#打开详情

    def 定位行(自身,键,全部行,过滤行,筛选):
        '展开祖先。行被筛选藏住时先清掉筛选'
        清筛选=筛选.生效 and not any(行['key']==键 for 行 in 过滤行)#当前过滤里没有
        if 清筛选:#先取消筛选
            自身.类型查询=''#清空
        自身.跟随='scroll'#滚到这一行，不追尾
        自身.选中=键#选中
        来源=全部行 if 清筛选 else 过滤行#用哪一份找父
        按键={}#键到行
        for 行 in 来源:#索引
            按键[行['key']]=行#记下
        下一=dict(自身.披露)#拷贝
        父=按键.get(键,{}).get('parent')#父键
        while 父 is not None:#沿祖先打开
            行=按键.get(父)#父行
            if 行 is None:#断了
                break#停
            下一[父]={'state':行.get('disclosure'),'collapsed':False}#打开
            父=行.get('parent')#再上一层
        自身.披露=下一#换上
        脉冲=1 if 自身.揭示 is None else 自身.揭示.get('pulse',0)+1#新的一次
        自身.揭示={'key':键,'pulse':脉冲}#等布局后滚动

    def 导航(自身,引用):
        '压入对象栈，定位对话，行还在就滚到那一行'
        属性=自身.属性#当前
        记录=自身.当前记录()#选中记录
        行标签=(str(记录.get('type') or '') if isinstance(记录,dict) else '')+' · '+(str(记录.get('identity')) if isinstance(记录,dict) and 记录.get('identity') is not None else str(自身.选中))#面包屑根
        先前=自身.对象历史#已有栈
        自身.对象历史={
            'rootKey':自身.选中 if 先前 is None else 先前.get('rootKey'),#最初的行
            'rootLabel':行标签 if 先前 is None else 先前.get('rootLabel'),#最初的标签
            'references':list(先前.get('references') if 先前 is not None else [])+[引用],#压入
        }#新栈
        自身.定位聊天(引用.get('target'))#闪对话
        if 引用.get('rowKey') is not None:#表格里有这一行
            全部=自身.读行()#全部行
            筛选=检查器类型筛选(自身.类型查询)#当前筛选
            过滤=筛选.套用(全部,属性['typeOf'])#过滤结果
            自身.定位行(引用['rowKey'],全部,过滤['rows'],筛选)#滚过去
        自身.渲染()#重画详情

    def 回到(自身,下标):
        '面包屑回到某一层，并滚到对应行'
        历史=自身.对象历史#当前栈
        if 历史 is None:#没有栈
            return#停
        引用=None if 下标==0 else 历史['references'][下标-1]#这一层
        键=历史['rootKey'] if 下标==0 else (None if 引用 is None else 引用.get('rowKey'))#行键
        导航=自身.属性.get('navigation')#导航
        if 下标==0:#回到根行
            目标=None if 导航 is None else 导航['target'](历史['rootKey'])#根坐标
            自身.对象历史=None#清栈
        else:#回到中间层
            目标=None if 引用 is None else 引用.get('target')#该层坐标
            自身.对象历史={'rootKey':历史['rootKey'],'rootLabel':历史['rootLabel'],'references':历史['references'][:下标]}#截断
        if 键 is not None:#有行
            全部=自身.读行()#全部行
            筛选=检查器类型筛选(自身.类型查询)#筛选
            过滤=筛选.套用(全部,自身.属性['typeOf'])#结果
            自身.定位行(键,全部,过滤['rows'],筛选)#滚过去
        自身.定位聊天(目标)#闪对话
        自身.渲染()#重画

    def 读行(自身):
        '当前全部行，不经筛选'
        def 原样(值):
            '整份行列表'
            return 值#原样
        行=自身.属性['useRows'](原样)#钩子
        return list(行 or [])#没有时当空

    def 当前记录(自身):
        '选中行的记录。没有选中时读空键'
        钩=自身.属性['useRecord']#按键记录
        快照=钩(自身.选中 or '')#快照或源
        if callable(getattr(快照,'getSnapshot',None)):#还是源
            return 快照.getSnapshot()#读
        return 快照#已经是记录

    def 渲染(自身):
        '画出工具栏、可见行和选中详情'
        if 自身.绘制中:#重入
            自身.待重画=True#记一笔
            return 自身.根#先返回
        自身.绘制中=True#占住
        try:#画完一定放开
            属性=自身.属性#当前
            窗口=属性['window']#窗口
            文档=窗口.document#文档
            确保样式(文档)#样式
            全部=自身.读行()#全部行
            def 还有(值):
                '会话是否还有更早的页'
                return isinstance(值,dict) and 值.get('hasMore') is True#还有
            def 在载(值):
                '是否正在加载更早'
                return isinstance(值,dict) and 值.get('loadingOlder') is True#在载
            def 打开错(值):
                '打开会话的错误'
                if not isinstance(值,dict):#没有快照
                    return None#无
                return 值.get('openError')#错误
            还有更多=属性['useSession'](还有)#翻页
            加载中=属性['useSession'](在载)#忙碌
            打开错误=属性['useSession'](打开错)#打开失败
            选取=属性.get('pickedRow')#对话里点到的行
            if 选取 is not None and 自身.已应用选取 is not 选取 and any(行['key']==选取.get('key') for 行 in 全部):#新的点选而且行在
                自身.已应用选取=选取#记下
                自身.对象历史=None#从这一行开始
                筛选前=检查器类型筛选(自身.类型查询)#当前筛选
                过滤前=筛选前.套用(全部,属性['typeOf'])#过滤
                自身.定位行(选取['key'],全部,过滤前['rows'],筛选前)#展开并选中
            筛选=检查器类型筛选(自身.类型查询)#确认后的筛选
            过滤=筛选.套用(全部,属性['typeOf'])#行和命中
            层级=检查器表格层级(过滤['rows'],自身.披露)#可见层级
            先前布局=None#手动展开不用上一份
            if 自身.已提交 is not None and 自身.已提交['disclosures'] is 自身.披露 and 自身.已提交['spacingGeneration']==自身.间距世代:#同一套展开
                先前布局=自身.已提交['layout']#用来保住折叠锚
            布局=检查器表格布局(层级,先前布局,自身.视口,自身.披露锚)#这一份布局
            现在=自身.现在()#当前时间
            到达={}#行第一次出现的时间
            for 行 in 全部:#每一行
                已有=自身.已见.get(行['key'])#见过
                if 已有 is None:#新行
                    到达[行['key']]=现在 if 自身.已初始化 else float('-inf')#第一次不闪历史
                else:#见过
                    到达[行['key']]=已有#沿用
            if len(全部)>0:#有行
                自身.已初始化=True#之后的新行可以闪
            自身.已见=到达#换上
            自身.保证骨架(文档,窗口,属性,全部,过滤,筛选,还有更多,加载中,打开错误)#工具栏和表
            自身.填行(文档,窗口,属性,布局,层级,过滤,筛选,到达)#可见行
            自身.安放滚动(窗口,布局)#锚、追尾、定位
            自身.画详情(文档,窗口,属性,筛选)#选中详情
            自身.订上()#变化后重画
        finally:#放开
            自身.绘制中=False#结束
        if 自身.待重画:#绘制中又来了
            自身.待重画=False#清掉
            return 自身.渲染()#再画
        return 自身.根#表格

    def 保证骨架(自身,文档,窗口,属性,全部,过滤,筛选,还有更多,加载中,打开错误):
        '第一次建表。之后只改文字、通知和按钮'
        if 自身.根 is None:#第一次
            根=模块节点(文档,'section',样式模块,'root')#整页
            根.setAttribute('aria-label',属性.get('title') or '')#标题
            栏=模块节点(文档,'div',样式模块,'toolbar')#工具栏
            标题=文档.createElement('span')#左侧标题
            栏.appendChild(标题)#放入
            更早=文档.createElement('button')#加载更早
            更早.setAttribute('type','button')#按钮
            def 点更早(事件):
                '翻页时停住追尾。失败留在表上'
                自身.跟随='scroll'#不追尾
                自身.失败=None#清旧失败
                try:#同步翻页
                    自身.属性['loadOlder']()#加载
                except Exception as 错误:#翻页失败
                    自身.失败=str(错误)#留下
                自身.渲染()#重画
            更早.addEventListener('click',点更早)#点击
            栏.appendChild(更早)#放入
            最新=文档.createElement('button')#跟踪最新
            最新.setAttribute('type','button')#按钮
            最新.textContent='跟踪最新'#中文
            def 点最新(事件):
                '回到追尾，并丢掉为折叠留下的空白'
                自身.跟随='tail'#追尾
                自身.间距世代=自身.间距世代+1#空白重算
                自身.渲染()#重画
            最新.addEventListener('click',点最新)#点击
            栏.appendChild(最新)#放入
            根.appendChild(栏)#工具栏
            通知=模块节点(文档,'div',样式模块,'pickNotice')#选取说明
            通知.setAttribute('role','status')#状态
            根.appendChild(通知)#先放着，没有说明时藏起
            警告=文档.createElement('p')#失败
            警告.setAttribute('role','alert')#警告
            根.appendChild(警告)#先放着
            滚动=模块节点(文档,'div',样式模块,'scroller')#滚动容器
            def 滚动时(事件):
                '离开底部就不再追尾。手动展开时不改跟随'
                盒=事件.currentTarget#滚动容器
                自身.视口['offset']=盒.scrollTop#记下
                if 自身.跟随!='manual':#不是手动展开
                    差=盒.scrollHeight-盒.clientHeight-盒.scrollTop#离底部
                    自身.跟随='tail' if 差<=40 else 'scroll'#靠近底部才追
            滚动.addEventListener('scroll',滚动时)#滚动
            表=模块节点(文档,'table',样式模块,'table')#表
            表.setAttribute('aria-label',属性.get('title') or '')#标题
            头=文档.createElement('thead')#表头
            头行=文档.createElement('tr')#表头行
            标样式模块(头行,样式模块)#模块
            for 文案,类 in (('序号','idColumn'),('类型','typeColumn'),('T/S','locationColumn')):#前三列
                格=模块节点(文档,'th',样式模块,类)#列
                if 类=='typeColumn':#类型列带筛选
                    盒=模块节点(文档,'span',样式模块,'typeHeader')#标题和按钮
                    字=文档.createElement('span')#文字
                    字.textContent='类型'#中文
                    盒.appendChild(字)#放入
                    格.appendChild(盒)#放入
                else:#普通列
                    格.textContent=文案#中文
                头行.appendChild(格)#放入
            时间头=模块节点(文档,'th',样式模块,'timeColumn')#时间列
            时间头.textContent='时间 (UTC)'#中文
            头行.appendChild(时间头)#先放着
            数据头=文档.createElement('th')#数据列
            标样式模块(数据头,样式模块)#模块
            数据头.textContent='数据'#中文
            头行.appendChild(数据头)#放入
            头.appendChild(头行)#表头行
            表.appendChild(头)#表头
            体=文档.createElement('tbody')#表体
            表.appendChild(体)#表体
            滚动.appendChild(表)#表
            空=模块节点(文档,'p',样式模块,'empty')#没有记录
            空.textContent='暂无记录'#中文
            滚动.appendChild(空)#放入
            根.appendChild(滚动)#滚动区
            自身.根=根#记住
            自身.滚动器=滚动#记住
            自身.表体=体#记住
            自身.标题节=标题#左侧文字
            自身.更早钮=更早#翻页
            自身.通知节=通知#选取说明
            自身.警告节=警告#失败
            自身.时间头=时间头#可隐藏
            自身.空节=空#空状态
            自身.类型盒=头行.children[1].firstChild#类型标题盒
            if 属性.get('parent') is not None:#有挂点
                属性['parent'].appendChild(根)#挂上
        选择器=属性.get('modeSelector')#展示形式
        左侧=自身.标题节#标题槽
        while 左侧.firstChild is not None:#清掉旧内容
            左侧.removeChild(左侧.firstChild)#拿掉
        if 选择器 is not None:#有选择器
            左侧.appendChild(选择器)#放进去
            左侧.appendChild(文档.createTextNode(' · '))#分隔
        else:#用标题
            左侧.appendChild(文档.createTextNode((属性.get('title') or '')+' · '))#标题
        if 筛选.生效:#正在筛选
            计数=str(len(过滤['matches']))+' / '+str(len(全部))#命中/全部
        else:#没有筛选
            计数=str(len(全部))#行数
        左侧.appendChild(文档.createTextNode(计数))#数字
        自身.更早钮.disabled=加载中 is True#加载时不能再点
        自身.更早钮.textContent='加载中…' if 加载中 else '加载更早'#中文
        自身.更早钮.style.display='' if 还有更多 else 'none'#没有更早就藏起
        说明=属性.get('notice')#选取说明
        if 说明 is None:#没有
            自身.通知节.style.display='none'#藏起
        else:#有说明
            自身.通知节.style.display=''#显示
            自身.通知节.textContent=说明#中文
        错误文=自身.失败#翻页失败
        if 错误文 is None and 打开错误 is not None:#打开失败
            if isinstance(打开错误,dict):#结构化错误
                错误文=打开错误.get('message')#消息
            else:#异常或其他
                错误文=getattr(打开错误,'message',None) or str(打开错误)#文本
        if 错误文 is None:#没有失败
            自身.警告节.style.display='none'#藏起
        else:#有失败
            自身.警告节.style.display=''#显示
            自身.警告节.textContent=str(错误文)#文本
        自身.时间头.style.display='' if 属性.get('showTime') else 'none'#对话分组没有时间
        自身.根.setAttribute('aria-label',属性.get('title') or '')#标题
        def 建议(查询):
            '从全部已加载行取候选'
            return 检查器类型筛选(查询).建议(全部,属性['typeOf'])#同步
        if 自身.筛选器 is None:#第一次
            自身.筛选器=类型筛选器({'window':窗口,'parent':自身.类型盒,'value':自身.类型查询,'suggest':建议,'apply':自身.套用筛选})#按钮
        else:#更新查询
            自身.筛选器.更新({'window':窗口,'parent':自身.类型盒,'value':自身.类型查询,'suggest':建议,'apply':自身.套用筛选})#新属性
            if 自身.筛选器.根 is not None and 自身.筛选器.根.parentNode is not 自身.类型盒:#不在类型列
                自身.类型盒.appendChild(自身.筛选器.根)#挂上
            自身.筛选器.渲染()#刷新按下状态

    def 填行(自身,文档,窗口,属性,布局,层级,过滤,筛选,到达):
        '只画视口附近的行，粘性祖先额外留下'
        while 自身.表体.firstChild is not None:#清表体
            自身.表体.removeChild(自身.表体.firstChild)#拿掉
        数量=len(布局.项)#数据行数
        偏移=自身.视口['offset']#当前滚动
        if 布局.滚动偏移 is not None and (自身.已提交 is None or 自身.已提交['layout'] is not 布局):#这份布局要求跳转
            偏移=布局.滚动偏移#先按锚画
        高度=自身.视口['height'] or 600#视口高度
        if 数量==0:#没有行
            下标列表=[]#不画
        else:#有行
            首=max(0,int(偏移/检查器行高))#第一可见行
            起=max(0,首-1-过扫描)#再往上一点
            止=min(数量-1,int((偏移+高度)/检查器行高)+过扫描)#再往下一点
            粘性=布局.偏移处粘性下标(偏移)#钉住的祖先
            集合=set(粘性)#先放祖先
            号=起#可见起点
            while 号<=止:#可见范围
                集合.add(号)#加上
                号=号+1#下一个
            下标列表=sorted(集合)#从上到下
        列数=5 if 属性.get('showTime') else 4#列数
        上一结束=检查器行高#表头占一行
        现在=自身.现在()#判断新行
        用过=set()#这一轮画了的行
        for 位置,项下标 in enumerate(下标列表):#每个可见项
            项=布局.项[项下标]#布局项
            起点=检查器行高+(项下标*检查器行高)#虚拟起点，表头之后
            空隙=起点-上一结束#中间空档
            if 空隙>0:#需要占位
                空行=文档.createElement('tr')#占位行
                空行.setAttribute('aria-hidden','true')#不读
                空格=文档.createElement('td')#一格撑开
                空格.setAttribute('colspan',str(列数))#跨列
                空格.style.height=str(空隙)+'px'#高度
                空格.style.padding='0'#不留内边距
                空行.appendChild(空格)#放入
                自身.表体.appendChild(空行)#放入表
            上一结束=起点+检查器行高#这一行的底
            行=项['row']#行数据
            实例=自身.行实例.get(行['key'])#已有实例
            行属性={
                'window':窗口,'row':行,'selected':行['key']==自身.选中,
                'branch':层级.是分支(行['key']),'collapsed':检查器行已折叠(行,自身.披露),
                'added':现在-到达.get(行['key'],现在)<700,
                'stickyLevel':None,'pulse':自身.揭示['pulse'] if 自身.揭示 is not None and 自身.揭示.get('key')==行['key'] else 0,
                'context':筛选.生效 and 行['key'] not in 过滤['matches'],
                'select':自身.选择,'toggle':自身.切换,'useRecord':属性['useRecord'],
                'flash':属性.get('flash'),'showTime':属性.get('showTime'),
            }#这一行
            粘性层=None#是否钉住
            for 层,粘下标 in enumerate(布局.偏移处粘性下标(偏移)):#当前粘性
                if 粘下标==项下标:#就是这一行
                    粘性层=层#层号
                    break#停
            行属性['stickyLevel']=粘性层#可能为空
            if 实例 is None:#第一次
                实例=数据行(行属性)#新建
                自身.行实例[行['key']]=实例#留下
            else:#还在
                实例.更新(行属性)#换属性
            节点=实例.渲染()#画出
            if 节点 is not None:#有行
                自身.表体.appendChild(节点)#放入
            用过.add(行['key'])#记过
        末尾=0#表尾空白
        if len(下标列表)>0:#有可见行
            最后=下标列表[-1]#最后一项
            最后底=检查器行高+(最后+1)*检查器行高#它的底
            总高=(数量+1)*检查器行高+布局.底边距#含表头和折叠空白
            末尾=max(0,总高-最后底)#剩下的高度
        if 末尾>0:#需要尾部占位
            空行=文档.createElement('tr')#占位
            空行.setAttribute('aria-hidden','true')#不读
            if 布局.底边距>0:#折叠留下的空白
                空行.setAttribute('data-inspector-fold-space','')#标记
            空格=文档.createElement('td')#一格
            空格.setAttribute('colspan',str(列数))#跨列
            空格.style.height=str(末尾)+'px'#高度
            空格.style.padding='0'#不留内边距
            空行.appendChild(空格)#放入
            自身.表体.appendChild(空行)#放入
        for 键,实例 in list(自身.行实例.items()):#没画到的行
            if 键 not in 用过:#离开视口
                实例.拆除()#卸
                del 自身.行实例[键]#忘掉
        自身.空节.style.display='' if 数量==0 else 'none'#没有可见行
        自身.滚动器.firstChild.setAttribute('aria-rowcount',str(len(层级.行)+1))#含表头

    def 安放滚动(自身,窗口,布局):
        '先跳到锚或追尾，再记下视口。新的定位滚到行中间'
        盒=自身.滚动器#滚动容器
        锚偏移=None#这份布局要不要跳
        if 布局.滚动偏移 is not None and (自身.已提交 is None or 自身.已提交['layout'] is not 布局):#新布局
            锚偏移=布局.滚动偏移#跳到这里
        if 锚偏移 is not None:#有锚
            盒.scrollTop=锚偏移#跳
        elif 自身.跟随=='tail' and 布局.底边距==0:#追尾且没有折叠空白
            盒.scrollTop=盒.scrollHeight#到底
        自身.视口={'offset':盒.scrollTop,'height':盒.clientHeight or 600}#量之后的几何
        自身.披露锚=None#用过了
        自身.已提交={'layout':布局,'disclosures':自身.披露,'spacingGeneration':自身.间距世代}#提交
        if 自身.揭示 is not None and 自身.已应用揭示 is not 自身.揭示:#还没滚到
            下标=-1#目标行
            for 号,项 in enumerate(布局.项):#找行
                if 项['key']==自身.揭示['key']:#命中
                    下标=号#记下
                    break#停
            if 下标>=0:#在可见层级里
                目标=max(0,下标*检查器行高-盒.clientHeight/2)#行中
                盒.scrollTop=目标#滚过去
                自身.视口['offset']=盒.scrollTop#更新
                自身.已应用揭示=自身.揭示#记过

    def 画详情(自身,文档,窗口,属性,筛选):
        '没有选中就卸掉详情。对话分组用对象树，日志用 JSON 树'
        if 自身.选中 is None:#没有选中
            if 自身.详情 is not None:#还开着
                自身.详情.拆除()#卸
            自身.详情=None#清空
            return#停
        记录=自身.当前记录()#选中记录
        对象表=属性.get('objects')#对话对象
        详情=检查器json(None if 对象表 is not None else (None if not isinstance(记录,dict) else 记录.get('value')))#日志才序列化
        if 记录 is None:#行没了
            文本='该记录已移除或结算，请选择当前记录。'#中文
            失败=False#不是序列化失败
        elif 详情['failed']:#写不出 JSON
            文本='无法序列化这条记录，可以选择其他记录继续查看。\n'+详情['text']#中文加错误
            失败=True#失败
        else:#成功
            文本=详情['text']#JSON
            失败=详情['failed']#假
        子=None#详情内容
        if 对象表 is None:#日志
            if 记录 is not None and not 详情['failed']:#可以画 JSON 树
                if not hasattr(自身,'json树') or 自身.json树 is None or getattr(自身,'json键',None)!=自身.选中:#换行
                    自身.json树=检查器json树({'window':窗口,'text':详情['text']})#新树
                    自身.json键=自身.选中#记下
                else:#同一行
                    自身.json树.更新({'window':窗口,'text':详情['text']})#换文本
                子=自身.json树.渲染()#树
        else:#对话对象
            历史=自身.对象历史#导航栈
            当前引用=None if 历史 is None or len(历史.get('references') or [])==0 else 历史['references'][-1]#栈顶
            值=记录.get('value') if isinstance(记录,dict) else None#根值
            if 当前引用 is not None:#在看链接进去的对象
                值=当前引用['read']()#再读
            行标签=''#根标签
            if isinstance(记录,dict):#有记录
                行标签=str(记录.get('type') or '')+' · '+str(记录.get('identity') if 记录.get('identity') is not None else 自身.选中)#类型和身份
            else:#没有记录
                行标签=' · '+str(自身.选中)#只有键
            屑=[历史['rootLabel'] if 历史 is not None else 行标签]#第一层
            种类表={'node':'Node','nodeData':'Node Data','group':'Group','groupData':'Group Data','turn':'Turn','turnData':'Turn Data','step':'Step','stepData':'Step Data'}#中文表原文
            for 引用 in (历史.get('references') if 历史 is not None else []) or []:#每一跳
                种类=引用.get('kind')#对象种类
                屑.append(种类表.get(种类,种类 or '')+' · '+str(引用.get('identity')))#种类和身份
            导航条=模块节点(文档,'nav',样式模块,'objectBreadcrumbs')#面包屑
            导航条.setAttribute('aria-label','原始数据导航')#中文
            列表=文档.createElement('ol')#有序列表
            for 下标,标签 in enumerate(屑):#每一层
                项=文档.createElement('li')#一项
                if 下标>0:#不是第一层
                    隔=文档.createElement('span')#分隔
                    隔.setAttribute('aria-hidden','true')#装饰
                    隔.textContent='›'#记号
                    项.appendChild(隔)#放入
                钮=文档.createElement('button')#一层
                钮.setAttribute('type','button')#按钮
                钮.setAttribute('title',标签)#完整标签
                钮.textContent=标签#文本
                最后=下标==len(屑)-1#当前层
                钮.disabled=最后#当前层不能再点
                if 最后:#当前
                    钮.setAttribute('aria-current','page')#当前页
                def 点屑(事件,层=下标):
                    '回到这一层'
                    自身.回到(层)#截断栈
                钮.addEventListener('click',点屑)#点击
                项.appendChild(钮)#放入
                列表.appendChild(项)#放入
            导航条.appendChild(列表)#列表
            对象键=当前引用.get('id') if 当前引用 is not None else 自身.选中#树的身份
            if not hasattr(自身,'对象树') or 自身.对象树 is None or getattr(自身,'对象键',None)!=对象键:#换了对象
                自身.对象树=检查器对象树({'window':窗口,'value':值,'objects':对象表,'navigate':自身.导航})#新树
                自身.对象键=对象键#记下
            else:#同一个对象
                自身.对象树.更新({'window':窗口,'value':值,'objects':对象表,'navigate':自身.导航})#换值
            盒=文档.createElement('div')#面包屑加树
            盒.appendChild(导航条)#面包屑
            树节点=自身.对象树.渲染()#树
            if 树节点 is not None:#有树
                盒.appendChild(树节点)#放入
            子=盒#作为详情子节点
        def 关闭():
            '关掉详情和对象栈'
            自身.选中=None#清选中
            自身.对象历史=None#清栈
            自身.渲染()#重画
        详情属性={'window':窗口,'parent':自身.根,'text':文本,'failed':失败,'children':子,'close':关闭}#详情
        if 自身.详情 is None:#第一次
            自身.详情=检查器详情(详情属性)#新建
        else:#还在
            自身.详情.更新(详情属性)#换内容
            自身.详情.渲染()#重画

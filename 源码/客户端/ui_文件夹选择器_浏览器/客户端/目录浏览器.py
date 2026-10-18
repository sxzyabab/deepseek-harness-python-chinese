from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块#模块样式
from ...ui_基础界面组件.按钮 import 按钮#共享按钮
from ...ui_基础界面组件.icons import 图标,图标勾描边常规#共享图标
from ...ui_基础界面组件.模态层 import 使用模态层#对话框键盘和焦点
from ...ui_工作区.客户端.导航 import 取同步结果#同步取回列举结果

__all__=['目录浏览器']

样式模块='directory-browser'#样式隔离名
慢扫描延迟毫秒=300#超过这个时间才显示加载中
草稿预览防抖毫秒=250#路径草稿停键后再列目录
未安排=['未']#还没按当前草稿排过定时

def 失败文案(错误):
    '宿主业务消息优先，否则用异常文本'
    远程=None#rpc 错误
    if isinstance(错误,dict) and 'rpcError' in 错误:#字典
        远程=错误['rpcError']#取出
    elif 错误 is not None and not isinstance(错误,(str,int,float,bool)):#对象
        远程=getattr(错误,'rpcError',None)#属性
    if isinstance(远程,dict) and isinstance(远程.get('message'),str):#字典消息
        return 远程['message']#业务句
    if 远程 is not None and isinstance(getattr(远程,'message',None),str):#对象消息
        return 远程.message#业务句
    if isinstance(错误,BaseException):#普通异常
        return str(错误)#异常文本
    return str(错误)#其他

def 展示面包屑(列举,主目录标签):
    '主目录子树从主目录标签起，外面用完整谱系'
    屑=列举['crumbs']#宿主谱系
    主页=列举['home']#主目录路径
    下标=-1#主目录所在
    序=0#序号
    for 项 in 屑:#逐层
        if 项['path']==主页:#就是主目录
            下标=序#记下
            break#停
        序+=1#下一层
    if 下标==-1:#不在主目录子树
        return list(屑)#原样
    尾=list(屑[下标+1:])#主目录之后
    头={'name':主目录标签,'path':主页,'hidden':False}#主目录标签
    return [头]+尾#拼上

def 分隔符于(列举):
    '从主目录路径判断平台分隔符'
    if '\\' in 列举['home']:#Windows
        return '\\'#反斜杠
    return '/'#斜杠

def 读草稿(列举,草稿,已扫描):
    '目录部分，以及这一层是否用末段做前缀过滤'
    分隔=分隔符于(列举)#平台分隔符
    if 分隔=='\\':#Windows 两种斜杠都切开
        切=草稿.rfind('\\')#反斜杠
        斜=草稿.rfind('/')#斜杠
        if 斜>切:#斜杠更靠后
            切=斜#用斜杠
    else:#POSIX 反斜杠是名字
        切=草稿.rfind('/')#只认斜杠
    if 切==-1:#还没写到目录
        return {'directory':None,'tail':None}#没有
    目录=草稿[:切+1]#含分隔符
    层目录=列举['path']#这一层路径
    if not 层目录.endswith(分隔):#根路径自己已经带分隔符
        层目录=层目录+分隔#补上
    应答=目录==层目录#路径对得上
    if not 应答 and 已扫描 is not None:#宿主可能改写过拼法
        if 已扫描['directory']==目录 and 已扫描['landed']==列举['path']:#这次扫描落下的就是它
            应答=True#算答上
    if 应答:#末段用来过滤
        return {'directory':目录,'tail':草稿[len(目录):]}#带尾
    return {'directory':目录,'tail':None}#只知道目录

def 拼类(*段):
    '把非空类名拼成一个 class 字符串'
    出=[]#缓冲
    for 段名 in 段:#逐段
        if isinstance(段名,str) and 段名!='':#有类名
            出.append(段名)#收下
    return ' '.join(出)#拼

def 挂(节点,类名=None):
    '写上官方类名，并接上本模块的样式'
    if isinstance(类名,str) and 类名!='':#有类
        节点.className=类名#官方类名
    return 标样式模块(节点,样式模块)#接上

def 画图标(窗口,名,尺寸,类名=None):
    '按共享图标表画一枚'
    属性={'window':窗口,'size':尺寸}#窗口和边长
    if isinstance(类名,str) and 类名!='':#要类名
        属性['className']=类名#类
    节点=图标(名,属性)#svg
    if 节点 is None:#没有这枚
        return None#空
    if isinstance(类名,str) and 类名!='':#颜色类
        挂(节点,类名)#接上样式
    return 节点#节点

def 清空(节点):
    '拆掉一个节点的全部子节点'
    while 节点.firstChild is not None:#还有
        节点.firstChild.remove()#拆

def 确保样式(文档):
    '本对话框样式插一次。模态壳用共享样式里的官方类名'
    注入模块样式文件(文档,'目录浏览器样式',os.path.join(os.path.dirname(__file__),'目录浏览器.module.css'),样式模块)#本模块
    if 文档.getElementById('目录浏览器模态壳') is not None:#已经插过
        return#停
    路径=os.path.join(os.path.dirname(__file__),'..','..','ui_基础界面组件','模态.module.css')#共享模态样式
    句柄=open(路径,encoding='utf-8')#打开
    文本=句柄.read()#原文
    句柄.close()#关掉
    样式=文档.createElement('style')#样式标签
    样式.id='目录浏览器模态壳'#只插一次
    样式.textContent=文本#官方类名
    文档.head.appendChild(样式)#放进文档

class 层级列:
    '米勒视图里的一列文件夹'
    def __init__(自身,属性):
        '记下这一列的条目和点击'
        自身.属性=属性#列 props

    def 渲染(自身):
        '画出过滤之后仍可见的行。选中行不受过滤影响'
        属性=自身.属性#列 props
        文档=属性['document']#文档
        条目表=属性['entries']#这一层
        选中路径=属性['selectedPath']#选中
        过滤前缀=属性['filterPrefix']#前缀
        显示隐藏=属性['showHidden']#隐藏文件开关
        针='' if 过滤前缀 is None else 过滤前缀.lower()#小写前缀
        def 可显示(条目):
            '隐藏项默认不显示。点开头的前缀会把对得上的隐藏项放出来'
            if 显示隐藏 or not 条目['hidden']:#开关开着或本来可见
                return True#显示
            return 针.startswith('.')#点前缀点名
        def 匹配(条目):
            '又能显示，名字又对得上前缀'
            if not 可显示(条目):#不显示
                return False#不匹配
            return 条目['name'].lower().startswith(针)#前缀
        收窄=针!='' and any(匹配(条目) for 条目 in 条目表)#有人匹配才收窄
        可见=[]#要画的行
        for 条目 in 条目表:#逐条
            if 选中路径 is not None and 条目['path']==选中路径:#选中始终留下
                可见.append(条目)#留下
                continue#下一条
            if 收窄:#按前缀收
                if 匹配(条目):#对得上
                    可见.append(条目)#留下
                continue#下一条
            if 显示隐藏 or not 条目['hidden']:#普通可见
                可见.append(条目)#留下
        列=文档.createElement('div')#列
        挂(列,'column')#列样式
        列.setAttribute('role','list')#列表
        窗口=属性['window']#窗口
        忙=属性['busy']#整列禁用
        点选=属性['onPick']#点击
        编辑中=属性['pathEditing']#路径编辑中
        for 条目 in 可见:#逐行
            选中=条目['path']==选中路径#这一行选中
            座=文档.createElement('span')#行座
            挂(座,'rowSeat')#座样式
            座.setAttribute('role','listitem')#列表项
            钮=文档.createElement('button')#行按钮
            钮.type='button'#按钮
            挂(钮,拼类('row','rowSelected' if 选中 else ''))#行样式
            if 选中:#当前行
                钮.setAttribute('aria-current','true')#当前
            钮.disabled=忙#禁用
            if 编辑中:#不要抢走输入框焦点
                def 按下(事件):
                    '路径编辑中，按下时别把焦点带走'
                    事件.preventDefault()#留下焦点
                钮.addEventListener('mousedown',按下)#按下
            def 点行(事件,当前=条目):
                '选中这一行'
                点选(当前)#交给列的调用方
            钮.addEventListener('click',点行)#点击
            if 选中:#打开的文件夹
                图=画图标(窗口,'folder-open-16',16,'rowIconSelected')#开文件夹
            else:#关上的文件夹
                图=画图标(窗口,'folder-close-16',16,'rowIcon')#关文件夹
            if 图 is not None:#有图标
                钮.appendChild(图)#放入
            名=文档.createElement('span')#名字
            挂(名,'rowName')#名字样式
            名.textContent=条目['name']#文件夹名
            钮.appendChild(名)#放入
            箭=画图标(窗口,'chevron-right-14',12,'rowChevron')#向右
            if 箭 is not None:#有箭头
                钮.appendChild(箭)#放入
            座.appendChild(钮)#放入座
            列.appendChild(座)#放入列
        return 列#列节点

class 目录浏览器:
    '应用内选择工作区目录。米勒两栏、路径编辑和新建文件夹'
    def __init__(自身,属性):
        '记下 props。构造不画'
        自身.属性=属性#主人与注入
        自身.父层=None#左列
        自身.选中=None#选中的文件夹
        自身.子层=None#右列
        自身.加载中=False#有列举在飞
        自身.慢扫描=False#慢到该显示加载中
        自身.扫描窗=0#每一次列举一个静默窗
        自身.错误=None#列举失败
        自身.路径草稿=None#空表示面包屑，字符串表示正在编辑
        自身.显示隐藏=False#隐藏文件
        自身.文件夹草稿=None#空表示没开新建，字符串表示草稿
        自身.创建中=False#正在创建
        自身.创建错误=None#创建失败
        自身.请求序号=0#后来的列举作废先前的
        自身.扫描控制器=None#当前列举的中止器
        自身.打开世代=0#关掉或重新打开之后，旧的创建结果作废
        自身.已打开=False#上一帧是否开着
        自身.已同步=False#已经处理过打开边沿
        自身.预览挂起=False#提交之后别让防抖再列一次
        自身.已扫描=None#上次草稿跟随扫描
        自身.组合中=False#输入法组合中
        自身.要回焦路径=False#预览落地后焦点回到路径框
        自身.要回焦选中=False#选中后焦点回到那一行
        自身.要回焦编辑区=False#失败或取消后焦点回到编辑区
        自身.要聚焦路径=False#刚打开路径编辑
        自身.绘制中=False#防止重入
        自身.待重画=False#绘制中又要求重画
        自身.根=None#模态罩
        自身.卡=None#对话框卡片
        自身.主拆除=None#主对话框键盘层
        自身.创建根=None#新建文件夹罩
        自身.创建卡=None#新建文件夹卡片
        自身.创建拆除=None#新建文件夹键盘层
        自身.路径输入=None#路径框
        自身.创建输入=None#文件夹名框
        自身.编辑区按钮=None#面包屑右侧编辑区
        自身.面包屑轨=None#面包屑
        自身.米勒行=None#两列
        自身.慢定时=None#慢扫描定时
        自身.预览定时=None#草稿防抖
        自身.后定时=None#布局后钉滚动
        自身.已安排草稿=未安排#上次安排预览时的草稿
        自身.已安排慢=None#上次安排慢扫描的键
        自身.已钉屑尾=未安排#上次钉住的面包屑尾
        自身.已钉子路径=未安排#上次钉住的子栏
        自身.选区=None#重画前从输入框读到的选区

    def 更新(自身,属性):
        '换上最新 props'
        自身.属性=属性#最新

    def 窗口(自身):
        '当前浏览器窗口'
        窗=自身.属性.get('window')#调用方给的
        if 窗 is None:#没有
            return 取握手窗口()#当前窗口
        return 窗#用给的

    def 文档(自身):
        '当前文档'
        return 自身.窗口().document#文档

    def 卸载(自身):
        '槽位卸下：作废在飞请求并拆掉界面'
        自身.请求序号+=1#旧结果作废
        自身.打开世代+=1#旧创建作废
        if 自身.扫描控制器 is not None:#还有控制器
            自身.扫描控制器.abort()#中止
            自身.扫描控制器=None#丢掉
        自身.已打开=False#视为关上
        自身.已同步=False#下次当新的一次打开
        自身.拆壳()#拆节点

    def 清定时(自身):
        '停掉慢扫描、草稿预览和滚动钉'
        窗口=自身.窗口()#窗口
        if 自身.慢定时 is not None:#慢扫描还在
            窗口.clearTimeout(自身.慢定时)#停
            自身.慢定时=None#丢掉
        if 自身.预览定时 is not None:#预览还在
            窗口.clearTimeout(自身.预览定时)#停
            自身.预览定时=None#丢掉
        if 自身.后定时 is not None:#滚动钉还在
            窗口.clearTimeout(自身.后定时)#停
            自身.后定时=None#丢掉

    def 拆创建(自身):
        '卸下新建文件夹对话框'
        if 自身.创建拆除 is not None:#键盘层还在
            拆=自身.创建拆除#拆除器
            自身.创建拆除=None#先丢掉
            拆()#卸下
        if 自身.创建根 is not None:#节点还在
            自身.创建根.remove()#拆掉
            自身.创建根=None#丢掉
        自身.创建卡=None#卡片
        自身.创建输入=None#输入框

    def 拆壳(自身):
        '卸下两个对话框和定时器'
        自身.清定时()#定时器
        if 自身.主拆除 is not None:#主键盘层
            拆=自身.主拆除#拆除器
            自身.主拆除=None#先丢掉
            拆()#卸下
        自身.拆创建()#新建文件夹
        if 自身.根 is not None:#主罩还在
            自身.根.remove()#拆掉
            自身.根=None#丢掉
        自身.卡=None#卡片
        自身.路径输入=None#路径框
        自身.编辑区按钮=None#编辑区
        自身.面包屑轨=None#面包屑
        自身.米勒行=None#两列

    def 取代(自身):
        '后来的操作作废上一次列举，并中止它'
        if 自身.扫描控制器 is not None:#上一次还在
            自身.扫描控制器.abort()#中止
            自身.扫描控制器=None#丢掉
        自身.请求序号+=1#新序号
        return 自身.请求序号#当前序号

    def 新控制器(自身):
        '换一个可中止的列举，并重开慢扫描的静默窗'
        控制器=自身.窗口().AbortController()#新的
        自身.扫描控制器=控制器#当前
        自身.慢扫描=False#先藏起加载提示
        自身.扫描窗+=1#新的静默窗
        return 控制器#控制器

    def 启动列举(自身,路径):
        '作废上一次，再列这一层。路径空着就是主目录'
        序号=自身.取代()#新序号
        控制器=自身.新控制器()#这一次
        try:#同步取回
            列举=取同步结果(自身.属性['listDirectory'](路径,控制器.signal))#列表
        except Exception as 错:#失败
            return {'序号':序号,'列举':None,'错误':错}#带错误
        return {'序号':序号,'列举':列举,'错误':None}#成功

    def 落单栏(自身,目标,关编辑):
        '只留下目标这一层'
        自身.父层=目标#整宽一列
        自身.选中=None#没有选中
        自身.子层=None#没有右列
        自身.收尾着陆(关编辑)#结束加载

    def 收尾着陆(自身,关编辑):
        '这一次落地结束。提交的路径会关掉编辑'
        自身.加载中=False#不再加载
        自身.慢扫描=False#藏起提示
        if 关编辑:#提交落地
            自身.路径草稿=None#回到面包屑
            return#停
        自身.错误=None#预览落地清掉旧错误
        自身.要回焦路径=True#焦点回到路径框

    def 着陆(自身,路径,关编辑,宣告):
        '列目标层。离显示根两层以上时，父层对得上就一次落成两栏'
        发出=自身.启动列举(路径)#目标层
        序号=发出['序号']#这次的序号
        自身.加载中=True#在飞
        if 宣告:#提交才清掉旧错误
            自身.错误=None#先清
        if 发出['错误'] is not None:#目标层失败
            if 序号!=自身.请求序号:#已被取代
                return#丢掉
            自身.加载中=False#结束
            自身.慢扫描=False#藏起
            if 宣告:#要告诉人
                自身.错误=失败文案(发出['错误'])#失败句
            return#停
        if 序号!=自身.请求序号:#已被取代
            return#丢掉
        目标=发出['列举']#目标列表
        if not 关编辑 and 路径 is not None:#草稿跟随记下宿主落下的路径
            自身.已扫描={'directory':路径,'landed':目标['path']}#对得上
        if len(展示面包屑(目标,''))<2:#就在显示根
            自身.落单栏(目标,关编辑)#一列
            return#停
        屑=目标['crumbs']#原始谱系
        if len(屑)<2:#没有父层
            自身.落单栏(目标,关编辑)#一列
            return#停
        父屑=屑[-2]#父层面包屑
        控制器=自身.新控制器()#父层这一次
        try:#父层失败不展示
            父层=取同步结果(自身.属性['listDirectory'](父屑['path'],控制器.signal))#父层列表
        except Exception as 父层错误:#父层没列出来，不展示这个错误
            if 序号!=自身.请求序号:#已被取代
                return#丢掉
            自身.落单栏(目标,关编辑)#只留目标
            return#停
        if 序号!=自身.请求序号:#已被取代
            return#丢掉
        分隔=分隔符于(父层)#平台
        def 折(值):
            'Windows 比较路径时忽略大小写'
            if 分隔=='\\':#Windows
                return 值.lower()#小写
            return 值#原样
        命中=None#父层里的目标
        for 条目 in 父层['entries']:#逐条
            if 折(条目['path'])==折(目标['path']):#就是目标
                命中=条目#记下
                break#停
        if 命中 is None:#父层窗口里没有目标
            自身.落单栏(目标,关编辑)#不留下悬空选中
            return#停
        自身.父层=父层#左列
        自身.选中=命中#选中目标
        自身.子层=目标#右列
        自身.收尾着陆(关编辑)#结束

    def 导航(自身,路径=None):
        '提交一条路径。编辑关掉，失败要说出来'
        自身.着陆(路径,True,True)#提交

    def 选定(自身,条目):
        '立刻记上选中，再列它的子层'
        发出=自身.启动列举(条目['path'])#子层
        if 自身.路径草稿 is not None:#编辑中选了一行
            自身.要回焦选中=True#焦点回到这一行
        自身.路径草稿=None#关掉编辑
        自身.选中=条目#选中
        自身.子层=None#等子层
        自身.加载中=True#在飞
        自身.错误=None#清掉旧错误
        if 发出['错误'] is not None:#子层失败
            if 发出['序号']!=自身.请求序号:#已被取代
                return#丢掉
            自身.加载中=False#结束
            自身.慢扫描=False#藏起
            自身.错误=失败文案(发出['错误'])#失败句
            自身.选中=None#不能留着这个选中
            自身.要回焦编辑区=True#焦点回到编辑区
            return#停
        if 发出['序号']!=自身.请求序号:#已被取代
            return#丢掉
        自身.子层=发出['列举']#右列
        自身.加载中=False#结束
        自身.慢扫描=False#藏起

    def 取消路径编辑(自身):
        '作废编辑期间发出的列举，回到面包屑'
        自身.取代()#在飞的结果不许再落地
        自身.加载中=False#不再加载
        自身.慢扫描=False#藏起
        自身.路径草稿=None#回到面包屑
        自身.错误=None#清掉
        if 自身.子层 is None:#选中没有预览
            自身.选中=None#回到一列
        if 自身.父层 is None:#主目录还没列出来
            自身.导航()#重新列主目录

    def 目标路径(自身):
        '打开或新建所作用的目录：选中优先，否则当前层'
        if 自身.选中 is not None:#有选中
            return 自身.选中['path']#选中
        if 自身.父层 is not None:#有当前层
            return 自身.父层['path']#当前层
        return None#还没有

    def 确认创建(自身):
        '在目标下建出这个文件夹，并选中它'
        目标=自身.目标路径()#建在哪
        if 目标 is None or 自身.文件夹草稿 is None or 自身.创建中:#不能建
            return#停
        名=自身.文件夹草稿#原样交给宿主
        if 名.strip()=='':#全是空白
            return#不建
        自身.创建中=True#在建
        自身.创建错误=None#清掉
        世代=自身.打开世代#这一次打开
        try:#同步创建
            新路径=取同步结果(自身.属性['createDirectory'](目标,名))#新路径
        except Exception as 原因:#创建失败
            if 世代!=自身.打开世代:#已经重开过
                return#丢掉
            自身.创建中=False#结束
            自身.创建错误=失败文案(原因)#失败句
            自身.渲染()#重画
            return#停
        if 世代!=自身.打开世代:#已经重开过
            return#丢掉
        自身.创建中=False#结束
        自身.文件夹草稿=None#关掉新建框
        发出=自身.启动列举(目标)#回到目标层
        自身.加载中=True#在飞
        自身.错误=None#清掉旧错误
        if 发出['错误'] is not None:#目标层失败
            if 发出['序号']==自身.请求序号:#还是这一次
                自身.加载中=False#结束
                自身.慢扫描=False#藏起
                自身.错误=失败文案(发出['错误'])#失败句
            自身.渲染()#重画
            return#停
        if 发出['序号']!=自身.请求序号:#已被取代
            自身.渲染()#重画
            return#停
        自身.父层=发出['列举']#目标层成为当前层
        自身.加载中=False#结束
        自身.慢扫描=False#藏起
        自身.选定({'name':名,'path':新路径,'hidden':False})#选中新建的
        自身.渲染()#重画

    def 请求关闭(自身):
        '遮罩或 Escape。新建框开着，或主人正在采纳时，不关'
        if 自身.文件夹草稿 is not None or 自身.属性.get('busy'):#让上面的框或采纳先结束
            return#不关
        自身.属性['onClose']()#取消

    def 请求关创建(自身):
        '新建框的遮罩。正在创建时不关'
        if 自身.创建中:#还在创建
            return#不关
        自身.文件夹草稿=None#关掉
        自身.渲染()#重画

    def 同步打开(自身):
        '打开边沿回到主目录。关上时作废在飞结果'
        开=True if 自身.属性.get('open') else False#现在是否打开
        if 自身.已同步 and 开==自身.已打开:#没变
            return#停
        自身.已同步=True#处理过
        自身.已打开=开#记下
        自身.打开世代+=1#旧创建作废
        if 开:#刚打开
            自身.父层=None#清空
            自身.选中=None#清空
            自身.子层=None#清空
            自身.创建中=False#不在创建
            自身.显示隐藏=False#隐藏文件重新关上
            自身.加载中=False#等导航自己打开
            自身.慢扫描=False#藏起
            自身.错误=None#清空
            自身.路径草稿=None#面包屑
            自身.文件夹草稿=None#不新建
            自身.创建错误=None#清空
            自身.要回焦选中=False#不安置
            自身.要回焦编辑区=False#不安置
            自身.要回焦路径=False#不安置
            自身.要聚焦路径=False#不安置
            自身.预览挂起=False#允许预览
            自身.已扫描=None#没有旧扫描
            自身.导航()#列主目录
            return#停
        自身.取代()#在飞的不许再落地
        自身.加载中=False#不再加载
        自身.慢扫描=False#藏起
        自身.错误=None#清空
        自身.路径草稿=None#清空
        自身.文件夹草稿=None#清空
        自身.创建错误=None#清空
        自身.要回焦选中=False#不安置
        自身.要回焦编辑区=False#不安置
        自身.要回焦路径=False#不安置
        自身.拆壳()#拆掉

    def 记下选区(自身):
        '重画前，若焦点在输入框里，把选区读回来'
        活动=自身.文档().activeElement#当前焦点
        自身.选区=None#先清
        if 活动 is None:#没有焦点
            return#停
        if 自身.路径输入 is not None and 活动 is 自身.路径输入:#在路径框
            自身.选区={'种类':'路径','起':getattr(活动,'selectionStart',None),'止':getattr(活动,'selectionEnd',None)}#选区
            return#停
        if 自身.创建输入 is not None and 活动 is 自身.创建输入:#在文件夹名框
            自身.选区={'种类':'创建','起':getattr(活动,'selectionStart',None),'止':getattr(活动,'selectionEnd',None)}#选区

    def 还回选区(自身):
        '重画后把选区放回对应输入框'
        快照=自身.选区#读到的
        自身.选区=None#用掉
        if 快照 is None:#没有
            return#停
        框=自身.路径输入 if 快照['种类']=='路径' else 自身.创建输入#对应框
        if 框 is None:#这只框没了
            return#停
        框.focus()#放回焦点
        起=快照['起']#起点
        止=快照['止']#终点
        if type(起) in (int,float) and type(止) in (int,float):#读到了数字
            框.setSelectionRange(int(起),int(止))#放回

    def 安排慢扫描(自身):
        '加载跨过静默窗才显示加载中'
        键=(自身.加载中,自身.扫描窗)#这一窗
        if 键==自身.已安排慢:#没变
            return#停
        自身.已安排慢=键#记下
        窗口=自身.窗口()#窗口
        if 自身.慢定时 is not None:#旧的
            窗口.clearTimeout(自身.慢定时)#停
            自身.慢定时=None#丢掉
        if not 自身.加载中:#已经结束
            return#不亮
        窗=自身.扫描窗#这一窗
        def 到时():
            '静默窗过了仍在加载，才亮出提示'
            if 自身.加载中 and 自身.扫描窗==窗:#还是这一次
                自身.慢扫描=True#亮
                自身.渲染()#重画
        自身.慢定时=窗口.setTimeout(到时,慢扫描延迟毫秒)#静默

    def 安排草稿预览(自身):
        '草稿变了才重开防抖。停键后若这一层答不上目录，就去列它'
        if 自身.已安排草稿==自身.路径草稿:#没变
            return#停
        自身.已安排草稿=自身.路径草稿#记下
        窗口=自身.窗口()#窗口
        if 自身.预览定时 is not None:#旧的
            窗口.clearTimeout(自身.预览定时)#停
            自身.预览定时=None#丢掉
        if 自身.路径草稿 is None:#不在编辑
            return#不列
        def 到时():
            '防抖结束，按当时的栏位决定要不要列'
            if 自身.预览挂起:#提交占着
                return#不列
            当前=自身.子层 if 自身.子层 is not None else 自身.父层#最后一栏
            if 当前 is None:#还没有栏
                return#不列
            读=读草稿(当前,自身.路径草稿,自身.已扫描)#目录和尾
            if 读['directory'] is None or 读['tail'] is not None:#没有目录，或这一层已经答上
                return#不列
            自身.着陆(读['directory'],False,False)#跟随，不关编辑，失败不宣告
            自身.渲染()#重画
        自身.预览定时=窗口.setTimeout(到时,草稿预览防抖毫秒)#防抖

    def 安置焦点(自身):
        '编辑结束之后，把焦点放回行或编辑区'
        文档=自身.文档()#文档
        if 自身.要回焦路径:#预览落地
            自身.要回焦路径=False#用掉
            if 文档.activeElement is 文档.body and 自身.路径输入 is not None:#焦点掉到页面
                自身.路径输入.focus()#回到路径框
        if 自身.路径草稿 is not None:#还在编辑
            return#留给路径框
        if 自身.要回焦选中:#选中了一行
            自身.要回焦选中=False#用掉
            自身.要回焦编辑区=False#不用编辑区
            if 自身.米勒行 is None:#没有列
                return#停
            行=自身.米勒行.querySelector('button[aria-current="true"]')#当前行
            if 行 is None:#没有
                return#停
            行.focus()#放上
            return#停
        if 自身.要回焦编辑区:#选中失败或取消
            自身.要回焦编辑区=False#用掉
            if 文档.activeElement is not 文档.body:#焦点还在别人那
                return#不动
            if 自身.编辑区按钮 is None:#没有编辑区
                return#停
            自身.编辑区按钮.focus()#放上

    def 做按钮(自身,窗口,变体,文案,点下,禁用=False,类名=None,图标名=None,图标尺寸=None):
        '用共享按钮画一个动作。图标插在文字前面'
        属性={'window':窗口,'variant':变体,'children':文案,'disabled':禁用,'onClick':点下}#按钮
        if isinstance(类名,str) and 类名!='':#附加类
            属性['className']=类名#官方类名
        钮=按钮(属性).渲染()#画
        if 钮 is None:#没画出来
            return None#空
        if isinstance(类名,str) and 类名!='':#本模块的类
            标样式模块(钮,样式模块)#接上
        if 图标名 is not None:#前导图标
            图=画图标(窗口,图标名,图标尺寸)#图标
            if 图 is not None:#有
                if 钮.firstChild is not None:#已有文字
                    钮.insertBefore(图,钮.firstChild)#放前面
                else:#没有文字
                    钮.appendChild(图)#放入
        return 钮#按钮

    def 绑输入法(自身,框):
        '组合期间不要把 Enter 当成提交'
        def 开始(事件):
            '进入组合'
            自身.组合中=True#开
        def 结束(事件):
            '组合结束'
            自身.组合中=False#关
        框.addEventListener('compositionstart',开始)#开始
        框.addEventListener('compositionend',结束)#结束

    def 确保壳(自身,文档):
        '主对话框的罩、遮罩和卡片只建一次'
        if 自身.根 is not None:#已经在
            自身.卡.setAttribute('aria-label','选择工作区目录')#标题
            return#停
        根=文档.createElement('div')#罩
        根.className='root'#共享模态罩
        根.setAttribute('role','presentation')#不参与无障碍树
        罩=文档.createElement('div')#遮罩
        罩.className='mask'#共享遮罩
        罩.setAttribute('aria-hidden','true')#装饰
        def 点罩(事件):
            '点遮罩等于取消'
            自身.请求关闭()#取消
        罩.addEventListener('click',点罩)#点击
        卡=文档.createElement('div')#卡片
        卡.className='dialog'#共享卡片，也是本模块的 dialog
        挂(卡,'dialog')#本模块尺寸
        卡.tabIndex=-1#可落到卡片
        卡.setAttribute('role','dialog')#对话框
        卡.setAttribute('aria-modal','true')#模态
        卡.setAttribute('aria-label','选择工作区目录')#标题
        根.appendChild(罩)#遮罩
        根.appendChild(卡)#卡片
        文档.body.appendChild(根)#送到页面
        自身.根=根#留下
        自身.卡=卡#留下
        自身.主拆除=使用模态层(卡,True,自身.请求关闭)#Escape 和 Tab

    def 填创建(自身,文档,窗口):
        '填新建文件夹对话框里的标题、名字和按钮'
        清空(自身.创建卡)#旧内容
        自身.创建卡.setAttribute('aria-label','新建文件夹')#标题
        体=文档.createElement('div')#正文
        挂(体,'createBody')#正文样式
        题=文档.createElement('h3')#标题
        挂(题,'createTitle')#标题样式
        题.textContent='新建文件夹'#标题
        体.appendChild(题)#放入
        if 自身.选中 is not None:#建在选中里
            目标名=自身.选中['name']#文件夹名
        elif 自身.父层 is None:#还没有层
            目标名=''#空
        else:#建在当前层
            屑=展示面包屑(自身.父层,'主目录')#面包屑
            目标名=屑[-1]['name'] if len(屑)>0 else 自身.父层['path']#最后一层
        句=文档.createElement('p')#说明
        挂(句,'createIn')#说明样式
        句.textContent='在"{name}"中新建文件夹'.replace('{name}',目标名)#填上名字
        体.appendChild(句)#放入
        框=文档.createElement('input')#名字
        挂(框,'createInput')#输入样式
        框.value=自身.文件夹草稿 if 自身.文件夹草稿 is not None else ''#草稿
        框.setAttribute('aria-label','文件夹名称')#名称
        框.setAttribute('placeholder','未命名文件夹')#占位
        框.setAttribute('data-modal-autofocus','')#打开时落这里
        框.disabled=自身.创建中#创建中不能改
        def 改名(事件):
            '从输入框读回文件夹名'
            自身.文件夹草稿=事件.target.value#草稿
        框.addEventListener('input',改名)#输入
        自身.绑输入法(框)#组合
        def 名键(事件):
            'Enter 创建，Escape 关掉新建框'
            if getattr(事件,'key',None)=='Enter' and not 自身.组合中:#提交
                事件.preventDefault()#不换行
                自身.确认创建()#创建
                return#停
            if getattr(事件,'key',None)=='Escape':#关掉
                事件.stopPropagation()#别再关外面的框
                if not 自身.创建中:#没在创建
                    自身.文件夹草稿=None#关掉
                    自身.渲染()#重画
        框.addEventListener('keydown',名键)#按键
        体.appendChild(框)#放入
        自身.创建输入=框#留下
        if 自身.创建错误 is not None:#有失败
            警=文档.createElement('div')#失败
            挂(警,'error')#失败样式
            警.setAttribute('role','alert')#提示
            警.textContent=自身.创建错误#句子
            体.appendChild(警)#放入
        行=文档.createElement('div')#按钮行
        挂(行,'createActions')#行样式
        def 点取消():
            '不新建'
            自身.文件夹草稿=None#关掉
            自身.渲染()#重画
        取消钮=自身.做按钮(窗口,'outline','取消',点取消,自身.创建中)#取消
        if 取消钮 is not None:#有
            行.appendChild(取消钮)#放入
        不能建=自身.创建中 or 自身.文件夹草稿 is None or 自身.文件夹草稿.strip()==''#空名字
        创建钮=自身.做按钮(窗口,'primary','创建',自身.确认创建,不能建)#创建
        if 创建钮 is not None:#有
            行.appendChild(创建钮)#放入
        体.appendChild(行)#放入
        自身.创建卡.appendChild(体)#放进卡片

    def 确保创建(自身,文档,窗口):
        '文件夹草稿不是空时才有新建框'
        if 自身.文件夹草稿 is None:#没开
            自身.拆创建()#卸下
            return#停
        初次=自身.创建根 is None#第一次
        if 初次:#建壳
            根=文档.createElement('div')#罩
            根.className='root'#共享罩
            根.setAttribute('role','presentation')#不参与
            罩=文档.createElement('div')#遮罩
            罩.className='mask'#遮罩
            罩.setAttribute('aria-hidden','true')#装饰
            def 点罩(事件):
                '点遮罩关掉新建框'
                自身.请求关创建()#关
            罩.addEventListener('click',点罩)#点击
            卡=文档.createElement('div')#卡片
            卡.className='dialog createDialog'#共享卡片加新建框
            挂(卡,'dialog createDialog')#两类都接上
            卡.style.height='auto'#不要用主对话框的高度
            卡.tabIndex=-1#可落到卡片
            卡.setAttribute('role','dialog')#对话框
            卡.setAttribute('aria-modal','true')#模态
            根.appendChild(罩)#遮罩
            根.appendChild(卡)#卡片
            文档.body.appendChild(根)#送到页面
            自身.创建根=根#留下
            自身.创建卡=卡#留下
        卡片=自身.创建卡#卡片
        卡片.className='dialog createDialog'#类名
        挂(卡片,'dialog createDialog')#重新接上
        卡片.style.height='auto'#高度
        自身.填创建(文档,窗口)#内容
        if 初次:#内容好了再抢键盘
            自身.创建拆除=使用模态层(自身.创建卡,True,自身.请求关创建)#Escape 和 Tab

    def 画开着(自身):
        '对话框开着时，按当前状态填卡片'
        if not 自身.加载中:#已经不在加载
            自身.慢扫描=False#不要留着提示
        文档=自身.文档()#文档
        窗口=自身.窗口()#窗口
        确保样式(文档)#样式
        自身.记下选区()#先读选区
        旧屑左=自身.面包屑轨.scrollLeft if 自身.面包屑轨 is not None else 0#面包屑滚动
        旧行左=自身.米勒行.scrollLeft if 自身.米勒行 is not None else 0#两列横向滚动
        旧列顶=[]#各列纵向滚动
        if 自身.米勒行 is not None:#有列
            for 列 in 自身.米勒行.querySelectorAll('.column'):#每一列
                旧列顶.append(列.scrollTop)#记下
        自身.确保壳(文档)#主壳
        清空(自身.卡)#重填
        范围=文档.createElement('div')#编辑范围
        挂(范围,'editorScope')#不占布局
        def 范围按键(事件):
            '编辑路径时，Escape 只收起编辑'
            if getattr(事件,'key',None)!='Escape' or 自身.路径草稿 is None:#不是这条
                return#放行
            事件.stopPropagation()#别关对话框
            自身.要回焦编辑区=文档.activeElement is 自身.路径输入#焦点原本在输入框
            自身.取消路径编辑()#收起
            自身.渲染()#重画
        def 范围失焦(事件):
            '焦点离开这张卡片就收起路径编辑'
            if 自身.绘制中 or 自身.路径草稿 is None:#重画或没在编辑
                return#不动
            if not 文档.hasFocus():#窗口没焦点
                return#不动
            卡=事件.currentTarget.closest('[role="dialog"]')#这张卡片
            if 卡 is None:#不在卡片里
                return#不动
            相关=getattr(事件,'relatedTarget',None)#新焦点
            if getattr(相关,'nodeType',None) is not None and 卡.contains(相关):#还在卡片里
                return#不动
            自身.要回焦编辑区=False#不要把焦点拽回来
            自身.取消路径编辑()#收起
            自身.渲染()#重画
        范围.addEventListener('keydown',范围按键)#Escape
        范围.addEventListener('focusout',范围失焦)#离开卡片
        头=文档.createElement('div')#头
        挂(头,'header')#头样式
        题=文档.createElement('h2')#标题
        挂(题,'title')#标题样式
        题.textContent='选择工作区目录'#标题
        头.appendChild(题)#放入
        条=文档.createElement('div')#路径条
        挂(条,'crumbBar')#条样式
        源=自身.子层 if 自身.子层 is not None else 自身.父层#最后一栏
        打前缀=None#过滤尾
        if 源 is not None and 自身.路径草稿 is not None:#正在编辑
            打前缀=读草稿(源,自身.路径草稿,自身.已扫描)['tail']#末段
        面包屑=展示面包屑(源,'主目录') if 源 is not None else []#面包屑
        if 自身.路径草稿 is None:#面包屑模式
            自身.路径输入=None#没有路径框
            轨=文档.createElement('span')#轨迹
            挂(轨,'crumbTrail')#轨迹样式
            轨.setAttribute('role','navigation')#导航
            自身.面包屑轨=轨#留下
            主人忙=自身.属性.get('busy') or 自身.文件夹草稿 is not None#外面的控件让开
            for 序,屑 in enumerate(面包屑):#逐层
                座=文档.createElement('span')#一座
                挂(座,'crumbSeat')#座样式
                if 序>0:#不是第一层
                    箭=画图标(窗口,'chevron-right-14',12,'crumbChevron')#分隔
                    if 箭 is not None:#有
                        座.appendChild(箭)#放入
                屑钮=文档.createElement('button')#这一层
                屑钮.type='button'#按钮
                挂(屑钮,'crumb')#层样式
                屑钮.disabled=主人忙#禁用
                屑钮.textContent=屑['name']#名字
                def 点屑(事件,路径=屑['path']):
                    '跳到这一层'
                    自身.导航(路径)#提交
                    自身.渲染()#重画
                屑钮.addEventListener('click',点屑)#点击
                座.appendChild(屑钮)#放入
                轨.appendChild(座)#放入
            条.appendChild(轨)#放入
            区=文档.createElement('button')#编辑区
            区.type='button'#按钮
            挂(区,'crumbEditZone')#编辑区样式
            区.setAttribute('aria-label','编辑路径')#名称
            区.setAttribute('title','编辑路径')#提示
            区.disabled=主人忙#禁用
            自身.编辑区按钮=区#留下
            def 点编辑(事件):
                '打开路径编辑。没有列出的层就从空草稿开始'
                自身.取代()#旧列举不许关掉编辑
                自身.加载中=False#不再加载
                自身.慢扫描=False#藏起
                自身.预览挂起=False#允许跟随
                自身.要聚焦路径=True#打开后落在输入框
                if 自身.父层 is None:#没有层
                    自身.路径草稿=''#空草稿
                    自身.渲染()#重画
                    return#停
                基=自身.选中['path'] if 自身.选中 is not None else 自身.父层['path']#从选中或当前层起
                分隔=分隔符于(自身.父层)#分隔符
                if not 基.endswith(分隔):#还没以分隔符结束
                    基=基+分隔#补上
                自身.路径草稿=基#草稿
                自身.渲染()#重画
            区.addEventListener('click',点编辑)#点击
            笔=画图标(窗口,'edit-16',14,'crumbEditGlyph')#铅笔
            if 笔 is not None:#有
                区.appendChild(笔)#放入
            条.appendChild(区)#放入
        else:#路径编辑
            自身.面包屑轨=None#没有轨迹
            自身.编辑区按钮=None#没有编辑区
            框=文档.createElement('input')#路径
            挂(框,'pathInput')#输入样式
            框.value=自身.路径草稿#草稿
            框.setAttribute('aria-label','编辑路径')#名称
            主人忙=自身.属性.get('busy') or 自身.文件夹草稿 is not None#让开
            框.disabled=主人忙#禁用
            自身.路径输入=框#留下
            def 改路径(事件):
                '从输入框读回路径，并作废旧的导航'
                自身.取代()#旧结果不许覆盖新字
                自身.加载中=False#不再加载
                自身.慢扫描=False#藏起
                自身.预览挂起=False#新的字可以跟随
                自身.路径草稿=事件.target.value#草稿
                自身.渲染()#重画
            框.addEventListener('input',改路径)#输入
            自身.绑输入法(框)#组合
            def 路径键(事件):
                'Enter 提交当前草稿'
                if getattr(事件,'key',None)!='Enter' or 自身.组合中:#不是提交
                    return#放行
                事件.preventDefault()#不换行
                if 自身.路径草稿 is None or 自身.路径草稿.strip()=='':#空白
                    return#不提交
                自身.要回焦编辑区=True#成功后回到编辑区
                自身.预览挂起=True#防抖不许再抢
                自身.导航(自身.路径草稿)#提交原文
                自身.渲染()#重画
            框.addEventListener('keydown',路径键)#按键
            条.appendChild(框)#放入
        头.appendChild(条)#放入
        范围.appendChild(头)#放入
        内容=文档.createElement('div')#内容
        挂(内容,'content')#内容样式
        行=文档.createElement('div')#两列
        挂(行,'millerRow')#行样式
        自身.米勒行=行#留下
        主人忙=自身.属性.get('busy') or 自身.文件夹草稿 is not None#让开
        编辑中=自身.路径草稿 is not None#正在编辑
        def 点选(条目):
            '左列选中后重画'
            自身.选定(条目)#选中
            自身.渲染()#重画
        def 点进(条目):
            '右列进入一层后重画'
            if 自身.子层 is None:#没有右列
                return#停
            自身.父层=自身.子层#右列升成左列
            自身.选定(条目)#再列新的子层
            自身.渲染()#重画
        if 自身.父层 is not None:#有左列
            左=层级列({#左列
                'window':窗口,#窗口
                'document':文档,#文档
                'entries':自身.父层['entries'],#条目
                'selectedPath':自身.选中['path'] if 自身.选中 is not None else None,#选中
                'busy':主人忙,#禁用
                'onPick':点选,#选中
                'showHidden':自身.显示隐藏,#隐藏
                'filterPrefix':打前缀 if 自身.子层 is None else None,#只有一列时过滤
                'pathEditing':编辑中,#编辑中
            }).渲染()#画
            行.appendChild(左)#放入
        if 自身.选中 is not None:#两列
            隔=文档.createElement('span')#分隔
            挂(隔,'divider')#分隔样式
            行.appendChild(隔)#放入
        if 自身.选中 is not None and 自身.子层 is not None:#有右列
            右=层级列({#右列
                'window':窗口,#窗口
                'document':文档,#文档
                'entries':自身.子层['entries'],#条目
                'selectedPath':None,#右列没有选中
                'busy':主人忙,#禁用
                'onPick':点进,#进入
                'showHidden':自身.显示隐藏,#隐藏
                'filterPrefix':打前缀,#过滤最后一栏
                'pathEditing':编辑中,#编辑中
            }).渲染()#画
            行.appendChild(右)#放入
        内容.appendChild(行)#放入
        if 自身.加载中 and 自身.慢扫描:#慢加载
            载=文档.createElement('div')#提示
            挂(载,拼类('status','loadingFloat'))#浮动
            载.setAttribute('role','status')#状态
            载.textContent='加载中…'#加载中
            内容.appendChild(载)#放入
        父截=自身.父层 is not None and 自身.父层.get('truncated') is True#左列被截
        子截=自身.子层 is not None and 自身.子层.get('truncated') is True#右列被截
        if 父截 or 子截:#有截断
            截=文档.createElement('div')#说明
            挂(截,'status')#状态样式
            截.setAttribute('role','status')#状态
            截.textContent='文件夹过多，仅显示开头部分。'#截断
            内容.appendChild(截)#放入
        if 自身.错误 is not None:#有失败
            警=文档.createElement('div')#失败
            挂(警,'error')#失败样式
            警.setAttribute('role','alert')#提示
            警.textContent=自身.错误#句子
            内容.appendChild(警)#放入
        范围.appendChild(内容)#放入
        脚=文档.createElement('div')#脚
        挂(脚,'footerBar')#脚样式
        不能新建=自身.父层 is None or 自身.加载中 or 主人忙 or 编辑中#不能新建
        def 点新建():
            '打开新建文件夹'
            自身.文件夹草稿=''#空草稿
            自身.创建错误=None#清掉
            自身.渲染()#重画
        新建钮=自身.做按钮(窗口,'outline','新建文件夹',点新建,不能新建,None,'plus-16',14)#新建
        if 新建钮 is not None:#有
            脚.appendChild(新建钮)#放入
        隐=文档.createElement('button')#隐藏文件
        隐.type='button'#按钮
        挂(隐,拼类('showHiddenToggle','showHiddenToggleActive' if 自身.显示隐藏 else ''))#开关样式
        隐.setAttribute('aria-pressed','true' if 自身.显示隐藏 else 'false')#按下
        隐.disabled=主人忙#禁用
        隐.textContent='显示隐藏文件'#标签
        if 编辑中:#不要抢走路径框
            def 隐按下(事件):
                '编辑路径时，切换隐藏文件不要取消编辑'
                事件.preventDefault()#留下焦点
            隐.addEventListener('mousedown',隐按下)#按下
        def 点隐(事件):
            '切换隐藏文件'
            自身.显示隐藏=not 自身.显示隐藏#反过来
            自身.渲染()#重画
        隐.addEventListener('click',点隐)#点击
        if 自身.显示隐藏:#开着才有勾
            勾=图标勾描边常规({'window':窗口,'size':14})#勾
            if 勾 is not None:#有
                隐.appendChild(勾)#放在文字后面
        脚.appendChild(隐)#放入
        隙=文档.createElement('span')#空隙
        挂(隙,'footerGap')#把打开和取消推到右边
        脚.appendChild(隙)#放入
        def 点取消():
            '不选目录'
            自身.属性['onClose']()#取消
        取消钮=自身.做按钮(窗口,'outline','取消',点取消,主人忙,'footerAction')#取消
        if 取消钮 is not None:#有
            脚.appendChild(取消钮)#放入
        目标=自身.目标路径()#打开的目标
        不能打开=目标 is None or 自身.加载中 or 主人忙 or 编辑中#不能打开
        def 点打开():
            '采纳选中，否则采纳当前层'
            路径=自身.目标路径()#目标
            if 路径 is not None:#有目标
                自身.属性['onOpen'](路径)#交给主人
        打开钮=自身.做按钮(窗口,'primary','打开',点打开,不能打开,'footerAction')#打开
        if 打开钮 is not None:#有
            脚.appendChild(打开钮)#放入
        范围.appendChild(脚)#放入
        自身.卡.appendChild(范围)#放进卡片
        新屑尾=面包屑[-1]['path'] if len(面包屑)>0 else None#面包屑尾
        新子=自身.子层['path'] if 自身.子层 is not None else None#子栏
        屑变了=新屑尾!=自身.已钉屑尾#这一次尾变了
        子变了=新子 is not None and 新子!=自身.已钉子路径#这一次子栏变了
        自身.已钉屑尾=新屑尾#记下尾
        自身.已钉子路径=新子#记下子栏
        if 屑变了 and 自身.面包屑轨 is not None:#钉到新尾
            自身.面包屑轨.scrollLeft=自身.面包屑轨.scrollWidth#钉
        elif 自身.面包屑轨 is not None:#没变
            自身.面包屑轨.scrollLeft=旧屑左#留在原地
        if 子变了:#钉到新子栏
            自身.米勒行.scrollLeft=自身.米勒行.scrollWidth#钉
        else:#没变
            自身.米勒行.scrollLeft=旧行左#留在原地
        列组=自身.米勒行.querySelectorAll('.column')#新列
        序=0#序号
        for 列 in 列组:#逐列
            if 序<len(旧列顶):#有旧位置
                列.scrollTop=旧列顶[序]#放回
            序+=1#下一列
        选区种类=自身.选区['种类'] if isinstance(自身.选区,dict) else None#重画前的焦点
        if 选区种类=='路径':#路径框还在
            自身.还回选区()#放回
        elif 自身.要聚焦路径 and 自身.路径输入 is not None:#刚打开编辑
            自身.路径输入.focus()#落进去
        自身.要聚焦路径=False#用掉
        自身.安置焦点()#行或编辑区
        def 再钉():
            '布局之后再钉一次这一轮变过的滚动'
            if 自身.根 is None:#已经拆了
                return#停
            if 屑变了 and 自身.面包屑轨 is not None:#尾是这一轮变的
                自身.面包屑轨.scrollLeft=自身.面包屑轨.scrollWidth#钉
            if 子变了 and 自身.米勒行 is not None:#子栏是这一轮变的
                自身.米勒行.scrollLeft=自身.米勒行.scrollWidth#钉
        if 自身.后定时 is not None:#旧的
            窗口.clearTimeout(自身.后定时)#停
        自身.后定时=窗口.setTimeout(再钉,0)#布局后
        自身.确保创建(文档,窗口)#新建框
        if 选区种类=='创建':#文件夹名框刚重画完
            自身.还回选区()#放回选区
        自身.安排慢扫描()#加载提示
        自身.安排草稿预览()#路径跟随
        return 自身.根#罩

    def 画出(自身):
        '处理打开边沿，再决定画不画'
        自身.同步打开()#打开或关上
        if not 自身.属性.get('open'):#关着
            return None#不画
        return 自身.画开着()#画

    def 渲染(自身):
        '按当前状态画出或收起。绘制中又来的请求等这一轮结束再画'
        if 自身.绘制中:#重入
            自身.待重画=True#等一下
            return 自身.根#当前
        自身.绘制中=True#开始
        try:#画完放开
            节点=自身.画出()#节点
        finally:#放开
            自身.绘制中=False#结束
        if 自身.待重画:#中间又要画
            自身.待重画=False#用掉
            return 自身.渲染()#再画
        return 节点#节点

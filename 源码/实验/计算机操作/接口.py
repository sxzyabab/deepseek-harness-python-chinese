'记在日志里的原生操作上面的对象门面。调用方拥有求值器持久化'
from ...基础设施.通用工具.序列化编码 import 严格解码base64,紧凑json编码
from .协议 import (
    尝试请求,请求问题消息,参数错误,
    动作结果,应用程序结果,运行应用程序结果,发现应用程序结果,
    悬停结果,截图结果,显示结果,状态结果,窗口结果,能力结果,
)
from .应用程序访问 import 等到

__all__=['创建计算机操作接口','应用程序表面','窗口表面','应用程序','计算机操作接口']

键名={#xdotool 风格修饰键到原生名
    'cmd':'command','command':'command','super':'command','Super_L':'command','Super_R':'command',
    'ctrl':'control','control':'control','Control_L':'control','Control_R':'control',
    'alt':'option','option':'option','Alt_L':'option','Alt_R':'option',
    'shift':'shift','Shift_L':'shift','Shift_R':'shift','fn':'fn',
}#修饰键表结束

def 键和弦(和弦):
    '把加号和弦拆成键名和修饰键。单独的加号也是键名'
    部分=和弦.split('+')#按加号拆
    键=部分.pop() if len(部分)>0 else ''#最后一段是键
    if 键=='' and len(部分)>0 and 部分[-1]=='':#连续加号表示加号键
        键='+'#加号键
        部分.pop()#去掉空段
    if not 键:#没有键名
        raise Exception('A key chord must end with a key name')#拒绝
    修饰=[]#修饰键
    for 段 in 部分:#前面的都是修饰键
        if 段 not in 键名:#不认识
            raise Exception('Unsupported key modifier: '+段)#拒绝
        修饰.append(键名[段])#换成原生名
    return 键,修饰#键和修饰键

def 选项值(选项,键):
    '缺席与显式空都当成没有这个选项'
    if 选项 is None:#没有选项
        return None#没有
    if isinstance(选项,dict):#字典
        if 键 not in 选项:#缺席
            return None#没有
        return 选项[键]#值
    if not hasattr(选项,键):#对象上没有
        return None#没有
    return getattr(选项,键)#值

def 要发出(选项):
    '只有显式 false 才不发给汇聚端'
    return 选项值(选项,'emit') is not False#缺省发出

def 是点(目标):
    '坐标目标是两个数'
    return isinstance(目标,(list,tuple)) and len(目标)==2#两个数

def 调用(派发,方法,参数):
    '先按操作模式检查，失败说明只讲参数'
    成功,数据,问题列表=尝试请求({'method':方法,'params':参数})#检查
    if not 成功:#没过
        raise 参数错误(方法+' '+请求问题消息(问题列表))#带上方法名
    return 派发(数据)#一次派发，失败不重试

def 动作(派发,方法,参数):
    '动作结果必须是已调度且未核实'
    return 动作结果(调用(派发,方法,参数))#校验

def 发出文本(汇聚,值):
    '汇聚端可以同步返回，也可以返回期约'
    if 汇聚 is None:#没有汇聚端
        return#不发
    等到(汇聚.text(值))#发出

def 发出图像(汇聚,截图):
    '汇聚端可以同步返回，也可以返回期约'
    if 汇聚 is None:#没有汇聚端
        return#不发
    等到(汇聚.image(截图))#发出

class 应用程序表面:
    '应用程序范围或显式窗口上的观察与动作'

    def __init__(自身,派发,汇聚,句柄,进程号,窗口标识=None):
        '钉住句柄。窗口标识缺省时从最近一次观察里选窗口'
        自身._派发=派发#已授权的派发
        自身._汇聚=汇聚#可选输出
        自身._句柄=句柄#应用程序句柄
        自身._进程号=进程号#进程号
        自身._窗口标识=窗口标识#显式窗口
        自身._已观察=None#最近一次成功的辅助功能树

    def _快照参数(自身):
        '元素动作必须先读过这一面的树'
        if 自身._已观察 is None:#还没有树
            raise Exception('Read getAXState before using this surface')#先读
        return {'appHandle':自身._句柄,'snapshotId':自身._已观察['snapshotId']}#快照身份

    def _窗口(自身):
        '显式窗口优先，否则用焦点上的非零窗口，再否则必须恰好一个'
        if 自身._窗口标识 is not None:#显式窗口
            return 自身._窗口标识#那个窗口
        窗口列表=None#屏上的非零窗口
        if 自身._已观察 is not None:#有观察
            窗口列表=[窗口 for 窗口 in 自身._已观察['windows'] if 窗口['isOnScreen'] and 窗口['bounds']['width']>0 and 窗口['bounds']['height']>0]#可用窗口
        焦点=None#焦点窗口
        if 窗口列表 is not None:#有候选
            for 窗口 in 窗口列表:#找焦点
                if 窗口['windowId']==自身._已观察.get('focusedWindowId'):#对上
                    焦点=窗口#记下
                    break#停
        if 焦点 is not None:#有焦点
            return 焦点['windowId']#焦点窗口
        if 窗口列表 is None or len(窗口列表)!=1:#没有唯一窗口
            raise Exception('Select a window with app.getWindows() and app.getWindow(windowId) before this operation')#先选定窗口
        return 窗口列表[0]['windowId']#唯一窗口

    def show(自身):
        '取消隐藏并恢复最小化窗口，不请求激活'
        参数={'appHandle':自身._句柄}#应用程序
        if 自身._窗口标识 is not None:#显式窗口
            参数['windowId']=自身._窗口标识#带上
        return 显示结果(调用(自身._派发,'show',参数))#调度证据

    def getAXState(自身,选项=None):
        '读取新的辅助功能文本。菜单默认折叠'
        自身._已观察=None#失败不能留着旧树
        参数={'appHandle':自身._句柄}#应用程序
        if 自身._窗口标识 is not None:#显式窗口
            参数['windowId']=自身._窗口标识#带上
        if 选项值(选项,'includeMenus') is not None:#调用方写了菜单开关
            参数['includeMenus']=选项值(选项,'includeMenus')#带上
        if 选项值(选项,'details') is not None:#调用方写了细节开关
            参数['details']=选项值(选项,'details')#带上
        状态=状态结果(调用(自身._派发,'getState',参数))#校验
        期望窗口=自身._窗口标识 if 自身._窗口标识 is not None else None#显式窗口或空
        if 状态['appHandle']!=自身._句柄 or 状态['pid']!=自身._进程号 or 状态['windowId']!=期望窗口:#不是这一面
            raise Exception('Native observation belongs to another application or window')#拒绝
        if any(窗口['pid']!=自身._进程号 for 窗口 in 状态['windows']):#窗口属于别的进程
            raise Exception('Native windows belong to another application')#拒绝
        自身._已观察=状态#留下
        if 要发出(选项):#默认发出树文本
            发出文本(自身._汇聚,状态['tree'])#文本，不是整份状态对象
        return 状态['tree']#树文本

    def getScreenshot(自身,选项=None):
        '捕获选定窗口。使用返回的 mimeType，不要假设是 PNG'
        if 自身._已观察 is None:#还没有树
            自身.getAXState({'emit':False})#先读，不重复发出
        目标=自身._窗口()#窗口
        图像=截图结果(调用(自身._派发,'screenshot',{'appHandle':自身._句柄,'windowId':目标}))#校验
        if 图像['windowId']!=目标:#不是这个窗口
            raise Exception('Native screenshot belongs to another window')#拒绝
        截图={#模型请求图像
            'bytes':严格解码base64(图像['data']),#字节
            'mimeType':图像['mimeType'],#媒体类型
            'pixelWidth':图像['pixelWidth'],#宽
            'pixelHeight':图像['pixelHeight'],#高
            'windowId':图像['windowId'],#窗口
        }#截图结束
        if 要发出(选项):#默认发给汇聚端
            发出图像(自身._汇聚,截图)#图像
        return 截图#截图

    def getAXStateAndScreenshot(自身,选项=None):
        '先读辅助功能再截图。两次观察不是原子的'
        状态=自身.getAXState(选项)#树
        return {'state':状态,'screenshot':自身.getScreenshot(选项)}#两份

    def hover(自身,目标,选项=None):
        '优先用辅助功能的备用界面，否则移动系统指针且不按下'
        参数=自身._快照参数()#快照
        if 选项值(选项,'relative') is not None:#只对坐标目标有意义，元素索引带上会在模式里被拒绝
            参数['relative']=选项值(选项,'relative')#带上
        if not 是点(目标):#元素索引
            参数['elementIndex']=目标#索引
        else:#坐标
            参数['windowId']=自身._窗口()#窗口
            参数['x']=目标[0]#横坐标
            参数['y']=目标[1]#纵坐标
        return 悬停结果(调用(自身._派发,'hover',参数))#路线

    def click(自身,目标,选项=None):
        '点击元素索引或截图局部坐标'
        按钮='left' if 选项值(选项,'mouseButton') is None else 选项值(选项,'mouseButton')#缺省左键
        次数=1 if 选项值(选项,'clickCount') is None else 选项值(选项,'clickCount')#缺省单击
        if 按钮!='left' and 次数!=1:#只有左键能双击
            raise Exception('Only left double-click is supported')#拒绝
        参数=自身._快照参数()#快照
        if 选项值(选项,'modifiers') is not None:#有修饰键
            参数['modifiers']=list(选项值(选项,'modifiers'))#拷贝
        if 选项值(选项,'relative') is not None:#坐标模式
            参数['relative']=选项值(选项,'relative')#带上
        if not 是点(目标):#元素索引
            参数['elementIndex']=目标#索引
            if 按钮!='left':#不是左键才写
                参数['mouseButton']=按钮#按钮
            if 次数!=1:#不是单击才写
                参数['clickCount']=次数#次数
        else:#坐标始终写按钮和次数
            参数['windowId']=自身._窗口()#窗口
            参数['x']=目标[0]#横坐标
            参数['y']=目标[1]#纵坐标
            参数['mouseButton']=按钮#按钮
            参数['clickCount']=次数#次数
        return 动作(自身._派发,'click',参数)#调度证据

    def setValue(自身,索引,值):
        '设置观察到的控件值'
        参数=自身._快照参数()#快照
        参数['elementIndex']=索引#索引
        参数['value']=值#新值
        return 动作(自身._派发,'setValue',参数)#调度证据

    def selectText(自身,索引,文本,选项=None):
        '选择唯一一段字面文本，或把光标放在它前面或后面'
        参数=自身._快照参数()#快照
        参数['elementIndex']=索引#索引
        参数['text']=文本#文本
        if 选项值(选项,'prefix') is not None:#前缀
            参数['prefix']=选项值(选项,'prefix')#带上
        if 选项值(选项,'suffix') is not None:#后缀
            参数['suffix']=选项值(选项,'suffix')#带上
        if 选项值(选项,'selectionType') is not None:#放置
            参数['selectionType']=选项值(选项,'selectionType')#带上
        return 动作(自身._派发,'selectText',参数)#调度证据

    def performSecondaryAction(自身,索引,动作名):
        '调用观察到的元素公布的动作。raise 会激活应用程序'
        参数=自身._快照参数()#快照
        参数['elementIndex']=索引#索引
        参数['action']=动作名#动作名
        return 动作(自身._派发,'performSecondaryAction',参数)#调度证据

    def scroll(自身,选项):
        '在截图局部的点或整数比例上滚动。至少一个增量非零'
        if 选项['deltaLinesX']==0 and 选项['deltaLinesY']==0:#都是零
            raise Exception('At least one scroll delta must be nonzero')#拒绝
        参数=自身._快照参数()#快照
        参数['windowId']=自身._窗口()#窗口
        参数['x']=选项['x']#横坐标
        参数['y']=选项['y']#纵坐标
        参数['deltaLinesX']=选项['deltaLinesX']#横向
        参数['deltaLinesY']=选项['deltaLinesY']#纵向
        if 'relative' in 选项 and 选项['relative'] is not None:#坐标模式
            参数['relative']=选项['relative']#带上
        return 动作(自身._派发,'scroll',参数)#调度证据

    def drag(自身,起点,终点,选项=None):
        '在同一个窗口里按住选定的按钮和修饰键拖拽'
        参数=自身._快照参数()#快照
        参数['windowId']=自身._窗口()#窗口
        参数['fromX']=起点[0]#起点横坐标
        参数['fromY']=起点[1]#起点纵坐标
        参数['toX']=终点[0]#终点横坐标
        参数['toY']=终点[1]#终点纵坐标
        if 选项值(选项,'relative') is not None:#坐标模式
            参数['relative']=选项值(选项,'relative')#带上
        if 选项值(选项,'mouseButton') is not None:#按钮
            参数['mouseButton']=选项值(选项,'mouseButton')#带上
        if 选项值(选项,'modifiers') is not None:#修饰键
            参数['modifiers']=list(选项值(选项,'modifiers'))#拷贝
        return 动作(自身._派发,'drag',参数)#调度证据

class 窗口表面(应用程序表面):
    '一个显式窗口。键盘操作仍跟随焦点，留在应用程序上'

    def __init__(自身,派发,汇聚,句柄,进程号,windowId):
        '钉住窗口标识'
        super().__init__(派发,汇聚,句柄,进程号,windowId)#这一面
        自身.windowId=windowId#模型读的窗口标识

class 应用程序(应用程序表面):
    '原生应用程序句柄。截图和坐标沿用最近一次辅助功能观察选出的窗口'

    def __init__(自身,派发,汇聚,句柄,进程号):
        '钉住进程号和句柄'
        super().__init__(派发,汇聚,句柄,进程号,None)#不绑定窗口
        自身.pid=进程号#进程号
        自身.appHandle=句柄#句柄

    def activate(自身):
        '显式激活。可能改变用户的焦点应用程序和空间'
        return 动作(自身._派发,'activate',{'appHandle':自身._句柄})#调度证据

    def getWindows(自身,选项=None):
        '列出当前窗口'
        窗口=窗口结果(调用(自身._派发,'listWindows',{'appHandle':自身._句柄}))#校验
        if any(项['pid']!=自身._进程号 for 项 in 窗口):#不是这个进程
            raise Exception('Native windows belong to another application')#拒绝
        if 要发出(选项):#默认发出
            发出文本(自身._汇聚,紧凑json编码(窗口))#JSON
        return 窗口#窗口

    def getWindow(自身,windowId):
        '观察一个指定窗口，并先发出它的初始辅助功能状态'
        窗口=窗口表面(自身._派发,自身._汇聚,自身._句柄,自身._进程号,windowId)#新的一面
        窗口.getAXState()#初始树，默认发出
        return 窗口#窗口

    def typeText(自身,文本):
        '在当前焦点输入。取消可能留下已经输入的前缀'
        return 动作(自身._派发,'typeText',{'appHandle':自身._句柄,'text':文本})#调度证据

    def paste(自身,文本,选项=None):
        '通过应用程序的标准粘贴命令粘贴文本或 HTML'
        参数={'appHandle':自身._句柄,'text':文本}#内容
        if 选项值(选项,'format') is not None:#格式
            参数['format']=选项值(选项,'format')#带上
        return 动作(自身._派发,'paste',参数)#调度证据

    def pressKey(自身,键):
        '在当前焦点发送按键或和弦'
        键名,修饰=键和弦(键)#拆开
        return 动作(自身._派发,'pressKey',{'appHandle':自身._句柄,'key':键名,'modifiers':修饰})#调度证据

class 计算机操作接口:
    '原生应用程序接口。调用方拥有全局绑定和变量持久化'

    def __init__(自身,派发,汇聚):
        '记下派发和可选汇聚端'
        自身._派发=派发#已授权的派发
        自身._汇聚=汇聚#可选输出

    def getCapabilities(自身,选项=None):
        '查看权限，不发起权限请求'
        结果=能力结果(调用(自身._派发,'getCapabilities',{}))#校验
        if 要发出(选项):#默认发出
            发出文本(自身._汇聚,紧凑json编码(结果))#JSON
        return 结果#能力

    def listApps(自身,选项=None):
        '列出正在运行的应用程序'
        结果=[]#选择器
        for 应用 in 运行应用程序结果(调用(自身._派发,'listApps',{})):#校验
            标识=应用['bundleId'] if 应用.get('bundleId') else str(应用['pid'])#包标识或进程号
            结果.append({'id':标识,'displayName':应用['name'],'isRunning':True,'pid':应用['pid']})#一条
        if 要发出(选项):#默认发出
            发出文本(自身._汇聚,紧凑json编码(结果))#JSON
        return 结果#列表

    def findApps(自身,查询,选项=None):
        '按名称、包标识或绝对路径搜索已安装应用程序，不启动'
        结果=发现应用程序结果(调用(自身._派发,'findApps',{'query':查询}))#校验
        if 要发出(选项):#默认发出
            发出文本(自身._汇聚,紧凑json编码(结果))#JSON
        return 结果#匹配

    def getState(自身,选项=None):
        '发现应用程序。浏览器列表保持为空'
        结果={'apps':自身.listApps({'emit':False}),'browsers':[]}#不把内部列表再发一次
        if 要发出(选项):#默认发出
            发出文本(自身._汇聚,紧凑json编码(结果))#JSON
        return 结果#状态

    def getApp(自身,选择器):
        '选择应用程序，取得同意，必要时在后台启动，并发出初始辅助功能状态'
        已选=应用程序结果(调用(自身._派发,'getApp',{'selector':选择器}))#校验
        应用=应用程序(自身._派发,自身._汇聚,已选['appHandle'],已选['pid'])#对象
        应用.getAXState()#初始树，默认发出
        return 应用#句柄

def 创建计算机操作接口(派发,汇聚=None):
    '用一次派发函数和可选观察汇聚端组装对象接口'
    return 计算机操作接口(派发,汇聚)#接口

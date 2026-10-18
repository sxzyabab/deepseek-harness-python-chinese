'把观察到的截图像素或整数比例换算成原生窗口点'
from .原生客户端 import 原生错误

__all__=['计算机操作坐标']

class 计算机操作坐标:
    '只跟踪当前窗口几何和最近一次成功准备的截图'

    def __init__(自身):
        '每个应用程序句柄一张窗口表'
        自身._应用程序={}#句柄到窗口帧

    def 观察(自身,应用程序句柄,窗口列表,窗口标识=None):
        '窗口关闭或改变尺寸时让截图映射失效。省略窗口标识表示整份应用程序清单'
        先前=自身._应用程序.get(应用程序句柄)#上一份帧
        if 窗口标识 is None or 先前 is None:#整份清单，或这一支还没有帧
            当前={}#从空表开始
        else:#范围观察保留其他窗口
            当前=dict(先前)#拷贝上一份
        if 窗口标识 is not None and not any(窗口['windowId']==窗口标识 for 窗口 in 窗口列表):#范围窗口已关闭
            当前.pop(窗口标识,None)#去掉它
        for 窗口 in 窗口列表:#逐个当前窗口
            宽=窗口['bounds']['width']#宽
            高=窗口['bounds']['height']#高
            旧=先前.get(窗口['windowId']) if 先前 is not None else None#旧帧
            if 旧 is not None and 旧['width']==宽 and 旧['height']==高:#尺寸没变就留住截图
                当前[窗口['windowId']]=旧#同一帧对象
            else:#尺寸变了或新窗口
                当前[窗口['windowId']]={'width':宽,'height':高}#只留几何
        自身._应用程序[应用程序句柄]=当前#替换这一支

    def 截图(自身,应用程序句柄,窗口标识,边界,图像):
        '把交给模型的那张图钉在原生窗口尺寸上'
        帧表=自身._应用程序.get(应用程序句柄)#这一支
        if 帧表 is None:#第一次
            帧表={}#新表
            自身._应用程序[应用程序句柄]=帧表#挂上
        帧表[窗口标识]={'width':边界['width'],'height':边界['height'],'image':{'width':图像['width'],'height':图像['height']}}#钉住像素

    def 参数(自身,请求):
        '在发到原生之前把已准入的坐标换算一次，并去掉只给宿主用的坐标选项'
        参数=请求['params']#已由操作模式检查过
        原生=dict(参数)#不改原来的请求
        if 'x' not in 参数 and 'fromX' not in 参数:#不是坐标操作
            return 原生#原样
        帧表=自身._应用程序.get(参数['appHandle'])#这一支
        帧=None if 帧表 is None else 帧表.get(参数['windowId'])#这一窗口
        if 帧 is None or 帧['width']<=0 or 帧['height']<=0:#没有可用几何
            raise 原生错误('STALE_SNAPSHOT','Read fresh window state before coordinate input')#先读新状态
        相对=参数.get('relative') is True#千分比
        if not 相对 and 'image' not in 帧:#像素坐标必须有截图
            raise 原生错误('SCREENSHOT_REQUIRED','Take a fresh screenshot before using absolute pixel coordinates')#先截图
        def 换算(值,轴):
            '把一个轴从像素或千分比换成窗口点'
            像素=帧['image'][轴] if 'image' in 帧 else 帧[轴]#像素边长，没有图时用窗口边长
            if 相对:#千分比，端点 1000 仍落在窗口内
                return min(值/1000*帧[轴],max(0,帧[轴]-1))#窗口点
            if 值>=像素:#超出最近一张截图
                raise 原生错误('INVALID_ARGUMENT','Coordinate is outside the latest screenshot')#拒绝
            return 值*帧[轴]/像素#按比例
        原生.pop('relative',None)#宿主选项不发给原生
        if 'x' in 参数:#点
            原生['x']=换算(参数['x'],'width')#横坐标
            原生['y']=换算(参数['y'],'height')#纵坐标
        else:#拖拽
            原生['fromX']=换算(参数['fromX'],'width')#起点横坐标
            原生['fromY']=换算(参数['fromY'],'height')#起点纵坐标
            原生['toX']=换算(参数['toX'],'width')#终点横坐标
            原生['toY']=换算(参数['toY'],'height')#终点纵坐标
        return 原生#原生参数

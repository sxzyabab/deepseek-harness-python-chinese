'计算机操作的共享执行、应用程序同意和对象运行时。平台提供方负责原生执行'
import base64,json,math,os,re,tempfile,threading,weakref
from ...依赖.工具 import 聚合错误,未传参
from ...工具.原子写入 import 带文件锁
from ...内核.智能体循环.中止与并发 import 中止控制器,合成信号
from ...计算机操作.计算机操作 import 计算机操作提供方名
from ...附件.附件.准入 import 准入编码图像批次
from ...基础设施.通用工具.序列化编码 import 紧凑json编码
from .原生客户端 import 原生错误,原生客户端,若已中止则抛出
from .应用程序访问 import 应用程序访问,等到
from .协议 import 请求,请求模式,应用程序结果,授权结果,状态结果,窗口结果,原生截图结果,协议错误
from .坐标 import 计算机操作坐标

__all__=['计算机操作配置','计算机操作后端','安装计算机操作']

整数上限=2**31-1#有符号 32 位上界
安全整数上限=2**53-1#没有单独上界的字节字段停在安全整数
摘要64=re.compile(r'^[a-f0-9]{64}$')#允许的应用程序身份

def 读取易失(字段):
    '列表和字符串本身就是值；只有其余对象的 get 才是易失读取'
    if isinstance(字段,(dict,list,str,bytes,bytearray)):#普通值
        return 字段#本身
    取值=getattr(字段,'get',None)#易失单元格
    if callable(取值):#有 get
        return 取值()#当前值
    return 字段#本身

def 是易失(字段):
    '配置单元格在写入后还能变'
    if isinstance(字段,(dict,list,str,bytes,bytearray,int,float,bool,type(None))):#普通值
        return False#不是单元格
    return callable(getattr(字段,'get',None))#有 get

def 取整数(数据,键,缺省,最小,最大):
    '缺省或越界都在加载时失败'
    值=缺省 if 键 not in 数据 or 数据[键] is None else 数据[键]#缺省
    if isinstance(值,bool) or not isinstance(值,(int,float)) or not math.isfinite(值) or 值!=int(值) or 值<最小 or 值>最大:#不是范围内的整数
        raise ValueError(键+' must be an integer from '+str(最小)+' to '+str(最大))#拒绝
    return int(值)#整数

def 取数(数据,键,缺省,最小,最大):
    '允许小数。textEventIntervalMs 的缺省是 0.25'
    值=缺省 if 键 not in 数据 or 数据[键] is None else 数据[键]#缺省
    if isinstance(值,bool) or not isinstance(值,(int,float)) or not math.isfinite(值) or 值<最小 or 值>最大:#超出范围
        raise ValueError(键+' must be a number from '+str(最小)+' to '+str(最大))#拒绝
    return 值#数

class 计算机操作配置:
    '原生可执行文件与单次操作的资源上限'

    def __init__(自身,允许的应用程序,辅助路径,构建超时毫秒,超时毫秒,连接超时毫秒,截图超时毫秒,辅助功能超时毫秒,最大响应字节,最大应用程序匹配数,最大剪贴板字节,粘贴读取超时毫秒,最大请求字节,拖拽时长毫秒,拖拽步数,文本事件间隔毫秒,宽限毫秒,最大元素数,最大深度):
        '记下已经校验的上限。允许的应用程序可以是易失单元格'
        自身.允许的应用程序=允许的应用程序#已允许的应用程序或单元格
        自身.辅助路径=辅助路径#绝对路径覆盖，空表示准备包内可执行文件
        自身.构建超时毫秒=构建超时毫秒#准备原生组件的上限
        自身.超时毫秒=超时毫秒#一次原生操作的截止
        自身.连接超时毫秒=连接超时毫秒#连接或启动辅助进程
        自身.截图超时毫秒=截图超时毫秒#含排队的截图截止
        自身.辅助功能超时毫秒=辅助功能超时毫秒#单次辅助功能调用
        自身.最大响应字节=最大响应字节#一帧响应
        自身.最大应用程序匹配数=最大应用程序匹配数#一次发现
        自身.最大剪贴板字节=最大剪贴板字节#一次粘贴保留的剪贴板
        自身.粘贴读取超时毫秒=粘贴读取超时毫秒#粘贴命令返回后等剪贴板被读
        自身.最大请求字节=最大请求字节#一帧请求
        自身.拖拽时长毫秒=拖拽时长毫秒#一次同窗口拖拽
        自身.拖拽步数=拖拽步数#拖拽分成多少段
        自身.文本事件间隔毫秒=文本事件间隔毫秒#每个 Unicode 按下或抬起之后
        自身.宽限毫秒=宽限毫秒#连接清理、套接字写入和启动器退出
        自身.最大元素数=最大元素数#一次辅助功能快照的节点
        自身.最大深度=最大深度#一次辅助功能快照的深度

    @classmethod
    def 校验数据(类,数据=未传参):
        '加载前校验宿主配置。运行时不下载驱动'
        if 数据 is 未传参 or 数据 is None:#缺省
            数据={}#空配置
        if not isinstance(数据,dict):#必须是对象
            raise ValueError('CUA config must be an object')#拒绝
        原始允许=数据['allowedApps'] if 'allowedApps' in 数据 and 数据['allowedApps'] is not None else []#允许列表或单元格
        明文=读取易失(原始允许)#当前快照
        if not isinstance(明文,list):#必须是数组
            raise ValueError('allowedApps must be an array')#拒绝
        已校验=[]#快照
        for 项 in 明文:#逐个
            if not isinstance(项,dict):#必须是对象
                raise ValueError('allowedApps entries must be objects')#拒绝
            标识=项.get('id')#摘要
            if not isinstance(标识,str) or 摘要64.fullmatch(标识) is None:#64 位小写十六进制
                raise ValueError('allowedApps id must be 64 lowercase hex characters')#拒绝
            名称=项.get('name')#显示名
            if not isinstance(名称,str):#必须是字符串
                raise ValueError('allowedApps name must be a string')#拒绝
            路径=项.get('executablePath')#可执行路径
            if not isinstance(路径,str) or len(路径)<1:#不能空
                raise ValueError('allowedApps executablePath must be a non-empty string')#拒绝
            已校验.append({'id':标识,'name':名称,'executablePath':路径})#只留这三个字段
        辅助路径=None#没有覆盖
        if 'helperPath' in 数据 and 数据['helperPath'] is not None:#写了覆盖
            if not isinstance(数据['helperPath'],str):#必须是字符串
                raise ValueError('helperPath must be a string')#拒绝
            辅助路径=数据['helperPath']#绝对路径由提供方再查
        return 类(#已校验配置
            原始允许 if 是易失(原始允许) else 已校验,#单元格继续活着
            辅助路径,#覆盖
            取整数(数据,'buildTimeoutMs',300000,1,整数上限),#准备
            取整数(数据,'timeoutMs',30000,1,整数上限),#操作
            取整数(数据,'connectTimeoutMs',5000,1,整数上限),#连接
            取整数(数据,'screenshotTimeoutMs',5000,1,整数上限),#截图
            取整数(数据,'axTimeoutMs',3000,1,整数上限),#辅助功能
            取整数(数据,'maxResponseBytes',32*1024*1024,1024,安全整数上限),#响应
            取整数(数据,'maxAppMatches',20,1,1000),#发现
            取整数(数据,'maxClipboardBytes',32*1024*1024,1024,安全整数上限),#剪贴板
            取整数(数据,'pasteReadTimeoutMs',1000,1,整数上限),#粘贴读取
            取整数(数据,'maxRequestBytes',1024*1024,1024,安全整数上限),#请求
            取整数(数据,'dragDurationMs',400,1,5000),#拖拽时长
            取整数(数据,'dragSteps',20,1,240),#拖拽步数
            取数(数据,'textEventIntervalMs',0.25,0,1000),#按键间隔
            取整数(数据,'graceMs',3000,1,整数上限),#宽限
            取整数(数据,'maxElements',2000,1,10000),#元素
            取整数(数据,'maxDepth',25,1,100),#深度
        )#配置结束

class 计算机操作后端:
    '平台准备好的可执行文件、传输和操作说明'

    def __init__(自身,辅助路径,创建通道,指引,描述):
        '记下这一平台的四件东西'
        自身.辅助路径=辅助路径#可执行文件
        自身.创建通道=创建通道#连接工厂
        自身.指引=指引#给模型的用法
        自身.描述=描述#工具描述

def 取执行(执行,键):
    '工具执行可能是字典，也可能是对象'
    if isinstance(执行,dict):#字典
        return 执行.get(键)#键
    return getattr(执行,键,None)#属性

def 当前授予(配置):
    '把易失单元格读成授予列表'
    结果=[]#授予
    for 项 in 读取易失(配置.允许的应用程序):#当前快照
        结果.append({'id':项['id'],'name':项['name'],'executablePath':项['executablePath']})#三个字段
    return 结果#列表

def 渲染结果(参数,值):
    '原生值留给程序。进模型内容的只有元数据和已存储的图像'
    if not isinstance(参数,dict) or 参数.get('method')!='screenshot':#不是截图
        return [{'type':'text','text':紧凑json编码(值)}]#整份 JSON
    元数据={}#去掉像素和附件
    for 键,项 in 值.items():#逐字段
        if 键 not in ('data','mimeType','attachment'):#元数据
            元数据[键]=项#留下
    return [{'type':'text','text':紧凑json编码(元数据)},{'type':'image','attachment':值['attachment']}]#文本加图像

def 截图存储(上下文,执行):
    '请求截图之前先解析调用模型和附件存储'
    附件=上下文.获取服务('attachments',False)#附件存储
    if 附件 is None:#没有存储
        raise Exception('CUA screenshots require an attachment store')#拒绝
    智能体=取执行(执行,'agent')#智能体
    头=智能体.session.请求头()#当前请求头
    路由=头.get('config') if isinstance(头,dict) else None#路由
    提供方=路由.get('provider') if isinstance(路由,dict) else None#提供方
    模型=路由.get('model') if isinstance(路由,dict) else None#模型
    选项=智能体.options if isinstance(getattr(智能体,'options',None),dict) else {}#创建选项
    if 提供方 is None:#请求头没有
        提供方=选项.get('provider')#创建选项
    if 模型 is None:#请求头没有
        模型=选项.get('model')#创建选项
    语言模型=上下文.获取服务('llm',False)#语言模型
    if 提供方 is None or 模型 is None or 语言模型 is None:#路由不完整
        raise Exception('CUA screenshot model route could not be resolved')#拒绝
    信息=等到(语言模型.解析模型信息(提供方,模型,取执行(执行,'signal')))#精确模型
    若已中止则抛出(取执行(执行,'signal'))#解析期间取消
    模态=信息.get('inputModalities') if isinstance(信息,dict) else None#输入模态
    if not isinstance(模态,list) or 'image' not in 模态:#没有图像输入
        raise Exception('CUA screenshots require model "'+str(模型)+'" to declare image input')#拒绝
    def 目标(图像):
        '这一模型和这一张图的请求目标'
        return 语言模型.图像请求目标(提供方,模型,图像)#宽高和字节目标
    return 附件,目标#存储和目标函数

def 文件网址(路径):
    '本地文件的 file URL，不放进错误消息'
    绝对=os.path.abspath(路径).replace('\\','/')#斜杠
    if 绝对.startswith('/'):#POSIX
        return 'file://'+绝对#file URL
    return 'file:///'+绝对#盘符

def 安装计算机操作(上下文,配置,后端):
    '按配置和后端挂载工具与对象运行时'
    原生配置={#交给原生客户端和握手的限额
        'helperPath':后端.辅助路径,'cwd':os.getcwd(),#可执行文件和工作目录
        'timeoutMs':配置.超时毫秒,'axTimeoutMs':配置.辅助功能超时毫秒,#操作和辅助功能
        'connectTimeoutMs':配置.连接超时毫秒,'screenshotTimeoutMs':配置.截图超时毫秒,#连接和截图
        'maxRequestBytes':配置.最大请求字节,'maxResponseBytes':配置.最大响应字节,#帧大小
        'graceMs':配置.宽限毫秒,'textEventIntervalMs':配置.文本事件间隔毫秒,#宽限和按键间隔
    }#限额结束
    纤程=getattr(上下文,'纤程',None)#本插件纤程
    插件配置=None if 纤程 is None else getattr(纤程,'插件配置',None)#加载器条目
    条目选项=None if 插件配置 is None else getattr(插件配置,'选项',None)#条目选项
    条目标识=条目选项.get('id') if isinstance(条目选项,dict) else None#设置命名空间
    def 关闭设置自动(子):
        '这一纤程关闭 settings 自动写入'
        def 挂配置():
            'auto 为假，修订由这次同意自己带'
            return 子.settings.configure({'auto':False},上下文.纤程)#绑到本纤程
        子.副作用(挂配置)#随 settings 纤程
    上下文.依赖启动(['settings'],关闭设置自动)#等到 settings
    def 取保存():
        '有设置条目才返回写入器'
        设置=上下文.获取服务('settings',False)#设置
        if 条目标识 is None or 设置 is None:#没有条目或服务
            return None#不能长期授权
        描述符=None#这一条
        for 条目 in 设置.描述({}):#当前描述
            if 条目['ns']==条目标识:#对上
                描述符=条目#记下
                break#停
        if 描述符 is None:#还没登记
            return None#不能写
        def 写入(授予列表):
            '整段替换 allowedApps'
            return 设置.改写(条目标识,[{'op':'set','path':['allowedApps'],'value':授予列表}],描述符['revision'])#带上读到的修订
        return 写入#写入器
    def 授予():
        '每次读取当前允许的应用程序'
        return 当前授予(配置)#当前
    访问=应用程序访问(上下文,{'grants':授予,'save':取保存})#同意
    客户端表={}#智能体 id 到客户端
    寿命=中止控制器()#插件寿命
    进行中={}#完成事件到智能体
    所有者清理={}#智能体 id 到清理
    已关闭=weakref.WeakSet()#已关闭的智能体
    def 建立所有者(智能体):
        '每个智能体一条连接和一份坐标'
        if 智能体 in 已关闭 or 上下文.agents.获取(智能体.id) is not 智能体:#已经拆除
            raise Exception('dsh-cua agent has been disposed')#拒绝
        键=id(智能体)#身份
        现有=所有者清理.get(键)#已有
        if 现有 is not None:#复用
            return 现有#已有
        控制器=中止控制器()#这个智能体的取消
        状态={'开始':False,'完成':threading.Event()}#关闭只做一次
        关闭锁=threading.Lock()#关闭互斥
        def 关闭():
            '关掉客户端并忘掉这个任务的同意'
            with 关闭锁:#只开始一次
                if 状态['开始']:#已经在关
                    等=True#去等
                else:#第一次
                    状态['开始']=True#记下
                    等=False#这一次做
            if 等:#后来的调用
                状态['完成'].wait()#等到
                return#结束
            已关闭.add(智能体)#记成已关闭
            控制器.中止()#取消进行中的操作
            try:#清理
                客户端=客户端表.get(键)#客户端
                if 客户端 is not None:#有连接
                    客户端.释放()#等到原生清理
            finally:#句柄和同意
                for 完成,所有者智能体 in list(进行中.items()):#这个任务还在跑的操作
                    if 所有者智能体 is 智能体:#是它的
                        完成.wait()#等到
                客户端表.pop(键,None)#丢掉客户端
                访问.忘记(智能体)#忘掉临时决定
                所有者清理.pop(键,None)#丢掉清理记录
                状态['完成'].set()#后来的关闭可以走
        def 挂关闭():
            '智能体纤程拆除时关闭'
            return 关闭#拆除器就是关闭
        释放器=智能体.ctx.副作用(挂关闭,'dsh-cua.agent')#随智能体
        所有者={'关闭':关闭,'释放':释放器,'信号':控制器.信号,'坐标':计算机操作坐标()}#记录
        所有者清理[键]=所有者#挂上
        return 所有者#记录
    def 调用原生(请求值,执行):
        '加上宿主资源字段，截图和选择应用程序走各自的路径'
        方法=请求值['method']#方法
        已解析参数=请求值['params']#模型参数
        参数=dict(执行['coordinates'].参数(请求值))#换算坐标
        智能体=执行['agent']#智能体
        信号=执行['signal']#取消
        若已中止则抛出(信号)#已取消
        客户端=执行['nativeClient']#连接
        if 方法=='findApps':#发现上限
            参数['maxAppMatches']=配置.最大应用程序匹配数#宿主字段
        elif 方法=='paste':#粘贴上限
            参数['maxClipboardBytes']=配置.最大剪贴板字节#剪贴板
            参数['pasteReadTimeoutMs']=配置.粘贴读取超时毫秒#读取等待
            参数['maxElements']=配置.最大元素数#元素
            参数['maxDepth']=配置.最大深度#深度
        elif 方法=='getState':#树上限
            参数['maxElements']=配置.最大元素数#元素
            参数['maxDepth']=配置.最大深度#深度
        elif 方法=='drag':#拖拽节奏
            参数['durationMs']=配置.拖拽时长毫秒#时长
            参数['steps']=配置.拖拽步数#步数
        def 请求原生():
            '发一帧'
            return 客户端.请求(方法,参数,信号,执行.get('callId'))#一帧
        if 方法=='screenshot':#截图要进附件存储
            附件,目标=截图存储(上下文,执行)#模型和存储
            截图=原生截图结果(请求原生())#原始 PNG
            若已中止则抛出(信号)#准入前取消
            引用列表=等到(准入编码图像批次(附件,[{'data':截图['data'],'mediaType':截图['mimeType']}]))#耐久引用
            若已中止则抛出(信号)#读请求图前取消
            引用=引用列表[0]#第一张
            原始=引用['originalDimensions'] if isinstance(引用,dict) and 引用.get('originalDimensions') is not None else 引用#规范化前的尺寸
            if 原始['width']!=截图['pixelWidth'] or 原始['height']!=截图['pixelHeight']:#和原图像素不一致
                raise 原生错误('NATIVE_PROTOCOL','Native screenshot dimensions disagree with its decoded image')#拒绝
            图像=等到(附件.读取图像请求(引用,目标(引用),信号))#模型请求版本
            若已中止则抛出(信号)#记下坐标前取消
            执行['coordinates'].截图(已解析参数['appHandle'],截图['windowId'],截图['bounds'],{'width':图像['width'],'height':图像['height']})#钉住像素
            数据=图像['data']#字节或已经是文本
            if isinstance(数据,str):#已经是 base64
                编码=数据#原样
            else:#字节
                编码=base64.b64encode(bytes(数据)).decode('ascii')#规范 base64
            返回=dict(截图)#几何
            返回['mimeType']=图像['mediaType']#请求版本的媒体类型
            返回['data']=编码#base64
            返回['pixelWidth']=图像['width']#请求像素
            返回['pixelHeight']=图像['height']#请求像素
            返回['coordinateSpace']='screenshot-pixels'#输入坐标用这些像素
            返回['attachment']=引用#已存储引用
            return 返回#截图
        if 方法=='paste':#系统剪贴板一次只有一个写者
            def 持锁():
                '锁内再发一次'
                return 请求原生()#发帧
            结果=带文件锁(os.path.join(tempfile.gettempdir(),'dsh-cua-system-clipboard'),持锁,{'waitMs':配置.超时毫秒})#跨进程锁
        else:#其余操作
            结果=请求原生()#发帧
        if 方法=='getApp':#选择、同意、必要时后台启动
            已准备=应用程序结果(结果,True)#pid 可以先空着
            授权=授权结果(结果)#身份
            访问.选择(智能体,客户端,已准备['appHandle'],授权,信号)#同意
            若已中止则抛出(信号)#启动前取消
            if 已准备.get('pid') is None:#还没在跑
                def 启动(寿命):
                    '同意之后才启动'
                    return 客户端.请求('launchApp',{'appHandle':已准备['appHandle']},寿命,执行.get('callId'))#后台启动
                已选=应用程序结果(访问.运行(客户端,已准备['appHandle'],信号,启动))#必须有进程号
            else:#已经在跑
                已选=应用程序结果(已准备)#再校验一次非空进程
            if 已选['appHandle']!=已准备['appHandle']:#启动换成了另一个句柄
                raise 原生错误('NATIVE_PROTOCOL','Launched application has another handle')#拒绝
            return 已选#选中的应用程序
        若已中止则抛出(信号)#读结果前取消
        if 方法=='getCapabilities':#能力结果是开放对象，再写上坐标空间
            if not isinstance(结果,dict):#必须是对象
                raise 协议错误('Invalid capabilities')#拒绝
            能力=dict(结果)#拷贝
            能力['coordinateSpace']='screenshot-pixels'#坐标空间
            return 能力#能力
        if 方法=='getState':#观察之后更新坐标
            状态=状态结果(结果)#校验
            if 状态.get('windowId') is None:#没有选定窗口就是整份清单
                执行['coordinates'].观察(状态['appHandle'],状态['windows'])#整份
            else:#范围观察
                执行['coordinates'].观察(状态['appHandle'],状态['windows'],状态['windowId'])#这一窗口
            return 状态#状态
        if 方法=='listWindows':#窗口清单替换坐标表
            执行['coordinates'].观察(已解析参数['appHandle'],窗口结果(结果))#整份
        return 结果#其余原样返回
    def 运行时():
        '登记提供方、工具和提示，拆除时清掉连接'
        yield 上下文.computerUse.登记(计算机操作提供方名('dsh-cua'))#唯一提供方槽
        def 清理():
            '中止新操作，等已接受的工作和连接都结束'
            寿命.中止()#不再接受
            错误=[]#清理失败
            try:#同意等待
                访问.释放()#取消提问并等操作
            except Exception as 项:#释放失败
                错误.append(项)#留下
            for 完成 in list(进行中):#工具调用
                完成.wait()#等到
            所有者们=list(所有者清理.values())#当前所有者
            for 项 in 所有者们:#先关连接
                try:#关闭
                    项['关闭']()#关掉
                except Exception as 失败:#关闭失败
                    错误.append(失败)#留下
            for 项 in 所有者们:#再摘掉智能体纤程上的副作用
                try:#释放
                    项['释放']()#拆除器
                except Exception as 失败:#释放失败
                    错误.append(失败)#留下
            if len(错误)>0:#有失败
                raise 聚合错误(错误,'dsh-cua helper cleanup failed')#聚合
        yield 清理#插件拆除时清理
        def 执行(参数,执行元数据):
            '校验操作，保证这个智能体有连接，然后派发'
            请求值=请求(参数)#模型操作
            智能体=取执行(执行元数据,'agent')#必须有智能体
            if 智能体 is None:#没有
                raise Exception('dsh-cua requires an agent-owned execution')#拒绝
            信号=取执行(执行元数据,'signal')#工具取消
            若已中止则抛出(信号)#已取消
            若已中止则抛出(寿命.信号)#插件正在拆除
            所有者=建立所有者(智能体)#连接和坐标
            合并=合成信号(信号,寿命.信号,所有者['信号'])#三路取消
            若已中止则抛出(合并)#已取消
            完成=threading.Event()#这次调用
            进行中[完成]=智能体#登记
            try:#一次调用
                先前=客户端表.get(id(智能体))#已有连接
                if 先前 is not None and 先前.已释放:#死连接先清掉
                    先前.释放()#等到
                若已中止则抛出(合并)#清理期间取消
                客户端=客户端表.get(id(智能体))#可能已经没了
                有句柄='appHandle' in 请求值['params']#读取或控制需要先选择
                if 有句柄 and 客户端 is None:#还没有连接
                    raise 原生错误('APP_ACCESS_REQUIRED','Select the application with getApp before reading or controlling it')#先选择
                if 客户端 is None or (客户端.已释放 and not 有句柄):#需要新连接
                    def 报告(消息):
                        '诊断进宿主日志'
                        上下文.日志.调试(消息)#调试
                    客户端=原生客户端(上下文,原生配置,后端.创建通道,报告)#新连接
                    客户端表[id(智能体)]=客户端#挂上
                    所有者['坐标']=计算机操作坐标()#新连接没有旧截图
                def 派发(寿命):
                    '带上这一次的信号和坐标'
                    范围={'agent':智能体,'signal':寿命,'callId':取执行(执行元数据,'callId'),'nativeClient':客户端,'coordinates':所有者['坐标']}#执行
                    结果值=调用原生(请求值,范围)#原生
                    若已中止则抛出(寿命)#返回前取消
                    return 结果值#结果
                if 有句柄:#先核对同意
                    return 访问.运行(客户端,请求值['params']['appHandle'],合并,派发)#同意仍在才发
                return 派发(合并)#不碰应用程序的操作
            finally:#离开进行中表
                完成.set()#清理可以走
                进行中.pop(完成,None)#摘掉
        yield 上下文.tools.登记({#工具
            'name':'cua',#工具名
            'description':后端.描述,#平台描述
            'parameters':请求模式,#模型可见操作
            'output':{'schema':{},'render':渲染结果},#截图单独渲染
            'execute':执行,#执行
        })#登记结束
        def 提示文本(_上下文=None):
            '持久 REPL 才附上对象接口的初始化片段'
            运行时=上下文.获取服务('ptcRuntime',False)#可选运行时
            格式=None if 运行时 is None else getattr(运行时,'programFormat',None)#程序格式
            if 格式!='repl':#不是持久 REPL
                return 后端.指引#只有用法
            网址=文件网址(os.path.join(os.path.dirname(os.path.abspath(__file__)),'桥接.py'))#本包桥接
            return 后端.指引+'\n\nPersistent PTC initialization:\nvar { connectCua } = await import('+json.dumps(网址)+');\nvar cua = connectCua(() => tools.cua, text => console.log(text));'#初始化片段
        yield 上下文.systemPrompt.段落({#提示
            'name':'computer-use:dsh-cua',#段落名
            'order':上下文.systemPrompt.获取段落顺序('TOOL_COMPUTER_USE'),#中央顺序
            'text':提示文本,#用法，持久 REPL 时再加初始化
        })#提示结束
    上下文.副作用(运行时,'dsh-cua.runtime')#随本插件纤程


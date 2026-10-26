'导出文件命名、浏览器传输令牌类型，以及原生的字节或资源请求。句柄与请求身份是字符串，铸造时走标识构造，本包不另定义品牌'
import mimetypes#标准库 MIME 后缀
import re#模块层编译一次
from typing import Literal,NotRequired,Protocol,TypedDict#字段与宿主操作约定

__all__=[#仅中文公开名
    '文件拖拽令牌类型','拖拽文件名','桌面字节来源','桌面资源来源','桌面文件拖拽','解析拖拽文件名',
]#公开面结束

文件拖拽令牌类型='application/x-dsh-file'#浏览器传输令牌类型；原始字节留在所属应用

非法名字符=re.compile(r'[<>:"/\\|?*\x00-\x1f]',re.ASCII)#路径分隔与控制字符
首尾点空白=re.compile(r'^[. ]+|[. ]+\Z',re.ASCII)#去掉首尾点与空格
参数尾=re.compile(r';.*\Z',re.ASCII|re.DOTALL)#丢掉 MIME 参数
前导点=re.compile(r'^\.',re.ASCII)#显式后缀前的一个点
非法后缀字符=re.compile(r'[^a-z\d_-]',re.ASCII|re.IGNORECASE)#后缀只留字母、数字、下划线与连字符
设备名=re.compile(r'^(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|\Z)',re.ASCII|re.IGNORECASE)#Windows 设备名

class 拖拽文件名(TypedDict):#调用方提供的导出命名，Web 与 Desktop 共用
    '调用方提供的导出命名，Web 与 Desktop 共用'
    mediaType:str#声明的内容类型
    name:NotRequired[str]#调用方名称；缺席当 file
    outputExtension:NotRequired[str]#显式后缀，可带点

class 桌面字节来源(拖拽文件名):#拷贝完整字节
    '拷贝完整字节'
    kind:Literal['bytes']#字节来源
    bytes:bytes#文件字节

class 桌面资源来源(拖拽文件名):#请宿主授权借用资源
    '请宿主授权借用资源'
    kind:Literal['resource']#资源来源
    address:str#会话资源地址
    sha256:NotRequired[str]#可选内容校验
    size:NotRequired[int]#可选字节大小

class 桌面文件拖拽(Protocol):#原生文件操作；任何请求都不接受渲染进程的原始文件系统路径
    '原生文件操作；任何请求都不接受渲染进程的原始文件系统路径。句柄与请求身份交给标识构造'

    def 准备(自身,来源,请求身份):#准备字节或可核验资源
        '准备字节或可核验资源。返回标识构造标记过的句柄；资源需要字节拷贝时没有返回'
        raise NotImplementedError('桌面文件拖拽由宿主实现')#本包只声明操作

    def 取消(自身,请求身份):#句柄返回前停掉未完成的准备
        '取消未完成的准备并释放尚未使用的资源'
        raise NotImplementedError('桌面文件拖拽由宿主实现')#本包只声明操作

    def 开始(自身,句柄):#把已准备的文件交给操作系统拖放
        '已准备的文件开始拖放。操作系统接受则为真'
        raise NotImplementedError('桌面文件拖拽由宿主实现')#本包只声明操作

    def 释放(自身,句柄):#释放未使用的准备
        '释放未使用的准备；操作系统已交付的临时文件有一段有界的读取宽限'
        raise NotImplementedError('桌面文件拖拽由宿主实现')#本包只声明操作

def 按字节截断(值,字节数):#按 UTF-8 字节留下前缀
    '按 UTF-8 字节留下前缀，切点落在字符边界'
    结果=[]#已留下的字符
    剩余=字节数#还剩的字节预算
    for 字符 in 值:#逐个 Unicode 字符
        长度=len(字符.encode('utf-8'))#该字符的 UTF-8 字节数
        if 长度>剩余:#放下一个字符就会切断
            break#停在字符边界
        结果.append(字符)#收下整字符
        剩余-=长度#扣掉字节
    return ''.join(结果)#拼回字符串

def 首选后缀(声明):#声明类型的首选后缀，不含点
    '声明类型的首选后缀，不含点；未知类型没有后缀'
    if 声明=='':#空类型
        return None#不补
    扩展=mimetypes.guess_extension(声明,strict=False)#标准库首选，带点
    if not 扩展:#未知
        return None#不补
    if 扩展.startswith('.'):#去掉点
        return 扩展[1:]#不含点
    return 扩展#本来就没有点

def 后缀兼容(声明,后缀):#现有后缀是否属于该声明类型
    '现有后缀是否属于该声明类型的已知后缀'
    if 声明=='' or 后缀=='':#无从比较
        return False#不兼容
    全部=mimetypes.guess_all_extensions(声明,strict=False) or []#全部已知后缀，带点；未知类型没有列表
    小写=后缀.lower()#比较时忽略大小写
    for 扩展 in 全部:#逐个已知后缀
        名=扩展[1:] if 扩展.startswith('.') else 扩展#去掉点
        if 名==小写:#命中
            return True#兼容
    return False#不在已知集合里

def 解析拖拽文件名(请求):#解析一个平台安全的导出文件名
    """解析一个平台安全的导出文件名。显式后缀优先；兼容的已有后缀保留。
    已知冲突按声明的 MIME 替换；未知 MIME 不拒绝调用方给出的名称。
    只在需要时补 MIME 后缀"""
    名称=请求['name'] if 'name' in 请求 and 请求['name'] is not None else 'file'#缺席名称
    干净=首尾点空白.sub('',非法名字符.sub('_',名称)) or 'file'#清掉非法字符与首尾点、空格
    点=干净.rfind('.')#最后一个点
    现有='' if 点<0 else 干净[点+1:]#现有后缀，不含点
    声明=参数尾.sub('',请求['mediaType']).strip().lower()#去掉参数后的类型
    首选=首选后缀(声明)#MIME 首选后缀
    兼容=后缀兼容(声明,现有)#现有后缀是否属于该类型
    输出后缀=请求['outputExtension'] if 'outputExtension' in 请求 else None#显式后缀
    if 输出后缀 is None:#没有显式后缀
        显式=''#空则不优先
    else:#清掉点与非法字符
        显式=非法后缀字符.sub('',前导点.sub('',输出后缀,count=1))#只留安全后缀
    if 显式:#显式后缀优先
        选定=显式#用显式的
    elif 现有=='' or (首选 is not None and not 兼容):#没有后缀，或已知类型且现有后缀冲突
        选定=首选#改用 MIME 首选；未知类型时首选为空
    else:#保留现有后缀
        选定=现有#含原来的大小写
    if 选定:#需要写上后缀
        词干=干净 if 点<0 else 干净[:点]#去掉旧后缀
        干净=词干+'.'+选定#接上选定后缀
    if 设备名.search(干净):#Windows 设备名
        干净='_'+干净#加前缀，避免被当成设备
    末点=干净.rfind('.')#截断前再看后缀
    尾巴='' if 末点<0 else 干净[末点:]#含点的尾巴
    词干=干净 if 末点<0 else 干净[:末点]#不含后缀的词干
    后缀尾巴=按字节截断(尾巴,32)#后缀最多 32 个 UTF-8 字节
    词干预算=255-len(后缀尾巴.encode('utf-8'))#整名不超过 255 字节
    return 按字节截断(词干,词干预算)+后缀尾巴#词干截在字符边界，再接后缀

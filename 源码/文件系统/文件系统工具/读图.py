"""面向模型的 read_image 工具：读取 PNG/JPEG/WebP/GIF 文件，经附件服务持久提交其字节（与用户上传图像同一生命周期），并返回图像块，使图像从下一请求起进入模型上下文。路由门控有意比宿主上传预检更严：工具结果进入持久会话历史，因此在无法承载图像的路由上发出图像会破坏该路由的续写；能力未知时因此拒绝，而不是依赖适配器守卫。对齐上游 tool-fs/src/read-image.ts。"""
from ...附件.附件 import 附件错误,附件标识#导入附件错误与附件id品牌
from ...模型后端.llm import 创建用户消息#导入用户消息构造
from ...内核.工具 import 定义工具#导入工具定义
from .读目标 import 解析普通读目标#导入普通文件目标解析
from .辅助 import 取字段,试取,解开#字段读取与承诺展开

图像扩展名={#扩展名到声明的媒体类型；附件服务的魔数校验仍是权威
    '.png':'image/png',#PNG
    '.jpg':'image/jpeg',#JPEG
    '.jpeg':'image/jpeg',#JPEG
    '.webp':'image/webp',#WebP
    '.gif':'image/gif',#GIF
}#图像扩展名结束

def 取基名(路径):#取路径最后一段
    """取路径最后一段，正斜杠与反斜杠都是分隔符。"""
    return 路径[max(路径.rfind('/'),路径.rfind('\\'))+1:]#基名

def 取扩展名(路径):#取带点后缀
    """按扩展名取带点后缀；点文件没有扩展名。"""
    基名=取基名(路径)#最后一段
    点=基名.rfind('.')#最后一个点
    if 点<=0:#无扩展名或点文件
        return ''#空扩展名
    return 基名[点:]#带点后缀

def 路径图像类型(文件路径):#按扩展名映射媒体类型
    """按扩展名把模型提供的路径映射为声明的图像媒体类型。"""
    return 图像扩展名.get(取扩展名(文件路径).lower())#小写扩展名查表

def 断言图像路由(上下文,执行,请求路径):#强制图像能力门控
    """对调用路由强制严格的图像能力门控。能力未知时拒绝，而不是依赖适配器守卫。"""
    智能体=试取(执行,'agent')#调用方智能体
    路由配置=None#请求头上的路由配置
    if 智能体 is not None:#有智能体
        头=取字段(智能体,'session').请求头()#请求头
        if 头 is not None:#有头
            路由配置=试取(头,'config')#路由配置
    提供方=试取(路由配置,'provider')#头上的提供方
    模型=试取(路由配置,'model')#头上的模型
    if 提供方 is None and 智能体 is not None:#头上没有提供方
        提供方=试取(取字段(智能体,'options'),'provider')#回退agent选项
    if 模型 is None and 智能体 is not None:#头上没有模型
        模型=试取(取字段(智能体,'options'),'model')#回退agent选项
    语言模型=上下文.get('llm')#可选的LLM服务
    if 提供方 is None or 模型 is None or 语言模型 is None:#路由无法解析
        raise Exception('cannot read "'+请求路径+'" as an image: the current model route could not be resolved')#拒绝：路由未知
    现行=解开(语言模型.解析模型信息(提供方,模型,试取(执行,'signal')))#解析该路由的模型信息
    输入模态=试取(现行,'inputModalities')#输入模态
    if 输入模态 is None or 'image' not in 输入模态:#未声明图像输入
        raise Exception('cannot read "'+请求路径+'" as an image: model "'+模型+'" does not declare image input; switch to an image-capable model to read images')#拒绝：模型不接受图像

def 值转图像引用(图像):#规范图像转附件引用
    """把规范图像结果再打成 ImageBlock 所携带的持久附件引用。"""
    引用={#附件引用
        'attachmentId':附件标识(取字段(图像,'attachmentId')),#打成附件id品牌
        'mediaType':取字段(图像,'mediaType'),#媒体类型
        'bytes':取字段(图像,'bytes'),#字节数
        'width':取字段(图像,'width'),#宽
        'height':取字段(图像,'height'),#高
    }#引用结束
    名字=试取(图像,'name')#可选文件名
    if 名字 is not None:#有名字
        引用['name']=名字#带上
    return 引用#附件引用

def 格式化读图输出(展示路径,图像):#格式化读图摘要信封
    """把读图格式化为图像块旁边的面向模型信封。"""
    return '<path>'+展示路径+'</path>\n<type>image</type>\n<content>\n'+取字段(图像,'mediaType')+' image, '+str(取字段(图像,'width'))+'x'+str(取字段(图像,'height'))+' px, '+str(取字段(图像,'bytes'))+' bytes\n</content>'#类型为image的摘要信封

def 读图内容(值):#投影为信封与图像块
    """把一次规范读图投影为面向模型的信封与图像。"""
    图像=取字段(值,'image')#图像元数据
    return [#文本信封加图像块
        {'type':'text','text':格式化读图输出(取字段(值,'path'),图像)},#摘要信封
        {'type':'image','attachment':值转图像引用(图像)},#图像附件块
    ]#内容块结束

def 应用读图工具(上下文):#注册 read_image 工具
    """向给定上下文注册 read_image 工具。组合插件拥有附件门控；执行仍再检查 attachments，并按调用路由声明的图像输入做门控。"""
    def 渲染(参数,值):#渲染信封加图像块
        """渲染信封加图像块。"""
        return 读图内容(值)#信封加图像块
    def 并发安全(参数):#读图并发安全
        """读图并发安全。"""
        return True#内容寻址的附件写入是幂等的
    def 执行(参数,执行上下文):#执行读图
        """执行读图。每一道门控都在任何文件系统 I/O 之前运行。"""
        if len(取字段(参数,'file_path').strip())==0:#路径不得为空
            raise Exception('file_path must be a non-empty string')#路径不得为空
        媒体类型=路径图像类型(取字段(参数,'file_path'))#按扩展名取声明类型
        if 媒体类型 is None:#不是接受的图像扩展名
            raise Exception('cannot read "'+取字段(参数,'file_path')+'": read_image only accepts PNG/JPEG/WebP/GIF paths')#拒绝非图像路径
        附件=上下文.get('attachments')#取出附件服务
        if 附件 is None:#未挂载附件服务
            raise Exception('cannot read "'+取字段(参数,'file_path')+'" as an image: no attachment service is mounted')#拒绝
        限额=取字段(附件,'图像限额')#部署图像限额（对齐附件服务中文公开属性）
        if 媒体类型 not in 取字段(限额,'mediaTypes'):#部署不接受该媒体类型；限额字段名与上游协议一致
            raise Exception('cannot read "'+取字段(参数,'file_path')+'": '+媒体类型+' images are not accepted by this deployment')#拒绝
        断言图像路由(上下文,执行上下文,取字段(参数,'file_path'))#断言当前路由接受图像
        已解析=解开(解析普通读目标(上下文,执行上下文,取字段(参数,'file_path')))#解析普通文件目标
        目标=已解析['target']#目标
        信息=已解析['info']#stat结果
        字节上限=min(取字段(限额,'maxImageBytes'),取字段(限额,'maxMessageImageBytes'))#取更严的字节上限
        数据=解开(上下文.fs.读字节(目标,试取(执行上下文,'signal'),字节上限))#按上限读取原始字节
        try:#保存图像附件
            引用=解开(附件.保存图像({'data':数据,'mediaType':媒体类型,'name':取基名(取字段(目标,'displayPath'))}))#按声明类型提交
        except Exception as 错误:#保存失败
            if (not isinstance(错误,附件错误)) or 错误.code!='IMAGE_TYPE_MISMATCH':#非类型不匹配
                raise#原样抛出
            扩展名=取扩展名(取字段(目标,'displayPath')).lower()#实际扩展名
            失败=Exception('cannot read "'+取字段(目标,'displayPath')+'": the '+扩展名+' extension declares '+媒体类型+', but the bytes use a different image format; rename the file to match its actual format if it is PNG/JPEG/WebP/GIF, or convert it to one of those formats')#扩展名与字节格式不一致
            raise 失败 from 错误#链接原始附件错误
        上下文.emit('fs/observed',目标,{'kind':'present','version':取字段(信息,'version')},执行上下文)#记录存在观察
        图像={#图像元数据
            'attachmentId':取字段(引用,'attachmentId'),#附件id
            'mediaType':取字段(引用,'mediaType'),#媒体类型
            'bytes':取字段(引用,'bytes'),#字节数
            'width':取字段(引用,'width'),#宽
            'height':取字段(引用,'height'),#高
        }#图像结束
        if 试取(引用,'name') is not None:#有名字
            图像['name']=取字段(引用,'name')#带上
        值={'path':取字段(目标,'displayPath'),'image':图像}#规范结果
        if 试取(执行上下文,'parent') is not None:#嵌套派发时把图像注入后续模型上下文
            取字段(执行上下文,'deferContext')(创建用户消息({#推迟一条用户消息
                'content':读图内容(值),#信封加图像块
                'source':{'kind':'plugin','plugin':'tool-fs'},#来源为本插件
            }))#deferContext结束
        return 值#返回规范结果
    def 呈现调用(参数):#调用时通用卡片
        """调用时通用卡片，跟随位置在图像文件上。"""
        return {#卡片
            'card':'generic',#通用卡片
            'title':'Read image '+取字段(参数,'file_path'),#标题
            'kind':'read',#读种类图标
            'locations':[{'path':取字段(参数,'file_path')}],#跟随到图像路径
        }#卡片结束
    上下文.tools.登记(定义工具({#注册工具
        'name':'read_image',#工具名
        'description':'Read a PNG/JPEG/WebP/GIF file and return the image itself. Requires the current model to accept image input.',#工具描述
        'parameters':{#参数schema
            'file_path':{'type':'string','required':True,'description':'Path to the image file, resolved by the filesystem backend.'},#图像路径
        },#parameters结束
        'output':{#结构化输出
            'schema':{#输出schema
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'path':{'type':'string','required':True},#已解析路径
                    'image':{#图像元数据
                        'type':'object',#对象
                        'additionalProperties':False,#禁止额外字段
                        'required':True,#必填
                        'properties':{#图像字段
                            'attachmentId':{'type':'string','required':True},#附件id
                            'mediaType':{'type':'string','enum':['image/png','image/jpeg','image/webp','image/gif'],'required':True},#媒体类型
                            'bytes':{'type':'integer','required':True},#字节数
                            'width':{'type':'integer','required':True},#宽
                            'height':{'type':'integer','required':True},#高
                            'name':{'type':'string'},#可选文件名
                        },#properties结束
                    },#image结束
                },#properties结束
            },#schema结束
            'render':渲染,#渲染信封加图像块
        },#output结束
        'isConcurrencySafe':并发安全,#读图并发安全
        'execute':执行,#执行读图
        'presentCall':呈现调用,#调用时通用卡片
    }))#register结束

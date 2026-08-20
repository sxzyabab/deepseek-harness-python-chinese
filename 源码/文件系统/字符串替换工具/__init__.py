"""面向模型的 `str_replace_editor`，建立在 Harness 文件系统 seam 上。"""
import os#绝对路径判断
from functools import cmp_to_key#目录列举排序对齐上游比较器
from schemastery import 模式#导入配置校验库
from tools import 定义工具#导入工具定义器
from fs import 文件系统错误#导入文件系统错误
from sandbox import 沙箱拒绝标记#导入沙箱拒绝标记文案
from cordis.工具 import 是否thenable#可等待判定

__all__=(#仅中文公开名
    '名称','注入','截断消息','默认描述','配置','安全整数上限',
    '取字段','解开','是否整数','是否安全整数','错误',
    '或许截断','码点比较','匹配下标','下标行号','变更政策',
    '解析目标','状态已存在','命令必填','格式化文件视图','列举目录',
    '查看路径','创建文件','文件内替换','文件内插入',
    '呈现编辑器调用','登记字符串替换编辑器','落实配置','应用','默认',
)#公开面结束

名称='tool-str-replace-editor'#Cordis插件名
注入=['tools','fs']#必需注入：工具与文件系统
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

截断消息='<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>'#超长视图的截断标记

默认描述=(#面向模型的默认工具描述（字面量保持上游英文）
    'Custom editing tool for viewing, creating and editing files\n'#工具总述
    '* State is persistent across command calls and discussions with the user\n'#跨调用持久
    '* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep\n'#view行为
    '* The `create` command cannot be used if the specified `path` already exists as a file\n'#create不得覆盖
    '* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`\n'#超长截断
    '\n'#空行分隔
    'Notes for using the `str_replace` command:\n'#替换说明标题
    '* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!\n'#old_str须逐字
    '* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique\n'#须唯一
    '* The `new_str` parameter should contain the edited lines that should replace the `old_str`'#new_str为替换文
)#去掉首尾空白由上游 trim；此处字面量已无首尾空白

配置=模式.对象({#插件配置校验模式
    'maxOutputChars':模式.数字().默认(16_000),#视图字符上限
    'description':模式.字符串().默认(默认描述),#工具描述
})#配置模式结束
Config=配置#Cordis配置模式

安全整数上限=2**53-1#对齐 Number.MAX_SAFE_INTEGER

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 是否整数(值):#对齐JS Number.isInteger
    """对齐 JS Number.isInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return True#整数
    if isinstance(值,float):#浮点
        return 值.is_integer()#整值浮点
    return False#其它类型

def 是否安全整数(值):#对齐JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if not 是否整数(值):#先要求整数
        return False#非整数
    return -安全整数上限<=值<=安全整数上限#落在安全整数范围

class 错误(Exception):#对齐上游 throw new Error 文案
    """运行时错误，错误信息保持上游英文原文。"""

def 或许截断(内容,最大输出字符):#按字符上限截断输出
    """超长输出截到 `maxOutputChars` 并接上截断提示。"""
    if len(内容)<=最大输出字符:#未超长则原样
        return 内容#完整文本
    return 内容[0:最大输出字符]+截断消息#截断并接提示

def 码点比较(左,右):#字符串码点序比较
    """按码点比较两条字符串，供目录列举排序。"""
    if 左<右:#小于
        return -1#左先
    if 左>右:#大于
        return 1#右先
    return 0#相等

def 匹配下标(内容,搜索):#收集字面量每一处起始下标
    """找出 `search` 在 `content` 中每一处字面量出现的起始下标。"""
    下标们=[]#命中起始下标
    起点=0#下一轮搜索起点
    while True:#直到找不到下一处
        命中=内容.find(搜索,起点)#从起点起找下一处
        if 命中<0:#没有更多命中
            return 下标们#返回已收集
        下标们.append(命中)#记下本处起始
        起点=命中+len(搜索)#从本处之后继续，避免零宽死循环

def 下标行号(内容,下标们):#下标转1基行号
    """把字节下标映射为 1 基行号。"""
    行号=1#当前行号
    游标=0#已扫描到的下标
    结果=[]#与下标们对齐的行号
    for 下标 in 下标们:#每个下标对应一行号
        while 游标<下标:#推进到该下标
            if 内容[游标]=='\n':#遇到换行则行号加一
                行号+=1#行号加一
            游标+=1#前进一步
        结果.append(行号)#该下标所在行
    return 结果#行号列表

class 变更政策:#变更所用的沙箱策略适配
    """在文件系统处于沙箱模式时解析并映射变更拒绝。"""
    def __init__(自身,上下文):#按文件系统沙箱模式解析策略服务
        """文件系统处于沙箱模式时必须能取到 `sandboxPolicy`。"""
        沙箱模式=getattr(上下文.fs,'sandboxMode',None)#读取后端默认沙箱模式
        if 沙箱模式 is None:#非沙箱则不取策略
            自身.政策=None#无策略服务
        else:#沙箱模式
            自身.政策=上下文.get('sandboxPolicy')#取已挂载的沙箱策略服务
        if 沙箱模式 is not None and 自身.政策 is None:#沙箱模式却没有策略服务
            raise 错误('tool-str-replace-editor: the mounted filesystem confines but ctx.sandboxPolicy is missing')#加载时大声失败

    def 解析(自身,执行上下文):#解析本次运行的沙箱策略
        """为本次工具运行解析沙箱执行策略。"""
        if 自身.政策 is None:#无策略服务
            return None#非沙箱
        智能体=取字段(执行上下文,'agent')#可选智能体
        请求={}#解析请求
        if 智能体 is not None:#有agent则带上会话
            请求['session']=取字段(智能体,'session')#会话
        return 自身.政策.resolve(请求)#有策略服务才解析

    def 映射错误(自身,错误,政策):#映射沙箱拒绝错误
        """把 `FS_SANDBOX_DENIED` 换成带当前模式标记的同类错误。"""
        if not isinstance(错误,文件系统错误):#非文件系统错误
            return 错误#原样
        if 取字段(错误,'code')!='FS_SANDBOX_DENIED':#非沙箱拒绝则原样
            return 错误#原样
        模式=取字段(政策,'mode')#取出当前沙箱模式
        return 文件系统错误(沙箱拒绝标记(模式),'FS_SANDBOX_DENIED',{'cause':错误})#换成带模式标记的拒绝

def 解析目标(上下文,路径,信号):#把绝对路径解析成FsTarget
    """把绝对路径解析成文件系统目标。"""
    if len(路径.strip())==0:#空白路径拒绝
        raise 错误('path must be a non-empty string')#空白路径
    if not os.path.isabs(路径):#必须是绝对路径
        raise 错误('The path '+路径+' is not an absolute path, it should start with `/`. Maybe you meant /'+路径+'?')#提示补上前导斜杠
    return 解开(上下文.fs.resolve(路径,{'signal':信号}))#交给文件系统解析

def 状态已存在(上下文,目标,命令,执行上下文):#确认目标存在并取出元数据
    """对已存在目标做 stat；缺失则发出 absent 观察并抛 `FS_NOT_FOUND`。目录上除 `view` 外拒绝。"""
    信息=解开(上下文.fs.stat(目标,取字段(执行上下文,'signal')))#探测目标
    if 信息 is None:#目标不存在
        上下文.emit('fs/observed',目标,{'kind':'absent'},执行上下文)#记录缺失观察
        raise 文件系统错误(#报未找到
            'The path '+取字段(目标,'displayPath')+' does not exist. Please provide a valid path.',#面向模型的缺失说明
            'FS_NOT_FOUND',#未找到码
        )#FsError结束
    if 取字段(信息,'type')=='directory' and 命令!='view':#目录上只允许view
        raise 文件系统错误(#报不是普通文件
            'The path '+取字段(目标,'displayPath')+' is a directory and only the `view` command can be used on directories',#目录不能替换或插入
            'FS_NOT_REGULAR_FILE',#非普通文件码
        )#目录拒绝结束
    return 信息#存在且允许该命令

def 命令必填(值,参数名,命令,允许空=True):#取出命令必填参数
    """命令所需参数：缺失则抛错；`allowEmpty` 为假时还拒绝空字符串。"""
    if 值 is None:#缺失则拒绝
        raise 错误('Parameter `'+参数名+'` is required for command: '+命令)#缺失参数
    if (not 允许空) and len(值)==0:#不允许空且给了空串
        raise 错误('Parameter `'+参数名+'` is empty for command: '+命令)#空串拒绝
    return 值#已确认的参数

def 格式化文件视图(路径,内容,最大输出字符,视图范围=None):#格式化带行号的文件视图
    """把文件内容格式化成带行号的视图，可选 `view_range`。"""
    全部行=内容.split('\n')#按行拆分
    行们=全部行#实际展示的行
    起始行=1#展示起始行号
    结束行=None#展示结束行号
    导语="Here's the content of "+路径+" with line numbers (which has a total of "+str(len(全部行))+" lines)"#视图导语
    if 视图范围 is not None:#指定了行范围
        if len(视图范围)!=2:#必须恰好两项
            raise 错误('Invalid `view_range`. It should be a list of two integers.')#要求两个整数
        请求起始=视图范围[0]#起始
        请求结束=视图范围[1]#结束
        if 请求起始 is None or 请求结束 is None:#起始或结束不得缺失
            raise 错误('Invalid `view_range`. It should be a list of two integers.')#要求两个整数
        if not all(是否整数(项) for 项 in 视图范围):#必须都是整数
            raise 错误('Invalid `view_range`. It should be a list of two integers.')#要求两个整数
        起始行=请求起始#采用请求的起始
        结束行=请求结束#采用请求的结束
        if 起始行<1 or 起始行>len(全部行):#起始超出文件
            raise 错误(#报起始越界
                'Invalid `view_range`: ['+', '.join(str(项) for 项 in 视图范围)+']. Its first element `'+str(起始行)+'` should be within the range of lines of the file: [1, '+str(len(全部行))+']',#起始必须在[1, 总行数]
            )#起始越界结束
        if 结束行>len(全部行):#结束大于总行数
            raise 错误(#报结束越界
                'Invalid `view_range`: ['+', '.join(str(项) for 项 in 视图范围)+']. Its second element `'+str(结束行)+'` should be smaller than the number of lines in the file: `'+str(len(全部行))+'`',#结束不得大于总行数
            )#结束越界结束
        if 结束行!=-1 and 结束行<起始行:#-1表示到末尾，否则结束不得小于起始
            raise 错误(#报起止颠倒
                'Invalid `view_range`: ['+', '.join(str(项) for 项 in 视图范围)+']. Its second element `'+str(结束行)+'` should be larger or equal than its first `'+str(起始行)+'`',#结束必须≥起始
            )#起止颠倒结束
        if 结束行==-1:#-1表示切到文件末尾
            行们=全部行[起始行-1:]#从起始切到末尾
        else:#闭区间切到结束行
            行们=全部行[起始行-1:结束行]#闭区间
        导语+=' with view_range=['+str(起始行)+', '+str(结束行)+']'#导语补上范围
    编号行=[]#给展示行编号
    for 序号,行 in enumerate(行们):#逐行编号
        编号行.append(str(起始行+序号).rjust(6,' ')+'  '+行)#6位右对齐行号
    正文='\n'.join(编号行)#行之间换行
    return 或许截断(导语+':\n'+正文+'\n',最大输出字符)#导语加编号正文，再截断

def 列举目录(上下文,目标,最大输出字符,执行上下文):#列举目录最多两层
    """列举目录最多 2 层，跳过隐藏项、`node_modules` 与 Python 缓存。"""
    信号=取字段(执行上下文,'signal')#中止信号
    def 访问(目录,深度):#递归列举一层
        """递归列举一层子项。"""
        条目=解开(上下文.fs.listDir(目录,信号))#列出直接子项
        行们=[]#本层及更深层的行
        for 候选项 in 条目:#遍历直接子项
            名=取字段(候选项,'name')#子项基名
            if 名.startswith('.'):#隐藏项
                continue#跳过
            if 名=='node_modules':#Node依赖目录
                continue#跳过
            if 名=='__pycache__':#Python缓存
                continue#跳过
            类型=取字段(候选项,'type')#子项类型
            if 类型=='directory':#目录
                标记='d'#目录标记
            elif 类型=='file':#普通文件
                标记='f'#文件标记
            else:#其它
                标记='?'#未知标记
            子目标=取字段(候选项,'target')#已解析子目标
            行们.append(标记+'\t'+取字段(子目标,'displayPath'))#标记加展示路径
            if 类型=='directory' and 深度<2:#未到两层则再下降
                行们.extend(访问(子目标,深度+1))#展开子目录
        return 行们#本层及更深层的行
    行们=['d\t'+取字段(目标,'displayPath')]+访问(目标,1)#根目录行加递归结果
    def 取路径(行):#去掉类型标记后的展示路径
        """从列举行取出展示路径。"""
        return 行[行.find('\t')+1:]#展示路径
    行们=sorted(行们,key=cmp_to_key(lambda 左,右:码点比较(取路径(左),取路径(右))))#按展示路径码点排序
    列举=或许截断('\n'.join(行们)+'\n',最大输出字符)#拼成文本再截断
    return "Here're the files and directories up to 2 levels deep in "+取字段(目标,'displayPath')+", excluding hidden items, node_modules, and Python cache directories:\n"+列举+'\n'#导语加列举

def 查看路径(上下文,路径,视图范围,最大输出字符,执行上下文):#查看文件或目录
    """查看文件或目录：目录走列举，文件走带行号视图。"""
    目标=解析目标(上下文,路径,取字段(执行上下文,'signal'))#解析目标
    信息=状态已存在(上下文,目标,'view',执行上下文)#确认存在
    if 取字段(信息,'type')=='directory':#目录走列举
        if 视图范围 is not None:#目录不允许view_range
            raise 错误('The `view_range` parameter is not allowed when `path` points to a directory.')#拒绝目录行范围
        return 列举目录(上下文,目标,最大输出字符,执行上下文)#最多两层列举
    if 取字段(信息,'type')!='file':#既非目录也非普通文件
        raise 文件系统错误('cannot view "'+取字段(目标,'displayPath')+'": not a regular file or directory','FS_NOT_REGULAR_FILE')#拒绝特殊文件
    内容=解开(上下文.fs.readText(目标,取字段(执行上下文,'signal')))#读出全文
    上下文.emit('fs/observed',目标,{'kind':'present','version':取字段(信息,'version')},执行上下文)#记录存在观察
    return 格式化文件视图(取字段(目标,'displayPath'),内容,最大输出字符,视图范围)#带行号视图

def 创建文件(上下文,政策,路径,文件文本,执行上下文):#仅在不存在时创建文件
    """仅在目标不存在时创建文件。"""
    内容=命令必填(文件文本,'file_text','create')#create必填file_text
    沙箱政策=政策.解析(执行上下文)#本次沙箱策略
    信号=取字段(执行上下文,'signal')#中止信号
    目标=解析目标(上下文,路径,信号)#解析目标
    if 解开(上下文.fs.stat(目标,信号)) is not None:#目标已存在
        raise 错误('File already exists at: '+取字段(目标,'displayPath')+'. Cannot overwrite files using command `create`.')#create不得覆盖
    def 默认写意图():#瀑布末端默认意图
        """默认仅在缺失时创建。"""
        return {'kind':'createIfAbsent'}#仅在缺失时创建
    意图=解开(上下文.waterfall(#询问写意图
        'fs/write-intent',#写意图瀑布
        目标,#目标
        执行上下文,#执行上下文
        默认写意图,#默认仅在缺失时创建
    ))#写意图结束
    try:#受沙箱策略约束写入
        结果=解开(上下文.fs.writeText(#创建文件
            目标,#目标
            内容,#全文
            意图,#写意图
            信号,#中止信号
            沙箱政策,#沙箱策略
        ))#writeText结束
    except BaseException as 异常:#写入失败
        raise 政策.映射错误(异常,沙箱政策)#沙箱拒绝换成带模式标记的错误
    上下文.emit('fs/observed',目标,{'kind':'present','version':取字段(结果,'version')},执行上下文)#记录存在观察
    return 'New file created successfully at: '+取字段(目标,'displayPath')#面向模型的成功说明

def 文件内替换(上下文,政策,路径,旧串,新串,执行上下文):#字面量替换恰好一处
    """把文件中恰好一处 `old_str` 替换为 `new_str`。"""
    沙箱政策=政策.解析(执行上下文)#本次沙箱策略
    信号=取字段(执行上下文,'signal')#中止信号
    目标=解析目标(上下文,路径,信号)#解析目标
    def 默认编辑意图():#瀑布末端默认意图
        """没有编辑意图监听器时返回空。"""
        return None#无意图
    意图=解开(上下文.waterfall('fs/edit-intent',目标,执行上下文,默认编辑意图))#询问编辑意图
    旧值=命令必填(旧串,'old_str','str_replace',False)#old_str必填且非空
    新值='' if 新串 is None else 新串#缺省new_str视为删除
    信息=状态已存在(上下文,目标,'str_replace',执行上下文)#确认存在且非目录
    if 取字段(信息,'type')!='file':#不是普通文件
        raise 文件系统错误('cannot edit "'+取字段(目标,'displayPath')+'": not a regular file','FS_NOT_REGULAR_FILE')#拒绝特殊文件
    之前=解开(上下文.fs.readText(目标,信号))#读出替换前全文
    下标们=匹配下标(之前,旧值)#找出每一处字面量
    if len(下标们)==0:#一处都没有
        raise 文件系统错误(#报未找到
            'No replacement was performed, old_str `'+旧值+'` did not appear verbatim in '+取字段(目标,'displayPath')+'.',#必须逐字匹配
            'FS_EDIT_NOT_FOUND',#未找到码
        )#未找到结束
    if len(下标们)>1:#多于一处则拒绝，避免误替换
        行号们=下标行号(之前,下标们)#各处行号
        raise 文件系统错误(#报不唯一
            'No replacement was performed. Multiple occurrences of old_str `'+旧值+'` in lines ['+', '.join(str(项) for 项 in 行号们)+']. Please ensure it is unique',#列出所有行号
            'FS_AMBIGUOUS_EDIT',#不唯一码
        )#不唯一结束
    下标=下标们[0]#第一处（唯一）
    之后=之前[0:下标]+新值+之前[下标+len(旧值):]#拼接替换后文本
    if 意图 is None:#没有编辑意图则用stat版本
        写意图={'kind':'replaceIfVersion','version':取字段(信息,'version')}#按stat版本替换
    else:#按意图版本替换
        写意图={'kind':'replaceIfVersion','version':取字段(意图,'version')}#按意图版本替换
    try:#按版本守卫替换
        结果=解开(上下文.fs.writeText(#写入替换后全文
            目标,#目标
            之后,#替换后文本
            写意图,#写意图
            信号,#中止信号
            沙箱政策,#沙箱策略
        ))#writeText结束
    except BaseException as 异常:#写入失败
        raise 政策.映射错误(异常,沙箱政策)#沙箱拒绝换成带模式标记的错误
    上下文.emit('fs/observed',目标,{'kind':'present','version':取字段(结果,'version')},执行上下文)#记录存在观察
    return 'The file '+取字段(目标,'displayPath')+' has been edited successfully.'#面向模型的成功说明

def 文件内插入(上下文,政策,路径,插入行,新串,执行上下文):#在指定行后插入文本
    """在指定行后插入 `new_str`。"""
    if 插入行 is None:#insert必填insert_line
        raise 错误('Parameter `insert_line` is required for command: insert')#缺失insert_line
    值=命令必填(新串,'new_str','insert')#insert必填new_str
    沙箱政策=政策.解析(执行上下文)#本次沙箱策略
    信号=取字段(执行上下文,'signal')#中止信号
    目标=解析目标(上下文,路径,信号)#解析目标
    def 默认编辑意图():#瀑布末端默认意图
        """没有编辑意图监听器时返回空。"""
        return None#无意图
    意图=解开(上下文.waterfall('fs/edit-intent',目标,执行上下文,默认编辑意图))#询问编辑意图
    信息=状态已存在(上下文,目标,'insert',执行上下文)#确认存在且非目录
    if 取字段(信息,'type')!='file':#不是普通文件
        raise 文件系统错误('cannot insert into "'+取字段(目标,'displayPath')+'": not a regular file','FS_NOT_REGULAR_FILE')#拒绝特殊文件
    之前=解开(上下文.fs.readText(目标,信号))#读出插入前全文
    行们=之前.split('\n')#按行拆分
    if (not 是否整数(插入行)) or 插入行<0 or 插入行>len(行们):#行号必须落在[0, 行数]
        raise 错误(#报insert_line越界
            'Invalid `insert_line` parameter: '+str(插入行)+'. It should be within the range of lines of the file: [0, '+str(len(行们))+']',#允许插在末尾
        )#越界结束
    之后='\n'.join(#插入后的行
        行们[0:插入行]#插入点之前
        +值.split('\n')#插入文本按行拆开
        +行们[插入行:]#插入点之后
    )#重新拼成全文
    if 意图 is None:#没有编辑意图则用stat版本
        期望={'kind':'replaceIfVersion','version':取字段(信息,'version')}#按stat版本替换
    else:#按意图版本替换
        期望={'kind':'replaceIfVersion','version':取字段(意图,'version')}#按意图版本替换
    try:#按版本守卫写入
        结果=解开(上下文.fs.writeText(目标,之后,期望,信号,沙箱政策))#写入插入后全文
    except BaseException as 异常:#写入失败
        raise 政策.映射错误(异常,沙箱政策)#沙箱拒绝换成带模式标记的错误
    上下文.emit('fs/observed',目标,{'kind':'present','version':取字段(结果,'version')},执行上下文)#记录存在观察
    return 'The file '+取字段(目标,'displayPath')+' has been edited successfully.'#面向模型的成功说明

def 呈现编辑器调用(参数):#调用中的编辑器卡片
    """调用中展示：`view`/`insert` 用通用卡片，`create`/`str_replace` 用 diff 卡片。"""
    命令=取字段(参数,'command')#当前命令
    路径=取字段(参数,'path')#目标路径
    if 命令=='view':#查看
        return {#通用读卡片
            'card':'generic',#通用卡片
            'title':'view '+路径,#标题带路径
            'kind':'read',#读操作
            'locations':[{'path':路径}],#定位到该路径
        }#view卡片结束
    if 命令=='create':#创建
        文件文本=取字段(参数,'file_text')#create的新文件内容
        return {#diff卡片，旧文本为空
            'card':'diff',#diff卡片
            'title':'create '+路径,#标题带路径
            'diffs':[{'path':路径,'oldText':None,'newText':'' if 文件文本 is None else 文件文本}],#新建：无旧文本
            'locations':[{'path':路径}],#定位到该路径
        }#create卡片结束
    if 命令=='str_replace':#字面量替换
        旧串=取字段(参数,'old_str')#被替换原文
        新串=取字段(参数,'new_str')#替换文本
        return {#diff卡片展示替换前后
            'card':'diff',#diff卡片
            'title':'str_replace '+路径,#标题带路径
            'diffs':[{#一处替换diff
                'path':路径,#目标路径
                'oldText':None if 旧串 is None else 旧串,#被替换原文
                'newText':'' if 新串 is None else 新串,#替换文本
            }],#diffs结束
            'locations':[{'path':路径}],#定位到该路径
        }#str_replace卡片结束
    if 命令=='insert':#插入
        插入行=取字段(参数,'insert_line')#insert的插入行
        定位={'path':路径}#定位到该路径
        if 插入行 is not None:#有insert_line则换成1基行号
            定位['line']=max(1,插入行+1)#1基行号
        return {#通用编辑卡片
            'card':'generic',#通用卡片
            'title':'insert '+路径,#标题带路径
            'kind':'edit',#编辑操作
            'locations':[定位],#locations结束
        }#insert卡片结束
    raise 错误('unsupported str_replace_editor command: '+str(命令))#封闭联合穷尽

def 登记字符串替换编辑器(上下文,已解析配置):#注册str_replace_editor
    """注册面向模型的 `str_replace_editor` 工具。"""
    政策=变更政策(上下文)#本次插件的变更策略
    def 渲染输出(_参数,值):#原样渲染为文本块
        """规范输出为字符串文本块。"""
        return [{'type':'text','text':值}]#原样渲染为文本块
    def 执行(参数,执行上下文):#按命令分派
        """按四种命令分派执行。"""
        命令=取字段(参数,'command')#当前命令
        if 命令=='view':#查看
            return 查看路径(上下文,取字段(参数,'path'),取字段(参数,'view_range'),已解析配置['maxOutputChars'],执行上下文)#文件或目录视图
        if 命令=='create':#创建
            return 创建文件(上下文,政策,取字段(参数,'path'),取字段(参数,'file_text'),执行上下文)#仅在不存在时创建
        if 命令=='str_replace':#字面量替换
            return 文件内替换(#恰好一处替换
                上下文,#插件上下文
                政策,#变更策略
                取字段(参数,'path'),#目标路径
                取字段(参数,'old_str'),#原文
                取字段(参数,'new_str'),#新文
                执行上下文,#运行上下文
            )#replaceInFile结束
        if 命令=='insert':#插入
            return 文件内插入(#在指定行后插入
                上下文,#插件上下文
                政策,#变更策略
                取字段(参数,'path'),#目标路径
                取字段(参数,'insert_line'),#插入行
                取字段(参数,'new_str'),#插入文本
                执行上下文,#运行上下文
            )#insertInFile结束
        raise 错误('unsupported str_replace_editor command: '+str(命令))#封闭联合穷尽
    上下文.tools.register(定义工具({#定义并注册工具
        'name':'str_replace_editor',#工具名
        'description':已解析配置['description'],#面向模型的描述
        'parameters':{#面向模型的参数模式
            'command':{#要运行的命令
                'type':'string',#字符串
                'required':True,#必填
                'enum':['view','create','str_replace','insert'],#四种命令
                'description':'The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`.',#命令说明
            },#command结束
            'path':{#绝对路径
                'type':'string',#字符串
                'required':True,#必填
                'description':'Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.',#路径说明
            },#path结束
            'file_text':{#create的文件内容
                'type':'string',#字符串
                'description':'Required parameter of `create` command, with the content of the file to be created.',#create必填
            },#file_text结束
            'insert_line':{#insert的插入行
                'type':'integer',#整数
                'description':'Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.',#插在该行之后
            },#insert_line结束
            'new_str':{#替换或插入文本
                'type':'string',#字符串
                'description':'Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.',#str_replace可选，insert必填
            },#new_str结束
            'old_str':{#被替换原文
                'type':'string',#字符串
                'description':'Required parameter of `str_replace` command containing the string in `path` to replace.',#str_replace必填
            },#old_str结束
            'view_range':{#view的行范围
                'type':'array',#数组
                'items':{'type':'integer'},#整数项
                'description':'Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.',#1基行范围，-1到末尾
            },#view_range结束
        },#parameters结束
        'output':{#规范输出为字符串
            'schema':{'type':'string'},#字符串结果
            'render':渲染输出,#原样渲染为文本块
        },#output结束
        'execute':执行,#按命令分派
        'presentCall':呈现编辑器调用,#调用中卡片
    }))#defineTool与register结束

def 落实配置(配置值):#填入默认值并校验
    """schemastery 填入默认值之后的运行配置校验。"""
    if 配置值 is None:#缺省配置
        配置值={}#空映射
    最大=取字段(配置值,'maxOutputChars')#视图字符上限
    if 最大 is None:#缺省
        最大=16_000#默认上限
    描述=取字段(配置值,'description')#工具描述
    if 描述 is None:#缺省
        描述=默认描述#默认描述
    if (not 是否安全整数(最大)) or 最大<=0:#必须是正的安全整数
        raise 错误('tool-str-replace-editor: maxOutputChars must be a positive safe integer')#加载时拒绝
    if len(描述.strip())==0:#描述不得空白
        raise 错误('tool-str-replace-editor: description must be non-empty')#加载时拒绝
    return {#已填满默认值的配置
        'maxOutputChars':最大,#视图字符上限
        'description':描述,#面向模型的工具描述
    }#resolved结束

def 应用(上下文,配置值=None):#注册str_replace_editor
    """在 `ctx.fs` 上注册一个 `str_replace_editor` 工具。"""
    已解析=落实配置(配置值)#填入默认值
    登记字符串替换编辑器(上下文,已解析)#注册工具

apply=应用#Cordis插件入口
default=应用#Cordis默认导出
默认=应用#中文默认导出

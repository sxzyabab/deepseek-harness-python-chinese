"""纯读展示：把提供方已解码文本变成有界、带行号的窗口和面向模型的信封。块扫描会封顶当前行，因此即使一行没有换行的巨型行也不能无界增长内存。对齐上游 tool-fs/src/read-render.ts。"""
import fs#文件系统错误类
from .辅助 import 试取,是否整数#字段读取与整数判定

读最大行长=2000#默认单行字符上限
读最大字节=50*1024#默认窗口50KiB

扩展名语言表={#扩展名到语言提示
    'ts':'ts','tsx':'tsx','mts':'ts','cts':'ts',#TypeScript
    'js':'js','jsx':'jsx','mjs':'js','cjs':'js',#JavaScript
    'json':'json','jsonc':'json',#JSON
    'py':'py','rb':'rb','go':'go','rs':'rs','java':'java',#常见后端语言
    'c':'c','h':'c','cc':'cpp','cpp':'cpp','hpp':'cpp','cxx':'cpp',#C/C++
    'cs':'cs','kt':'kotlin','swift':'swift','php':'php',#其他编译语言
    'sh':'sh','bash':'sh','zsh':'sh',#shell
    'yaml':'yaml','yml':'yaml','toml':'toml','ini':'ini',#配置
    'md':'md','markdown':'md','mdx':'mdx',#Markdown
    'html':'html','htm':'html','css':'css','scss':'scss','less':'less',#Web
    'sql':'sql','xml':'xml','lua':'lua',#其他
}#扩展名语言表结束

def 新建累加器():#新建空窗口累加器
    """新建空窗口累加器。"""
    return {'lines':[],'totalLines':0,'outputBytes':0,'truncatedByBytes':False}#全部从零开始

def 截断行(行,最大行长):#按字符上限截断一行
    """按字符上限截断一行。"""
    if len(行)>最大行长:#超长
        return 行[0:最大行长]+'... (line truncated to '+str(最大行长)+' chars)'#截断并加后缀
    return 行#原样

def 行字节大小(行,当前行数):#计算该行计入窗口时的UTF-8字节
    """计算该行计入窗口时的 UTF-8 字节。非首行再加一个换行字节。"""
    return len(行.encode('utf-8'))+(1 if 当前行数>0 else 0)#UTF-8字节加可选换行

def 消费行(累加器,原始行,请求):#把一行计入累加器
    """把一行计入累加器。已截断、尚未到窗口或窗口已满则只计数。"""
    累加器['totalLines']=累加器['totalLines']+1#总行数加一
    if 累加器['truncatedByBytes'] or 累加器['totalLines']<请求['offset'] or len(累加器['lines'])>=请求['limit']:#只计数
        return#不再收入
    文本=截断行(原始行,请求['maxLineLength'])#按字符上限截断
    字节=行字节大小(文本,len(累加器['lines']))#该行将占用的字节
    if 累加器['outputBytes']+字节>请求['maxBytes']:#加上会超过字节上限
        累加器['truncatedByBytes']=True#标记字节截断
        return#不再收入此行
    累加器['outputBytes']=累加器['outputBytes']+字节#累加已用字节
    累加器['lines'].append({'number':累加器['totalLines'],'text':文本})#收入窗口

def 去掉回车(行):#去掉行尾CR
    """去掉行尾 CR。"""
    if 行.endswith('\r'):#CRLF拆分后留下的CR
        return 行[0:-1]#去掉CR
    return 行#原样

def 收尾(累加器,请求,展示路径):#扫描结束后校验offset并打包结果
    """扫描结束后校验 offset 并打包结果。offset 越过 EOF 时抛出 FS_NOT_FOUND（空文件读第 1 行除外）。"""
    if (not 累加器['truncatedByBytes']) and 请求['offset']>累加器['totalLines'] and not (累加器['totalLines']==0 and 请求['offset']==1):#offset越过EOF
        raise fs.文件系统错误('offset '+str(请求['offset'])+' is out of range for "'+展示路径+'" ('+str(累加器['totalLines'])+' lines)','FS_NOT_FOUND')#按未找到报告越界
    return {'lines':累加器['lines'],'totalLines':累加器['totalLines'],'truncatedByBytes':累加器['truncatedByBytes']}#打包窗口结果

def 构建窗口(块们,请求,展示路径):#从文本块构建有界行窗口
    """从流式或整文件块构建一个窗口，强制行与字节上限，同时仍扫描到精确总行数。"""
    累加器=新建累加器()#空累加器
    行缓冲上限=请求['maxLineLength']+1#行缓冲上限
    行缓冲=''#当前尚未遇到换行的行缓冲
    def 追加到行缓冲(片段):#把片段追加到行缓冲并封顶
        """把片段追加到行缓冲并封顶。"""
        nonlocal 行缓冲#修改外层缓冲
        if len(行缓冲)>=行缓冲上限:#已满则丢弃后续
            return#丢弃
        行缓冲=行缓冲+片段#追加
        if len(行缓冲)>行缓冲上限:#超出则裁到上限
            行缓冲=行缓冲[0:行缓冲上限]#裁到上限
    def 刷新行():#把当前行缓冲交给累加器
        """把当前行缓冲交给累加器。"""
        nonlocal 行缓冲#修改外层缓冲
        消费行(累加器,去掉回车(行缓冲),请求)#去掉CR后计入
        行缓冲=''#清空缓冲
    for 块 in 块们:#按块扫描
        起点=0#本块尚未消费的起点
        while True:#本块内还有换行
            换行位置=块.find('\n',起点)#下一个换行位置
            if 换行位置==-1:#没有换行
                break#跳出换行循环
            追加到行缓冲(块[起点:换行位置])#换行前的片段
            刷新行()#完成一行
            起点=换行位置+1#跳过换行
        追加到行缓冲(块[起点:])#块尾没有换行的残余
    if len(行缓冲)>0:#文件不以换行结束
        刷新行()#刷新最后一行
    return 收尾(累加器,请求,展示路径)#校验并打包

def 格式化读输出(展示路径,结果):#格式化read信封
    """把读结果格式化成一块 OpenCode 风格的带行号文本体。"""
    窗口行=结果['lines']#窗口行
    if len(窗口行)>0:#有窗口行
        末行=窗口行[-1]['number']#窗口末行
    else:#空窗口
        末行=max(0,结果['offset']-1)#offset前一行
    if 试取(结果,'truncatedByBytes'):#因字节上限截断
        页脚='(Output capped. Showing lines '+str(结果['offset'])+'-'+str(末行)+'. Use offset='+str(末行+1)+' to continue.)'#提示用下一offset继续
    elif 末行<结果['totalLines']:#行窗口未到EOF
        页脚='(Showing lines '+str(结果['offset'])+'-'+str(末行)+' of '+str(结果['totalLines'])+'. Use offset='+str(末行+1)+' to continue.)'#提示继续
    else:#已到文件末
        页脚='(End of file - total '+str(结果['totalLines'])+' lines)'#EOF页脚
    if len(窗口行)>0:#有窗口行
        正文='\n'.join(str(行['number'])+': '+行['text'] for 行 in 窗口行)+'\n\n'+页脚#编号行加页脚
    else:#空窗口
        正文=页脚#只给页脚
    return '<path>'+展示路径+'</path>\n<type>file</type>\n<content>\n'+正文+'\n</content>'#完整信封

def 路径语言(路径):#按路径扩展名推导高亮语言
    """从读路径的文件扩展名推导语法高亮语言提示。对扩展名纯函数且不区分大小写；点文件和未知扩展名得到 None。"""
    斜杠=路径.rfind('/')#最后一个正斜杠
    反斜杠=路径.rfind('\\')#最后一个反斜杠
    基名=路径[max(斜杠,反斜杠)+1:]#取基名
    点=基名.rfind('.')#最后一个点
    if 点<=0:#无扩展名或点文件
        return None#无语言
    扩展名=基名[点+1:].lower()#小写扩展名
    if 扩展名 in 扩展名语言表:#有映射
        return 扩展名语言表[扩展名]#语言提示
    return None#无映射

def 是否文本行(值):#收窄为带行号文本行
    """value 是否为合法带行号文本行。number 必须是 1 基整数行号。"""
    if not isinstance(值,dict):#必须是普通对象
        return False#不是对象
    行号=试取(值,'number')#行号
    文本=试取(值,'text')#文本
    return 是否整数(行号) and 行号>=1 and isinstance(文本,str)#1基整数行号加字符串文本

def 从元数据取读窗口(元数据):#从结果meta收窄出read窗口
    """把不透明的现场或回放结果元数据收窄为结构化读窗口。畸形或语义非法时为 None。"""
    if not isinstance(元数据,dict):#必须是普通对象
        return None#畸形
    路径=试取(元数据,'path')#路径
    偏移=试取(元数据,'offset')#起始行
    窗口行=试取(元数据,'lines')#窗口行
    总行数=试取(元数据,'totalLines')#总行数
    语言=试取(元数据,'lang')#可选语言
    if (not isinstance(路径,str)) or (not 是否整数(总行数)) or (not 是否整数(偏移)):#基础类型
        return None#畸形
    if 偏移<1:#offset必须是1基
        return None#畸形
    if 总行数<0:#总行数必须非负
        return None#畸形
    if (not isinstance(窗口行,list)) or (not all(是否文本行(行) for 行 in 窗口行)):#每行必须合法
        return None#畸形
    if 语言 is not None and not isinstance(语言,str):#lang要么没有要么是字符串
        return None#畸形
    上一行号=偏移-1#上一行号，初始为offset前一行
    for 行 in 窗口行:#检查行号序列
        行号=行['number']#行号
        if 行号<=上一行号 or 行号>总行数:#必须严格递增且不超过总行数
            return None#畸形
        上一行号=行号#更新上一行号
    结果={'path':路径,'offset':偏移,'lines':窗口行,'totalLines':总行数}#已校验meta
    if 语言 is not None:#有语言提示
        结果['lang']=语言#带上
    return 结果#打包

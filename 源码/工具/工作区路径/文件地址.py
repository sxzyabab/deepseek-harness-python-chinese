from urllib.parse import quote,unquote#段编解码

__all__=['会话文件地址','绝对文件地址','解析文件地址']#公开面

文件地址前缀='dsh-resource://file/'#文件地址前缀

def 编码段(段):#编码一段
    """组件编码一个 id 或路径段，保留 `:` 字面以便盘符。"""
    return quote(段,safe=':')#编码并保留冒号

def 编码路径(路径):#编码路径
    """按段编码 `/` 分隔路径。"""
    return '/'.join(编码段(段) for 段 in 路径.split('/'))#分段编码再拼接

def 是否盘符段(段):#是否盘符段
    """解码后的首路径段是否为 Windows 盘符（`C:`）。"""
    return 段 is not None and len(段)==2 and 段[0].isalpha() and 段[1]==':'#盘符形态

def 会话文件地址(会话标识,路径):#会话文件地址
    """构建经一个会话读取的文件地址。"""
    规范=路径.replace('\\','/')#正斜杠
    while 规范.startswith('./'):#去掉前导./
        规范=规范[2:]#剥一层
    return 文件地址前缀+'session/'+编码段(会话标识)+'/'+编码路径(规范)#拼地址

def 绝对文件地址(路径):#绝对文件地址
    """按绝对路径构建文件地址。"""
    规范=路径.replace('\\','/')#正斜杠
    是unc=规范.startswith('//')#是否UNC
    绝对=规范.lstrip('/')#去掉前导斜杠
    return 文件地址前缀+'absolute/'+('/' if 是unc else '')+编码路径(绝对)#拼地址

def 解析文件地址(地址):#解析文件地址
    """把文件地址读回各部分，不解析 `.` 或 `..`。"""
    try:#解析前缀
        if not 地址.startswith(文件地址前缀):#非文件资源前缀
            return None#非本协议
        截=地址[len(文件地址前缀):]#去掉前缀
        for 界 in ('?','#'):#查询或片段
            位=截.find(界)#起点
            if 位!=-1:#有后缀
                截=截[:位]#去掉
        段列表=截.split('/')#拆段
        if len(段列表)==0:#空
            return None#无效
        作用域=段列表[0]#首段
        其余=段列表[1:]#余段
        if 作用域=='session':#会话作用域
            if len(其余)==0:#缺id
                return None#无效
            标识=其余[0]#id
            路径段=其余[1:]#路径段
            if 标识=='' or len(路径段)==0:#缺段
                return None#无效
            return {'scope':'session','sessionId':unquote(标识),'path':'/'.join(unquote(段) for 段 in 路径段)}#会话地址
        if 作用域=='absolute':#绝对作用域
            是unc=len(其余)>0 and 其余[0]=='' and len(其余)>1#UNC空首段
            路径段=[unquote(段) for 段 in (其余[1:] if 是unc else 其余)]#解码段
            if len(路径段)==0 or 路径段[0]=='':#无路径
                return None#无效
            if 是unc:#UNC
                return {'scope':'absolute','path':'//'+'/'.join(路径段)}#UNC路径
            if 是否盘符段(路径段[0]):#盘符
                return {'scope':'absolute','path':'/'.join(路径段)}#盘符路径
            return {'scope':'absolute','path':'/'+'/'.join(路径段)}#POSIX
        return None#未知作用域
    except (TypeError,ValueError,AttributeError):
        return None#非文件地址

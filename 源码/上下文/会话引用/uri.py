"""规范会话 URI 与行内提及编码。"""
import base64,json,re#base64url、JSON与提及正则
from session import 会话标识#导入会话id品牌
from .配置 import 会话引用错误#导入会话引用错误

会话引用方案='dsh-session:'#会话引用URI方案前缀
载荷字符=re.compile(r'^[A-Za-z0-9_-]+$')#base64url字符集
提及模式=re.compile(r'@\[((?:\\.|[^\\\]])*)\]\((dsh-session:[^\s)]*)\)|(dsh-session:[A-Za-z0-9_-]+)')#匹配Markdown提及或裸URI

def 编码会话引用URI(会话号):#编码规范会话引用URI
    """把任意会话 id 字符串编码为无损的规范 URI。"""
    载荷=base64.urlsafe_b64encode(json.dumps(会话号,ensure_ascii=False).encode('utf-8')).decode('ascii').rstrip('=')#JSON后按utf8做base64url
    return 会话引用方案+载荷#方案前缀加载荷

def 解码会话引用URI(统一资源):#解码规范会话引用URI
    """解码并规范化一条会话引用 URI。"""
    if not 统一资源.startswith(会话引用方案):#不是本方案则非法
        raise 非法URI(统一资源)#抛出非法URI错误
    载荷=统一资源[len(会话引用方案):]#去掉方案前缀得到载荷
    if not 载荷字符.match(载荷):#载荷须为base64url字符
        raise 非法URI(统一资源)#非法载荷
    try:#尝试解码并校验规范形
        填充=(4-len(载荷)%4)%4#补回padding
        解析=json.loads(base64.urlsafe_b64decode(载荷+'='*填充).decode('utf-8'))#base64url还原后JSON解析
        if not isinstance(解析,str):#解析结果必须是字符串
            raise TypeError('decoded session id is not a string')#类型非法
        会话号=会话标识(解析)#打上会话id品牌
        if 编码会话引用URI(会话号)!=统一资源:#须与规范编码完全一致
            raise TypeError('URI is not canonical')#非规范形
        return 会话号#返回已校验会话id
    except 会话引用错误:#已是本包错误则原样抛
        raise#不包装
    except Exception as 错误:#解码、解析或规范检查失败
        raise 非法URI(统一资源,错误)#统一包装为非法URI错误

def 格式化会话引用提及(引用):#格式化Markdown提及
    """渲染携带规范 URI 的宿主中立 Markdown 提及。"""
    标签原文=引用.get('label') if isinstance(引用,dict) else getattr(引用,'label',None)#可选标签
    会话号=引用.get('sessionId') if isinstance(引用,dict) else getattr(引用,'sessionId')#源会话id
    标签=转义标签(标签原文 if 标签原文 is not None else 会话号)#标签缺省用会话id并转义
    return '@['+标签+']('+编码会话引用URI(会话号)+')'#拼成@[标签](URI)

def 解析会话引用文本(文本):#解析文本中的会话引用
    """从一段文本抽出 Markdown 提及与裸规范 URI。显式 Markdown 提及在 URI 畸形时失败。裸文本仅当载荷非空且呈 base64url 形态才当作引用，若该候选不是规范形仍失败。"""
    引用们=[]#按出现顺序收集引用
    def 替换(匹配):#把匹配替换为@标签
        """替换回调：解码 URI、记下引用、返回可读 @标签。"""
        原始标签=匹配.group(1)#Markdown标签原文
        MarkdownURI=匹配.group(2)#Markdown里的URI
        裸URI=匹配.group(3)#裸URI
        统一资源=MarkdownURI if MarkdownURI is not None else 裸URI#两分支必有一个URI
        if 统一资源 is None:#缺失URI则引用非法
            raise 会话引用错误('session reference URI is missing','SESSION_REFERENCE_INVALID_REFERENCE')#缺失URI
        会话号=解码会话引用URI(统一资源)#解码并校验规范URI
        标签=会话号 if 原始标签 is None else 还原标签(原始标签)#裸URI用会话id，否则还原标签
        引用们.append({'sessionId':会话号,'label':标签})#按出现顺序记下引用
        return '@'+标签#正文里改成可读@标签
    渲染=提及模式.sub(替换,文本)#替换全部匹配
    return {'text':渲染,'references':引用们}#返回替换文本与引用列表

def 转义标签(标签):#转义提及标签里的反斜杠与右方括号
    """转义提及标签里的反斜杠与右方括号。"""
    def 替换一处(匹配):#给命中字符加反斜杠
        """给命中字符加反斜杠。"""
        return '\\'+匹配.group(0)#转义
    return re.sub(r'[\\\]]',替换一处,标签)#给\和]加反斜杠

def 还原标签(标签):#还原提及标签转义
    """还原提及标签转义。"""
    return re.sub(r'\\(.)',r'\1',标签)#去掉反斜杠只留被转义字符

def 非法URI(统一资源,原因=None):#构造非法URI错误
    """构造非法 URI 错误。"""
    选项=None if 原因 is None else {'cause':原因}#有cause则挂上
    return 会话引用错误('invalid session reference URI '+json.dumps(统一资源,ensure_ascii=False),'SESSION_REFERENCE_INVALID_REFERENCE',选项)#包装为会话引用错误

已解析会话引用文本字段=('text','references')#文本解析结果字段
"""共享 Files 解析、有界陈旧 id 恢复与归一化图诊断。"""
import re#分类正则
from ...工具.超时 import 截止#单次上传截止
from ...llm import 大模型错误#LLM 错误

__all__=('文件解析失败','请求文件')#仅中文公开名

原因在图前=re.compile(r'(?:unsupported|invalid|cannot read|failed to (?:decode|process)).{0,40}image',re.I|re.ASCII)#原因在 image 前
图在原因前=re.compile(r'image.{0,40}(?:unsupported|invalid|cannot be decoded)',re.I|re.ASCII)#image 在原因前
文件词=re.compile(r'\bfile(?:[_ -]?(?:id|api|not[_ -]?found|deleted|expired))?',re.I|re.ASCII)#file 词
缺失词=re.compile(r'(?:expired|not[_ -]?found|deleted|do(?:es)? not exist|not created under (?:this|your) account)',re.I|re.ASCII)#缺失
非法标识=re.compile(r'(?:invalid.{0,20}file[_ -]?(?:id|api)|file[_ -]?(?:id|api).{0,20}invalid)',re.I|re.ASCII)#非法 id
标识边界=re.compile(r'[\w-]',re.UNICODE)#标识前后边界

class 文件解析失败(Exception):
    """一次文件上传失败，可供整请求内联回落。"""
    def __init__(自身,原因):#记下原因
        """用固定英文消息包装原因。"""
        super().__init__('DeepSeek Files API could not resolve a request image.')#英文消息
        自身.name='FileResolutionFailure'#类名
        自身.__cause__=原因 if isinstance(原因,BaseException) else None#原因链

def 提供方拒绝归一化图(细节):#是否拒绝归一化图
    """提供方是否按归一化图拒绝。"""
    return 原因在图前.search(细节) is not None or 图在原因前.search(细节) is not None#措辞命中

def 提供方拒绝文件标识(细节):#是否陈旧文件 id
    """提供方是否按缺失或非法文件 id 拒绝。"""
    return 文件词.search(细节) is not None and (缺失词.search(细节) is not None or 非法标识.search(细节) is not None)#文件且缺失或非法

def 细节点名文件标识(细节,文件标识):#细节是否点名该 id
    """细节文本是否把该文件 id 当作独立词。"""
    起点=细节.find(文件标识)#首次
    while 起点>=0:#逐处
        前=细节[起点-1] if 起点>0 else ''#前一字符
        后下标=起点+len(文件标识)#后一位置
        后=细节[后下标] if 后下标<len(细节) else ''#后一字符
        前界=前=='' or 标识边界.search(前) is None#前边界
        后界=后=='' or 标识边界.search(后) is None#后边界
        if 前界 and 后界:#独立词
            return True#点名
        起点=细节.find(文件标识,起点+1)#下一处
    return False#未点名

def 陈旧映射(文件列表,细节):#选出要失效的映射
    """精确点名优先，否则全部去重后的已用映射。"""
    去重=[]#去重表
    已见=set()#键
    for 文件 in 文件列表:#逐条
        键=文件['version']['variantId']+'\0'+文件['fileId']#去重键
        if 键 in 已见:#已见
            continue#跳过
        已见.add(键)#记下
        去重.append(文件)#收下
    精确=[文件 for 文件 in 去重 if 细节点名文件标识(细节,文件['fileId'])]#点名
    return 精确 if len(精确)>0 else 去重#精确或全部

def 归一化图事实(文件):#单张诊断事实
    """拼出一张已上传图的位置与媒体事实。"""
    版本=文件['version']#请求版本
    附件=版本['attachment']#附件
    名称=附件['name'] if 'name' in 附件 and 附件['name'] is not None else 附件['attachmentId']#展示名
    色彩='sRGBA' if 版本.get('hasAlpha') else 'sRGB'#色空间
    位置=文件['location']#线路位置
    return '"'+str(名称)+'" at message '+str(位置['message'])+', image '+str(位置['image'])+' ('+str(版本['mediaType'])+', 8-bit '+色彩+', '+str(版本['width'])+'x'+str(版本['height'])+')'#事实

def 归一化图诊断(文件列表,提供方消息,提供方细节):#归一化图拒绝诊断
    """把归一化图拒绝归到实际上传出现。"""
    精确=None#点名目标
    for 文件 in 文件列表:#逐条
        if 细节点名文件标识(提供方细节,文件['fileId']):#点名
            精确=文件#记下
            break#找到即停
    目标=精确#点名
    if 目标 is None and len(文件列表)==1:#仅一张
        目标=文件列表[0]#唯一候选
    if 目标 is not None:#能定位
        return 'DeepSeek rejected normalized image '+归一化图事实(目标)+': '+提供方消息+'. The provider rejected bytes already normalized by the harness; PNG, JPEG, WebP, and GIF remain supported input formats.'#单张诊断
    候选=[]#去重候选
    已见=set()#键
    for 文件 in 文件列表:#逐条
        位置=文件['location']#位置
        键=文件['version']['variantId']+'\0'+str(位置['message'])+'\0'+str(位置['image'])#去重键
        if 键 in 已见:#已见
            continue#跳过
        已见.add(键)#记下
        候选.append(文件)#收下
    return 'DeepSeek rejected a normalized request image: '+提供方消息+'. Candidate images: '+'; '.join(归一化图事实(项) for 项 in 候选)+'. The provider rejected bytes already normalized by the harness; PNG, JPEG, WebP, and GIF remain supported input formats.'#候选诊断

class 请求文件:#一次模型请求拥有的 Files 状态
    """一次模型请求拥有的 Files 状态，至多一次陈旧 id 重试。"""
    def __init__(自身,文件仓,连接,政策,超时毫秒,信号,活动):
        """记下仓、连接、政策、超时、取消与传输活动回调。"""
        自身.文件仓=文件仓#上传仓
        自身.连接=连接#文件连接事实
        自身.政策=政策#过期政策
        自身.超时毫秒=超时毫秒#单次解析超时
        自身.信号=信号#取消
        自身.活动=活动#传输活动
        自身.已用=[]#本尝试已用文件
        自身.已重试=False#是否已重试过

    def 开始尝试(自身):#重置出现跟踪
        """序列化下一次 HTTP 尝试前重置出现跟踪。"""
        自身.已用=[]#清空

    def 解析(自身,版本,位置):#解析一张保留图
        """在独立上传截止下解析一张保留图，返回可复用提供方 id。"""
        句柄=截止(自身.信号,自身.超时毫秒,'DEEPSEEK_FILES_API_TIMEOUT')#武装截止
        try:#上传
            try:#解析
                已解析=自身.文件仓.确保已上传(版本,自身.连接,自身.政策,句柄.信号)#确保已上传
            except (大模型错误,OSError,RuntimeError,文件解析失败) as 错误:#上传失败
                if 自身.信号 is not None and 自身.信号.is_set():#已中止
                    raise 错误#原样
                raise 文件解析失败(错误) from 错误#整请求回落
            自身.活动()#传输活动
            自身.已用.append({'version':版本,'fileId':已解析['record']['fileId'],'location':位置})#记下
            return 已解析['record']['fileId']#文件 id
        finally:#释放截止
            句柄.释放()#清定时器

    def 重试(自身,细节):#陈旧 id 失效
        """失效被拒绝映射；仅第一次陈旧 id 响应允许再发一次请求。"""
        if len(自身.已用)==0 or not 提供方拒绝文件标识(细节):#无文件或非陈旧
            return False#不重试
        for 文件 in 陈旧映射(自身.已用,细节):#逐条失效
            自身.文件仓.失效(文件['version'],文件['fileId'],自身.连接)#失效
        if 自身.已重试:#已经重试过
            return False#不再
        自身.已重试=True#记下
        return True#允许再发

    def 错误消息(自身,状态,消息,细节):#归一化图诊断
        """把归一化图拒绝归到实际上传出现，否则原样提供方消息。"""
        if 状态==400 and len(自身.已用)>0 and 提供方拒绝归一化图(细节):#400 且像归一化图
            return 归一化图诊断(自身.已用,消息,细节)#诊断
        return 消息#原消息

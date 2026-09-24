"""共享 Files 解析、有界陈旧 id 恢复与归一化图诊断。"""
import re
from ...工具.超时 import 截止,若已中止则抛出

__all__=['文件解析失败','请求文件']

类名前=re.compile(r'(?:unsupported|invalid|cannot read|failed to (?:decode|process)).{0,40}image',re.I)
图前=re.compile(r'image.{0,40}(?:unsupported|invalid|cannot be decoded)',re.I)
文件词=re.compile(r'\bfile(?:[_ -]?(?:id|api|not[_ -]?found|deleted|expired))?',re.I)
缺失=re.compile(r'(?:expired|not[_ -]?found|deleted|do(?:es)? not exist|not created under (?:this|your) account)',re.I)
非法号=re.compile(r'(?:invalid.{0,20}file[_ -]?(?:id|api)|file[_ -]?(?:id|api).{0,20}invalid)',re.I)

class 文件解析失败(Exception):
    """上传失败，整请求可回退内联。"""
    def __init__(自身,原因=None):
        """记下原因。"""
        super().__init__('DeepSeek Files API could not resolve a request image.')
        自身.name='FileResolutionFailure'
        if 原因 is not None:
            自身.__cause__=原因

def 提供方拒归一化图(详情):
    """详情是否像拒归一化图。"""
    return 类名前.search(详情) is not None or 图前.search(详情) is not None

def 提供方拒文件号(详情):
    """详情是否像拒文件 id。"""
    return 文件词.search(详情) is not None and (缺失.search(详情) is not None or 非法号.search(详情) is not None)

def 详情点名文件号(详情,文件号):
    """详情是否独立点名该 id。"""
    起点=详情.find(文件号)
    while 起点>=0:
        前=详情[起点-1] if 起点>0 else None
        后=详情[起点+len(文件号)] if 起点+len(文件号)<len(详情) else None
        前界=前 is None or not (前.isalnum() or 前 in '_-')
        后界=后 is None or not (后.isalnum() or 后 in '_-')
        if 前界 and 后界:
            return True
        起点=详情.find(文件号,起点+1)
    return False

def 陈旧映射(文件列表,详情):
    """选出该作废的映射。"""
    去重={}
    for 项 in 文件列表:
        去重[项['version']['variantId']+'\0'+项['fileId']]=项
    唯一=list(去重.values())
    精确=[项 for 项 in 唯一 if 详情点名文件号(详情,项['fileId'])]
    return 精确 if len(精确)>0 else 唯一

def 归一化图事实(项):
    """诊断用事实串。"""
    版本=项['version']
    名=版本['attachment'].get('name') or 版本['attachment']['attachmentId']
    色='sRGBA' if 版本.get('hasAlpha') else 'sRGB'
    return '"'+str(名)+'" at message '+str(项['location']['message'])+', image '+str(项['location']['image'])+' ('+str(版本['mediaType'])+', 8-bit '+色+', '+str(版本['width'])+'x'+str(版本['height'])+')'

def 归一化图诊断(文件列表,提供方消息,提供方详情):
    """把拒图归到实际上传出现。"""
    精确=None
    for 项 in 文件列表:
        if 详情点名文件号(提供方详情,项['fileId']):
            精确=项
            break
    目标=精确 if 精确 is not None else (文件列表[0] if len(文件列表)==1 else None)
    if 目标 is not None:
        return 'DeepSeek rejected normalized image '+归一化图事实(目标)+': '+提供方消息+'. The provider rejected bytes already normalized by the harness; PNG, JPEG, WebP, and GIF remain supported input formats.'
    候选={}
    for 项 in 文件列表:
        候选[项['version']['variantId']+'\0'+str(项['location']['message'])+'\0'+str(项['location']['image'])]=项
    return 'DeepSeek rejected a normalized request image: '+提供方消息+'. Candidate images: '+'; '.join(归一化图事实(项) for 项 in 候选.values())+'. The provider rejected bytes already normalized by the harness; PNG, JPEG, WebP, and GIF remain supported input formats.'

class 请求文件:
    """一次模型请求拥有的 Files 状态，至多一次陈旧 id 重试。"""
    def __init__(自身,仓,连接,政策,超时毫秒,信号,活动):
        """记下仓、连接、政策与活动脉冲。"""
        自身.仓=仓
        自身.连接=连接
        自身.政策=政策
        自身.超时毫秒=超时毫秒
        自身.信号=信号
        自身.活动=活动
        自身.已用=[]
        自身.已重试=False

    def 开始尝试(自身):
        """下一次 HTTP 序列化前清空出现跟踪。"""
        自身.已用=[]

    def 解析(自身,版本,位置):
        """在自己的上传截止下解析一张保留图。"""
        限=截止(自身.信号,自身.超时毫秒,'DEEPSEEK_FILES_API_TIMEOUT')
        try:
            解析=自身.仓.确保已上传(版本,自身.连接,自身.政策,限.信号)
        except Exception as 错误:
            若已中止则抛出(自身.信号)
            raise 文件解析失败(错误)
        finally:
            限.释放()
        自身.活动()
        自身.已用.append({'version':版本,'fileId':解析['record']['fileId'],'location':位置})
        return 解析['record']['fileId']

    def 重试(自身,详情):
        """作废被拒映射；仅第一次陈旧 id 允许再发请求。"""
        if len(自身.已用)==0 or not 提供方拒文件号(详情):
            return False
        for 项 in 陈旧映射(自身.已用,详情):
            自身.仓.作废(项['version'],项['fileId'],自身.连接)
        if 自身.已重试:
            return False
        自身.已重试=True
        return True

    def 错误消息(自身,状态,消息,详情):
        """把归一化图拒绝归到实际上传出现。"""
        if 状态==400 and len(自身.已用)>0 and 提供方拒归一化图(详情):
            return 归一化图诊断(自身.已用,消息,详情)
        return 消息

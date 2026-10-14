import os

__all__=['pdf工作线程失败','表格预览错误','去掉敏感','页面失败文案']

class 文档预览错误(Exception):
    '本包文档预览登记失败'

    def __init__(自身,消息):
        '记下英文消息'
        super().__init__(消息)#消息原样英文

class pdf工作线程失败(Exception):
    '区分工作线程启动/传输失败与文档解析错误'

    种类='worker'#线路字面量

    def __init__(自身,原因=None):
        '记下原因供诊断'
        super().__init__()#无消息；文案层解释
        自身.__cause__=原因#保留
        自身.name='PdfWorkerFailure'#结构识别名

class 表格预览错误(Exception):
    '与文案无关的表格解析失败类别'
    def __init__(自身,code):
        super().__init__(code)
        自身.code=code
        自身.name='ExcelPreviewError'

def 去掉敏感(文本):
    '去掉绝对路径、用户名和环境变量，留下其余说明'
    用户名=set()
    for 键 in ('USER','USERNAME','LOGNAME'):
        值=os.environ.get(键)
        if isinstance(值,str) and 值!='':
            用户名.add(值)
    环境路径=[]
    for 值 in os.environ.values():
        if isinstance(值,str) and len(值)>=3 and (('\\' in 值) or ('/' in 值)):
            环境路径.append(值.replace('\\','/'))
    留下=[]
    for 词 in str(文本).split():
        去引=词.strip('\'"')
        统一=去引.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        if 统一.startswith('$') or (len(统一)>=3 and 统一[0]=='%' and 统一[-1]=='%'):
            continue
        if 去引 in 用户名 or 统一 in 用户名:
            continue
        命中环境=False
        for 片段 in 环境路径:
            if 片段!='' and 片段 in 统一:
                命中环境=True
                break
        if 命中环境:
            continue
        留下.append(词)
    return ' '.join(留下).strip()

def 页面失败文案(错误):
    '类型名加说明。说明里不放绝对路径、用户名或环境变量。'
    名=type(错误).__name__
    说明=去掉敏感(错误)
    if 说明=='' or 说明==名:
        return 名
    return 名+'：'+说明

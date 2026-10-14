def 去掉绝对路径(文本):
    '失败说明里去掉盘符路径、根路径和家目录路径'
    留下=[]
    for 词 in str(文本).split():
        统一=词.strip('\'"').replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~/'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        留下.append(词)
    return ' '.join(留下).strip()

class cordis客户端错误(Exception):
    'Cordis 客户端包的异常基类。说明去掉绝对路径'
    def __init__(自身,消息=''):
        '说明去掉绝对路径'
        干净=去掉绝对路径(消息)
        if 干净=='':
            干净='cordis客户端错误'
        super().__init__(干净)

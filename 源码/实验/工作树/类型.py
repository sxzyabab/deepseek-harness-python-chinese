'创建工作树的请求、结果与相对路径约束。线协议键保持原文'
__all__=['工作树错误','创建请求字段','创建结果字段','是相对路径','创建结果']#仅中文公开名

创建请求字段=('name','from')#可选新分支名，以及本地提交、分支或标签；缺省由服务生成名称并使用 HEAD
创建结果字段=('path','branch','baseCommit','repositoryRoot')#检出路径、新分支、解析出的提交、源仓库根

class 工作树错误(Exception):
    '工作树服务拒绝非法配置、名称、修订或检出'
    def __init__(自身,消息):
        '用给人看的说明构造'
        super().__init__(消息)#异常文本
        自身.message=消息#工具错误读取的说明

def 是相对路径(值):
    '拒绝空串、反斜杠、冒号、空段、当前段与父段'
    if not isinstance(值,str) or len(值)==0 or '\\' in 值 or ':' in 值:#不是可用的相对路径
        return False#拒绝
    for 段 in 值.split('/'):#逐段
        if len(段)==0 or 段=='.' or 段=='..':#空段或点段
            return False#拒绝
    return True#通过

def 创建结果(路径,分支,基线提交,仓库根):
    '按线协议字段组装一次成功的检出'
    return {'path':路径,'branch':分支,'baseCommit':基线提交,'repositoryRoot':仓库根}#四个线协议字段

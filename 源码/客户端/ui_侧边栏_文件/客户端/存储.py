
__all__=['文件树错误','创建文件存储']#仅中文公开名


class 文件树错误(Exception):
    """本包文件树存储失败。"""

    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文


def _分桶(状态,标签标识):
    """取一 tab 的树桶；`start` 之后的写者都依赖它。状态为 dict。"""
    按标签=状态['byTab']#分桶表
    if 标签标识 not in 按标签:#尚未播种
        raise 文件树错误('ui-sidebar-files: no tree for tab "'+str(标签标识)+'"')#拒绝
    return 按标签[标签标识]#该 tab 的树


def 初值():
    """空分桶表。"""
    return {'byTab':{}}#初态


def 启动(草稿,标签标识,根):
    """在工作区根播种一 tab 的树，根默认展开。"""
    草稿['byTab'][标签标识]={'root':根,'levels':{},'expanded':[根],'scrollTop':0}#播种


def 加载中(草稿,标签标识,路径):
    """标记某目录正在列举。"""
    _分桶(草稿,标签标识)['levels'][路径]={'kind':'loading'}#加载中


def 已加载(草稿,标签标识,路径,层级):
    """记下某目录的内容。层级为 dict：entries / truncated。"""
    _分桶(草稿,标签标识)['levels'][路径]={'kind':'ready','level':层级}#就绪


def 已失败(草稿,标签标识,路径,失败):
    """记下某目录列举失败原因。失败为跨包 RemoteFailure dict。"""
    _分桶(草稿,标签标识)['levels'][路径]={'kind':'failed','failure':失败}#失败


def 已切换(草稿,标签标识,路径):
    """展开已折叠目录，或折叠已展开者；折叠级保留已加载内容。"""
    树=_分桶(草稿,标签标识)#该桶
    展开=树['expanded']#展开列表
    if 路径 in 展开:#已展开则收起
        树['expanded']=[项 for 项 in 展开 if 项!=路径]#去掉
    else:#未展开则打开
        展开.append(路径)#追加


def 已滚动(草稿,标签标识,滚动顶):
    """记下某 tab 体当前滚动偏移（px）。"""
    _分桶(草稿,标签标识)['scrollTop']=滚动顶#滚动顶

def 重置(草稿,标签标识):
    """丢掉全部已加载级，保留展开集合（重新读取的前半）。"""
    _分桶(草稿,标签标识)['levels']={}#清空层级


def 遗忘(草稿,标签标识):
    """忘掉已消失 tab 记录的树。"""
    草稿['byTab']={键:值 for 键,值 in 草稿['byTab'].items() if 键!=标签标识}#过滤


def 创建文件存储():
    """声明文件树存储规格（init / actions），供登记收下；框架按会话铸造实例。"""
    return {#规格进、句柄出（对齐 defineStore 入参）
        'init':初值,#播种
        'actions':{#动作写集合；每个动作点名所写 tab
            'start':启动,#播种根
            'loading':加载中,#标记加载
            'loaded':已加载,#记下内容
            'failed':已失败,#记下失败
            'toggled':已切换,#展开/折叠
            'scrolled':已滚动,#记下滚动
            'reset':重置,#清层级
            'forget':遗忘,#删桶
        },#动作结束
    }#规格结束

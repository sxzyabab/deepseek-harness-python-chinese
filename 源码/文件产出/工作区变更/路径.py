"""变更文件的路径归类与展示形态。"""
import os,tempfile#路径与临时目录
__all__=[#仅中文公开名
    '转斜杠路径','是否位于内','临时根列表','规范路径','是否临时路径','展示路径自','持久路径自','比较展示',
]#公开面结束

def 转斜杠路径(路径):#原生相对路径转斜杠
    """把原生相对路径改成斜杠分隔。"""
    return '/'.join(路径.split(os.sep))#斜杠分隔

def 是否位于内(根,路径):#是否根或其后代
    """路径是否为根本身或位于其下。"""
    相对=os.path.relpath(路径,根)#相对根
    return 相对=='.' or (not 相对.startswith('..') and not os.path.isabs(相对))#根或后代

def 临时根列表(候选=None):#规范化临时根
    """工作区写入沙箱授予的临时目录规范拼写，含符号链接解析形。"""
    if 候选 is None:#默认宿主tmp与平台临时区
        候选=['/tmp',tempfile.gettempdir()]#两处
    根集=set()#去重
    for 根 in 候选:#逐个
        根集.add(根)#原拼写
        根集.add(规范路径(根))#解析后
    return list(根集)#列表

def 规范路径(路径):#符号链接解析
    """符号链接解析后的路径；尚不存在时经最近已存在祖先解析并拼回缺失后缀。"""
    缺失=[]#缺失后缀
    头=路径#当前尝试点
    while True:#向上找已存在祖先
        try:#realpath
            return os.path.join(os.path.realpath(头),*缺失) if len(缺失)>0 else os.path.realpath(头)#拼回
        except OSError:#缺失或不可读
            父=os.path.dirname(头)#上一层
            if 父==头 or os.path.dirname(父)==父:#已到根
                return 路径#整段保留原拼写
            缺失.insert(0,os.path.basename(头))#记下缺失段
            头=父#继续向上

def 是否临时路径(路径,根表):#是否落在临时根下
    """文件是否位于临时根下（工作区外的草稿不进摘要）。"""
    for 根 in 根表:#逐根
        if 是否位于内(根,路径):#命中
            return True#是临时
    return False#否

def 展示路径自(绝对路径,工作目录,仓库根,家目录):#排序与标签路径
    """变更文件的展示路径：工作区或仓库内相对，家目录下 ~，否则绝对；始终斜杠分隔。"""
    if 是否位于内(工作目录,绝对路径) or 是否位于内(仓库根,绝对路径):#工作区或仓库内
        return 转斜杠路径(os.path.relpath(绝对路径,工作目录))#相对工作目录
    if 家目录!='' and 是否位于内(家目录,绝对路径):#家目录下
        return '~/'+转斜杠路径(os.path.relpath(绝对路径,家目录))#波浪号
    return 转斜杠路径(绝对路径)#绝对斜杠形

def 持久路径自(绝对路径,工作目录):#耐久path字段
    """耐久 path：工作目录内相对，否则绝对。"""
    return 转斜杠路径(os.path.relpath(绝对路径,工作目录)) if 是否位于内(工作目录,绝对路径) else 绝对路径#相对或绝对

def 比较展示(甲,乙):#按display码元序
    """按 display 码元序比较；甲乙为带 display 键的 dict。"""
    甲显=甲['display']#甲展示
    乙显=乙['display']#乙展示
    if 甲显<乙显:#小于
        return -1#甲先
    if 甲显>乙显:#大于
        return 1#乙先
    return 0#相等

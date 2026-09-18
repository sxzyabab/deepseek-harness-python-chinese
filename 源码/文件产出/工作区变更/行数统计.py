"""解析 git diff-tree --numstat -z 输出。"""
__all__=['解析行数统计']#仅中文公开名

class 行数统计错误(Exception):#本模块异常
    """行数统计输出畸形。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 解析行数统计(输出):#解析NUL终止的numstat
    """解析 NUL 终止的 numstat 记录；重命名记录空路径后跟旧路径与新路径。输出须完整。"""
    队列=输出.split('\0')#按NUL切开
    if len(队列)==0 or 队列[-1]!='':#须以NUL收尾
        raise 行数统计错误('numstat output is not NUL-terminated')#截断或畸形
    队列.pop()#丢掉末尾空段
    条目表=[]#按输出顺序
    while len(队列)>0:#还有记录
        记录=队列.pop(0)#取出一条
        第一=记录.find('\t')#首个制表
        第二=-1 if 第一<0 else 记录.find('\t',第一+1)#第二个制表
        if 第二<0:#字段不足
            raise 行数统计错误('malformed numstat record: '+记录)#畸形
        新增串=记录[0:第一]#新增列
        删除串=记录[第一+1:第二]#删除列
        路径=记录[第二+1:]#路径列
        目标=路径#默认目标路径
        旧路径=None#无重命名
        if 目标=='':#重命名记录
            旧路径=队列.pop(0) if len(队列)>0 else None#旧路径
            改名后=队列.pop(0) if len(队列)>0 else None#新路径
            if 旧路径 is None or 改名后 is None:#缺段
                raise 行数统计错误('malformed numstat rename record')#畸形
            目标=改名后#新路径
        二进制=新增串=='-'#git用-标二进制
        条目={'path':目标,'added':0 if 二进制 else int(新增串),'deleted':0 if 二进制 else int(删除串),'binary':二进制}#条目
        if 旧路径 is not None:#有重命名
            条目['oldPath']=旧路径#旧路径
        条目表.append(条目)#收下
    return 条目表#输出顺序

import builtins#页面 document 与 window

__all__=['安装文档拖放事件']#仅中文公开名

def 放下目录集(传输,文件表):
    """目录项只能靠 entry API 识别；无该 API 的浏览器用空集。"""
    目录=set()
    文件下标=0
    项表=传输['items'] if 'items' in 传输 else []
    for 项 in 项表:
        种类=项['kind'] if isinstance(项,dict) and 'kind' in 项 else getattr(项,'kind',None)
        if 种类!='file':
            continue
        文件=文件表[文件下标] if 文件下标<len(文件表) else None
        文件下标+=1
        取条目=None
        if isinstance(项,dict) and 'webkitGetAsEntry' in 项:
            取条目=项['webkitGetAsEntry']
        else:
            取条目=getattr(项,'webkitGetAsEntry',None)
        if not callable(取条目):
            continue
        条目=取条目()
        if 条目 is None:
            continue
        是否目录=条目['isDirectory'] if isinstance(条目,dict) and 'isDirectory' in 条目 else getattr(条目,'isDirectory',False)
        if 是否目录 is not True:
            continue
        if 文件 is not None:
            目录.add(文件)
    return 目录

def 安装文档拖放事件(可接受拖放,加入文件,拖放深度,设拖放活动):
    """给一份已挂载附件视图装上整页文件拖放监听。拖放深度为含 current 的计数盒。"""
    文档=builtins.document#页面文档
    窗口=builtins.window#页面窗口
    def 文件传输(事件):
        """只认携带 Files 类型的 DataTransfer。"""
        传输=事件['dataTransfer'] if 'dataTransfer' in 事件 else None#传输
        if 传输 is None:#无
            return None#不是文件拖
        类型表=传输['types'] if 'types' in 传输 else []#类型
        if 'Files' not in 类型表:#无 Files
            return None#不是文件拖
        return 传输#传输
    def 复位():
        """清嵌套计数并关掉活动。"""
        拖放深度['current']=0#清零
        设拖放活动(False)#关
    def 进入(事件):
        """进入一层文件拖。"""
        if 文件传输(事件) is None:#非文件
            return#停
        事件.阻止默认()#占住
        拖放深度['current']=拖放深度['current']+1#加深
        设拖放活动(True)#开
    def 经过(事件):
        """悬停时声明 copy 或 none。"""
        传输=文件传输(事件)#传输
        if 传输 is None:#非文件
            return#停
        事件.阻止默认()#占住
        传输['dropEffect']='copy' if 可接受拖放 else 'none'#效果
    def 离开(事件):
        """离开一层；离开视口则复位。"""
        if 文件传输(事件) is None:#非文件
            return#停
        拖放深度['current']=max(0,拖放深度['current']-1)#减层
        if 拖放深度['current']==0:#到底
            设拖放活动(False)#关
        横坐标=事件['clientX']#X
        纵坐标=事件['clientY']#Y
        离开视口=横坐标<=0 or 纵坐标<=0 or 横坐标>=窗口.innerWidth or 纵坐标>=窗口.innerHeight#视口外
        目标=事件['target']#目标
        if (目标 is 文档.documentElement or 目标 is 文档.body) and 离开视口:#根上离开视口
            复位()#清
    def 放下(事件):
        """放下文件并复位。"""
        传输=文件传输(事件)#传输
        if 传输 is None:#非文件
            return#停
        事件.阻止默认()#占住
        复位()#清
        if 可接受拖放:#接受
            文件表=list(传输['files'])#文件
            加入文件(文件表,放下目录集(传输,文件表))#摄入，第二参为目录集
    窗口.添加监听('dragend',复位)#结束一律复位
    def 拆除():
        """卸下这组监听。"""
        文档.移除监听('dragenter',进入)#卸进入
        文档.移除监听('dragover',经过)#卸经过
        文档.移除监听('dragleave',离开)#卸离开
        文档.移除监听('drop',放下)#卸放下
        窗口.移除监听('dragend',复位)#卸结束
    return 拆除#拆除器

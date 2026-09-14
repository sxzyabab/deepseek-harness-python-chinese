__all__=['匹配文档预览','文档预览注册表']#仅中文公开名


def 匹配文档预览(定义列表,路径):
    """在不查阅可变服务状态的情况下为观察到的定义快照排序。

    定义列表为 dict 列表；返回匹配实现，外部档优先，随后最长后缀。
    """
    归一=路径.replace('\\','/').lower()#归一
    名=归一[归一.rfind('/')+1:]#文件名
    候选=[]#候选
    for 序,定义 in enumerate(定义列表):#登记序
        档=0 if 定义.get('priority')=='builtin' else 1#档位秩
        长度=0#最长后缀
        for 后缀 in 定义.get('extensions',[]):#各后缀
            净=后缀.lower().lstrip('.')#去点
            if 名.endswith('.'+净) and len(净)>长度:#更长匹配
                长度=len(净)#更新
        if 长度>0:#有匹配
            候选.append({'definition':定义,'order':序,'rank':档,'length':长度})#挂上
    候选.sort(key=lambda 项:(-项['rank'],-项['length'],项['order']))#排序
    return [项['definition'] for 项 in 候选]#定义列表


class 文档预览注册表:
    """全部存活实现的可观察注册表，含较低优先级备选。"""

    def __init__(自身):
        """空注册表。"""
        自身._已登记={}#id → 定义
        自身._监听器=set()#监听器
        自身._快照=()#快照

    def 取快照(自身):
        """读取当前登记。"""
        return 自身._快照#快照

    def 订阅(自身,监听器):
        """观察登记变更；返回拆除器。"""
        自身._监听器.add(监听器)#挂上

        def 拆除():
            """卸下监听器。"""
            自身._监听器.discard(监听器)#卸

        return 拆除#拆除器

    def 注册(自身,定义):
        """与匹配的带键槽组件分开登记元数据；返回幂等拆除器。"""
        标识=定义['id']#实现名
        if 标识 in 自身._已登记:#重复
            raise ValueError('documentPreviews: 重复实现 "'+标识+'"')
        自身._已登记[标识]=定义#挂上
        自身._发布()#发布
        存活=[True]#可变旗

        def 拆除():
            """幂等卸下。"""
            if not 存活[0]:#已拆
                return#停
            存活[0]=False#标记
            if 标识 in 自身._已登记:#仍在
                del 自身._已登记[标识]#卸
            自身._发布()#发布

        return 拆除#拆除器

    def 候选(自身,路径):
        """按自动选择顺序列出每个匹配实现。"""
        return 匹配文档预览(自身._快照,路径)#匹配

    def _发布(自身):
        """刷新快照并通知。"""
        自身._快照=tuple(自身._已登记.values())#新快照
        for 监听器 in list(自身._监听器):#通知
            监听器()#回调

    # 与上游 ObservableSnapshot 字段对齐的别名
    getSnapshot=取快照#框架槽形
    subscribe=订阅#框架槽形
    register=注册#框架槽形
    candidates=候选#框架槽形

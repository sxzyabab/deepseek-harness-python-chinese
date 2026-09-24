from ...工具.值 import 深冻结#不可变消息

__all__=['图片省略错误','省略消息图片']#仅中文公开名

class 图片省略错误(Exception):#本包异常基类
    """图片省略投影或选图失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 省略消息图片(消息,下标列表):#把选中出现标为已省略
    """把选中的图片出现投影成不可变已省略块。缺席或已省略则抛错。"""
    图片下标=0#深度优先图片计数
    已选=0#已命中选中项
    def 访问(块列表):#深度优先改写
        """改写本层块；未改动则交还原列表。"""
        nonlocal 图片下标,已选#改外层计数
        下一层=None#惰性拷贝
        下标=0#本层下标
        for 块 in 块列表:#逐块
            投影块=块#默认原块
            if 块['type']=='image':#图片块
                if 已选<len(下标列表) and 图片下标==下标列表[已选]:#命中选中
                    if 'offloaded' in 块 and 块['offloaded'] is True:#已经省略
                        raise 图片省略错误('image/offload: image index '+str(图片下标)+' is already offloaded')#重复
                    投影块=dict(块)#复制外壳
                    投影块['offloaded']=True#标已省略
                    已选+=1#前进选中
                图片下标+=1#计数所有出现
            if 投影块 is not 块:#本块改了
                if 下一层 is None:#首次改写
                    下一层=list(块列表[0:下标])#拷贝前缀
                下一层.append(投影块)#推入改写块
            elif 下一层 is not None:#已在拷贝
                下一层.append(投影块)#推入原块
            下标+=1#前进
        if 下一层 is None:#未改写
            return 块列表#原列表
        return 下一层#新列表
    内容=访问(消息['content'])#改写内容
    if 已选!=len(下标列表):#有选中未命中
        raise 图片省略错误('image/offload: image index '+str(下标列表[已选])+' does not exist')#缺席
    结果=dict(消息)#复制外壳
    结果['content']=内容#写入
    return 深冻结(结果)#不可变

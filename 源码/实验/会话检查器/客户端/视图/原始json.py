'把还活着的对象写成 JSON。循环的位置存储标成循环，格式失败不拆掉视图'

import json#标准 JSON

class 检查器json书写器:
    '只把祖先算作循环。兄弟之间的再次引用仍写出完整值'
    def __init__(自身):
        '祖先栈和 Map、Set 转出来的容器'
        自身.祖先=[]#当前路径上的对象
        自身.容器={}#原对象身份到已经转过的容器

    def 写入(自身,值):
        '按两格缩进写出。不能序列化时返回空文本'
        try:#书写器自己的失败交给外层
            结果=自身.转换(None,值)#从根转换
            文本=json.dumps(结果,ensure_ascii=False,indent=2)#两格缩进
        except (TypeError,ValueError):#仍有不可序列化的值
            return ''#与 stringify 得不到字符串时一样
        if not isinstance(文本,str):#没有文本
            return ''#空
        return 文本#JSON 文本

    def 转换(自身,父,值):
        '按父对象退栈，再决定是原值、容器还是循环标记'
        if isinstance(值,bool) or 值 is None or isinstance(值,(int,float,str)):#JSON 标量
            return 值#原样
        if not isinstance(值,(dict,list,set,tuple)):#其余当文本留下，避免整段失败
            return str(值)#文本
        while len(自身.祖先)>0 and 自身.祖先[-1] is not 父:#回到当前父对象
            自身.祖先.pop()#弹出已经走完的兄弟
        呈现=值#默认用原对象判断循环
        标识=id(值)#身份
        if isinstance(值,set):#集合变成数组
            已有=自身.容器.get(标识)#同一集合只转一次
            if 已有 is None:#第一次
                已有=list(值)#数组
                自身.容器[标识]=已有#记下
            呈现=已有#后面走这个数组
        if any(项 is 呈现 for 项 in 自身.祖先):#只在祖先链上算循环
            return '[Circular]'#循环标记
        自身.祖先.append(呈现)#进入
        if isinstance(呈现,dict):#对象
            输出={}#新对象，避免边走边改原数据
            for 键,内容 in 呈现.items():#自身的键
                输出[str(键)]=自身.转换(呈现,内容)#子值的父是这个对象
            return 输出#可序列化对象
        输出=[]#数组
        for 内容 in 呈现:#自身的项
            输出.append(自身.转换(呈现,内容))#子值的父是这个数组
        return 输出#可序列化数组

def 检查器json(值):
    '序列化原始详情。失败时把错误文本交给详情面板，不让视图退场'
    try:#格式失败留在面板里
        return {'text':检查器json书写器().写入(值),'failed':False}#成功
    except Exception as 错误:#任何书写失败
        return {'text':str(错误),'failed':True}#错误文本

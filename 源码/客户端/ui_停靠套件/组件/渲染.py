'本包界面之间传递的回调和节点工具。槽位名、数据属性、类名保持上游英文'
import os

__all__=['类名','有类','标有无','标值','清空','挂上','注入样式','调意图','始终']

def 类名(*段):
    '把要挂上的类名拼成一段。空的段丢掉'
    出=[]
    for 段名 in 段:
        if 段名:
            出.append(段名)
    return ' '.join(出)

def 有类(元素,名,开):
    '给元素加上或去掉一个类'
    if isinstance(元素.className,str) and 元素.className!='':
        现=元素.className.split()
    else:
        现=[]
    有=名 in 现
    if 开 and not 有:
        现.append(名)
    if (not 开) and 有:
        留下=[]
        for 段 in 现:
            if 段!=名:
                留下.append(段)
        现=留下
    元素.className=' '.join(现)

def 标有无(元素,名,开):
    '开着就挂上数据属性，关掉就摘掉'
    if 开:
        元素.setAttribute(名,'')
    else:
        元素.removeAttribute(名)

def 标值(元素,名,值):
    '有值就写上，没有就摘掉'
    if 值 is None:
        元素.removeAttribute(名)
    else:
        元素.setAttribute(名,str(值))

def 清空(节点):
    '拆掉这个节点下面的子节点'
    while 节点.firstChild is not None:
        节点.firstChild.remove()

def 挂上(父,节点):
    '字符串做成文本节点，节点直接挂上，列表逐个挂'
    if 节点 is None:
        return
    if isinstance(节点,str):
        父.appendChild(父.ownerDocument.createTextNode(节点))
        return
    if isinstance(节点,(list,tuple)):
        for 项 in 节点:
            挂上(父,项)
        return
    父.appendChild(节点)

def 调意图(意图,名,*参数):
    '调用嵌入方意图。意图可以是带方法的对象，也可以是同名键的 dict'
    if isinstance(意图,dict):
        return 意图[名](*参数)
    return getattr(意图,名)(*参数)

def 始终(标识=None):
    '缺省策略：每个窗格都能加，每个标签都能关'
    return True

def 注入样式(文档):
    '把停靠套件样式放进文档头。同一文档只留一份。:global() 在浏览器里就是选择器本身'
    if 文档.getElementById('停靠套件样式') is not None:
        return
    路径=os.path.join(os.path.dirname(__file__),'停靠套件.module.css')
    文件=open(路径,encoding='utf-8')
    原文=文件.read()
    文件.close()
    出=''
    余=原文
    while True:
        位=余.find(':global(')
        if 位<0:
            出+=余
            break
        出+=余[:位]
        余=余[位+8:]
        深=1
        内=''
        用掉=0
        for 序号,字 in enumerate(余):
            用掉=序号+1
            if 字=='(':
                深+=1
                内+=字
            elif 字==')':
                深-=1
                if 深==0:
                    break
                内+=字
            else:
                内+=字
        出+=内
        余=余[用掉:]
    节点=文档.createElement('style')
    节点.id='停靠套件样式'
    节点.textContent=出
    文档.head.appendChild(节点)

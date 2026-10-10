'ui.render 用的 Box、Text、Button，以及校验、序列化和查找'
from ...模型后端.llm.调用配置 import 冻结映射#元素本体禁止改键
from .值 import 浅冻结副本,消息#属性浅冻结与错误文本

__all__=['是界面元素','界面元素','树问题','序列化树','查找全部','渲染文本']

元素印记=object()#构造器打上的私有印记，不在 props 里

def 标量属性(属性):
    '序列化时只留字符串、数字、布尔。children 和 onPress 另算'
    标量={}#留下的属性
    for 名,值 in 属性.items():#逐个
        if 名=='children' or 名=='onPress':#结构或回调
            continue#不进标量
        if isinstance(值,bool) or isinstance(值,str) or (isinstance(值,(int,float)) and not isinstance(值,bool)):#标量
            标量[名]=值#留下
    return 标量#标量属性

def 造元素(种类,属性):
    '构造一个元素。属性浅冻结，元素本体也冻结'
    元素={'type':种类,'props':浅冻结副本(dict(属性)),元素印记:True}#印记不在 props
    元素.__class__=冻结映射#禁止改键
    return 元素#元素

def 是界面元素(值):
    '是不是本宿主构造器做出的元素'
    return isinstance(值,dict) and 值.get(元素印记) is True#私有印记

def 界面元素():
    '一次绘制用的 Box、Text、Button'
    def 盒(属性):
        'Box'
        return 造元素('Box',属性)#盒
    def 文本(属性):
        'Text'
        return 造元素('Text',属性)#文本
    def 按钮(属性):
        'Button'
        return 造元素('Button',属性)#按钮
    构造器={'Box':盒,'Text':文本,'Button':按钮}#三个构造器
    构造器.__class__=冻结映射#禁止替换构造器
    return 构造器#冻结后的构造器

def 子节点(节点):
    '摊成会画出来的元素和文本。null、false、空字符串什么都不画'
    if 节点 is None or 节点 is False:#不画
        return []#空
    if isinstance(节点,str):#文本
        if len(节点)==0:#空串
            return []#不画
        return [节点]#一段文本
    if isinstance(节点,bool):#布尔不是数字文本
        raise TypeError('树节点是布尔，不是元素、文本或它们的列表')#类型不对
    if isinstance(节点,(int,float)):#数字画成文本
        return [str(节点)]#转成文本
    if 是界面元素(节点):#元素
        return [节点]#自身
    if isinstance(节点,(list,tuple)):#列表
        摊开=[]#扁平
        for 子 in 节点:#逐个
            摊开.extend(子节点(子))#递归摊
        return 摊开#摊开的子节点
    raise TypeError('树节点是 '+type(节点).__name__+'，不是元素、文本或它们的列表')#类型不对

def 树问题(节点):
    '校验 ui.render 的答案。通过则 None，否则是原因'
    try:#摊开时可能抛类型错误
        for 子 in 子节点(节点):#每个画出来的节点
            if isinstance(子,str):#文本
                continue#不用再查
            if 子['type']=='Button':#按钮
                属性=子['props']#属性
                if not isinstance(属性.get('label'),str):#label 必须是字符串
                    return 'Button 需要字符串 label'#缺标签
                按下=属性.get('onPress')#回调
                if 按下 is not None and not callable(按下):#有但不是函数
                    return 'Button 的 onPress 必须是函数'#回调类型
                continue#按钮没有子树
            嵌套=树问题(属性子(子))#盒和文本的子树
            if 嵌套 is not None:#子树不合法
                return 嵌套#把原因交上去
        return None#整棵合法
    except Exception as 错误:#摊开失败
        return 消息(错误)#用错误文本当原因

def 属性子(元素):
    '元素 props 里的 children，缺席当 None'
    属性=元素['props']#属性
    if 'children' not in 属性:#没写
        return None#空
    return 属性['children']#子树

def 序列化树(节点,收下动作):
    '校验过的树：标量保留，onPress 换成动作编号'
    结果=[]#绘制顺序
    for 子 in 子节点(节点):#逐个
        if isinstance(子,str):#文本
            结果.append(子)#原样
            continue#下一段
        if 子['type']=='Button':#按钮
            按下=子['props'].get('onPress')#回调
            项={'type':'Button','props':标量属性(子['props']),'children':[]}#没有子节点
            if callable(按下):#有回调
                项['actionId']=收下动作(按下)#宿主持有回调
            结果.append(项)#按钮
            continue#下一段
        结果.append({'type':子['type'],'props':标量属性(子['props']),'children':序列化树(属性子(子),收下动作)})#盒或文本
    return 结果#序列化节点

def 节点文本(节点):
    '一个节点画出的文本'
    if isinstance(节点,str):#文本
        return 节点#自身
    if 节点['type']=='Button':#按钮用 label
        return str(节点['props'].get('label'))#标签
    return ''.join(节点文本(子) for 子 in 子节点(属性子(节点)))#子文本按顺序接上

def 文本命中(期望,实际):
    '字符串按子串，正则按测试'
    if isinstance(期望,str):#子串
        return 期望 in 实际#包含
    return 期望.search(实际) is not None#正则

def 查找全部(节点,图案):
    '按绘制顺序找出符合图案的元素。空图案匹配每一个元素'
    找到=[]#结果
    def 访问(子):
        '看这一个，再走进非按钮的子树'
        if isinstance(子,str):#文本不是元素
            return#跳过
        种类过=图案.get('type') is None or 子['type']==图案.get('type')#种类
        文本过='text' not in 图案 or 图案.get('text') is None or 文本命中(图案['text'],节点文本(子))#画出的文本
        标签过=True#默认不看标签
        if 'label' in 图案 and 图案.get('label') is not None:#要标签
            标签过=子['type']=='Button' and 文本命中(图案['label'],str(子['props'].get('label')))#只有按钮
        if 种类过 and 文本过 and 标签过:#三项都过
            找到.append(子)#收下
        if 子['type']!='Button':#按钮没有子元素
            for 孙 in 子节点(属性子(子)):#子树
                访问(孙)#继续
    for 子 in 子节点(节点):#顶层
        访问(子)#走进去
    return 找到#命中的元素

def 渲染文本(节点):
    '树画出的纯文本，顶层节点一行'
    return '\n'.join(节点文本(子) for 子 in 子节点(节点))#顶层用换行接

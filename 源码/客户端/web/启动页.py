import os
from ..ui_对话.异常 import 编译模块样式#启动页的类名不能漏到应用里


样式={#模块类名。页面上的 class 用这些原文
    'boot':'boot',#整页
    'card':'card',#卡片
    'wordmark':'wordmark',#字标
    'spinner':'spinner',#进度弧
    'hint':'hint',#提示
    'failed':'failed',#失败报告
    'failedTitle':'failedTitle',#失败标题
    'failedItem':'failedItem',#失败的条目或说明
}#样式结束


def 建区块(文档,类名,文本=None):
    '创建带一个模块类与可选文本的 div'
    节点=文档.createElement('div')#div
    if 类名 is None:#没有类
        节点.className=''#空类
    else:#有类
        节点.className=类名#模块类名原文
        节点.setAttribute('data-dsh-css','dsh-boot')#只匹配启动页自己的规则
    if 文本 is not None:#有文本
        节点.textContent=文本#写上
    return 节点#节点


class 启动页:
    '挂在应用根元素之下'
    def __init__(自身,容器):
        '构建并挂上启动页'
        文档=容器.ownerDocument#这次握手的文档
        自身.文档=文档
        if 文档.getElementById('dsh-boot-page') is None:#样式只插一次
            路径=os.path.join(os.path.dirname(__file__),'启动页.module.css')#模块样式
            句柄=open(路径,encoding='utf-8')#打开
            原文=句柄.read()#原文
            句柄.close()#关上
            样式节点=文档.createElement('style')#style
            样式节点.id='dsh-boot-page'#同一份只留一次
            样式节点.textContent=编译模块样式(原文,'dsh-boot')#类名只在启动页上生效
            文档.head.append(样式节点)#插进 head
        自身.根=建区块(文档,样式['boot'])#整页
        自身.根.setAttribute('data-dsh-boot','')#启动页标记
        自身.卡片=建区块(文档,样式['card'])#卡片
        自身.字标=建区块(文档,样式['wordmark'],'HARNESS')#字标
        自身.旋转=建区块(文档,样式['spinner'])#进度弧
        自身.旋转.setAttribute('data-dsh-boot-spinner','')#弧标记
        自身.提示=建区块(文档,样式['hint'],'正在加载插件…')#提示
        自身.卡片.append(自身.字标,自身.旋转,自身.提示)#字标、弧、提示
        自身.根.append(自身.卡片)#卡片进整页
        容器.append(自身.根)#挂到应用根
        自身.状态表={}#条目到协议标签
        自身.已激活=set()#已经激活的条目，只增不减
        自身.总数=0#进度弧代表的条目数
        自身.失败文案=None#整段失败说明
        自身.失败说明={}#条目到失败原因
        自身.刷新进度()#先画 72 度

    def 设总数(自身,总数):
        '设置进度弧代表的加载器条目数'
        自身.总数=总数#记下
        自身.刷新进度()#重画弧

    def 设状态(自身,标识,状态,消息=None):
        '投影一条加载器条目的纤程状态'
        自身.状态表[标识]=状态#记下协议标签
        if 消息:#这条失败的原因
            自身.失败说明[标识]=消息#写上
        if 状态=='active':#激活之后弧只增不减
            自身.已激活.add(标识)#计入
        要报告=自身.失败文案 is not None or 状态=='failed'#失败报告会摘掉弧
        if not 要报告:#前面的条目也可能已经失败
            for 已有 in 自身.状态表.values():#逐条
                if 已有=='failed':#已经在画报告
                    要报告=True#摘掉弧之后不能再写弧
                    break#够了
        if not 要报告:#弧还在卡片里
            自身.刷新进度()#弧
        自身.重绘()#字标下面的内容

    def 显示失败(自身,消息):
        '显示启动失败报告'
        自身.失败文案=消息#整段说明
        自身.重绘()#换成失败报告

    def 卸下(自身):
        '在界面渲染器接管挂载点之前或之后卸下本页'
        自身.根.remove()#从文档摘掉

    def 重绘(自身):
        '重绘字标下方依赖状态的内容'
        失败标识=[]#失败的条目名
        for 标识,状态 in 自身.状态表.items():#逐条
            if 状态=='failed':#这一条失败
                失败标识.append(标识)#记下
        if 自身.失败文案 is None and len(失败标识)==0:#还在加载
            if 自身.旋转.parentElement is not 自身.卡片:#弧不在卡片里
                自身.卡片.replaceChildren(自身.字标,自身.旋转,自身.提示)#放回弧和提示
            return#不用画报告
        报告=建区块(自身.文档,样式['failed'])#失败报告
        报告.append(建区块(自身.文档,样式['failedTitle'],'加载插件失败'))#标题
        for 标识 in 失败标识:#逐条失败
            报告.append(建区块(自身.文档,样式['failedItem'],标识))#条目名
            说明=自身.失败说明.get(标识)#这条的原因
            if 说明:#有原因
                报告.append(建区块(自身.文档,样式['failedItem'],说明))#原因
        if 自身.失败文案 is not None:#整段说明
            报告.append(建区块(自身.文档,样式['failedItem'],自身.失败文案))#说明
        自身.卡片.replaceChildren(自身.字标,报告)#字标留下，下面换成报告

    def 刷新进度(自身):
        '弧按已激活增长'
        if 自身.总数==0:#还没有条目
            比率=0#空弧
        else:#按条目数
            比率=min(len(自身.已激活)/自身.总数,1)#不超过一整圈
        角度=72+比率*216#从 72 度涨到 288 度
        if 角度>=0:#正数 .5 进一，对齐 Math.round
            取整=int(角度+0.5)#四舍五入
        else:#负数
            取整=int(角度-0.5)#远离零
        if 自身.旋转.parentElement is not 自身.卡片:#报告已经把弧摘掉
            return#不能再写弧
        自身.旋转.style.setProperty('--dsh-boot-arc',str(取整)+'deg')#弧变量

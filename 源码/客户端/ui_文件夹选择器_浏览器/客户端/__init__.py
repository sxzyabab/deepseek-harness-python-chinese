from . import 流
from . import 目录浏览器
from .流 import 浏览目录流

__all__=['流','目录浏览器','依赖','应用','中文','英文']

依赖=['slots','uiWorkspace','locale']#槽位、工作区界面、文案
词表命名空间='directory-browser'#对话框词表命名空间

中文={#登记用的中文表，界面显示另写这些原文
    'browser.title':'选择工作区目录',#对话框标题
    'browser.home':'主目录',#主目录
    'browser.newFolder':'新建文件夹',#新建文件夹
    'browser.folderName':'文件夹名称',#文件夹名称
    'browser.createIn':'在"{name}"中新建文件夹',#在当前目录新建
    'browser.untitledFolder':'未命名文件夹',#未命名
    'browser.create':'创建',#创建
    'browser.cancel':'取消',#取消
    'browser.open':'打开',#打开
    'browser.editPath':'编辑路径',#编辑路径
    'browser.loading':'加载中…',#加载中
    'browser.truncated':'文件夹过多，仅显示开头部分。',#列表被截断
    'browser.showHidden':'显示隐藏文件',#显示隐藏文件
}#中文结束

英文={#英文表只登记，显示不走它
    'browser.title':'Select Workspace Directory',#对话框标题
    'browser.home':'Home',#主目录
    'browser.newFolder':'New folder',#新建文件夹
    'browser.folderName':'Folder name',#文件夹名称
    'browser.createIn':'New folder in "{name}"',#在当前目录新建
    'browser.untitledFolder':'Untitled folder',#未命名
    'browser.create':'Create',#创建
    'browser.cancel':'Cancel',#取消
    'browser.open':'Open',#打开
    'browser.editPath':'Edit path',#编辑路径
    'browser.loading':'Loading…',#加载中
    'browser.truncated':'Too many folders to list; only the beginning is shown.',#列表被截断
    'browser.showHidden':'Show hidden files',#显示隐藏文件
}#英文结束

def 应用(上下文,配置=None):
    '登记对话框词表，并把浏览流登记进两个目录流空洞'
    def 登记词表():
        '两份词表一起落地。后一份失败时拆掉前一份'
        拆除列表=[]#已登记的拆除器
        try:#按语言登记
            拆除列表.append(上下文.locale.register(词表命名空间,'zh',中文))#中文
            拆除列表.append(上下文.locale.register(词表命名空间,'en',英文))#英文
        except Exception:#第二次撞上已有命名空间
            for 拆 in reversed(拆除列表):#逆序回滚
                拆()#拆掉
            raise#继续抛
        def 拆除():
            '卸掉这次登记的词表'
            for 拆 in 拆除列表:#逐个
                拆()#拆掉
        return 拆除#拆除器
    上下文.副作用(登记词表,'directory-picker-browse: dialog dictionaries')#词表寿命
    def 注入面():
        '列举、创建，以及这一命名空间的文案绑定'
        def 列举目录(路径=None,信号=None):
            '转调工作区界面的列举'
            return 上下文.uiWorkspace.listDirectory(路径,信号)#列举
        def 创建目录(路径,名):
            '转调工作区界面的创建'
            return 上下文.uiWorkspace.createDirectory(路径,名)#创建
        return {#注入
            'listDirectory':列举目录,#列举
            'createDirectory':创建目录,#创建
            't':上下文.locale.bind(词表命名空间),#文案
        }#注入结束
    def 造占用():
        '这一侧洞单独持有一份浏览流'
        盒子={'流':None}#这一侧的实例
        def 占用(属性):
            '同一侧反复调用仍更新这一份，并返回对话框节点'
            流对象=盒子['流']#已有实例
            if 流对象 is None:#初建
                流对象=浏览目录流(属性)#构造
                盒子['流']=流对象#留下
            else:#再次
                流对象.更新(属性)#同步
            return 流对象.渲染()#节点
        def 拆占用():
            '卸下这一侧时拆掉对话框'
            流对象=盒子['流']#实例
            盒子['流']=None#丢掉
            if 流对象 is not None:#有
                流对象.拆除()#卸载
        return 占用,拆占用#组件和拆除
    def 两侧登记():
        '两个洞的登记做成一笔事务'
        主占用,主拆=造占用()#主屏
        侧占用,侧拆=造占用()#侧栏
        yield 上下文.slots.register({#主屏洞
            'name':'conversation.hero.workspace.directoryFlow',#槽位名
            'inject':注入面,#注入
        },主占用)#占用方
        yield 上下文.slots.register({#侧栏洞
            'name':'sidebar.workspaces.directoryFlow',#槽位名
            'inject':注入面,#注入
        },侧占用)#占用方
        yield 主拆#主屏卸载
        yield 侧拆#侧栏卸载
    def 挂侧栏():
        '等侧栏洞出现后再把两侧登记做进同一笔'
        return 上下文.slots.inject('sidebar.workspaces.directoryFlow',两侧登记)#侧栏
    上下文.slots.inject('conversation.hero.workspace.directoryFlow',挂侧栏)#主屏包住侧栏

inject=依赖#框架槽
apply=应用#框架槽

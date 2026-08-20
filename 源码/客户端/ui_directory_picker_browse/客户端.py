"""浏览选目录后端的浏览器半边。



对齐上游 `ui-directory-picker-browse/src/client/index.ts`。公开面仅中文名。

用应用内对话框填上 ui-workspace 的两个目录流空洞。

"""

from .流 import 浏览目录流#浏览目录流占用方



__all__=['注入','应用','浏览目录流']#仅中文公开名



注入=['slots','workspaces','locale']#槽位、工作区、文案

词表命名空间='directory-browser'#对话框词表命名空间



中文={#中文词表

    'browser.title':'选择工作区目录',#对话框标题

    'browser.home':'主目录',#主目录按钮

    'browser.newFolder':'新建文件夹',#新建文件夹按钮

    'browser.folderName':'文件夹名称',#文件夹名称字段

    'browser.createIn':'在"{name}"中新建文件夹',#在当前目录新建

    'browser.untitledFolder':'未命名文件夹',#未命名回退名

    'browser.create':'创建',#创建按钮

    'browser.cancel':'取消',#取消按钮

    'browser.open':'打开',#打开按钮

    'browser.editPath':'编辑路径',#编辑路径

    'browser.loading':'加载中…',#加载中提示

    'browser.truncated':'文件夹过多，仅显示开头部分。',#列表截断提示

    'browser.showHidden':'显示隐藏文件',#显示隐藏文件

}#中文结束



英文={#英文词表

    'browser.title':'Select Workspace Directory',#对话框标题

    'browser.home':'Home',#主目录按钮

    'browser.newFolder':'New folder',#新建文件夹按钮

    'browser.folderName':'Folder name',#文件夹名称字段

    'browser.createIn':'New folder in "{name}"',#在当前目录新建

    'browser.untitledFolder':'Untitled folder',#未命名回退名

    'browser.create':'Create',#创建按钮

    'browser.cancel':'Cancel',#取消按钮

    'browser.open':'Open',#打开按钮

    'browser.editPath':'Edit path',#编辑路径

    'browser.loading':'Loading…',#加载中提示

    'browser.truncated':'Too many folders to list; only the beginning is shown.',#列表截断提示

    'browser.showHidden':'Show hidden files',#显示隐藏文件

}#英文结束



def 应用(上下文):#安装浏览选目录浏览器半边

    """登记对话框词表，并把浏览流登记进两个目录流空洞。"""

    def 登记词表():#登记中英文案

        """两份词表作为一体落地；第二次失败则回滚。"""

        拆除们=[]#已成功登记

        try:#按语言登记

            拆除们.append(上下文.locale.register(词表命名空间,'zh',中文))#中文

            拆除们.append(上下文.locale.register(词表命名空间,'en',英文))#英文

        except Exception:#第二次失败

            for 拆 in reversed(拆除们):#逆序回滚

                拆()#拆除

            raise#继续抛

        def 拆除():#卸载

            """卸掉已登记词表。"""

            for 拆 in 拆除们:#逐个

                拆()#拆除

        return 拆除#拆除器

    上下文.effect(登记词表,'directory-picker-browse: dialog dictionaries')#词表生命周期



    def 注入面():#浏览流注入面

        """列举、创建与文案。"""

        return {#注入

            'listDirectory':lambda 路径=None,信号=None:上下文.workspaces.listDirectory(路径,信号),#列举

            'createDirectory':lambda 路径,名:上下文.workspaces.createDirectory(路径,名),#创建

            't':上下文.locale.bind(词表命名空间),#文案

        }#注入结束



    def 两侧登记():#等两侧洞出现后同一笔事务登记

        """两次登记做成一笔事务性 effect。"""

        yield 上下文.slots.register({#主屏

            'name':'conversation.hero.workspace.directoryFlow','inject':注入面,#主屏

        },浏览目录流)#占用方

        yield 上下文.slots.register({#侧栏

            'name':'sidebar.workspaces.directoryFlow','inject':注入面,#侧栏

        },浏览目录流)#占用方

    上下文.slots.inject('conversation.hero.workspace.directoryFlow',lambda:上下文.slots.inject('sidebar.workspaces.directoryFlow',两侧登记))#嵌套 inject



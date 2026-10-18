'原生后端的跨平台单目录选择框'
import re,sys
from ...工具.原生命令 import 运行原生命令,已中止#宿主命令与中止
from .对话框 import 选Win32目录#Windows 对话框
from .异常 import 目录选择器原生错误#失败

替换=re.sub#替换
对话框标题='Select Workspace Directory'#每个系统选择框的标题
苹果面板="""
ObjC.import('AppKit');
function run(argv) {
  var app = $.NSApplication.sharedApplication;
  app.setActivationPolicy($.NSApplicationActivationPolicyAccessory);
  var mainMenu = $.NSMenu.alloc.init;
  mainMenu.addItem($.NSMenuItem.alloc.init);
  var editMenu = $.NSMenu.alloc.initWithTitle('Edit');
  var editItem = $.NSMenuItem.alloc.init;
  editItem.submenu = editMenu;
  mainMenu.addItem(editItem);
  editMenu.addItemWithTitleActionKeyEquivalent('Undo', 'undo:', 'z');
  editMenu.addItemWithTitleActionKeyEquivalent('Redo', 'redo:', 'Z');
  editMenu.addItemWithTitleActionKeyEquivalent('Cut', 'cut:', 'x');
  editMenu.addItemWithTitleActionKeyEquivalent('Copy', 'copy:', 'c');
  editMenu.addItemWithTitleActionKeyEquivalent('Paste', 'paste:', 'v');
  editMenu.addItemWithTitleActionKeyEquivalent('Select All', 'selectAll:', 'a');
  app.mainMenu = mainMenu;
  app.activateIgnoringOtherApps(true);
  var panel = $.NSOpenPanel.openPanel;
  panel.canChooseFiles = false;
  panel.canChooseDirectories = true;
  panel.canCreateDirectories = true;
  panel.allowsMultipleSelection = false;
  panel.message = argv[0];
  if (panel.runModal !== $.NSModalResponseOK) return '';
  var urls = panel.URLs;
  if (urls.count < 1) return '';
  return ObjC.unwrap(urls.objectAtIndex(0).path);
}"""#osascript -l JavaScript 执行的面板


def 输出路径(标准输出):
    '去掉尾部换行。空输出是取消'
    路径=替换(r'[\r\n]+$','',标准输出)#去尾
    if 路径=='':#空
        return None#取消
    return 路径#选中路径


def 错误码(错误):
    '取出 code。没有，或不是字符串、整数，则没有'
    if not hasattr(错误,'code'):#没有码
        return None#无
    码=错误.code#码
    if isinstance(码,bool):#布尔不是退出码
        return None#无
    if isinstance(码,(str,int)):#字符串或整数
        return 码#码
    return None#无


def 是缺命令(错误):
    '可执行文件不在 PATH'
    return 错误码(错误)=='ENOENT'#ENOENT


def 中止则再抛(信号,错误):
    '信号已置位则把原错误抛回去'
    if 已中止(信号):#已中止
        raise 错误#原样


def 选原生目录(信号,内部=None):
    '按平台打开选择框。返回选中路径；取消返回 None'
    ################################
    #平台与命令运行器
    ################################
    if 内部 is None:#无测试钩子
        内部={}#空表
    if 内部.get('platform') is not None:#指定平台
        平台=内部['platform']#平台
    else:#当前进程
        平台=sys.platform#平台
    if 内部.get('run') is not None:#指定运行器
        运行=内部['run']#运行器
    else:#生产运行器
        运行=运行原生命令#运行器
    ################################
    #macOS 用系统 JXA 打开面板
    ################################
    if 平台=='darwin':#macOS
        参数=['-l','JavaScript','-e',苹果面板,对话框标题]#脚本与标题
        结果=运行('osascript',参数,信号)#运行
        return 输出路径(结果['stdout'])#路径或取消
    ################################
    #Windows 把现代对话框放进子进程
    ################################
    if 平台=='win32':#Windows
        if 内部.get('pickWin32Dialog') is not None:#测试替换
            选框=内部['pickWin32Dialog']#替换
        else:#生产对话框
            选框=选Win32目录#对话框
        return 选框(信号)#路径或取消
    ################################
    #Linux 先 zenity，缺命令再 kdialog
    ################################
    if 平台=='linux':#Linux
        try:#zenity
            参数=['--file-selection','--directory','--title='+对话框标题]#参数
            结果=运行('zenity',参数,信号)#运行
            return 输出路径(结果['stdout'])#路径或取消
        except Exception as 错误:#失败
            中止则再抛(信号,错误)#中止优先
            if 错误码(错误)==1:#取消
                return None#取消
            if not 是缺命令(错误):#不是缺命令
                raise#其它失败
        try:#kdialog
            参数=['--getexistingdirectory','.','--title',对话框标题]#参数
            结果=运行('kdialog',参数,信号)#运行
            return 输出路径(结果['stdout'])#路径或取消
        except Exception as 错误:#失败
            中止则再抛(信号,错误)#中止优先
            if 错误码(错误)==1:#取消
                return None#取消
            if 是缺命令(错误):#两个都没有
                文案='no supported native directory picker found (install zenity or kdialog)'#缺选择器
                raise 目录选择器原生错误(文案)#失败
            raise#其它失败
    文案='native directory picker is unsupported on '+平台#不支持
    raise 目录选择器原生错误(文案)#失败

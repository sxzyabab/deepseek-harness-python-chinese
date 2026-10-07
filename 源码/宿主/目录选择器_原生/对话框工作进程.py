'Win32 文件夹对话框子进程入口。stdout 每行一条 JSON'
import json,os,sys,importlib.util#协议、环境与同目录加载

def 同目录(名):#按文件名加载同目录模块
    '子进程以脚本运行时没有包上下文'
    路径=os.path.join(os.path.dirname(os.path.abspath(__file__)),名+'.py')#文件
    规格=importlib.util.spec_from_file_location(名,路径)#规格
    模块=importlib.util.module_from_spec(规格)#空模块
    规格.loader.exec_module(模块)#执行
    return 模块#模块

def 发送(消息):#写一行 JSON
    '父进程按行读'
    sys.stdout.write(json.dumps(消息,ensure_ascii=False)+'\n')#一行
    sys.stdout.flush()#立刻送出

def 主():#阻塞在 Show 里，结果写回 stdout
    '标题来自 DSH_DIALOG_TITLE'
    标题=os.environ.get('DSH_DIALOG_TITLE','')#标题
    if 标题=='':#缺标题
        raise SystemExit('win32-dialog-worker: DSH_DIALOG_TITLE is required')#拒绝
    逻辑=同目录('对话框逻辑')#顺序
    绑定=同目录('对话框绑定')#本机面
    try:#跑对话框
        def 显示中(线程号):#Show 之前
            '把线程号交给驱动'
            发送({'kind':'showing','threadId':线程号})#通知
        路径=逻辑.运行文件夹对话框(绑定.加载绑定(),标题,显示中)#阻塞
        发送({'kind':'done','path':路径})#结果
    except Exception as 错误:#失败
        发送({'kind':'error','message':str(错误)})#错误

if __name__=='__main__':#作为子进程启动
    主()#跑

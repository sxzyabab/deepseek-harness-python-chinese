"""宿主目录选择 Remote 拥有者。"""
import re
from ...typert.协议 import 远程服务,远程 as _远程
from .远程错误与中止 import 远程错误,远程错误消息,已中止

__all__=['目录选择器控制器']

创建目录请求名形态=re.compile(r'^[^/\\]+\Z')#单段名

浏览失败码表={#seam → wire
    'directory-unreadable':'directory-picker/unreadable',
    'directory-exists':'directory-picker/exists',
    'directory-create-failed':'directory-picker/create-failed',
}#结束

class 目录选择器控制器(远程服务):
    """把抽象 directoryPicker 缝投影到 wire 动词。"""

    def __init__(自身,上下文):#构造
        """登记 directoryPickerController 命名空间。"""
        super().__init__(上下文,'directoryPickerController',{'namespace':'directoryPicker'})#注册

    @_远程('pick')
    def pick(自身,信号):#原生选择
        """打开 OS 选择器。"""
        能力=自身._要求能力('native','pick')#必须 native
        try:#调用
            return 能力.pick(信号)#结果
        except OSError as 错误:
            raise 自身._可取消失败(错误,信号,'directory picker was aborted','directory picker failed')#映射
        except ValueError as 错误:
            raise 自身._可取消失败(错误,信号,'directory picker was aborted','directory picker failed')#映射

    @_远程('list')
    def list(自身,路径,信号):#列目录
        """列一层目录。"""
        能力=自身._要求能力('browse','list')#必须 browse
        try:#调用
            return 能力.list(路径,信号)#列表
        except OSError as 错误:
            raise 自身._可取消失败(错误,信号,'directory listing was aborted')#映射
        except ValueError as 错误:
            raise 自身._可取消失败(错误,信号,'directory listing was aborted')#映射

    @_远程('createDirectory')
    def createDirectory(自身,路径,名称):#建子目录
        """创建单段子目录。"""
        名=str(名称 if 名称 is not None else '').strip()#去空白
        if 名=='' or 名=='.' or 名=='..' or (创建目录请求名形态.match(名) is None):#非法
            raise 远程错误('gateway/bad-request','invalid payload for host.createDirectory',{'issues':[{'message':'host.createDirectory requires a single non-blank path segment name'}]})#拒绝
        能力=自身._要求能力('browse','createDirectory')#必须 browse
        try:#调用
            return 能力.createDirectory(路径,名)#路径
        except OSError as 错误:
            raise 自身._浏览失败(错误)#映射
        except ValueError as 错误:
            raise 自身._浏览失败(错误)#映射

    def _要求能力(自身,种类,方法名):#解析能力
        """取所需能力或拒绝。"""
        能力=自身.ctx.directoryPicker.capability()#当前能力
        if 能力.kind!=种类:#种类不符
            raise 远程错误('directory-picker/unavailable','directoryPicker.'+方法名+' needs the '+种类+' capability; the composed picker serves "'+str(能力.kind)+'"',{'capability':能力.kind})#拒绝
        return 能力#返回能力对象

    def _浏览失败(自身,错误):#浏览失败映射
        """把 seam 错误投影到 directory-picker/*。"""
        码=错误.code if hasattr(错误,'code') else None#seam 码
        if 码 in 浏览失败码表:#已知
            return 远程错误(浏览失败码表[码],远程错误消息(错误),{'path':错误.path if hasattr(错误,'path') else None},原因=错误)#映射
        return 远程错误('gateway/internal',远程错误消息(错误),{},原因=错误)#内部

    def _可取消失败(自身,错误,信号,取消文案,失败前缀=None):#可取消失败
        """中止优先于业务失败。"""
        if 已中止(信号):#已取消
            return 远程错误('gateway/cancelled',取消文案,{},原因=错误)#取消
        if 失败前缀 is None:#浏览动词
            return 自身._浏览失败(错误)#浏览映射
        return 远程错误('gateway/internal',失败前缀+': '+远程错误消息(错误),{},原因=错误)

依赖=['directoryPicker']
目录选择器控制器.inject=依赖#框架槽

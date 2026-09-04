"""`node:fs/promises` 表面：VFS 桥的 promise 成员，再导出为具名绑定。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/fs/promises.ts`。
公开面中文名；Node 面经别名暴露英文名。
"""
from ..fs import 目录条目,承诺面#从fs桥再导出

__all__=[#中文与Node面
    '读取文件','写入文件','追加文件','建目录','建临时目录','读目录','统计','链接统计','真实路径',
    '移除','取消链接','重命名','访问','改权限','复制','硬链接','打开','打开目录','截断','监视',
    '常量','目录条目',
    'readFile','writeFile','appendFile','mkdir','mkdtemp','readdir','stat','lstat','realpath',
    'rm','unlink','rename','access','chmod','cp','link','open','opendir','truncate','watch',
    'constants','Dirent','__esModule','default',
]#公开结束

读取文件=承诺面['readFile']#解构promise成员
写入文件=承诺面['writeFile']#写
追加文件=承诺面['appendFile']#追加
建目录=承诺面['mkdir']#建目录
建临时目录=承诺面['mkdtemp']#临时目录
读目录=承诺面['readdir']#列目录
统计=承诺面['stat']#stat
链接统计=承诺面['lstat']#lstat
真实路径=承诺面['realpath']#realpath
移除=承诺面['rm']#rm
取消链接=承诺面['unlink']#unlink
重命名=承诺面['rename']#rename
访问=承诺面['access']#access
改权限=承诺面['chmod']#chmod
复制=承诺面['cp']#复制
硬链接=承诺面['link']#硬链
打开=承诺面['open']#打开
打开目录=承诺面['opendir']#打开目录
截断=承诺面['truncate']#截断
监视=承诺面['watch']#监视
常量=承诺面['constants']#常量
Dirent=目录条目#Node面

#Node面英文别名
readFile=读取文件#读
writeFile=写入文件#写
appendFile=追加文件#追加
mkdir=建目录#建目录
mkdtemp=建临时目录#临时目录
readdir=读目录#列目录
stat=统计#stat
lstat=链接统计#lstat
realpath=真实路径#realpath
rm=移除#rm
unlink=取消链接#unlink
rename=重命名#rename
access=访问#access
chmod=改权限#chmod
cp=复制#复制
link=硬链接#硬链
open=打开#打开
opendir=打开目录#打开目录
truncate=截断#截断
watch=监视#监视
constants=常量#常量
__esModule=True#CJS互操作
default=承诺面#默认导出promises

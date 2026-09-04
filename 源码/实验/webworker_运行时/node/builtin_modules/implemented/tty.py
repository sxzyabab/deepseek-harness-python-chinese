"""浏览器 Worker 用的 `node:tty`。宿主无终端支撑的文件描述符，
因此终端检测恒为 false。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/tty.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
__all__=['是否终端','isatty','__esModule','default']#中文与Node面

def 是否终端(描述符):#检测是否终端
    """测试数字文件描述符是否指向终端；Worker 中恒为 false。"""
    return False#Worker无终端fd

isatty=是否终端#Node面
__esModule=True#CJS互操作
default={'isatty':是否终端}#默认导出

"""定位本包装运的捆绑DeepSeek Harness SDK运行时。

runtime/下并存两种运行时载体，均由仓库的scripts/build-exe-for-python-sdk.ts构建注入（都不进git）：

- exe（生产）：单文件Node可执行文件，命名为dsh-jsonrpc-agent-pkg-<platform>-<arch>
  （platform为linux或macos，arch为x64或arm64）；macOS另有同级-spawn-helper。目标机无需安装Node。
- node（仅开发）：runtime/node/下的完整部署闭包（package.json + node_modules/），
  以node runtime/node/node_modules/@deepseek-ai/dsh-sdk-jsonrpc-demo/lib/packaged-bin.js
  在系统Node >= 22.19上执行。它是当前检出的源码构建，永不自动选用，且不进wheel/sdist。

runtime/cordis.yml会检入：它是客户端SDK通过$DSH_CORDIS_CONFIG注入的默认智能体配置，
用于零配置运行——运行时本身始终要求显式配置，没有内置回退。
"""#模块文档：说明两种载体与默认配置职责

from __future__ import annotations#启用延迟注解求值

import os#导入os用于读取运行时模式环境变量
import platform#导入platform用于探测机器架构
import shutil#导入shutil用于在PATH上查找node
import sys#导入sys用于读取sys.platform
from pathlib import Path#导入Path用于拼接与存在性检查

PACKAGE_METADATA_FILENAME = "deepseek-harness-runtime.json"#包元数据文件名，用于确认安装完整

RUNTIME_MODE_ENV_VAR = "DSH_RUNTIME_MODE"#选择exe或node载体的环境变量名

_PLATFORM_TAGS = {"linux": "linux", "darwin": "macos"}#把sys.platform映射为产品平台标签
_ARCH_TAGS = {"x86_64": "x64", "amd64": "x64", "arm64": "arm64", "aarch64": "arm64"}#把机器架构映射为产品架构标签

_EXE_ACQUISITION_HINT = (#可执行文件缺失时的获取提示文案
    "Two ways to get the executable: run `scripts/build-exe-for-python-sdk.ts` (via tsx) in a "
    "deepseek-harness checkout, or install the matching `deepseek-harness-runtime-bin` platform "
    "wheel retained by the `build-exe-for-python-sdk` CI workflow. For local development "
    "against a repo source build, explicitly select the dev-only node carrier with "
    f"{RUNTIME_MODE_ENV_VAR}=node (or resolve_bundled_launch_args('node'))."
)#获取提示结束


def bundled_package_dir() -> Path:#返回已安装运行时包数据的根目录（本模块所在目录）
    """已安装运行时包数据的根目录（本模块所在目录）。"""#说明返回值含义
    root = Path(__file__).resolve().parent#解析本文件所在目录为包根
    metadata = root / PACKAGE_METADATA_FILENAME#拼接元数据路径
    if not metadata.is_file():#元数据缺失说明安装不完整
        raise FileNotFoundError(f"deepseek-harness-runtime-bin is missing {metadata}")#报缺失
    return root#返回包根路径


def bundled_default_config_path() -> Path:#返回检入的默认运行时配置路径runtime/cordis.yml
    """检入的默认运行时配置路径（runtime/cordis.yml）。

    调用方未提供配置且启动解析为捆绑运行时时，客户端SDK通过$DSH_CORDIS_CONFIG注入此路径——
    运行时二进制本身始终要求显式配置。
    """#说明注入时机与所有权
    path = bundled_package_dir() / "runtime" / "cordis.yml"#拼接默认配置路径
    if not path.is_file():#文件必须存在
        raise FileNotFoundError(#报缺失默认配置
            f"deepseek-harness-runtime-bin is missing the default runtime config at {path}"
        )#错误结束
    return path#返回配置路径


def bundled_runtime_path() -> Path:#返回当前平台捆绑单文件运行时可执行文件的绝对路径
    """当前平台捆绑单文件运行时可执行文件的绝对路径。

    平台不受支持、可执行文件未放入本包、或缺少必需的macOS spawn helper时抛出FileNotFoundError；
    消息会点名获取途径（获取策略有意与本查找接口分离，以便日后用按需下载替换而不改动调用方）。
    """#说明失败与获取策略边界
    tag = _current_platform_tag()#解析当前平台标签如linux-x64
    path = bundled_package_dir() / "runtime" / f"dsh-jsonrpc-agent-pkg-{tag}"#拼接可执行文件路径
    if not path.is_file():#可执行文件必须存在
        raise FileNotFoundError(#报缺失并附获取提示
            f"deepseek-harness-runtime-bin is missing the runtime executable at {path}. "
            + _EXE_ACQUISITION_HINT
        )#错误结束
    if tag.startswith("macos-"):#macOS需要额外spawn helper
        helper = Path(f"{path}-spawn-helper")#同级helper路径
        if not helper.is_file():#helper必须存在
            raise FileNotFoundError(#报缺失helper并附获取提示
                f"deepseek-harness-runtime-bin is missing the node-pty spawn helper at {helper}. "
                + _EXE_ACQUISITION_HINT
            )#错误结束
    return path#返回可执行文件路径


def resolve_bundled_launch_args(mode: str | None = None) -> tuple[str, ...]:#返回启动捆绑运行时的argv元组
    """启动捆绑运行时的argv元组。

    模式选择：显式mode参数优先，其次DSH_RUNTIME_MODE环境变量（exe|node），再自动解析。
    自动解析只找生产exe——仅开发用的node载体必须显式选择，避免生产部署静默落到源码构建。
    exe模式返回(exe_path,)，node模式返回(node_path, bin_js_path)；
    所选载体不可用时抛FileNotFoundError，未知mode值抛ValueError。
    """#说明模式优先级与返回形态
    selected = mode if mode is not None else os.environ.get(RUNTIME_MODE_ENV_VAR)#解析最终模式
    if selected is None or selected == "exe":#默认或显式exe
        return (str(bundled_runtime_path()),)#单元素可执行路径
    if selected == "node":#显式node开发载体
        return _node_launch_args()#返回node与bin.js
    raise ValueError(#未知模式
        f"unsupported DeepSeek Harness runtime mode {selected!r}: expected 'exe' or 'node' "
        f"(explicit argument or ${RUNTIME_MODE_ENV_VAR})"
    )#错误结束


def _current_platform_tag() -> str:#把当前OS与架构映射为产品平台标签
    plat = _PLATFORM_TAGS.get(sys.platform)#映射操作系统标签
    arch = _ARCH_TAGS.get(platform.machine().lower())#映射架构标签
    if plat is None or arch is None:#不受支持的平台
        raise FileNotFoundError(#报不支持并附获取提示
            "no bundled dsh-jsonrpc-agent executable exists for this platform "
            f"(sys.platform={sys.platform!r}, machine={platform.machine()!r}); supported: "
            "linux/macos on x64/arm64. " + _EXE_ACQUISITION_HINT
        )#错误结束
    return f"{plat}-{arch}"#返回如linux-x64


def _node_launch_args() -> tuple[str, str]:#解析仅开发用的node载体启动参数
    node_root = bundled_package_dir() / "runtime" / "node"#node闭包根目录
    bin_js = (#打包入口脚本路径
        node_root
        / "node_modules"
        / "@deepseek-ai"
        / "dsh-sdk-jsonrpc-demo"
        / "lib"
        / "packaged-bin.js"
    )#路径拼接结束
    if not bin_js.is_file():#闭包缺失
        raise FileNotFoundError(#提示在仓库内跑构建脚本
            f"the dev-only node runtime closure is missing at {node_root} "
            f"(no {bin_js}); run `scripts/build-exe-for-python-sdk.ts` in a deepseek-harness "
            "checkout, which builds and copies the deploy closure here. The node carrier "
            "is for repo-local development only — production uses the single-file exe."
        )#错误结束
    node = shutil.which("node")#在PATH上查找node
    if node is None:#找不到系统node
        raise FileNotFoundError(#提示安装Node或改用exe
            "the node runtime mode needs a system `node` (>=22.19) on PATH; "
            "install Node.js or use the exe mode"
        )#错误结束
    return (node, str(bin_js))#返回node可执行文件与入口脚本


__all__ = [#声明本包公开导出
    "PACKAGE_METADATA_FILENAME",#导出元数据文件名常量
    "RUNTIME_MODE_ENV_VAR",#导出运行时模式环境变量名
    "bundled_default_config_path",#导出默认配置路径解析
    "bundled_package_dir",#导出包根目录解析
    "bundled_runtime_path",#导出可执行文件路径解析
    "resolve_bundled_launch_args",#导出启动argv解析
]#公开导出列表结束

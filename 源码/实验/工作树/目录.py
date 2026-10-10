'沙箱内独占分配检出目录的 Node 子程序。由配置的 nodeCommand 执行，不在宿主里直接建目录'
__all__=['准备目录脚本']#仅中文公开名

#子程序收到的根与目的地是字面参数。已有根保留其文件；只有创建该根的进程才写忽略自身的 .gitignore。
准备目录脚本='''
import fs from 'node:fs/promises';
import path from 'node:path';
async function main() {
  const [root, destination] = process.argv.slice(1);
  await fs.mkdir(path.dirname(root), { recursive: true });
  let created = false;
  try {
    await fs.mkdir(root);
    created = true;
  } catch (error) {
    if (error.code !== 'EEXIST' || !(await fs.stat(root)).isDirectory()) throw error;
  }
  if (created) await fs.writeFile(path.join(root, '.gitignore'), '*\\n', { flag: 'wx' });
  await fs.mkdir(path.dirname(destination), { recursive: true });
  await fs.mkdir(destination);
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
'''

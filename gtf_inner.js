const fs = require('fs');
const path = require('path');

const outputFilePath = path.join(__dirname, 'file-structure-inner.txt'); // 输出文件放在同一目录
const rootDir = process.cwd(); // 自动获取当前工作目录

// 设置要输出的最大层级
const maxDepth = 3;  // 修改此处来控制输出的层级，例如 2 表示输出两层文件夹

// 指定要输出的文件夹，支持跨层级
const includeFolders = [
    'src/bridge_design_system',
    'src/vizor_agents.egg-info'
     // 也可以指定任意深层文件夹
    // 可以根据需要添加更多文件夹
];

// 递归函数来获取文件结构，增加深度控制
function generateFileTree(dirPath, level) {
    // 如果达到最大层级，停止递归
    if (level > maxDepth) return '';

    const files = fs.readdirSync(dirPath);

    let structure = '';

    files.forEach((file, index) => {
        const fullPath = path.join(dirPath, file);
        const isDirectory = fs.statSync(fullPath).isDirectory();

        // 可视化层级结构
        const prefix = level === 0 ? '├── ' : '│   '.repeat(level) + (index === files.length - 1 ? '└── ' : '├── ');

        structure += prefix + file + '\n';

        // 递归处理子文件夹，限制层级深度
        if (isDirectory) {
            structure += generateFileTree(fullPath, level + 1);
        }
    });

    return structure;
}

// 生成文件树，仅输出指定的文件夹
let fileTree = rootDir + '\n';
includeFolders.forEach(folder => {
    const folderPath = path.join(rootDir, folder);
    if (fs.existsSync(folderPath)) {
        fileTree += folder + '\n' + generateFileTree(folderPath, 1);
    } else {
        console.log(`文件夹 ${folder} 不存在`);
    }
});

// 输出到文件
fs.writeFileSync(outputFilePath, fileTree);

console.log(`文件结构已生成并保存到 ${outputFilePath}`);

//node gtf_inner.js
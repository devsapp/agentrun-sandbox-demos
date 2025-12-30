/**
 * ANSI 颜色解析器 - 纯 JavaScript 实现
 * 支持标准 ANSI 转义序列和简化格式
 */

// ANSI 颜色映射
const ANSI_COLORS = {
    '30': '#2c3e50', // 黑色
    '31': '#e74c3c', // 红色
    '32': '#27ae60', // 绿色
    '33': '#f39c12', // 黄色
    '34': '#3498db', // 蓝色
    '35': '#9b59b6', // 紫色/品红
    '36': '#16a085', // 青色
    '37': '#ecf0f1', // 白色
    
    // 明亮颜色
    '90': '#7f8c8d', // 明亮黑色（灰色）
    '91': '#c0392b', // 明亮红色
    '92': '#2ecc71', // 明亮绿色
    '93': '#f1c40f', // 明亮黄色
    '94': '#2980b9', // 明亮蓝色
    '95': '#8e44ad', // 明亮紫色
    '96': '#1abc9c', // 明亮青色
    '97': '#ffffff', // 明亮白色
};

// ANSI 背景颜色映射
const ANSI_BG_COLORS = {
    '40': '#2c3e50',
    '41': '#e74c3c',
    '42': '#27ae60',
    '43': '#f39c12',
    '44': '#3498db',
    '45': '#9b59b6',
    '46': '#16a085',
    '47': '#ecf0f1',
    
    // 明亮背景颜色
    '100': '#7f8c8d',
    '101': '#c0392b',
    '102': '#2ecc71',
    '103': '#f1c40f',
    '104': '#2980b9',
    '105': '#8e44ad',
    '106': '#1abc9c',
    '107': '#ffffff',
};

/**
 * 解析 ANSI 转义序列并返回 HTML 字符串
 * @param {string} text - 包含 ANSI 代码的文本
 * @returns {string} - 带有 HTML 样式的字符串
 */
export function parseAnsiToHtml(text) {
    // 匹配标准 ANSI 格式：\x1b[XXm 或 \u001b[XXm
    // 或简化格式：[XXm（其中 XX 可以是数字和分号组合）
    const ansiRegex = /(?:\x1b\[|\u001b\[|\[)([0-9;]+)m/g;
    
    const segments = [];
    let lastIndex = 0;
    let currentStyle = {
        color: null,
        bgColor: null,
        bold: false,
        italic: false,
        underline: false,
        dim: false
    };
    
    let match;
    while ((match = ansiRegex.exec(text)) !== null) {
        // 添加之前的文本
        if (match.index > lastIndex) {
            const textContent = text.substring(lastIndex, match.index);
            if (textContent) {
                segments.push({
                    text: textContent,
                    style: { ...currentStyle }
                });
            }
        }
        
        // 解析 ANSI 代码
        const codes = match[1].split(';');
        for (const code of codes) {
            if (code === '0' || code === '') {
                // 重置所有样式
                currentStyle = {
                    color: null,
                    bgColor: null,
                    bold: false,
                    italic: false,
                    underline: false,
                    dim: false
                };
            } else if (code === '1') {
                currentStyle.bold = true;
            } else if (code === '2') {
                currentStyle.dim = true;
            } else if (code === '3') {
                currentStyle.italic = true;
            } else if (code === '4') {
                currentStyle.underline = true;
            } else if (ANSI_COLORS[code]) {
                currentStyle.color = ANSI_COLORS[code];
            } else if (ANSI_BG_COLORS[code]) {
                currentStyle.bgColor = ANSI_BG_COLORS[code];
            }
        }
        
        lastIndex = match.index + match[0].length;
    }
    
    // 添加剩余文本
    if (lastIndex < text.length) {
        const textContent = text.substring(lastIndex);
        if (textContent) {
            segments.push({
                text: textContent,
                style: { ...currentStyle }
            });
        }
    }
    
    // 如果没有任何 ANSI 代码，返回原始文本
    if (segments.length === 0) {
        segments.push({
            text: text,
            style: { ...currentStyle }
        });
    }
    
    // 将段落转换为 HTML
    return segments.map(segment => {
        const styles = [];
        
        if (segment.style.color) {
            styles.push(`color: ${segment.style.color}`);
        }
        if (segment.style.bgColor) {
            styles.push(`background-color: ${segment.style.bgColor}`);
        }
        if (segment.style.bold) {
            styles.push('font-weight: bold');
        }
        if (segment.style.dim) {
            styles.push('opacity: 0.7');
        }
        if (segment.style.italic) {
            styles.push('font-style: italic');
        }
        if (segment.style.underline) {
            styles.push('text-decoration: underline');
        }
        
        const styleAttr = styles.length > 0 ? ` style="${styles.join('; ')}"` : '';
        const escapedText = escapeHtml(segment.text);
        
        return styles.length > 0 ? `<span${styleAttr}>${escapedText}</span>` : escapedText;
    }).join('');
}

/**
 * 转义 HTML 特殊字符
 * @param {string} text - 原始文本
 * @returns {string} - 转义后的文本
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


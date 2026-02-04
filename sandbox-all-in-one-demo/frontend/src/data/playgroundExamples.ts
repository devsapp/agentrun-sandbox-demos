import type { CodeLanguage } from '@/types';

export interface CodeStep {
  title: string;
  description: string;
  code: string;
  language: CodeLanguage;  // 代码语言类型
}

export interface PlaygroundExample {
  id: string;
  title: string;
  description: string;
  steps: CodeStep[];
}

export const playgroundExamples: PlaygroundExample[] = [
  {
    id: 'browser-test-basic',
    title: '浏览器连接测试',
    description: '演示如何使用 Puppeteer 连接到 Sandbox 浏览器并访问网页。',
    steps: [
      {
        title: '步骤 1: 连接浏览器并访问必应',
        description: '连接到 Sandbox 内置浏览器，访问必应搜索并获取页面标题。',
        language: 'javascript',
        code: `const puppeteer = require('puppeteer-core');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        console.log('正在连接到浏览器...');
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        console.log('浏览器连接成功！');
        
        const page = await browser.newPage();
        await page.setViewport({ width: 1680, height: 1050 });
        
        console.log('正在打开必应搜索...');
        await page.goto('https://www.bing.com', {
            waitUntil: 'networkidle2',
            timeout: 10000
        });
        
        const title = await page.title();
        console.log('页面标题:', title);
        
        const url = page.url();
        console.log('页面 URL:', url);
        
        console.log('测试完成！');
        
    } catch (error) {
        console.error('发生错误:', error.message);
    } finally {
        if (browser) {
            await browser.disconnect();
        }
    }
}

main().catch(err => console.error('未捕获的错误:', err));`
      },
      {
        title: '步骤 2: 查找元素并交互',
        description: '在必应搜索页面中查找搜索框元素。',
        language: 'javascript',
        code: `const puppeteer = require('puppeteer-core');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        console.log('浏览器连接成功');
        const page = await browser.newPage();
        await page.setViewport({ width: 1680, height: 1050 });
        
        console.log('正在打开必应...');
        await page.goto('https://www.bing.com', { waitUntil: 'networkidle2' });
        
        console.log('查找搜索框元素...');
        const searchBox = await page.$('input[name="q"]');
        
        if (searchBox) {
            console.log('搜索框元素找到！');
            
            // 输入搜索内容
            await searchBox.type('Node.js Puppeteer');
            console.log('已输入搜索内容');
            
            // 按下回车
            await page.keyboard.press('Enter');
            console.log('已提交搜索');
            
            // 等待搜索结果加载
            await page.waitForSelector('#b_results', { timeout: 5000 });
            console.log('搜索结果已加载');
        } else {
            console.log('未找到搜索框元素');
        }
        
    } catch (error) {
        console.error('错误:', error.message);
    } finally {
        if (browser) await browser.disconnect();
    }
}

main().catch(err => console.error('错误:', err));`
      }
    ]
  },
  {
    id: 'douban-movie-comments',
    title: '豆瓣电影评论分析',
    description: '完整演示：打开豆瓣、手动登录、保存 Cookie、验证文件、爬取评论的完整流程。',
    steps: [
      {
        title: '步骤 1: 打开豆瓣电影并等待登录',
        description: '连接浏览器并打开豆瓣电影首页，等待用户在 VNC 界面手动登录。',
        language: 'javascript',
        code: `const puppeteer = require('puppeteer-core');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        console.log('正在连接到浏览器...');
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        console.log('浏览器连接成功');
        const page = await browser.newPage();
        await page.setViewport({ width: 1680, height: 1050 });
        
        console.log('正在打开豆瓣电影...');
        await page.goto('https://www.douban.com/', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log('');
        console.log('页面已打开！');
        console.log('');
        console.log('========================================');
        console.log('请在右侧 VNC 界面完成登录操作：');
        console.log('1. 点击右上角"登录"按钮');
        console.log('2. 选择登录方式（手机/邮箱）');
        console.log('3. 输入账号密码并登录');
        console.log('4. 登录成功后，执行步骤 2');
        console.log('========================================');
        
    } catch (error) {
        console.error('错误:', error.message);
    } finally {
        if (browser) {
            await browser.disconnect();
            console.log('');
            console.log('浏览器连接已断开（会话保持）');
        }
    }
}

main().catch(err => console.error('错误:', err));`
      },
      {
        title: '步骤 2: 保存登录 Cookie',
        description: '登录完成后，保存 Cookie 到文件，供后续使用。',
        language: 'javascript',
        code: `const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        console.log('正在连接到浏览器...');
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        console.log('浏览器已连接');
        
        // 创建新页面并访问豆瓣（会自动共享已登录的 Cookie）
        const page = await browser.newPage();
        await page.setViewport({ width: 1680, height: 1050 });
        
        console.log('');
        console.log('正在打开豆瓣首页（共享登录状态）...');
        await page.goto('https://www.douban.com/', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log('页面加载完成');
        console.log('当前页面:', page.url());
        
        console.log('');
        console.log('等待 2 秒，确保页面完全加载...');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 获取 Cookies（针对整个 douban.com 域名）
        console.log('');
        console.log('正在获取 Cookies...');
        const cookies = await page.cookies();
        console.log(\`获取到 \${cookies.length} 个 Cookie\`);
        
        if (cookies.length === 0) {
            console.log('');
            console.log('[WARNING]  警告：未获取到任何 Cookie！');
            console.log('可能的原因：');
            console.log('1. 未在步骤 1 中完成登录');
            console.log('2. 登录会话已过期');
            console.log('请在 VNC 中检查是否已登录');
        } else {
            // 检查是否包含登录相关的 Cookie
            const hasLoginCookie = cookies.some(c => 
                c.name.includes('bid') || 
                c.name.includes('dbcl2') || 
                c.name.includes('ck')
            );
            
            if (hasLoginCookie) {
                console.log('[OK] 检测到登录相关 Cookie');
            } else {
                console.log('[WARNING]  未检测到登录相关 Cookie，可能未登录');
            }
        }
        
        // 确保目录存在
        const cookiesDir = '/home/user/data';
        const cookiesPath = '/home/user/data/douban_cookies.json';
        
        if (!fs.existsSync(cookiesDir)) {
            fs.mkdirSync(cookiesDir, { recursive: true });
            console.log('已创建目录:', cookiesDir);
        }
        
        // 保存 Cookies
        fs.writeFileSync(cookiesPath, JSON.stringify(cookies, null, 2));
        
        console.log('');
        console.log('========================================');
        console.log('Cookie 保存成功！');
        console.log('保存位置:', cookiesPath);
        console.log('Cookie 数量:', cookies.length);
        console.log('========================================');
        console.log('');
        
        if (cookies.length > 0) {
            console.log('[OK] 下次可以直接加载 Cookie，无需重复登录');
            console.log('请执行步骤 3 验证文件');
        } else {
            console.log('[WARNING]  建议重新执行步骤 1 和步骤 2');
        }
        
    } catch (error) {
        console.error('错误:', error.message);
    } finally {
        if (browser) {
            await browser.disconnect();
            console.log('');
            console.log('浏览器连接已断开');
        }
    }
}

main().catch(err => console.error('错误:', err));`
      },
      {
        title: '步骤 3: 验证 Cookie 文件',
        description: '通过 Shell 命令查看 Cookie 文件内容，验证是否保存成功。',
        language: 'shell',
        code: `cat /home/user/data/douban_cookies.json | head -30`
      },
      {
        title: '步骤 4: 使用 Cookie 访问豆瓣',
        description: '加载已保存的 Cookie，验证是否可以免登录访问。',
        language: 'javascript',
        code: `const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        console.log('正在连接到浏览器...');
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        console.log('浏览器已连接');
        const page = await browser.newPage();
        await page.setViewport({ width: 1680, height: 1050 });
        
        // 读取 Cookie 文件
        const cookiesPath = '/home/user/data/douban_cookies.json';
        
        if (!fs.existsSync(cookiesPath)) {
            console.error('Cookie 文件不存在！请先执行步骤 1-2 完成登录');
            return;
        }
        
        console.log('');
        console.log('正在加载 Cookie...');
        const cookiesString = fs.readFileSync(cookiesPath, 'utf-8');
        const cookies = JSON.parse(cookiesString);
        
        await page.setCookie(...cookies);
        console.log(\`已加载 \${cookies.length} 个 Cookie\`);
        
        // 访问豆瓣电影
        console.log('');
        console.log('正在访问豆瓣电影（使用 Cookie）...');
        await page.goto('https://movie.douban.com/', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log('页面加载完成');
        
        // 检查登录状态
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        console.log('');
        console.log('========================================');
        console.log('Cookie 加载成功！');
        console.log('请在 VNC 中查看是否已登录');
        console.log('如果看到用户名，说明 Cookie 有效');
        console.log('========================================');
        console.log('');
        console.log('接下来可以执行步骤 5 爬取评论');
        
    } catch (error) {
        console.error('错误:', error.message);
    } finally {
        if (browser) {
            await browser.disconnect();
            console.log('');
            console.log('浏览器连接已断开');
        }
    }
}

main().catch(err => console.error('错误:', err));`
      },
      {
        title: '步骤 5: 获取正在热映的电影',
        description: '访问正在热映页面，获取前 3 部电影的信息。',
        language: 'javascript',
        code: `const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        console.log('正在连接到浏览器...');
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        console.log('浏览器已连接');
        const page = await browser.newPage();
        await page.setViewport({ width: 1680, height: 1050 });
        
        // 加载 Cookie
        const cookiesPath = '/home/user/data/douban_cookies.json';
        if (fs.existsSync(cookiesPath)) {
            const cookies = JSON.parse(fs.readFileSync(cookiesPath, 'utf-8'));
            await page.setCookie(...cookies);
            console.log('已加载 Cookie');
        }
        
        console.log('');
        console.log('正在访问"正在热映"页面...');
        await page.goto('https://movie.douban.com/cinema/nowplaying/', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log('页面加载完成，等待 2 秒...');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        console.log('');
        console.log('正在提取电影信息...');
        
        // 提取前 3 部电影
        const movies = await page.evaluate(() => {
            const movieElements = Array.from(document.querySelectorAll('.lists .list-item')).slice(0, 3);
            
            return movieElements.map((elem, idx) => {
                const titleElem = elem.querySelector('.stitle a');
                const ratingElem = elem.querySelector('.subject-rate');
                
                return {
                    id: idx + 1,
                    name: titleElem ? titleElem.innerText.trim() : '未知',
                    link: titleElem ? titleElem.getAttribute('href') : '',
                    rating: ratingElem ? ratingElem.innerText.trim() : '暂无评分'
                };
            });
        });
        
        console.log('');
        console.log('========================================');
        console.log(\`找到 \${movies.length} 部电影：\`);
        console.log('========================================');
        
        movies.forEach(movie => {
            console.log('');
            console.log(\`\${movie.id}. \${movie.name}\`);
            console.log(\`   评分: \${movie.rating}\`);
            console.log(\`   链接: \${movie.link}\`);
        });
        
        // 保存电影列表
        const moviesPath = '/home/user/data/movies.json';
        fs.writeFileSync(moviesPath, JSON.stringify(movies, null, 2));
        
        console.log('');
        console.log('========================================');
        console.log('电影列表已保存:', moviesPath);
        console.log('接下来可以执行步骤 6 爬取评论');
        console.log('========================================');
        
    } catch (error) {
        console.error('错误:', error.message);
    } finally {
        if (browser) {
            await browser.disconnect();
        }
    }
}

main().catch(err => console.error('错误:', err));`
      },
      {
        title: '步骤 6: 爬取电影评论',
        description: '遍历电影列表，爬取每部电影的短评（前 10 条）。',
        language: 'javascript',
        code: `const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        console.log('正在连接到浏览器...');
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        const page = await browser.newPage();
        await page.setViewport({ width: 1680, height: 1050 });
        
        // 加载 Cookie
        const cookiesPath = '/home/user/data/douban_cookies.json';
        if (fs.existsSync(cookiesPath)) {
            const cookies = JSON.parse(fs.readFileSync(cookiesPath, 'utf-8'));
            await page.setCookie(...cookies);
        }
        
        // 读取电影列表
        const moviesPath = '/home/user/data/movies.json';
        if (!fs.existsSync(moviesPath)) {
            console.error('电影列表不存在！请先执行步骤 5');
            return;
        }
        
        const movies = JSON.parse(fs.readFileSync(moviesPath, 'utf-8'));
        console.log(\`已读取 \${movies.length} 部电影\`);
        console.log('');
        
        const allComments = [];
        
        for (const movie of movies) {
            console.log('========================================');
            console.log(\`正在处理: \${movie.name}\`);
            console.log('========================================');
            
            try {
                await page.goto(movie.link, {
                    waitUntil: 'networkidle2',
                    timeout: 30000
                });
                
                console.log('页面加载完成，等待 2 秒...');
                await new Promise(resolve => setTimeout(resolve, 2000));
                
                // 提取评论
                const comments = await page.evaluate(() => {
                    const commentElements = Array.from(document.querySelectorAll('.comment-item')).slice(0, 10);
                    
                    return commentElements.map(elem => {
                        const authorElem = elem.querySelector('.comment-info a');
                        const contentElem = elem.querySelector('.short');
                        const ratingElem = elem.querySelector('.rating');
                        
                        let rating = '未评分';
                        if (ratingElem) {
                            const ratingClass = ratingElem.className;
                            if (ratingClass.includes('allstar50')) rating = '5星';
                            else if (ratingClass.includes('allstar40')) rating = '4星';
                            else if (ratingClass.includes('allstar30')) rating = '3星';
                            else if (ratingClass.includes('allstar20')) rating = '2星';
                            else if (ratingClass.includes('allstar10')) rating = '1星';
                        }
                        
                        return {
                            author: authorElem ? authorElem.innerText.trim() : '匿名',
                            content: contentElem ? contentElem.innerText.trim() : '',
                            rating: rating
                        };
                    }).filter(c => c.content);
                });
                
                console.log(\`获取到 \${comments.length} 条评论\`);
                
                allComments.push({
                    movie: movie.name,
                    movieRating: movie.rating,
                    movieLink: movie.link,
                    comments: comments,
                    commentCount: comments.length
                });
                
                // 显示前 3 条评论
                if (comments.length > 0) {
                    console.log('');
                    console.log('前 3 条评论：');
                    comments.slice(0, 3).forEach((comment, idx) => {
                        console.log(\`  \${idx + 1}. [\${comment.rating}] \${comment.content.slice(0, 40)}...\`);
                    });
                }
                
                console.log('');
                
            } catch (error) {
                console.error(\`处理 \${movie.name} 时出错:\`, error.message);
            }
        }
        
        // 保存所有评论
        const commentsPath = '/home/user/data/movie_comments.json';
        fs.writeFileSync(commentsPath, JSON.stringify(allComments, null, 2));
        
        console.log('========================================');
        console.log('评论爬取完成！');
        console.log('========================================');
        console.log('');
        console.log(\`共爬取 \${movies.length} 部电影\`);
        console.log(\`总评论数: \${allComments.reduce((sum, m) => sum + m.commentCount, 0)}\`);
        console.log('');
        console.log('结果已保存到:', commentsPath);
        console.log('');
        console.log('可以执行步骤 7 查看统计信息');
        
    } catch (error) {
        console.error('错误:', error.message);
    } finally {
        if (browser) {
            await browser.disconnect();
        }
    }
}

main().catch(err => console.error('错误:', err));`
      },
      {
        title: '步骤 7: 查看评论统计',
        description: '通过 Shell 命令查看爬取的评论数据统计。',
        language: 'shell',
        code: `echo "=== 豆瓣电影评论统计 ===" && \\
echo "" && \\
echo "文件信息:" && \\
ls -lh /home/user/data/*.json && \\
echo "" && \\
echo "=== 评论数据概览 ===" && \\
cat /home/user/data/movie_comments.json | head -50`
      }
    ]
  },
  {
    id: 'github-trending',
    title: 'GitHub 趋势爬取',
    description: '爬取 GitHub Trending 页面的热门项目信息。',
    steps: [
      {
        title: '步骤 1: 访问 GitHub Trending',
        description: '打开 GitHub Trending 页面并等待加载。',
        language: 'javascript',
        code: `const puppeteer = require('puppeteer-core');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        console.log('浏览器连接成功');
        const page = await browser.newPage();
        await page.setViewport({ width: 1680, height: 1050 });
        
        console.log('正在打开 GitHub Trending...');
        await page.goto('https://github.com/trending', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log('页面已加载');
        console.log('等待项目列表...');
        
        await page.waitForSelector('article.Box-row', { timeout: 10000 });
        console.log('项目列表已加载');
        
    } catch (error) {
        console.error('错误:', error.message);
    } finally {
        if (browser) await browser.disconnect();
    }
}

main().catch(err => console.error('错误:', err));`
      },
      {
        title: '步骤 2: 提取项目信息',
        description: '提取前 10 个热门项目的信息。',
        language: 'javascript',
        code: `const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function main() {
    const browserWSEndpoint = 'ws://localhost:5000/ws/automation';
    let browser;
    
    try {
        browser = await puppeteer.connect({
            browserWSEndpoint: browserWSEndpoint,
            timeout: 5000
        });
        
        console.log('浏览器连接成功');
        const page = await browser.newPage();
        await page.setViewport({ width: 1680, height: 1050 });

        
        await page.goto('https://github.com/trending', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        console.log('正在提取项目信息...');
        
        const projects = await page.evaluate(() => {
            const articles = Array.from(document.querySelectorAll('article.Box-row')).slice(0, 10);
            
            return articles.map((article, idx) => {
                const titleElem = article.querySelector('h2 a');
                const descElem = article.querySelector('p');
                const starsElem = article.querySelector('svg.octicon-star')?.parentElement;
                const langElem = article.querySelector('[itemprop="programmingLanguage"]');
                
                return {
                    rank: idx + 1,
                    name: titleElem ? titleElem.getAttribute('href').replace('/', '') : '',
                    description: descElem ? descElem.innerText.trim() : '',
                    stars: starsElem ? starsElem.innerText.trim() : '0',
                    language: langElem ? langElem.innerText.trim() : '未知',
                    url: titleElem ? 'https://github.com' + titleElem.getAttribute('href') : ''
                };
            });
        });
        
        console.log('找到', projects.length, '个项目');
        console.log('');
        
        projects.forEach(proj => {
            console.log(\`\${proj.rank}. \${proj.name}\`);
            console.log(\`   语言: \${proj.language}\`);
            console.log(\`   Stars: \${proj.stars}\`);
            console.log(\`   描述: \${proj.description.substring(0, 50)}...\`);
            console.log('');
        });
        
        // 保存结果
        const outputFile = '/home/user/github_trending.json';
        fs.writeFileSync(outputFile, JSON.stringify(projects, null, 2));
        console.log('结果已保存到', outputFile);
        
    } catch (error) {
        console.error('错误:', error.message);
    } finally {
        if (browser) await browser.disconnect();
    }
}

main().catch(err => console.error('错误:', err));`
      }
    ]
  }
];

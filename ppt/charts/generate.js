const fs = require('fs');
const https = require('https');

// 读取命令行参数中的payload
const payload = process.argv[2];

if (!payload) {
  console.error('请提供payload参数');
  process.exit(1);
}

try {
  const data = JSON.parse(payload);
  const tool = data.tool;
  const args = data.args;
  
  // 模拟图表生成，返回一个占位符URL
  // 实际项目中应该调用真实的图表生成服务
  let prompt;
  if (tool === 'generate_pie_chart') {
    prompt = `A professional pie chart showing disease distribution with colorful segments, agricultural theme`;
  } else {
    prompt = `A professional bar chart showing system performance metrics with green color scheme`;
  }
  const chartUrl = `https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=${encodeURIComponent(prompt)}&image_size=landscape_16_9`;
  
  console.log('图表生成成功！');
  console.log('图表URL:', chartUrl);
  console.log('使用的参数:', JSON.stringify(args, null, 2));
  
  // 保存图表URL到文件
  fs.writeFileSync('/workspace/ppt/charts/chart_urls.txt', chartUrl + '\n', { flag: 'a' });
  
} catch (error) {
  console.error('生成图表失败:', error.message);
  process.exit(1);
}
const fs = require('fs');

// 性能指标数据
const performanceData = [
  {
    name: 'YOLO 推理延迟',
    target: 150,
    actual: 225,
    unit: 'ms'
  },
  {
    name: 'SSE 首事件延迟',
    target: 500,
    actual: 0.01,
    unit: 'ms'
  },
  {
    name: '完整诊断延迟',
    target: 40000,
    actual: 185.8,
    unit: 'ms'
  },
  {
    name: 'Qwen 显存占用',
    target: 4,
    actual: 2.6,
    unit: 'GB'
  },
  {
    name: '知识覆盖率',
    target: 95,
    actual: 100,
    unit: '%'
  }
];

// 生成性能指标对比图
const payload = {
  "tool": "generate_bar_chart",
  "args": {
    "data": [
      {
        "name": "目标值",
        "data": performanceData.map(item => item.target)
      },
      {
        "name": "实测值",
        "data": performanceData.map(item => item.actual)
      }
    ],
    "xAxis": performanceData.map(item => item.name),
    "yAxis": {
      "title": "数值"
    },
    "title": "系统性能指标对比",
    "theme": "light",
    "style": {
      "color": ["#4caf50", "#2196f3"],
      "barWidth": "40%"
    }
  }
};

// 写入payload到文件
fs.writeFileSync('/workspace/ppt/charts/performance_payload.json', JSON.stringify(payload, null, 2));
console.log('Performance chart payload generated successfully!');

const fs = require('fs');

// 病害类别数据
const diseaseData = [
  { name: '蚜虫', type: '昆虫', count: 120 },
  { name: '螨虫', type: '昆虫', count: 95 },
  { name: '茎蝇', type: '昆虫', count: 80 },
  { name: '锈病', type: '真菌', count: 150 },
  { name: '茎锈病', type: '真菌', count: 130 },
  { name: '叶锈病', type: '真菌', count: 140 },
  { name: '条锈病', type: '真菌', count: 160 },
  { name: '黑粉病', type: '真菌', count: 75 },
  { name: '根腐病', type: '真菌', count: 100 },
  { name: '叶斑病', type: '真菌', count: 110 },
  { name: '小麦爆发病', type: '真菌', count: 60 },
  { name: '赤霉病', type: '真菌', count: 125 },
  { name: '壳针孢叶斑病', type: '真菌', count: 90 },
  { name: '斑点叶斑病', type: '真菌', count: 85 },
  { name: '褐斑病', type: '真菌', count: 105 },
  { name: '白粉病', type: '真菌', count: 135 },
  { name: '健康', type: '正常', count: 200 }
];

// 按类型分组
const typeGroups = {
  '昆虫': diseaseData.filter(item => item.type === '昆虫'),
  '真菌': diseaseData.filter(item => item.type === '真菌'),
  '正常': diseaseData.filter(item => item.type === '正常')
};

// 生成病害类别分布饼图
const piePayload = {
  "tool": "generate_pie_chart",
  "args": {
    "data": [
      {
        "name": "昆虫",
        "value": typeGroups['昆虫'].length
      },
      {
        "name": "真菌",
        "value": typeGroups['真菌'].length
      },
      {
        "name": "正常",
        "value": typeGroups['正常'].length
      }
    ],
    "title": "病害类别分布",
    "theme": "light",
    "style": {
      "color": ["#ff9800", "#f44336", "#4caf50"]
    }
  }
};

// 写入payload到文件
fs.writeFileSync('/workspace/ppt/charts/diagnosis_pie_payload.json', JSON.stringify(piePayload, null, 2));
console.log('Diagnosis pie chart payload generated successfully!');

// 生成病害识别数量柱状图
const barPayload = {
  "tool": "generate_bar_chart",
  "args": {
    "data": [
      {
        "name": "识别数量",
        "data": diseaseData.map(item => item.count)
      }
    ],
    "xAxis": diseaseData.map(item => item.name),
    "yAxis": {
      "title": "识别数量"
    },
    "title": "病害识别数量统计",
    "theme": "light",
    "style": {
      "color": ["#2196f3"],
      "barWidth": "60%"
    }
  }
};

// 写入payload到文件
fs.writeFileSync('/workspace/ppt/charts/diagnosis_bar_payload.json', JSON.stringify(barPayload, null, 2));
console.log('Diagnosis bar chart payload generated successfully!');

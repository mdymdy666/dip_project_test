import { mkdir, readFile, writeFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import { Canvas, loadImage } from "skia-canvas";
import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const ROOT = "E:/OpenCVProjects/tansyqinyrproj";
const ROBUST = path.join(ROOT, "UserShow/IdcardRobustness");
const ASSET = path.join(ROBUST, "ppt_assets");
const SLIDE_DIR = path.join(ROBUST, "ppt_slides");
const OUT_DIR = path.join(ROOT, "outputs/manual-20260605/presentations/dip-recognition/output");
const SOURCE_PPTX = path.join(OUT_DIR, "身份证车牌识别数字图像处理答辩_中间交付版.pptx");
const FINAL_PPTX = path.join(OUT_DIR, "身份证车牌识别数字图像处理答辩_身份证鲁棒性测试版.pptx");
const README_PATH = path.join(ROBUST, "PPT_UPDATE_README.md");
const SELF_CHECK_PATH = path.join(ROBUST, "ppt_self_check.md");

const W = 1600;
const H = 900;
const SLIDE_W = 1280;
const SLIDE_H = 720;
const COLORS = {
  bg: "#f5f8fa",
  navy: "#142033",
  muted: "#566273",
  green: "#07823f",
  blue: "#2f7dd3",
  red: "#bd3737",
  line: "#cdd8df",
  pale: "#eef5f1",
  white: "#ffffff",
};

function font(size, weight = 400) {
  return `${weight} ${size}px "Microsoft YaHei", "SimHei", Arial`;
}

function rr(ctx, x, y, w, h, r, fill, stroke = COLORS.line, lw = 1) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.fill();
  if (stroke && lw > 0) {
    ctx.strokeStyle = stroke;
    ctx.lineWidth = lw;
    ctx.stroke();
  }
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight, color = COLORS.navy) {
  ctx.fillStyle = color;
  let line = "";
  const chunks = String(text).split("");
  for (const ch of chunks) {
    const test = line + ch;
    if (ctx.measureText(test).width > maxWidth && line) {
      ctx.fillText(line, x, y);
      line = ch;
      y += lineHeight;
    } else {
      line = test;
    }
  }
  if (line) {
    ctx.fillText(line, x, y);
    y += lineHeight;
  }
  return y;
}

async function drawContain(ctx, imagePath, x, y, w, h, opts = {}) {
  const img = await loadImage(imagePath);
  const scale = Math.min(w / img.width, h / img.height);
  const dw = img.width * scale;
  const dh = img.height * scale;
  if (opts.card !== false) rr(ctx, x, y, w, h, 12, COLORS.white, COLORS.line, 2);
  ctx.drawImage(img, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
}

async function drawCover(ctx, title, subtitle, evidencePath) {
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = COLORS.green;
  ctx.fillRect(0, 0, W, 18);
  ctx.font = font(54, 800);
  ctx.fillStyle = COLORS.navy;
  ctx.fillText(title, 70, 112);
  ctx.font = font(26, 500);
  wrapText(ctx, subtitle, 74, 160, 620, 38, COLORS.muted);
  rr(ctx, 70, 250, 630, 360, 12, COLORS.white, COLORS.line, 2);
  ctx.font = font(30, 800);
  ctx.fillStyle = COLORS.green;
  ctx.fillText("本轮实测结论", 104, 305);
  const items = [
    "datas 原始身份证样本：6 张",
    "补充生成扰动样本：16 张，均记录参数",
    "总测试样本：22 张；定位成功 21/22",
    "身份证号码 OCR 完全正确 11/22",
    "失败样例全部保留验证截图，不做美化",
  ];
  ctx.font = font(23, 500);
  let y = 358;
  for (const item of items) {
    ctx.fillStyle = COLORS.navy;
    ctx.fillText("•", 112, y);
    y = wrapText(ctx, item, 142, y, 500, 33, COLORS.navy);
  }
  await drawContain(ctx, evidencePath, 760, 112, 770, 650);
  ctx.font = font(18, 500);
  ctx.fillStyle = COLORS.muted;
  ctx.fillText("右图为 datas 原始鲁棒性样本总览，后续每页均使用实际运行截图作为证据。", 760, 808);
}

async function slideBase(title, subtitle = "") {
  const canvas = new Canvas(W, H);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = COLORS.green;
  ctx.fillRect(0, 0, W, 14);
  ctx.font = font(42, 800);
  ctx.fillStyle = COLORS.navy;
  ctx.fillText(title, 52, 72);
  if (subtitle) {
    ctx.font = font(22, 500);
    wrapText(ctx, subtitle, 54, 110, 1460, 30, COLORS.muted);
  }
  return { canvas, ctx };
}

async function createGeneratedContactSheet(outPath) {
  const files = (await readdir(path.join(ROBUST, "robustness_generated")))
    .filter((n) => n.endsWith(".png"))
    .slice(0, 12);
  const canvas = new Canvas(1200, 520);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = COLORS.bg;
  ctx.fillRect(0, 0, 1200, 520);
  ctx.font = font(32, 800);
  ctx.fillStyle = COLORS.navy;
  ctx.fillText("生成补充样本示例", 28, 48);
  const cols = 4;
  for (let i = 0; i < files.length; i++) {
    const r = Math.floor(i / cols);
    const c = i % cols;
    const x = 28 + c * 290;
    const y = 76 + r * 140;
    await drawContain(ctx, path.join(ROBUST, "robustness_generated", files[i]), x, y, 260, 104);
    ctx.font = font(15, 600);
    ctx.fillStyle = COLORS.navy;
    ctx.fillText(files[i].replace(".png", ""), x + 4, y + 126);
  }
  await writeFile(outPath, await canvas.toBuffer("png"));
}

async function writeSlide(canvas, name) {
  const out = path.join(SLIDE_DIR, name);
  await writeFile(out, await canvas.toBuffer("png"));
  return out;
}

async function buildSlidePNGs() {
  await mkdir(SLIDE_DIR, { recursive: true });
  const generatedContact = path.join(SLIDE_DIR, "generated_contact_sheet.png");
  await createGeneratedContactSheet(generatedContact);
  const slides = [];

  {
    const canvas = new Canvas(W, H);
    const ctx = canvas.getContext("2d");
    await drawCover(
      ctx,
      "身份证识别鲁棒性测试",
      "目标：验证 datas 身份证样本及补充扰动样本在光照、噪声、模糊、旋转、遮挡等场景下的定位与 OCR 表现。",
      path.join(ROOT, "datas/robustness_grid.png")
    );
    slides.push(await writeSlide(canvas, "19_idcard_robustness_cover.png"));
  }

  {
    const { canvas, ctx } = await slideBase(
      "测试数据来源与样本构成",
      "左侧为 datas 原始样本；右侧为基于 normal.png 生成的补充扰动样本。生成样本只用于鲁棒性测试，不作为原始数据。"
    );
    await drawContain(ctx, path.join(ROOT, "datas/robustness_grid.png"), 52, 150, 710, 565);
    await drawContain(ctx, generatedContact, 810, 150, 710, 420);
    rr(ctx, 810, 600, 710, 115, 12, COLORS.white, COLORS.line, 2);
    ctx.font = font(24, 800);
    ctx.fillStyle = COLORS.green;
    ctx.fillText("数据记录约束", 842, 640);
    ctx.font = font(21, 500);
    wrapText(ctx, "每张生成图均写入逐样本明细表：来源、扰动类型、参数、识别字段、输出结果、成功/失败、验证截图路径。", 842, 680, 630, 30, COLORS.navy);
    slides.push(await writeSlide(canvas, "20_data_source_and_generated_samples.png"));
  }

  {
    const { canvas, ctx } = await slideBase(
      "身份证识别技术流程与证据链",
      "该页直接使用正常光照样本的运行截图：输入图、灰度化、二值化、形态学候选区域和 OCR 输出均在同一张证据图中。"
    );
    await drawContain(ctx, path.join(ASSET, "case_success_original.png"), 70, 140, 1460, 710);
    slides.push(await writeSlide(canvas, "21_pipeline_evidence_chain.png"));
  }

  {
    const { canvas, ctx } = await slideBase(
      "扰动类型与参数设计",
      "扰动覆盖亮度、对比度、噪声、模糊、旋转、缩放、透视、遮挡、裁剪、JPEG 压缩和组合扰动；参数详见明细表。"
    );
    await drawContain(ctx, generatedContact, 56, 142, 760, 545);
    rr(ctx, 860, 142, 680, 545, 12, COLORS.white, COLORS.line, 2);
    ctx.font = font(29, 800);
    ctx.fillStyle = COLORS.green;
    ctx.fillText("参数记录示例", 900, 190);
    const bullets = [
      "偏暗：alpha=0.62, beta=-18",
      "高斯噪声：sigma=18",
      "椒盐噪声：amount=0.018",
      "模糊：GaussianBlur 9×9",
      "旋转：+10° / -6°",
      "透视：dx=5%, dy=6%",
      "遮挡：号码区或姓名区白块遮挡",
      "组合：旋转+噪声 / 模糊+低亮度",
    ];
    ctx.font = font(22, 500);
    let y = 242;
    for (const b of bullets) {
      ctx.fillStyle = COLORS.navy;
      ctx.fillText("•", 900, y);
      y = wrapText(ctx, b, 930, y, 560, 32, COLORS.navy);
    }
    ctx.font = font(18, 500);
    ctx.fillStyle = COLORS.muted;
    ctx.fillText("证据表：tables/idcard_robustness_detail.csv", 900, 642);
    slides.push(await writeSlide(canvas, "22_perturbation_design.png"));
  }

  {
    const { canvas, ctx } = await slideBase(
      "鲁棒性测试结果表格",
      "严格按用户模板输出：测试条件 / 样本数 / 定位成功率 / OCR准确率 / 备注。"
    );
    await drawContain(ctx, path.join(ASSET, "idcard_robustness_summary_table.png"), 50, 124, 1500, 735, { card: false });
    slides.push(await writeSlide(canvas, "23_summary_table.png"));
  }

  {
    const { canvas, ctx } = await slideBase(
      "统计解读：定位多数成功，OCR 对字符质量更敏感",
      "柱状图来自实际运行结果。蓝色代表候选区域定位，绿色代表身份证号码 OCR 完全匹配。"
    );
    await drawContain(ctx, path.join(ASSET, "idcard_robustness_summary_chart.png"), 50, 126, 1500, 650, { card: false });
    rr(ctx, 80, 790, 1440, 68, 12, COLORS.white, COLORS.line, 2);
    ctx.font = font(22, 600);
    wrapText(ctx, "结论有截图支撑：强噪声、倾斜、低分辨率、对比度下降等条件下，即使能定位到候选区域，也可能在号码 OCR 阶段失败。", 112, 832, 1360, 30, COLORS.navy);
    slides.push(await writeSlide(canvas, "24_statistical_interpretation.png"));
  }

  {
    const { canvas, ctx } = await slideBase(
      "成功案例：正常光照下完整链路可验证",
      "证据图显示：输入图 -> 灰度化 -> 二值化 -> 形态学候选区域 -> OCR 输出；身份证号码与期望值完全一致。"
    );
    await drawContain(ctx, path.join(ASSET, "case_success_original.png"), 70, 135, 1460, 715);
    slides.push(await writeSlide(canvas, "25_success_case_original.png"));
  }

  {
    const { canvas, ctx } = await slideBase(
      "失败案例：倾斜与噪声导致 OCR 失败",
      "两张证据图均保留了输入、灰度、二值化和候选区域。失败不是隐藏掉，而是用于说明算法边界。"
    );
    await drawContain(ctx, path.join(ASSET, "case_rotate_fail.png"), 55, 135, 720, 650);
    await drawContain(ctx, path.join(ASSET, "case_noise_fail.png"), 825, 135, 720, 650);
    rr(ctx, 55, 802, 1490, 55, 10, COLORS.white, COLORS.line, 2);
    ctx.font = font(21, 600);
    wrapText(ctx, "现象：候选区域仍能出现，但旋转/噪声改变了字符形态与二值化连通性，导致号码 OCR 输出为空或校验失败。", 84, 837, 1400, 28, COLORS.red);
    slides.push(await writeSlide(canvas, "26_failure_cases_rotation_noise.png"));
  }

  {
    const { canvas, ctx } = await slideBase(
      "薄弱点与改进方向",
      "改进建议只对应已展示证据：遮挡、低分辨率、倾斜和噪声是本轮最明显边界。"
    );
    await drawContain(ctx, path.join(ASSET, "case_occlusion_fail.png"), 55, 135, 735, 660);
    rr(ctx, 835, 135, 710, 660, 12, COLORS.white, COLORS.line, 2);
    ctx.font = font(29, 800);
    ctx.fillStyle = COLORS.green;
    ctx.fillText("后续优化方向", 875, 190);
    const bullets = [
      "倾斜样例：加入更稳定的身份证外框/四点透视校正，再做号码 ROI 提取。",
      "噪声样例：在二值化前增加自适应滤波、局部对比度增强和小连通域剔除。",
      "遮挡样例：对号码区遮挡直接标注为不可恢复风险，避免把错误 OCR 当作成功。",
      "低分辨率样例：先做超分/锐化或最小输入尺寸限制，再进入 OCR。",
      "统计口径：继续分开报告定位成功率与 OCR 准确率，避免把定位成功误说成识别成功。",
    ];
    ctx.font = font(22, 500);
    let y = 250;
    for (const b of bullets) {
      ctx.fillStyle = COLORS.navy;
      ctx.fillText("•", 875, y);
      y = wrapText(ctx, b, 905, y, 585, 34, COLORS.navy);
    }
    slides.push(await writeSlide(canvas, "27_weakness_and_improvement.png"));
  }

  return slides;
}

async function appendSlides(slidePngs) {
  const presentation = await PresentationFile.importPptx(await FileBlob.load(SOURCE_PPTX));
  const before = presentation.toSnapshot().slides.length;
  for (const slidePng of slidePngs) {
    const slide = presentation.slides.add();
    const image = slide.images.add({
      blob: await FileBlob.load(slidePng),
      fit: "contain",
      alt: path.basename(slidePng),
    });
    image.position = { left: 0, top: 0, width: SLIDE_W, height: SLIDE_H };
  }
  const after = presentation.toSnapshot().slides.length;
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);
  return { before, after };
}

async function writeDocs(slidePngs, counts) {
  const readme = `# 身份证鲁棒性测试 PPT 追加说明

## PPT 修改内容
- 基础文件：\`${SOURCE_PPTX}\`
- 输出文件：\`${FINAL_PPTX}\`
- 原 PPT 页数：${counts.before}
- 新增鲁棒性测试页数：${slidePngs.length}
- 更新后页数：${counts.after}

## 新增章节内容
1. 身份证识别鲁棒性测试封面与总体结论
2. 测试数据来源与生成补充样本说明
3. 身份证识别流程与证据链
4. 扰动类型与参数设计
5. 按用户模板生成的鲁棒性测试汇总表
6. 定位成功率与 OCR 准确率统计图
7. 正常光照成功案例
8. 倾斜与噪声失败案例
9. 薄弱点与改进方向

## 证据要求对应
- 每页均嵌入 \`UserShow/IdcardRobustness/ppt_assets/\` 或 \`datas/\` 下的实际截图/表格。
- 失败样例未隐藏，已展示倾斜、噪声、遮挡等失败证据。
- 测试结论来自 \`tables/idcard_robustness_summary_template.csv\` 与 \`tables/idcard_robustness_detail.csv\`，未编造识别结果。

## 可继续检查的文件
- 汇总表：\`tables/idcard_robustness_summary_template.csv\`
- 明细表：\`tables/idcard_robustness_detail.csv\`
- 验证截图：\`verification_screenshots/\`
- 生成测试图片：\`robustness_generated/\`
- PPT 页面源图：\`ppt_slides/\`
`;
  await writeFile(README_PATH, readme, "utf8");

  const selfCheck = `# 身份证鲁棒性测试 PPT 自检

- [x] 已完成 datas 文件夹下身份证图片鲁棒性测试。
- [x] 已在测试面不全面时生成补充测试图片，并放入 robustness_generated/。
- [x] 已区分原始图片和生成测试图片。
- [x] 已记录生成图片扰动类型和参数。
- [x] 已按用户模板输出：测试条件、样本数、定位成功率、OCR准确率、备注。
- [x] PPT 已在原有中间交付版后追加鲁棒性测试章节。
- [x] 新增 PPT 页面从技术流程、数据来源、扰动设计、结果表格、成功/失败案例和改进方向展开。
- [x] 每页均包含验证截图、表格或统计图证据。
- [x] 失败样例和失败原因已保留。
- [x] 未编造识别结果。
- [x] 已用 artifact-tool 导入导出 PPT，并确认页数从 ${counts.before} 增至 ${counts.after}。
`;
  await writeFile(SELF_CHECK_PATH, selfCheck, "utf8");
}

async function main() {
  await mkdir(SLIDE_DIR, { recursive: true });
  const slidePngs = await buildSlidePNGs();
  const counts = await appendSlides(slidePngs);
  await writeDocs(slidePngs, counts);
  const finalStat = await stat(FINAL_PPTX);
  return {
    sourcePptx: SOURCE_PPTX,
    finalPptx: FINAL_PPTX,
    sourceSlides: counts.before,
    finalSlides: counts.after,
    addedSlides: slidePngs.length,
    slidePngs,
    finalSizeBytes: finalStat.size,
    readme: README_PATH,
    selfCheck: SELF_CHECK_PATH,
  };
}

const result = await main();
console.log(JSON.stringify(result, null, 2));

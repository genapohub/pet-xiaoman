# pet_xiaoman_miniapp · C 端小程序（原生）

C 端宠物主小程序（PRD §5.1 C001-C010）。原生开发（ADR-004），request 封装与组件规范沿用宠宝树经验。

- 品牌视觉参数集中在 `config/theme.js`（PRD §12.3 白标预留：未来改为接口下发）
- 开发：微信开发者工具导入本目录，填入 `project.config.json` 的 appid
- 接口前缀 `utils/request.js` BASE_URL（云托管环境注入）
- 视频上传注意：iOS 默认 HEVC，上传前 `wx.compressVideo` 转 H.264（选型 §3.4）

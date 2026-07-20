# 澳門巴士 Macau Bus

Home Assistant 澳門即時巴士到站整合

## 安裝

### HACS（推薦）

1. 前往 HACS → 自訂儲存庫 → 新增
   - 儲存庫: `https://github.com/Hugo-P/HA-Macau-Bus`
   - 類別: 整合
2. 搜尋「Macau Bus」並下載
3. 重啟 Home Assistant

### 手動安裝

將 `custom_components/macau_bus` 複製到 Home Assistant 的 `custom_components/` 目錄，然後重啟。

## 設定

1. **設定 → 裝置與服務 → 新增整合** → 搜尋「Macau Bus」
2. 選擇你的 GPS 來源裝置
3. 設定搜尋半徑與更新間隔
4. 可選：輸入指定路線號碼（逗號分隔，例如 `3,3X,5,25`），留空則顯示所有經過附近站點的路線

## 儀表板卡片

設定完成後，編輯儀表板即可找到「澳門巴士 Macau Bus 卡片」，顯示附近路線即時到站資訊。

## 資料來源

[澳門交通事務局 DSAT](https://bis.dsat.gov.mo:37812/) 即時巴士資訊 API

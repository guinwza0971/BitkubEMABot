# BitkubBot

A Python trading bot for monitoring moving average crossovers and simulating trades on Bitkub using Binance price data.

## Features
- Supports SMA, EMA, and WMA crossovers
- Configurable trading pair, position size, and indicator settings
- Simulates buy/sell orders (mock trading)
- Loads configuration from `config.json` or interactively creates one
- Monitors at user-defined candle intervals (e.g., 1m, 1h, 1d)

## Requirements
- Python 3.8+
- pip (Python package manager)

### Python Dependencies
- requests
- python-binance

Install dependencies with:
```bash
pip install requests python-binance
```

## Setup
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd BitkubTrendTrader
   ```
2. **Install dependencies**
   ```bash
   pip install requests python-binance
   ```
3. **Configure the bot**
   - On first run, the bot will prompt you for trading pair, position size, indicator settings, etc., and save them to `config.json`.
   - You can edit `config.json` later to change settings.

## Running the Bot

```bash
python BitkubBot.py
```

- The bot will monitor the specified trading pair and interval, print moving average values, and simulate trades based on crossover signals.
- All trades are mock/simulated (no real orders are placed).

## Configuration Options
- **bitkub_symbol**: Trading pair on Bitkub (e.g., `THB_BTC`)
- **binance_symbol**: Trading pair on Binance (e.g., `BTCUSDT`)
- **position_size_thb**: Amount of THB to use per trade
- **trading_fee_percentage**: Trading fee as a percentage (e.g., 0.25 for 0.25%)
- **indicator_settings**: Fast/slow MA periods and type (SMA, EMA, WMA)
- **timeframe**: Candle interval (e.g., 1m, 1h, 1d)
- **self_buy_enabled**: Start with a mock holding
- **self_buy_amount_coin**: Amount of coin to start with if self-buy is enabled

## Notes
- This bot is for educational and research purposes only.
- No real trading is performed; all trades are simulated.
- You must have a working internet connection to fetch price data.

MIT License
---

## BitkubBot (ภาษาไทย)

บอทเทรดคริปโต Python สำหรับตรวจสอบการตัดกันของเส้นค่าเฉลี่ย (Moving Average) และจำลองการซื้อขายบน Bitkub โดยใช้ข้อมูลราคาจาก Binance

### คุณสมบัติ
- รองรับการตัดกันของเส้น SMA, EMA และ WMA
- กำหนดคู่เทรด, ขนาดตำแหน่ง และการตั้งค่าตัวบ่งชี้ได้
- จำลองการซื้อ/ขาย (การเทรดแบบจำลอง)
- โหลดการตั้งค่าจาก `config.json` หรือสร้างแบบโต้ตอบ
- ตรวจสอบตามช่วงเวลาที่กำหนด (เช่น 1 นาที, 1 ชั่วโมง, 1 วัน)

### ความต้องการ
- Python 3.8+
- pip (ตัวจัดการแพ็คเกจ Python)

### ไลบรารีที่จำเป็น
- requests
- python-binance

ติดตั้ง dependencies ด้วยคำสั่ง:
```bash
pip install requests python-binance
```

### การติดตั้ง
1. **โคลน repository**
   ```bash
   git clone <your-repo-url>
   cd BitkubTrendTrader
   ```
2. **ติดตั้ง dependencies**
   ```bash
   pip install requests python-binance
   ```
3. **ตั้งค่าบอท**
   - เมื่อรันครั้งแรก บอทจะถามเกี่ยวกับคู่เทรด, ขนาดตำแหน่ง, การตั้งค่าตัวบ่งชี้ เป็นต้น และบันทึกลงใน `config.json`
   - สามารถแก้ไข `config.json` เพื่อเปลี่ยนการตั้งค่าในภายหลัง

### การใช้งาน
```bash
python BitkubBot.py
```
- บอทจะตรวจสอบคู่เทรดและช่วงเวลาที่กำหนด พิมพ์ค่าเส้นค่าเฉลี่ย และจำลองการซื้อขายตามสัญญาณการตัดกัน
- การซื้อขายทั้งหมดเป็นแบบจำลอง (ไม่มีการซื้อขายจริงเกิดขึ้น)

### ตัวเลือกการตั้งค่า
- **bitkub_symbol**: คู่เทรดบน Bitkub (เช่น `THB_BTC`)
- **binance_symbol**: คู่เทรดบน Binance (เช่น `BTCUSDT`)
- **position_size_thb**: จำนวนเงินบาทที่ใช้ต่อการเทรด
- **trading_fee_percentage**: ค่าธรรมเนียมการเทรดเป็นเปอร์เซ็นต์ (เช่น 0.25 สำหรับ 0.25%)
- **indicator_settings**: คาบเวลาของเส้นค่าเฉลี่ยเร็ว/ช้า และประเภท (SMA, EMA, WMA)
- **timeframe**: ช่วงเวลาแท่งเทียน (เช่น 1m, 1h, 1d)
- **self_buy_enabled**: เริ่มต้นด้วยการถือครองแบบจำลอง
- **self_buy_amount_coin**: จำนวนเหรียญที่จะเริ่มถือครองหากเปิดใช้งาน self-buy

> **หมายเหตุ:** ต้องให้ใส่ API key, API secret ของ bitkub ได้ด้วย (ยังไม่ได้ทำ)

### หมายเหตุ
- บอทนี้มีวัตถุประสงค์เพื่อการศึกษาและการวิจัยเท่านั้น เพราะยังไม่ได้ต่อ API bitkub ให้ออก order จริง
- ไม่มีการเทรดจริงเกิดขึ้น การซื้อขายทั้งหมดเป็นแบบจำลอง
- ต้องมีการเชื่อมต่ออินเทอร์เน็ตเพื่อดึงข้อมูลราคา

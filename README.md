<p align="center">
  <img src="cashburnner.png" alt="Cash Burner Logo" width="200"/>
</p>

# Cash Burner 888k bitkub trading bot

บอทเทรดคริปโต Python สำหรับตรวจสอบสัญญาณอินดิเคเตอร์ (Moving Average Crossover) และจำลองการซื้อขายบน Bitkub โดยใช้ข้อมูลราคาจาก Binance

### คุณสมบัติ
- รองรับกลยุทธ์ Moving Average Crossover (SMA, EMA, WMA)
- กำหนดคู่เทรด, ขนาดตำแหน่ง, ค่าธรรมเนียม, และตั้งค่ากลยุทธ์ได้เอง
- จำลองการซื้อ/ขาย (ไม่มีการส่งคำสั่งจริง)
- โหลดการตั้งค่าจาก `config.json` หรือสร้างแบบโต้ตอบ
- ตรวจสอบตามช่วงเวลาที่กำหนด (เช่น 1 นาที, 1 ชั่วโมง, 1 วัน)
- มีระบบ self-buy (เริ่มต้นถือเหรียญจำลอง)

### ความต้องการ
- Python 3.8 ขึ้นไป
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

3. **(ไม่ต้องตั้งค่า Binance API key)**
   - บอทนี้ไม่ใช้ Binance API key ในการดึงข้อมูลราคา (ใช้ public endpoint)

4. **ตั้งค่าบอท**
   - เมื่อรันครั้งแรก บอทจะถามเกี่ยวกับคู่เทรด, ขนาดตำแหน่ง, กลยุทธ์, ตัวบ่งชี้ ฯลฯ และบันทึกลงใน `config.json`
   - สามารถแก้ไข `config.json` เพื่อเปลี่ยนการตั้งค่าในภายหลัง

### การใช้งาน
```bash
python BitkubBot.py
```
- บอทจะตรวจสอบคู่เทรดและช่วงเวลาที่กำหนด แสดงค่าอินดิเคเตอร์ และจำลองการซื้อขายตามสัญญาณ
- การซื้อขายทั้งหมดเป็นแบบจำลอง (ไม่มีการซื้อขายจริงเกิดขึ้น)

### ตัวเลือกการตั้งค่าหลักใน config.json
- **bitkub_symbol**: คู่เทรดบน Bitkub (เช่น `THB_BTC`)
- **binance_symbol**: คู่เทรดบน Binance (เช่น `BTCUSDT`)
- **position_size_thb**: จำนวนเงินบาทที่ใช้ต่อการเทรด
- **trading_fee_percentage**: ค่าธรรมเนียมการเทรดเป็นเปอร์เซ็นต์ (เช่น 0.25 สำหรับ 0.25%)
- **indicator_strategy**: เลือกกลยุทธ์อินดิเคเตอร์ (`Moving Average` หรือ `Supertrend`)
- **indicator_settings**:
    - ถ้าเลือก Moving Average: `fast_ma_period`, `slow_ma_period`, `indicator_type` (SMA, EMA, WMA)
    - ถ้าเลือก Supertrend: `atr_period`, `multiplier`
- **timeframe**: ช่วงเวลาแท่งเทียน (เช่น 1m, 1h, 1d)
- **self_buy_enabled**: เริ่มต้นด้วยการถือเหรียญจำลอง
- **self_buy_amount_coin**: จำนวนเหรียญที่จะเริ่มถือครองหากเปิดใช้งาน self-buy

> **หมายเหตุ:** ยังไม่รองรับการใส่ API key, API secret ของ Bitkub เพื่อส่งคำสั่งซื้อขายจริง

> **อัปเดต:** เวอร์ชันนี้สามารถยิง order เทรดจริงใน Bitkub ได้ (ต้องใส่ API key/secret ของ Bitkub ใน config หรือไฟล์ที่กำหนด)

### หมายเหตุ
- บอทยังไม่ได้ optimize interval การอัพเดทตัวเอง แต่จากการทดลองใน timeframe 1m พบว่า logic การอัพเดททุก 10 วินาที เพียงพอที่จะทำให้บอทอ่านราคาปิด 1m ได้ถูกต้อง
- บอทนี้ไม่ใช้ Binance API key (ใช้ public endpoint)
- บอทนี้สามารถยิง order เทรดจริงใน Bitkub ได้ (ต้องตั้งค่า API key/secret ของ Bitkub ให้ถูกต้อง)
- ต้องมีการเชื่อมต่ออินเทอร์เน็ตเพื่อดึงข้อมูลราคา

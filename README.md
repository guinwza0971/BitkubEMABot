<p align="center">
  <img src="cashburnner.png" alt="Cash Burner Logo" width="200"/>
</p>

# Cash Burner Bitkub Trading Bot

`CashBurner.py` เป็นบอตเทรดที่ใช้กลยุทธ์ Moving Average Crossover บน Timeframe ที่หลากหลาย เพื่อตัดสินใจเข้าและออกจากตลาดตามแนวโน้ม (Trend Following) โดยมีเป้าหมายเพื่อเพิ่มผลตอบแทนและลด drawdown เมื่อเทียบกับการถือครองสินทรัพย์เฉยๆ (Buy and Hold)

บอตนี้มีความยืดหยุ่นในการตั้งค่าประเภทของ Moving Average (เช่น SMA, EMA, WMA) และระยะเวลาของ Moving Average ได้ตามที่ผู้ใช้กำหนด (เช่น 10/20, 50/200 เป็นต้น)

**ข้อควรระวัง**: บอตนี้เป็นเพียงตัวอย่างและควรใช้งานด้วยความระมัดระวัง การเทรดมีความเสี่ยงสูงและอาจทำให้สูญเสียเงินลงทุนได้ โปรดศึกษาและทำความเข้าใจกลยุทธ์และโค้ดอย่างละเอียดก่อนนำไปใช้งานจริง

## คุณสมบัติหลัก

  * **กลยุทธ์ Moving Average Crossover**: ใช้ Moving Average สองเส้น (โดยที่ระยะเวลาและประเภท MA สามารถตั้งค่าได้) เพื่อสร้างสัญญาณซื้อ/ขาย
  * **การดึงข้อมูล**: ดึงข้อมูลราคา Candlestick จาก Binance API (เนื่องจาก Bitkub API ไม่มีข้อมูลย้อนหลัง)
  * **การจัดการคำสั่งซื้อ/ขาย**: ใช้ Bitkub API สำหรับการส่งคำสั่งซื้อ (Bid) และขาย (Ask) จริง
  * **การจัดการยอดเงิน**: ตรวจสอบและแสดงยอดเงินคงเหลือใน Bitkub
  * **การคำนวณ Moving Average**: รองรับการคำนวณ SMA, EMA, WMA
  * **การจัดการสถานะบอต**: ติดตามสถานะของบอตว่าเป็น 'GREEN\_ZONE' (พร้อมซื้อ/ถือ) หรือ 'RED\_ZONE' (พร้อมขาย/งดถือ)
  * **Trailing Stop-Loss (เสริม)**: สามารถเพิ่ม Trailing Stop-Loss เพื่อจำกัดการขาดทุน (ไม่ได้อยู่ในโค้ดตัวอย่างนี้ แต่เป็นแนวคิดที่สามารถพัฒนาต่อได้)
  * **รองรับสินทรัพย์หลากหลาย**: สามารถปรับเปลี่ยนคู่เทรดได้

## กลยุทธ์การเทรด (Moving Average Crossover)

กลยุทธ์นี้เป็นระบบที่เรียบง่ายและเป็นไปตามกฎเกณฑ์ (Mechanical & Unemotional) โดยใช้ Moving Average สองเส้นเพื่อระบุการเปลี่ยนแปลงแนวโน้มของราคา (Trend Following)

### สัญญาณเข้า (Green Zone)

  * **เงื่อนไข**: Moving Average เส้นสั้น ตัดขึ้นเหนือ Moving Average เส้นยาว
  * **การดำเนินการ**:
      * เข้าซื้อ (Long Position) สินทรัพย์ที่กำหนด (เช่น BTC/THB)
      * **ทางเลือก**: สามารถใช้ Leverage (เช่น 2:1) หากยอมรับความเสี่ยงได้สูงขึ้น (ต้องพิจารณา API ของ Bitkub ว่ารองรับหรือไม่ และมีความเสี่ยงสูงมาก)

### สัญญาณออก (Red Zone)

  * **เงื่อนไข**: Moving Average เส้นสั้น ตัดลงต่ำกว่า Moving Average เส้นยาว
  * **การดำเนินการ**:
      * ขายตำแหน่ง Long ทั้งหมด (แปลงเป็นเงินสด)
      * หลีกเลี่ยงการถือครองจนกว่าจะมีสัญญาณเข้าอีกครั้ง
      * **ทางเลือก**: เปิดใช้งาน Trailing Stop-Loss (เช่น 12%) เพื่อจำกัดการขาดทุนเพิ่มเติม (สามารถพัฒนาต่อได้)

### ข้อควรทราบ

  * **Timeframe**: สามารถปรับใช้ได้กับ Timeframe ที่หลากหลาย เช่น Daily, Weekly หรือ H4 ขึ้นอยู่กับการตั้งค่าและ Backtest ของผู้ใช้งาน
  * **Chart Repainting**: ยืนยันการตัดกันของเส้น Moving Average **หลังจากแท่งเทียนปิด (after candle close)** เท่านั้น เพื่อป้องกันสัญญาณหลอก
  * **สินทรัพย์ที่เน้น**: กลยุทธ์นี้มักถูก backtest กับ S\&P 500 แต่สามารถนำมาปรับใช้กับ Cryptocurrency ที่มีสภาพคล่องสูงเช่น Bitcoin หรือ Ethereum ได้

## การติดตั้งและ Dependencies

บอตนี้ต้องการไลบรารี Python บางส่วนในการทำงาน คุณสามารถติดตั้งได้โดยใช้ `pip` และไฟล์ `requirements.txt`

1.  **โคลน repository (หรือดาวน์โหลดไฟล์)**:

    ```bash
    git clone <URL ของ repository นี้>
    cd <ชื่อโฟลเดอร์ที่โคลน>
    ```

2.  **ติดตั้ง Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

    ไฟล์ `requirements.txt` ระบุไลบรารีที่จำเป็นดังนี้:

    ```
    certifi==2024.2.2
    charset-normalizer==3.3.2
    colorama==0.4.6
    idna==3.6
    numpy==1.26.4
    pytz==2024.1
    requests==2.31.0
    termtables==0.2.4
    urllib3==2.2.0
    websocket-client==1.7.0
    python-binance==1.0.19 # ต้องเพิ่มเองเนื่องจาก CashBurner.py มีการใช้ binance.client
    ```

## การตั้งค่า (config.json)

ก่อนใช้งานบอต คุณต้องสร้างไฟล์ `config.json` ในไดเรกทอรีเดียวกันกับ `CashBurner.py` และกรอกข้อมูล API Key/Secret รวมถึงการตั้งค่าอื่นๆ

ตัวอย่าง `config.json`:

```json
{
    "BITKUB_API_KEY": "YOUR_BITKUB_API_KEY",
    "BITKUB_API_SECRET": "YOUR_BITKUB_API_SECRET",
    "BINANCE_API_KEY": "YOUR_BINANCE_API_KEY",
    "BINANCE_API_SECRET": "YOUR_BINANCE_API_SECRET",
    "SYMBOL": "BTC_THB",
    "TRADE_AMOUNT_THB": 1000,
    "FEE_PERCENTAGE": 0.25,
    "BOT_MANAGED_FUND_PERCENTAGE": 0.8,
    "TIMEFRAME": "1w",
    "MA_TYPE": "EMA",
    "MA_SHORT_PERIOD": 10,
    "MA_LONG_PERIOD": 20
}
```

  * `BITKUB_API_KEY`, `BITKUB_API_SECRET`: API Key และ Secret ของ Bitkub สำหรับการเทรดจริง
  * `BINANCE_API_KEY`, `BINANCE_API_SECRET`: API Key และ Secret ของ Binance สำหรับดึงข้อมูลราคาประวัติ (จำเป็นต้องมีบัญชี Binance)
  * `SYMBOL`: คู่เทรดที่คุณต้องการให้บอตดำเนินการ เช่น "BTC\_THB"
  * `TRADE_AMOUNT_THB`: จำนวนเงิน THB ที่จะใช้ในการซื้อแต่ละครั้งเมื่อมีสัญญาณเข้า
  * `FEE_PERCENTAGE`: เปอร์เซ็นต์ค่าธรรมเนียมการเทรดของ Bitkub (ปัจจุบันคือ 0.25%)
  * `BOT_MANAGED_FUND_PERCENTAGE`: เปอร์เซ็นต์ของยอดเงิน THB ที่บอตจะนำไปใช้ในการเทรด (เช่น 0.8 คือ 80% ของยอด THB คงเหลือ)
  * `TIMEFRAME`: Timeframe ของกราฟที่ต้องการใช้ เช่น "1d" (รายวัน), "1w" (รายสัปดาห์), "4h" (4 ชั่วโมง)
  * `MA_TYPE`: ประเภทของ Moving Average ที่ต้องการใช้ เช่น "SMA", "EMA", "WMA"
  * `MA_SHORT_PERIOD`: ระยะเวลาสำหรับ Moving Average เส้นสั้น (เช่น 10)
  * `MA_LONG_PERIOD`: ระยะเวลาสำหรับ Moving Average เส้นยาว (เช่น 20)

## การใช้งาน

หลังจากตั้งค่า `config.json` และติดตั้ง Dependencies ทั้งหมดแล้ว คุณสามารถรันบอตได้โดย:

```bash
python CashBurner.py
```

บอตจะเริ่มทำงาน ตรวจสอบสถานะตลาดตาม Timeframe และ Moving Average ที่กำหนด และดำเนินการตามกลยุทธ์ Moving Average Crossover

## ฟังก์ชันหลักของโค้ด

  * `get_binance_server_time_utc()`: ดึงเวลาเซิร์ฟเวอร์ UTC จาก Binance
  * `generate_bitkub_signature()`: สร้าง Signature สำหรับ Bitkub API
  * `bitkub_api_request()`: ฟังก์ชัน Helper สำหรับการเรียก Bitkub API
  * `get_bitkub_balance()`: ดึงยอดคงเหลือของสินทรัพย์จาก Bitkub
  * `get_binance_klines()`: ดึงข้อมูล Candlestick จาก Binance ตาม Timeframe ที่กำหนด
  * `calculate_moving_average()`: ฟังก์ชันที่ถูกปรับปรุงให้สามารถคำนวณ SMA, EMA, WMA ได้
  * `place_bitkub_order()`: วางคำสั่งซื้อ (Bid) หรือขาย (Ask) บน Bitkub
  * `get_last_trade_type()`: ดึงประเภทการเทรดล่าสุดจาก Bitkub (ใช้ `my-order-history`)
  * `monitor_mas_on_candle_close()`: ฟังก์ชันหลักที่รันลูปเพื่อตรวจสอบสัญญาณ MA และดำเนินการเทรด

## ข้อจำกัดและความเสี่ยง

  * **ข้อมูลย้อนหลัง**: เนื่องจาก Bitkub API ไม่มีข้อมูลราคาในอดีต บอตนี้จึงใช้ Binance API ในการดึงข้อมูล หาก Binance API มีปัญหา อาจส่งผลกระทบต่อการทำงาน
  * **ค่าธรรมเนียมและ Slippage**: กลยุทธ์นี้ไม่ได้คำนึงถึงค่าธรรมเนียมการเทรดและ Slippage ในการคำนวณผลตอบแทน ซึ่งอาจลดทอนผลกำไรจริง
  * **Market Order (การดำเนินการคำสั่ง)**: บอตนี้ใช้ Market Order ซึ่งหมายความว่าคำสั่งซื้อ/ขายจะดำเนินการที่ราคาตลาดปัจจุบัน ซึ่งอาจไม่ตรงกับราคาที่คำนวณได้เป๊ะๆ โดยเฉพาะในตลาดที่มีสภาพคล่องต่ำหรือมีความผันผวนสูง
  * **Whipsaws**: ในตลาด Sideways หรือตลาดที่มีความผันผวนสูง กลยุทธ์ Crossover อาจให้สัญญาณซื้อ/ขายที่ผิดพลาดบ่อยครั้ง (Whipsaws) ซึ่งอาจทำให้เกิดการขาดทุน
  * **Black Swan Events**: กลยุทธ์นี้อาจไม่สามารถป้องกันการขาดทุนอย่างรุนแรงในกรณีที่เกิดเหตุการณ์ Black Swan (เหตุการณ์ไม่คาดฝันที่ส่งผลกระทบอย่างรุนแรง) ได้อย่างสมบูรณ์
  * **การจัดการเงินทุน (Money Management)**: บอตนี้ยังไม่มีระบบการจัดการเงินทุนที่ซับซ้อน เช่น การกำหนดขนาด Position แบบ Risk per trade และการ Pyramiding
  * **ข้อจำกัด API**: Bitkub API มี Rate Limit และข้อจำกัดอื่นๆ ที่ต้องพิจารณาในการออกแบบบอต เพื่อไม่ให้ถูกบล็อกการใช้งาน
  * **ความปลอดภัยของ API Key**: API Key และ Secret ควรถูกเก็บรักษาไว้อย่างปลอดภัย และไม่ควรอัปโหลดไฟล์ `config.json` ที่มีข้อมูลเหล่านี้ไปยัง Public Repository

โปรดใช้งานบอตนี้ด้วยความเข้าใจในความเสี่ยงและข้อจำกัดต่างๆ และพิจารณาปรับปรุงโค้ดให้เหมาะสมกับความต้องการและความเสี่ยงที่คุณยอมรับได้

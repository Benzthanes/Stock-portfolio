    const CHARTS_DATA = window.CHARTS_DATA || {};
    const STOCKS_META = window.STOCKS_META || {};

    // Technical Indicators Knowledge Base
    const INDICATOR_GUIDES = {
        ema9: {
            icon: '⚡',
            title: 'EMA 9 (Fast Momentum / แนวโน้มเร็ว)',
            cat: 'Trend Following',
            desc: 'เส้นค่าเฉลี่ยเคลื่อนที่แบบถ่วงน้ำหนักย้อนหลัง 9 วัน ตอบสนองต่อการเปลี่ยนแปลงราคาเร็วที่สุด เหมาะสำหรับดูแรงส่งและโมเมนตัมปัจจุบันของหุ้น.',
            usage: 'หากแท่งเทียนยืนเหนือเส้น EMA 9 ได้ต่อเนื่อง แสดงว่าแรงซื้อแข็งแกร่งมาก (Strong Momentum) แต่หากแท่งเทียนหลุดต่ำกว่าเส้น EMA 9 มักเป็นสัญญาณเตือนแรกว่ารอบการขึ้นกำลังเริ่มพักตัวหรือชะลอตัว.',
            tip: 'ใช้ดูควบคู่กับเส้น EMA 21 เมื่อเส้น EMA 9 ตัดขึ้นเหนือ EMA 21 เรียกว่า Golden Cross ระยะสั้น เป็นจุดเข้าซื้อตามโมเมนตัมที่ได้เปรียบ.'
        },
        ema21: {
            icon: '📈',
            title: 'EMA 21 (Short-Term Base / เส้นแนวรับสวิง)',
            cat: 'Trend Following',
            desc: 'เส้นค่าเฉลี่ยเคลื่อนที่ย้อนหลัง 21 วัน (ประมาณ 1 เดือนทำการ) เป็นเส้นฐานสำคัญที่สุดของนักลงทุนสาย Swing Trade ทั่วโลก.',
            usage: 'ในหุ้นขาขึ้นที่แข็งแกร่ง ราคาจะย่อตัวลงมาทดสอบเส้น EMA 21 แล้วดีดตัวกลับเสมอ (Pullback & Bounce) จึงเหมาะเป็นโซนตั้งรับซื้อ (Buy on Dip).',
            tip: 'หากราคาหลุดเส้น EMA 21 ด้วยวอลุ่มสูง เป็นสัญญาณให้ระมัดระวังและพิจารณาแบ่งขายทำกำไรเพื่อลดความเสี่ยง.'
        },
        ema50: {
            icon: '🏛️',
            title: 'EMA 50 (Institutional Line / เส้นสถาบันระยะกลาง)',
            cat: 'Medium-Term Trend',
            desc: 'เส้นค่าเฉลี่ยเคลื่อนที่ย้อนหลังประมาณ 1 ไตรมาส (2-3 เดือน) สถาบันการเงินและกองทุนใช้เป็นเส้นตัดสินทิศทางแนวโน้มหลักของรอบ.',
            usage: 'ตราบใดที่ราคาอยู่เหนือ EMA 50 โครงสร้างหลักยังคงเป็นขาขึ้น หากราคาย่อตัวลงมาชนเส้น EMA 50 มักมีแรงซื้อจากสถาบันเข้ามาพยุงราคา.',
            tip: 'หากเกิด Death Cross (เส้นสั้นตัดเส้น 50 ลง) แสดงว่าหุ้นกำลังเข้าสู่รอบพักฐานใหญ่ ควรรอให้ราคาเริ่มสร้างฐานให้ชัดเจนก่อนเข้าซื้อ.'
        },
        ema200: {
            icon: '🛡️',
            title: 'EMA 200 (Macro Bull/Bear Line / เส้นแบ่งยุคตลาด)',
            cat: 'Long-Term Macro Trend',
            desc: 'เส้นค่าเฉลี่ยเคลื่อนที่รอบ 1 ปี (200 วันทำการ) เป็นเส้นที่ทรงอิทธิพลที่สุดในตลาดหุ้นสหรัฐ ใช้แยกตลาดกระทิง (Bull) และตลาดหมี (Bear).',
            usage: 'หุ้นที่เทรดเหนือ EMA 200 จัดเป็นหุ้นในวัฏจักรขาขึ้นระยะยาว ส่วนหุ้นที่เทรดใต้เส้นนี้จัดว่าอยู่ในช่วงซึมตัวหรือพักฐาน.',
            tip: 'หุ้นผู้นำคุณภาพดีที่ย่อลงมาใกล้โซน EMA 200 (ระยะห่าง 0-5%) ถือเป็น Value Zone โซนทองคำของนักลงทุนระยะยาวที่มี Risk to Reward สูงเป็นพิเศษ.'
        },
        pivots: {
            icon: '🎯',
            title: 'Support and Resistance Levels with Breaks [LuxAlgo]',
            cat: 'Dynamic Pivot S/R & Volume Breakouts',
            desc: 'ระบบระบุแนวรับและแนวต้านเชิงสวิงตามโมเมนตัมแบบไดนามิก พัฒนาตามอัลกอริทึมของ LuxAlgo บน TradingView (Left Bars 15, Right Bars 12) พร้อมตรวจจับแท่งเทียนที่ระเบิดแนวต้าน (Breakout) หลุดแนวรับ (Breakdown) และแท่งเทียนกับดักหลอก (Bull Wick / Bear Wick).',
            usage: '🟢 <strong>Breakout (Vol):</strong> ราคาปิดทะลุแนวต้านพร้อมปริมาณ Volume Oscillator พุ่งเกิน +20% เป็นจุดตามน้ำ.<br>' +
                   '🔴 <strong>Breakdown (Vol):</strong> ราคาปิดหลุดแนวรับพร้อม Volume พุ่งสูง เป็นจุดตัดขาดทุนหรือเผ่น.<br>' +
                   '⚠️ <strong>Bull/Bear Wick (Trap):</strong> ราคาทะลุหรือหลุดแนวสำคัญแต่โดนแรงสถาบันกดดันจนทิ้งไส้ยาว เป็นกับดักราคาหลอก.',
            tip: 'ใช้ Volume Oscillator เป็นตัวกรอง Fakeout หากราคาเบรกแนวแต่ไม่มีวอลุ่มยืนยัน ให้ระวังการดึงกลับทันที.'
        },
        smc: {
            icon: '🏛️',
            title: 'Smart Money Concepts (SMC) [LuxAlgo]',
            cat: 'Institutional Order Flow & Gaps',
            desc: 'ระบบตรวจจับร่องรอยการเข้าซื้อและกระจายหุ้นของนักลงทุนสถาบัน (Smart Money) ตามมาตรฐาน LuxAlgo TradingView ครอบคลุม Fair Value Gaps (FVG) และ Order Blocks (OB).',
            usage: '🟢 <strong>Demand FVG & Bullish OB:</strong> โซนช่องว่างราคาที่ราคายังไม่ได้กลับมาแตะ (Unmitigated) ทำหน้าที่เป็นแม่เหล็กดึงดูดราคาให้ย่อลงมาทดสอบเพื่อเปิดสถานะซื้อ.<br>' +
                   '🔴 <strong>Supply FVG & Bearish OB:</strong> โซนช่องว่างราคาฝั่งขาย ทำหน้าที่เป็นแนวต้านสำคัญที่สถาบันรอเทขายทำกำไร.',
            tip: 'เมื่อราคาลงมาแตะกล่อง Fair Value Gap สีเขียว (Demand) โดยมี RSI ต่ำ มักเกิดการดีดตัวกลับอย่างรุนแรง.'
        },
        ew: {
            icon: '🌊',
            title: 'Elliott Wave Theory (ทฤษฎีคลื่น 1-2-3-4-5 และ A-B-C-D-E)',
            cat: 'Wave Theory & Market Cycles',
            desc: '<div style="margin-bottom:8px;"><strong>วัฏจักรคลื่นโมเมนตัมแบ่งออกเป็น 2 วงจรหลัก:</strong></div>' +
                  '<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px 12px; margin-bottom:10px;">' +
                  '<div style="font-weight:700; color:#38bdf8; margin-bottom:6px;">▲ 1. คลื่นขับเคลื่อนหลัก (Motive / Impulse Waves: 1 ถึง 5)</div>' +
                  '<ul style="margin:0; padding-left:18px; line-height:1.7;">' +
                  '<li><span style="color:#34d399; font-weight:700;">🟢 Wave (1) [คลื่นขึ้น]:</span> จุดเริ่มต้นรอบใหม่ สถาบันเริ่มแอบสะสมหุ้นเงียบๆ หลังผ่านจุดต่ำสุด.</li>' +
                  '<li><span style="color:#fb7185; font-weight:700;">🔴 Wave (2) [คลื่นลง/ย่อ]:</span> ย่อพักฐานเพื่อสลัดผู้เล่นใจไม่นิ่ง <em>(กฎ: ห้ามย่อหลุดจุดเริ่ม Wave 0)</em>.</li>' +
                  '<li><span style="color:#34d399; font-weight:700;">🟢 Wave (3) [คลื่นขึ้นใหญ่]:</span> คลื่นที่พุ่งแรงและยาวที่สุด สถาบันและมวลชนแห่ซื้อพร้อมกัน <em>(กฎ: ห้ามสั้นที่สุดใน 1, 3, 5)</em>.</li>' +
                  '<li><span style="color:#fb7185; font-weight:700;">🔴 Wave (4) [คลื่นลง/พักฐาน]:</span> พักฐานสะสมพลังชะลอตัว มักเป็นไซด์เวย์ <em>(กฎ: ห้ามย่อทับยอด Wave 1)</em>.</li>' +
                  '<li><span style="color:#34d399; font-weight:700;">🟢 Wave (5) [คลื่นขึ้นส่งท้าย]:</span> ดันราคาขึ้นรอบสุดท้าย รายย่อยไล่ซื้อตามข่าวดี แต่มักเกิด Bearish Divergence สถาบันเริ่มทยอยขาย.</li>' +
                  '</ul>' +
                  '</div>' +
                  '<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px 12px;">' +
                  '<div style="font-weight:700; color:#facc15; margin-bottom:6px;">🔄 2. คลื่นปรับฐาน (Corrective Waves: A-B-C และ A-B-C-D-E)</div>' +
                  '<ul style="margin:0; padding-left:18px; line-height:1.7;">' +
                  '<li><span style="color:#fb7185; font-weight:700;">🔴 Wave (A) [คลื่นลง]:</span> คลื่นทิ้งตัวรอบแรกหลังจบลูป 5 คลื่น แรงเทขายทำกำไรระลอกใหญ่.</li>' +
                  '<li><span style="color:#34d399; font-weight:700;">🟢 Wave (B) [คลื่นขึ้น/รีบาวด์หลอก]:</span> เด้งขึ้นระยะสั้น (Bull Trap) เพื่อล่อซื้อ ไม่ผ่านไฮเดิม.</li>' +
                  '<li><span style="color:#fb7185; font-weight:700;">🔴 Wave (C) [คลื่นลงปรับฐานจริง]:</span> ทิ้งตัวแรงและยาวนาน หลุดฐาน Wave A ลงสู่จุดสมดุลใหม่.</li>' +
                  '<li><span style="color:#38bdf8; font-weight:700;">📐 Wave (D) & (E) [คลื่นสามเหลี่ยมพักฐาน]:</span> เกิดในโครงสร้างสามเหลี่ยมบีบอัด (Triangle Correction A-B-C-D-E) โดย <span style="color:#34d399; font-weight:700;">Wave (D) [🟢 คลื่นขึ้น ไม่ผ่านไฮเดิม]</span> และ <span style="color:#fb7185; font-weight:700;">Wave (E) [🔴 คลื่นลง ไม่หลุดโลว์เดิม]</span> เป็นจุดเขย่าครั้งสุดท้ายก่อนระเบิดเทรนด์ใหม่.</li>' +
                  '</ul>' +
                  '</div>',
            usage: '<div style="margin-bottom:8px;"><strong>🎯 วิธีดูจังหวะเทรดและกฎเหล็ก 3 ข้อ (LuxAlgo Three Cardinal Rules):</strong></div>' +
                   '<div style="line-height:1.7;">' +
                   '• <strong>กฎข้อ 1:</strong> Wave (2) ห้ามย่อทะลุจุดเริ่มต้น Wave (0) หรือ Wave (1).<br>' +
                   '• <strong>กฎข้อ 2:</strong> Wave (4) ห้ามย่อเหลื่อมทับ (Overlap) อาณาเขตราคาของ Wave (1).<br>' +
                   '• <strong>กฎข้อ 3 (สำคัญที่สุด):</strong> Wave (3) ห้ามเป็นคลื่นที่สั้นที่สุดในบรรดาคลื่น Motive (1, 3, 5).<br>' +
                   '• <strong>LuxAlgo Golden Pocket (61.8%):</strong> หลังจบรอบ Wave (5) ระบบจะกางสัดส่วน Fibonacci 50.0%, 61.8% (Golden Pocket), 76.4% และ 85.4% Invalidation Floor เพื่อดักจับรอบพักฐาน.<br>' +
                   '• <strong>🟢 New Cycle Breakout:</strong> เมื่อราคาปรับฐาน A-B-C เสร็จและระเบิดผ่านยอดดอยเดิม ระบบจะยิงสัญญาณเริ่มคลื่นลูกใหม่ทันที.' +
                   '</div>',
            tip: '<div style="line-height:1.7;">' +
                 '⚠️ <strong>มาตรฐาน LuxAlgo:</strong> ระบบรองรับทั้งคลื่นขาขึ้น (Bullish Motive) และคลื่นขาลง (Bearish Motive) พร้อมตรวจจับสถานะ Invalidation (เส้นประ Dotted) เมื่อราคาละเมิดกฎคลื่น.' +
                 '</div>'
        },
        earn: {
            icon: '🗓️',
            title: 'ผลงบการเงินย้อนหลัง (Historical Earnings Reaction)',
            cat: 'Fundamental Catalyst',
            desc: 'ป้าย 🗓️ ±xx% แสดงผลตอบรับของราคาหุ้นต่อวันประกาศผลประกอบการจริงย้อนหลัง 3 ปี ซึ่งอ้างอิงจากปฏิทินงบที่ได้รับการยืนยันแล้ว ตัวเลขคือ % เปลี่ยนแปลงของราคา.',
            usage: 'ป้ายสีเหลืองทอง +xx% คือวันประกาศงบที่ราคากระโดดบวก ส่วนป้ายสีชมพู -xx% คือวันประกาศงบที่ราคาปรับตัวลง เพื่อให้เห็นปฏิกิริยารับงบชัดเจน.',
            tip: 'ช่วยให้เห็นประวัติและพฤติกรรมความผันผวนของหุ้นตัวนี้ในวันงบออก เพื่อใช้วางแผนบริหารความเสี่ยงก่อนถึงวันประกาศงบรอบถัดไป.'
        },
        fibo: {
            icon: '📐',
            title: 'Fibonacci Retracement (สัดส่วนทองคำธรรมชาติ)',
            cat: 'Support & Resistance',
            desc: 'อัตราส่วนพักฐานธรรมชาติ 23.6%, 38.2%, 50.0%, 61.8% (Golden Ratio) และ 78.6% คำนวณจากรอบ High และ Low ของวัฏจักร 52 สัปดาห์ หรือรอบ 2Y Macro (504 แท่งล่าสุด).',
            usage: 'ระดับ 61.8% และ 50.0% เป็นแนวรับทองคำที่มีแรงซื้อจากนักลงทุนทั่วโลกเข้ามาดักรับหนาแน่นที่สุด.',
            tip: 'สามารถกดปุ่ม 2Y Macro บนแถบ Fibo เพื่อสลับดูสัดส่วนราคาของรอบ 2 ปีล่าสุดได้ทันที.'
        },
        pat: {
            icon: '🏛️',
            title: 'Classical Chart Patterns (การตรวจจับรูปแบบกราฟ)',
            cat: 'Pattern Recognition',
            desc: 'ระบบตรวจจับรูปแบบราคาคลาสสิกอัตโนมัติ เช่น Double Bottom (กลับตัวขึ้น), Bull Flag (พักตัวเพื่อไปต่อ), Cup with Handle, และ Falling Wedge.',
            usage: 'ใช้ยืนยันจุดเบรกเอาต์ (Breakout Confirmation) และคำนวณเป้าหมายราคาตามความสูงของทรงกราฟ (Measured Move Target).',
            tip: 'อ่านเหตุผลเบื้องหลังจิตวิทยาตลาดในกล่อง Pattern Deep Dive ที่อยู่ด้านล่างของหน้าจอเพื่อทำความเข้าใจการเคลื่อนไหวของราคา.'
        },
        bb: {
            icon: '📊',
            title: 'Bollinger Bands (แถบวัดความผันผวน 20 วัน)',
            cat: 'Volatility & Mean Reversion',
            desc: 'ประกอบด้วยเส้นกลาง SMA 20 วัน และกรอบบน-กรอบล่างที่คำนวณจากส่วนเบี่ยงเบนมาตรฐาน (Standard Deviation ±2.0) ครอบคลุมการแกว่งตัวของราคาประมาณ 95%.',
            usage: 'เมื่อราคาหลุดลงมาแตะหรือทะลุกรอบล่าง บ่งชี้ภาวะ Oversold มีโอกาสเกิด Technical Rebound ดีดตัวกลับเข้าสู่เส้นกลาง.',
            tip: 'ช่วงที่แถบ Bollinger Bands บีบตัวแคบลงผิดปกติ (Squeeze) มักเป็นสัญญาณเตือนว่ากำลังจะเกิดการระเบิดตัวของราคาครั้งใหญ่ในเร็วๆ นี้.'
        },
        st: {
            icon: '🟢',
            title: 'Supertrend (ทิศทางเทรนด์ตามความผันผวน)',
            cat: 'Trend Following',
            desc: 'ตัวชี้วัดระบุทิศทางแนวโน้มที่คำนวณจากค่าเฉลี่ยความผันผวน ATR (10, Multiplier 3) ช่วยติดตามทิศทางของเทรนด์.',
            usage: 'เมื่อเส้นสีเขียวอยู่ใต้ราคา บ่งบอกสถานะขาขึ้น (Buy / Hold) เมื่อเส้นเปลี่ยนเป็นสีแดงอยู่เหนือราคา บ่งบอกสถานะขาลง (Sell / Exit).',
            tip: 'ใช้เส้น Supertrend เป็นจุด Trailing Stop ขยับตามราคาเพื่อล็อกกำไรคำโตโดยไม่ขายหมูกลางทาง.'
        },
        sar: {
            icon: '🟣',
            title: 'Parabolic SAR (จุดหยุดและกลับตัวของราคา)',
            cat: 'Momentum & Trailing Stop',
            desc: 'จุดไข่ปลา (Dots) ที่คำนวณจากความเร่งของราคา (Acceleration Factor) พัฒนาโดย J. Welles Wilder Jr.',
            usage: 'หากจุดไข่ปลาอยู่ใต้แท่งเทียน แสดงว่าแนวโน้มยังเป็นขาขึ้น ให้ถือหุ้นต่อ หากจุดสลับขึ้นมาอยู่เหนือแท่งเทียน แสดงว่ารอบการขึ้นสิ้นสุดลงแล้ว.',
            tip: 'เหมาะสำหรับใช้เป็นจุด Stop Loss หรือจุดปิดสถานะทำกำไรแบบอัตโนมัติ.'
        },
        ichi: {
            icon: '☁️',
            title: 'Ichimoku Kinko Hyo (ระบบเมฆอิจิโมกุ)',
            cat: 'Trend & Equilibrium',
            desc: 'ระบบวิเคราะห์สมดุลราคาจากญี่ปุ่น ประกอบด้วยกลุ่มเมฆ Kumo (Leading Span A & B) ที่แสดงแนวรับแนวต้านในอนาคต.',
            usage: 'ถ้าราคาเทรดอยู่เหนือเมฆเขียว แสดงว่าแนวโน้มแข็งแกร่งมาก เมฆจะทำหน้าที่เป็นเบาะรับราคาขนาดใหญ่ หากราคาหลุดใต้เมฆเป็นสัญญาณเปลี่ยนเทรนด์.',
            tip: 'ความหนาของเมฆสะท้อนถึงความแข็งแกร่งของแนวรับ ยิ่งเมฆหนา ราคาจะยิ่งดีดกลับได้ง่าย.'
        },
        vwap: {
            icon: '🟡',
            title: 'VWAP (Volume-Weighted Average Price)',
            cat: 'Volume & Benchmark',
            desc: 'ราคาเฉลี่ยที่แท้จริงของการซื้อขายทั้งหมดในรอบนั้น โดยถ่วงน้ำหนักตามปริมาณการซื้อขาย (Volume).',
            usage: 'กองทุนสถาบันใช้ VWAP เป็นมาตรวัดต้นทุน หากราคาอยู่ต่ำกว่า VWAP สถาบันจะมองว่าเป็นราคาที่มีส่วนลด (Discount) และมักเข้าซื้อสะสม.',
            tip: 'การที่ราคาสามารถทะลุผ่านเส้น VWAP ขึ้นไปได้ มักดึงดูดแรงซื้อตามของนักลงทุนสถาบันตามมา.'
        },
        cdc: {
            icon: '🚦',
            title: 'CDC ActionZone V3 2020 (ระบบเทรดตามแนวโน้มลุงโฉลก)',
            cat: 'Trend Following & Candle Color System',
            desc: 'ระบบสัญลักษณ์สีแท่งเทียนที่ได้รับความนิยมสูงสุดในไทย พัฒนาโดยคุณโฉลก สัมพันธารักษ์ (ลุงโฉลก) อิงเส้นคู่ Fast EMA 12 และ Slow EMA 26 วัน.',
            usage: 'แท่งสีเขียว (Bullish Run) คือสถานะถือรันเทรนด์ / ซื้อตาม, แท่งสีฟ้า (Take Profit / Buy on Dip) คือจุดพักตัวหรือเด้งกลับ, แท่งสีส้ม (Rebound in Downtrend) คือเด้งสั้นในขาลง, และแท่งสีแดง (Strong Bearish / Cash) คือสถานะถือเงินสด ไม่ซื้อ.',
            tip: 'จุดเข้าซื้อตามระบบคือวันแรกที่แท่งเทียนเปลี่ยนจากสีแดงเป็น สีเขียว (Golden Cross) และขายเมื่อเปลี่ยนเป็น สีแดง (Death Cross).'
        },
        rsi: {
            icon: '⚡',
            title: 'RSI 14 (Relative Strength Index / กำลังสัมพัทธ์)',
            cat: 'Momentum Oscillator',
            desc: 'ดัชนีวัดโมเมนตัมความเร็วและขนาดของการเคลื่อนไหวของราคา บนมาตรวัด 0 ถึง 100 ในกรอบเวลา 14 วัน.',
            usage: 'RSI < 30 บ่งชี้ภาวะขายมากเกินไป (Oversold โซนดักช้อนซื้อ) ส่วน RSI > 70 บ่งชี้ภาวะซื้อมากเกินไป (Overbought โซนระวังแรงขาย).',
            tip: 'สัญญาณสำคัญคือ Bullish Divergence เมื่อราคาหุ้นทำจุดต่ำสุดใหม่ (Lower Low) แต่ RSI ยกจุดต่ำสุดสูงขึ้น (Higher Low) มักบ่งชี้โอกาสการกลับตัวขึ้น.'
        },
        sqz: {
            icon: '🎯',
            title: 'Squeeze Momentum Indicator [LazyBear]',
            cat: 'Volatility Compression & Momentum Explosion',
            desc: 'อินดิเคเตอร์ยอดนิยมบน TradingView ของ LazyBear พัฒนาจากทฤษฎี John Carter TTM Squeeze วัดการบีบอัดตัวของ Bollinger Bands ภายใน Keltner Channels เพื่อจับจังหวะสะสมพลังก่อนระเบิดเทรนด์.',
            usage: '🟠 <strong>จุดสีส้ม/ดำ (Squeeze ON):</strong> ความผันผวนบีบตัวต่ำผิดปกติ เป็นช่วงสะสมพลังก่อนเลือกทิศทาง.<br>' +
                   '🟢 <strong>จุดสีเขียว/เทา (Squeeze FIRED):</strong> เกิดการระเบิดของกรอบความผันผวน พร้อมแท่งโมเมนตัมพุ่งขึ้น (เขียวสว่าง = ขาขึ้นเร่งตัว, แดงสว่าง = ขาลงเร่งตัว).',
            tip: 'เมื่อเห็นจุดสีส้มเกิดขึ้นติดต่อกันหลายแท่ง แล้วเปลี่ยนเป็นจุดสีเขียวพร้อมแท่งโมเมนตัมสีเขียวสว่าง บ่งชี้ว่าเกิดการเบรกเอาต์ความผันผวน.'
        },
        chand: {
            icon: '🪔',
            title: 'Chandelier Exit [everget]',
            cat: 'Volatility Trailing Stop',
            desc: 'ระบบ Trailing Stop-Loss ระดับตำนานของ Charles Le Beau ช่วยแก้ปัญหาการขายหมูหรือตกรถกลางทาง โดยคำนวณจุดหยุดการขาดทุนจากจุดสูงสุด Highest High ลบด้วย 3 เท่าของ ATR.',
            usage: '🟢 <strong>Long Stop (เส้นประ):</strong> ถือหุ้นรันเทรนด์ไปได้เรื่อยๆ ตราบใดที่ราคาปิดยังยืนเหนือเส้นนี้.<br>' +
                   '🔴 <strong>Sell / Flip to Short:</strong> เมื่อราคาปิดหลุดเส้น Long Stop ระบบจะสั่งปิดสถานะทันทีเพื่อล็อคกำไรก้อนใหญ่.',
            tip: 'เหมาะมากสำหรับนักลงทุนที่ต้องการรันเทรนด์ใหญ่ให้สุดทาง โดยปล่อยให้เส้น Chandelier Exit ขยับตามจุดสูงสุดใหม่ของหุ้น.'
        },
        aisig: {
            icon: '📌',
            title: 'Rule markers (BUY / DCA / TP)',
            cat: 'Algorithmic Signal System',
            desc: 'ระบบป้ายสัญญาณซื้อขายอัจฉริยะ (Rule-based Multi-Factor Engine) วิเคราะห์ร่วมกันระหว่างโมเมนตัม RSI, การตัดกันของเส้น EMA, สภาพคล่อง Order Block และ Fibonacci Golden Pocket.',
            usage: '🟢 <strong>BUY (1-5/5):</strong> สัญญาณจุดเข้าซื้อตามโมเมนตัม ยิ่งคะแนนสูงยิ่งมีความน่าเชื่อถือ.<br>' +
                   '🔵 <strong>DCA (1-5/5):</strong> สัญญาณจุดสะสมหุ้นเพิ่มเมื่อราคาย่อตัวลงมาแตะแนวรับสำคัญ.<br>' +
                   '🔴 <strong>TP (1-5/5):</strong> สัญญาณทยอยแบ่งขายทำกำไรเมื่อราคาเข้าใกล้เป้าหมาย Fibonacci หรือแนวต้าน.',
            tip: 'ใช้สัญญาณคะแนน 4/5 หรือ 5/5 เพื่อหาจุดเข้าที่ปลอดภัยและมีแต้มต่อ Risk-to-Reward สูงที่สุด.'
        },
        ext: {
            icon: '☀️',
            title: 'Pre-Market & After-Hours Extended Trading',
            cat: 'Extended Session Trading',
            desc: 'แสดงระดับราคาซื้อขายนอกเวลาตลาดสหรัฐ (Pre-Market 15:00-20:30 น. และ After-Hours 03:00-07:00 น. ตามเวลาไทย) เพื่อให้เห็นแนวโน้มราคาก่อนตลาดเปิดจริง.',
            usage: 'เส้นประแนวนอนสีฟ้า (บวก) หรือสีชมพู (ลบ) แสดงระดับราคาและเปอร์เซ็นต์เปลี่ยนแปลงล่าสุดเทียบกับราคาปิดรอบปกติ.',
            tip: 'ราคานอกเวลาตลาดมักมี Volume น้อยและผันผวนสูง ให้ใช้สังเกตการตอบสนองต่อข่าวและงบการเงิน.'
        }
    };

    let currentModalInd = null;
    function openIndicatorHelp(indKey, event) {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        const g = INDICATOR_GUIDES[indKey];
        if (!g) return;
        currentModalInd = indKey;

        document.getElementById('im_icon').textContent = g.icon;
        document.getElementById('im_title').textContent = g.title;
        document.getElementById('im_badge').textContent = g.cat;
        document.getElementById('im_desc').innerHTML = g.desc;
        document.getElementById('im_usage').innerHTML = g.usage;
        document.getElementById('im_tip').innerHTML = g.tip;

        const isSubpane = ['rsi', 'sqz'].includes(indKey);
        const isVis = isSubpane ? activeSubpaneOscs.includes(indKey) : indicatorVisibility[indKey];
        const btn = document.getElementById('im_toggle_btn');
        if (btn) {
            btn.textContent = isVis ? '👁️ ปิดเส้นนี้บนกราฟ' : '⚡ เปิดเส้นนี้บนกราฟ';
            btn.style.color = isVis ? '#fb7185' : '#38bdf8';
        }

        const modal = document.getElementById('ind_modal');
        if (modal) modal.classList.add('open');
    }

    function closeIndicatorHelp(event) {
        if (event && event.target !== event.currentTarget && !event.target.classList.contains('ind-modal-close')) {
            return;
        }
        const modal = document.getElementById('ind_modal');
        if (modal) modal.classList.remove('open');
    }

    function toggleFromModal() {
        if (!currentModalInd) return;
        const isSubpane = ['rsi', 'sqz'].includes(currentModalInd);
        if (isSubpane) {
            toggleSubpane(currentModalInd);
        } else {
            toggleIndicator(currentModalInd);
        }
        const isVis = isSubpane ? activeSubpaneOscs.includes(currentModalInd) : indicatorVisibility[currentModalInd];
        const btn = document.getElementById('im_toggle_btn');
        if (btn) {
            btn.textContent = isVis ? '👁️ ปิดเส้นนี้บนกราฟ' : '⚡ เปิดเส้นนี้บนกราฟ';
            btn.style.color = isVis ? '#fb7185' : '#38bdf8';
        }
    }

    function openNewsModal(ticker, idx) {
        const meta = STOCKS_META[ticker] || {};
        const news = meta.news || [];
        const item = news[idx];
        if (!item) return;

        const modal = document.getElementById('news_modal');
        if (!modal) return;

        const tickerElem = document.getElementById('nm_ticker');
        if (tickerElem) tickerElem.textContent = ticker;

        const metaElem = document.getElementById('nm_meta');
        if (metaElem) metaElem.textContent = (item.source || 'News') + ' • ' + (item.published || 'วันนี้');

        const badgeElem = document.getElementById('nm_sentiment_badge');
        const impactContainer = document.getElementById('nm_impact_container');
        const impactTitle = document.getElementById('nm_impact_title');

        const sent = (item.sentiment || 'neutral').toLowerCase();
        let sentText = '⚪ เป็นกลาง (Neutral)';
        let sentCol = '#94a3b8';
        let sentBg = 'rgba(148, 163, 184, 0.15)';
        let sentBorder = 'rgba(148, 163, 184, 0.3)';
        let impactBorder = 'rgba(148, 163, 184, 0.25)';
        let impactBg = 'rgba(148, 163, 184, 0.05)';
        let impactTitleCol = '#94a3b8';

        if (sent === 'bullish') {
            sentText = '🟢 เชิงบวก (Bullish)';
            sentCol = '#34d399';
            sentBg = 'rgba(16, 185, 129, 0.15)';
            sentBorder = 'rgba(16, 185, 129, 0.35)';
            impactBorder = 'rgba(16, 185, 129, 0.25)';
            impactBg = 'rgba(16, 185, 129, 0.06)';
            impactTitleCol = '#34d399';
        } else if (sent === 'bearish') {
            sentText = '🔴 เชิงลบ (Bearish)';
            sentCol = '#fb7185';
            sentBg = 'rgba(244, 63, 94, 0.15)';
            sentBorder = 'rgba(244, 63, 94, 0.35)';
            impactBorder = 'rgba(244, 63, 94, 0.25)';
            impactBg = 'rgba(244, 63, 94, 0.06)';
            impactTitleCol = '#fb7185';
        } else if (sent === 'mixed') {
            sentText = '🟡 สองด้าน (Mixed)';
            sentCol = '#fbbf24';
            sentBg = 'rgba(245, 158, 11, 0.15)';
            sentBorder = 'rgba(245, 158, 11, 0.35)';
            impactBorder = 'rgba(245, 158, 11, 0.25)';
            impactBg = 'rgba(245, 158, 11, 0.06)';
            impactTitleCol = '#fbbf24';
        }

        if (badgeElem) {
            badgeElem.textContent = sentText;
            badgeElem.style.color = sentCol;
            badgeElem.style.background = sentBg;
            badgeElem.style.borderColor = sentBorder;
        }

        if (impactContainer) {
            impactContainer.style.background = impactBg;
            impactContainer.style.borderColor = impactBorder;
        }
        if (impactTitle) {
            impactTitle.style.color = impactTitleCol;
        }

        const topicElem = document.getElementById('nm_topic');
        if (topicElem) topicElem.textContent = '🏷️ ' + (item.topic || 'ข่าวสารตลาดการเงิน');

        const isAi = Boolean(item.ai_analyzed);
        const disclaimerElem = document.getElementById('nm_disclaimer');
        const sumTitleElem = document.getElementById('nm_summary_title');

        if (disclaimerElem) {
            if (isAi) {
                disclaimerElem.style.color = '#34d399';
                disclaimerElem.style.background = 'rgba(16, 185, 129, 0.08)';
                disclaimerElem.style.borderColor = 'rgba(16, 185, 129, 0.35)';
                disclaimerElem.style.borderStyle = 'solid';
                disclaimerElem.innerHTML = '📰 <b>สรุปและแปลเชิงลึก</b> • แปลภาษาและสังเคราะห์สาระสำคัญตามบริบทธุรกิจจริง';
            } else {
                disclaimerElem.style.color = '#fbbf24';
                disclaimerElem.style.background = 'rgba(245, 158, 11, 0.08)';
                disclaimerElem.style.borderColor = 'rgba(245, 158, 11, 0.35)';
                disclaimerElem.style.borderStyle = 'dashed';
                disclaimerElem.innerHTML = '⚠️ หัวข้อแปลด้วย Google Translate ส่วนสรุป ผลกระทบ และกลยุทธ์ด้านล่างเป็นแนวทางทั่วไปตาม sentiment ของหัวข่าว ไม่ได้สรุปจากเนื้อข่าวจริง โปรดอ่านข่าวต้นฉบับประกอบ';
            }
        }

        if (sumTitleElem) {
            sumTitleElem.textContent = isAi ? '📌 สรุปสาระสำคัญเชิงลึก (AI Contextual Summary)' : '📌 ภาพรวมประเด็นข่าว (แนวทางทั่วไปตาม sentiment)';
        }

        const titleThElem = document.getElementById('nm_title_th');
        if (titleThElem) titleThElem.textContent = item.title_th || item.title || '-';

        const titleEnElem = document.getElementById('nm_title_en');
        if (titleEnElem) titleEnElem.textContent = item.title ? ('ต้นฉบับ EN: ' + item.title) : '';

        const summaryElem = document.getElementById('nm_summary');
        if (summaryElem) {
            const rawSum = item.summary_th || item.summary || 'ไม่มีสรุปเนื้อหาข่าว';
            const lines = rawSum.split('\n').filter(Boolean);
            if (lines.length > 0) {
                summaryElem.innerHTML = lines.map(line => '<div style="margin-bottom:6px; line-height:1.6;">' + escapeHtml(line) + '</div>').join('');
            } else {
                summaryElem.textContent = rawSum;
            }
        }

        const impactElem = document.getElementById('nm_impact');
        if (impactElem) impactElem.textContent = item.impact_th || '-';

        const actionElem = document.getElementById('nm_action');
        if (actionElem) actionElem.textContent = item.action_th || '-';

        const srcLinkElem = document.getElementById('nm_source_link');
        if (srcLinkElem) {
            srcLinkElem.href = item.link || '#';
            srcLinkElem.style.display = item.link ? 'inline-flex' : 'none';
        }

        modal.classList.add('open');
    }

    function closeNewsModal(event) {
        if (event && event.target !== event.currentTarget && !event.target.classList.contains('ind-modal-close')) {
            return;
        }
        const modal = document.getElementById('news_modal');
        if (modal) modal.classList.remove('open');
    }

    let activeLwChart = null;
    let activeRsiChart = null;
    let activeSubpaneCharts = [];
    let activeSubpaneOscs = ['rsi'];
    let activeCandleSeries = null;
    let activeRsiSeries = null;
    let currentStockTicker = '__DEFAULT_TICKER__';
    let currentStockExchange = 'NYSE';
    let currentCandles = [];
    let currentChartMode = 'tech';
    let dcaInputMode = 'USD';

    // INDICATORS VISIBILITY STATE
    const indicatorVisibility = {
        ema9: false,
        ema21: false,
        ema50: false,
        ema200: false,
        cdc: false,
        rsiPane: true, // RSI sub-pane defaults to active!
        pivots: false,
        smc: false,
        ew: false,
        earn: true,
        vwap: false,
        st: false,
        sar: false,
        ichi: false,
        bb: false,
        pat: false,
        fibo: false,
        chand: false,
        aisig: false,
        ext: true,
    };

    const chartSeriesRegistry = {
        ema9: [],
        ema21: [],
        ema50: [],
        ema200: [],
        cdc: [],
        vwap: [],
        st: [],
        sar: [],
        ichi: [],
        bb: [],
        pat: [],
        patPriceLines: [],
        ew: [],
        pivotLines: [],
        smcLines: [],
        ewPriceLines: [],
        fiboLines: [],
        chand: [],
        extPriceLine: null
    };

    const ALL_TICKERS = __SORTED_TICKERS_JSON__;
    let currentAggTimeframe = 'D';
    let currentFiboMode = 'cycle';

    function getWeekIdentifier(dateStr) {
        const d = new Date(dateStr);
        const day = d.getUTCDay();
        const diff = d.getUTCDate() - day + (day === 0 ? -6 : 1);
        const monday = new Date(d.setUTCDate(diff));
        return monday.toISOString().split('T')[0];
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, ch => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[ch]);
    }

    function safeUrl(url) {
        return /^https?:\/\//i.test(url || '') ? escapeHtml(url) : '#';
    }

    function aggregateCandles(candles, tf) {
        if (!candles || candles.length === 0 || tf === 'D') return candles;
        const groups = new Map();
        for (let i = 0; i < candles.length; i++) {
            const c = candles[i];
            let key = (tf === 'W') ? getWeekIdentifier(c.time) : c.time.substring(0, 7);
            if (!groups.has(key)) groups.set(key, []);
            groups.get(key).push(c);
        }
        const aggregated = [];
        for (const [key, list] of groups.entries()) {
            let high = -Infinity;
            let low = Infinity;
            let volume = 0;
            for (let j = 0; j < list.length; j++) {
                if (list[j].high > high) high = list[j].high;
                if (list[j].low < low) low = list[j].low;
                volume += (list[j].volume || 0);
            }
            aggregated.push({
                time: list[list.length - 1].time,
                open: list[0].open,
                high: Number(high.toFixed(2)),
                low: Number(low.toFixed(2)),
                close: list[list.length - 1].close,
                volume: volume
            });
        }
        return aggregated;
    }

    function setCandleAggregation(tf) {
        currentAggTimeframe = tf;
        document.querySelectorAll('.agg-tf-btn').forEach(b => b.classList.remove('active'));
        const btn = document.getElementById('agg_btn_' + tf);
        if (btn) btn.classList.add('active');
        renderLightweightChart(currentStockTicker);
    }

    function getActiveFibo(tData) {
        if (!tData) return {};
        if (currentFiboMode === 'macro' && tData.fibo_macro) {
            return tData.fibo_macro;
        }
        return tData.fibo_cycle || tData.fibo || {};
    }

    function drawFiboPriceLines(series, tData, mode) {
        if (!series || !tData) return [];
        const isMacro = (mode === 'macro');
        const fiboObj = isMacro ? (tData.fibo_macro || {}) : (tData.fibo_cycle || tData.fibo || {});
        const lines = [];
        const levels = [
            { key: '0.0', title: isMacro ? '🏔️ 0.0% 2Y High' : '📅 0.0% 52W High', color: 'rgba(244, 63, 94, 0.85)', width: isMacro ? 2 : 1 },
            { key: '23.6', title: '23.6%', color: 'rgba(56, 189, 248, 0.65)' },
            { key: '38.2', title: '38.2%', color: 'rgba(56, 189, 248, 0.75)' },
            { key: '50.0', title: '50.0% Mid', color: 'rgba(250, 204, 21, 0.85)' },
            { key: '61.8', title: '⭐ 61.8% Golden', color: 'rgba(16, 185, 129, 0.95)', width: 2 },
            { key: '78.6', title: '78.6%', color: 'rgba(168, 85, 247, 0.75)' },
            { key: '100.0', title: isMacro ? '🌊 100.0% 2Y Low' : '📅 100.0% 52W Low', color: 'rgba(16, 185, 129, 0.85)', width: isMacro ? 2 : 1 },
        ];

        levels.forEach(lvl => {
            const val = fiboObj[lvl.key];
            if (val !== undefined && val !== null) {
                try {
                    const pl = series.createPriceLine({
                        price: Number(val),
                        color: lvl.color,
                        lineWidth: lvl.width || 1,
                        lineStyle: lvl.key === '61.8' ? LightweightCharts.LineStyle.Solid : LightweightCharts.LineStyle.Dashed,
                        axisLabelVisible: true,
                        title: lvl.title + ' $' + Number(val).toFixed(2),
                    });
                    lines.push(pl);
                } catch (e) {}
            }
        });

        // When in 2Y Macro mode, ALSO draw the 52-Week High and 52-Week Low reference lines
        if (isMacro) {
            const cycleFibo = tData.fibo_cycle || tData.fibo || {};
            const w52Hi = cycleFibo['0.0'];
            const w52Lo = cycleFibo['100.0'];
            if (w52Hi !== undefined && w52Hi !== null) {
                try {
                    const pl = series.createPriceLine({
                        price: Number(w52Hi),
                        color: '#fb923c',
                        lineWidth: 1.5,
                        lineStyle: LightweightCharts.LineStyle.Dotted,
                        axisLabelVisible: true,
                        title: '📅 52W High $' + Number(w52Hi).toFixed(2),
                    });
                    lines.push(pl);
                } catch(e) {}
            }
            if (w52Lo !== undefined && w52Lo !== null) {
                try {
                    const pl = series.createPriceLine({
                        price: Number(w52Lo),
                        color: '#38bdf8',
                        lineWidth: 1.5,
                        lineStyle: LightweightCharts.LineStyle.Dotted,
                        axisLabelVisible: true,
                        title: '📅 52W Low $' + Number(w52Lo).toFixed(2),
                    });
                    lines.push(pl);
                } catch(e) {}
            }
        }

        return lines;
    }

    function toggleFiboCycleMode() {
        currentFiboMode = (currentFiboMode === 'cycle') ? 'macro' : 'cycle';
        const btn = document.getElementById('btn_fibo_mode');
        const lbl = document.getElementById('fibo_title_label');
        if (currentFiboMode === 'macro') {
            if (btn) btn.textContent = '🔄 สลับเป็น: 52W Cycle';
            if (lbl) lbl.textContent = '🏔️ 2Y MACRO FIBO:';
        } else {
            if (btn) btn.textContent = '🔄 สลับเป็น: 2Y Macro';
            if (lbl) lbl.textContent = '📐 52W CYCLE FIBO:';
        }

        const tData = CHARTS_DATA[currentStockTicker] || {};
        updateFiboChips(tData);

        if (!indicatorVisibility.fibo) {
            indicatorVisibility.fibo = true;
            const togBtn = document.getElementById('tog_fibo');
            if (togBtn) togBtn.classList.add('active');
        }

        if (activeCandleSeries) {
            if (chartSeriesRegistry.fiboLines) {
                chartSeriesRegistry.fiboLines.forEach(pl => {
                    try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                });
            }
            chartSeriesRegistry.fiboLines = drawFiboPriceLines(activeCandleSeries, tData, currentFiboMode);
        }

        if (indicatorVisibility.ew && activeLwChart && activeCandleSeries) {
            if (chartSeriesRegistry.ew) {
                chartSeriesRegistry.ew.forEach(s => {
                    try { activeLwChart.removeSeries(s); } catch(e) {}
                });
                chartSeriesRegistry.ew = [];
            }
            if (chartSeriesRegistry.ewPriceLines) {
                chartSeriesRegistry.ewPriceLines.forEach(pl => {
                    try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                });
                chartSeriesRegistry.ewPriceLines = [];
            }
            const res = drawElliottWave(activeLwChart, activeCandleSeries, tData);
            chartSeriesRegistry.ew = res.series;
            chartSeriesRegistry.ewPriceLines = res.priceLines;
            updateChartMarkers(activeCandleSeries, currentStockTicker);
        }
        if (indicatorVisibility.pat && activeLwChart && activeCandleSeries) {
            if (chartSeriesRegistry.pat) {
                chartSeriesRegistry.pat.forEach(s => {
                    try { activeLwChart.removeSeries(s); } catch(e) {}
                });
                chartSeriesRegistry.pat = [];
            }
            if (chartSeriesRegistry.patPriceLines) {
                chartSeriesRegistry.patPriceLines.forEach(pl => {
                    try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                });
                chartSeriesRegistry.patPriceLines = [];
            }
            const pRes = drawPatternLines(activeLwChart, activeCandleSeries, tData);
            chartSeriesRegistry.pat = pRes.series;
            chartSeriesRegistry.patPriceLines = pRes.priceLines;
            updateChartMarkers(activeCandleSeries, currentStockTicker);
        }
        updateElliottWaveSidebar(currentStockTicker);
    }

    function updateFiboChips(tData) {
        if (!tData) return;
        const isMacro = (currentFiboMode === 'macro');
        const fibo = isMacro ? (tData.fibo_macro || {}) : (tData.fibo_cycle || tData.fibo || {});
        const fmt = (v) => (v !== undefined && v !== null) ? '$' + Number(v).toFixed(2) : '-';

        const chip0 = document.getElementById('chip_f0');
        const chip100 = document.getElementById('chip_f100');
        if (chip0) chip0.textContent = (isMacro ? '0.0% 2Y High: ' : '0.0% High: ') + fmt(fibo['0.0']);
        document.getElementById('chip_f236').textContent = '23.6%: ' + fmt(fibo['23.6']);
        document.getElementById('chip_f382').textContent = '38.2%: ' + fmt(fibo['38.2']);
        document.getElementById('chip_f500').textContent = '50.0%: ' + fmt(fibo['50.0']);
        document.getElementById('chip_f618').textContent = '⭐ 61.8%: ' + fmt(fibo['61.8']);
        document.getElementById('chip_f786').textContent = '78.6%: ' + fmt(fibo['78.6']);
        if (chip100) chip100.textContent = (isMacro ? '100.0% 2Y Low: ' : '100.0% Low: ') + fmt(fibo['100.0']);

        const chip52Hi = document.getElementById('chip_w52_hi');
        const chip52Lo = document.getElementById('chip_w52_lo');
        if (isMacro) {
            const cycleFibo = tData.fibo_cycle || tData.fibo || {};
            if (chip52Hi) {
                chip52Hi.style.display = 'inline-flex';
                chip52Hi.textContent = '📅 52W High: ' + fmt(cycleFibo['0.0']);
            }
            if (chip52Lo) {
                chip52Lo.style.display = 'inline-flex';
                chip52Lo.textContent = '📅 52W Low: ' + fmt(cycleFibo['100.0']);
            }
        } else {
            if (chip52Hi) chip52Hi.style.display = 'none';
            if (chip52Lo) chip52Lo.style.display = 'none';
        }
    }

    function drawPivotPriceLines(series, tData, m) {
        if (!series || !tData) return [];
        const lines = [];
        const lastP = (currentCandles.length ? currentCandles[currentCandles.length - 1].close : 0);
        const r2Val = tData.pivots ? tData.pivots.r2 : 0;
        const r1Val = (m && m.resistance) || (tData.pivots ? tData.pivots.r1 : 0);
        const s1Val = (m && m.support) || (tData.pivots ? tData.pivots.s1 : 0);
        const s2Val = tData.pivots ? tData.pivots.s2 : 0;
        const slVal = (m && m.sl) || (tData.atr14 ? (lastP - 1.5 * tData.atr14.value) : 0);

        // LuxAlgo Support & Resistance Levels (Left 15, Right 12)
        const luxSr = tData.luxalgo_sr;
        if (luxSr && luxSr.resistance && Number(luxSr.resistance) > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(luxSr.resistance),
                    color: '#ec4899',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: '🟣 Lux Resistance $' + Number(luxSr.resistance).toFixed(2),
                }));
            } catch(e) {}
        }
        if (luxSr && luxSr.support && Number(luxSr.support) > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(luxSr.support),
                    color: '#38bdf8',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: '🔵 Lux Support $' + Number(luxSr.support).toFixed(2),
                }));
            } catch(e) {}
        }

        if (r2Val > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(r2Val),
                    color: 'rgba(236, 72, 153, 0.75)',
                    lineWidth: 1,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: '🟣 R2 $' + Number(r2Val).toFixed(2),
                }));
            } catch(e) {}
        }
        if (r1Val > 0 && (!luxSr || !luxSr.resistance)) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(r1Val),
                    color: '#ec4899',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: '🟣 R1 $' + Number(r1Val).toFixed(2),
                }));
            } catch(e) {}
        }
        const ppVal = tData.pivots ? tData.pivots.pivot : 0;
        if (ppVal > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(ppVal),
                    color: '#facc15',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: '🟡 PP $' + Number(ppVal).toFixed(2),
                }));
            } catch(e) {}
        }
        if (s1Val > 0 && (!luxSr || !luxSr.support)) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(s1Val),
                    color: '#38bdf8',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: '🔵 S1 $' + Number(s1Val).toFixed(2),
                }));
            } catch(e) {}
        }
        if (s2Val > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(s2Val),
                    color: 'rgba(56, 189, 248, 0.75)',
                    lineWidth: 1,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: '🛡️ S2 $' + Number(s2Val).toFixed(2),
                }));
            } catch(e) {}
        }
        if (slVal > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(slVal),
                    color: '#f97316',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Dotted,
                    axisLabelVisible: true,
                    title: '🛑 SL 1.5 ATR $' + Number(slVal).toFixed(2),
                }));
            } catch(e) {}
        }
        return lines;
    }

    function drawSmcPriceLines(series, tData) {
        if (!series || !tData || !tData.smc) return [];
        const lines = [];
        const smc = tData.smc;
        const fvgs = smc.unmitigated_fvgs || [];
        fvgs.forEach(f => {
            const isBull = f.type === 'BULLISH_FVG';
            const fvgCol = isBull ? 'rgba(56, 189, 248, 0.75)' : 'rgba(236, 72, 153, 0.75)';
            try {
                lines.push(series.createPriceLine({
                    price: Number(f.top),
                    color: fvgCol,
                    lineWidth: 1,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: (isBull ? '🔵 FVG Demand Top $' : '🟣 FVG Supply Top $') + Number(f.top).toFixed(2),
                }));
                lines.push(series.createPriceLine({
                    price: Number(f.bottom),
                    color: fvgCol,
                    lineWidth: 1,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: (isBull ? '🔵 FVG Demand Low $' : '🟣 FVG Supply Low $') + Number(f.bottom).toFixed(2),
                }));
            } catch(e) {}
        });
        const obs = smc.order_blocks || [];
        obs.forEach(ob => {
            const isBull = ob.type === 'BULLISH_OB';
            const obBottom = ob.bottom != null ? Number(ob.bottom) : null;
            const obTop = ob.top != null ? Number(ob.top) : null;
            const obLevel = ob.level != null ? Number(ob.level) : ((obBottom != null && obTop != null) ? (obBottom + obTop) / 2 : null);
            if (obLevel == null || isNaN(obLevel)) return;
            try {
                lines.push(series.createPriceLine({
                    price: obLevel,
                    color: isBull ? '#facc15' : '#ec4899',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: (isBull ? '🟡 Bullish OB $' : '🟣 Bearish OB $') + obLevel.toFixed(2),
                }));
            } catch(e) {}
        });
        return lines;
    }

    function getActiveElliottWave(tData) {
        if (!tData) return null;
        if (currentFiboMode === 'macro' && tData.elliott_wave_macro && tData.elliott_wave_macro.detected) {
            return tData.elliott_wave_macro;
        }
        return tData.elliott_wave;
    }

    function drawElliottWave(chart, series, tData) {
        const ew = getActiveElliottWave(tData);
        if (!chart || !series || !ew || !ew.detected) return { series: [], priceLines: [] };
        const ewSeriesList = [];
        const priceLines = [];

        const isBear = ew.direction === 'bearish';
        const isInvalid = ew.status === 'invalidated';
        const waveColor = isBear ? '#f43f5e' : '#818cf8';
        const waveStyle = isInvalid ? LightweightCharts.LineStyle.Dotted : LightweightCharts.LineStyle.Solid;

        if (ew.lines && ew.lines.length >= 2) {
            try {
                const s = chart.addLineSeries({
                    color: waveColor,
                    lineWidth: 2.5,
                    lineStyle: waveStyle,
                    title: (currentFiboMode === 'macro' ? '🏔️ EW Macro' : '🌊 EW Cycle') + (isBear ? ' (Bearish)' : ''),
                    visible: true,
                });
                s.setData(interpolatePatternPoints(ew.lines, currentCandles));
                ewSeriesList.push(s);
            } catch(e) {}
        }

        // LuxAlgo Post-Impulse Fibonacci Retracement Grid (Golden Pocket 61.8% & 85.4% Invalidation Floor)
        if (ew.fibo_pullback) {
            try {
                if (ew.fibo_pullback.fib_618) {
                    priceLines.push(series.createPriceLine({
                        price: Number(ew.fibo_pullback.fib_618),
                        color: '#f59e0b',
                        lineWidth: 1.5,
                        lineStyle: LightweightCharts.LineStyle.Dashed,
                        axisLabelVisible: true,
                        title: '🟡 EW Golden Pocket (61.8%) $' + Number(ew.fibo_pullback.fib_618).toFixed(2),
                    }));
                }
                if (ew.fibo_pullback.fib_854) {
                    const broken = ew.fibo_pullback.floor_broken;
                    priceLines.push(series.createPriceLine({
                        price: Number(ew.fibo_pullback.fib_854),
                        color: broken ? '#ef4444' : '#64748b',
                        lineWidth: 1.5,
                        lineStyle: LightweightCharts.LineStyle.Dotted,
                        axisLabelVisible: true,
                        title: (broken ? '❌ EW 85.4% Breached $' : '🛡️ EW 85.4% Floor $') + Number(ew.fibo_pullback.fib_854).toFixed(2),
                    }));
                }
            } catch(e) {}
        }

        if (ew.target && ew.target > 0) {
            try {
                const badge = ew.current_wave_badge || 'Target';
                priceLines.push(series.createPriceLine({
                    price: Number(ew.target),
                    color: isBear ? '#f43f5e' : '#38bdf8',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: (isBear ? '🎯 Bearish Target $' : '🎯 ' + badge + ' Target $') + Number(ew.target).toFixed(2),
                }));
            } catch(e) {}
        }

        if (ew.invalidation && ew.invalidation > 0) {
            try {
                priceLines.push(series.createPriceLine({
                    price: Number(ew.invalidation),
                    color: '#f43f5e',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Dotted,
                    axisLabelVisible: true,
                    title: (isBear ? '🛑 EW Roof $' : '🚫 EW Floor $') + Number(ew.invalidation).toFixed(2),
                }));
            } catch(e) {}
        }

        return { series: ewSeriesList, priceLines: priceLines };
    }

    function findClosestCandleIndex(candleTimes, targetTime) {
        if (!candleTimes || candleTimes.length === 0) return -1;
        const exact = candleTimes.indexOf(targetTime);
        if (exact !== -1) return exact;
        const targetMs = new Date(targetTime).getTime();
        let closestIdx = 0;
        let minDiff = Infinity;
        for (let i = 0; i < candleTimes.length; i++) {
            const diff = Math.abs(new Date(candleTimes[i]).getTime() - targetMs);
            if (diff < minDiff) {
                minDiff = diff;
                closestIdx = i;
            }
        }
        return closestIdx;
    }

    function interpolatePatternPoints(pts, candles) {
        if (!pts || pts.length < 2 || !candles || candles.length === 0) return pts || [];
        const candleTimes = candles.map(c => c.time);
        const res = [];
        for (let p = 0; p < pts.length - 1; p++) {
            const pA = pts[p];
            const pB = pts[p + 1];
            let idxA = candleTimes.indexOf(pA.time);
            let idxB = candleTimes.indexOf(pB.time);
            if (idxA === -1) idxA = findClosestCandleIndex(candleTimes, pA.time);
            if (idxB === -1) idxB = findClosestCandleIndex(candleTimes, pB.time);
            if (idxA === -1 || idxB === -1) continue;
            if (idxA >= idxB) {
                if (res.length === 0 || res[res.length - 1].time !== candleTimes[idxA]) {
                    res.push({ time: candleTimes[idxA], value: Number(pA.value || pA.price) });
                }
                res.push({ time: candleTimes[idxB], value: Number(pB.value || pB.price) });
                continue;
            }
            const span = idxB - idxA;
            const vA = Number(pA.value || pA.price);
            const vB = Number(pB.value || pB.price);
            for (let i = idxA; i <= idxB; i++) {
                if (res.length > 0 && res[res.length - 1].time === candleTimes[i]) continue;
                const ratio = (i - idxA) / span;
                const val = vA + (vB - vA) * ratio;
                res.push({
                    time: candleTimes[i],
                    value: Number(val.toFixed(2))
                });
            }
        }
        const ordered = [];
        for (const r of res) {
            if (ordered.length === 0 || new Date(r.time) > new Date(ordered[ordered.length - 1].time)) ordered.push(r);
        }
        return ordered;
    }

    function drawPatternLines(chart, series, tData) {
        const pat = tData ? tData.pattern : null;
        if (!chart || !series || !pat) return { series: [], priceLines: [] };
        const patSeriesList = [];
        const priceLines = [];

        // 1. Draw Pattern Boundary Lines (Necklines, Support/Resistance channels, Flag lines)
        if (pat.lines && pat.lines.length > 0) {
            pat.lines.forEach(lineDef => {
                if (!lineDef.points || lineDef.points.length < 2) return;
                const interpData = interpolatePatternPoints(lineDef.points, currentCandles);
                if (interpData && interpData.length >= 2) {
                    try {
                        const s = chart.addLineSeries({
                            color: lineDef.color || '#38bdf8',
                            lineWidth: 2,
                            lineStyle: LightweightCharts.LineStyle.Solid,
                            title: '🏛️ ' + (lineDef.name || pat.name),
                            visible: true,
                        });
                        s.setData(interpData);
                        patSeriesList.push(s);
                    } catch(e) {}
                }
            });
        }

        // 2. Draw Pattern Geometric Skeleton (Connecting swing key points like W, M, Shoulders, Head)
        // Do NOT draw zigzag skeleton across boundaries for channel, wedge, triangle, flag, or box patterns.
        const pNameLower = (pat.name || '').toLowerCase();
        const isBoundingPattern = pNameLower.includes('wedge') || pNameLower.includes('triangle') || pNameLower.includes('channel') || pNameLower.includes('flag') || pNameLower.includes('box');
        if (!isBoundingPattern && pat.key_points && pat.key_points.length >= 2) {
            const sortedKp = [...pat.key_points].sort((a, b) => new Date(a.time) - new Date(b.time));
            const skelPoints = sortedKp.map(kp => ({ time: kp.time, value: kp.price }));
            const skelData = interpolatePatternPoints(skelPoints, currentCandles);
            if (skelData && skelData.length >= 2) {
                try {
                    const isBear = pat.type && pat.type.toLowerCase().includes('bear');
                    const isFailed = pat.status === 'failed';
                    const isBrokeDown = pat.status === 'broke_down';
                    const isConfirmed = pat.status === 'confirmed';
                    const isForming = pat.status === 'forming' || (!isConfirmed && !isFailed && !isBrokeDown);
                    const skelColor = isFailed ? '#ef4444' : (isBrokeDown ? '#fb7185' : (isBear ? '#fb7185' : (isForming ? '#fbbf24' : '#34d399')));
                    const skelStatusText = isFailed ? ' (ล้มเหลว/หลุดรับ)' : (isBrokeDown ? ' (เบรกลง)' : (isConfirmed ? ' (ยืนยันแล้ว)' : ' (กำลังฟอร์มตัว)'));
                    const skelTitle = isFailed ? ('⚠️ ' + pat.name + skelStatusText) : (isBrokeDown ? ('🔻 ' + pat.name + skelStatusText) : ('🏛️ ' + pat.name + skelStatusText));
                    const skelSeries = chart.addLineSeries({
                        color: skelColor,
                        lineWidth: 2.5,
                        lineStyle: LightweightCharts.LineStyle.Solid,
                        title: skelTitle,
                        visible: true,
                    });
                    skelSeries.setData(skelData);
                    patSeriesList.push(skelSeries);
                } catch(e) {}
            }
        }

        // 3. Draw Price Lines for Neckline and Measured Move Target
        if (pat.neckline && pat.neckline > 0) {
            try {
                const patNameLower = String(pat.name || '').toLowerCase();
                const isNecklinePattern = patNameLower.includes('head') || patNameLower.includes('shoulder') || patNameLower.includes('double');
                const lineLabel = isNecklinePattern ? '🏛️ Neckline $' : '🏛️ แนวเบรก $';
                priceLines.push(series.createPriceLine({
                    price: Number(pat.neckline),
                    color: '#38bdf8',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: lineLabel + Number(pat.neckline).toFixed(2),
                }));
            } catch(e) {}
        }

        if (pat.target && pat.target > 0 && pat.status !== 'failed' && pat.status !== 'broke_down') {
            try {
                const uVal = typeof pat.upside_pct === 'number' ? pat.upside_pct : parseFloat(pat.upside_pct || 0);
                const isUp = uVal >= 0;
                const uSign = uVal > 0 ? '+' : (uVal < 0 ? '-' : '');
                const uStr = uSign + Math.abs(uVal).toFixed(1) + '%';
                const isForming = pat.status === 'forming';
                priceLines.push(series.createPriceLine({
                    price: Number(pat.target),
                    color: isUp ? '#facc15' : '#ec4899',
                    lineWidth: 2,
                    lineStyle: isForming ? LightweightCharts.LineStyle.Dashed : LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: '🎯 Target $' + Number(pat.target).toFixed(2) + (isForming ? ' (รอเบรก)' : ` (${uStr})`),
                }));
            } catch(e) {}
        }

        return { series: patSeriesList, priceLines: priceLines };
    }

    function parseEarningsDateToIso(str) {
        if (!str || str === '-' || str === 'None') return null;
        const trimmed = str.trim();
        if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return trimmed;
        const parts = trimmed.split(/\s+/);
        if (parts.length === 3) {
            const months = { jan: '01', feb: '02', mar: '03', apr: '04', may: '05', jun: '06', jul: '07', aug: '08', sep: '09', oct: '10', nov: '11', dec: '12' };
            const day = parts[0].padStart(2, '0');
            const m = months[parts[1].toLowerCase().slice(0, 3)] || '01';
            const y = parts[2];
            return y + '-' + m + '-' + day;
        }
        return null;
    }

    function getBusinessDaysBetween(startDateStr, endDateStr) {
        const dates = [];
        let cur = new Date(startDateStr + 'T00:00:00Z');
        const end = new Date(endDateStr + 'T00:00:00Z');

        cur.setUTCDate(cur.getUTCDate() + 1);
        while (cur < end) {
            const day = cur.getUTCDay();
            if (day !== 0 && day !== 6) {
                dates.push(cur.toISOString().split('T')[0]);
            }
            cur.setUTCDate(cur.getUTCDate() + 1);
        }
        dates.push(endDateStr);
        return dates;
    }

    let upcomingEarningsSeries = null;
    let currentEarningsIso = null;

    function ensureEarningsOverlay() {
        let overlay = document.getElementById('earnings_vertical_line_overlay');
        if (!overlay) {
            const wrap = document.getElementById('chart_container_wrap') || (document.getElementById('chart_container') ? document.getElementById('chart_container').parentElement : null);
            if (!wrap) return null;
            overlay = document.createElement('div');
            overlay.id = 'earnings_vertical_line_overlay';
            overlay.style.cssText = 'position: absolute; top: 0; bottom: 0; left: 0; right: 0; pointer-events: none; z-index: 10; display: none; overflow: hidden;';
            overlay.innerHTML = `
                <div id="v_earn_line" style="position: absolute; top: 0; bottom: 26px; width: 0px; border-left: 2px dashed #facc15; box-shadow: 0 0 10px rgba(250, 204, 21, 0.5); pointer-events: auto;">
                    <div id="v_earn_badge" style="position: absolute; top: 10px; left: 50%; transform: translateX(-50%); background: #12182b; border: 1.5px solid #facc15; color: #facc15; border-radius: 6px; padding: 4px 8px; font-size: 0.72rem; font-weight: 700; white-space: nowrap; box-shadow: 0 4px 14px rgba(0,0,0,0.6); display: flex; align-items: center; gap: 4px;">
                        <span style="font-size: 0.85rem;">🗓️</span>
                        <span id="v_earn_text">วันประกาศงบ</span>
                    </div>
                    <div style="position: absolute; bottom: 2px; left: 50%; transform: translateX(-50%); background: #facc15; color: #060810; font-size: 0.62rem; font-weight: 800; border-radius: 3px; padding: 1px 4px; white-space: nowrap; letter-spacing: 0.5px;">
                        EARNINGS
                    </div>
                </div>
            `;
            wrap.appendChild(overlay);
        }
        return overlay;
    }

    function syncVerticalEarningsPosition() {
        const overlay = ensureEarningsOverlay();
        if (!overlay || !activeLwChart || !currentEarningsIso || !indicatorVisibility.earn || currentChartMode !== 'tech') {
            if (overlay) overlay.style.display = 'none';
            return;
        }
        const timeScale = activeLwChart.timeScale();
        let coord = null;
        try {
            coord = timeScale.timeToCoordinate(currentEarningsIso);
            if (coord === null && typeof currentEarningsIso === 'string') {
                const parts = currentEarningsIso.split('-');
                if (parts.length === 3) {
                    coord = timeScale.timeToCoordinate({ year: parseInt(parts[0], 10), month: parseInt(parts[1], 10), day: parseInt(parts[2], 10) });
                }
            }
        } catch(e) {}

        if (coord === null || coord === undefined || isNaN(coord)) {
            overlay.style.display = 'none';
            return;
        }
        const container = document.getElementById('chart_container');
        const maxW = container ? container.clientWidth : 1000;
        if (coord < -20 || coord > maxW - 35) {
            overlay.style.display = 'none';
            return;
        }
        overlay.style.display = 'block';
        const vLine = document.getElementById('v_earn_line');
        if (vLine) {
            vLine.style.left = Math.round(coord) + 'px';
        }
    }

    function getDaysToEarningsDisplay(dEarn) {
        if (dEarn === null || dEarn === undefined || isNaN(dEarn)) return null;
        return Math.round(Number(dEarn));
    }

    function updateUpcomingEarnings(ticker) {
        if (!indicatorVisibility.earn) {
            currentEarningsIso = null;
            syncVerticalEarningsPosition();
            if (upcomingEarningsSeries && activeLwChart) {
                try { activeLwChart.removeSeries(upcomingEarningsSeries); } catch(e) {}
                upcomingEarningsSeries = null;
            }
            return;
        }

        const mInfo = STOCKS_META[ticker] || {};
        let dEarn = mInfo.days_to_earnings;
        const earnIso = parseEarningsDateToIso(mInfo.earnings_date);
        const lastBar = (currentCandles && currentCandles.length > 0) ? currentCandles[currentCandles.length - 1] : null;

        if (!lastBar || !earnIso || earnIso <= lastBar.time) {
            currentEarningsIso = null;
            syncVerticalEarningsPosition();
            if (upcomingEarningsSeries && activeLwChart) {
                try { activeLwChart.removeSeries(upcomingEarningsSeries); } catch(e) {}
                upcomingEarningsSeries = null;
            }
            return;
        }

        if (dEarn === null || dEarn === undefined) {
            const diffMs = new Date(earnIso) - new Date(lastBar.time);
            dEarn = Math.round(diffMs / (1000 * 60 * 60 * 24));
        }

        if (dEarn < 0 || dEarn > 120) {
            currentEarningsIso = null;
            syncVerticalEarningsPosition();
            if (upcomingEarningsSeries && activeLwChart) {
                try { activeLwChart.removeSeries(upcomingEarningsSeries); } catch(e) {}
                upcomingEarningsSeries = null;
            }
            return;
        }

        currentEarningsIso = earnIso;

        ensureEarningsOverlay();
        const vText = document.getElementById('v_earn_text');
        if (vText) {
            const roundedDays = getDaysToEarningsDisplay(dEarn);
            const earnDayTxt = roundedDays === 0 ? 'วันนี้' : (roundedDays !== null ? 'ใน ' + roundedDays + ' วัน' : '');
            vText.textContent = 'วันประกาศงบ: ' + (mInfo.earnings_date || '') + (earnDayTxt ? ' (' + earnDayTxt + ')' : '');
        }

        try {
            if (upcomingEarningsSeries && activeLwChart) {
                try { activeLwChart.removeSeries(upcomingEarningsSeries); } catch(e) {}
                upcomingEarningsSeries = null;
            }
            if (activeLwChart) {
                upcomingEarningsSeries = activeLwChart.addLineSeries({
                    color: 'transparent',
                    lineWidth: 1,
                    priceLineVisible: false,
                    lastValueVisible: false,
                    crosshairMarkerVisible: false,
                });
                const bDays = getBusinessDaysBetween(lastBar.time, earnIso);
                const timelineData = [
                    { time: lastBar.time, value: lastBar.close },
                    ...bDays.map(d => ({ time: d, value: lastBar.close }))
                ];
                upcomingEarningsSeries.setData(timelineData);
            }
        } catch(e) {
            console.warn('Could not set timeline data for earnings:', e);
        }

        syncVerticalEarningsPosition();
        requestAnimationFrame(syncVerticalEarningsPosition);
        setTimeout(syncVerticalEarningsPosition, 60);
    }

    function updateChartMarkers(series, ticker) {
        if (!series) return;
        const tData = CHARTS_DATA[ticker] || {};
        const mInfo = STOCKS_META[ticker] || {};
        const markers = [];

        // 1. High and Low Swing Points (Default ON)
        if (tData.swing_high && tData.swing_high.time) {
            markers.push({
                time: tData.swing_high.time,
                position: 'aboveBar',
                color: '#ec4899',
                shape: 'arrowDown',
                text: 'High $' + tData.swing_high.price,
            });
        }
        if (tData.swing_low && tData.swing_low.time) {
            markers.push({
                time: tData.swing_low.time,
                position: 'belowBar',
                color: '#38bdf8',
                shape: 'arrowUp',
                text: 'Low $' + tData.swing_low.price,
            });
        }

        // 2. Decision Signals - Evaluated from sig.type
        if (indicatorVisibility.aisig && tData.ai_signals) {
            const aiSignals = tData.ai_signals || [];
            aiSignals.forEach(sig => {
                let type = (sig.type || '').toUpperCase();
                // Map legacy action/type
                if (!type && sig.action) {
                    const act = (sig.action || '').toUpperCase();
                    if (act === 'ENTRY' || act === 'BUY' || act.includes('STRONG')) type = 'RULE_ENTRY';
                    else if (act === 'DCA') type = 'RULE_DCA';
                    else if (act === 'SELL' || act === 'TRIM' || act === 'TP') type = 'RULE_TP';
                    else if (act.includes('พักสัญญาณ') || sig.earnings_guard) type = 'EARNINGS_GUARD';
                    else if (act.includes('เลี่ยง') || act === 'AVOID') type = 'AVOID';
                    else if (act.includes('รอ') || act === 'WAIT' || act === 'HOLD') type = 'WAIT';
                }
                if ((type.includes('STRONG') && type.includes('BUY')) || type === 'BUY') {
                    type = 'RULE_ENTRY';
                } else if (type === 'DCA') {
                    type = 'RULE_DCA';
                } else if (type === 'SELL') {
                    type = 'RULE_TP';
                }

                // AVOID / HOLD / WAIT: do not render marker
                if (type === 'AVOID' || type === 'HOLD' || type === 'WAIT') {
                    return;
                }

                if (type === 'ENTRY' || type === 'RULE_ENTRY' || type === 'RULE_DCA') {
                    const isDca = type === 'RULE_DCA';
                    const scoreText = sig.score ? ` (${sig.score}/5)` : '';
                    markers.push({
                        time: sig.time,
                        position: 'belowBar',
                        color: sig.marker_color || (isDca ? '#38bdf8' : '#10b981'),
                        shape: sig.marker_shape || 'arrowUp',
                        text: (isDca ? 'DCA' : 'Entry') + scoreText,
                        id: 'sig_' + sig.time,
                    });
                } else if (type === 'RULE_TP' || type === 'TRIM') {
                    const isTrim = type === 'TRIM';
                    markers.push({
                        time: sig.time,
                        position: 'aboveBar',
                        color: sig.marker_color || (isTrim ? '#f59e0b' : '#f43f5e'),
                        shape: sig.marker_shape || 'arrowDown',
                        text: isTrim ? 'Trim' : 'TP',
                        id: 'sig_' + sig.time,
                    });
                } else if (type === 'EARNINGS_GUARD' || sig.earnings_guard) {
                    const gDays = sig.guard_days != null ? ` (${sig.guard_days}d)` : '';
                    markers.push({
                        time: sig.time,
                        position: sig.position || 'aboveBar',
                        color: sig.marker_color || '#facc15',
                        shape: 'circle',
                        text: 'พักสัญญาณ' + gDays,
                        id: 'sig_' + sig.time,
                    });
                }
            });
        }

        // Historical Earnings Reaction Markers (Rocket Tool Style: 'งบ +xx.x%')
        if (indicatorVisibility.earn && tData.earnings_history) {
            tData.earnings_history.forEach(e => {
                const rVal = typeof e.reaction_pct === 'number' ? e.reaction_pct : parseFloat(e.reaction_pct || 0);
                const isPos = rVal >= 0;
                const rSign = rVal > 0 ? '+' : (rVal < 0 ? '-' : '');
                const rStr = rSign + Math.abs(rVal).toFixed(1) + '%';
                markers.push({
                    time: e.time,
                    position: e.position || (isPos ? 'belowBar' : 'aboveBar'),
                    color: isPos ? '#facc15' : '#ec4899',
                    shape: 'circle',
                    size: 2,
                    text: '🗓️ ' + rStr,
                });
            });
        }

        // Elliott Wave Markers (0, 1, 2, 3, 4, 5, Live Current Bar, New Motive Cycle Breakout)
        const ew = getActiveElliottWave(tData);
        if (indicatorVisibility.ew && ew && ew.detected && ew.points) {
            const isBear = ew.direction === 'bearish';
            ew.points.forEach(pt => {
                const isNewCycle = pt.label && (pt.label.includes('New Cycle') || pt.label.includes('Breakout'));
                const isOddWave = pt.wave === '(1)' || pt.wave === '(3)' || pt.wave === '(5)';
                const isPeak = isBear ? !isOddWave : isOddWave;
                const isCurrent = pt.label && pt.label.includes('ปัจจุบัน');

                let mColor = isCurrent ? '#f59e0b' : (isBear ? '#f43f5e' : '#818cf8');
                let mShape = isCurrent ? 'circle' : (isPeak ? 'arrowDown' : 'arrowUp');
                let mSize = 1;

                if (isNewCycle) {
                    mColor = '#10b981';
                    mShape = 'circle';
                    mSize = 2;
                }

                markers.push({
                    time: pt.time,
                    position: isPeak ? 'aboveBar' : 'belowBar',
                    color: mColor,
                    shape: mShape,
                    size: mSize,
                    text: pt.label || (pt.wave + ' $' + Number(pt.price).toFixed(2)),
                });
            });
        }

        // Classical Chart Pattern Markers (Swing points: Bottoms, Tops, Shoulders, Neckline)
        const pat = tData.pattern;
        if (indicatorVisibility.pat && pat && pat.key_points && pat.key_points.length > 0) {
            const sortedKp = [...pat.key_points].sort((a, b) => new Date(a.time) - new Date(b.time));
            let lastMarkerTime = null;
            let lastMarkerPos = null;
            let lastMarkerPrice = null;

            sortedKp.forEach((kp, idx) => {
                const isStart = kp.role === 'start' || idx === 0;
                const isHi = (kp.name && (kp.name.toLowerCase().includes('top') || kp.name.toLowerCase().includes('peak') || kp.name.toLowerCase().includes('head') || kp.name.toLowerCase().includes('shoulder') || kp.name.toLowerCase().includes('high') || kp.name.toLowerCase().includes('resistance') || kp.name.toLowerCase().includes('ceiling')));
                const isBreakdown = kp.name && kp.name.toLowerCase().includes('breakdown');
                const isBreakout = kp.name && kp.name.toLowerCase().includes('breakout');

                let pos = isBreakdown ? 'belowBar' : (isBreakout ? 'aboveBar' : (isHi ? 'aboveBar' : 'belowBar'));

                // Anti-collision: if previous marker is within 7 days and close in price, alternate vertical position
                if (lastMarkerTime && lastMarkerPos) {
                    const dDiff = Math.abs((new Date(kp.time) - new Date(lastMarkerTime)) / (1000 * 60 * 60 * 24));
                    const pDiff = lastMarkerPrice ? Math.abs(kp.price - lastMarkerPrice) / lastMarkerPrice : 1;
                    if (dDiff <= 7 || pDiff <= 0.05) {
                        if (pos === lastMarkerPos) {
                            pos = (pos === 'aboveBar') ? 'belowBar' : 'aboveBar';
                        }
                    }
                }
                lastMarkerTime = kp.time;
                lastMarkerPos = pos;
                lastMarkerPrice = kp.price;

                if (isStart) {
                    markers.push({
                        time: kp.time,
                        position: pos,
                        color: '#facc15',
                        shape: 'circle',
                        text: '🚩 จุดเริ่มแพทเทิร์น: ' + (kp.name || 'Start') + ' $' + Number(kp.price).toFixed(2),
                        size: 2,
                    });
                } else if (isBreakdown) {
                    markers.push({
                        time: kp.time,
                        position: pos,
                        color: '#ef4444',
                        shape: 'arrowDown',
                        text: '⚠️ ' + kp.name + ' $' + Number(kp.price).toFixed(2),
                        size: 2,
                    });
                } else if (isBreakout) {
                    markers.push({
                        time: kp.time,
                        position: pos,
                        color: '#10b981',
                        shape: 'arrowUp',
                        text: '↗ ' + kp.name + ' $' + Number(kp.price).toFixed(2),
                        size: 2,
                    });
                } else {
                    markers.push({
                        time: kp.time,
                        position: pos,
                        color: pat.type && pat.type.toLowerCase().includes('bear') ? '#fb7185' : '#34d399',
                        shape: pos === 'aboveBar' ? 'arrowDown' : 'arrowUp',
                        text: '🏛️ ' + kp.name + ' $' + Number(kp.price).toFixed(2),
                    });
                }
            });
        }

        // LuxAlgo Support and Resistance Levels with Breaks & Wicks
        if (indicatorVisibility.pivots && tData.luxalgo_sr && tData.luxalgo_sr.recent_breaks) {
            tData.luxalgo_sr.recent_breaks.forEach(b => {
                const isBull = b.type === 'BREAKOUT_VOL' || b.type === 'BEAR_WICK';
                markers.push({
                    time: b.time,
                    position: isBull ? 'belowBar' : 'aboveBar',
                    color: b.type === 'BREAKOUT_VOL' ? '#10b981' : (b.type === 'BREAKDOWN_VOL' ? '#f43f5e' : '#f59e0b'),
                    shape: b.type === 'BREAKOUT_VOL' ? 'arrowUp' : (b.type === 'BREAKDOWN_VOL' ? 'arrowDown' : 'circle'),
                    size: b.type.includes('VOL') ? 2 : 1,
                    text: b.label + ' $' + Number(b.level).toFixed(2),
                });
            });
        }

        // Smart Money Concepts (SMC) Unmitigated FVGs & Order Blocks
        if (indicatorVisibility.smc && tData.smc) {
            if (tData.smc.unmitigated_fvgs) {
                tData.smc.unmitigated_fvgs.forEach(f => {
                    const isDemand = f.type === 'BULLISH_FVG';
                    markers.push({
                        time: f.time,
                        position: isDemand ? 'belowBar' : 'aboveBar',
                        color: isDemand ? '#38bdf8' : '#ec4899',
                        shape: 'circle',
                        size: 1,
                        text: (isDemand ? '🔵 Demand FVG' : '🟣 Supply FVG') + ' $' + Number(f.bottom).toFixed(2) + ' - $' + Number(f.top).toFixed(2),
                    });
                });
            }
            if (tData.smc.order_blocks) {
                tData.smc.order_blocks.forEach(ob => {
                    const isBull = ob.type === 'BULLISH_OB';
                    const obBottom = ob.bottom != null ? Number(ob.bottom) : null;
                    const obTop = ob.top != null ? Number(ob.top) : null;
                    const obLevel = ob.level != null ? Number(ob.level) : ((obBottom != null && obTop != null) ? (obBottom + obTop) / 2 : null);
                    markers.push({
                        time: ob.time,
                        position: isBull ? 'belowBar' : 'aboveBar',
                        color: isBull ? '#facc15' : '#ec4899',
                        shape: isBull ? 'arrowUp' : 'arrowDown',
                        size: 2,
                        text: ob.label || ((isBull ? '🟡 Demand OB $' : '🟣 Supply OB $') + (obLevel != null ? obLevel.toFixed(2) : '')),
                    });
                });
            }
        }

        // Squeeze Fired Markers on Candles (Only when sub-pane oscillator is active)
        if (activeSubpaneOscs.includes('sqz') && tData.squeeze_momentum && tData.squeeze_momentum.squeeze_fired && currentCandles.length > 0) {
            const lastBar = currentCandles[currentCandles.length - 1];
            const isBull = tData.squeeze_momentum.direction === 'BULLISH';
            markers.push({
                time: lastBar.time,
                position: isBull ? 'belowBar' : 'aboveBar',
                color: isBull ? '#facc15' : '#ec4899',
                shape: isBull ? 'arrowUp' : 'arrowDown',
                size: 2,
                text: '🎯 SQZ FIRED (' + (isBull ? 'Bull ▲' : 'Bear ⚠️') + ')',
            });
        }

        // Chandelier Exit flip markers
        if (indicatorVisibility.chand && tData.chandelier_exit && currentCandles.length > 0) {
            const ch = tData.chandelier_exit;
            if (ch.buy_signal) {
                markers.push({
                    time: currentCandles[currentCandles.length - 1].time,
                    position: 'belowBar',
                    color: '#10b981',
                    shape: 'arrowUp',
                    size: 2,
                    text: '🪔 CHAND BUY $' + Number(ch.long_stop).toFixed(2),
                });
            } else if (ch.sell_signal) {
                markers.push({
                    time: currentCandles[currentCandles.length - 1].time,
                    position: 'aboveBar',
                    color: '#f43f5e',
                    shape: 'arrowDown',
                    size: 2,
                    text: '🪔 CHAND SELL $' + Number(ch.short_stop).toFixed(2),
                });
            }
        }

        markers.sort((a, b) => new Date(a.time) - new Date(b.time));
        try {
            series.setMarkers(markers);
        } catch(e) {}
    }

    // Toggle Indicators
    function toggleIndicator(key) {
        indicatorVisibility[key] = !indicatorVisibility[key];
        const btn = document.getElementById('tog_' + key);
        if (btn) {
            if (indicatorVisibility[key]) btn.classList.add('active');
            else btn.classList.remove('active');
        }

        if (key === 'aisig') {
            updateChartMarkers(activeCandleSeries, currentStockTicker);
            return;
        }

        if (key === 'ext') {
            updateExtPriceLine(activeCandleSeries, currentStockTicker);
            return;
        }

        if (key === 'pivots') {
            const tData = CHARTS_DATA[currentStockTicker] || {};
            const m = STOCKS_META[currentStockTicker] || {};
            if (indicatorVisibility.pivots) {
                if (activeCandleSeries && (!chartSeriesRegistry.pivotLines || chartSeriesRegistry.pivotLines.length === 0)) {
                    chartSeriesRegistry.pivotLines = drawPivotPriceLines(activeCandleSeries, tData, m);
                }
            } else {
                if (activeCandleSeries && chartSeriesRegistry.pivotLines) {
                    chartSeriesRegistry.pivotLines.forEach(pl => {
                        try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                    });
                    chartSeriesRegistry.pivotLines = [];
                }
            }
            updateChartMarkers(activeCandleSeries, currentStockTicker);
            return;
        }

        if (key === 'smc') {
            const tData = CHARTS_DATA[currentStockTicker] || {};
            if (indicatorVisibility.smc) {
                if (activeCandleSeries && (!chartSeriesRegistry.smcLines || chartSeriesRegistry.smcLines.length === 0)) {
                    chartSeriesRegistry.smcLines = drawSmcPriceLines(activeCandleSeries, tData);
                }
            } else {
                if (activeCandleSeries && chartSeriesRegistry.smcLines) {
                    chartSeriesRegistry.smcLines.forEach(pl => {
                        try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                    });
                    chartSeriesRegistry.smcLines = [];
                }
            }
            updateChartMarkers(activeCandleSeries, currentStockTicker);
            return;
        }

        if (key === 'ew') {
            const tData = CHARTS_DATA[currentStockTicker] || {};
            if (indicatorVisibility.ew) {
                if (activeLwChart && activeCandleSeries && (!chartSeriesRegistry.ew || chartSeriesRegistry.ew.length === 0)) {
                    const res = drawElliottWave(activeLwChart, activeCandleSeries, tData);
                    chartSeriesRegistry.ew = res.series;
                    chartSeriesRegistry.ewPriceLines = res.priceLines;
                }
            } else {
                if (activeLwChart && chartSeriesRegistry.ew) {
                    chartSeriesRegistry.ew.forEach(s => {
                        try { activeLwChart.removeSeries(s); } catch(e) {}
                    });
                    chartSeriesRegistry.ew = [];
                }
                if (activeCandleSeries && chartSeriesRegistry.ewPriceLines) {
                    chartSeriesRegistry.ewPriceLines.forEach(pl => {
                        try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                    });
                    chartSeriesRegistry.ewPriceLines = [];
                }
            }
            updateChartMarkers(activeCandleSeries, currentStockTicker);
            return;
        }

        if (key === 'earn') {
            indicatorVisibility.upcomingEarn = indicatorVisibility.earn;
            updateUpcomingEarnings(currentStockTicker);
            updateChartMarkers(activeCandleSeries, currentStockTicker);
            return;
        }

        if (key === 'cdc') {
            if (activeCandleSeries) {
                if (indicatorVisibility.cdc) {
                    activeCandleSeries.setData(getCdcActionZoneCandles(currentCandles));
                } else {
                    activeCandleSeries.setData(currentCandles);
                }
            }
            const cdcSeries = chartSeriesRegistry.cdc || [];
            cdcSeries.forEach(s => {
                try { s.applyOptions({ visible: indicatorVisibility.cdc }); } catch(e) {}
            });
            return;
        }

        if (key === 'fibo') {
            const tData = CHARTS_DATA[currentStockTicker] || {};
            if (indicatorVisibility.fibo) {
                if (activeCandleSeries && (!chartSeriesRegistry.fiboLines || chartSeriesRegistry.fiboLines.length === 0)) {
                    chartSeriesRegistry.fiboLines = drawFiboPriceLines(activeCandleSeries, tData, currentFiboMode);
                }
            } else {
                if (activeCandleSeries && chartSeriesRegistry.fiboLines) {
                    chartSeriesRegistry.fiboLines.forEach(pl => {
                        try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                    });
                    chartSeriesRegistry.fiboLines = [];
                }
            }
            return;
        }

        if (key === 'pat') {
            const tData = CHARTS_DATA[currentStockTicker] || {};
            if (indicatorVisibility.pat) {
                if (activeLwChart && activeCandleSeries && (!chartSeriesRegistry.pat || chartSeriesRegistry.pat.length === 0)) {
                    const res = drawPatternLines(activeLwChart, activeCandleSeries, tData);
                    chartSeriesRegistry.pat = res.series;
                    chartSeriesRegistry.patPriceLines = res.priceLines;
                }
                const chartEl = document.getElementById('chart_container');
                if (chartEl) chartEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                if (activeLwChart && chartSeriesRegistry.pat) {
                    chartSeriesRegistry.pat.forEach(s => {
                        try { activeLwChart.removeSeries(s); } catch(e) {}
                    });
                    chartSeriesRegistry.pat = [];
                }
                if (activeCandleSeries && chartSeriesRegistry.patPriceLines) {
                    chartSeriesRegistry.patPriceLines.forEach(pl => {
                        try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                    });
                    chartSeriesRegistry.patPriceLines = [];
                }
            }
            const patBtn = document.getElementById('btn_toggle_pat_chart');
            if (patBtn) {
                if (indicatorVisibility.pat) {
                    patBtn.classList.add('active');
                    patBtn.textContent = '✅ ซ่อนเส้นแพทเทิร์น';
                } else {
                    patBtn.classList.remove('active');
                    patBtn.textContent = '⚡ ตีเส้นแพทเทิร์นบนกราฟ';
                }
            }
            updateChartMarkers(activeCandleSeries, currentStockTicker);
            return;
        }

        if (key === 'chand') {
            if (activeCandleSeries) {
                renderLightweightChart(currentStockTicker);
            }
            return;
        }

        const seriesList = chartSeriesRegistry[key] || [];
        seriesList.forEach(s => {
            try {
                s.applyOptions({ visible: indicatorVisibility[key] });
            } catch(e) {}
        });
    }

    // Sub-pane toggle and multi-selection logic
    function toggleSubpane(oscKey) {
        const idx = activeSubpaneOscs.indexOf(oscKey);
        if (idx >= 0) {
            activeSubpaneOscs.splice(idx, 1);
        } else {
            activeSubpaneOscs.push(oscKey);
        }
        indicatorVisibility.rsiPane = (activeSubpaneOscs.length > 0);
        updateSubpaneButtons();
        renderLightweightChart(currentStockTicker);
    }

    function switchOscillatorPane(oscKey) {
        toggleSubpane(oscKey);
    }

    function toggleRsiPane() {
        toggleSubpane('rsi');
    }

    function updateSubpaneButtons() {
        ['rsi', 'sqz'].forEach(k => {
            const btn = document.getElementById('tog_osc_' + k);
            if (btn) {
                if (activeSubpaneOscs.includes(k)) btn.classList.add('active');
                else btn.classList.remove('active');
            }
        });
    }

    function resetAllIndicators() {
        Object.keys(indicatorVisibility).forEach(k => {
            if (k !== 'rsiPane') {
                indicatorVisibility[k] = false;
                const btn = document.getElementById('tog_' + k);
                if (btn) btn.classList.remove('active');
            }
        });
        activeSubpaneOscs = [];
        indicatorVisibility.rsiPane = false;
        updateSubpaneButtons();

        if (activeCandleSeries) {
            activeCandleSeries.setData(currentCandles);
            if (chartSeriesRegistry.fiboLines) {
                chartSeriesRegistry.fiboLines.forEach(pl => {
                    try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                });
                chartSeriesRegistry.fiboLines = [];
            }
            if (chartSeriesRegistry.pivotLines) {
                chartSeriesRegistry.pivotLines.forEach(pl => {
                    try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                });
                chartSeriesRegistry.pivotLines = [];
            }
            if (chartSeriesRegistry.smcLines) {
                chartSeriesRegistry.smcLines.forEach(pl => {
                    try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                });
                chartSeriesRegistry.smcLines = [];
            }
            if (chartSeriesRegistry.ewPriceLines) {
                chartSeriesRegistry.ewPriceLines.forEach(pl => {
                    try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                });
                chartSeriesRegistry.ewPriceLines = [];
            }
            if (chartSeriesRegistry.patPriceLines) {
                chartSeriesRegistry.patPriceLines.forEach(pl => {
                    try { activeCandleSeries.removePriceLine(pl); } catch(e) {}
                });
                chartSeriesRegistry.patPriceLines = [];
            }
            if (chartSeriesRegistry.extPriceLine) {
                try { activeCandleSeries.removePriceLine(chartSeriesRegistry.extPriceLine); } catch(e) {}
                chartSeriesRegistry.extPriceLine = null;
            }
        }
        if (activeLwChart && chartSeriesRegistry.ew) {
            chartSeriesRegistry.ew.forEach(s => {
                try { activeLwChart.removeSeries(s); } catch(e) {}
            });
            chartSeriesRegistry.ew = [];
        }
        if (activeLwChart && chartSeriesRegistry.pat) {
            chartSeriesRegistry.pat.forEach(s => {
                try { activeLwChart.removeSeries(s); } catch(e) {}
            });
            chartSeriesRegistry.pat = [];
        }
        const patBtn = document.getElementById('btn_toggle_pat_chart');
        if (patBtn) {
            patBtn.classList.remove('active');
            patBtn.textContent = '⚡ ตีเส้นแพทเทิร์นบนกราฟ';
        }
        Object.keys(chartSeriesRegistry).forEach(k => {
            if (k !== 'fiboLines' && k !== 'pivotLines' && k !== 'smcLines' && k !== 'ewPriceLines' && k !== 'ew' && k !== 'pat' && k !== 'patPriceLines') {
                (chartSeriesRegistry[k] || []).forEach(s => {
                    try { s.applyOptions({ visible: false }); } catch(e) {}
                });
            }
        });
        indicatorVisibility.upcomingEarn = false;
        currentEarningsIso = null;
        if (upcomingEarningsSeries && activeLwChart) {
            try { activeLwChart.removeSeries(upcomingEarningsSeries); } catch(e) {}
            upcomingEarningsSeries = null;
        }
        syncVerticalEarningsPosition();
        updateChartMarkers(activeCandleSeries, currentStockTicker);
    }

    function updateElliottWaveSidebar(ticker) {
        const tData = CHARTS_DATA[ticker] || {};
        const ewBody = document.getElementById('ew_sidebar_body');
        const ewDegree = document.getElementById('ew_degree');
        if (!ewBody) return;

        const ew = getActiveElliottWave(tData);
        if (!ew || !ew.detected) {
            if (ewDegree) ewDegree.textContent = 'Consolidation / Sideway';
            ewBody.innerHTML = `
                <div style="display:flex; align-items:center; gap:6px; margin-bottom:8px;">
                    <span style="font-size:0.75rem; font-weight:700; padding:3px 8px; border-radius:6px; color:#94a3b8; background:rgba(148, 163, 184, 0.12); border:1px solid rgba(148, 163, 184, 0.25);">
                        ⚪ พักฐาน / สะสมพลังไซด์เวย์
                    </span>
                </div>
                <div style="font-size:0.78rem; color:#cbd5e1; line-height:1.5;">
                    ${ew && ew.summary ? ew.summary : 'ไม่พบโครงสร้างคลื่นโมเมนตัมที่สมบูรณ์ในรอบล่าสุด (ราคาอยู่ในสภาวะพักฐาน ปรับฐาน หรือสะสมพลังไซด์เวย์ แนะนำอ้างอิง Classical Chart Pattern หรือแนวรับต้าน EMA ในการจับจังหวะเทรด)'}
                </div>
            `;
            return;
        }

        if (ewDegree) ewDegree.textContent = (currentFiboMode === 'macro' ? '🏔️ All-Time Macro Wave' : '📐 52W Intermediate Wave');
        const targetStr = ew.target ? ('$' + Number(ew.target).toFixed(2)) : '-';
        const invalStr = ew.invalidation ? ('$' + Number(ew.invalidation).toFixed(2)) : '-';
        const waveBadge = ew.current_wave_badge || ew.current_wave || '(3) กำลังขึ้น';
        const wavePhase = ew.current_wave_phase || (ew.direction === 'bearish' ? 'Bearish Motive Expansion' : 'Impulse Wave Expansion');

        let badgeCol = '#818cf8';
        let badgeBg = 'rgba(129, 140, 248, 0.15)';
        let badgeBorder = 'rgba(129, 140, 248, 0.35)';

        if (waveBadge.includes('New Cycle') || (ew.cycle_signal && ew.cycle_signal.includes('New'))) {
            badgeCol = '#10b981';
            badgeBg = 'rgba(16, 185, 129, 0.15)';
            badgeBorder = 'rgba(16, 185, 129, 0.35)';
        } else if (ew.direction === 'bearish' || waveBadge.includes('Bear')) {
            badgeCol = '#f43f5e';
            badgeBg = 'rgba(244, 63, 94, 0.15)';
            badgeBorder = 'rgba(244, 63, 94, 0.35)';
        } else if (waveBadge.includes('5')) {
            badgeCol = '#38bdf8';
            badgeBg = 'rgba(56, 189, 248, 0.15)';
            badgeBorder = 'rgba(56, 189, 248, 0.35)';
        } else if (waveBadge.includes('3')) {
            badgeCol = '#34d399';
            badgeBg = 'rgba(16, 185, 129, 0.15)';
            badgeBorder = 'rgba(16, 185, 129, 0.35)';
        } else if (waveBadge.includes('4') || waveBadge.includes('2')) {
            badgeCol = '#fbbf24';
            badgeBg = 'rgba(245, 158, 11, 0.15)';
            badgeBorder = 'rgba(245, 158, 11, 0.35)';
        } else if (waveBadge.includes('C') || waveBadge.includes('A')) {
            badgeCol = '#fb7185';
            badgeBg = 'rgba(244, 63, 94, 0.15)';
            badgeBorder = 'rgba(244, 63, 94, 0.35)';
        }

        let fiboRowsHtml = '';
        if (ew.fibo_pullback) {
            const f618 = ew.fibo_pullback.fib_618 ? ('$' + Number(ew.fibo_pullback.fib_618).toFixed(2)) : '-';
            const f854 = ew.fibo_pullback.fib_854 ? ('$' + Number(ew.fibo_pullback.fib_854).toFixed(2)) : '-';
            const broken = ew.fibo_pullback.floor_broken;
            fiboRowsHtml = `
                <tr>
                    <td class="kl-name" style="color:#f59e0b;">🟡 Golden Pocket (61.8%)</td>
                    <td class="kl-val" style="color:#f59e0b; font-weight:700;">${f618}</td>
                </tr>
                <tr>
                    <td class="kl-name" style="color:${broken ? '#ef4444' : '#94a3b8'};">🛡️ LuxAlgo Floor (85.4%)</td>
                    <td class="kl-val" style="color:${broken ? '#ef4444' : '#94a3b8'}; font-weight:700;">${f854}${broken ? ' ⚠️ Breached' : ''}</td>
                </tr>
            `;
        }

        ewBody.innerHTML = `
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 8px;">
                <span style="font-size:0.75rem; font-weight:800; padding:3px 9px; border-radius:6px; color:${badgeCol}; background:${badgeBg}; border:1px solid ${badgeBorder};">
                    📍 ปัจจุบัน: ${ew.current_wave || waveBadge}
                </span>
                <span style="font-size:0.68rem; color:#94a3b8; font-weight:600;">${wavePhase}</span>
            </div>
            <div style="font-size:0.78rem; color:#cbd5e1; line-height:1.5; margin-bottom:8px;">
                ${ew.summary || ''}
            </div>
            <table class="kl-table" style="margin-top:6px;">
                <tbody>
                    <tr>
                        <td class="kl-name" style="color:${ew.direction === 'bearish' ? '#f43f5e' : '#38bdf8'};">🎯 เป้าหมาย ${ew.direction === 'bearish' ? 'Bear Target' : 'Wave (5)'}</td>
                        <td class="kl-val" style="color:${ew.direction === 'bearish' ? '#f43f5e' : '#38bdf8'}; font-weight:700;">${targetStr}</td>
                    </tr>
                    <tr>
                        <td class="kl-name" style="color:#fb7185;">🛑 จุดเสียทรง (${ew.direction === 'bearish' ? 'Roof' : 'Floor'})</td>
                        <td class="kl-val" style="color:#fb7185; font-weight:700;">${invalStr}</td>
                    </tr>
                    ${fiboRowsHtml}
                </tbody>
            </table>
            <div style="margin-top:8px; font-size:0.70rem; color:#94a3b8;">
                💡 ถอดแบบตรรกะ LuxAlgo 3 Cardinal Rules & Fibonacci Retracement Grid ลากเชื่อมต่อ Live Candle อัตโนมัติ
            </div>
        `;
    }

    function updateScoreSidebar(ticker) {
        const body = document.getElementById('score_sidebar_body');
        const badge = document.getElementById('score_grade_badge');
        if (!body) return;
        const meta = STOCKS_META[ticker] || {};
        const sc = meta.score;
        if (!sc) {
            body.innerHTML = '<div style="color:#94a3b8;">ไม่มีข้อมูลคะแนนสำหรับหุ้นนี้</div>';
            if (badge) badge.textContent = '-';
            return;
        }
        const gradeColor = {'A+': '#34d399', 'A': '#34d399', 'B': '#fbbf24', 'C': '#fb923c', 'F': '#fb7185'}[sc.grade] || '#94a3b8';
        if (badge) {
            badge.textContent = sc.grade === 'ETF' ? 'ETF' : `เกรด ${sc.grade}` + (sc.total != null ? ` · ${Math.round(sc.total)}/100` : '');
            badge.style.color = gradeColor;
        }
        const bar = (label, val, hint) => {
            const v = val == null ? null : Math.max(0, Math.min(100, val));
            const fill = v == null ? '' : `<div style="height:100%; width:${v}%; background:${v >= 70 ? '#34d399' : v >= 40 ? '#fbbf24' : '#fb7185'}; border-radius:4px;"></div>`;
            return `<div style="margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between;"><span>${label}</span><b>${v == null ? 'ไม่ประเมิน' : Math.round(v) + '/100'}</b></div>
                <div style="height:6px; background:rgba(255,255,255,0.06); border-radius:4px; margin-top:3px;">${fill}</div>
                <div style="font-size:0.68rem; color:#94a3b8; margin-top:2px;">${hint}</div>
            </div>`;
        };
        const reasons = (sc.reasons || []).map(r => `<li>${escapeHtml(r)}</li>`).join('');
        const flags = [];
        if (sc.timing && sc.timing.entry_signal) flags.push('<span style="color:#34d399; font-weight:700;">⤴ Entry Signal (RSI Hook)</span>');
        if (sc.earnings_guard) {
            const thresh = sc.guard_days_threshold || meta.earnings_guard_days;
            const roundedDays = getDaysToEarningsDisplay(meta.days_to_earnings);
            let threshText = 'ใกล้วันประกาศงบ';
            if (roundedDays !== null && roundedDays >= 0) {
                threshText = roundedDays === 0 ? 'งบออกวันนี้' : `งบออกใน ${roundedDays} วัน`;
            } else if (thresh) {
                threshText = `งบออกภายใน ${thresh} วัน`;
            }
            flags.push(`<span style="color:#fb923c; font-weight:700;">🟠 ${threshText} (ระงับการถัว)</span>`);
        }
        body.innerHTML = `
            ${bar('🏦 พื้นฐาน (60%)', sc.pillars.fundamental, 'รายได้ กำไร ROE PEG D/E FCF')}
            ${bar('📍 โซนราคา vs EMA200 (40%)', sc.pillars.timing, 'วัดจาก backtest: โซน 0-10% เหนือ EMA200 มี drawdown ต่ำสุด')}
            ${flags.length ? `<div style="margin:6px 0;">${flags.join('<br>')}</div>` : ''}
            <ul style="margin:6px 0 0 16px; padding:0;">${reasons}</ul>
            <div style="margin-top:8px; font-size:0.68rem; color:#94a3b8;">ข้อมูลครบ ${Math.round((sc.coverage || 0) * 100)}% • อินดิเคเตอร์ประกอบบนกราฟ (Squeeze, Chandelier) ไม่ผ่าน backtest จึงไม่นับคะแนน</div>
        `;
    }

    function updateSmcSidebar(ticker) {
        const tData = CHARTS_DATA[ticker] || {};
        const smcBody = document.getElementById('smc_sidebar_body');
        const msBadge = document.getElementById('smc_ms_badge');
        if (!smcBody) return;

        const smc = tData.smc;
        const luxSr = tData.luxalgo_sr;

        if (!smc && !luxSr) {
            smcBody.innerHTML = '<div style="font-size:0.78rem; color:#94a3b8;">ไม่พบข้อมูลโครงสร้างสถาบัน</div>';
            return;
        }

        const ms = (smc && smc.structure) || 'NEUTRAL';
        if (msBadge) {
            msBadge.textContent = ms === 'BULLISH' ? '🟢 Bullish Structure' : (ms === 'BEARISH' ? '🔴 Bearish Structure' : '⚪ Neutral Flow');
        }

        const fvgs = (smc && smc.unmitigated_fvgs) || [];
        const obs = (smc && smc.order_blocks) || [];
        const breaks = (luxSr && luxSr.recent_breaks) || [];

        let fvgHtml = '';
        if (fvgs.length > 0) {
            fvgHtml = fvgs.slice(-2).map(f => {
                const isBull = f.type === 'BULLISH_FVG';
                const col = isBull ? '#34d399' : '#fb7185';
                const bg = isBull ? 'rgba(52, 211, 153, 0.12)' : 'rgba(251, 113, 133, 0.12)';
                return `
                    <div style="display:flex; justify-content:space-between; align-items:center; background:${bg}; border-radius:6px; padding:4px 8px; margin-bottom:4px; font-size:0.75rem;">
                        <span style="color:${col}; font-weight:700;">${isBull ? '🟢 Demand FVG' : '🔴 Supply FVG'}</span>
                        <span style="color:#f8fafc; font-family:monospace; font-weight:600;">$${f.bottom.toFixed(2)} - $${f.top.toFixed(2)}</span>
                    </div>
                `;
            }).join('');
        } else {
            fvgHtml = '<div style="font-size:0.72rem; color:#94a3b8; margin-bottom:4px;">ไม่มี Unmitigated FVG ตกค้าง</div>';
        }

        let obHtml = '';
        if (obs.length > 0) {
            const lastOb = obs[obs.length - 1];
            const isBull = lastOb.type === 'BULLISH_OB';
            const obBottom = lastOb.bottom != null ? Number(lastOb.bottom) : null;
            const obTop = lastOb.top != null ? Number(lastOb.top) : null;
            const obLevel = lastOb.level != null ? Number(lastOb.level) : ((obBottom != null && obTop != null) ? (obBottom + obTop) / 2 : 0);
            const rangeText = (obBottom != null && obTop != null)
                ? `$${obBottom.toFixed(2)} - $${obTop.toFixed(2)}`
                : `$${obLevel.toFixed(2)}`;
            obHtml = `
                <div style="display:flex; justify-content:space-between; align-items:center; background:${isBull ? 'rgba(56, 189, 248, 0.12)' : 'rgba(244, 63, 94, 0.12)'}; border-radius:6px; padding:4px 8px; margin-bottom:4px; font-size:0.75rem;">
                    <span style="color:${isBull ? '#38bdf8' : '#f43f5e'}; font-weight:700;">${lastOb.label || (isBull ? '🛡️ Demand OB' : '🛑 Supply OB')}</span>
                    <span style="color:#f8fafc; font-family:monospace; font-weight:600;">${rangeText} (${lastOb.time})</span>
                </div>
            `;
        }

        let breaksHtml = '';
        if (breaks.length > 0) {
            const lastBreak = breaks[breaks.length - 1];
            breaksHtml = `
                <div style="margin-top:6px; font-size:0.73rem; color:#cbd5e1; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:6px; padding:6px 8px;">
                    <div style="font-weight:700; color:#facc15; margin-bottom:2px;">🎯 สัญญาณ Lux S/R ล่าสุด:</div>
                    <div>${lastBreak.label} ที่ $${Number(lastBreak.level).toFixed(2)} <span style="color:#94a3b8;">(${lastBreak.time})</span></div>
                    <div style="color:#94a3b8; font-size:0.68rem; margin-top:2px;">${(lastBreak.desc || '').replace(/\+\s*-\s*/g, '- ')}</div>
                </div>
            `;
        }

        smcBody.innerHTML = `
            <div style="margin-bottom:6px;">
                <div style="font-size:0.70rem; color:#94a3b8; font-weight:700; margin-bottom:4px;">โซนช่องว่างราคาของสถาบัน (Fair Value Gaps):</div>
                ${fvgHtml}
            </div>
            ${obHtml ? `
            <div style="margin-bottom:6px;">
                <div style="font-size:0.70rem; color:#94a3b8; font-weight:700; margin-bottom:4px;">โซนต้นทุนบล็อกคำสั่ง (Order Block):</div>
                ${obHtml}
            </div>` : ''}
            ${breaksHtml}
            <div style="margin-top:6px; font-size:0.68rem; color:#64748b;">
                ⚡ ตรวจจับ Fair Value Gaps, Order Blocks และ Breakouts ด้วยปริมาณ Volume Oscillator ตามสคริปต์ LuxAlgo
            </div>
        `;
    }

    function updateOscillatorsSidebar(ticker) {
        const tData = CHARTS_DATA[ticker] || {};
        const container = document.getElementById('osc_sidebar_body');
        const badge = document.getElementById('osc_sidebar_badge');
        if (!container) return;

        const sqz = tData.squeeze_momentum;

        if (!sqz) {
            container.innerHTML = '<div style="font-size:0.78rem; color:#94a3b8;">ไม่พบข้อมูลโมเมนตัม</div>';
            return;
        }

        let sqzStatusText = '⚪ ปกติ';
        let sqzColor = '#94a3b8';
        let sqzBg = 'rgba(148, 163, 184, 0.12)';
        if (sqz.squeeze_on) {
            sqzStatusText = '🟠 Squeeze ON (สะสมพลัง)';
            sqzColor = '#f97316';
            sqzBg = 'rgba(249, 115, 22, 0.15)';
        } else if (sqz.squeeze_fired) {
            sqzStatusText = '🟢 Squeeze FIRED (ระเบิดเทรนด์)';
            sqzColor = '#10b981';
            sqzBg = 'rgba(16, 185, 129, 0.15)';
        }

        if (badge) {
            badge.textContent = 'ไม่ผ่าน backtest ใช้ประกอบเท่านั้น';
            badge.style.color = '#f59e0b';
        }

        container.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:6px;">
                <div style="background:${sqzBg}; border:1px solid ${sqzColor}40; border-radius:6px; padding:6px 8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
                        <span style="font-weight:700; color:${sqzColor}; font-size:0.75rem;">🎯 LazyBear Squeeze</span>
                        <span style="font-weight:800; color:${sqzColor}; font-size:0.72rem;">${sqzStatusText}</span>
                    </div>
                    <div style="font-size:0.70rem; color:#cbd5e1;">${sqz.summary || ''}</div>
                </div>
            </div>
            <div style="margin-top:8px; font-size:0.68rem; color:#64748b;">
                💡 สลับดูกราฟย่อยได้ทันทีด้วยปุ่ม SUB-PANE ด้านบน (⚡ RSI | 🎯 Squeeze Mom)
            </div>
        `;
    }

    function updateMlSidebar(ticker) {
        const tData = CHARTS_DATA[ticker] || {};
        const container = document.getElementById('ml_sidebar_body');
        const badge = document.getElementById('ml_sidebar_badge');
        if (!container) return;

        const ch = tData.chandelier_exit;

        if (!ch) {
            container.innerHTML = '<div style="font-size:0.78rem; color:#94a3b8;">ไม่พบข้อมูล Chandelier Exit</div>';
            return;
        }

        let chColor = ch.direction === 'LONG' ? '#10b981' : '#f43f5e';
        let chBg = ch.direction === 'LONG' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(244, 63, 94, 0.12)';
        let chText = (ch.trailing_stop != null) ? `${ch.direction} (Stop $${Number(ch.trailing_stop).toFixed(2)})` : `${ch.direction}`;

        if (badge) {
            badge.textContent = 'ไม่ผ่าน backtest ใช้ประกอบเท่านั้น';
            badge.style.color = '#f59e0b';
        }

        container.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:6px;">
                <div style="background:${chBg}; border:1px solid ${chColor}40; border-radius:6px; padding:6px 8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2px;">
                        <span style="font-weight:700; color:${chColor}; font-size:0.75rem;">🪔 Chandelier Exit</span>
                        <span style="font-weight:800; color:${chColor}; font-size:0.72rem;">${chText}</span>
                    </div>
                    <div style="font-size:0.70rem; color:#cbd5e1;">${ch.summary || ''}</div>
                </div>
            </div>
            <div style="margin-top:8px; font-size:0.68rem; color:#64748b;">
                💡 เปิด/ปิดเส้น Chandelier Exit ได้ที่แถบ Toolbar ด้านบนกราฟ
            </div>
        `;
    }

    function updateWhalesSidebar(ticker) {
        const meta = STOCKS_META[ticker] || {};
        const whales = meta.whales || [];
        const container = document.getElementById('whales_sidebar_body');
        if (!container) return;

        if (whales.length === 0) {
            container.innerHTML = `
                <div style="font-size:0.78rem; color:#94a3b8; line-height:1.5;">
                    เป็นกองทุนดัชนีหรือหุ้นที่กระจายการถือครองในหมู่นักลงทุนสถาบันทั่วไป
                </div>
            `;
            return;
        }

        let html = '';
        whales.forEach(w => {
            html += `
                <div class="whale-item">
                    <div class="whale-top">
                        <div style="display:flex; align-items:center; gap:6px;">
                            <span style="font-size:1.05rem;">${w.icon || '🐋'}</span>
                            <div>
                                <div style="font-size:0.80rem; font-weight:700; color:#f8fafc;">${escapeHtml(w.name)}</div>
                                <div style="font-size:0.68rem; color:#94a3b8;">${escapeHtml(w.fund)}</div>
                            </div>
                        </div>
                        <span class="whale-badge" style="background:${w.action_color || '#3b82f6'}22; color:${w.action_color || '#60a5fa'}; border: 1px solid ${w.action_color || '#3b82f6'}55;">
                            ${escapeHtml(w.action)}
                        </span>
                    </div>
                    <div style="font-size:0.74rem; font-weight:700; color:#93c5fd; margin-top:4px;">
                        💰 ${escapeHtml(w.shares_str)}
                    </div>
                    <div style="font-size:0.72rem; color:#cbd5e1; margin-top:3px; line-height:1.4;">
                        ${escapeHtml(w.summary)}
                    </div>
                </div>
            `;
        });
        const asOf = whales[0] && whales[0].as_of ? whales[0].as_of : '';
        if (asOf) html += `<div style="font-size:0.66rem; color:#94a3b8; margin-top:6px; line-height:1.4;">📅 ${escapeHtml(asOf)}</div>`;
        container.innerHTML = html;
    }

    function updateNewsSidebar(ticker) {
        const meta = STOCKS_META[ticker] || {};
        const news = meta.news || [];
        const container = document.getElementById('news_sidebar_body');
        const badgeElem = document.getElementById('news_count_badge');
        if (!container) return;

        if (badgeElem) {
            badgeElem.textContent = news.length > 0 ? (news.length + ' ข่าวล่าสุด') : 'ไม่มีข่าว';
        }

        if (news.length === 0) {
            container.innerHTML = `
                <div style="font-size:0.78rem; color:#94a3b8; line-height:1.5; padding:8px 0;">
                    ไม่พบข่าวสารล่าสุดหรืออยู่ในช่วงไม่มีประเด็นสำคัญสำหรับ ${ticker}
                </div>
            `;
            return;
        }

        let html = '';
        news.forEach((item, idx) => {
            const sent = (item.sentiment || 'neutral').toLowerCase();
            let sentBadge = '⚪ เป็นกลาง';
            let sentCol = '#94a3b8';
            let sentBg = 'rgba(148, 163, 184, 0.12)';
            let sentBorder = 'rgba(148, 163, 184, 0.25)';

            if (sent === 'bullish') {
                sentBadge = '🟢 เชิงบวก';
                sentCol = '#34d399';
                sentBg = 'rgba(16, 185, 129, 0.15)';
                sentBorder = 'rgba(16, 185, 129, 0.35)';
            } else if (sent === 'bearish') {
                sentBadge = '🔴 เชิงลบ';
                sentCol = '#fb7185';
                sentBg = 'rgba(244, 63, 94, 0.15)';
                sentBorder = 'rgba(244, 63, 94, 0.35)';
            } else if (sent === 'mixed') {
                sentBadge = '🟡 สองด้าน';
                sentCol = '#fbbf24';
                sentBg = 'rgba(245, 158, 11, 0.15)';
                sentBorder = 'rgba(245, 158, 11, 0.35)';
            }

            const enLink = safeUrl(item.link);
            const displayTitle = escapeHtml(item.title_th || item.title);
            const topicText = item.topic ? `🏷️ ${escapeHtml(item.topic)}` : '';

            html += `
                <div class="news-item" onclick="openNewsModal('${ticker}', ${idx})">
                    <div class="news-top">
                        <span class="news-source-meta">${escapeHtml(item.source || 'News')} • ${escapeHtml(item.published || 'วันนี้')}</span>
                        <span class="news-sentiment-badge" style="color: ${sentCol}; background: ${sentBg}; border: 1px solid ${sentBorder};">
                            ${sentBadge}
                        </span>
                    </div>
                    ${topicText ? `<div style="font-size:0.65rem; color:#38bdf8; font-weight:700; margin-bottom:5px;">${topicText}</div>` : ''}
                    <div class="news-title">
                        ${displayTitle}
                    </div>
                    ${item.ai_analyzed
                        ? `<div class="news-ai-tag" style="display:inline-flex; align-items:center; gap:4px; font-size:0.64rem; font-weight:700; color:#34d399; background:rgba(16, 185, 129, 0.12); border:1px solid rgba(16, 185, 129, 0.3); border-radius:4px; padding:2px 6px; margin:4px 0 6px;">📰 สรุปข่าวเชิงลึก</div>`
                        : `<div class="news-heuristic" title="เซนติเมนต์และสรุปสร้างจากคีย์เวิร์ดในพาดหัว ไม่ได้อ่านเนื้อข่าวจริง" style="font-size:0.62rem; color:#94a3b8; margin:4px 0 6px;">🔎 วิเคราะห์จากคีย์เวิร์ด</div>`}
                    <div class="news-actions-row">
                        <button class="news-btn-th" onclick="event.stopPropagation(); openNewsModal('${ticker}', ${idx})">
                            🔍 สรุปไทย & วิเคราะห์
                        </button>
                        <a href="${enLink}" target="_blank" rel="noopener noreferrer" class="news-btn-en" onclick="event.stopPropagation()">
                            🔗 ต้นฉบับ EN
                        </a>
                    </div>
                </div>
            `;
        });
        container.innerHTML = html;
    }

    // Technical Math Utilities
    function calcEMA(candles, period) {
        if (!candles || candles.length < period) return [];
        const k = 2 / (period + 1);
        let sum = 0;
        for (let i = 0; i < period; i++) sum += candles[i].close;
        let ema = sum / period;
        const res = [{ time: candles[period - 1].time, value: Number(ema.toFixed(2)) }];
        for (let i = period; i < candles.length; i++) {
            ema = candles[i].close * k + ema * (1 - k);
            res.push({ time: candles[i].time, value: Number(ema.toFixed(2)) });
        }
        return res;
    }

    function calcRSI(candles, period = 14) {
        if (!candles || candles.length <= period) return [];
        const res = [];
        let gains = 0, losses = 0;
        for (let i = 1; i <= period; i++) {
            const change = candles[i].close - candles[i - 1].close;
            if (change >= 0) gains += change;
            else losses += Math.abs(change);
        }
        let avgGain = gains / period;
        let avgLoss = losses / period;
        let rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
        let rsi = avgLoss === 0 ? 100 : 100 - (100 / (1 + rs));
        res.push({ time: candles[period].time, value: Number(rsi.toFixed(2)) });

        for (let i = period + 1; i < candles.length; i++) {
            const change = candles[i].close - candles[i - 1].close;
            const gain = change >= 0 ? change : 0;
            const loss = change < 0 ? Math.abs(change) : 0;
            avgGain = (avgGain * (period - 1) + gain) / period;
            avgLoss = (avgLoss * (period - 1) + loss) / period;
            rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
            rsi = avgLoss === 0 ? 100 : 100 - (100 / (1 + rs));
            res.push({ time: candles[i].time, value: Number(rsi.toFixed(2)) });
        }
        return res;
    }

    function calcVWAP(candles, anchorTime) {
        if (!candles || candles.length === 0) return [];
        let cumV = 0, cumVP = 0;
        const res = [];
        for (let i = 0; i < candles.length; i++) {
            const c = candles[i];
            if (anchorTime && c.time < anchorTime) continue;
            const v = c.volume > 0 ? c.volume : 1;
            const typ = (c.high + c.low + c.close) / 3;
            cumVP += typ * v;
            cumV += v;
            res.push({ time: c.time, value: Number((cumVP / cumV).toFixed(2)) });
        }
        return res;
    }

    function calcBollinger(candles, period = 20, mult = 2.0) {
        if (!candles || candles.length < period) return { upper: [], lower: [], middle: [] };
        const upper = [], lower = [], middle = [];
        for (let i = period - 1; i < candles.length; i++) {
            let sum = 0;
            for (let j = 0; j < period; j++) sum += candles[i - j].close;
            const mean = sum / period;
            let sqDiff = 0;
            for (let j = 0; j < period; j++) sqDiff += Math.pow(candles[i - j].close - mean, 2);
            const std = Math.sqrt(sqDiff / period);
            const t = candles[i].time;
            middle.push({ time: t, value: Number(mean.toFixed(2)) });
            upper.push({ time: t, value: Number((mean + mult * std).toFixed(2)) });
            lower.push({ time: t, value: Number((mean - mult * std).toFixed(2)) });
        }
        return { upper, lower, middle };
    }

    function calcParabolicSAR(candles, step = 0.02, maxStep = 0.2) {
        if (!candles || candles.length < 5) return [];
        const res = [];
        let isLong = candles[1].close > candles[0].close;
        let af = step;
        let ep = isLong ? candles[0].high : candles[0].low;
        let sar = isLong ? candles[0].low : candles[0].high;

        for (let i = 1; i < candles.length; i++) {
            const c = candles[i];
            const prev = candles[i - 1];
            sar = sar + af * (ep - sar);
            if (isLong) {
                if (i >= 2) sar = Math.min(sar, prev.low, candles[i - 2].low);
                else sar = Math.min(sar, prev.low);
                if (c.low < sar) {
                    isLong = false;
                    sar = ep;
                    af = step;
                    ep = c.low;
                } else {
                    if (c.high > ep) {
                        ep = c.high;
                        af = Math.min(af + step, maxStep);
                    }
                }
            } else {
                if (i >= 2) sar = Math.max(sar, prev.high, candles[i - 2].high);
                else sar = Math.max(sar, prev.high);
                if (c.high > sar) {
                    isLong = true;
                    sar = ep;
                    af = step;
                    ep = c.high;
                } else {
                    if (c.low < ep) {
                        ep = c.low;
                        af = Math.min(af + step, maxStep);
                    }
                }
            }
            res.push({ time: c.time, value: Number(sar.toFixed(2)) });
        }
        return res;
    }

    function calcIchimoku(candles, convP = 9, baseP = 26) {
        if (!candles || candles.length < baseP) return { tenkan: [], kijun: [] };
        const tenkan = [], kijun = [];
        for (let i = 0; i < candles.length; i++) {
            const t = candles[i].time;
            if (i >= convP - 1) {
                let h9 = -Infinity, l9 = Infinity;
                for (let j = 0; j < convP; j++) {
                    h9 = Math.max(h9, candles[i - j].high);
                    l9 = Math.min(l9, candles[i - j].low);
                }
                tenkan.push({ time: t, value: Number(((h9 + l9) / 2).toFixed(2)) });
            }
            if (i >= baseP - 1) {
                let h26 = -Infinity, l26 = Infinity;
                for (let j = 0; j < baseP; j++) {
                    h26 = Math.max(h26, candles[i - j].high);
                    l26 = Math.min(l26, candles[i - j].low);
                }
                kijun.push({ time: t, value: Number(((h26 + l26) / 2).toFixed(2)) });
            }
        }
        return { tenkan, kijun };
    }

    function getCdcActionZoneCandles(candles) {
        if (!candles || candles.length === 0) return candles;
        const ema12 = calcEMA(candles, 12);
        const ema26 = calcEMA(candles, 26);
        const e12Map = {};
        for (let i = 0; i < ema12.length; i++) e12Map[ema12[i].time] = ema12[i].value;
        const e26Map = {};
        for (let i = 0; i < ema26.length; i++) e26Map[ema26[i].time] = ema26[i].value;

        return candles.map(c => {
            const e12 = e12Map[c.time];
            const e26 = e26Map[c.time];
            if (e12 === undefined || e26 === undefined) return c;
            const isBull = e12 > e26;
            let col;
            if (isBull) {
                col = (c.close > e12) ? '#22c55e' : '#38bdf8';
            } else {
                col = (c.close > e12) ? '#f59e0b' : '#ef4444';
            }
            return Object.assign({}, c, {
                color: col,
                wickColor: col,
                borderColor: col,
            });
        });
    }

    // Render Single Sub-Pane Chart Component (TradingView Multi-Pane Stacking)
    function renderSingleSubpane(oscKey, container, tData, candles, width, height, isLast) {
        if (currentAggTimeframe !== 'D' && oscKey !== 'rsi') {
            const wrap = document.createElement('div');
            wrap.className = 'rsi-subpane-wrap';
            wrap.id = 'subpane_wrap_' + oscKey;

            const titleMap = {
                sqz: '🎯 Squeeze Momentum [LazyBear]',
            };
            const oscTitle = titleMap[oscKey] || oscKey.toUpperCase();

            wrap.innerHTML = `
                <div class="rsi-pane-header">
                    <span class="rsi-pane-title" style="color:#94a3b8; font-weight:700;">${oscTitle}</span>
                    <button class="subpane-close-btn" onclick="toggleSubpane('${oscKey}')" title="ปิดหน้าต่างนี้ (Close)">✕</button>
                </div>
                <div style="padding: 16px; text-align: center; color: #94a3b8; font-size: 0.82rem; background: #080c16; border-radius: 6px; border: 1px dashed rgba(255,255,255,0.08); margin: 6px 10px 10px;">
                    ⚠️ ใช้ได้เฉพาะกราฟรายวัน
                </div>
            `;
            container.appendChild(wrap);
            return null;
        }

        const wrap = document.createElement('div');
        wrap.className = 'rsi-subpane-wrap';
        wrap.id = 'subpane_wrap_' + oscKey;

        const header = document.createElement('div');
        header.className = 'rsi-pane-header';

        const chartDiv = document.createElement('div');
        chartDiv.id = 'subpane_chart_' + oscKey;
        chartDiv.className = 'rsi-container';

        wrap.appendChild(header);
        wrap.appendChild(chartDiv);
        container.appendChild(wrap);

        const subChart = LightweightCharts.createChart(chartDiv, {
            width: width,
            height: height,
            layout: {
                background: { type: 'solid', color: '#080c16' },
                textColor: '#94a3b8',
                fontFamily: "'Inter', sans-serif",
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.03)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.03)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    color: 'rgba(148, 163, 184, 0.45)',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                    visible: true,
                    labelVisible: true,
                    labelBackgroundColor: '#1e293b',
                },
                horzLine: {
                    color: 'rgba(148, 163, 184, 0.45)',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                    visible: true,
                    labelVisible: true,
                    labelBackgroundColor: '#1e293b',
                },
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                scaleMargins: { top: 0.1, bottom: 0.1 },
                autoScale: true,
                alignLabels: true,
                minimumWidth: 70,
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: false,
                secondsVisible: false,
                visible: isLast,
                rightOffset: 15,
            },
            handleScroll: {
                mouseWheel: true,
                pressedMouseMove: true,
                horzTouchDrag: true,
                vertTouchDrag: false,
            },
            handleScale: {
                mouseWheel: true,
                pinch: true,
                axisPressedMouseMove: true,
                axisDoubleClickReset: true,
            },
        });

        let targetSeries = null;
        let getValue = null;
        let updateHover = null;

        if (oscKey === 'sqz') {
            header.innerHTML = `
                <span class="rsi-pane-title" style="color:#f59e0b; font-weight:700;">🎯 Squeeze Momentum [LazyBear]</span>
                <span class="rsi-ref-label" style="color:#f97316;">🟠 Squeeze ON</span>
                <span class="rsi-ref-label" style="color:#10b981;">🟢 Squeeze FIRED</span>
                <span id="sub_hover_${oscKey}" style="margin-left:6px; font-weight:700; color:#94a3b8;">-</span>
                <button class="subpane-close-btn" onclick="toggleSubpane('${oscKey}')" title="ปิดหน้าต่างนี้ (Close)">✕</button>
            `;
            const sqzHist = (tData.squeeze_momentum && tData.squeeze_momentum.histogram) || [];
            const sqzSeries = subChart.addHistogramSeries({
                priceLineVisible: false,
                lastValueVisible: true,
            });
            sqzSeries.createPriceLine({
                price: 0,
                color: 'rgba(255, 255, 255, 0.25)',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dotted,
            });
            const sqzByTime = new Map(sqzHist.map(h => [h.time, h]));
            sqzSeries.setData(candles.map(c => {
                const entry = sqzByTime.get(c.time);
                return entry ? { time: c.time, value: entry.value, color: entry.color } : { time: c.time, value: 0 };
            }));

            targetSeries = sqzSeries;
            getValue = (timeStr) => {
                const entry = sqzByTime.get(timeStr);
                return entry ? entry.value : 0;
            };

            const valElem = document.getElementById('sub_hover_' + oscKey);
            if (tData.squeeze_momentum && valElem) {
                const m = tData.squeeze_momentum.momentum;
                const statusStr = tData.squeeze_momentum.status;
                const col = m > 0 ? '#10b981' : '#f43f5e';
                valElem.innerHTML = `<span style="color:${col}">${m.toFixed(2)} (${statusStr})</span>`;
            }

            updateHover = (timeStr) => {
                const h = sqzByTime.get(timeStr);
                if (h && valElem) {
                    const col = h.value >= 0 ? '#10b981' : '#f43f5e';
                    valElem.innerHTML = `<span style="color:${col}">M: ${h.value.toFixed(2)}</span>`;
                }
            };
        } else {
            // Default: 'rsi'
            header.innerHTML = `
                <span class="rsi-pane-title" style="color:#c084fc; font-weight:700;">⚡ RSI (14)</span>
                <span class="rsi-ref-label" style="color:#fb7185;">Overbought: 70</span>
                <span class="rsi-ref-label" style="color:#34d399;">Oversold: 30</span>
                <span id="sub_hover_${oscKey}" style="margin-left:6px; font-weight:700; color:#94a3b8;">-</span>
                <button class="subpane-close-btn" onclick="toggleSubpane('${oscKey}')" title="ปิดหน้าต่างนี้ (Close)">✕</button>
            `;
            const rsiSeries = subChart.addLineSeries({
                color: '#c084fc',
                lineWidth: 1.5,
                priceLineVisible: false,
                lastValueVisible: true,
            });
            rsiSeries.createPriceLine({
                price: 70,
                color: 'rgba(251, 113, 133, 0.65)',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: '70',
            });
            rsiSeries.createPriceLine({
                price: 50,
                color: 'rgba(255, 255, 255, 0.18)',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dotted,
                title: '50',
            });
            rsiSeries.createPriceLine({
                price: 30,
                color: 'rgba(52, 211, 153, 0.65)',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: '30',
            });

            const rsiData = calcRSI(candles, 14);
            const rsiByTime = new Map(rsiData.map(r => [r.time, r.value]));
            rsiSeries.setData(candles.map(c => rsiByTime.has(c.time) ? { time: c.time, value: rsiByTime.get(c.time) } : { time: c.time }));

            targetSeries = rsiSeries;
            getValue = (timeStr) => {
                const r = rsiByTime.get(timeStr);
                return r !== undefined ? r : null;
            };

            const valElem = document.getElementById('sub_hover_' + oscKey);
            if (rsiData.length > 0 && valElem) {
                const latestR = rsiData[rsiData.length - 1].value;
                const c = latestR >= 70 ? '#fb7185' : (latestR <= 30 ? '#34d399' : '#f8fafc');
                valElem.innerHTML = `<span style="color:${c}">${latestR.toFixed(1)}</span>`;
            }

            updateHover = (timeStr) => {
                const rVal = rsiByTime.get(timeStr);
                if (rVal !== undefined && valElem) {
                    const c = rVal >= 70 ? '#fb7185' : (rVal <= 30 ? '#34d399' : '#f8fafc');
                    valElem.innerHTML = `<span style="color:${c}">RSI: ${rVal.toFixed(1)}</span>`;
                }
            };
        }

        return { key: oscKey, chart: subChart, series: targetSeries, getValue, updateHover };
    }

    // Render Multi-Pane Charts (Candles + Stacked Oscillators)
    function renderLightweightChart(ticker) {
        const mainContainer = document.getElementById('chart_container');
        const stackContainer = document.getElementById('subpanes_stack');
        if (!mainContainer) return;
        mainContainer.innerHTML = '';
        if (stackContainer) stackContainer.innerHTML = '';

        const tData = CHARTS_DATA[ticker];
        if (!tData || !tData.candles || tData.candles.length === 0) {
            mainContainer.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#94a3b8;font-size:1rem;">ไม่มีข้อมูลแท่งเทียนสำหรับหุ้น ' + ticker + '</div>';
            return;
        }

        if (typeof LightweightCharts === 'undefined') {
            mainContainer.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#94a3b8;">กำลังโหลดไลบรารีกราฟ...</div>';
            return;
        }

        if (activeLwChart) {
            try { activeLwChart.remove(); } catch(e) {}
            activeLwChart = null;
        }
        if (activeSubpaneCharts && activeSubpaneCharts.length > 0) {
            activeSubpaneCharts.forEach(item => {
                try { if (item.chart) item.chart.remove(); } catch(e) {}
            });
        }
        activeSubpaneCharts = [];
        activeRsiChart = null;

        currentCandles = aggregateCandles(tData.candles, currentAggTimeframe);

        const numSubpanes = activeSubpaneOscs.length;
        let mainHeight = 620;
        let subHeight = 130;
        if (numSubpanes === 1) {
            mainHeight = 480;
            subHeight = 140;
        } else if (numSubpanes === 2) {
            mainHeight = 400;
            subHeight = 125;
        } else if (numSubpanes === 3) {
            mainHeight = 350;
            subHeight = 115;
        } else if (numSubpanes >= 4) {
            mainHeight = 300;
            subHeight = 105;
        }
        mainContainer.style.height = mainHeight + 'px';

        // 1. Create Main Candlestick Chart
        const chart = LightweightCharts.createChart(mainContainer, {
            width: mainContainer.clientWidth || 980,
            height: mainHeight,
            layout: {
                background: { type: 'solid', color: '#0a0e1a' },
                textColor: '#94a3b8',
                fontFamily: "'Inter', sans-serif",
            },
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.04)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.04)' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
                vertLine: {
                    color: 'rgba(148, 163, 184, 0.45)',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                    visible: true,
                    labelVisible: true,
                    labelBackgroundColor: '#1e293b',
                },
                horzLine: {
                    color: 'rgba(148, 163, 184, 0.45)',
                    width: 1,
                    style: LightweightCharts.LineStyle.Dashed,
                    visible: true,
                    labelVisible: true,
                    labelBackgroundColor: '#1e293b',
                },
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                scaleMargins: { top: 0.10, bottom: 0.22 },
                autoScale: true,
                alignLabels: true,
                minimumWidth: 70,
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: false,
                secondsVisible: false,
                visible: (numSubpanes === 0),
                rightOffset: 15,
            },
            handleScroll: {
                mouseWheel: true,
                pressedMouseMove: true,
                horzTouchDrag: true,
                vertTouchDrag: false,
            },
            handleScale: {
                mouseWheel: true,
                pinch: true,
                axisPressedMouseMove: true,
                axisDoubleClickReset: true,
            },
        });
        activeLwChart = chart;

        chart.timeScale().subscribeVisibleLogicalRangeChange(() => {
            syncVerticalEarningsPosition();
        });

        // Candlestick Series
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#f43f5e',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#f43f5e',
        });

        const candlesToRender = indicatorVisibility.cdc ? getCdcActionZoneCandles(currentCandles) : currentCandles;
        candleSeries.setData(candlesToRender);
        activeCandleSeries = candleSeries;

        // Volume Histogram Series
        const volData = currentCandles.map(c => ({
            time: c.time,
            value: c.volume,
            color: c.close >= c.open ? 'rgba(16, 185, 129, 0.40)' : 'rgba(244, 63, 94, 0.40)'
        }));
        const volumeSeries = chart.addHistogramSeries({
            priceFormat: { type: 'volume' },
            priceScaleId: '',
        });
        volumeSeries.priceScale().applyOptions({
            scaleMargins: { top: 0.82, bottom: 0 },
        });
        volumeSeries.setData(volData);

        // Core Swing EMAs
        const addEmaSeries = (period, key, color, width) => {
            const data = calcEMA(currentCandles, period);
            chartSeriesRegistry[key] = [];
            if (data.length > 0) {
                const s = chart.addLineSeries({
                    color: color,
                    lineWidth: width,
                    title: 'EMA ' + period,
                    visible: indicatorVisibility[key],
                });
                s.setData(data);
                chartSeriesRegistry[key] = [s];
            }
        };

        addEmaSeries(9, 'ema9', '#fbbf24', 1.5);
        addEmaSeries(21, 'ema21', '#38bdf8', 1.5);
        addEmaSeries(50, 'ema50', '#a78bfa', 2);
        addEmaSeries(200, 'ema200', '#22d3ee', 2);

        // CDC ActionZone Fast EMA 12 & Slow EMA 26 (Calculated strictly from currentCandles)
        chartSeriesRegistry.cdc = [];
        const cdcEma12 = calcEMA(currentCandles, 12);
        const cdcEma26 = calcEMA(currentCandles, 26);
        if (cdcEma12.length > 0) {
            const fEma = chart.addLineSeries({
                color: '#22c55e',
                lineWidth: 1.5,
                title: 'CDC Fast EMA (12)',
                visible: indicatorVisibility.cdc,
            });
            fEma.setData(cdcEma12);
            chartSeriesRegistry.cdc.push(fEma);
        }
        if (cdcEma26.length > 0) {
            const sEma = chart.addLineSeries({
                color: '#ef4444',
                lineWidth: 1.5,
                title: 'CDC Slow EMA (26)',
                visible: indicatorVisibility.cdc,
            });
            sEma.setData(cdcEma26);
            chartSeriesRegistry.cdc.push(sEma);
        }

        const vwapData = calcVWAP(currentCandles, tData.anchor_2y && tData.anchor_2y.time);
        chartSeriesRegistry.vwap = [];
        if (vwapData.length > 0) {
            const s = chart.addLineSeries({
                color: '#eab308',
                lineWidth: 1.5,
                title: (tData.anchor_2y ? 'VWAP (2Y)' : 'Inception VWAP'),
                visible: indicatorVisibility.vwap,
            });
            s.setData(vwapData);
            chartSeriesRegistry.vwap = [s];
        }

        // Bollinger Bands
        const bb = calcBollinger(currentCandles, 20, 2.0);
        chartSeriesRegistry.bb = [];
        if (bb.upper.length > 0) {
            const u = chart.addLineSeries({
                color: 'rgba(6, 182, 212, 0.7)',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: 'BB Upper',
                visible: indicatorVisibility.bb,
            });
            u.setData(bb.upper);
            const m = chart.addLineSeries({
                color: 'rgba(6, 182, 212, 0.4)',
                lineWidth: 1,
                title: 'BB Mid',
                visible: indicatorVisibility.bb,
            });
            m.setData(bb.middle);
            const l = chart.addLineSeries({
                color: 'rgba(6, 182, 212, 0.7)',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: 'BB Lower',
                visible: indicatorVisibility.bb,
            });
            l.setData(bb.lower);
            chartSeriesRegistry.bb = [u, m, l];
        }

        // Supertrend
        chartSeriesRegistry.st = [];
        if (tData.supertrend && tData.supertrend.last_value) {
            const isBull = tData.supertrend.trend === 'BULLISH';
            const stColor = isBull ? '#10b981' : '#f43f5e';
            const stLineData = currentCandles.slice(-80).map(c => ({
                time: c.time,
                value: tData.supertrend.last_value
            }));
            const stSeries = chart.addLineSeries({
                color: stColor,
                lineWidth: 2,
                title: 'Supertrend ' + (isBull ? 'Bull' : 'Bear'),
                visible: indicatorVisibility.st,
            });
            stSeries.setData(stLineData);
            chartSeriesRegistry.st = [stSeries];
        }

        // Parabolic SAR
        const sarData = calcParabolicSAR(currentCandles);
        chartSeriesRegistry.sar = [];
        if (sarData.length > 0) {
            const sarSeries = chart.addLineSeries({
                color: '#ec4899',
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dotted,
                title: 'Parabolic SAR',
                visible: indicatorVisibility.sar,
            });
            sarSeries.setData(sarData);
            chartSeriesRegistry.sar = [sarSeries];
        }

        // Ichimoku Cloud
        const ichiRes = calcIchimoku(currentCandles, 9, 26);
        chartSeriesRegistry.ichi = [];
        if (ichiRes.tenkan.length > 0) {
            const tenkanSeries = chart.addLineSeries({
                color: '#38bdf8',
                lineWidth: 1,
                title: 'Tenkan-sen (9)',
                visible: indicatorVisibility.ichi,
            });
            tenkanSeries.setData(ichiRes.tenkan);
            chartSeriesRegistry.ichi.push(tenkanSeries);
        }
        if (ichiRes.kijun.length > 0) {
            const kijunSeries = chart.addLineSeries({
                color: '#f43f5e',
                lineWidth: 1.5,
                title: 'Kijun-sen (26)',
                visible: indicatorVisibility.ichi,
            });
            kijunSeries.setData(ichiRes.kijun);
            chartSeriesRegistry.ichi.push(kijunSeries);
        }

        const isDailyTf = (currentAggTimeframe === 'D');

        // Chandelier Exit [everget]
        chartSeriesRegistry.chand = [];
        if (isDailyTf && tData.chandelier_exit && tData.chandelier_exit.series) {
            const chList = tData.chandelier_exit.series;
            const chByTime = new Map(chList.map(ch => [ch.time, ch]));
            const isLongCh = tData.chandelier_exit.direction === 'LONG';
            const chSeries = chart.addLineSeries({
                color: isLongCh ? '#10b981' : '#f43f5e',
                lineWidth: 1.5,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                title: 'Chandelier Stop',
                visible: indicatorVisibility.chand,
            });
            chSeries.setData(currentCandles.map(c => {
                const ch = chByTime.get(c.time);
                return { time: c.time, value: ch ? ch.stop : c.close };
            }));
            chartSeriesRegistry.chand = [chSeries];
        }

        // Classical Chart Pattern Lines & Neckline/Target Price Lines (Only drawn when toggled ON!)
        chartSeriesRegistry.pat = [];
        chartSeriesRegistry.patPriceLines = [];
        if (indicatorVisibility.pat) {
            const patRes = drawPatternLines(chart, candleSeries, tData);
            chartSeriesRegistry.pat = patRes.series;
            chartSeriesRegistry.patPriceLines = patRes.priceLines;
        }

        // Synchronized Markers (Swings, AI Decisions, Elliott Wave, etc.)
        updateChartMarkers(candleSeries, ticker);

        // Upcoming Earnings Future Timeline Projection
        updateUpcomingEarnings(ticker);

        // Fibonacci Lines
        chartSeriesRegistry.fiboLines = [];
        if (indicatorVisibility.fibo) {
            chartSeriesRegistry.fiboLines = drawFiboPriceLines(candleSeries, tData, currentFiboMode);
        }

        // Position Levels & Pivot Lines on Chart
        const m = STOCKS_META[ticker] || {};
        const lastP = (currentCandles.length ? currentCandles[currentCandles.length - 1].close : 0);
        if (m.cost && m.cost > 0) {
            const isHolding = Boolean(m.is_holding && m.shares && m.shares > 0);
            candleSeries.createPriceLine({
                price: m.cost,
                color: isHolding ? '#3b82f6' : '#64748b',
                lineWidth: isHolding ? 1.5 : 1,
                lineStyle: isHolding ? LightweightCharts.LineStyle.Dashed : LightweightCharts.LineStyle.Dotted,
                axisLabelVisible: true,
                title: (isHolding ? '💵 ทุนพอร์ต $' : '💵 ทุนเดิม (ขายแล้ว) $') + Number(m.cost).toFixed(2),
            });
        }

        // Pivots & ATR Stop Loss Lines (Only drawn when toggled ON!)
        chartSeriesRegistry.pivotLines = [];
        if (indicatorVisibility.pivots) {
            chartSeriesRegistry.pivotLines = drawPivotPriceLines(candleSeries, tData, m);
        }

        // Smart Money Concepts (SMC) Price Lines (Only drawn when toggled ON!)
        chartSeriesRegistry.smcLines = [];
        if (indicatorVisibility.smc) {
            chartSeriesRegistry.smcLines = drawSmcPriceLines(candleSeries, tData);
        }

        // Elliott Wave Zigzag & Target/Floor Lines (Only drawn when toggled ON!)
        chartSeriesRegistry.ew = [];
        chartSeriesRegistry.ewPriceLines = [];
        if (indicatorVisibility.ew) {
            const ewRes = drawElliottWave(chart, candleSeries, tData);
            chartSeriesRegistry.ew = ewRes.series;
            chartSeriesRegistry.ewPriceLines = ewRes.priceLines;
        }

        // Extended Hours (Pre-market / After-hours) Price Line
        chartSeriesRegistry.extPriceLine = null;
        updateExtPriceLine(candleSeries, ticker);

        // Click on chart sets DCA target price
        chart.subscribeClick(param => {
            if (param && param.point) {
                const clickedPrice = candleSeries.coordinateToPrice(param.point.y);
                if (clickedPrice && clickedPrice > 0) {
                    setDcaTargetPrice(Number(clickedPrice.toFixed(2)));
                }
            }
        });

        // 2. Create Multi-Pane Stacked Sub-Charts
        if (stackContainer) {
            stackContainer.style.display = (numSubpanes > 0) ? 'flex' : 'none';
        }

        if (numSubpanes > 0 && stackContainer) {
            const chartWidth = mainContainer.clientWidth || 980;
            activeSubpaneOscs.forEach((oscKey, idx) => {
                const isLast = (idx === numSubpanes - 1);
                const subObj = renderSingleSubpane(oscKey, stackContainer, tData, currentCandles, chartWidth, subHeight, isLast);
                if (subObj) {
                    activeSubpaneCharts.push(subObj);
                    if (oscKey === 'rsi') {
                        activeRsiChart = subObj.chart;
                    }
                }
            });
        }

        // 3. Bidirectional N-Chart TimeScale & Crosshair Synchronization
        const allCharts = [chart, ...activeSubpaneCharts.map(item => item.chart)];
        let isSyncingTimeScale = false;

        allCharts.forEach(c => {
            c.timeScale().subscribeVisibleLogicalRangeChange(range => {
                if (isSyncingTimeScale || !range) return;
                isSyncingTimeScale = true;
                allCharts.forEach(other => {
                    if (other !== c) {
                        try { other.timeScale().setVisibleLogicalRange(range); } catch(e) {}
                    }
                });
                isSyncingTimeScale = false;
            });
        });

        const candleByTime = new Map((currentCandles || []).map(c => [c.time, c]));
        const candleIndexByTime = new Map((currentCandles || []).map((c, i) => [c.time, i]));

        const updateHoverBar = (tStr, bar) => {
            const dateEl = document.getElementById('chb_date');
            const ohlcEl = document.getElementById('chb_ohlc');
            if (dateEl && tStr) {
                dateEl.textContent = '📅 วันที่: ' + tStr;
            }
            if (ohlcEl && bar && bar.open !== undefined) {
                const isUp = bar.close >= bar.open;
                const cColor = isUp ? '#10b981' : '#f43f5e';
                const idx = candleIndexByTime.get(tStr);
                const prevBar = (idx !== undefined && idx > 0) ? currentCandles[idx - 1] : null;

                // Day change vs previous bar close (standard return base)
                let dayChangeHtml = '';
                if (prevBar && prevBar.close > 0) {
                    const dayDiff = ((bar.close - prevBar.close) / prevBar.close) * 100;
                    const daySign = dayDiff > 0 ? '+' : (dayDiff < 0 ? '-' : '');
                    const dayColor = dayDiff >= 0 ? '#10b981' : '#f43f5e';
                    dayChangeHtml = `<span style="color:${dayColor}; font-weight:700;">(${daySign}${Math.abs(dayDiff).toFixed(2)}% vs วันก่อน)</span>`;
                }

                // Intraday candle change vs bar open
                const intraDiff = bar.open > 0 ? (((bar.close - bar.open) / bar.open) * 100) : 0;
                const intraSign = intraDiff > 0 ? '+' : (intraDiff < 0 ? '-' : '');
                const intraHtml = `<span style="font-size:0.70rem; color:#94a3b8;" title="การเปลี่ยนแปลงภายในแท่ง เทียบราคาเปิด $${Number(bar.open).toFixed(2)}">[แท่ง: ${intraSign}${Math.abs(intraDiff).toFixed(2)}%]</span>`;

                ohlcEl.innerHTML = `O: <b>$${Number(bar.open).toFixed(2)}</b> &nbsp;H: <b>$${Number(bar.high).toFixed(2)}</b> &nbsp;L: <b>$${Number(bar.low).toFixed(2)}</b> &nbsp;C: <b style="color:${cColor};">$${Number(bar.close).toFixed(2)}</b> ${dayChangeHtml} ${intraHtml}`;
            }
        };

        if (currentCandles && currentCandles.length > 0) {
            const lastBar = currentCandles[currentCandles.length - 1];
            updateHoverBar(lastBar.time, lastBar);
        }

        const mainEntry = {
            key: 'main',
            chart: chart,
            series: candleSeries,
            getValue: (tStr) => {
                const c = candleByTime.get(tStr);
                return c ? c.close : null;
            }
        };
        const allEntries = [mainEntry, ...activeSubpaneCharts];
        let isSyncingCrosshair = false;

        allEntries.forEach(source => {
            source.chart.subscribeCrosshairMove(param => {
                if (isSyncingCrosshair) return;
                isSyncingCrosshair = true;
                try {
                    if (!param || !param.time || !param.point) {
                        allEntries.forEach(target => {
                            if (target.chart !== source.chart) {
                                try { target.chart.clearCrosshairPosition(); } catch(e) {}
                            }
                        });
                        if (currentCandles && currentCandles.length > 0) {
                            const lastBar = currentCandles[currentCandles.length - 1];
                            updateHoverBar(lastBar.time, lastBar);
                        }
                        return;
                    }

                    const tStr = (typeof param.time === 'object')
                        ? `${param.time.year}-${String(param.time.month).padStart(2, '0')}-${String(param.time.day).padStart(2, '0')}`
                        : param.time;

                    let bar = null;
                    if (param.seriesData && candleSeries) {
                        bar = param.seriesData.get(candleSeries);
                    }
                    if (!bar && candleByTime) {
                        bar = candleByTime.get(tStr);
                    }
                    updateHoverBar(tStr, bar);

                    activeSubpaneCharts.forEach(item => {
                        if (item.updateHover) item.updateHover(tStr);
                    });

                    // Seamlessly propagate vertical crosshair line & date badge across all charts
                    allEntries.forEach(target => {
                        if (target.chart !== source.chart && target.series) {
                            try {
                                const val = target.getValue ? target.getValue(tStr) : null;
                                if (val !== null && val !== undefined) {
                                    target.chart.setCrosshairPosition(val, param.time, target.series);
                                } else {
                                    target.chart.clearCrosshairPosition();
                                }
                            } catch(e) {}
                        }
                    });
                } finally {
                    isSyncingCrosshair = false;
                }
            });
        });

        // Set Default 1Y View with Right Offset after layout
        requestAnimationFrame(() => {
            setTimeout(() => {
                setTimeframe('1Y');
            }, 60);
        });
    }

    // Responsive Auto-Resize for Main & All Subpane Charts
    window.addEventListener('resize', () => {
        const mainContainer = document.getElementById('chart_container');
        if (activeLwChart && mainContainer) {
            activeLwChart.applyOptions({ width: mainContainer.clientWidth });
        }
        if (activeSubpaneCharts && activeSubpaneCharts.length > 0 && mainContainer) {
            activeSubpaneCharts.forEach(item => {
                if (item.chart) item.chart.applyOptions({ width: mainContainer.clientWidth });
            });
        }
        syncVerticalEarningsPosition();
    });

    // Timeframe Zoom Presets with Right Margin Offset
    function setTimeframe(tf) {
        document.querySelectorAll('.chart-botbar .botbar-btn').forEach(b => {
            if (b.id && b.id.startsWith('tf_')) b.classList.remove('active');
        });
        const activeBtn = document.getElementById('tf_' + tf.toLowerCase());
        if (activeBtn) activeBtn.classList.add('active');

        if (!activeLwChart || !currentCandles || currentCandles.length === 0) return;

        if (tf === 'ALL') {
            try {
                activeLwChart.timeScale().fitContent();
            } catch(e) {}
            return;
        }

        const n = currentCandles.length;
        let barCount = n;

        if (tf === '3M') {
            barCount = currentAggTimeframe === 'W' ? 13 : (currentAggTimeframe === 'M' ? 3 : 63);
        } else if (tf === '6M') {
            barCount = currentAggTimeframe === 'W' ? 26 : (currentAggTimeframe === 'M' ? 6 : 126);
        } else if (tf === '1Y') {
            barCount = currentAggTimeframe === 'W' ? 52 : (currentAggTimeframe === 'M' ? 12 : 252);
        } else if (tf === '5Y') {
            barCount = currentAggTimeframe === 'W' ? 260 : (currentAggTimeframe === 'M' ? 60 : 1260);
        }

        const visibleBars = Math.min(n, Math.max(10, barCount));
        const rightBuffer = (indicatorVisibility.earn && currentEarningsIso) ? 22 : 15;

        try {
            activeLwChart.timeScale().setVisibleLogicalRange({
                from: n - visibleBars,
                to: n + rightBuffer,
            });
            setTimeout(syncVerticalEarningsPosition, 50);
        } catch(e) {}
    }

    // Smart DCA Calculator Functions
    function updateSmartDca(ticker) {
        const meta = STOCKS_META[ticker] || {};
        const tData = CHARTS_DATA[ticker] || {};
        const holdingShares = meta.shares || 0;
        const holdingCost = meta.cost || 0;
        const currentPrice = meta.price || (currentCandles.length ? currentCandles[currentCandles.length - 1].close : 0);

        const posBox = document.getElementById('dca_pos_box');
        if (posBox) {
            if (meta.is_holding && holdingShares > 0) {
                const totalCost = holdingShares * holdingCost;
                const marketVal = holdingShares * currentPrice;
                const pnl = marketVal - totalCost;
                const pnlPct = totalCost > 0 ? (pnl / totalCost) * 100 : 0;
                const pnlColor = pnl >= 0 ? '#34d399' : '#fb7185';
                const pnlSign = pnl >= 0 ? '+' : '';
                posBox.className = 'dca-pos-badge';
                posBox.innerHTML = `
                    <div><b>พอร์ตของคุณ:</b> ถือ ${holdingShares.toFixed(2)} หุ้น @ ทุน ${holdingCost.toFixed(2)}</div>
                    <div style="font-size:0.72rem; color:#94a3b8; margin-top:2px;">
                        มูลค่า $${marketVal.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} • กำไร/ขาดทุน: <b style="color:${pnlColor}">${pnlSign}$${pnl.toFixed(2)} (${pnlSign}${pnlPct.toFixed(1)}%)</b>
                    </div>
                `;
            } else {
                posBox.className = 'dca-pos-badge not-held';
                posBox.innerHTML = `<b>สถานะ:</b> ยังไม่มีหุ้น ${ticker} ในพอร์ต (โหมดคำนวณซื้อไม้ใหม่/จำลองถัว)`;
            }
        }

        const priceInput = document.getElementById('dca_trade_price');
        if (priceInput) {
            priceInput.value = currentPrice > 0 ? currentPrice.toFixed(2) : '';
        }

        recalcDca();
    }

    function setDcaMode(mode) {
        dcaInputMode = mode;
        document.getElementById('dca_mode_usd').classList.toggle('active', mode === 'USD');
        document.getElementById('dca_mode_shares').classList.toggle('active', mode === 'SHARES');
        const input = document.getElementById('dca_amount_input');
        if (input) {
            if (mode === 'USD') {
                input.placeholder = 'จำนวนเงินลงทุน ($)';
                if (parseFloat(input.value) <= 10) input.value = '1000';
            } else {
                input.placeholder = 'จำนวนหุ้นที่จะซื้อ';
                if (parseFloat(input.value) > 100) input.value = '5';
            }
        }
        recalcDca();
    }

    function applyDcaPreset(type) {
        const meta = STOCKS_META[currentStockTicker] || {};
        const tData = CHARTS_DATA[currentStockTicker] || {};
        const currentPrice = meta.price || (currentCandles.length ? currentCandles[currentCandles.length - 1].close : 0);
        let targetPrice = currentPrice;

        if (type === 'curr') {
            targetPrice = currentPrice;
        } else if (type === 's1') {
            targetPrice = meta.support || (tData.pivots ? tData.pivots.s1 : currentPrice * 0.95);
        } else if (type === 's2') {
            targetPrice = (tData.pivots ? tData.pivots.s2 : currentPrice * 0.90);
        }

        setDcaTargetPrice(targetPrice);
    }

    function setDcaTargetPrice(price) {
        const priceInput = document.getElementById('dca_trade_price');
        if (priceInput && price > 0) {
            priceInput.value = price.toFixed(2);
            recalcDca();
        }
    }

    function recalcDca() {
        const meta = STOCKS_META[currentStockTicker] || {};
        const currentPrice = meta.price || (currentCandles.length ? currentCandles[currentCandles.length - 1].close : 0);
        const holdingShares = meta.shares || 0;
        const holdingCost = meta.cost || 0;

        const tradePrice = parseFloat(document.getElementById('dca_trade_price').value) || currentPrice;
        const amountVal = parseFloat(document.getElementById('dca_amount_input').value) || 0;

        let addShares = 0;
        let addCost = 0;

        if (dcaInputMode === 'USD') {
            addCost = amountVal;
            addShares = tradePrice > 0 ? addCost / tradePrice : 0;
        } else {
            addShares = amountVal;
            addCost = addShares * tradePrice;
        }

        const totalShares = holdingShares + addShares;
        const totalInvested = (holdingShares * holdingCost) + addCost;
        const newAvg = totalShares > 0 ? totalInvested / totalShares : 0;

        const breakevenDist = currentPrice > 0 ? ((newAvg - currentPrice) / currentPrice) * 100 : 0;

        document.getElementById('dca_res_add_shares').textContent = addShares.toFixed(2) + ' หุ้น';
        document.getElementById('dca_res_add_cost').textContent = '$' + addCost.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById('dca_res_new_avg').textContent = '$' + newAvg.toFixed(2);

        const beElem = document.getElementById('dca_res_breakeven');
        if (beElem) {
            if (holdingShares === 0) {
                beElem.innerHTML = `<span style="color:#94a3b8;">เป็นราคาซื้อไม้แรก ($${tradePrice.toFixed(2)})</span>`;
            } else if (breakevenDist <= 0) {
                beElem.innerHTML = `<span style="color:#34d399; font-weight:700;">กำไรทันที +${Math.abs(breakevenDist).toFixed(1)}% จากราคาปัจจุบัน</span>`;
            } else {
                beElem.innerHTML = `<span style="color:#fb7185; font-weight:700;">ต้องการอีก +${breakevenDist.toFixed(1)}% เพื่อคืนทุน</span>`;
            }
        }
    }

    // AI Narrative Assistant Readout
    function updateAiNarrative(ticker) {
        const meta = STOCKS_META[ticker] || {};
        const tData = CHARTS_DATA[ticker] || {};
        const price = meta.price || (currentCandles.length ? currentCandles[currentCandles.length - 1].close : 0);
        const s1 = meta.support || (tData.pivots ? tData.pivots.s1 : 0);
        const s2 = tData.pivots ? tData.pivots.s2 : (s1 * 0.92);
        const r1 = meta.resistance || (tData.pivots ? tData.pivots.r1 : 0);
        const r2 = tData.pivots ? tData.pivots.r2 : (r1 * 1.08);
        const rsi = (tData.latest_rsi !== null && tData.latest_rsi !== undefined) ? Number(tData.latest_rsi) : 50;

        const badgeContainer = document.getElementById('ai_narrative_badge_container');
        const textElem = document.getElementById('ai_narrative_text');
        if (!textElem) return;

        let badgeHtml = '';
        let story = '';

        if (price > 0 && s1 > 0) {
            const diffS1 = ((price - s1) / s1) * 100;
            const diffR1 = r1 > 0 ? ((r1 - price) / price) * 100 : 0;

            if (price < s1) {
                badgeHtml = `<span class="ai-narrative-tag caution">🔴 หลุดแนวรับหลัก</span>`;
                story = `<b>${ticker}</b> ราคาปัจจุบัน <b>$${price.toFixed(2)}</b> หลุดแนวรับหลัก <b>$${s1.toFixed(2)}</b> ลงมาแล้ว ${Math.abs(diffS1).toFixed(1)}%. `;
                if (s2 > 0) {
                    const diffS2 = ((price - s2) / price) * 100;
                    story += `แนวรับถัดไป $${s2.toFixed(2)} อยู่ต่ำลงไปอีก ${diffS2.toFixed(1)}%. `;
                }
                story += `ต้องรอให้ราคากลับขึ้นมายืนเหนือ $${s1.toFixed(2)} ก่อนทรงขาขึ้นเดิมจึงจะกลับมา. `;
            } else {
                if (diffS1 <= 3.5) {
                    badgeHtml = `<span class="ai-narrative-tag buy">🟢 ใกล้แนวรับ (น่าสะสม)</span>`;
                    story = `<b>${ticker}</b> อยู่ใกล้โซนแนวรับหลัก <b>$${s1.toFixed(2)}</b> เพียง ${diffS1.toFixed(1)}% เป็นโซนความเสี่ยงต่ำและ Risk/Reward สวยงาม. `;
                } else if (diffR1 > 0) {
                    badgeHtml = `<span class="ai-narrative-tag watch">🟡 ทรงแข็งแรง (เหนือแนวรับ)</span>`;
                    story = `<b>${ticker}</b> วิ่งอยู่เหนือแนวรับ <b>$${s1.toFixed(2)}</b> ราว ${diffS1.toFixed(1)}% และมีระยะวิ่งไปชนแนวต้าน <b>$${r1.toFixed(2)}</b> อีก ${diffR1.toFixed(1)}%. `;
                } else {
                    badgeHtml = `<span class="ai-narrative-tag buy">↗ ทะลุแนวต้าน (Breakout)</span>`;
                    story = `<b>${ticker}</b> เบรกเอาท์ทะลุแนวต้าน <b>$${r1.toFixed(2)}</b> สำเร็จ โมเมนตัมฝั่งซื้อควบคุมตลาด. `;
                }
            }

            // RSI Momentum Addition
            if (rsi >= 70) {
                story += `ด้านโมเมนตัม RSI อยู่ที่ <b>${rsi.toFixed(1)}</b> เข้าเขตซื้อมากเกินไป (Overbought) ควรระวังแรงขายทำกำไรระยะสั้น.`;
            } else if (rsi <= 30) {
                story += `ด้านโมเมนตัม RSI อยู่ที่ <b>${rsi.toFixed(1)}</b> เข้าเขตขายมากเกินไป (Oversold) มีโอกาสเด้งตัวทางเทคนิค (Technical Rebound) สูง.`;
            } else {
                story += `RSI อยู่ที่ <b>${rsi.toFixed(1)}</b> อยู่ในเกณฑ์สมดุล ไม่ร้อนแรง.`;
            }
        } else {
            badgeHtml = `<span class="ai-narrative-tag watch">⚖️ กำลังประมวลผล</span>`;
            story = `กำลังตรวจสอบข้อมูลราคาและแนวรับแนวต้านของ ${ticker}...`;
        }

        if (badgeContainer) badgeContainer.innerHTML = badgeHtml;
        textElem.innerHTML = story;
    }

    // Key Levels Radar
    function updateKeyLevelsRadar(ticker) {
        const meta = STOCKS_META[ticker] || {};
        const tData = CHARTS_DATA[ticker] || {};
        const lastBar = (currentCandles && currentCandles.length > 0) ? currentCandles[currentCandles.length - 1] : (tData.candles && tData.candles.length ? tData.candles[tData.candles.length - 1] : null);
        const candleClose = lastBar ? lastBar.close : (meta.price || 0);
        const livePrice = meta.price || candleClose;
        const fmt = (v) => (v && v > 0) ? '$' + Number(v).toFixed(2) : '-';

        const p = tData.pivots;
        const hasPivots = p && (p.r1 || p.r2 || p.s1 || p.s2);

        let r2 = 0, r1 = 0, s1 = 0, s2 = 0, sourceLabel = 'Pivot รายเดือน';
        if (hasPivots) {
            r2 = p.r2 || 0;
            r1 = p.r1 || 0;
            s1 = p.s1 || 0;
            s2 = p.s2 || 0;
            sourceLabel = 'Pivot รายเดือน';
        } else {
            r1 = meta.resistance || 0;
            r2 = meta.resistance2 || (r1 > 0 ? r1 * 1.05 : 0);
            s1 = meta.support || 0;
            s2 = meta.support2 || (s1 > 0 ? s1 * 0.95 : 0);
            sourceLabel = 'แนวรับต้านจาก swing';
        }

        const klBadge = document.getElementById('kl_source_badge');
        if (klBadge) klBadge.textContent = sourceLabel;

        const latestSig = (tData.ai_signals && tData.ai_signals.length) ? tData.ai_signals[tData.ai_signals.length - 1] : null;
        const isInformational = Boolean(latestSig && latestSig.levels_informational);

        // R2 row
        const r2NameElem = document.getElementById('kl_r2_name');
        const r2ValElem = document.getElementById('kl_r2');
        if (r2ValElem) {
            r2ValElem.textContent = fmt(r2);
            const isBroken = r2 > 0 && candleClose > r2;
            if (isBroken) {
                r2ValElem.style.color = '#94a3b8';
                r2ValElem.style.opacity = '0.7';
                if (r2NameElem) r2NameElem.innerHTML = `🔴 แนวต้าน 2 (R2) (${sourceLabel}) <span style="font-size:0.68rem; color:#94a3b8; background:rgba(148,163,184,0.18); padding:1px 5px; border-radius:3px; margin-left:4px;">ทะลุแล้ว</span>`;
            } else {
                r2ValElem.style.color = '#fb7185';
                r2ValElem.style.opacity = '1';
                if (r2NameElem) r2NameElem.textContent = `🔴 แนวต้าน 2 (R2) (${sourceLabel})`;
            }
        }

        // R1 row
        const r1NameElem = document.getElementById('kl_r1_name');
        const r1ValElem = document.getElementById('kl_r1');
        if (r1ValElem) {
            r1ValElem.textContent = fmt(r1);
            const isBroken = r1 > 0 && candleClose > r1;
            if (isBroken) {
                r1ValElem.style.color = '#94a3b8';
                r1ValElem.style.opacity = '0.7';
                if (r1NameElem) r1NameElem.innerHTML = `🔴 แนวต้าน 1 (R1) (${sourceLabel}) <span style="font-size:0.68rem; color:#94a3b8; background:rgba(148,163,184,0.18); padding:1px 5px; border-radius:3px; margin-left:4px;">ทะลุแล้ว</span>`;
            } else {
                r1ValElem.style.color = '#fb7185';
                r1ValElem.style.opacity = '1';
                if (r1NameElem) r1NameElem.textContent = `🔴 แนวต้าน 1 (R1) (${sourceLabel})`;
            }
        }

        const klCurrent = document.getElementById('kl_current');
        if (klCurrent) {
            if (meta.price && Math.abs(meta.price - candleClose) > 0.001) {
                klCurrent.innerHTML = fmt(candleClose) + ` <span style="font-size:0.72rem; color:#94a3b8; font-weight:normal;" title="ราคาสด: ${fmt(livePrice)}">(สด ${fmt(livePrice)})</span>`;
            } else {
                klCurrent.textContent = fmt(candleClose);
            }
        }

        // S1 row
        const s1NameElem = document.getElementById('kl_s1_name');
        const s1ValElem = document.getElementById('kl_s1');
        if (s1ValElem) {
            s1ValElem.textContent = fmt(s1);
            const isBroken = s1 > 0 && candleClose < s1;
            if (isBroken) {
                s1ValElem.style.color = '#94a3b8';
                s1ValElem.style.opacity = '0.7';
                if (s1NameElem) s1NameElem.innerHTML = `🟢 แนวรับ 1 (S1) (${sourceLabel}) <span style="font-size:0.68rem; color:#f43f5e; background:rgba(244,63,94,0.18); padding:1px 5px; border-radius:3px; margin-left:4px;">หลุดแล้ว</span>`;
            } else {
                s1ValElem.style.color = '#34d399';
                s1ValElem.style.opacity = '1';
                if (s1NameElem) s1NameElem.textContent = `🟢 แนวรับ 1 (S1) (${sourceLabel})`;
            }
        }

        // S2 row
        const s2NameElem = document.getElementById('kl_s2_name');
        const s2ValElem = document.getElementById('kl_s2');
        if (s2ValElem) {
            s2ValElem.textContent = fmt(s2);
            const isBroken = s2 > 0 && candleClose < s2;
            if (isBroken) {
                s2ValElem.style.color = '#94a3b8';
                s2ValElem.style.opacity = '0.7';
                if (s2NameElem) s2NameElem.innerHTML = `🛡️ แนวรับ 2 (S2) (${sourceLabel}) <span style="font-size:0.68rem; color:#f43f5e; background:rgba(244,63,94,0.18); padding:1px 5px; border-radius:3px; margin-left:4px;">หลุดแล้ว</span>`;
            } else {
                s2ValElem.style.color = '#34d399';
                s2ValElem.style.opacity = '1';
                if (s2NameElem) s2NameElem.textContent = `🛡️ แนวรับ 2 (S2) (${sourceLabel})`;
            }
        }

        // SL: prioritize ai_signals/Python, fallback to meta.sl or ATR
        const slVal = (latestSig && latestSig.stop_loss) ? latestSig.stop_loss : (meta.sl || (tData.atr14 ? (candleClose - 1.5 * tData.atr14.value) : 0));
        const slNameElem = document.getElementById('kl_sl_name');
        const slValElem = document.getElementById('kl_sl');
        if (slValElem) {
            slValElem.textContent = fmt(slVal);
            if (isInformational) {
                slValElem.style.color = '#94a3b8';
                if (slNameElem) slNameElem.innerHTML = `🛑 Stop Loss <span style="font-size:0.68rem; color:#94a3b8; background:rgba(148,163,184,0.18); padding:1px 5px; border-radius:3px; margin-left:4px;">ข้อมูลอ้างอิง</span>`;
            } else {
                slValElem.style.color = '#f43f5e';
                if (slNameElem) slNameElem.textContent = `🛑 Stop Loss (1.5 ATR)`;
            }
        }
    }

    // Earnings Radar Update
    function updateEarningsRadar(ticker) {
        const meta = STOCKS_META[ticker] || {};
        const tData = CHARTS_DATA[ticker] || {};
        const latestSig = (tData.ai_signals && tData.ai_signals.length) ? tData.ai_signals[tData.ai_signals.length - 1] : null;
        const guardThresh = (latestSig && latestSig.guard_days_threshold) || (meta.score && meta.score.guard_days_threshold) || meta.earnings_guard_days || null;
        const radarBody = document.getElementById('earn_radar_body');
        const radarCard = document.getElementById('earn_radar_card');
        const dEarn = meta.days_to_earnings;
        const dDate = escapeHtml(meta.earnings_date || '-');
        const roundedDays = getDaysToEarningsDisplay(dEarn);

        if (!radarBody) return;

        if (roundedDays !== null && roundedDays >= 0) {
            const isShockZone = guardThresh != null ? (roundedDays <= guardThresh) : Boolean(meta.earnings_guard_active || (latestSig && latestSig.earnings_guard) || (meta.score && meta.score.earnings_guard));
            if (isShockZone) {
                const zoneHint = guardThresh != null ? ` ภายใน ${guardThresh} วัน` : '';
                const earnText = roundedDays === 0 ? 'งบออกวันนี้' : `งบออกใน ${roundedDays} วัน`;
                radarBody.innerHTML = `
                    <div style="color: #fb7185; font-weight: 700; font-size: 0.88rem; margin-bottom: 4px;">⚠️ ${earnText} (${dDate})</div>
                    <div>ความผันผวนสูง (Earnings Shock Zone${zoneHint}) แนะนำหลีกเลี่ยงการเปิดสถานะใหม่ขนาดใหญ่ก่อนงบออก</div>
                `;
                if (radarCard) {
                    radarCard.style.borderColor = 'rgba(244, 63, 94, 0.4)';
                    radarCard.style.background = 'rgba(244, 63, 94, 0.08)';
                }
            } else if (roundedDays <= 30) {
                radarBody.innerHTML = `
                    <div style="color: #facc15; font-weight: 700; font-size: 0.88rem; margin-bottom: 4px;">🟡 งบออกใน ${roundedDays} วัน (${dDate})</div>
                    <div>เข้าใกล้ฤดูกาลประกาศผลประกอบการ ควรวางกรอบ Stop Loss ให้รัดกุม</div>
                `;
                if (radarCard) {
                    radarCard.style.borderColor = 'rgba(250, 204, 21, 0.3)';
                    radarCard.style.background = 'rgba(250, 204, 21, 0.04)';
                }
            } else {
                radarBody.innerHTML = `
                    <div style="color: #cbd5e1; font-weight: 700; margin-bottom: 4px;">🗓️ วันประกาศงบ: ${dDate} (ใน ${roundedDays} วัน)</div>
                    <div>ยังไม่อยู่ในโซนความผันผวนของงบการเงิน สามารถใช้สัญญาณเทคนิคอลนำการตัดสินใจได้เต็มที่</div>
                `;
                if (radarCard) {
                    radarCard.style.borderColor = 'var(--border-color)';
                    radarCard.style.background = 'var(--bg-card)';
                }
            }
        } else {
            radarBody.innerHTML = `
                <div style="color: #94a3b8;">ไม่พบข้อมูลรอบประกาศงบการเงินที่ใกล้จะถึงสำหรับ ${ticker}</div>
            `;
            if (radarCard) {
                radarCard.style.borderColor = 'var(--border-color)';
                radarCard.style.background = 'var(--bg-card)';
            }
        }
    }

    // Select Stock
    function selectStock(ticker) {
        currentStockTicker = ticker;
        const m = STOCKS_META[ticker] || {};
        const tData = CHARTS_DATA[ticker] || {};

        currentStockExchange = m.exchange || 'NASDAQ';

        // Update active pill
        document.querySelectorAll('.sp-pill').forEach(p => p.classList.remove('active'));
        const activePill = document.getElementById('pill_' + ticker);
        if (activePill) {
            activePill.classList.add('active');
            activePill.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        if (window.innerWidth <= 1100 && typeof toggleStockSidebar === 'function') {
            toggleStockSidebar(false);
        }

        // Update Page Title & URL hash
        document.title = `${ticker} • Technical Chart & Rule-based Confluence`;
        history.replaceState(null, '', `stock_chart.html?ticker=${ticker}#${ticker}`);

        // Update Header
        document.getElementById('st_ticker_pill').textContent = ticker;
        document.getElementById('st_name').textContent = m.name || ticker;
        document.getElementById('st_sector_exchange').textContent = (m.sector ? m.sector + ' • ' : '') + currentStockExchange;
        const staleBadge = document.getElementById('st_stale_badge');
        if (staleBadge) {
            staleBadge.style.display = tData.stale ? 'inline-block' : 'none';
            if (tData.stale && tData.timestamp) {
                staleBadge.title = 'ดึงข้อมูลล่าสุดไม่สำเร็จ ข้อมูลนี้อัปเดตเมื่อ ' + new Date(tData.timestamp * 1000).toLocaleString('th-TH');
            }
        }

        const extChipReset = document.getElementById('st_head_ext');
        if (extChipReset) extChipReset.style.display = 'none';
        const extCardReset = document.getElementById('hud_ext_card');
        if (extCardReset) extCardReset.style.display = 'none';

        const lastBar = (tData.candles && tData.candles.length) ? tData.candles[tData.candles.length - 1] : null;
        const candleClose = lastBar ? lastBar.close : (m.price || 0);
        const lastPrice = m.price || candleClose;
        const headPriceElem = document.getElementById('st_head_price');
        if (headPriceElem) headPriceElem.textContent = '$' + Number(lastPrice).toFixed(2);

        // Header Change %
        const headChangeElem = document.getElementById('st_head_change');
        if (headChangeElem && tData.candles && tData.candles.length >= 2) {
            const cLen = tData.candles.length;
            const prevClose = tData.candles[cLen - 2].close;
            const diffPct = prevClose > 0 ? ((lastPrice - prevClose) / prevClose) * 100 : 0;
            const isUp = diffPct >= 0;
            const chgSign = diffPct > 0 ? '+' : (diffPct < 0 ? '-' : '');
            headChangeElem.className = 'header-change-chip ' + (isUp ? 'up' : 'down');
            headChangeElem.textContent = (isUp ? '▲ ' : '▼ ') + (chgSign ? chgSign : '') + Math.abs(diffPct).toFixed(2) + '%';
            headChangeElem.title = `เทียบราคาปิดวันก่อนหน้า $${Number(prevClose).toFixed(2)} (vs Previous Close)`;
        }

        const sym = (currentStockExchange && currentStockExchange !== 'US') ? (currentStockExchange + ':' + ticker) : ticker;
        document.getElementById('st_ext_link').href = 'https://www.tradingview.com/chart/?symbol=' + sym;

        // Update HUD Strip with Technical Fallbacks
        const fmt = (v) => (v && v > 0) ? '$' + Number(v).toFixed(2) : '-';
        const isHolding = Boolean(m.is_holding && m.shares && m.shares > 0);
        const hudCostElem = document.getElementById('hud_cost');
        if (hudCostElem) {
            if (m.cost && m.cost > 0 && !isHolding) {
                hudCostElem.innerHTML = fmt(m.cost) + ` <span style="font-size:0.65rem; color:#94a3b8; font-weight:normal;">(ขายแล้ว)</span>`;
            } else {
                hudCostElem.textContent = fmt(m.cost);
            }
        }

        const hudPriceLabel = document.getElementById('hud_price_label');
        const hudPrice = document.getElementById('hud_price');
        if (m.price && Math.abs(m.price - candleClose) > 0.001) {
            if (hudPriceLabel) hudPriceLabel.textContent = '⚡ ราคาสด';
            if (hudPrice) hudPrice.innerHTML = fmt(m.price) + ` <div style="font-size:0.68rem; color:#94a3b8; font-weight:normal;" title="ราคาปิดแท่งล่าสุด: ${fmt(candleClose)}">ปิดแท่ง: ${fmt(candleClose)}</div>`;
        } else {
            if (hudPriceLabel) hudPriceLabel.textContent = '⚡ ราคาปิดแท่งล่าสุด';
            if (hudPrice) hudPrice.textContent = fmt(lastPrice);
        }

        // Technical fallback cascade
        const fibo618 = (tData.fibonacci && tData.fibonacci['61.8%']) ? tData.fibonacci['61.8%'].price : 0;
        let supVal = 0, supSource = 'swing';
        if (m.support) {
            supVal = m.support;
            supSource = 'swing';
        } else if (tData.pivots && tData.pivots.s1) {
            supVal = tData.pivots.s1;
            supSource = 'Pivot';
        } else {
            supVal = fibo618;
            supSource = 'Fibo';
        }
        document.getElementById('hud_support').textContent = fmt(supVal);
        const hudSupLabel = document.getElementById('hud_support_label');
        if (hudSupLabel) hudSupLabel.textContent = `🟢 แนวรับสำคัญ (S1) (${supSource})`;

        const fibo236 = (tData.fibonacci && tData.fibonacci['23.6%']) ? tData.fibonacci['23.6%'].price : 0;
        let resVal = 0, resSource = 'swing';
        if (m.resistance) {
            resVal = m.resistance;
            resSource = 'swing';
        } else if (tData.pivots && tData.pivots.r1) {
            resVal = tData.pivots.r1;
            resSource = 'Pivot';
        } else {
            resVal = fibo236;
            resSource = 'Fibo';
        }
        document.getElementById('hud_resistance').textContent = fmt(resVal);
        const hudResLabel = document.getElementById('hud_resistance_label');
        if (hudResLabel) hudResLabel.textContent = `🔴 แนวต้านสำคัญ (R1) (${resSource})`;

        const latestSig = (tData.ai_signals && tData.ai_signals.length) ? tData.ai_signals[tData.ai_signals.length - 1] : null;
        const hudSlVal = (latestSig && latestSig.stop_loss) ? latestSig.stop_loss : (m.sl || (tData.atr14 ? (lastPrice - 1.5 * tData.atr14.value) : (tData.pivots ? tData.pivots.s2 : 0)));
        const hudSlElem = document.getElementById('hud_sl');
        hudSlElem.textContent = fmt(hudSlVal);

        const ewTarget = (tData.elliott_wave && tData.elliott_wave.target) ? tData.elliott_wave.target : 0;
        const tpVal = (latestSig && latestSig.target) ? latestSig.target : (m.tp || (tData.pivots ? tData.pivots.r2 : 0) || ewTarget || (lastPrice > 0 ? (lastPrice * 1.08) : 0));
        const hudTpElem = document.getElementById('hud_tp');
        hudTpElem.textContent = fmt(tpVal);

        if (latestSig && latestSig.levels_informational) {
            hudSlElem.style.color = '#94a3b8';
            hudSlElem.title = 'ข้อมูลอ้างอิง';
            hudTpElem.style.color = '#94a3b8';
            hudTpElem.title = 'ข้อมูลอ้างอิง';
        } else {
            hudSlElem.style.color = '#f43f5e';
            hudSlElem.title = '';
            hudTpElem.style.color = '#10b981';
            hudTpElem.title = '';
        }

        const targetVal = m.target || (tData.pivots ? tData.pivots.r1 : 0) || ewTarget;
        document.getElementById('hud_target').textContent = fmt(targetVal);

        if (tData.atr14) {
            document.getElementById('hud_atr').innerHTML = '$' + Number(tData.atr14.value).toFixed(2) + ' <span style="font-size:0.70rem; color:#94a3b8; font-weight:600;">(' + Number(tData.atr14.pct).toFixed(1) + '%)</span>';
        } else {
            document.getElementById('hud_atr').textContent = '-';
        }

        if (tData.vol_surge) {
            const r = tData.vol_surge.ratio;
            document.getElementById('hud_vol').innerHTML = r.toFixed(2) + 'x <span style="font-size:0.75rem;">' + (r >= 1.5 ? '🔥' : (r <= 0.7 ? '💤' : '⚖️')) + '</span>';
            document.getElementById('hud_vol').style.color = r >= 1.5 ? '#34d399' : (r <= 0.7 ? '#94a3b8' : '#f8fafc');
        } else {
            document.getElementById('hud_vol').textContent = '-';
        }

        const earnVal = document.getElementById('hud_earnings');
        const dEarn = m.days_to_earnings;
        const dDate = m.earnings_date || '-';
        if (earnVal) {
            const roundedDays = getDaysToEarningsDisplay(dEarn);
            const earnThresh = (latestSig && latestSig.guard_days_threshold) || (m.score && m.score.guard_days_threshold) || m.earnings_guard_days || null;
            if (roundedDays !== null && roundedDays >= 0) {
                const shortDate = escapeHtml(String(dDate).replace(/\s+202\d$/, ''));
                const isNearGuard = earnThresh != null ? (roundedDays <= earnThresh) : Boolean(latestSig && latestSig.earnings_guard);
                earnVal.innerHTML = `<span style="color:${isNearGuard ? '#fb7185' : '#facc15'};">ใน ${roundedDays} วัน</span> <span style="font-size:0.70rem; color:#94a3b8; font-weight:600;">(${shortDate})</span>`;
            } else {
                earnVal.textContent = dDate;
            }
        }

        // Update Fibo Chips
        updateFiboChips(tData);

        // Update Sidebar Widgets
        currentCandles = aggregateCandles(tData.candles || [], currentAggTimeframe);
        updateSmartDca(ticker);
        updateAiNarrative(ticker);
        updateKeyLevelsRadar(ticker);
        updateEarningsRadar(ticker);
        updateElliottWaveSidebar(ticker);
        updateScoreSidebar(ticker);
        updateSmcSidebar(ticker);
        updateOscillatorsSidebar(ticker);
        updateMlSidebar(ticker);
        updateWhalesSidebar(ticker);
        updateNewsSidebar(ticker);

        // Render AI Decision Engine & Pattern Breakdown
        renderAiDecisionSection(tData);
        renderPatternDeepDive(tData);

        // Render Financial Statements & Quarterly Trends
        updateFinancialsSection(ticker);

        // Render Chart
        if (currentChartMode === 'tech') {
            renderLightweightChart(ticker);
        } else {
            renderTradingViewWidget(ticker);
        }

        if (typeof latestLiveQuotesMap !== 'undefined' && latestLiveQuotesMap[ticker]) {
            handleLiveQuotesBroadcast({ quotes: { [ticker]: latestLiveQuotesMap[ticker] } });
        }
    }

    function getSignalBadgeText(sig, isGuard, guardDays) {
        if (isGuard) {
            const guardText = guardDays === 0 ? 'งบออกวันนี้' : (guardDays != null ? 'งบออกใน ' + guardDays + ' วัน' : 'ใกล้วันประกาศงบ');
            return `พักสัญญาณ (${guardText})`;
        }
        if (!sig) return '-';
        let type = (sig.type || '').toUpperCase();
        if (!type && sig.action) {
            const act = (sig.action || '').toUpperCase();
            if (act === 'ENTRY' || act === 'BUY' || act.includes('STRONG')) type = 'RULE_ENTRY';
            else if (act === 'DCA') type = 'RULE_DCA';
            else if (act === 'SELL' || act === 'TRIM' || act === 'TP') type = 'RULE_TP';
            else if (act.includes('พักสัญญาณ') || sig.earnings_guard) type = 'EARNINGS_GUARD';
            else if (act.includes('เลี่ยง') || act === 'AVOID') type = 'AVOID';
            else if (act.includes('รอ') || act === 'WAIT' || act === 'HOLD') type = 'WAIT';
        }
        if ((type.includes('STRONG') && type.includes('BUY')) || type === 'BUY') type = 'RULE_ENTRY';
        else if (type === 'DCA') type = 'RULE_DCA';
        else if (type === 'SELL') type = 'RULE_TP';

        if (type === 'ENTRY') return 'เข้าเงื่อนไขจุดเข้า';
        if (type === 'RULE_ENTRY') return 'จุดเข้าตามกฎ';
        if (type === 'RULE_DCA') return 'จุดสะสม DCA';
        if (type === 'RULE_TP') return 'จุดทำกำไร';
        if (type === 'TRIM') return 'แบ่งทำกำไร / รอ';
        if (type === 'AVOID') return 'เลี่ยง';
        if (type === 'HOLD') return 'รอจังหวะ';
        if (type === 'WAIT') return 'รอ';
        if (type === 'EARNINGS_GUARD') {
            const guardText = guardDays === 0 ? 'งบออกวันนี้' : (guardDays != null ? 'งบออกใน ' + guardDays + ' วัน' : 'ใกล้วันประกาศงบ');
            return `พักสัญญาณ (${guardText})`;
        }
        if (sig.badge && !sig.badge.includes('BUY')) {
            return String(sig.badge).replace(/🚀\s*/g, '').replace(/[\u{1F916}]\s*/gu, '');
        }
        return 'สัญญาณทางเทคนิค';
    }

    // AI Decision Cards
    function renderAiDecisionSection(tData) {
        const chipsContainer = document.getElementById('signal_chips');
        const decisionCard = document.getElementById('decision_card');
        if (!chipsContainer || !decisionCard) return;

        chipsContainer.innerHTML = '';
        const signals = tData.ai_signals || [];

        if (signals.length === 0) {
            chipsContainer.innerHTML = '<span style="font-size:0.80rem; color:#94a3b8;">ไม่มีสัญญาณตัดสินใจบันทึกไว้สำหรับหุ้นตัวนี้</span>';
            decisionCard.innerHTML = '<div style="color:#94a3b8; font-size:0.85rem; text-align:center; padding:18px;">ระบบยังไม่พบสัญญาณการเข้าทำกำไรหรือจุดสะสม DCA ในแท่งเทียนล่าสุด</div>';
            return;
        }

        const meta = STOCKS_META[currentStockTicker] || {};
        const unified = meta.score;
        const dEarn = meta.days_to_earnings;
        const daysToEarn = getDaysToEarningsDisplay(dEarn);
        const threshold = (signals.length && signals[signals.length - 1].guard_days_threshold) || (unified && unified.guard_days_threshold) || null;

        signals.forEach((sig, idx) => {
            const isLast = idx === signals.length - 1;
            const sigThresh = sig.guard_days_threshold || threshold;
            const isSigGuard = Boolean(
                sig.earnings_guard ||
                sig.guard_active ||
                sig.type === 'EARNINGS_GUARD' ||
                sig.action === 'PAUSE' ||
                (sig.badge && sig.badge.includes('พักสัญญาณ')) ||
                (isLast && ((unified && unified.earnings_guard) || (daysToEarn !== null && daysToEarn >= 0 && sigThresh && daysToEarn <= sigThresh)))
            );
            const guardDays = (daysToEarn !== null && daysToEarn >= 0) ? daysToEarn : (sig.guard_days || null);
            const chipBadge = getSignalBadgeText(sig, isSigGuard, guardDays);

            const btn = document.createElement('button');
            btn.className = 'tv-sig-chip' + (isLast ? ' active' : '');
            btn.id = 'chip_sig_' + sig.time;
            btn.innerHTML = `<span>${sig.time}</span> <span>${chipBadge}</span>`;
            btn.onclick = () => showDecisionDetail(sig);
            chipsContainer.appendChild(btn);
        });

        showDecisionDetail(signals[signals.length - 1]);
    }

    function showDecisionDetail(sig) {
        document.querySelectorAll('.tv-sig-chip').forEach(c => c.classList.remove('active'));
        const chip = document.getElementById('chip_sig_' + sig.time);
        if (chip) chip.classList.add('active');

        const card = document.getElementById('decision_card');
        if (!card) return;

        const meta = STOCKS_META[currentStockTicker] || {};
        const unified = meta.score;
        const sigs = (CHARTS_DATA[currentStockTicker] || {}).ai_signals || [];
        const isLatest = sigs.length && sigs[sigs.length - 1].time === sig.time;
        const dEarn = meta.days_to_earnings;
        const daysToEarn = getDaysToEarningsDisplay(dEarn);
        const sigThresh = sig.guard_days_threshold || (sigs.length && sigs[sigs.length - 1].guard_days_threshold) || (unified && unified.guard_days_threshold) || null;
        const isGuardActive = Boolean(
            sig.earnings_guard ||
            sig.guard_active ||
            sig.type === 'EARNINGS_GUARD' ||
            sig.action === 'PAUSE' ||
            (sig.badge && sig.badge.includes('พักสัญญาณ')) ||
            (isLatest && ((unified && unified.earnings_guard) || (daysToEarn !== null && daysToEarn >= 0 && sigThresh && daysToEarn <= sigThresh)))
        );
        const guardDays = (daysToEarn !== null && daysToEarn >= 0) ? daysToEarn : (sig.guard_days || null);

        let type = (sig.type || '').toUpperCase();
        if (!type && sig.action) {
            const act = (sig.action || '').toUpperCase();
            if (act === 'ENTRY' || act === 'BUY' || act.includes('STRONG')) type = 'RULE_ENTRY';
            else if (act === 'DCA') type = 'RULE_DCA';
            else if (act === 'SELL' || act === 'TRIM' || act === 'TP') type = 'RULE_TP';
            else if (act.includes('พักสัญญาณ') || sig.earnings_guard) type = 'EARNINGS_GUARD';
            else if (act.includes('เลี่ยง') || act === 'AVOID') type = 'AVOID';
            else if (act.includes('รอ') || act === 'WAIT' || act === 'HOLD') type = 'WAIT';
        }
        if ((type.includes('STRONG') && type.includes('BUY')) || type === 'BUY') type = 'RULE_ENTRY';
        else if (type === 'DCA') type = 'RULE_DCA';
        else if (type === 'SELL') type = 'RULE_TP';

        let actionClass = 'hold';
        if (isGuardActive || type === 'EARNINGS_GUARD') actionClass = 'guard';
        else if (type === 'ENTRY' || type === 'RULE_ENTRY') actionClass = 'buy';
        else if (type === 'RULE_DCA') actionClass = 'dca';
        else if (type === 'RULE_TP' || type === 'TRIM') actionClass = 'sell';
        else if (type === 'AVOID') actionClass = 'sell';
        else if (type === 'WAIT' || type === 'HOLD') actionClass = 'hold';

        const badgeText = getSignalBadgeText(sig, isGuardActive, guardDays);
        const reasonsHtml = (sig.reasons || []).map(r => `<li style="margin-bottom: 5px; color: #cbd5e1;">${r}</li>`).join('');

        const bannerDaysText = sigThresh ? `ภายใน ${sigThresh} วัน` : 'ใกล้วันประกาศงบ';
        const guardHtml = isGuardActive
            ? `<div style="margin-bottom:10px; padding:8px 12px; border-radius:6px; background:rgba(251,146,60,0.12); border:1px solid rgba(251,146,60,0.45); color:#fdba74; font-size:0.80rem; font-weight:700;">🟠 งบจะออก${bannerDaysText} คะแนนรวมให้ระงับการซื้อเพิ่มจนกว่างบออก สัญญาณนี้จึงยังไม่ควรใช้</div>`
            : '';

        const isInfo = Boolean(sig.levels_informational || isGuardActive);
        const slColor = isInfo ? '#94a3b8' : '#fb7185';
        const tpColor = isInfo ? '#94a3b8' : '#34d399';
        const rrColor = isInfo ? '#94a3b8' : '#facc15';
        const infoBadge = isInfo ? ' <span style="font-size:0.68rem; color:#94a3b8; font-weight:normal;">(ข้อมูลอ้างอิง)</span>' : '';

        card.innerHTML = `
            ${guardHtml}
            <div class="dc-top">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="dc-badge ${actionClass}">${badgeText}</span>
                    <span style="font-size: 0.88rem; font-weight: 700; color: #f8fafc;">วันที่: ${sig.time}</span>
                    <span style="font-size: 0.80rem; color: #94a3b8;">(ราคาแท่ง: $${sig.price})</span>
                </div>
                <div style="font-size: 0.80rem; font-weight: 700; color: #60a5fa;">
                    ${sig.score_text || (sig.score ? sig.score + '/5 สัญญาณคอนฟลูเอนซ์' : '')}
                </div>
            </div>
            <div style="font-size: 0.84rem; color: #cbd5e1; margin-bottom: 12px; line-height: 1.55;">
                ${sig.summary || ''}
            </div>
            <div style="margin-bottom: 14px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 6px;">ปัจจัยคอนฟลูเอนซ์ที่สนับสนุน:</div>
                <ul style="padding-left: 20px; font-size: 0.80rem; line-height: 1.5;">
                    ${reasonsHtml || '<li>สอดคล้องกับโครงสร้างแนวรับและค่าเฉลี่ยทางเทคนิค</li>'}
                </ul>
            </div>
            <div class="dc-grid">
                <div class="dc-box">
                    <div class="dc-box-title">🛑 จุดตัดขาดทุน (STOP LOSS)${infoBadge}</div>
                    <div class="dc-box-val" style="color: ${slColor};">$${sig.stop_loss ? sig.stop_loss.toFixed(2) : '-'}</div>
                </div>
                <div class="dc-box">
                    <div class="dc-box-title">🎯 เป้าหมายทำกำไร (TARGET)${infoBadge}</div>
                    <div class="dc-box-val" style="color: ${tpColor};">$${sig.target ? sig.target.toFixed(2) : '-'}</div>
                </div>
                <div class="dc-box">
                    <div class="dc-box-title">⚖️ RISK-TO-REWARD (R:R)</div>
                    <div class="dc-box-val" style="color: ${rrColor};">${sig.rr || '1:2.0'}</div>
                </div>
            </div>
        `;
    }

    function getPatternDiagramSvg(pat) {
        const patName = (pat && pat.name) ? pat.name.toLowerCase() : '';
        const neckVal = (pat && pat.neckline) ? ('$' + Number(pat.neckline).toFixed(2)) : 'Neckline';
        const tgtVal = (pat && pat.target) ? ('$' + Number(pat.target).toFixed(2)) : 'Target';
        let upsideVal = '';
        if (pat && pat.upside_pct !== undefined && pat.upside_pct !== null) {
            const u = Number(pat.upside_pct);
            if (!isNaN(u)) {
                upsideVal = (u > 0 ? '+' : (u < 0 ? '-' : '')) + Math.abs(u).toFixed(1) + '%';
            }
        }

        const defs = `
            <defs>
                <filter id="pdd-glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="3" result="blur" />
                    <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
                <marker id="pdd-arr-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10b981" />
                </marker>
                <marker id="pdd-arr-rose" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#f43f5e" />
                </marker>
                <marker id="pdd-arr-cyan" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38bdf8" />
                </marker>
                <linearGradient id="pdd-bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#070a14" />
                    <stop offset="100%" stop-color="#0a1020" />
                </linearGradient>
            </defs>
            <rect width="520" height="230" fill="url(#pdd-bg-grad)" rx="8" />
            <g stroke="rgba(255, 255, 255, 0.035)" stroke-width="1">
                <line x1="40" y1="40" x2="480" y2="40" /><line x1="40" y1="85" x2="480" y2="85" />
                <line x1="40" y1="130" x2="480" y2="130" /><line x1="40" y1="175" x2="480" y2="175" />
                <line x1="120" y1="20" x2="120" y2="210" /><line x1="220" y1="20" x2="220" y2="210" />
                <line x1="320" y1="20" x2="320" y2="210" /><line x1="420" y1="20" x2="420" y2="210" />
            </g>
        `;

        let body = '';

        const isFailed = pat && pat.status === 'failed';
        if (patName.includes('double bottom') || patName.includes('w-shape')) {
            if (isFailed) {
                body = `
                <!-- Failed Double Bottom Breakdown Blueprint -->
                <line x1="70" y1="70" x2="465" y2="70" stroke="#38bdf8" stroke-width="1.8" stroke-dasharray="4,4" />
                <rect x="80" y="52" width="130" height="18" rx="4" fill="rgba(56, 189, 248, 0.15)" stroke="rgba(56, 189, 248, 0.4)" stroke-width="1"/>
                <text x="145" y="65" fill="#38bdf8" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">Neckline ต้าน ${neckVal}</text>

                <!-- Broken Support Floor -->
                <line x1="70" y1="145" x2="465" y2="145" stroke="#ef4444" stroke-width="1.8" stroke-dasharray="3,3" />
                <rect x="80" y="150" width="180" height="18" rx="4" fill="rgba(239, 68, 68, 0.15)" stroke="rgba(239, 68, 68, 0.4)" stroke-width="1"/>
                <text x="170" y="163" fill="#f87171" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">⚠️ แนวรับที่หลุด (Broken Floor)</text>

                <path d="M 60 75 L 130 145 L 225 70 L 320 145 L 380 95 L 450 205" stroke="#ef4444" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="380" y1="95" x2="450" y2="205" stroke="#ef4444" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-rose)" />

                <!-- Swing Nodes -->
                <circle cx="130" cy="145" r="5" fill="#f87171" stroke="#ffffff" stroke-width="1.5" />
                <text x="130" y="133" fill="#fca5a5" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">Bottom 1</text>

                <circle cx="225" cy="70" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" />
                <text x="225" y="52" fill="#7dd3fc" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ยอด Neckline</text>

                <circle cx="320" cy="145" r="5" fill="#f87171" stroke="#ffffff" stroke-width="1.5" />
                <text x="320" y="133" fill="#fca5a5" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">Bottom 2</text>

                <circle cx="380" cy="95" r="5" fill="#fbbf24" stroke="#ffffff" stroke-width="1.5" />
                <text x="380" y="80" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ไม่ผ่าน</text>

                <circle cx="410" cy="155" r="5" fill="#ef4444" stroke="#ffffff" stroke-width="1.5" />
                <text x="445" y="185" fill="#fca5a5" font-size="11" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakdown ⚠️</text>
            `;
            } else {
                body = `
                <!-- Double Bottom W-Shape Blueprint -->
                <line x1="70" y1="85" x2="465" y2="85" stroke="#38bdf8" stroke-width="1.8" stroke-dasharray="4,4" />
                <rect x="80" y="68" width="130" height="18" rx="4" fill="rgba(56, 189, 248, 0.15)" stroke="rgba(56, 189, 248, 0.4)" stroke-width="1"/>
                <text x="145" y="81" fill="#38bdf8" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">Neckline ${neckVal}</text>

                <line x1="395" y1="32" x2="495" y2="32" stroke="#10b981" stroke-width="1.8" stroke-dasharray="3,3" />
                <rect x="395" y="15" width="105" height="18" rx="4" fill="rgba(16, 185, 129, 0.2)" stroke="rgba(16, 185, 129, 0.5)" stroke-width="1"/>
                <text x="447" y="28" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 ${tgtVal} (${upsideVal})</text>

                <path d="M 50 60 L 130 185 L 235 85 L 340 185 L 415 85 L 475 32" stroke="#10b981" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="415" y1="85" x2="475" y2="32" stroke="#10b981" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-green)" />

                <!-- Swing Nodes -->
                <circle cx="130" cy="185" r="5" fill="#10b981" stroke="#ffffff" stroke-width="1.5" />
                <text x="130" y="206" fill="#a7f3d0" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ฐานแรก (Bottom 1)</text>

                <circle cx="235" cy="85" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" />
                <text x="235" y="66" fill="#7dd3fc" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ยอด Neckline</text>

                <circle cx="340" cy="185" r="5" fill="#10b981" stroke="#ffffff" stroke-width="1.5" />
                <text x="340" y="206" fill="#a7f3d0" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ฐานสอง (Bottom 2)</text>

                <circle cx="415" cy="85" r="5" fill="#facc15" stroke="#ffffff" stroke-width="1.5" />
                <text x="415" y="108" fill="#fef08a" font-size="11" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout ↗</text>

                <!-- Measured Move Dimension -->
                <line x1="235" y1="85" x2="235" y2="185" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="2,2" />
                <text x="245" y="140" fill="#94a3b8" font-size="10" font-family="'JetBrains Mono', monospace">H</text>
                <line x1="415" y1="85" x2="415" y2="32" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="2,2" />
                <text x="425" y="60" fill="#94a3b8" font-size="10" font-family="'JetBrains Mono', monospace">+H</text>
            `;
            }
        } else if (patName.includes('double top') || patName.includes('m-shape')) {
            body = `
                <!-- Double Top M-Shape Blueprint -->
                <line x1="70" y1="145" x2="465" y2="145" stroke="#f43f5e" stroke-width="1.8" stroke-dasharray="4,4" />
                <rect x="80" y="152" width="140" height="18" rx="4" fill="rgba(244, 63, 94, 0.15)" stroke="rgba(244, 63, 94, 0.4)" stroke-width="1"/>
                <text x="150" y="165" fill="#fb7185" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">Neckline รับ ${neckVal}</text>

                <line x1="395" y1="202" x2="495" y2="202" stroke="#f43f5e" stroke-width="1.8" stroke-dasharray="3,3" />
                <rect x="395" y="206" width="105" height="18" rx="4" fill="rgba(244, 63, 94, 0.2)" stroke="rgba(244, 63, 94, 0.5)" stroke-width="1"/>
                <text x="447" y="219" fill="#fda4af" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 เป้าลง ${tgtVal} (${upsideVal})</text>

                <path d="M 50 170 L 130 55 L 235 145 L 340 55 L 415 145 L 475 202" stroke="#f43f5e" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="415" y1="145" x2="475" y2="202" stroke="#f43f5e" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-rose)" />

                <!-- Swing Nodes -->
                <circle cx="130" cy="55" r="5" fill="#f43f5e" stroke="#ffffff" stroke-width="1.5" />
                <text x="130" y="40" fill="#fecdd3" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ยอดแรก (Peak 1)</text>

                <circle cx="235" cy="145" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" />
                <text x="235" y="132" fill="#7dd3fc" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ฐาน Neckline</text>

                <circle cx="340" cy="55" r="5" fill="#f43f5e" stroke="#ffffff" stroke-width="1.5" />
                <text x="340" y="40" fill="#fecdd3" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ยอดสอง (Peak 2)</text>

                <circle cx="415" cy="145" r="5" fill="#fb7185" stroke="#ffffff" stroke-width="1.5" />
                <text x="415" y="132" fill="#fb7185" font-size="11" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakdown 🔻</text>
            `;
        } else if (patName.includes('inverted') || patName.includes('inv h&s')) {
            body = `
                <!-- Inverted Head & Shoulders Blueprint -->
                <line x1="60" y1="85" x2="470" y2="85" stroke="#10b981" stroke-width="1.8" stroke-dasharray="4,4" />
                <rect x="70" y="68" width="130" height="18" rx="4" fill="rgba(16, 185, 129, 0.15)" stroke="rgba(16, 185, 129, 0.4)" stroke-width="1"/>
                <text x="135" y="81" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">Neckline ${neckVal}</text>

                <line x1="395" y1="28" x2="495" y2="28" stroke="#10b981" stroke-width="1.8" stroke-dasharray="3,3" />
                <rect x="395" y="12" width="105" height="18" rx="4" fill="rgba(16, 185, 129, 0.2)" stroke="rgba(16, 185, 129, 0.5)" stroke-width="1"/>
                <text x="447" y="25" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 ${tgtVal} (${upsideVal})</text>

                <path d="M 50 60 L 110 135 L 175 85 L 245 190 L 315 85 L 380 135 L 425 85 L 475 28" stroke="#10b981" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="425" y1="85" x2="475" y2="28" stroke="#10b981" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-green)" />

                <circle cx="110" cy="135" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" />
                <text x="110" y="155" fill="#7dd3fc" font-size="10" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ไหล่ซ้าย</text>

                <circle cx="245" cy="190" r="5" fill="#10b981" stroke="#ffffff" stroke-width="1.5" />
                <text x="245" y="210" fill="#a7f3d0" font-size="11" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">หัวกลับ (Head ลึกสุด)</text>

                <circle cx="380" cy="135" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" />
                <text x="380" y="155" fill="#7dd3fc" font-size="10" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ไหล่ขวา (ยกฐาน)</text>

                <circle cx="425" cy="85" r="5" fill="#facc15" stroke="#ffffff" stroke-width="1.5" />
                <text x="425" y="105" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout ↗</text>
            `;
        } else if (patName.includes('head & shoulders') || patName.includes('หัวและไหล่')) {
            body = `
                <!-- Head & Shoulders Blueprint -->
                <line x1="60" y1="145" x2="470" y2="145" stroke="#f43f5e" stroke-width="1.8" stroke-dasharray="4,4" />
                <rect x="70" y="152" width="130" height="18" rx="4" fill="rgba(244, 63, 94, 0.15)" stroke="rgba(244, 63, 94, 0.4)" stroke-width="1"/>
                <text x="135" y="165" fill="#fb7185" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">Neckline ${neckVal}</text>

                <line x1="395" y1="205" x2="495" y2="205" stroke="#f43f5e" stroke-width="1.8" stroke-dasharray="3,3" />
                <rect x="395" y="208" width="105" height="18" rx="4" fill="rgba(244, 63, 94, 0.2)" stroke="rgba(244, 63, 94, 0.5)" stroke-width="1"/>
                <text x="447" y="221" fill="#fda4af" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 ${tgtVal} (${upsideVal})</text>

                <path d="M 50 170 L 110 95 L 175 145 L 245 40 L 315 145 L 380 95 L 425 145 L 475 205" stroke="#f43f5e" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="425" y1="145" x2="475" y2="205" stroke="#f43f5e" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-rose)" />

                <circle cx="110" cy="95" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" />
                <text x="110" y="80" fill="#7dd3fc" font-size="10" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ไหล่ซ้าย</text>

                <circle cx="245" cy="40" r="5" fill="#f43f5e" stroke="#ffffff" stroke-width="1.5" />
                <text x="245" y="25" fill="#fecdd3" font-size="11" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">หัว (Head สูงสุด)</text>

                <circle cx="380" cy="95" r="5" fill="#38bdf8" stroke="#ffffff" stroke-width="1.5" />
                <text x="380" y="80" fill="#7dd3fc" font-size="10" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ไหล่ขวา</text>

                <circle cx="425" cy="145" r="5" fill="#fb7185" stroke="#ffffff" stroke-width="1.5" />
                <text x="425" y="135" fill="#fb7185" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">หลุด Neckline 🔻</text>
            `;
        } else if (patName.includes('flag') || patName.includes('ธง')) {
            body = `
                <!-- Bull Flag Blueprint -->
                <path d="M 60 205 L 180 55" stroke="#10b981" stroke-width="4.5" stroke-linecap="round" filter="url(#pdd-glow)" />
                <line x1="180" y1="55" x2="330" y2="95" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4,4" />
                <line x1="180" y1="105" x2="330" y2="145" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4,4" />

                <path d="M 180 55 L 220 120 L 260 75 L 300 135 L 330 95 L 470 30" stroke="#10b981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none" />
                <line x1="330" y1="95" x2="470" y2="30" stroke="#10b981" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-green)" />

                <rect x="365" y="12" width="105" height="18" rx="4" fill="rgba(16, 185, 129, 0.2)" stroke="rgba(16, 185, 129, 0.5)" stroke-width="1"/>
                <text x="417" y="25" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 ${tgtVal} (${upsideVal})</text>

                <text x="110" y="140" fill="#a7f3d0" font-size="11" font-family="'Inter', sans-serif" font-weight="700">เสาธง (Pole)</text>
                <text x="255" y="125" fill="#7dd3fc" font-size="11" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">กรอบธงสะสมพลัง</text>
                <circle cx="330" cy="95" r="5" fill="#facc15" stroke="#ffffff" stroke-width="1.5" />
                <text x="330" y="80" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout ↗</text>
            `;
        } else if (patName.includes('ascending triangle') || patName.includes('สามเหลี่ยมลู่ขึ้น')) {
            body = `
                <!-- Ascending Triangle Blueprint -->
                <line x1="70" y1="70" x2="420" y2="70" stroke="#f43f5e" stroke-width="2.5" />
                <text x="150" y="60" fill="#fb7185" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700">แนวต้านคงที่ ${neckVal}</text>

                <line x1="70" y1="195" x2="420" y2="85" stroke="#10b981" stroke-width="2.5" />
                <text x="150" y="180" fill="#34d399" font-size="10" font-family="'Inter', sans-serif" font-weight="700">แนวรับยกฐาน (Higher Lows)</text>

                <path d="M 70 195 L 150 70 L 230 155 L 310 70 L 370 115 L 420 70 L 475 25" stroke="#38bdf8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="420" y1="70" x2="475" y2="25" stroke="#10b981" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-green)" />

                <rect x="365" y="10" width="105" height="18" rx="4" fill="rgba(16, 185, 129, 0.2)" stroke="rgba(16, 185, 129, 0.5)" stroke-width="1"/>
                <text x="417" y="23" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 ${tgtVal} (${upsideVal})</text>
                <circle cx="420" cy="70" r="5" fill="#facc15" stroke="#ffffff" stroke-width="1.5" />
                <text x="420" y="90" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">ทะลุต้าน ↗</text>
            `;
        } else if (patName.includes('descending triangle') || patName.includes('สามเหลี่ยมกดไฮ')) {
            body = `
                <!-- Descending Triangle Blueprint -->
                <line x1="70" y1="165" x2="420" y2="165" stroke="#10b981" stroke-width="2.5" />
                <text x="150" y="180" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700">แนวรับคงที่ ${neckVal}</text>

                <line x1="70" y1="45" x2="420" y2="155" stroke="#f43f5e" stroke-width="2.5" />
                <text x="150" y="65" fill="#fb7185" font-size="10" font-family="'Inter', sans-serif" font-weight="700">แนวต้านกดต่ำ (Lower Highs)</text>

                <path d="M 70 45 L 150 165 L 230 80 L 310 165 L 370 120 L 420 165 L 475 210" stroke="#fb7185" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="420" y1="165" x2="475" y2="210" stroke="#f43f5e" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-rose)" />

                <rect x="365" y="206" width="105" height="18" rx="4" fill="rgba(244, 63, 94, 0.2)" stroke="rgba(244, 63, 94, 0.5)" stroke-width="1"/>
                <text x="417" y="219" fill="#fda4af" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 ${tgtVal} (${upsideVal})</text>
                <circle cx="420" cy="165" r="5" fill="#f43f5e" stroke="#ffffff" stroke-width="1.5" />
                <text x="420" y="152" fill="#fb7185" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">หลุดแนวรับ 🔻</text>
            `;
        } else if (patName.includes('wedge') || patName.includes('ลิ่ม')) {
            body = `
                <!-- Falling Wedge Blueprint -->
                <line x1="70" y1="50" x2="390" y2="155" stroke="#38bdf8" stroke-width="2.5" />
                <line x1="70" y1="130" x2="390" y2="175" stroke="#10b981" stroke-width="2.5" />

                <path d="M 70 50 L 140 145 L 220 85 L 290 160 L 345 125 L 365 145 L 475 35" stroke="#10b981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="365" y1="145" x2="475" y2="35" stroke="#10b981" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-green)" />

                <rect x="365" y="15" width="105" height="18" rx="4" fill="rgba(16, 185, 129, 0.2)" stroke="rgba(16, 185, 129, 0.5)" stroke-width="1"/>
                <text x="417" y="28" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 ${tgtVal} (${upsideVal})</text>
                <text x="210" y="65" fill="#7dd3fc" font-size="10" font-family="'Inter', sans-serif" font-weight="700">แนวต้านลิ่มเฉียงลง</text>
                <text x="210" y="175" fill="#a7f3d0" font-size="10" font-family="'Inter', sans-serif" font-weight="700">แนวรับลิ่ม</text>
                <circle cx="365" cy="145" r="5" fill="#facc15" stroke="#ffffff" stroke-width="1.5" />
                <text x="365" y="165" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout ลิ่ม ↗</text>
            `;
        } else if (patName.includes('channel') || patName.includes('ช่องคู่ขนาน')) {
            body = `
                <!-- Ascending Channel Blueprint -->
                <line x1="60" y1="95" x2="450" y2="35" stroke="#10b981" stroke-width="2.5" />
                <line x1="60" y1="195" x2="450" y2="135" stroke="#38bdf8" stroke-width="2.5" />

                <path d="M 60 195 L 150 75 L 240 170 L 340 55 L 420 145 L 475 40" stroke="#34d399" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="420" y1="145" x2="475" y2="40" stroke="#10b981" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-green)" />

                <rect x="365" y="15" width="105" height="18" rx="4" fill="rgba(16, 185, 129, 0.2)" stroke="rgba(16, 185, 129, 0.5)" stroke-width="1"/>
                <text x="417" y="28" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 ${tgtVal} (${upsideVal})</text>
                <text x="180" y="55" fill="#a7f3d0" font-size="10" font-family="'Inter', sans-serif" font-weight="700">กรอบบน (Higher High)</text>
                <text x="180" y="195" fill="#7dd3fc" font-size="10" font-family="'Inter', sans-serif" font-weight="700">กรอบล่าง (Higher Low)</text>
            `;
        } else if (patName.includes('triple bottom') || patName.includes('สามฐาน')) {
            body = `
                <!-- Triple Bottom Blueprint -->
                <line x1="70" y1="180" x2="430" y2="180" stroke="#10b981" stroke-width="2.5" />
                <line x1="70" y1="95" x2="450" y2="95" stroke="#38bdf8" stroke-dasharray="4,4" />
                <text x="140" y="85" fill="#38bdf8" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700">Neckline ${neckVal}</text>

                <path d="M 50 60 L 110 180 L 175 95 L 240 180 L 305 95 L 370 180 L 420 95 L 475 35" stroke="#10b981" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="420" y1="95" x2="475" y2="35" stroke="#10b981" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-green)" />

                <circle cx="110" cy="180" r="5" fill="#10b981" stroke="#ffffff" stroke-width="1.5" />
                <circle cx="240" cy="180" r="5" fill="#10b981" stroke="#ffffff" stroke-width="1.5" />
                <circle cx="370" cy="180" r="5" fill="#10b981" stroke="#ffffff" stroke-width="1.5" />
                <text x="240" y="200" fill="#a7f3d0" font-size="10" font-family="'Inter', sans-serif" font-weight="700" text-anchor="middle">ฐานรับหินผา 3 ครั้ง (Triple Floor)</text>
            `;
        } else {
            // Default Box / Range Consolidation Blueprint
            body = `
                <!-- Consolidation Box / Standard Price Action Blueprint -->
                <rect x="80" y="75" width="340" height="95" fill="rgba(56, 189, 248, 0.08)" stroke="rgba(56, 189, 248, 0.3)" stroke-width="1.5" stroke-dasharray="4,4" rx="4"/>
                <line x1="70" y1="75" x2="430" y2="75" stroke="#f43f5e" stroke-width="2" />
                <line x1="70" y1="170" x2="430" y2="170" stroke="#10b981" stroke-width="2" />

                <path d="M 80 170 L 150 75 L 220 170 L 290 75 L 360 170 L 415 75 L 475 25" stroke="#38bdf8" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none" filter="url(#pdd-glow)" />
                <line x1="415" y1="75" x2="475" y2="25" stroke="#10b981" stroke-width="3" stroke-linecap="round" marker-end="url(#pdd-arr-green)" />

                <text x="140" y="65" fill="#fb7185" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700">กรอบแนวต้าน ${neckVal}</text>
                <text x="140" y="190" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700">กรอบแนวรับสะสม</text>

                <rect x="365" y="10" width="105" height="18" rx="4" fill="rgba(16, 185, 129, 0.2)" stroke="rgba(16, 185, 129, 0.5)" stroke-width="1"/>
                <text x="417" y="23" fill="#34d399" font-size="10" font-family="'JetBrains Mono', monospace" font-weight="700" text-anchor="middle">🎯 ${tgtVal} (${upsideVal})</text>
                <circle cx="415" cy="75" r="5" fill="#facc15" stroke="#ffffff" stroke-width="1.5" />
                <text x="415" y="95" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout ↗</text>
            `;
        }

        return `<svg width="100%" height="220" viewBox="0 0 520 230" fill="none" xmlns="http://www.w3.org/2000/svg">` + defs + body + `</svg>`;
    }

    // Pattern Deep-Dive Breakdown
    function renderPatternDeepDive(tData) {
        const pat = tData ? tData.pattern : null;
        const badge = document.getElementById('pdd_badge');
        const dTitle = document.getElementById('pdd_diagram_title');
        const dType = document.getElementById('pdd_diagram_type');
        const dContainer = document.getElementById('pdd_diagram_container');
        const caption = document.getElementById('pdd_summary_caption');
        const struct = document.getElementById('pdd_structure');
        const psych = document.getElementById('pdd_psychology');
        const act = document.getElementById('pdd_action_plan');
        const inv = document.getElementById('pdd_invalidation');
        const patBtn = document.getElementById('btn_toggle_pat_chart');

        if (patBtn) {
            if (indicatorVisibility.pat) {
                patBtn.classList.add('active');
                patBtn.textContent = '✅ ซ่อนเส้นแพทเทิร์น';
            } else {
                patBtn.classList.remove('active');
                patBtn.textContent = '⚡ ตีเส้นแพทเทิร์นบนกราฟ';
            }
        }

        if (!pat) {
            if (badge) {
                badge.textContent = '⚪ ไม่พบรูปแบบแพทเทิร์นชัดเจน';
                badge.style.color = '#94a3b8';
                badge.style.borderColor = 'rgba(148, 163, 184, 0.3)';
                badge.style.background = 'rgba(148, 163, 184, 0.1)';
            }
            if (dTitle) dTitle.textContent = 'โครงสร้างการแกว่งตัวทั่วไป (Standard Price Action)';
            if (dType) {
                dType.textContent = 'Price Action';
                dType.style.color = '#94a3b8';
            }
            if (dContainer) dContainer.innerHTML = getPatternDiagramSvg(null);
            if (caption) caption.innerHTML = '💡 <strong>สภาวะปัจจุบัน:</strong> ไม่พบรูปแบบเรขาคณิตคลาสสิกที่เด่นชัด การเคลื่อนไหวของราคาอิงตามเส้นแนวโน้ม EMA และระดับราคาทางจิตวิทยา Pivot Points';
            if (struct) struct.textContent = 'ราคาแกว่งตัวตามแนวโน้มปกติ ไม่ปรากฏการบีบอัดตัวหรือการฟอร์มตัวของโครงสร้าง Reversal/Continuation ที่มีนัยสำคัญทางสถิติ';
            if (psych) psych.textContent = 'ตลาดยังอยู่ในสภาวะสมดุลระหว่างแรงซื้อและแรงขาย (Equilibrium) สถาบันยังไม่มีการเข้าทำธุรกรรมสะสม (Accumulation) หรือกระจายของ (Distribution) ก้อนใหญ่';
            if (act) act.textContent = 'เน้นการเทรดตามทิศทางแนวโน้ม EMA 4 เส้น (Trend Following) หรือเข้าซื้อเมื่อราคาลงทดสอบแนวรับ Support 1 / 52-Week Low';
            if (inv) inv.textContent = 'ใช้ระดับ Stop Loss ตามความผันผวน 1.5 ATR หรือจุดต่ำสุดเดิมของสัปดาห์';
            return;
        }

        const isBear = (pat.type && pat.type.toLowerCase().includes('bear')) || pat.status === 'broke_down';
        const isFailed = pat.status === 'failed';
        const isBrokeDown = pat.status === 'broke_down';
        const isForming = pat.status === 'forming';

        if (badge) {
            badge.textContent = pat.badge || pat.name;
            if (isFailed) {
                badge.style.color = '#ef4444';
                badge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                badge.style.background = 'rgba(239, 68, 68, 0.15)';
            } else if (isBrokeDown) {
                badge.style.color = '#fb7185';
                badge.style.borderColor = 'rgba(251, 113, 133, 0.4)';
                badge.style.background = 'rgba(251, 113, 133, 0.15)';
            } else if (isForming) {
                badge.style.color = '#facc15';
                badge.style.borderColor = 'rgba(250, 204, 21, 0.4)';
                badge.style.background = 'rgba(250, 204, 21, 0.15)';
            } else {
                badge.style.color = isBear ? '#fb7185' : '#34d399';
                badge.style.borderColor = isBear ? 'rgba(251, 113, 133, 0.4)' : 'rgba(52, 211, 153, 0.4)';
                badge.style.background = isBear ? 'rgba(251, 113, 133, 0.15)' : 'rgba(52, 211, 153, 0.15)';
            }
        }
        if (dTitle) dTitle.textContent = (isFailed ? '⚠️ ' : (isBrokeDown ? '🔻 ' : 'แผนผัง ')) + pat.name + ' (Visual Pattern Blueprint)';
        if (dType) {
            dType.textContent = pat.type || 'Technical Model';
            if (isFailed) {
                dType.style.color = '#ef4444';
                dType.style.borderColor = 'rgba(239, 68, 68, 0.3)';
            } else if (isBrokeDown) {
                dType.style.color = '#fb7185';
                dType.style.borderColor = 'rgba(251, 113, 133, 0.3)';
            } else if (isForming) {
                dType.style.color = '#facc15';
                dType.style.borderColor = 'rgba(250, 204, 21, 0.3)';
            } else {
                dType.style.color = isBear ? '#fb7185' : '#34d399';
                dType.style.borderColor = isBear ? 'rgba(251, 113, 133, 0.3)' : 'rgba(52, 211, 153, 0.3)';
            }
        }
        if (dContainer) dContainer.innerHTML = getPatternDiagramSvg(pat);
        if (caption) {
            let upsideTxt = '-';
            if (pat.upside_pct !== undefined && pat.upside_pct !== null) {
                const u = Number(pat.upside_pct);
                if (!isNaN(u)) {
                    upsideTxt = (u > 0 ? '+' : (u < 0 ? '-' : '')) + Math.abs(u).toFixed(1) + '%';
                }
            }
            const neckTxt = pat.neckline ? ('$' + Number(pat.neckline).toFixed(2)) : '-';
            const tgtTxt = isFailed ? '<span style="color:#ef4444;font-weight:700;">ยกเลิกเป้าหมาย (แพทเทิร์นล้มเหลว)</span>' : (isBrokeDown ? '<span style="color:#fb7185;font-weight:700;">เบรกลง (หลุดกรอบล่าง)</span>' : (pat.target ? ('$' + Number(pat.target).toFixed(2) + ' (' + upsideTxt + ')') : '-'));
            const startPt = pat.key_points && pat.key_points.length > 0 ? pat.key_points[0] : null;
            const startTxt = startPt ? (' | 🚩 <strong>จุดเริ่มแพทเทิร์น:</strong> ' + startPt.time + ' ที่ $' + Number(startPt.price).toFixed(2) + ' (' + (startPt.name || 'Start') + ')') : '';
            caption.innerHTML = `📐 <strong>สรุปสัญญาณ:</strong> ${pat.summary || pat.name}${startTxt} | <strong>Neckline:</strong> ${neckTxt} | <strong>เป้าหมาย (Measured Target):</strong> ${tgtTxt} | <strong>วิธีคำนวณเป้า:</strong> ${pat.target_calc || '-'}`;
        }
        if (struct) {
            let structTxt = pat.structure || pat.summary || '-';
            if (pat.key_points && pat.key_points.length > 0) {
                const chain = pat.key_points.map(kp => kp.name + ' ($' + Number(kp.price).toFixed(2) + ')').join(' ➔ ');
                structTxt = 'ลำดับจุดสวิง: ' + chain + ' • ' + structTxt;
            }
            struct.textContent = structTxt;
        }
        if (psych) psych.textContent = pat.psychology || '-';
        if (act) act.textContent = pat.action_plan || '-';
        if (inv) inv.textContent = pat.invalidation || '-';
    }

    // =========================================================================
    // Financial Statements & Quarterly Trends Engine (8 Quarters / 2 Years)
    // =========================================================================
    let currentFinView = 'all';

    function switchFinView(mode) {
        currentFinView = mode;
        const btnAll = document.getElementById('fin_tab_all');
        const btnTable = document.getElementById('fin_tab_table');
        const chartPanel = document.getElementById('fin_chart_panel');
        const tablePanel = document.getElementById('fin_table_panel');

        if (mode === 'table') {
            if (btnAll) btnAll.classList.remove('active');
            if (btnTable) btnTable.classList.add('active');
            if (chartPanel) chartPanel.style.display = 'none';
            if (tablePanel) tablePanel.style.display = 'block';
        } else {
            if (btnAll) btnAll.classList.add('active');
            if (btnTable) btnTable.classList.remove('active');
            if (chartPanel) chartPanel.style.display = 'block';
            if (tablePanel) tablePanel.style.display = 'block';
        }
    }

    function scrollToFinancials() {
        const elem = document.getElementById('financials_card');
        if (elem) elem.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function toggleFScoreCriteria() {
        const el = document.getElementById('fin_fscore_criteria');
        const arrow = document.getElementById('fin_fscore_arrow');
        if (!el) return;
        const isOpen = el.style.display !== 'none';
        el.style.display = isOpen ? 'none' : 'flex';
        if (arrow) arrow.textContent = isOpen ? '▼' : '▲';
    }

    window.switchFinView = switchFinView;
    window.scrollToFinancials = scrollToFinancials;
    window.toggleFScoreCriteria = toggleFScoreCriteria;

    function _formatFinCurrency(val) {
        if (val === undefined || val === null || isNaN(val)) return '-';
        const absVal = Math.abs(val);
        const sign = val < 0 ? '-' : '';
        if (absVal >= 1e12) return `${sign}$${(absVal / 1e12).toFixed(2)}T`;
        if (absVal >= 1e9) return `${sign}$${(absVal / 1e9).toFixed(2)}B`;
        if (absVal >= 1e6) return `${sign}$${(absVal / 1e6).toFixed(2)}M`;
        if (absVal >= 1e3) return `${sign}$${(absVal / 1e3).toFixed(1)}K`;
        return `${sign}$${Number(absVal).toFixed(2)}`;
    }

    function _renderGrowthBadge(pct, label) {
        if (pct === undefined || pct === null || isNaN(pct)) return '<span class="fin-badge-neutral">-</span>';
        const num = Number(pct);
        const isPos = num > 0;
        const isNeg = num < 0;
        const sign = isPos ? '+' : (isNeg ? '-' : '');
        const arrow = isPos ? '▲' : (isNeg ? '▼' : '');
        const cls = isPos ? 'fin-badge-pos' : (isNeg ? 'fin-badge-neg' : 'fin-badge-neutral');
        const lbl = label ? ` ${label}` : '';
        return `<span class="${cls}">${sign}${Math.abs(num).toFixed(1)}% ${arrow}${lbl}</span>`;
    }

    function updateFinancialsSection(ticker) {
        const card = document.getElementById('financials_card');
        if (!card) return;

        const finData = (window.FINANCIALS_DATA && window.FINANCIALS_DATA[ticker]) ||
                        (STOCKS_META[ticker] && STOCKS_META[ticker].financials);

        const badge = document.getElementById('fin_latest_quarter_badge');
        const hudGrid = document.getElementById('fin_hud_grid');
        const insightsGrid = document.getElementById('fin_insights_grid');
        const chartPanel = document.getElementById('fin_chart_panel');
        const tablePanel = document.getElementById('fin_table_panel');
        const emptyState = document.getElementById('fin_empty_state');
        const emptyTitle = document.getElementById('fin_empty_title');
        const emptyDesc = document.getElementById('fin_empty_desc');

        if (!finData || !finData.has_data || !finData.quarters || finData.quarters.length === 0) {
            const isEtf = (finData && finData.is_etf) || ['VOO', 'QQQI', 'SPY', 'IVV'].includes(ticker);
            if (emptyState) emptyState.style.display = 'block';
            if (hudGrid) hudGrid.style.display = 'none';
            if (insightsGrid) insightsGrid.style.display = 'none';
            if (chartPanel) chartPanel.style.display = 'none';
            if (tablePanel) tablePanel.style.display = 'none';

            if (badge) {
                badge.textContent = isEtf ? 'กองทุน ETF' : 'ไม่มีข้อมูลงบ';
                badge.style.background = 'rgba(245, 158, 11, 0.15)';
                badge.style.color = '#fbbf24';
                badge.style.borderColor = 'rgba(245, 158, 11, 0.35)';
            }

            if (isEtf) {
                if (emptyTitle) emptyTitle.textContent = `${ticker} เป็นกองทุน ETF ไม่มีรายงานงบการเงินรายไตรมาสแบบหุ้นรายตัว`;
                if (emptyDesc) emptyDesc.textContent = `กองทุนดัชนีและ High Income ETF (เช่น VOO, QQQI) ไม่มีรายงานรายได้ กำไร หรือหนี้สินแบบบริษัทจดทะเบียน โปรดดูผลตอบแทน เงินปันผล และราคาตลาดจากกราฟและแถบข้อมูลด้านขวา`;
            } else {
                if (emptyTitle) emptyTitle.textContent = `ยังไม่มีรายงานงบการเงินรายไตรมาสสำหรับ ${ticker}`;
                if (emptyDesc) emptyDesc.textContent = `บริษัทอาจเป็นหุ้นที่เพิ่งเข้าตลาด หรือยังไม่มีรายงานงบการเงินรอบล่าสุดส่งตลาดหลักทรัพย์`;
            }
            return;
        }

        // Show data containers
        if (emptyState) emptyState.style.display = 'none';
        if (hudGrid) hudGrid.style.display = 'grid';
        if (insightsGrid) insightsGrid.style.display = 'grid';
        if (chartPanel) chartPanel.style.display = (currentFinView === 'table') ? 'none' : 'block';
        if (tablePanel) tablePanel.style.display = 'block';

        const quarters = finData.quarters;
        const latest = quarters[quarters.length - 1] || {};

        if (badge) {
            badge.textContent = `งบล่าสุด ${latest.quarter_label || '-'} (${latest.date || '-'})`;
            badge.style.background = 'rgba(59, 130, 246, 0.15)';
            badge.style.color = '#60a5fa';
            badge.style.borderColor = 'rgba(59, 130, 246, 0.35)';
        }

        // 1. HUD Strip
        const revTtmElem = document.getElementById('fin_hud_rev_ttm');
        const revSubElem = document.getElementById('fin_hud_rev_sub');
        if (revTtmElem) revTtmElem.textContent = finData.ttm_revenue_fmt || '-';
        if (revSubElem) {
            const yoyRev = latest.rev_growth_yoy;
            const yoyBadge = yoyRev != null ? _renderGrowthBadge(yoyRev, 'YoY') : '';
            revSubElem.innerHTML = `ล่าสุด: <strong>${latest.revenue_fmt || '-'}</strong> ${yoyBadge}`;
        }

        const niTtmElem = document.getElementById('fin_hud_ni_ttm');
        const niSubElem = document.getElementById('fin_hud_ni_sub');
        if (niTtmElem) niTtmElem.textContent = finData.ttm_net_income_fmt || '-';
        if (niSubElem) {
            const margin = latest.net_margin;
            const marginColor = (margin != null && margin >= 20) ? '#34d399' : ((margin != null && margin >= 0) ? '#38bdf8' : '#fb7185');
            niSubElem.innerHTML = `Net Margin ล่าสุด: <strong style="color:${marginColor}">${margin != null ? margin.toFixed(1) + '%' : '-'}</strong> (กำไร ${latest.net_income_fmt || '-'})`;
        }

        const deElem = document.getElementById('fin_hud_de');
        const deSubElem = document.getElementById('fin_hud_de_sub');
        if (deElem) {
            const de = latest.debt_to_equity;
            deElem.textContent = de != null ? `${de.toFixed(2)}x` : '-';
            deElem.style.color = (de != null && de > 2.5) ? '#fb7185' : ((de != null && de <= 1.0) ? '#34d399' : '#f8fafc');
        }
        if (deSubElem) deSubElem.textContent = `หนี้สินรวม: ${latest.total_debt_fmt || '-'} • ทุน: ${latest.stockholders_equity_fmt || '-'}`;

        const fcfElem = document.getElementById('fin_hud_fcf');
        const fcfSubElem = document.getElementById('fin_hud_fcf_sub');
        if (fcfElem) fcfElem.textContent = latest.fcf_fmt || '-';
        if (fcfSubElem) fcfSubElem.textContent = `12M รวม (TTM): ${finData.ttm_fcf_fmt || '-'}`;

        // 2. Financial Checklist Card (เกณฑ์ของระบบนี้ ไม่ใช่ Piotroski)
        const fScore = finData.f_score || {};
        const fScoreTitleElem = document.getElementById('fin_fscore_title');
        if (fScoreTitleElem) {
            fScoreTitleElem.textContent = fScore.title || '🏆 เช็กลิสต์งบ 9 ข้อ (เกณฑ์ของระบบนี้ ไม่ใช่ Piotroski)';
        }
        const fScoreValElem = document.getElementById('fin_fscore_val');
        const fScoreLabelElem = document.getElementById('fin_fscore_label');
        const isInsufficient = Boolean(fScore.insufficient_data || fScore.label === 'ข้อมูลไม่พอ' || (fScore.evaluated_count !== undefined && fScore.evaluated_count < 5));

        if (fScoreValElem) {
            if (isInsufficient) {
                fScoreValElem.innerHTML = `-<span>/${fScore.max_score || 9}</span>`;
                fScoreValElem.style.color = '#94a3b8';
            } else if (fScore.score != null) {
                fScoreValElem.innerHTML = `${fScore.score}<span>/${fScore.max_score || 9}</span>`;
                fScoreValElem.style.color = fScore.color || '#34d399';
            } else {
                fScoreValElem.innerHTML = `-<span>/9</span>`;
                fScoreValElem.style.color = '#94a3b8';
            }
        }
        if (fScoreLabelElem) {
            if (isInsufficient) {
                fScoreLabelElem.textContent = 'ข้อมูลไม่พอ';
                fScoreLabelElem.style.color = '#94a3b8';
            } else {
                fScoreLabelElem.textContent = fScore.label || '-';
                fScoreLabelElem.style.color = fScore.color || '#cbd5e1';
            }
        }

        const criteriaList = document.getElementById('fin_fscore_criteria');
        if (criteriaList && fScore.criteria) {
            criteriaList.innerHTML = fScore.criteria.map(c => {
                const passClass = c.passed ? 'fin-criteria-pass' : 'fin-criteria-fail';
                const passIcon = c.passed ? '✓' : '✗';
                return `<div class="fin-criteria-item">
                    <span class="${passClass}">${passIcon} ${escapeHtml(c.name || '')}</span>
                    <span style="font-family:'JetBrains Mono',monospace;color:#cbd5e1;">${escapeHtml(c.detail || '')}</span>
                </div>`;
            }).join('');
        }

        // 3. 3-Dimension Executive Summary Card
        const execSummary = finData.executive_summary || {};
        const growthElem = document.getElementById('fin_summary_growth');
        const profElem = document.getElementById('fin_summary_profitability');
        const debtElem = document.getElementById('fin_summary_debt');
        if (growthElem) growthElem.textContent = execSummary.growth || '-';
        if (profElem) profElem.textContent = execSummary.profitability || '-';
        if (debtElem) debtElem.textContent = execSummary.debt || '-';

        // 4. Render SVG Interactive Chart
        renderFinancialTrendChart(quarters);

        // 5. Render Detailed 8-Quarter Statement Table
        renderFinancialStatementTable(quarters);
    }

    function renderFinancialTrendChart(quarters) {
        const wrap = document.getElementById('fin_svg_wrap');
        if (!wrap || !quarters || quarters.length === 0) return;

        const W = 960;
        const H = 250;
        const padL = 70;
        const padR = 25;
        const padT = 30;
        const padB = 45;
        const plotW = W - padL - padR;
        const plotH = H - padT - padB;

        // Find max value across revenue, net income, fcf
        let maxVal = 0;
        quarters.forEach(q => {
            if (q.revenue && q.revenue > maxVal) maxVal = q.revenue;
            if (q.net_income && q.net_income > maxVal) maxVal = q.net_income;
            if (q.fcf && q.fcf > maxVal) maxVal = q.fcf;
        });
        if (maxVal <= 0) maxVal = 1000000;
        maxVal = maxVal * 1.15; // 15% headroom

        // Y-axis grid levels (4 steps)
        let gridLines = '';
        for (let i = 0; i <= 4; i++) {
            const ratio = i / 4;
            const y = padT + plotH - (ratio * plotH);
            const val = ratio * maxVal;
            gridLines += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="rgba(255,255,255,0.07)" stroke-dasharray="3,3" />`;
            gridLines += `<text x="${padL - 10}" y="${y + 4}" fill="#64748b" font-size="10" font-family="'JetBrains Mono', monospace" text-anchor="end">${_formatFinCurrency(val)}</text>`;
        }

        const slotW = plotW / quarters.length;
        const barW = Math.min(slotW * 0.22, 28);
        const gap = Math.min(slotW * 0.04, 6);

        let barsSvg = '';
        quarters.forEach((q, idx) => {
            const slotCenter = padL + (idx * slotW) + (slotW / 2);
            const isLatest = idx === quarters.length - 1;

            // X-axis quarter labels
            const qX = slotCenter;
            const qY = H - 22;
            const labelColor = isLatest ? '#60a5fa' : '#94a3b8';
            const fontWt = isLatest ? '800' : '600';
            barsSvg += `<text x="${qX}" y="${qY}" fill="${labelColor}" font-size="11" font-weight="${fontWt}" font-family="'Inter', sans-serif" text-anchor="middle">${q.quarter_label}</text>`;
            barsSvg += `<text x="${qX}" y="${qY + 14}" fill="#64748b" font-size="9" font-family="'JetBrains Mono', monospace" text-anchor="middle">${q.date.slice(2)}</text>`;

            // Highlight latest column subtle background
            if (isLatest) {
                barsSvg += `<rect x="${slotCenter - (slotW / 2) + 2}" y="${padT}" width="${slotW - 4}" height="${plotH}" fill="rgba(59,130,246,0.04)" rx="6" />`;
            }

            // Bar 1: Revenue (Left)
            const rev = q.revenue || 0;
            const revH = Math.max((rev / maxVal) * plotH, 2);
            const revX = slotCenter - barW - (gap / 2) - (barW / 2);
            const revY = padT + plotH - revH;
            const revTip = `${q.quarter_label} (${q.date})&#10;รายได้รวม: ${q.revenue_fmt || '-'} (${q.rev_growth_yoy != null ? (q.rev_growth_yoy >= 0 ? '+' : '') + q.rev_growth_yoy + '% YoY' : 'QoQ: ' + (q.rev_growth_qoq || '-') + '%'})`;
            barsSvg += `<rect x="${revX}" y="${revY}" width="${barW}" height="${revH}" fill="url(#finGradRev)" rx="3" ry="3"><title>${revTip}</title></rect>`;

            // Bar 2: Net Income (Center)
            const ni = q.net_income || 0;
            const niH = Math.max((Math.abs(ni) / maxVal) * plotH, 2);
            const niX = slotCenter - (barW / 2);
            const niY = padT + plotH - niH;
            const niGrad = ni >= 0 ? 'url(#finGradNiPos)' : 'url(#finGradNiNeg)';
            const niTip = `${q.quarter_label} (${q.date})&#10;กำไรสุทธิ: ${q.net_income_fmt || '-'} (Net Margin: ${q.net_margin != null ? q.net_margin + '%' : '-'})`;
            barsSvg += `<rect x="${niX}" y="${niY}" width="${barW}" height="${niH}" fill="${niGrad}" rx="3" ry="3"><title>${niTip}</title></rect>`;

            // Bar 3: FCF (Right)
            const fcf = q.fcf || 0;
            const fcfH = Math.max((Math.abs(fcf) / maxVal) * plotH, 2);
            const fcfX = slotCenter + (gap / 2) + (barW / 2);
            const fcfY = padT + plotH - fcfH;
            const fcfTip = `${q.quarter_label} (${q.date})&#10;กระแสเงินสดอิสระ (FCF): ${q.fcf_fmt || '-'}`;
            barsSvg += `<rect x="${fcfX}" y="${fcfY}" width="${barW}" height="${fcfH}" fill="url(#finGradFcf)" rx="3" ry="3"><title>${fcfTip}</title></rect>`;

            // Revenue value pill on top
            if (revH > 25) {
                barsSvg += `<text x="${revX + (barW / 2)}" y="${revY - 4}" fill="#38bdf8" font-size="9" font-weight="700" font-family="'JetBrains Mono', monospace" text-anchor="middle">${q.revenue_fmt}</text>`;
            }
        });

        const svgContent = `
            <svg width="100%" height="250" viewBox="0 0 ${W} ${H}" fill="none" xmlns="http://www.w3.org/2000/svg">
                <defs>
                    <linearGradient id="finGradRev" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.95" />
                        <stop offset="100%" stop-color="#0284c7" stop-opacity="0.75" />
                    </linearGradient>
                    <linearGradient id="finGradNiPos" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#34d399" stop-opacity="0.95" />
                        <stop offset="100%" stop-color="#059669" stop-opacity="0.75" />
                    </linearGradient>
                    <linearGradient id="finGradNiNeg" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#fb7185" stop-opacity="0.95" />
                        <stop offset="100%" stop-color="#e11d48" stop-opacity="0.75" />
                    </linearGradient>
                    <linearGradient id="finGradFcf" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#c084fc" stop-opacity="0.95" />
                        <stop offset="100%" stop-color="#7e22ce" stop-opacity="0.75" />
                    </linearGradient>
                </defs>
                ${gridLines}
                ${barsSvg}
            </svg>
        `;
        wrap.innerHTML = svgContent;
    }

    function renderFinancialStatementTable(quarters) {
        const container = document.getElementById('fin_table_container');
        if (!container || !quarters || quarters.length === 0) return;

        // Header Columns
        let thCols = '<th class="th-metric">รายการตัวชี้วัด (Financial Metrics)</th>';
        quarters.forEach((q, idx) => {
            const isLatest = idx === quarters.length - 1;
            const latestBadge = isLatest ? ' <span style="font-size:0.65rem; background:#3b82f6; color:#fff; padding:1px 5px; border-radius:3px;">ล่าสุด</span>' : '';
            thCols += `<th class="th-quarter ${isLatest ? 'th-latest' : ''}"><div>${q.quarter_label}${latestBadge}</div><div style="font-size:0.65rem; color:#64748b; font-weight:normal; margin-top:2px;">${q.date}</div></th>`;
        });

        // Helper to build a table row
        function buildRow(title, getter, isSub = false) {
            let rowHtml = `<tr class="${isSub ? 'fin-row-sub' : ''}"><td class="fin-row-header">${title}</td>`;
            quarters.forEach((q, idx) => {
                const isLatest = idx === quarters.length - 1;
                const cellVal = getter(q, idx);
                rowHtml += `<td class="fin-cell ${isLatest ? 'td-latest' : ''}">${cellVal}</td>`;
            });
            rowHtml += `</tr>`;
            return rowHtml;
        }

        let rowsHtml = '';
        // 1. Revenue
        rowsHtml += buildRow('💰 รายได้รวม (Total Revenue)', q => `<strong>${q.revenue_fmt || '-'}</strong>`);
        // 2. QoQ Revenue Growth
        rowsHtml += buildRow('⚡ เติบโต QoQ (%)', q => _renderGrowthBadge(q.rev_growth_qoq), true);
        // 3. YoY Revenue Growth
        rowsHtml += buildRow('📈 เติบโต YoY (%)', q => _renderGrowthBadge(q.rev_growth_yoy), true);
        // 4. Gross Profit
        rowsHtml += buildRow('📈 กำไรขั้นต้น (Gross Profit)', q => q.gross_profit_fmt || '-');
        // 5. Gross Margin
        rowsHtml += buildRow('⚙️ อัตรากำไรขั้นต้น (Gross Margin)', q => q.gross_margin != null ? `${q.gross_margin.toFixed(1)}%` : '-', true);
        // 6. Operating Income
        rowsHtml += buildRow('🏢 กำไรจากการดำเนินงาน (Operating Income)', q => q.operating_income_fmt || '-');
        // 7. Net Income
        rowsHtml += buildRow('🎯 กำไรสุทธิ (Net Income)', q => {
            const ni = q.net_income;
            const col = (ni != null && ni >= 0) ? '#34d399' : '#fb7185';
            return `<strong style="color:${col}">${q.net_income_fmt || '-'}</strong>`;
        });
        // 8. Net Margin
        rowsHtml += buildRow('📊 อัตรากำไรสุทธิ (Net Margin)', q => {
            const m = q.net_margin;
            if (m == null) return '-';
            const col = m >= 15 ? '#34d399' : (m >= 0 ? '#38bdf8' : '#fb7185');
            return `<span style="color:${col}; font-weight:700;">${m.toFixed(1)}%</span>`;
        }, true);
        // 9. Diluted EPS
        rowsHtml += buildRow('💵 กำไรต่อหุ้น (Diluted EPS)', q => {
            const eps = q.eps;
            if (eps == null) return '-';
            const epsBadge = q.eps_growth_yoy != null ? ` ${_renderGrowthBadge(q.eps_growth_yoy)}` : '';
            return `$${eps.toFixed(2)}${epsBadge}`;
        });
        // 10. Free Cash Flow
        rowsHtml += buildRow('🌊 กระแสเงินสดอิสระ (FCF)', q => `<span style="color:#c084fc;">${q.fcf_fmt || '-'}</span>`);
        // 11. Total Debt
        rowsHtml += buildRow('💳 หนี้สินรวม (Total Debt)', q => q.total_debt_fmt || '-');
        // 12. Stockholders Equity
        rowsHtml += buildRow('🏛️ ส่วนของผู้ถือหุ้น (Stockholders Equity)', q => q.stockholders_equity_fmt || '-');
        // 13. Debt to Equity
        rowsHtml += buildRow('⚖️ หนี้สินต่อทุน (D/E Ratio)', q => {
            const de = q.debt_to_equity;
            if (de == null) return '-';
            const col = de > 2.5 ? '#fb7185' : (de <= 1.0 ? '#34d399' : '#f8fafc');
            return `<span style="color:${col}; font-weight:700;">${de.toFixed(2)}x</span>`;
        }, true);
        // 14. Quarterly P/E
        rowsHtml += buildRow('🏷️ P/E อ้างอิงไตรมาส', q => q.pe_quarterly != null ? `${q.pe_quarterly.toFixed(1)}x` : '-', true);

        container.innerHTML = `
            <table class="fin-table">
                <thead><tr>${thCols}</tr></thead>
                <tbody>${rowsHtml}</tbody>
            </table>
        `;
    }

    // Switch Tabs (Lightweight Chart vs TradingView Full Embed)
    function switchChartTab(mode) {
        currentChartMode = mode;
        const btnTech = document.getElementById('tab_tech');
        const btnTv = document.getElementById('tab_tv');
        const lwWrap = document.getElementById('chart_container_wrap');
        const lwMain = document.getElementById('chart_container');
        const stackWrap = document.getElementById('subpanes_stack');
        const botBar = document.querySelector('.chart-botbar');
        const tvBox = document.getElementById('tv_widget_container');

        if (mode === 'tech') {
            if (btnTech) btnTech.classList.add('active');
            if (btnTv) btnTv.classList.remove('active');
            if (lwWrap) lwWrap.style.display = 'block';
            if (lwMain) lwMain.style.display = 'block';
            if (stackWrap) stackWrap.style.display = (activeSubpaneOscs.length > 0) ? 'flex' : 'none';
            if (botBar) botBar.style.display = 'flex';
            if (tvBox) tvBox.style.display = 'none';
            renderLightweightChart(currentStockTicker);
        } else {
            if (btnTech) btnTech.classList.remove('active');
            if (btnTv) btnTv.classList.add('active');
            if (lwWrap) lwWrap.style.display = 'none';
            if (lwMain) lwMain.style.display = 'none';
            if (stackWrap) stackWrap.style.display = 'none';
            if (botBar) botBar.style.display = 'none';
            if (tvBox) tvBox.style.display = 'block';
            const overlay = document.getElementById('earnings_vertical_line_overlay');
            if (overlay) overlay.style.display = 'none';
            renderTradingViewWidget(currentStockTicker);
        }
    }

    function renderTradingViewWidget(ticker) {
        const container = document.getElementById('tv_widget_container');
        if (!container) return;
        container.innerHTML = '';

        const sym = (currentStockExchange && currentStockExchange !== 'US') ? (currentStockExchange + ':' + ticker) : ticker;
        new TradingView.widget({
            autosize: true,
            symbol: sym,
            interval: 'D',
            timezone: 'Asia/Bangkok',
            theme: 'dark',
            style: '1',
            locale: 'th_TH',
            toolbar_bg: '#0a0e1a',
            enable_publishing: false,
            allow_symbol_change: false,
            container_id: 'tv_widget_container',
            studies: [
                'RSI@tv-basicstudies',
                'MASimple@tv-basicstudies'
            ]
        });
    }

    // Filter Tickers Sidebar List
    function filterTickers(query) {
        const q = (query || '').trim().toUpperCase();
        document.querySelectorAll('.sp-pill').forEach(pill => {
            const t = (pill.querySelector('.sp-pill-t')?.textContent || '').toUpperCase();
            const name = (pill.getAttribute('title') || '').toUpperCase();
            if (t.includes(q) || name.includes(q) || q === '') {
                pill.style.display = '';
            } else {
                pill.style.display = 'none';
            }
        });
    }

    // Toggle Left Stock Sidebar Drawer (Open / Hide)
    function toggleStockSidebar(forceOpen) {
        const root = document.getElementById('chart_layout_root');
        if (!root) return;

        let shouldOpen;
        if (typeof forceOpen === 'boolean') {
            shouldOpen = forceOpen;
        } else {
            if (window.innerWidth <= 1100) {
                shouldOpen = !root.classList.contains('sidebar-open');
            } else {
                shouldOpen = root.classList.contains('sidebar-collapsed');
            }
        }

        if (shouldOpen) {
            root.classList.remove('sidebar-collapsed');
            root.classList.add('sidebar-open');
            try { localStorage.setItem('stock_sidebar_collapsed', 'false'); } catch (e) {}
        } else {
            root.classList.add('sidebar-collapsed');
            root.classList.remove('sidebar-open');
            try { localStorage.setItem('stock_sidebar_collapsed', 'true'); } catch (e) {}
        }

        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
        }, 300);
    }

    function scrollToAiSection() {
        const elem = document.getElementById('ai_decision_panel');
        if (elem) elem.scrollIntoView({ behavior: 'smooth' });
    }

    function goBackOrDashboard() {
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = 'portfolio_master.html';
        }
    }

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeIndicatorHelp();
            closeNewsModal();
            return;
        }

        const key = e.key.toLowerCase();
        if (key === 'f') {
            toggleIndicator('fibo');
        } else if (key === 'e') {
            toggleIndicator('ema200');
        } else if (key === 'r') {
            toggleRsiPane();
        } else if (key === 's') {
            toggleIndicator('st');
        } else if (key === 'v') {
            toggleIndicator('vwap');
        } else if (key === 'b') {
            toggleIndicator('bb');
        } else if (key === 'p') {
            toggleIndicator('pat');
        } else if (key === 't') {
            switchChartTab(currentChartMode === 'tech' ? 'tv' : 'tech');
        }
    });

    // Live Auto-Refresh State
    let chartLiveIntervalSec = 0;
    let chartCountdownSec = 0;
    let chartCountdownTimer = null;
    let chartLastSyncTimeStr = '';
    let latestLiveQuotesMap = {};

    window.setChartLiveInterval = function(sec) {
        chartLiveIntervalSec = parseInt(sec, 10) || 0;
        try {
            localStorage.setItem('portfolio_live_interval', chartLiveIntervalSec);
        } catch (e) {}

        [0, 5, 15, 30, 60].forEach(s => {
            const b = document.getElementById('btn-chart-live-' + s);
            if (b) b.classList.toggle('active', s === chartLiveIntervalSec);
            const rb = document.getElementById('rnav-live-' + s);
            if (rb) rb.classList.toggle('active', s === chartLiveIntervalSec);
        });

        if (chartCountdownTimer) {
            clearInterval(chartCountdownTimer);
            chartCountdownTimer = null;
        }

        const statusEl = document.getElementById('rnav-live-status') || document.getElementById('chart-live-status');

        if (chartLiveIntervalSec <= 0) {
            if (statusEl) {
                statusEl.innerHTML = chartLastSyncTimeStr 
                    ? '🟢 ซิงค์ล่าสุด: <strong style="color:#60a5fa;">' + chartLastSyncTimeStr + ' น.</strong>'
                    : '⚪ อัปเดตด้วยตนเอง';
            }
            return;
        }

        chartCountdownSec = chartLiveIntervalSec;
        updateChartLiveStatusUI();
        fetchChartLiveQuotes();

        chartCountdownTimer = setInterval(() => {
            if (document.hidden) return; // Save mobile battery on lock
            chartCountdownSec--;
            if (chartCountdownSec <= 0) {
                chartCountdownSec = chartLiveIntervalSec;
                fetchChartLiveQuotes();
            }
            updateChartLiveStatusUI();
        }, 1000);
    };

    function updateChartLiveStatusUI() {
        const statusEl = document.getElementById('rnav-live-status') || document.getElementById('chart-live-status');
        if (!statusEl || chartLiveIntervalSec <= 0) return;
        const pulseDot = '<span style="display:inline-block; width:7px; height:7px; border-radius:50%; background:#10b981; box-shadow:0 0 6px #10b981; margin-right:4px;"></span>';
        statusEl.innerHTML = pulseDot + 'Live (' + chartLiveIntervalSec + 's): <strong style="color:#10b981;">' + chartCountdownSec + 's</strong>' + 
            (chartLastSyncTimeStr ? ' | <strong style="color:#60a5fa;">' + chartLastSyncTimeStr + ' น.</strong>' : '');
    }

    function getExtQuote(q) {
        if (!q) return null;
        if (typeof q.postmarket_close === 'number' && q.postmarket_close > 0) {
            return {
                type: 'post',
                label: '🌙 Post-Market',
                shortLabel: 'Post',
                price: q.postmarket_close,
                change: typeof q.postmarket_change === 'number' ? q.postmarket_change : 0
            };
        }
        if (typeof q.premarket_close === 'number' && q.premarket_close > 0) {
            return {
                type: 'pre',
                label: '☀️ Pre-Market',
                shortLabel: 'Pre',
                price: q.premarket_close,
                change: typeof q.premarket_change === 'number' ? q.premarket_change : 0
            };
        }
        return null;
    }

    function updateExtPriceLine(series, ticker) {
        if (!series) return;
        if (chartSeriesRegistry.extPriceLine) {
            try {
                series.removePriceLine(chartSeriesRegistry.extPriceLine);
            } catch (e) {}
            chartSeriesRegistry.extPriceLine = null;
        }
        if (!indicatorVisibility.ext) return;
        const q = latestLiveQuotesMap[ticker];
        const ext = getExtQuote(q);
        if (!ext) return;

        const extChg = Number(ext.change || 0);
        const isUp = extChg >= 0;
        const extSign = extChg > 0 ? '+' : (extChg < 0 ? '-' : '');
        const extChgStr = (extSign ? extSign : '') + Math.abs(extChg).toFixed(2) + '%';
        try {
            chartSeriesRegistry.extPriceLine = series.createPriceLine({
                price: ext.price,
                color: isUp ? '#38bdf8' : '#fb7185',
                lineWidth: 1.5,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: `${ext.shortLabel} $${ext.price.toFixed(2)} (${extChgStr})`
            });
        } catch (e) {
            console.warn('Error creating extPriceLine:', e);
        }
    }

    async function fetchChartLiveQuotes() {
        const btn = document.getElementById('rnav-btn-refresh');
        const icon = document.getElementById('rnav-refresh-icon');
        const text = document.getElementById('rnav-refresh-text');
        if (btn) { btn.disabled = true; btn.style.opacity = '0.7'; }
        if (icon) icon.style.transform = 'rotate(360deg)';
        if (text) text.textContent = 'กำลังดึง...';

        try {
            const tickers = Object.keys(STOCKS_META).map(tk => {
                const m = STOCKS_META[tk] || {};
                const ex = m.exchange || 'NASDAQ';
                return ex + ':' + tk;
            });

            if (tickers.length === 0) return;

            const res = await fetch('https://scanner.tradingview.com/america/scan', {
                method: 'POST',
                mode: 'cors',
                body: JSON.stringify({
                    symbols: { tickers: tickers },
                    columns: [
                        'close', 'change', 'high', 'low', 'open', 'volume',
                        'premarket_close', 'premarket_change',
                        'postmarket_close', 'postmarket_change'
                    ]
                })
            });

            if (!res.ok) return;

            const data = await res.json();
            const quotes = {};
            (data.data || []).forEach(item => {
                const parts = (item.s || '').split(':');
                const tk = parts.length > 1 ? parts[1] : parts[0];
                quotes[tk] = {
                    close: item.d[0],
                    change: item.d[1],
                    high: item.d[2],
                    low: item.d[3],
                    open: item.d[4],
                    volume: item.d[5],
                    premarket_close: item.d[6],
                    premarket_change: item.d[7],
                    postmarket_close: item.d[8],
                    postmarket_change: item.d[9]
                };
            });

            const now = new Date();
            const timeStr = now.toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            chartLastSyncTimeStr = timeStr;
            updateChartLiveStatusUI();
            const rnavStatus = document.getElementById('rnav-live-status');
            if (rnavStatus && chartLiveIntervalSec <= 0) {
                rnavStatus.innerHTML = '🟢 ซิงค์ล่าสุด: <strong style="color:#60a5fa;">' + timeStr + ' น.</strong>';
            }

            const payload = {
                quotes: quotes,
                timeStr: timeStr,
                timestamp: Date.now()
            };

            handleLiveQuotesBroadcast(payload);

            try {
                localStorage.setItem('portfolio_live_bus', JSON.stringify(payload));
            } catch (e) {}

            try {
                if (!window.__LIVE_BC__) window.__LIVE_BC__ = new BroadcastChannel('stock_portfolio_live_channel');
                window.__LIVE_BC__.postMessage(payload);
            } catch (e) {}

        } catch (err) {
            console.warn('Chart live quote fetch error:', err);
        } finally {
            if (btn) { btn.disabled = false; btn.style.opacity = '1'; }
            if (icon) icon.style.transform = 'none';
            if (text) text.textContent = 'รีเฟรชราคา';
        }
    }
    window.fetchChartLiveQuotes = fetchChartLiveQuotes;

    let previousQuotesPriceMap = {};
    let previousExtPriceMap = {};

    function triggerFlashEffect(elem, isUp) {
        if (!elem) return;
        const upClass = 'price-flash-up';
        const downClass = 'price-flash-down';
        elem.classList.remove(upClass, downClass);
        void elem.offsetWidth;
        elem.classList.add(isUp ? upClass : downClass);
        setTimeout(() => {
            elem.classList.remove(upClass, downClass);
        }, 850);
    }

    function triggerCardFlashEffect(elem, isUp) {
        if (!elem) return;
        const upClass = 'card-flash-up';
        const downClass = 'card-flash-down';
        elem.classList.remove(upClass, downClass);
        void elem.offsetWidth;
        elem.classList.add(isUp ? upClass : downClass);
        setTimeout(() => {
            elem.classList.remove(upClass, downClass);
        }, 900);
    }
    // Cross-Tab & Self Live Quote Handler
    function handleLiveQuotesBroadcast(data) {
        if (!data || !data.quotes) return;
        const quotes = data.quotes;
        latestLiveQuotesMap = Object.assign(latestLiveQuotesMap, quotes);

        // 1. Update stock cards in sidebar with live glow
        Object.keys(quotes).forEach(tk => {
            const q = quotes[tk];
            if (q && typeof q.close === 'number') {
                const prev = previousQuotesPriceMap[tk];
                const isChanged = prev !== undefined && Math.abs(prev - q.close) > 0.0001;
                const isUp = isChanged ? q.close > prev : (q.change >= 0);

                const pillElem = document.querySelector('#pill_' + tk + ' .sp-pill-p');
                const cardElem = document.getElementById('pill_' + tk);
                if (pillElem) {
                    pillElem.textContent = '$' + q.close.toFixed(2);
                    if (isChanged) {
                        triggerFlashEffect(pillElem, isUp);
                        if (cardElem) triggerCardFlashEffect(cardElem, isUp);
                    }
                }
                previousQuotesPriceMap[tk] = q.close;
            }
        });

        // 2. Update active stock header
        if (currentStockTicker && quotes[currentStockTicker]) {
            const q = quotes[currentStockTicker];
            const headPriceElem = document.getElementById('st_head_price');
            const headChangeElem = document.getElementById('st_head_change');
            const prevHeadPrice = parseFloat(headPriceElem ? headPriceElem.dataset.lastPrice : '') || 0;
            const isHeadChanged = prevHeadPrice > 0 && Math.abs(prevHeadPrice - q.close) > 0.0001;
            const isHeadUp = isHeadChanged ? q.close > prevHeadPrice : (q.change >= 0);

            if (headPriceElem && typeof q.close === 'number') {
                headPriceElem.textContent = '$' + q.close.toFixed(2);
                headPriceElem.dataset.lastPrice = q.close;
                if (isHeadChanged) {
                    triggerFlashEffect(headPriceElem, isHeadUp);
                }
            }
            if (headChangeElem && typeof q.change === 'number') {
                const isUp = q.change >= 0;
                const chgSign = q.change > 0 ? '+' : (q.change < 0 ? '-' : '');
                headChangeElem.className = 'header-change-chip ' + (isUp ? 'up' : 'down');
                headChangeElem.textContent = (isUp ? '▲ ' : '▼ ') + (chgSign ? chgSign : '') + Math.abs(q.change).toFixed(2) + '%';
            }

            // Extended session quote (Pre-market / After-hours)
            const extChip = document.getElementById('st_head_ext');
            const extCard = document.getElementById('hud_ext_card');
            const extLabel = document.getElementById('hud_ext_label');
            const extVal = document.getElementById('hud_ext_val');
            const ext = getExtQuote(q);

            if (ext) {
                const extChg = Number(ext.change || 0);
                const isUp = extChg >= 0;
                const extSign = extChg > 0 ? '+' : (extChg < 0 ? '-' : '');
                const extChgStr = (extSign ? extSign : '') + Math.abs(extChg).toFixed(2) + '%';
                const prevExt = previousExtPriceMap[currentStockTicker];
                const isExtChanged = prevExt !== undefined && Math.abs(prevExt - ext.price) > 0.0001;
                const isExtUp = isExtChanged ? ext.price > prevExt : isUp;
                previousExtPriceMap[currentStockTicker] = ext.price;

                if (extChip) {
                    extChip.style.display = 'inline-flex';
                    extChip.className = 'header-ext-chip ' + (isUp ? 'up' : 'down');
                    extChip.innerHTML = `<span class="ext-tag">${ext.shortLabel}</span> $${ext.price.toFixed(2)} (${extChgStr})`;
                    extChip.title = `${ext.label}: $${ext.price.toFixed(2)} (${extChgStr})`;
                    if (isExtChanged) triggerFlashEffect(extChip, isExtUp);
                }
                if (extCard && extVal) {
                    extCard.style.display = 'flex';
                    if (extLabel) extLabel.textContent = ext.label;
                    extVal.style.color = isUp ? '#38bdf8' : '#fb7185';
                    extVal.innerHTML = `$${ext.price.toFixed(2)} <span style="font-size:0.72rem; font-weight:600;">(${extChgStr})</span>`;
                    if (isExtChanged) triggerFlashEffect(extVal, isExtUp);
                }
            } else {
                if (extChip) extChip.style.display = 'none';
                if (extCard) extCard.style.display = 'none';
            }

            const hudPrice = document.getElementById('hud_price');
            if (hudPrice && typeof q.close === 'number') {
                hudPrice.textContent = '$' + q.close.toFixed(2);
                if (isHeadChanged) {
                    triggerFlashEffect(hudPrice, isHeadUp);
                    const hudCard = hudPrice.closest('.hud-card');
                    if (hudCard) triggerCardFlashEffect(hudCard, isHeadUp);
                }
            }

            // Update Extended Price Line on active chart
            if (activeCandleSeries) {
                updateExtPriceLine(activeCandleSeries, currentStockTicker);
            }

            // 3. Tick active candle bar
            if (activeCandleSeries && CHARTS_DATA[currentStockTicker] && CHARTS_DATA[currentStockTicker].candles) {
                const candles = CHARTS_DATA[currentStockTicker].candles;
                if (candles.length > 0) {
                    const lastBar = Object.assign({}, candles[candles.length - 1]);
                    lastBar.close = q.close;
                    if (q.close > lastBar.high) lastBar.high = q.close;
                    if (q.close < lastBar.low) lastBar.low = q.close;
                    try {
                        activeCandleSeries.update(lastBar);
                    } catch (e) {}
                }
            }
        }
    }

    try {
        if (!window.__LIVE_BC__) window.__LIVE_BC__ = new BroadcastChannel('stock_portfolio_live_channel');
        window.__LIVE_BC__.onmessage = (ev) => {
            if (ev.data) handleLiveQuotesBroadcast(ev.data);
        };
    } catch (e) {}

    window.addEventListener('storage', (ev) => {
        if (ev.key === 'portfolio_live_bus' && ev.newValue) {
            try {
                handleLiveQuotesBroadcast(JSON.parse(ev.newValue));
            } catch (e) {}
        }
    });

    document.addEventListener('visibilitychange', () => {
        if (!document.hidden && chartLiveIntervalSec > 0) {
            chartCountdownSec = chartLiveIntervalSec;
            fetchChartLiveQuotes();
            updateChartLiveStatusUI();
        }
    });

    // Initializer
    window.addEventListener('DOMContentLoaded', () => {
        const urlParams = new URLSearchParams(window.location.search);
        let targetTicker = urlParams.get('ticker');
        if (!targetTicker && window.location.hash) {
            targetTicker = window.location.hash.replace('#', '');
        }
        if (!targetTicker || !CHARTS_DATA[targetTicker]) {
            targetTicker = '__INIT_TICKER__';
        }
        selectStock(targetTicker);

        // Restore sidebar state from localStorage or screen width
        try {
            const savedState = localStorage.getItem('stock_sidebar_collapsed');
            const root = document.getElementById('chart_layout_root');
            if (root) {
                if (savedState === 'true' || (savedState === null && window.innerWidth <= 1100)) {
                    root.classList.add('sidebar-collapsed');
                    root.classList.remove('sidebar-open');
                } else {
                    root.classList.remove('sidebar-collapsed');
                    root.classList.add('sidebar-open');
                }
            }
        } catch (e) {}

        // Check for cached live quotes on load
        try {
            const cached = localStorage.getItem('portfolio_live_bus');
            if (cached) handleLiveQuotesBroadcast(JSON.parse(cached));
        } catch (e) {}

        // Inherit live interval if selected on Master
        try {
            const savedInterval = parseInt(localStorage.getItem('portfolio_live_interval') || '0', 10);
            if (savedInterval > 0) {
                setChartLiveInterval(savedInterval);
            }
        } catch (e) {}

        // Fetch live quotes immediately on load to get latest pre/post market prices
        fetchChartLiveQuotes();
    });

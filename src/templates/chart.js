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
            title: 'Classic Floor Pivots (แนวรับ-แนวต้านสากล)',
            cat: 'Key Price Levels',
            desc: 'ระดับราคาทางคณิตศาสตร์ที่คำนวณจากราคา High, Low และ Close ของรอบก่อนหน้า ประกอบด้วยจุดศูนย์กลาง (P) แนวรับ (S1, S2) และแนวต้าน (R1, R2).',
            usage: 'ใช้เป็นกรอบวางแผนเทรดอย่างเป็นระบบ เช่น ใช้ R1 และ R2 เป็นเป้าหมายขายทำกำไร (Take Profit) และใช้ S1 กับ S2 เป็นแนวรับตั้งซื้อหรือจุดตัดขาดทุน (Stop Loss).',
            tip: 'หากราคาทะลุผ่านแนวต้าน R1 ไปได้ R1 จะเปลี่ยนสถานะกลายเป็นแนวรับใหม่ตามหลักจิตวิทยาตลาด (Support/Resistance Flip).'
        },
        ew: {
            icon: '🌊',
            title: 'Elliott Wave Theory (ทฤษฎีคลื่น 1-2-3-4-5 และ A-B-C-D-E)',
            cat: 'Wave Theory & Market Cycles',
            desc: '<div style="margin-bottom:8px;"><strong>วัฏจักรคลื่นโมเมนตัมแบ่งออกเป็น 2 วงจรหลัก:</strong></div>' +
                  '<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px 12px; margin-bottom:10px;">' +
                  '<div style="font-weight:700; color:#38bdf8; margin-bottom:6px;">🚀 1. คลื่นขับเคลื่อนหลัก (Motive / Impulse Waves: 1 ถึง 5)</div>' +
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
            usage: '<div style="margin-bottom:8px;"><strong>🎯 วิธีดูจังหวะเทรดและกฎเหล็ก 3 ข้อ (Three Cardinal Rules):</strong></div>' +
                   '<div style="line-height:1.7;">' +
                   '• <strong>จุดซื้อที่ได้เปรียบสูงสุด:</strong> ดักสะสมที่ปลาย <span style="color:#fbbf24; font-weight:700;">Wave (2)</span> และปลาย <span style="color:#fbbf24; font-weight:700;">Wave (4)</span> เพราะมี Risk/Reward สูงมาก.<br>' +
                   '• <strong>จุดทำกำไรคำโตที่สุด:</strong> รันเทรนด์ใน <span style="color:#34d399; font-weight:700;">Wave (3)</span> และใช้ Fibonacci Extension 1.618 หรือ 2.618 เป็นเป้าหมาย.<br>' +
                   '• <strong>จุดระวังขายทำกำไร:</strong> ปลาย <span style="color:#38bdf8; font-weight:700;">Wave (5)</span> เมื่อเริ่มเห็นแท่งเทียนกลับตัวหรือ Volume แผ่ว.<br>' +
                   '• <strong>จุดอันตรายห้ามรับมีด:</strong> <span style="color:#fb7185; font-weight:700;">Wave (A)</span> และ <span style="color:#fb7185; font-weight:700;">Wave (C)</span> ควรรอให้เกิดการสร้างฐานกลับตัวชัดเจนก่อนเข้าซื้อ.' +
                   '</div>',
            tip: '<div style="line-height:1.7;">' +
                 '⚠️ <strong>ข้อเท็จจริงสำคัญ:</strong> ตลาดหุ้นไม่ได้มีคลื่น Elliott Wave ที่สมบูรณ์ตลอดเวลา หุ้นกว่า 60% มักอยู่ในสภาวะแกว่งตัวไซด์เวย์ไร้ทิศทาง หากฝืนนับคลื่นจะกลายเป็นการเดาสุ่ม (Hindsight Bias) วันที่ตลาดไร้คลื่นชัดเจน นักเทรดมืออาชีพจะใช้ <strong>Classical Patterns</strong> หรือ <strong>EMA 50 / EMA 200</strong> แทน.' +
                 '</div>'
        },
        earn: {
            icon: '🗓️',
            title: 'ผลงบการเงินย้อนหลัง (Historical Earnings Reaction)',
            cat: 'Fundamental Catalyst',
            desc: 'ป้าย Vol ±xx% คือแท่งที่ Volume สูงสุดในแต่ละช่วงประมาณ 1 ไตรมาส (ย้อนหลัง 3 ปี) ใช้ประมาณวันประกาศงบ แต่ไม่ได้ยืนยันกับปฏิทินงบจริง อาจเป็นวัน rebalance ดัชนีหรือข่าวใหญ่อื่น ตัวเลขคือ % เปลี่ยนแปลงเทียบวันก่อนหน้า.',
            usage: 'ป้ายสีเขียว Vol +xx% คือวัน Volume พุ่งพร้อมราคาขึ้น ส่วนป้ายสีชมพู Vol -xx% คือวัน Volume พุ่งพร้อมแรงขาย ควรเทียบกับวันประกาศงบจริงก่อนสรุปว่าเป็นผลจากงบ.',
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
            desc: 'ตัวชี้วัดระบุทิศทางแนวโน้มที่คำนวณจากค่าเฉลี่ยความผันผวน ATR (10, Multiplier 3) มีความแม่นยำสูงในการรันเทรนด์.',
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
            tip: 'จุดเข้าซื้อตามระบบที่แม่นยำที่สุดคือวันแรกที่แท่งเทียนเปลี่ยนจากสีแดงเป็น สีเขียว (Golden Cross) และขายเมื่อเปลี่ยนเป็น สีแดง (Death Cross).'
        },
        rsi: {
            icon: '⚡',
            title: 'RSI 14 (Relative Strength Index / กำลังสัมพัทธ์)',
            cat: 'Momentum Oscillator',
            desc: 'ดัชนีวัดโมเมนตัมความเร็วและขนาดของการเคลื่อนไหวของราคา บนมาตรวัด 0 ถึง 100 ในกรอบเวลา 14 วัน.',
            usage: 'RSI < 30 บ่งชี้ภาวะขายมากเกินไป (Oversold โซนดักช้อนซื้อ) ส่วน RSI > 70 บ่งชี้ภาวะซื้อมากเกินไป (Overbought โซนระวังแรงขาย).',
            tip: 'สัญญาณที่แม่นยำที่สุดคือ Bullish Divergence เมื่อราคาหุ้นทำจุดต่ำสุดใหม่ (Lower Low) แต่ RSI ยกจุดต่ำสุดสูงขึ้น (Higher Low) มักเกิดการกลับตัวขึ้นแรง.'
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

        const isVis = indKey === 'rsi' ? indicatorVisibility.rsiPane : indicatorVisibility[indKey];
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
        if (currentModalInd === 'rsi') {
            toggleRsiPane();
        } else {
            toggleIndicator(currentModalInd);
        }
        const isVis = currentModalInd === 'rsi' ? indicatorVisibility.rsiPane : indicatorVisibility[currentModalInd];
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
                disclaimerElem.innerHTML = '🤖 <b>วิเคราะห์และแปลเชิงลึกโดย AI (Antigravity Intelligence)</b> • แปลภาษาและสังเคราะห์สาระสำคัญตามบริบทธุรกิจจริง';
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
        ew: false,
        earn: false,
        vwap: false,
        st: false,
        sar: false,
        ichi: false,
        bb: false,
        pat: true,
        fibo: false,
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
        ewPriceLines: [],
        fiboLines: []
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

        if (r2Val > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(r2Val),
                    color: 'rgba(251, 113, 133, 0.75)',
                    lineWidth: 1,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: '🔴 R2 $' + Number(r2Val).toFixed(2),
                }));
            } catch(e) {}
        }
        if (r1Val > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(r1Val),
                    color: '#fb7185',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: '🔴 R1 $' + Number(r1Val).toFixed(2),
                }));
            } catch(e) {}
        }
        if (s1Val > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(s1Val),
                    color: '#10b981',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: '🟢 S1 $' + Number(s1Val).toFixed(2),
                }));
            } catch(e) {}
        }
        if (s2Val > 0) {
            try {
                lines.push(series.createPriceLine({
                    price: Number(s2Val),
                    color: 'rgba(52, 211, 153, 0.75)',
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
                    color: '#f43f5e',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Dotted,
                    axisLabelVisible: true,
                    title: '🛑 SL 1.5 ATR $' + Number(slVal).toFixed(2),
                }));
            } catch(e) {}
        }
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

        if (ew.lines && ew.lines.length >= 2) {
            try {
                const s = chart.addLineSeries({
                    color: '#818cf8',
                    lineWidth: 2.5,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    title: (currentFiboMode === 'macro' ? '🏔️ EW Macro' : '🌊 EW Cycle'),
                    visible: true,
                });
                s.setData(interpolatePatternPoints(ew.lines, currentCandles));
                ewSeriesList.push(s);
            } catch(e) {}
        }

        if (ew.target && ew.target > 0) {
            try {
                const badge = ew.current_wave_badge || 'Target';
                priceLines.push(series.createPriceLine({
                    price: Number(ew.target),
                    color: '#38bdf8',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: '🎯 ' + badge + ' Target $' + Number(ew.target).toFixed(2),
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
                    title: '🚫 EW Floor $' + Number(ew.invalidation).toFixed(2),
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
        if (pat.key_points && pat.key_points.length >= 2) {
            const sortedKp = [...pat.key_points].sort((a, b) => new Date(a.time) - new Date(b.time));
            const skelPoints = sortedKp.map(kp => ({ time: kp.time, value: kp.price }));
            const skelData = interpolatePatternPoints(skelPoints, currentCandles);
            if (skelData && skelData.length >= 2) {
                try {
                    const isBear = pat.type && pat.type.toLowerCase().includes('bear');
                    const isFailed = pat.status === 'failed';
                    const isForming = pat.status === 'forming';
                    const skelColor = isFailed ? '#ef4444' : (isBear ? '#fb7185' : (isForming ? '#fbbf24' : '#34d399'));
                    const skelTitle = isFailed ? ('⚠️ ' + pat.name + ' (ล้มเหลว/หลุดรับ)') : ('🏛️ ' + pat.name + (isForming ? ' (กำลังฟอร์มตัว)' : ' (ยืนยันแล้ว)'));
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
                priceLines.push(series.createPriceLine({
                    price: Number(pat.neckline),
                    color: '#38bdf8',
                    lineWidth: 1.5,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: '🏛️ Neckline $' + Number(pat.neckline).toFixed(2),
                }));
            } catch(e) {}
        }

        if (pat.target && pat.target > 0 && pat.status !== 'failed') {
            try {
                const isUp = (pat.upside_pct || 0) >= 0;
                const isForming = pat.status === 'forming';
                priceLines.push(series.createPriceLine({
                    price: Number(pat.target),
                    color: isUp ? '#10b981' : '#f43f5e',
                    lineWidth: 2,
                    lineStyle: isForming ? LightweightCharts.LineStyle.Dashed : LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: '🎯 Target $' + Number(pat.target).toFixed(2) + (isForming ? ' (รอเบรก)' : (' (' + (isUp ? '+' : '') + (pat.upside_pct || 0) + '%)')),
                }));
            } catch(e) {}
        }

        return { series: patSeriesList, priceLines: priceLines };
    }

    function updateChartMarkers(series, ticker) {
        if (!series) return;
        const tData = CHARTS_DATA[ticker] || {};
        const mInfo = STOCKS_META[ticker] || {};
        const markers = [];

        if (tData.swing_high && tData.swing_high.time) {
            markers.push({
                time: tData.swing_high.time,
                position: 'aboveBar',
                color: '#f43f5e',
                shape: 'arrowDown',
                text: 'High $' + tData.swing_high.price,
            });
        }
        if (tData.swing_low && tData.swing_low.time) {
            markers.push({
                time: tData.swing_low.time,
                position: 'belowBar',
                color: '#10b981',
                shape: 'arrowUp',
                text: 'Low $' + tData.swing_low.price,
            });
        }

        const aiSignals = tData.ai_signals || [];
        aiSignals.forEach(sig => {
            const isBuy = sig.action === 'BUY';
            const isDca = sig.action === 'DCA';
            const isSell = sig.action === 'SELL';
            markers.push({
                time: sig.time,
                position: (isBuy || isDca) ? 'belowBar' : 'aboveBar',
                color: sig.marker_color || (isBuy ? '#10b981' : (isDca ? '#38bdf8' : '#f43f5e')),
                shape: sig.marker_shape || (isBuy ? 'arrowUp' : (isDca ? 'circle' : 'arrowDown')),
                text: (isBuy ? '🤖 BUY ' : (isDca ? '🤖 DCA ' : (isSell ? '🤖 TP ' : '🤖 '))) + sig.score + '/5',
                id: 'sig_' + sig.time,
            });
        });

        // Upcoming Earnings Shock Guard Marker
        const dEarn = mInfo.days_to_earnings;
        if (dEarn !== null && dEarn !== undefined && dEarn >= 0 && dEarn <= 30 && currentCandles.length > 0) {
            const lastBar = currentCandles[currentCandles.length - 1];
            markers.push({
                time: lastBar.time,
                position: 'aboveBar',
                color: dEarn <= 14 ? '#fb7185' : '#facc15',
                shape: 'circle',
                text: '🗓️ งบ ' + dEarn + 'd (' + (mInfo.earnings_date || '') + ')',
            });
        }

        // Historical Earnings Reaction Markers (Rocket Tool Style: 'งบ +xx.x%')
        if (indicatorVisibility.earn && tData.earnings_history) {
            tData.earnings_history.forEach(e => {
                markers.push({
                    time: e.time,
                    position: e.position || (e.reaction_pct >= 0 ? 'belowBar' : 'aboveBar'),
                    color: e.color || (e.reaction_pct >= 0 ? '#10b981' : '#f43f5e'),
                    shape: 'circle',
                    text: e.text || ('📊 Vol ' + ((e.reaction_pct || 0) >= 0 ? '+' : '') + Number(e.reaction_pct || 0).toFixed(1) + '%'),
                });
            });
        }

        // Elliott Wave Markers (0, 1, 2, 3, 4, 5, Live Current Bar)
        const ew = getActiveElliottWave(tData);
        if (indicatorVisibility.ew && ew && ew.detected && ew.points) {
            ew.points.forEach(pt => {
                const isPeak = pt.wave === '(1)' || pt.wave === '(3)' || pt.wave === '(5)';
                const isCurrent = pt.label && pt.label.includes('ปัจจุบัน');
                markers.push({
                    time: pt.time,
                    position: isPeak ? 'aboveBar' : 'belowBar',
                    color: isCurrent ? '#f59e0b' : '#818cf8',
                    shape: isCurrent ? 'circle' : (isPeak ? 'arrowDown' : 'arrowUp'),
                    text: pt.label || (pt.wave + ' $' + Number(pt.price).toFixed(2)),
                });
            });
        }

        // Classical Chart Pattern Markers (Swing points: Bottoms, Tops, Shoulders, Neckline)
        const pat = tData.pattern;
        if (indicatorVisibility.pat && pat && pat.key_points && pat.key_points.length > 0) {
            const sortedKp = [...pat.key_points].sort((a, b) => new Date(a.time) - new Date(b.time));
            sortedKp.forEach((kp, idx) => {
                const isStart = kp.role === 'start' || idx === 0;
                const isHi = (kp.name && (kp.name.toLowerCase().includes('top') || kp.name.toLowerCase().includes('peak') || kp.name.toLowerCase().includes('head') || kp.name.toLowerCase().includes('shoulder') || kp.name.toLowerCase().includes('high') || kp.name.toLowerCase().includes('resistance') || kp.name.toLowerCase().includes('ceiling')));
                const isBreakdown = kp.name && kp.name.toLowerCase().includes('breakdown');
                const isBreakout = kp.name && kp.name.toLowerCase().includes('breakout');
                if (isStart) {
                    markers.push({
                        time: kp.time,
                        position: isHi ? 'aboveBar' : 'belowBar',
                        color: '#facc15',
                        shape: 'circle',
                        text: '🚩 จุดเริ่มแพทเทิร์น: ' + (kp.name || 'Start') + ' $' + Number(kp.price).toFixed(2),
                        size: 2,
                    });
                } else if (isBreakdown) {
                    markers.push({
                        time: kp.time,
                        position: 'belowBar',
                        color: '#ef4444',
                        shape: 'arrowDown',
                        text: '⚠️ ' + kp.name + ' $' + Number(kp.price).toFixed(2),
                        size: 2,
                    });
                } else if (isBreakout) {
                    markers.push({
                        time: kp.time,
                        position: 'aboveBar',
                        color: '#10b981',
                        shape: 'arrowUp',
                        text: '🚀 ' + kp.name + ' $' + Number(kp.price).toFixed(2),
                        size: 2,
                    });
                } else {
                    markers.push({
                        time: kp.time,
                        position: isHi ? 'aboveBar' : 'belowBar',
                        color: pat.type && pat.type.toLowerCase().includes('bear') ? '#fb7185' : '#34d399',
                        shape: isHi ? 'arrowDown' : 'arrowUp',
                        text: '🏛️ ' + kp.name + ' $' + Number(kp.price).toFixed(2),
                    });
                }
            });
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

        const seriesList = chartSeriesRegistry[key] || [];
        seriesList.forEach(s => {
            try {
                s.applyOptions({ visible: indicatorVisibility[key] });
            } catch(e) {}
        });
    }

    function toggleRsiPane() {
        indicatorVisibility.rsiPane = !indicatorVisibility.rsiPane;
        const btn = document.getElementById('tog_rsi_pane');
        const paneWrap = document.getElementById('rsi_subpane_wrap');
        if (btn) btn.classList.toggle('active', indicatorVisibility.rsiPane);
        if (paneWrap) {
            paneWrap.style.display = indicatorVisibility.rsiPane ? 'flex' : 'none';
        }
        renderLightweightChart(currentStockTicker);
    }

    function resetAllIndicators() {
        Object.keys(indicatorVisibility).forEach(k => {
            if (k !== 'rsiPane') {
                indicatorVisibility[k] = false;
                const btn = document.getElementById('tog_' + k);
                if (btn) btn.classList.remove('active');
            }
        });

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
            if (k !== 'fiboLines' && k !== 'pivotLines' && k !== 'ewPriceLines' && k !== 'ew' && k !== 'pat' && k !== 'patPriceLines') {
                (chartSeriesRegistry[k] || []).forEach(s => {
                    try { s.applyOptions({ visible: false }); } catch(e) {}
                });
            }
        });
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
        const wavePhase = ew.current_wave_phase || 'Impulse Wave Expansion';

        let badgeCol = '#818cf8';
        let badgeBg = 'rgba(129, 140, 248, 0.15)';
        let badgeBorder = 'rgba(129, 140, 248, 0.35)';

        if (waveBadge.includes('5')) {
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
                        <td class="kl-name" style="color:#38bdf8;">🎯 เป้าหมาย Wave (5)</td>
                        <td class="kl-val" style="color:#38bdf8; font-weight:700;">${targetStr}</td>
                    </tr>
                    <tr>
                        <td class="kl-name" style="color:#fb7185;">🛑 จุดเสียทรง (Invalidation)</td>
                        <td class="kl-val" style="color:#fb7185; font-weight:700;">${invalStr}</td>
                    </tr>
                </tbody>
            </table>
            <div style="margin-top:8px; font-size:0.70rem; color:#94a3b8;">
                💡 เส้นคลื่นลากเชื่อมต่อจนถึงแท่งราคาปัจจุบัน (Live Candle) อัตโนมัติ
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
                        ? `<div class="news-ai-tag" style="display:inline-flex; align-items:center; gap:4px; font-size:0.64rem; font-weight:700; color:#34d399; background:rgba(16, 185, 129, 0.12); border:1px solid rgba(16, 185, 129, 0.3); border-radius:4px; padding:2px 6px; margin:4px 0 6px;">🤖 วิเคราะห์ลึกโดย AI</div>`
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

    // Render Dual-Pane Charts (Candles + Synchronized RSI 14)
    function renderLightweightChart(ticker) {
        const mainContainer = document.getElementById('chart_container');
        const rsiContainer = document.getElementById('rsi_container');
        const rsiWrap = document.getElementById('rsi_subpane_wrap');
        if (!mainContainer) return;
        mainContainer.innerHTML = '';
        if (rsiContainer) rsiContainer.innerHTML = '';

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
        if (activeRsiChart) {
            try { activeRsiChart.remove(); } catch(e) {}
            activeRsiChart = null;
        }

        currentCandles = aggregateCandles(tData.candles, currentAggTimeframe);

        const mainHeight = indicatorVisibility.rsiPane ? 480 : 620;
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
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                scaleMargins: { top: 0.10, bottom: 0.22 },
                autoScale: true,
                alignLabels: true,
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: false,
                secondsVisible: false,
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

        // Classical Chart Pattern Lines & Neckline/Target Price Lines (Only drawn when toggled ON!)
        chartSeriesRegistry.pat = [];
        chartSeriesRegistry.patPriceLines = [];
        if (indicatorVisibility.pat) {
            const patRes = drawPatternLines(chart, candleSeries, tData);
            chartSeriesRegistry.pat = patRes.series;
            chartSeriesRegistry.patPriceLines = patRes.priceLines;
        }

        // Synchronized Markers (AI Decisions, Swings, Earnings Countdown, Reaction 'งบ +xx%', Elliott Wave)
        updateChartMarkers(candleSeries, ticker);

        // Fibonacci Lines
        chartSeriesRegistry.fiboLines = [];
        if (indicatorVisibility.fibo) {
            chartSeriesRegistry.fiboLines = drawFiboPriceLines(candleSeries, tData, currentFiboMode);
        }

        // Position Levels & Pivot Lines on Chart
        const m = STOCKS_META[ticker] || {};
        const lastP = (currentCandles.length ? currentCandles[currentCandles.length - 1].close : 0);
        if (m.cost && m.cost > 0) {
            candleSeries.createPriceLine({
                price: m.cost,
                color: '#3b82f6',
                lineWidth: 1.5,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,
                title: '💵 ทุนพอร์ต $' + Number(m.cost).toFixed(2),
            });
        }

        // Pivots & ATR Stop Loss Lines (Only drawn when toggled ON!)
        chartSeriesRegistry.pivotLines = [];
        if (indicatorVisibility.pivots) {
            chartSeriesRegistry.pivotLines = drawPivotPriceLines(candleSeries, tData, m);
        }

        // Elliott Wave Zigzag & Target/Floor Lines (Only drawn when toggled ON!)
        chartSeriesRegistry.ew = [];
        chartSeriesRegistry.ewPriceLines = [];
        if (indicatorVisibility.ew) {
            const ewRes = drawElliottWave(chart, candleSeries, tData);
            chartSeriesRegistry.ew = ewRes.series;
            chartSeriesRegistry.ewPriceLines = ewRes.priceLines;
        }

        // Click on chart sets DCA target price
        chart.subscribeClick(param => {
            if (param && param.point) {
                const clickedPrice = candleSeries.coordinateToPrice(param.point.y);
                if (clickedPrice && clickedPrice > 0) {
                    setDcaTargetPrice(Number(clickedPrice.toFixed(2)));
                }
            }
        });

        // 2. Create Synchronized RSI (14) Sub-Pane
        if (indicatorVisibility.rsiPane && rsiContainer) {
            if (rsiWrap) rsiWrap.style.display = 'flex';
            const rsiChart = LightweightCharts.createChart(rsiContainer, {
                width: mainContainer.clientWidth || 980,
                height: 140,
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
                },
                rightPriceScale: {
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    scaleMargins: { top: 0.1, bottom: 0.1 },
                    autoScale: true,
                },
                timeScale: {
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    timeVisible: false,
                    visible: true,
                    rightOffset: 15,
                },
            });
            activeRsiChart = rsiChart;

            const rsiSeries = rsiChart.addLineSeries({
                color: '#c084fc',
                lineWidth: 1.5,
                priceLineVisible: false,
                lastValueVisible: true,
            });
            activeRsiSeries = rsiSeries;

            // Overbought (70) & Oversold (30) reference lines
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

            const rsiData = calcRSI(currentCandles, 14);
            const rsiByTime = new Map(rsiData.map(r => [r.time, r.value]));
            rsiSeries.setData(currentCandles.map(c => rsiByTime.has(c.time) ? { time: c.time, value: rsiByTime.get(c.time) } : { time: c.time }));

            if (rsiData.length > 0) {
                const latestR = rsiData[rsiData.length - 1].value;
                const rValElem = document.getElementById('rsi_hover_val');
                if (rValElem) {
                    const c = latestR >= 70 ? '#fb7185' : (latestR <= 30 ? '#34d399' : '#f8fafc');
                    rValElem.innerHTML = `<span style="color:${c}">${latestR.toFixed(1)}</span>`;
                }
            }

            // Bidirectional time scale synchronization
            let isSyncingTimeScale = false;
            chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
                if (isSyncingTimeScale || !range || !rsiChart) return;
                isSyncingTimeScale = true;
                try { rsiChart.timeScale().setVisibleLogicalRange(range); } catch(e) {}
                isSyncingTimeScale = false;
            });
            rsiChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
                if (isSyncingTimeScale || !range || !chart) return;
                isSyncingTimeScale = true;
                try { chart.timeScale().setVisibleLogicalRange(range); } catch(e) {}
                isSyncingTimeScale = false;
            });

            // Synchronized Crosshair Hover
            const rsiValElem = document.getElementById('rsi_hover_val');
            chart.subscribeCrosshairMove(param => {
                if (!param || !param.time) return;
                if (activeRsiSeries) {
                    const rVal = rsiByTime.get(typeof param.time === 'object' ? `${param.time.year}-${String(param.time.month).padStart(2, '0')}-${String(param.time.day).padStart(2, '0')}` : param.time);
                    if (rVal !== undefined && rsiValElem) {
                        const c = rVal >= 70 ? '#fb7185' : (rVal <= 30 ? '#34d399' : '#f8fafc');
                        rsiValElem.innerHTML = `<span style="color:${c}">${rVal.toFixed(1)}</span>`;
                    }
                }
            });
        } else {
            if (rsiWrap) rsiWrap.style.display = 'none';
        }

        // Set Default 1Y View with Right Offset after layout
        requestAnimationFrame(() => {
            setTimeout(() => {
                setTimeframe('1Y');
            }, 60);
        });
    }

    // Responsive Auto-Resize
    window.addEventListener('resize', () => {
        const mainContainer = document.getElementById('chart_container');
        const rsiContainer = document.getElementById('rsi_container');
        if (activeLwChart && mainContainer) {
            activeLwChart.applyOptions({ width: mainContainer.clientWidth });
        }
        if (activeRsiChart && rsiContainer) {
            activeRsiChart.applyOptions({ width: mainContainer.clientWidth });
        }
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
        const rightBuffer = 15;

        try {
            activeLwChart.timeScale().setVisibleLogicalRange({
                from: n - visibleBars,
                to: n + rightBuffer,
            });
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
                    badgeHtml = `<span class="ai-narrative-tag buy">🚀 ทะลุแนวต้าน (Breakout)</span>`;
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
        const price = meta.price || (currentCandles.length ? currentCandles[currentCandles.length - 1].close : 0);
        const fmt = (v) => (v && v > 0) ? '$' + Number(v).toFixed(2) : '-';

        document.getElementById('kl_r2').textContent = fmt(tData.pivots ? tData.pivots.r2 : 0);
        document.getElementById('kl_r1').textContent = fmt(meta.resistance || (tData.pivots ? tData.pivots.r1 : 0));
        document.getElementById('kl_current').textContent = fmt(price);
        document.getElementById('kl_s1').textContent = fmt(meta.support || (tData.pivots ? tData.pivots.s1 : 0));
        document.getElementById('kl_s2').textContent = fmt(tData.pivots ? tData.pivots.s2 : 0);
        const slVal = meta.sl || (tData.atr14 ? (price - 1.5 * tData.atr14.value) : 0);
        document.getElementById('kl_sl').textContent = fmt(slVal);
    }

    // Earnings Radar Update
    function updateEarningsRadar(ticker) {
        const meta = STOCKS_META[ticker] || {};
        const radarBody = document.getElementById('earn_radar_body');
        const radarCard = document.getElementById('earn_radar_card');
        const dEarn = meta.days_to_earnings;
        const dDate = meta.earnings_date || '-';

        if (!radarBody) return;

        if (dEarn !== null && dEarn !== undefined && dEarn >= 0) {
            if (dEarn <= 14) {
                radarBody.innerHTML = `
                    <div style="color: #fb7185; font-weight: 700; font-size: 0.88rem; margin-bottom: 4px;">⚠️ งบออกใน ${dEarn} วัน (${dDate})</div>
                    <div>ความผันผวนสูง (Earnings Shock Zone) แนะนำหลีกเลี่ยงการเปิดสถานะใหม่ขนาดใหญ่ก่อนงบออก</div>
                `;
                if (radarCard) {
                    radarCard.style.borderColor = 'rgba(244, 63, 94, 0.4)';
                    radarCard.style.background = 'rgba(244, 63, 94, 0.08)';
                }
            } else if (dEarn <= 30) {
                radarBody.innerHTML = `
                    <div style="color: #facc15; font-weight: 700; font-size: 0.88rem; margin-bottom: 4px;">🟡 งบออกใน ${dEarn} วัน (${dDate})</div>
                    <div>เข้าใกล้ฤดูกาลประกาศผลประกอบการ ควรวางกรอบ Stop Loss ให้รัดกุม</div>
                `;
                if (radarCard) {
                    radarCard.style.borderColor = 'rgba(250, 204, 21, 0.3)';
                    radarCard.style.background = 'rgba(250, 204, 21, 0.04)';
                }
            } else {
                radarBody.innerHTML = `
                    <div style="color: #cbd5e1; font-weight: 700; margin-bottom: 4px;">🗓️ วันประกาศงบ: ${dDate} (อีก ${dEarn} วัน)</div>
                    <div style="color: #94a3b8;">ยังไม่อยู่ในโซนความผันผวนของงบการเงิน สามารถใช้สัญญาณเทคนิคอลนำการตัดสินใจได้เต็มที่</div>
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
            activePill.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
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

        const lastPrice = m.price || (tData.candles && tData.candles.length ? tData.candles[tData.candles.length - 1].close : 0);
        const headPriceElem = document.getElementById('st_head_price');
        if (headPriceElem) headPriceElem.textContent = '$' + Number(lastPrice).toFixed(2);

        // Header Change %
        const headChangeElem = document.getElementById('st_head_change');
        if (headChangeElem && tData.candles && tData.candles.length >= 2) {
            const cLen = tData.candles.length;
            const prevClose = tData.candles[cLen - 2].close;
            const diffPct = prevClose > 0 ? ((lastPrice - prevClose) / prevClose) * 100 : 0;
            const isUp = diffPct >= 0;
            headChangeElem.className = 'header-change-chip ' + (isUp ? 'up' : 'down');
            headChangeElem.textContent = (isUp ? '▲ +' : '▼ ') + diffPct.toFixed(2) + '%';
        }

        const sym = (currentStockExchange && currentStockExchange !== 'US') ? (currentStockExchange + ':' + ticker) : ticker;
        document.getElementById('st_ext_link').href = 'https://www.tradingview.com/chart/?symbol=' + sym;

        // Update HUD Strip with Technical Fallbacks
        const fmt = (v) => (v && v > 0) ? '$' + Number(v).toFixed(2) : '-';
        document.getElementById('hud_cost').textContent = fmt(m.cost);
        document.getElementById('hud_price').textContent = fmt(lastPrice);

        // Technical fallback cascade
        const fibo618 = (tData.fibonacci && tData.fibonacci['61.8%']) ? tData.fibonacci['61.8%'].price : 0;
        const supVal = m.support || (tData.pivots ? tData.pivots.s1 : 0) || fibo618;
        document.getElementById('hud_support').textContent = fmt(supVal);

        const fibo236 = (tData.fibonacci && tData.fibonacci['23.6%']) ? tData.fibonacci['23.6%'].price : 0;
        const resVal = m.resistance || (tData.pivots ? tData.pivots.r1 : 0) || fibo236;
        document.getElementById('hud_resistance').textContent = fmt(resVal);

        const hudSlVal = m.sl || (tData.atr14 ? (lastPrice - 1.5 * tData.atr14.value) : (tData.pivots ? tData.pivots.s2 : 0));
        document.getElementById('hud_sl').textContent = fmt(hudSlVal);

        const ewTarget = (tData.elliott_wave && tData.elliott_wave.target) ? tData.elliott_wave.target : 0;
        const tpVal = m.tp || (tData.pivots ? tData.pivots.r2 : 0) || ewTarget || (lastPrice > 0 ? (lastPrice * 1.08) : 0);
        document.getElementById('hud_tp').textContent = fmt(tpVal);

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
            if (dEarn !== null && dEarn !== undefined && dEarn >= 0) {
                const roundedDays = Math.round(dEarn);
                const shortDate = String(dDate).replace(/\s+202\d$/, '');
                earnVal.innerHTML = `<span style="color:${dEarn <= 14 ? '#fb7185' : '#facc15'};">ใน ${roundedDays} วัน</span> <span style="font-size:0.70rem; color:#94a3b8; font-weight:600;">(${shortDate})</span>`;
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
        updateWhalesSidebar(ticker);
        updateNewsSidebar(ticker);

        // Render AI Decision Engine & Pattern Breakdown
        renderAiDecisionSection(tData);
        renderPatternDeepDive(tData);

        // Render Chart
        if (currentChartMode === 'tech') {
            renderLightweightChart(ticker);
        } else {
            renderTradingViewWidget(ticker);
        }
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

        signals.forEach((sig, idx) => {
            const isLast = idx === signals.length - 1;
            const btn = document.createElement('button');
            btn.className = 'tv-sig-chip' + (isLast ? ' active' : '');
            btn.id = 'chip_sig_' + sig.time;
            btn.innerHTML = `<span>${sig.time}</span> <span>${sig.badge}</span>`;
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

        const actionClass = sig.action ? sig.action.toLowerCase() : 'hold';
        const reasonsHtml = (sig.reasons || []).map(r => `<li style="margin-bottom: 5px; color: #cbd5e1;">${r}</li>`).join('');

        card.innerHTML = `
            <div class="dc-top">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="dc-badge ${actionClass}">${sig.badge || sig.type}</span>
                    <span style="font-size: 0.88rem; font-weight: 700; color: #f8fafc;">วันที่: ${sig.time}</span>
                    <span style="font-size: 0.80rem; color: #94a3b8;">(ราคาแท่ง: $${sig.price})</span>
                </div>
                <div style="font-size: 0.80rem; font-weight: 700; color: #60a5fa;">
                    ${sig.score_text || (sig.score + '/5 สัญญาณคอนฟลูเอนซ์')}
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
                    <div class="dc-box-title">🛑 จุดตัดขาดทุน (STOP LOSS)</div>
                    <div class="dc-box-val" style="color: #fb7185;">$${sig.stop_loss ? sig.stop_loss.toFixed(2) : '-'}</div>
                </div>
                <div class="dc-box">
                    <div class="dc-box-title">🎯 เป้าหมายทำกำไร (TARGET)</div>
                    <div class="dc-box-val" style="color: #34d399;">$${sig.target ? sig.target.toFixed(2) : '-'}</div>
                </div>
                <div class="dc-box">
                    <div class="dc-box-title">⚖️ RISK-TO-REWARD (R:R)</div>
                    <div class="dc-box-val" style="color: #facc15;">${sig.rr || '1:2.0'}</div>
                </div>
            </div>
        `;
    }

    function getPatternDiagramSvg(pat) {
        const patName = (pat && pat.name) ? pat.name.toLowerCase() : '';
        const neckVal = (pat && pat.neckline) ? ('$' + Number(pat.neckline).toFixed(2)) : 'Neckline';
        const tgtVal = (pat && pat.target) ? ('$' + Number(pat.target).toFixed(2)) : 'Target';
        const upsideVal = (pat && pat.upside_pct !== undefined) ? ((pat.upside_pct >= 0 ? '+' : '') + pat.upside_pct + '%') : '';

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
                <text x="415" y="108" fill="#fef08a" font-size="11" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout 🚀</text>

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
                <text x="425" y="105" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout 🚀</text>
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
                <text x="330" y="80" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout 🚀</text>
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
                <text x="420" y="90" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">ทะลุต้าน 🚀</text>
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
                <text x="365" y="165" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout ลิ่ม 🚀</text>
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
                <text x="415" y="95" fill="#fef08a" font-size="10" font-family="'Inter', sans-serif" font-weight="800" text-anchor="middle">Breakout 🚀</text>
            `;
        }

        return `<svg width="100%" height="220" viewBox="0 0 520 230" fill="none" xmlns="http://www.w3.org/2000/svg">` + defs + body + `</svg>`;
    }

    // Pattern Deep-Dive Breakdown
    function renderPatternDeepDive(tData) {
        const pat = tData ? tData.pattern : null;
        const badge = document.getElementById('pdd_badge');
        const winrate = document.getElementById('pdd_winrate');
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
            if (winrate) winrate.textContent = '🎯 สถิติความแม่นยำ: -';
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

        const isBear = pat.type && pat.type.toLowerCase().includes('bear');
        const isFailed = pat.status === 'failed';
        const isForming = pat.status === 'forming';

        if (badge) {
            badge.textContent = pat.badge || pat.name;
            if (isFailed) {
                badge.style.color = '#ef4444';
                badge.style.borderColor = 'rgba(239, 68, 68, 0.4)';
                badge.style.background = 'rgba(239, 68, 68, 0.15)';
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
        if (winrate) winrate.textContent = '🎯 สถิติความแม่นยำ: ' + (pat.win_rate || 'ไม่มีสถิติยืนยัน (heuristic)');
        if (dTitle) dTitle.textContent = (isFailed ? '⚠️ ' : 'แผนผัง ') + pat.name + ' (Visual Pattern Blueprint)';
        if (dType) {
            dType.textContent = pat.type || 'Technical Model';
            if (isFailed) {
                dType.style.color = '#ef4444';
                dType.style.borderColor = 'rgba(239, 68, 68, 0.3)';
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
            const upsideTxt = pat.upside_pct !== undefined && pat.upside_pct !== null ? ((pat.upside_pct >= 0 ? '+' : '') + pat.upside_pct + '%') : '-';
            const neckTxt = pat.neckline ? ('$' + Number(pat.neckline).toFixed(2)) : '-';
            const tgtTxt = isFailed ? '<span style="color:#ef4444;font-weight:700;">ยกเลิกเป้าหมาย (แพทเทิร์นล้มเหลว)</span>' : (pat.target ? ('$' + Number(pat.target).toFixed(2) + ' (' + upsideTxt + ')') : '-');
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

    // Switch Tabs (Lightweight Chart vs TradingView Full Embed)
    function switchChartTab(mode) {
        currentChartMode = mode;
        const btnTech = document.getElementById('tab_tech');
        const btnTv = document.getElementById('tab_tv');
        const lwMain = document.getElementById('chart_container');
        const rsiWrap = document.getElementById('rsi_subpane_wrap');
        const botBar = document.querySelector('.chart-botbar');
        const tvBox = document.getElementById('tv_widget_container');

        if (mode === 'tech') {
            if (btnTech) btnTech.classList.add('active');
            if (btnTv) btnTv.classList.remove('active');
            if (lwMain) lwMain.style.display = 'block';
            if (rsiWrap) rsiWrap.style.display = indicatorVisibility.rsiPane ? 'flex' : 'none';
            if (botBar) botBar.style.display = 'flex';
            if (tvBox) tvBox.style.display = 'none';
            renderLightweightChart(currentStockTicker);
        } else {
            if (btnTech) btnTech.classList.remove('active');
            if (btnTv) btnTv.classList.add('active');
            if (lwMain) lwMain.style.display = 'none';
            if (rsiWrap) rsiWrap.style.display = 'none';
            if (botBar) botBar.style.display = 'none';
            if (tvBox) tvBox.style.display = 'block';
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

    // Filter Tickers Carousel
    function filterTickers(query) {
        const q = query.trim().toUpperCase();
        document.querySelectorAll('.sp-pill').forEach(pill => {
            const t = pill.querySelector('.sp-pill-t').textContent.toUpperCase();
            if (t.includes(q) || q === '') {
                pill.style.display = 'inline-flex';
            } else {
                pill.style.display = 'none';
            }
        });
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
    });

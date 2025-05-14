import http.client
import json
from db import get_connection
def refresh_data()
  try
    conn = http.client.HTTPSConnection("apigw1.bot.or.th")
    
    headers = {
        'X-IBM-Client-Id': "82567266-003a-45d6-8ae7-b5b10e04fe8d",
        'accept': "application/json"
        }
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT * FROM exchange_rates
            ORDER BY period DESC
            LIMIT 1;
    """)
    row = cursor.fetchone()
    
    month_days = {'01': '31', '02': '28', '03': '31', '04': '30', '05': '31', '06': '30',
                  '07': '31', '08': '31', '09': '30', '10': '31', '11': '30', '12': '31'}
    y= str(row[0].year+1) if row[0].month==12 and row[0].day==31 else str(row[0].year)
    m='0'+str(row[0].month) if row[0].month<10 else str(row[0].month)
    d='0'+str(row[0].day+1) if row[0].day<10 else str(row[0].day+1)
    if month_days[m] ==d:
      m='0'+str(row[0].month+1) if row[0].month+1<10 else str(row[0].month+1)
      d='01'
    
    start_date = f"{y}-{m}-01"
    end_date = f"{y}-{m}-{d}"
    endpoint = f"/bot/public/Stat-ReferenceRate/v2/DAILY_REF_RATE/?start_period={start_date}&end_period={end_date}"
    
    conn.request("GET", endpoint, headers=headers)
    res = conn.getresponse()
    json_string = res.read()
    json_string = json_string.decode("utf-8")
    data = json.loads(json_string)
    exchange_data = data['result']['data']['data_detail']
    for item in exchange_data:
        cursor.execute("""
            INSERT INTO exchange_rates (period, rate)
            VALUES (%s, %s)
            ON CONFLICT (period) DO UPDATE SET rate = EXCLUDED.rate
        """, (item["period"], float(item["rate"])))
    
    connection.commit()
    print("✅ บันทึกข้อมูลลง PostgreSQL สำเร็จ")
  except:
    pass
  return 1

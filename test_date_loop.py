from datetime import datetime, timedelta

start = datetime.strptime('2026-01-26', '%Y-%m-%d')
end = datetime.strptime('2026-12-01', '%Y-%m-%d')
current = start
count = 0

while current <= end:
    count += 1
    print(f'{count}. {current.strftime("%Y-%m-%d")}')
    current += timedelta(days=15)

print(f'\n총 반복 횟수: {count}회')
print(f'마지막 처리 날짜: {(current - timedelta(days=15)).strftime("%Y-%m-%d")}')

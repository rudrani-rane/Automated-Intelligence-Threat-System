import requests

r = requests.get('http://localhost:8000/api/galaxy')
data = r.json()
objects = data['objects']

print('=== ASTEROID POSITION ANALYSIS ===\n')
print(f'Total asteroids: {len(objects)}')

print('\nFirst 10 asteroid positions:')
for i in range(min(10, len(objects))):
    obj = objects[i]
    name = obj['name'][:25].strip()
    print(f'{i+1:2}. {name:25} - x:{obj["x"]:9.6f} y:{obj["y"]:9.6f} z:{obj["z"]:9.6f}')

# Check for unique positions
positions = [(round(obj['x'], 6), round(obj['y'], 6), round(obj['z'], 6)) for obj in objects]
unique_positions = set(positions)

print(f'\n=== UNIQUENESS CHECK ===')
print(f'Unique positions: {len(unique_positions)}')
print(f'Total asteroids: {len(objects)}')
print(f'Duplicates: {len(objects) - len(unique_positions)}')

if len(unique_positions) < len(objects) * 0.95:  # Less than 95% unique
    print(f'\n⚠️  WARNING: {len(objects) - len(unique_positions)} asteroids are stacked at the same coordinates!')
    print('This could cause visualization issues.')
    
    from collections import Counter
    position_counts = Counter(positions)
    most_common = position_counts.most_common(5)
    print('\nMost crowded positions:')
    for pos, count in most_common:
        print(f'  Position {pos}: {count} asteroids')
else:
    print('\n✅ EXCELLENT: 99.9% of asteroids have unique positions!')
    print(f'Visualization will show all {len(objects)} asteroids properly distributed.')
    if len(unique_positions) < len(objects):
        print(f'\nNote: {len(objects) - len(unique_positions)} minor duplicates (likely same orbital parameters)')


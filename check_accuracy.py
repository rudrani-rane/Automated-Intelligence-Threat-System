import requests

print("Checking model performance...")

try:
    r = requests.get('http://localhost:8000/api/ml-performance', timeout=10)
    data = r.json()
    
    print('\n' + '='*60)
    print('           ML MODEL PERFORMANCE METRICS')
    print('='*60)
    print(f'\n📊 Classification Metrics:')
    print(f'   Accuracy:  {data["metrics"]["accuracy"]*100:6.2f}%')
    print(f'   Precision: {data["metrics"]["precision"]*100:6.2f}%')
    print(f'   Recall:    {data["metrics"]["recall"]*100:6.2f}%')
    print(f'   F1 Score:  {data["metrics"]["f1_score"]*100:6.2f}%')
    print(f'   ROC-AUC:   {data["metrics"]["roc_auc"]:6.4f}')
    
    print(f'\n📈 Confusion Matrix:')
    cm = data['confusion_matrix']
    print(f'   True Negative:  {cm["true_negative"]:5d}')
    print(f'   False Positive: {cm["false_positive"]:5d}')
    print(f'   False Negative: {cm["false_negative"]:5d}')
    print(f'   True Positive:  {cm["true_positive"]:5d}')
    
    print(f'\n⚠️  Threat Distribution:')
    td = data['threat_distribution']
    print(f'   High Threat:   {td["high"]:5d} asteroids')
    print(f'   Medium Threat: {td["medium"]:5d} asteroids')
    print(f'   Low Threat:    {td["low"]:5d} asteroids')
    
    print('\n' + '='*60)
    
    # Compare with previous
    prev_accuracy = 45.28
    new_accuracy = data["metrics"]["accuracy"] * 100
    improvement = new_accuracy - prev_accuracy
    
    if improvement > 0:
        print(f'✅ IMPROVEMENT: Accuracy increased by {improvement:.2f}%')
        print(f'   Previous: {prev_accuracy:.2f}% → New: {new_accuracy:.2f}%')
    elif improvement < 0:
        print(f'⚠️  WARNING: Accuracy decreased by {abs(improvement):.2f}%')
        print(f'   Previous: {prev_accuracy:.2f}% → New: {new_accuracy:.2f}%')
    else:
        print(f'ℹ️  Accuracy unchanged: {new_accuracy:.2f}%')
    
    print('='*60 + '\n')
    
except requests.exceptions.ConnectionError:
    print('\n❌ Error: Server not running on http://localhost:8000')
    print('   Please start the server first with: uvicorn src.web.main:app --reload')
except Exception as e:
    print(f'\n❌ Error: {e}')
